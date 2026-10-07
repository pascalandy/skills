"""Installer behavior through its CLI with isolated repositories and homes."""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from conftest import commit, skill
from install_skills import replace

MAC = (
    ".pi/agent/skills",
    ".agents/skills",
    ".claude/skills",
    ".config/opencode/skills",
    ".config/agents/skills",
)
OM1 = (".pi/agent/skills", ".codex/skills", ".claude/skills", ".config/opencode/skills")
COMMANDS = (".claude/commands", ".pi/agent/prompts", ".config/opencode/commands")
RETIRED = (".codex/prompts", ".config/agents/commands")


def command(repo: Path, name: str, body: str = "command") -> Path:
    path = repo / "commands" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")
    return path


def run(
    repo: Path, home: Path, *args: str, script: str = "install_skills.py"
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["UV_CACHE_DIR"] = str(home.parent / "uv-cache")
    # Pin the host-dependent default; a later --profile in args wins.
    result = subprocess.run(
        [
            "uv",
            "run",
            str(repo / "scripts" / script),
            "--profile",
            "mac",
            *args,
        ],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


OK = '{"ok":true}\n'


def report(result: subprocess.CompletedProcess[str]) -> list[dict]:
    """The installer's changes, each as its kind, target, and name."""
    return [
        {
            "kind": kind,
            "target": path[2:].rsplit("/", 1)[0],
            "name": path.rsplit("/", 1)[1],
        }
        for kind, path in json.loads(result.stdout).get("changes", [])
    ]


def failed(*errors: str, **fields: object) -> str:
    answer = {"ok": False, "errors": list(errors), **fields}
    return json.dumps(answer, separators=(",", ":")) + "\n"


def test_preview_apply_check_and_repeat_agree(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "alpha", "new")
    preview = run(repo, home, "--dry-run")
    assert preview.returncode == 0
    assert {a["kind"] for a in report(preview)} == {"add"}
    assert not home.exists()
    assert (repo / "skills/alpha/SKILL.md").read_text(
        encoding="utf-8"
    ) == "# alpha\n\nold\n"
    assert run(repo, home, "--check").returncode == 1
    applied = run(repo, home)
    assert applied.returncode == 0
    assert [(a["target"], a["name"], a["kind"]) for a in report(applied)] == [
        (a["target"], a["name"], a["kind"]) for a in report(preview)
    ]
    assert all(
        (home / target / "alpha/SKILL.md").read_text(encoding="utf-8")
        == "# alpha\n\nnew\n"
        for target in MAC
    )
    converged = run(repo, home, "--check")
    assert (converged.returncode, converged.stdout, converged.stderr) == (0, OK, "")


# Applies like the CLI, but pauses after staging its sources until `resume`
# exists, so a newer apply can start while this older one is in flight.
PAUSED_APPLY = """
import sys
import time
from pathlib import Path

scripts, staged, resume = sys.argv[1:]
sys.path.insert(0, scripts)
import install_skills

stage = install_skills.skill_sources


def paused(*args):
    sources = stage(*args)
    Path(staged).touch()
    while not Path(resume).exists():
        time.sleep(0.05)
    return sources


install_skills.skill_sources = paused
raise SystemExit(install_skills.main(["--profile", "mac"]))
"""


def test_overlapping_applies_leave_the_newest_tree_installed(
    sandbox: tuple[Path, Path], tmp_path: Path
) -> None:
    repo, home = sandbox
    driver, staged, resume = (
        tmp_path / name for name in ("apply.py", "staged", "resume")
    )
    driver.write_text(PAUSED_APPLY)
    older = subprocess.Popen(
        [sys.executable, str(driver), str(repo / "scripts"), str(staged), str(resume)],
        env={**os.environ, "HOME": str(home)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 30
        while not staged.exists():
            assert older.poll() is None, older.communicate()[1]
            assert time.monotonic() < deadline, "the older apply never staged"
            time.sleep(0.05)
        skill(repo / "authoring/content", "alpha", "new")
        with ThreadPoolExecutor(max_workers=1) as pool:
            newer = pool.submit(run, repo, home)
            # A newer apply that does not wait for the older one finishes here.
            with contextlib.suppress(TimeoutError):
                newer.result(timeout=2)
            resume.touch()
            _, errors = older.communicate(timeout=60)
            assert older.returncode == 0, errors
            assert newer.result(timeout=60).returncode == 0
    finally:
        resume.touch()
        older.kill()
    assert {
        (home / target / "alpha/SKILL.md").read_text(encoding="utf-8") for target in MAC
    } == {"# alpha\n\nnew\n"}


def test_every_private_package_installs_and_a_public_namesake_stops_the_install(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    missing = run(repo, home, "--private-root", str(repo / "absent"))
    assert missing.returncode == 1 and "private source" in missing.stderr
    assert not home.exists()
    root = repo / "_skills_private"
    private = skill(root / "knowledge", "secret", "private")
    skill(private / "references", "example")
    applied = run(repo, home)
    assert applied.returncode == 0, applied.stderr
    assert {a["name"] for a in report(applied)} == {"alpha", "secret"}
    assert all((home / target / "secret/SKILL.md").exists() for target in MAC)
    assert not (repo / "skills/secret").exists()
    skill(repo / "authoring/content", "gamma")
    skill(root / "content", "alpha", "private")
    skill(root / "content", "gamma", "private")
    shadowed = run(repo, home)
    assert (shadowed.returncode, shadowed.stdout) == (1, "")
    assert shadowed.stderr == failed(
        *(
            f"skill '{name}' is public and private; remove authoring/content/{name} "
            f"to keep it private, or delete {root / 'content' / name} to publish it, "
            "then rerun: just install-skills"
            for name in ("alpha", "gamma")
        )
    )
    assert not any((home / target / "gamma").exists() for target in MAC)
    shutil.rmtree(root / "content" / "alpha")
    shutil.rmtree(repo / "authoring/content/gamma")
    resolved = run(repo, home)
    assert (resolved.returncode, resolved.stderr) == (0, "")
    assert {
        (home / target / name / "SKILL.md").read_text(encoding="utf-8")
        for target in MAC
        for name in ("alpha", "gamma")
    } == {"# alpha\n\nold\n", "# gamma\n\nprivate\n"}


def test_a_worktree_installs_the_main_checkouts_private_skills(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    skill(repo / "_skills_private/content", "secret", "private")
    worktree = repo.parent / "worktree"
    subprocess.run(
        ["git", "worktree", "add", "-q", str(worktree)], cwd=repo, check=True
    )

    applied = run(worktree, home)

    assert applied.returncode == 0, applied.stderr
    assert {a["name"] for a in report(applied)} == {"alpha", "secret"}
    assert all(
        (home / target / "secret/SKILL.md").read_text(encoding="utf-8")
        == "# secret\n\nprivate\n"
        for target in MAC
    )
    assert not (worktree / "_skills_private").exists()


def test_private_skill_promotes_to_public_without_flags(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    private = skill(repo / "_skills_private/content", "secret", "private")
    assert run(repo, home).returncode == 0
    shutil.rmtree(private)
    skill(repo / "authoring/content", "secret", "public")
    promoted = run(repo, home)
    assert promoted.returncode == 0, promoted.stderr
    assert all(
        (home / target / "secret/SKILL.md").read_text(encoding="utf-8")
        == "# secret\n\npublic\n"
        for target in MAC
    )
    assert run(repo, home, "--check").returncode == 0


def test_private_skill_deleted_in_its_clone_leaves_every_target(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    private = repo / "_skills_private"
    subprocess.run(["git", "init", "-q", str(private)], check=True)
    retired = skill(private / "content", "retired")
    outer = skill(private / "content", "outer")
    # A nested reference with its own SKILL.md is part of outer, not a skill.
    skill(outer / "references", "nested")
    commit(private)
    assert run(repo, home).returncode == 0
    nested = skill(home / ".claude/skills", "nested")
    subprocess.run(["git", "rm", "-qr", "content/retired"], cwd=private, check=True)
    commit(private)

    result = run(repo, home)

    assert result.returncode == 0, result.stderr
    assert not retired.exists()
    assert not any((home / target / "retired").exists() for target in MAC)
    assert all((home / target / "outer/SKILL.md").is_file() for target in MAC)
    assert (nested / "SKILL.md").is_file()
    assert run(repo, home, "--check").returncode == 0


def test_removes_only_published_names_and_overwrites_edits(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "beta")
    skill(repo / "skills", "beta")
    commit(repo)
    assert run(repo, home).returncode == 0
    synced = skill(home / ".claude/skills/synced/cache", "docx")
    foreign = skill(home / ".claude/skills", "foreign")
    edited = home / ".claude/skills/alpha/SKILL.md"
    edited.write_text("edited\n", encoding="utf-8")
    subprocess.run(["git", "rm", "-qr", "authoring/content/beta"], cwd=repo, check=True)
    preview = report(run(repo, home, "--dry-run"))
    assert [(a["target"], a["kind"]) for a in preview if a["name"] == "beta"] == [
        (target, "remove") for target in MAC
    ]
    assert Counter(a["kind"] for a in preview) == {"update": 1, "remove": len(MAC)}
    assert run(repo, home).returncode == 0
    assert not any((home / target / "beta").exists() for target in MAC)
    assert edited.read_text(encoding="utf-8") == "# alpha\n\nold\n"
    assert (synced / "SKILL.md").exists() and (foreign / "SKILL.md").exists()


def test_uncommitted_public_skill_is_removed_after_its_source_goes(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    draft = skill(repo / "authoring/content", "draft")
    assert run(repo, home).returncode == 0
    shutil.rmtree(draft)
    assert run(repo, home).returncode == 0
    assert not any((home / target / "draft").exists() for target in MAC)


def test_a_skill_without_a_kind_installs_the_compiled_kind_unknown(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    source = repo / "authoring/content/alpha/SKILL.md"
    source.write_text('---\nname: "alpha"\n---\nnew\n', encoding="utf-8")
    assert run(repo, home).returncode == 0
    published = '---\nname: "alpha"\nkind: "unknown"\n---\nnew\n'
    assert (repo / "skills/alpha/SKILL.md").read_text(encoding="utf-8") == published
    assert all(
        (home / target / "alpha/SKILL.md").read_text(encoding="utf-8") == published
        for target in MAC
    )


def test_an_apply_deletes_folders_holding_only_caches_and_fails_on_other_leftovers(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    with (repo / ".gitignore").open("a") as ignore:
        ignore.write(".DS_Store\n.env\nnode_modules/\n.vscode/\n")
    skill(repo / "authoring", "solo")
    skill(repo / "skills", "solo")
    commit(repo)
    for path in (
        "authoring/retired/beta/__pycache__/beta.pyc",
        "authoring/content/gone/.DS_Store",
        "skills/retired/.DS_Store",
        "authoring/kept/.env",
        "authoring/solo/scripts/node_modules/dep.js",
    ):
        (repo / path).parent.mkdir(parents=True)
        (repo / path).write_text("ignored\n")
    (repo / "authoring/content/empty").mkdir()
    (repo / "authoring/linked/.vscode").mkdir(parents=True)
    (repo / "authoring/linked/.vscode/node_modules").symlink_to(home.parent)
    (repo / "authoring/fresh/draft").mkdir(parents=True)

    assert run(repo, home, "--dry-run").returncode == 0
    assert (repo / "authoring/retired").exists()
    applied = run(repo, home)
    assert (applied.returncode, applied.stdout) == (1, "")
    answer = json.loads(applied.stderr)
    assert answer["errors"] == [
        "installed, but authoring/kept holds only ignored files, such as "
        + "authoring/kept/.env; delete it once nothing in it is needed",
        "installed, but authoring/linked holds only ignored files, such as "
        + "authoring/linked/.vscode/node_modules; delete it once nothing in it is needed",
    ]
    assert ["add", "~/.claude/skills/solo"] in answer["changes"]
    assert {
        folder: (repo / folder).exists()
        for folder in (
            "authoring/retired",
            "authoring/content/gone",
            "skills/retired",
            "authoring/kept",
            "authoring/linked",
            "authoring/solo/scripts/node_modules",
            "authoring/content/empty",
            "authoring/fresh/draft",
        )
    } == {
        "authoring/retired": False,
        "authoring/content/gone": False,
        "skills/retired": False,
        "authoring/kept": True,
        "authoring/linked": True,
        "authoring/solo/scripts/node_modules": True,
        "authoring/content/empty": True,
        "authoring/fresh/draft": True,
    }


def test_an_apply_keeps_external_files_behind_a_category_symlink(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    retired = skill(repo / "authoring/retired", "gone")
    subprocess.run(["git", "add", "authoring"], cwd=repo, check=True)
    shutil.rmtree(retired.parent)
    with (repo / ".gitignore").open("a", encoding="utf-8") as ignore:
        ignore.write("/authoring/retired\n")
    cache = repo.parent / "external/personal/__pycache__/keep.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"external cache")
    link = repo / "authoring/retired"
    link.symlink_to(cache.parents[2], target_is_directory=True)

    applied = run(repo, home)

    assert (applied.returncode, applied.stderr) == (0, "")
    assert link.is_symlink()
    assert cache.read_bytes() == b"external cache"
    assert all((home / target / "alpha/SKILL.md").is_file() for target in MAC)


def test_a_leftover_the_apply_cannot_delete_fails_once_the_install_ran(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    cache = repo / "authoring/retired/__pycache__"
    cache.mkdir(parents=True)
    (cache / "beta.pyc").write_text("ignored\n")
    locked = repo / "authoring/sealed/locked"
    locked.mkdir(parents=True)
    sealed_cache = locked.parent / "__pycache__/old.pyc"
    sealed_cache.parent.mkdir()
    sealed_cache.write_text("ignored\n")
    cache.chmod(0o500)
    locked.chmod(0o000)
    try:
        applied = run(repo, home)
    finally:
        cache.chmod(0o700)
        locked.chmod(0o700)
    assert (applied.returncode, applied.stdout) == (1, "")
    assert json.loads(applied.stderr)["errors"] == [
        "installed, but could not delete authoring/retired: Permission denied; "
        + "delete it by hand",
        "installed, but could not delete authoring/sealed: Permission denied; "
        + "delete it by hand",
    ]
    assert sealed_cache.is_file()
    assert all((home / target / "alpha/SKILL.md").is_file() for target in MAC)


def test_a_file_saved_after_the_prune_scan_survives(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    cache = repo / "authoring/retired/package/scripts/__pycache__"
    cache.mkdir(parents=True)
    (cache / "old.pyc").write_bytes(b"cache")
    saved = cache.parent / "new-work.txt"
    driver = repo / "scripts/save_during_prune.py"
    driver.write_text(
        """\
from pathlib import Path
import install_skills

rmtree = install_skills.shutil.rmtree
retired = install_skills.compile_skills.AUTHORING / "retired"

def save(path, *args, **kwargs):
    if Path(path).is_relative_to(retired):
        (retired / "package/scripts/new-work.txt").write_text(
            "work saved during cleanup\\n", encoding="utf-8"
        )
    return rmtree(path, *args, **kwargs)

install_skills.shutil.rmtree = save
raise SystemExit(install_skills.main())
""",
        encoding="utf-8",
    )

    applied = run(repo, home, script=driver.name)

    assert (applied.returncode, applied.stdout) == (1, "")
    assert saved.read_text(encoding="utf-8") == "work saved during cleanup\n"
    assert json.loads(applied.stderr)["errors"] == [
        "installed, but could not delete authoring/retired: Directory not empty; "
        + "delete it by hand"
    ]
    assert not cache.exists()
    assert all((home / target / "alpha/SKILL.md").is_file() for target in MAC)


def test_shallow_clone_is_refused(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    shallow = repo.parent / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(shallow)],
        check=True,
    )
    refused = run(shallow, home, "--dry-run")
    assert refused.returncode == 1
    assert "git fetch --unshallow" in refused.stderr


def test_symlink_at_a_target_blocks_apply_and_fails_a_preview_too(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    elsewhere = skill(home / "elsewhere", "alpha")
    link = home / ".claude/skills/alpha"
    link.parent.mkdir(parents=True)
    link.symlink_to(elsewhere, target_is_directory=True)
    conflict = (
        "~/.claude/skills/alpha is a symlink or file; "
        "move it aside, then rerun: just install-skills"
    )

    blocked = run(repo, home)
    preview = run(repo, home, "--dry-run")

    assert (blocked.returncode, blocked.stdout) == (1, "")
    assert blocked.stderr == failed(conflict)
    assert not (home / ".agents").exists()
    assert (preview.returncode, preview.stdout) == (1, "")
    answer = json.loads(preview.stderr)
    assert answer["errors"] == [conflict]
    assert ["add", "~/.agents/skills/alpha"] in answer["changes"]


def test_om1_exclusion_and_inactive_mac_target(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "apple-mail")
    preview = run(repo, home, "--profile", "om1", "--dry-run")
    assert preview.returncode == 0
    assert {a["name"] for a in report(preview)} == {"alpha"}
    assert run(repo, home, "--profile", "om1").returncode == 0
    assert not (home / ".agents").exists()
    assert not any((home / target / "apple-mail").exists() for target in OM1)
    assert (home / ".codex/skills/alpha/SKILL.md").exists()


def test_target_parent_file_fails_before_any_copy(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    home.mkdir()
    (home / ".config").write_text("file", encoding="utf-8")
    result = run(repo, home, "--dry-run")
    assert result.returncode == 1
    assert "file ancestor" in result.stderr
    assert not (home / ".agents").exists()


def test_interrupted_swap_restores_previous_copy(tmp_path: Path) -> None:
    source = skill(tmp_path / "source", "alpha", "new")
    destination = skill(tmp_path / "home", "alpha", "old")
    original_rename = Path.rename

    def interrupt(path: Path, target: Path) -> Path:
        moved = original_rename(path, target)
        if path == destination:
            raise KeyboardInterrupt
        return moved

    with patch.object(Path, "rename", interrupt), pytest.raises(KeyboardInterrupt):
        replace(source, destination)
    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "# alpha\n\nold\n"


def test_commands_install_and_only_published_ones_are_removed(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    text = '---\ndescription: "Review it"\n---\n\nshared command'
    source = command(repo, "review", text)
    commit(repo)
    foreign = home / ".claude/commands/foreign.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("keep\n", encoding="utf-8")
    preview = report(run(repo, home, "--dry-run"))
    assert [
        (a["target"], a["name"], a["kind"]) for a in preview if a["name"] != "alpha"
    ] == [(".codex/skills", "review", "add")] + [
        (target, "review.md", "add") for target in COMMANDS
    ]
    assert run(repo, home).returncode == 0
    assert all(
        (home / target / "review.md").read_text(encoding="utf-8") == text + "\n"
        for target in COMMANDS
    )
    assert (home / ".codex/skills/review/SKILL.md").read_text(encoding="utf-8") == (
        '---\nname: "review"\ndescription: "Review it"\n---\n\nshared command\n'
    )
    assert run(repo, home, "--check").returncode == 0
    (home / ".claude/commands/review.md").write_text("local edit\n", encoding="utf-8")
    source.unlink()
    assert run(repo, home).returncode == 0
    assert not any((home / target / "review.md").exists() for target in COMMANDS)
    assert not (home / ".codex/skills/review").exists()
    assert foreign.read_text(encoding="utf-8") == "keep\n"


def test_a_command_retired_from_authoring_commands_is_still_removed(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    old = repo / "authoring/commands/legacy.md"
    old.parent.mkdir(parents=True)
    old.write_text("legacy\n", encoding="utf-8")
    commit(repo)
    old.unlink()
    commit(repo)
    for target in COMMANDS:
        (home / target).mkdir(parents=True)
        (home / target / "legacy.md").write_text("legacy\n", encoding="utf-8")
    assert run(repo, home).returncode == 0
    assert not any((home / target / "legacy.md").exists() for target in COMMANDS)


def test_om1_codex_directory_holds_skills_beside_commands(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    command(repo, "review")
    commit(repo)
    assert run(repo, home, "--profile", "om1").returncode == 0
    assert sorted(path.name for path in (home / ".codex/skills").iterdir()) == [
        "alpha",
        "review",
    ]
    checked = run(repo, home, "--profile", "om1", "--check", "-v")
    assert (checked.returncode, checked.stdout) == (0, OK)
    assert "~/.codex/skills: 2 of 2 current\n" in checked.stderr


def test_retired_command_targets_lose_only_published_commands(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    command(repo, "review")
    commit(repo)
    for target in RETIRED:
        (home / target).mkdir(parents=True)
        (home / target / "review.md").write_text("old\n", encoding="utf-8")
        (home / target / "mine.md").write_text("keep\n", encoding="utf-8")
    applied = run(repo, home, "--profile", "om1")
    assert applied.returncode == 0
    assert {("remove", target, "review.md") for target in RETIRED} <= {
        (a["kind"], a["target"], a["name"]) for a in report(applied)
    }
    for target in RETIRED:
        assert not (home / target / "review.md").exists()
        assert (home / target / "mine.md").read_text(encoding="utf-8") == "keep\n"
    assert run(repo, home, "--profile", "om1", "--check").returncode == 0


def test_retired_targets_reached_through_a_symlink_are_left_alone(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    command(repo, "review", "shared")
    commit(repo)
    # One links to a live target, the other to a checkout's command sources
    checkout = home / "checkout/commands"
    for directory in (home / ".claude/commands", checkout, home / ".codex"):
        directory.mkdir(parents=True)
    (checkout / "review.md").write_text("source\n", encoding="utf-8")
    (home / ".codex/prompts").symlink_to(home / ".claude/commands")
    (home / ".config/agents").mkdir(parents=True)
    (home / ".config/agents/commands").symlink_to(checkout)
    assert run(repo, home).returncode == 0
    assert run(repo, home).stdout == OK
    assert (home / ".claude/commands/review.md").read_text(encoding="utf-8") == (
        "shared\n"
    )
    assert (checkout / "review.md").read_text(encoding="utf-8") == "source\n"


def test_codex_skill_descriptions_follow_yaml_quoting(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    command(repo, "inner", '---\ndescription: Use "review"\n---\nbody')
    command(repo, "single", "---\ndescription: 'It''s here'\n---\nbody")
    command(repo, "escaped", '---\ndescription: "Say \\"hi\\""\n---\nbody')
    command(repo, "folded", "---\ndescription: >\n  long\n---\nbody")
    command(repo, "bare", "body")
    assert run(repo, home).returncode == 0
    headers = {
        name: (home / ".codex/skills" / name / "SKILL.md")
        .read_text(encoding="utf-8")
        .splitlines()[2]
        for name in ("inner", "single", "escaped", "folded", "bare")
    }
    assert headers == {
        "inner": 'description: "Use \\"review\\""',
        "single": 'description: "It\'s here"',
        "escaped": 'description: "Say \\"hi\\""',
        "folded": 'description: "folded"',
        "bare": 'description: "bare"',
    }


def test_a_command_named_like_a_skill_stops_before_writing(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    command(repo, "alpha")
    result = run(repo, home)
    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == failed(
        "command 'alpha' has the same name as a skill; rename "
        "commands/alpha.md, then rerun: just install-skills"
    )
    assert not home.exists()


def test_a_codex_directory_linked_to_a_skill_target_stops_before_writing(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    (home / ".agents/skills").mkdir(parents=True)
    (home / ".codex").mkdir()
    (home / ".codex/skills").symlink_to(home / ".agents/skills")
    result = run(repo, home)
    assert (result.returncode, result.stdout) == (1, "")
    assert "~/.codex/skills is the same directory as ~/.agents/skills" in result.stderr
    assert list((home / ".agents/skills").iterdir()) == []


def test_apply_and_preview_answer_each_change_and_check_counts_each_target(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "beta")
    command(repo, "hello")
    commit(repo)
    changes = sorted(
        [["add", f"~/{target}/{name}"] for target in MAC for name in ("alpha", "beta")]
        + [["add", f"~/{target}/hello.md"] for target in COMMANDS]
        + [["add", "~/.codex/skills/hello"]]
    )

    preview = run(repo, home, "-n")
    applied = run(repo, home)

    assert (preview.returncode, preview.stderr) == (0, "")
    assert (applied.returncode, applied.stderr) == (0, "")
    assert sorted(json.loads(preview.stdout)["changes"]) == changes
    assert applied.stdout == preview.stdout
    assert run(repo, home).stdout == OK
    # A caller from before this version still passes -q
    for flag in ("-q", "--quiet"):
        bridged = run(repo, home, flag)
        assert (bridged.returncode, bridged.stdout, bridged.stderr) == (0, OK, "")
    shutil.rmtree(home / ".claude/skills/beta")

    checked = run(repo, home, "--check", "-v")

    assert (checked.returncode, checked.stdout) == (1, "")
    assert checked.stderr.endswith(
        failed(
            "1 installed entries differ from the checkout; run: just install-skills",
            changes=[["add", "~/.claude/skills/beta"]],
        )
    )
    assert "~/.claude/skills: 1 of 2 current\n" in checked.stderr
    assert "~/.claude/commands: 1 of 1 current\n" in checked.stderr


def test_a_failure_midway_answers_the_entries_already_installed(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    blocked = home / ".claude/skills"
    blocked.mkdir(parents=True)
    blocked.chmod(0o500)
    try:
        result = run(repo, home)
    finally:
        blocked.chmod(0o700)

    assert (result.returncode, result.stdout) == (1, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    assert answer["errors"][0].startswith("PermissionError: ")
    done = [path for _, path in answer["changes"]]
    assert done, "the targets before ~/.claude/skills were installed"
    assert all((home / path[2:]).exists() for path in done)
    assert not any(path.startswith("~/.claude/skills/") for path in done)


def test_an_interrupt_during_the_prune_answers_the_entries_installed(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    # The installer, with its prune after the install interrupted
    (repo / "scripts/interrupted_install.py").write_text(
        "import sys\n"
        "import install_skills\n"
        "def interrupted():\n"
        "    raise KeyboardInterrupt\n"
        "install_skills.prune_leftovers = interrupted\n"
        "sys.exit(install_skills.main())\n"
    )

    result = run(repo, home, script="interrupted_install.py")

    assert (result.returncode, result.stdout) == (130, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    assert answer["errors"] == ["interrupted"]
    assert ["add", "~/.claude/skills/alpha"] in answer["changes"]
    assert (home / ".claude/skills/alpha/SKILL.md").is_file()


def test_an_apply_gives_up_with_75_when_another_holds_the_lock(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    lock = repo / ".git/install-skills.lock"
    with lock.open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        waited = run(repo, home, "--timeout", "1s")
        preview = run(repo, home, "--dry-run", "--timeout", "1s")

    assert (waited.returncode, waited.stdout) == (75, "")
    assert waited.stderr == failed(
        f"another run still holds {lock} after 1s",
        retry="just install-skills --profile mac --timeout 1s",
    )
    assert not home.exists()
    assert (preview.returncode, preview.stderr) == (0, ""), "a preview never waits"

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
from conftest import commit, exits, observe, skill
from install_skills import replace

MAC = (
    ".pi/agent/skills",
    ".agents/skills",
    ".claude/skills",
    ".config/opencode/skills",
    ".config/agents/skills",
)
OM1 = (".pi/agent/skills", ".codex/skills", ".claude/skills", ".config/opencode/skills")
MAC_COMMANDS = (
    ".claude/commands",
    ".pi/agent/prompts",
    ".codex/prompts",
    ".config/opencode/commands",
    ".config/agents/commands",
)


def command(repo: Path, name: str, body: str = "command") -> Path:
    path = repo / "authoring/commands" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")
    return path


def run(repo: Path, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["UV_CACHE_DIR"] = str(home.parent / "uv-cache")
    # Pin the host-dependent default; a later --profile in args wins.
    result = subprocess.run(
        [
            "uv",
            "run",
            str(repo / "scripts/install_skills.py"),
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
    observe("install_skills", result.returncode)
    return result


def report(result: subprocess.CompletedProcess[str]) -> list[dict]:
    return json.loads(result.stdout)["actions"]


@exits("install_skills", 0, 1)
def test_preview_apply_check_and_repeat_agree(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "alpha", "new")
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    assert {a["kind"] for a in report(preview)} == {"add"}
    assert not home.exists()
    assert (repo / "skills/alpha/SKILL.md").read_text(
        encoding="utf-8"
    ) == "# alpha\n\nold\n"
    assert run(repo, home, "--check", "--json").returncode == 1
    applied = run(repo, home, "--json")
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
    assert (converged.returncode, converged.stdout, converged.stderr) == (0, "", "")


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


def test_every_private_package_installs_and_duplicates_are_all_named(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    missing = run(repo, home, "--private-root", str(repo / "absent"))
    assert missing.returncode == 1 and "private source" in missing.stderr
    assert not home.exists()
    root = repo / "_skills_private"
    private = skill(root / "knowledge", "secret", "private")
    skill(private / "references", "example")
    applied = run(repo, home, "--json")
    assert applied.returncode == 0, applied.stderr
    assert {a["name"] for a in report(applied)} == {"alpha", "secret"}
    assert all((home / target / "secret/SKILL.md").exists() for target in MAC)
    assert not (repo / "skills/secret").exists()
    skill(repo / "authoring/content", "gamma")
    skill(root / "content", "alpha", "private")
    skill(root / "content", "gamma", "private")
    duplicate = run(repo, home, "--dry-run")
    assert duplicate.returncode == 1
    assert "skill 'alpha' is public and private" in duplicate.stderr
    assert "skill 'gamma' is public and private" in duplicate.stderr


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
    preview = report(run(repo, home, "--dry-run", "--json"))
    assert [(a["target"], a["kind"]) for a in preview if a["name"] == "beta"] == [
        (target, "remove") for target in MAC
    ]
    assert Counter(a["kind"] for a in preview) == {
        "current": len(MAC) - 1,
        "update": 1,
        "remove": len(MAC),
    }
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


@exits("install_skills", 0, 1)
def test_symlink_at_a_target_blocks_apply_and_a_preview_warns(
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
    assert blocked.stderr == f"error: {conflict}\n"
    assert not (home / ".agents").exists()
    assert preview.returncode == 0
    assert "add\t~/.agents/skills/alpha\n" in preview.stdout
    assert preview.stderr == f"warning: {conflict}\n"


def test_om1_exclusion_and_inactive_mac_target(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "apple-mail")
    preview = run(repo, home, "--profile", "om1", "--dry-run", "--json")
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
    source = command(repo, "review", "shared command")
    commit(repo)
    foreign = home / ".claude/commands/foreign.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("keep\n", encoding="utf-8")
    preview = report(run(repo, home, "--dry-run", "--json"))
    assert [(a["target"], a["kind"]) for a in preview if a["source"] == "command"] == [
        (target, "add") for target in MAC_COMMANDS
    ]
    assert run(repo, home).returncode == 0
    assert all(
        (home / target / "review.md").read_text(encoding="utf-8") == "shared command\n"
        for target in MAC_COMMANDS
    )
    assert run(repo, home, "--check").returncode == 0
    (home / ".claude/commands/review.md").write_text("local edit\n", encoding="utf-8")
    source.unlink()
    assert run(repo, home).returncode == 0
    assert not any((home / target / "review.md").exists() for target in MAC_COMMANDS)
    assert foreign.read_text(encoding="utf-8") == "keep\n"


def test_om1_preserves_inactive_mac_command_target(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    source = command(repo, "review", "old")
    assert run(repo, home, "--profile", "mac").returncode == 0
    source.write_text("new\n", encoding="utf-8")
    preview = report(run(repo, home, "--profile", "om1", "--dry-run", "--json"))
    assert not any(a["target"] == ".config/agents/commands" for a in preview)
    assert run(repo, home, "--profile", "om1").returncode == 0
    assert (home / ".config/agents/commands/review.md").read_text() == "old\n"
    assert (home / ".codex/prompts/review.md").read_text() == "new\n"


@exits("install_skills", 0, 1)
def test_apply_and_preview_print_one_line_per_change_and_check_counts_each_target(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "beta")
    command(repo, "hello")
    commit(repo)
    lines = sorted(
        [f"add\t~/{target}/{name}" for target in MAC for name in ("alpha", "beta")]
        + [f"add\t~/{target}/hello.md" for target in MAC_COMMANDS]
    )

    preview = run(repo, home, "-n")
    applied = run(repo, home)

    assert (preview.returncode, preview.stderr) == (0, "")
    assert (applied.returncode, applied.stderr) == (0, "")
    assert sorted(preview.stdout.splitlines()) == lines
    assert applied.stdout == preview.stdout
    assert run(repo, home).stdout == ""
    # A caller from before this version still passes -q
    assert (run(repo, home, "--quiet").returncode, run(repo, home, "-q").stdout) == (
        0,
        "",
    )
    shutil.rmtree(home / ".claude/skills/beta")

    checked = run(repo, home, "--check", "--json")

    assert (checked.returncode, checked.stdout) == (1, "")
    failure = json.loads(checked.stderr)
    assert failure["errors"] == [
        "1 installed entries differ from the checkout; run: just install-skills"
    ]
    targets = {t["target"]: t for t in failure["targets"]}
    assert targets[".claude/skills"] == {
        "target": ".claude/skills",
        "expected": 2,
        "current": 1,
        "counts": {"add": 1, "current": 1},
    }
    assert targets[".claude/commands"] == {
        "target": ".claude/commands",
        "expected": 1,
        "current": 1,
        "counts": {"current": 1},
    }


@exits("install_skills", 75)
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
    assert waited.stderr == (
        f"error: another run still holds {lock} after 1s\n"
        "retry: just install-skills --profile mac --timeout 1s\n"
    )
    assert not home.exists()
    assert (preview.returncode, preview.stderr) == (0, ""), "a preview never waits"

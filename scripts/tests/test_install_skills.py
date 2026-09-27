"""Installer behavior through its CLI with isolated repositories and homes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from install_skills import replace

SCRIPT = Path(__file__).parent.parent / "install_skills.py"
MAC = (
    ".pi/agent/skills",
    ".agents/skills",
    ".claude/skills",
    ".config/opencode/skills",
    ".config/agents/skills",
)
OM1 = (".pi/agent/skills", ".codex/skills", ".claude/skills", ".config/opencode/skills")


def skill(root: Path, name: str, body: str = "old") -> Path:
    package = root / name
    package.mkdir(parents=True, exist_ok=True)
    (package / "SKILL.md").write_text(f"# {name}\n\n{body}\n", encoding="utf-8")
    return package


def command(repo: Path, name: str, body: str = "command") -> Path:
    path = repo / "authoring/commands" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")
    subprocess.run(["git", "add", str(path.relative_to(repo))], cwd=repo, check=True)
    return path


@pytest.fixture
def sandbox(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in ("_common.py", "flatten_skills.py", "install_skills.py"):
        shutil.copy2(SCRIPT.parent / name, scripts / name)
    skill(repo / "authoring/content", "alpha")
    skill(repo / "skills", "alpha")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "add", "authoring/content/alpha/SKILL.md", "skills/alpha/SKILL.md"],
        cwd=repo,
        check=True,
    )
    return repo, tmp_path / "home"


def run(repo: Path, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_STATE_HOME"] = str(home / "state")
    env["UV_CACHE_DIR"] = str(home.parent / "uv-cache")
    return subprocess.run(
        ["uv", "run", str(repo / "scripts/install_skills.py"), *args],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def report(result: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(result.stdout)


def manifest(home: Path) -> dict:
    return json.loads(
        (home / "state/install-skills/manifest.json").read_text(encoding="utf-8")
    )


def test_preview_apply_check_and_repeat_agree(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "alpha", "new")
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    assert {a["kind"] for a in report(preview)["actions"]} == {"add"}
    assert not home.exists()
    assert (repo / "skills/alpha/SKILL.md").read_text(
        encoding="utf-8"
    ) == "# alpha\n\nold\n"
    assert run(repo, home, "--check", "--json").returncode == 1
    applied = run(repo, home, "--json")
    assert applied.returncode == 0
    assert [
        (a["target"], a["name"], a["kind"]) for a in report(applied)["actions"]
    ] == [(a["target"], a["name"], a["kind"]) for a in report(preview)["actions"]]
    assert all(
        (home / target / "alpha/SKILL.md").read_text(encoding="utf-8")
        == "# alpha\n\nnew\n"
        for target in MAC
    )
    assert all(
        a["kind"] == "current"
        for a in report(run(repo, home, "--check", "--json"))["actions"]
    )
    summary = run(repo, home, "--check")
    assert summary.returncode == 0
    assert "skills=1, commands=0;" in summary.stdout
    assert all(
        a["kind"] == "current" for a in report(run(repo, home, "--json"))["actions"]
    )


def test_v1_migration_preserves_inactive_targets_and_private_omission(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    first = run(repo, home, "--profile", "om1")
    assert first.returncode == 0, first.stderr
    old = manifest(home)
    old["version"] = 1
    old["targets"] = {
        target: {name: record["digest"] for name, record in records.items()}
        for target, records in old["targets"].items()
    }
    private = skill(home / ".codex/skills", "hidden")
    old["targets"][".codex/skills"]["hidden"] = "a" * 64
    old["targets"][".agents/skills"] = {"other": "b" * 64}
    path = home / "state/install-skills/manifest.json"
    path.write_text(json.dumps(old), encoding="utf-8")
    result = run(repo, home, "--profile", "mac", "--json")
    assert result.returncode == 0, result.stderr
    new = manifest(home)
    assert new["version"] == 2
    assert "other" not in new["targets"][".agents/skills"]
    assert new["targets"][".codex/skills"]["hidden"] == {
        "source": "public",
        "digest": "a" * 64,
    }
    assert private.exists()
    assert all(a["target"] != ".codex/skills" for a in report(result)["actions"])
    # Once source-aware, omitted private ownership is preserved on an active target too.
    new["targets"][".claude/skills"]["hidden"] = {
        "source": "private",
        "digest": "c" * 64,
    }
    skill(home / ".claude/skills", "hidden")
    path.write_text(json.dumps(new), encoding="utf-8")
    assert run(repo, home, "--profile", "mac").returncode == 0
    assert (home / ".claude/skills/hidden/SKILL.md").exists()
    assert manifest(home)["targets"][".claude/skills"]["hidden"]["source"] == "private"


def test_private_selection_missing_duplicate_and_nested_reference(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    missing = run(repo, home, "--private", "secret")
    assert missing.returncode == 1 and "private source" in missing.stderr
    assert not home.exists()
    root = repo / "_skills_private"
    private = skill(root / "knowledge", "secret", "private")
    skill(private / "references", "example")
    selected = run(repo, home, "--private", "secret", "--json")
    assert selected.returncode == 0, selected.stderr
    assert {a["name"] for a in report(selected)["actions"]} == {"alpha", "secret"}
    assert manifest(home)["targets"][".claude/skills"]["secret"]["source"] == "private"
    assert not (repo / "skills/secret").exists()
    assert run(repo, home, "--json").returncode == 0
    assert (home / ".claude/skills/secret/SKILL.md").exists()
    skill(root / "content", "alpha", "private")
    duplicate = run(repo, home, "--private", "alpha", "--json")
    assert duplicate.returncode == 1 and "duplicate selected skill" in duplicate.stderr
    assert not (repo / "skills/secret").exists()
    assert run(repo, home, "--private", "absent").returncode == 1


def test_om1_exclusion_and_inactive_mac_target(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "apple-mail")
    subprocess.run(
        ["git", "add", "authoring/content/apple-mail/SKILL.md"], cwd=repo, check=True
    )
    preview = run(repo, home, "--profile", "om1", "--dry-run", "--json")
    assert preview.returncode == 0
    assert {a["name"] for a in report(preview)["actions"]} == {"alpha"}
    assert run(repo, home, "--profile", "om1").returncode == 0
    assert not (home / ".agents").exists()
    assert not any((home / target / "apple-mail").exists() for target in OM1)
    assert (home / ".codex/skills/alpha/SKILL.md").exists()


def test_conflicts_and_selected_owned_removal(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    foreign = skill(home / ".claude/skills", "alpha", "foreign")
    conflict = run(repo, home, "--dry-run", "--json")
    assert conflict.returncode == 0
    assert any(a["kind"] == "conflict" for a in report(conflict)["actions"])
    assert run(repo, home, "--check").returncode == 1
    summary = run(repo, home, "--dry-run")
    assert len(summary.stdout.splitlines()) == 1
    assert "conflict=1" in summary.stdout
    detail = run(repo, home, "--dry-run", "--verbose")
    assert "conflict: ~/.claude/skills/alpha" in detail.stdout
    assert run(repo, home, "--json").returncode == 1
    assert (
        foreign.joinpath("SKILL.md").read_text(encoding="utf-8")
        == "# alpha\n\nforeign\n"
    )
    assert run(repo, home, "--force").returncode == 0
    private = skill(repo / "_skills_private/content", "secret")
    assert run(repo, home, "--private", "secret").returncode == 0
    checksum = manifest(home)["targets"][".claude/skills"]["secret"]["digest"]
    shutil.rmtree(private)
    assert run(repo, home).returncode == 0
    assert (home / ".claude/skills/secret/SKILL.md").exists()
    assert run(repo, home, "--retire-private", "secret:" + "0" * 64).returncode == 1
    assert run(repo, home, "--retire-private", f"secret:{checksum}").returncode == 0
    assert not (home / ".claude/skills/secret").exists()


def test_public_removal_and_edited_copy(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    skill(repo / "authoring/content", "beta")
    subprocess.run(
        ["git", "add", "authoring/content/beta/SKILL.md"], cwd=repo, check=True
    )
    assert run(repo, home).returncode == 0
    (home / ".claude/skills/alpha/SKILL.md").write_text("edited\n", encoding="utf-8")
    assert run(repo, home, "--check").returncode == 1
    assert run(repo, home).returncode == 1
    assert run(repo, home, "--force").returncode == 0
    (repo / "authoring/content/beta/SKILL.md").unlink()
    subprocess.run(
        ["git", "add", "-u", "authoring/content/beta/SKILL.md"], cwd=repo, check=True
    )
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    assert sum(a["kind"] == "remove" for a in report(preview)["actions"]) == len(MAC)
    assert run(repo, home).returncode == 0
    assert not (home / ".claude/skills/beta").exists()


def test_repeat_after_partial_install_finishes_remaining_targets(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    assert run(repo, home).returncode == 0
    skill(repo / "authoring/content", "alpha", "new")
    # A prior interrupted apply already copied this target but did not save ownership.
    skill(home / ".claude/skills", "alpha", "new")
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    assert sum(a["kind"] == "current" for a in report(preview)["actions"]) == 1
    assert sum(a["kind"] == "update" for a in report(preview)["actions"]) == 4
    assert run(repo, home).returncode == 0
    assert run(repo, home, "--check").returncode == 0


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
    assert not (home / "state").exists()


def test_manifest_parent_file_fails_before_any_copy(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    home.mkdir()
    (home / "state").write_text("file", encoding="utf-8")
    result = run(repo, home)
    assert result.returncode == 1
    assert "manifest parent" in result.stderr
    assert not (home / ".agents").exists()


def test_private_retirement_allows_unowned_selected_targets(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    assert run(repo, home).returncode == 0
    private = skill(home / ".claude/skills", "secret")
    path = home / "state/install-skills/manifest.json"
    saved = manifest(home)
    from install_skills import digest

    checksum = digest(private)
    saved["targets"][".claude/skills"]["secret"] = {
        "source": "private",
        "digest": checksum,
    }
    path.write_text(json.dumps(saved), encoding="utf-8")
    preview = run(
        repo, home, "--retire-private", f"secret:{checksum}", "--dry-run", "--json"
    )
    assert preview.returncode == 0
    assert [
        (a["target"], a["kind"])
        for a in report(preview)["actions"]
        if a["name"] == "secret"
    ] == [(".claude/skills", "remove")]
    assert run(repo, home, "--retire-private", f"secret:{checksum}").returncode == 0
    assert not private.exists()


def test_private_skill_promotes_to_public_with_matching_retirement(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    private = skill(repo / "_skills_private/content", "secret", "private")
    assert run(repo, home, "--private", "secret").returncode == 0
    checksum = manifest(home)["targets"][".claude/skills"]["secret"]["digest"]
    skill(repo / "authoring/content", "secret", "public")
    subprocess.run(
        ["git", "add", "authoring/content/secret/SKILL.md"], cwd=repo, check=True
    )

    missing = run(repo, home)
    assert missing.returncode == 1
    assert "source ownership differs" in missing.stderr
    wrong = run(repo, home, "--retire-private", "secret:" + "0" * 64)
    assert wrong.returncode == 1
    assert "lacks matching ownership evidence" in wrong.stderr

    installed = home / ".claude/skills/secret/SKILL.md"
    installed.write_text("edited\n", encoding="utf-8")
    edited = run(repo, home, "--retire-private", f"secret:{checksum}", "--json")
    assert edited.returncode == 1
    assert edited.stdout, edited.stderr
    assert any(
        action["target"] == ".claude/skills"
        and action["name"] == "secret"
        and action["kind"] == "conflict"
        for action in report(edited)["actions"]
    )
    assert installed.read_text(encoding="utf-8") == "edited\n"

    shutil.copy2(private / "SKILL.md", installed)
    promoted = run(repo, home, "--retire-private", f"secret:{checksum}")
    assert promoted.returncode == 0, promoted.stderr
    assert all(
        (home / target / "secret/SKILL.md").read_text(encoding="utf-8")
        == "# secret\n\npublic\n"
        for target in MAC
    )
    records = manifest(home)["targets"]
    assert all(records[target]["secret"]["source"] == "public" for target in MAC)
    assert run(repo, home, "--check").returncode == 0


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


def test_invalid_manifest_and_help(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    path = home / "state/install-skills/manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        '{"version":2,"targets":{".claude/skills":{"alpha":{"source":"private","digest":"bad"}}}}',
        encoding="utf-8",
    )
    result = run(repo, home, "--dry-run")
    assert result.returncode == 1 and "invalid manifest ownership" in result.stderr
    assert not (home / ".claude").exists()
    help_text = run(repo, home, "--help")
    assert help_text.returncode == 0
    for option in ("--profile", "--private", "--retire-private", "--check", "--json"):
        assert option in help_text.stdout


def test_command_preview_apply_adoption_and_repeat(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    source = command(repo, "review", "shared command")
    adopted = home / ".claude/commands/review.md"
    adopted.parent.mkdir(parents=True)
    shutil.copy2(source, adopted)
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    command_actions = [
        a for a in report(preview)["actions"] if a["source"] == "command"
    ]
    assert len(command_actions) == 5
    assert {a["kind"] for a in command_actions} == {"add", "adopt"}
    assert run(repo, home, "--check").returncode == 1
    applied = run(repo, home, "--json")
    assert applied.returncode == 0
    assert [
        (a["target"], a["kind"])
        for a in report(applied)["actions"]
        if a["source"] == "command"
    ] == [(a["target"], a["kind"]) for a in command_actions]
    for target in (
        ".claude/commands",
        ".pi/agent/prompts",
        ".codex/prompts",
        ".config/opencode/commands",
        ".config/agents/commands",
    ):
        assert (home / target / "review.md").read_text(
            encoding="utf-8"
        ) == "shared command\n"
        assert "review.md" in manifest(home)["commands"][target]
    assert run(repo, home, "--check").returncode == 0
    assert all(
        a["kind"] == "current" for a in report(run(repo, home, "--json"))["actions"]
    )


def test_command_conflict_force_and_owned_removal(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    source = command(repo, "review", "shared command")
    foreign = home / ".claude/commands/foreign.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("keep\n", encoding="utf-8")
    assert run(repo, home).returncode == 0
    edited = home / ".claude/commands/review.md"
    edited.write_text("local edit\n", encoding="utf-8")
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    assert any(
        a["kind"] == "conflict" and a["source"] == "command"
        for a in report(preview)["actions"]
    )
    assert run(repo, home).returncode == 1
    assert edited.read_text(encoding="utf-8") == "local edit\n"
    assert run(repo, home, "--force").returncode == 0
    assert edited.read_text(encoding="utf-8") == "shared command\n"
    source.unlink()
    subprocess.run(
        ["git", "add", "-u", "authoring/commands/review.md"], cwd=repo, check=True
    )
    removal = run(repo, home, "--dry-run", "--json")
    assert removal.returncode == 0
    assert (
        sum(
            a["kind"] == "remove" and a["source"] == "command"
            for a in report(removal)["actions"]
        )
        == 5
    )
    assert run(repo, home).returncode == 0
    assert not edited.exists()
    assert foreign.read_text(encoding="utf-8") == "keep\n"


def test_om1_preserves_inactive_mac_command_target(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    source = command(repo, "review", "old")
    assert run(repo, home, "--profile", "mac").returncode == 0
    source.write_text("new\n", encoding="utf-8")
    preview = run(repo, home, "--profile", "om1", "--dry-run", "--json")
    assert preview.returncode == 0
    assert not any(
        action["target"] == ".config/agents/commands"
        for action in report(preview)["actions"]
    )
    assert run(repo, home, "--profile", "om1").returncode == 0
    assert (home / ".config/agents/commands/review.md").read_text() == "old\n"
    assert ".config/agents/commands" in manifest(home)["commands"]
    assert (home / ".codex/prompts/review.md").read_text() == "new\n"


def test_force_removes_edited_owned_command_with_removed_source(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    source = command(repo, "review", "old")
    assert run(repo, home).returncode == 0
    owned = home / ".claude/commands/review.md"
    owned.write_text("local edit\n", encoding="utf-8")
    foreign = home / ".claude/commands/foreign.md"
    foreign.write_text("keep\n", encoding="utf-8")
    source.unlink()
    subprocess.run(
        ["git", "add", "-u", "authoring/commands/review.md"], cwd=repo, check=True
    )
    preview = run(repo, home, "--dry-run", "--json")
    assert preview.returncode == 0
    assert any(
        action["kind"] == "conflict" and action["target"] == ".claude/commands"
        for action in report(preview)["actions"]
    )
    assert run(repo, home).returncode == 1
    assert owned.read_text() == "local edit\n"
    assert run(repo, home, "--force").returncode == 0
    assert not owned.exists()
    assert foreign.read_text() == "keep\n"

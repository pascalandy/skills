"""Installer behavior through its CLI with isolated repositories and homes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections import Counter
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
    return subprocess.run(
        ["uv", "run", str(repo / "scripts/install_skills.py"), *args],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def report(result: subprocess.CompletedProcess[str]) -> list[dict]:
    return json.loads(result.stdout)["actions"]


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
    summary = run(repo, home, "--check")
    assert summary.returncode == 0
    assert "skills=1, commands=0;" in summary.stdout


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


def test_symlink_at_a_target_blocks_apply(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    elsewhere = skill(home / "elsewhere", "alpha")
    link = home / ".claude/skills/alpha"
    link.parent.mkdir(parents=True)
    link.symlink_to(elsewhere, target_is_directory=True)
    blocked = run(repo, home, "--verbose")
    assert blocked.returncode == 1
    assert (
        "conflict: ~/.claude/skills/alpha (~/.claude/skills/alpha is a symlink or file)"
        in blocked.stdout
    )
    assert not (home / ".agents").exists()


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

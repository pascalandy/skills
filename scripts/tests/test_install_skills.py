"""Behavior of just install-skills: ownership, drift, removal, and the CLI surface."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from _common import ScriptError
from install_skills import SOURCE, TARGETS, install, replace

SCRIPT = Path(__file__).parent.parent / "install_skills.py"
TIMEOUT = 60  # seconds
DIRS = len(TARGETS)


def run(
    *args: str, home: Path, script: Path = SCRIPT
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_STATE_HOME"] = str(home / "state")
    return subprocess.run(
        ["uv", "run", str(script), *args],
        check=False,  # tests assert on returncode themselves
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=TIMEOUT,
    )


def write_skill(root: Path, name: str, body: str = "body") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"# {name}\n\n{body}\n", encoding="utf-8")
    return skill


@pytest.fixture
def source(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    write_skill(root, "alpha")
    write_skill(root, "beta")
    return root


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return tmp_path / "home"


def sync(
    source: Path, home: Path, *, dry_run: bool = False, force: bool = False
) -> str:
    return install(
        source, home, home / "state" / "manifest.json", dry_run=dry_run, force=force
    )


def test_first_install_copies_every_skill_into_every_target(
    source: Path, home: Path
) -> None:
    summary = sync(source, home)
    assert (
        summary
        == f"ok: 2 skills, {DIRS} agent dirs; {2 * DIRS} added, 0 updated, 0 removed, 0 adopted"
    )
    for target in TARGETS:
        assert (home / target / "alpha" / "SKILL.md").read_text(encoding="utf-8") == (
            "# alpha\n\nbody\n"
        )


def test_second_install_changes_nothing(source: Path, home: Path) -> None:
    sync(source, home)
    summary = sync(source, home)
    assert (
        summary
        == f"ok: 2 skills, {DIRS} agent dirs; 0 added, 0 updated, 0 removed, 0 adopted"
    )


def test_source_change_updates_installed_copies(source: Path, home: Path) -> None:
    sync(source, home)
    (source / "alpha" / "SKILL.md").write_text("changed\n", encoding="utf-8")
    summary = sync(source, home)
    assert (
        summary
        == f"ok: 2 skills, {DIRS} agent dirs; 0 added, {DIRS} updated, 0 removed, 0 adopted"
    )
    for target in TARGETS:
        assert (home / target / "alpha" / "SKILL.md").read_text(encoding="utf-8") == (
            "changed\n"
        )


def test_interrupt_after_moving_destination_restores_previous_copy(
    source: Path, home: Path
) -> None:
    destination = home / ".claude/skills/alpha"
    shutil.copytree(source / "alpha", destination)
    (destination / "SKILL.md").write_text("keep me\n", encoding="utf-8")
    original_rename = Path.rename

    def interrupt_after_move(path: Path, target: Path) -> Path:
        moved = original_rename(path, target)
        if path == destination:
            raise KeyboardInterrupt
        return moved

    with (
        patch.object(Path, "rename", interrupt_after_move),
        pytest.raises(KeyboardInterrupt),
    ):
        replace(source / "alpha", destination)

    assert (destination / "SKILL.md").read_text(encoding="utf-8") == "keep me\n"


def test_dry_run_writes_nothing(source: Path, home: Path) -> None:
    summary = sync(source, home, dry_run=True)
    assert summary == (
        f"dry run: 2 skills, {DIRS} agent dirs; {2 * DIRS} to add, 0 to update, 0 to remove, 0 to adopt"
    )
    assert not home.exists()


def test_identical_copy_from_elsewhere_is_adopted(source: Path, home: Path) -> None:
    for target in TARGETS:
        shutil.copytree(source / "alpha", home / target / "alpha")
    summary = sync(source, home)
    assert (
        summary
        == f"ok: 2 skills, {DIRS} agent dirs; {DIRS} added, 0 updated, 0 removed, {DIRS} adopted"
    )
    manifest = json.loads(
        (home / "state" / "manifest.json").read_text(encoding="utf-8")
    )
    assert sorted(manifest["targets"][".claude/skills"]) == ["alpha", "beta"]


def test_differing_copy_from_elsewhere_stops_the_run(source: Path, home: Path) -> None:
    foreign = write_skill(home / ".claude/skills", "alpha", body="someone else's")
    with pytest.raises(ScriptError) as raised:
        sync(source, home)
    assert str(raised.value) == (
        "~/.claude/skills/alpha differs from skills/alpha and was not installed "
        "by this script; rerun with --force to replace it"
    )
    assert (foreign / "SKILL.md").read_text(encoding="utf-8") == (
        "# alpha\n\nsomeone else's\n"
    )
    assert not (home / ".agents/skills").exists()


def test_force_replaces_a_differing_copy(source: Path, home: Path) -> None:
    write_skill(home / ".claude/skills", "alpha", body="someone else's")
    sync(source, home, force=True)
    installed = home / ".claude/skills/alpha/SKILL.md"
    assert installed.read_text(encoding="utf-8") == "# alpha\n\nbody\n"


def test_edited_install_stops_the_run(source: Path, home: Path) -> None:
    sync(source, home)
    installed = home / ".claude/skills/alpha/SKILL.md"
    installed.write_text("edited in place\n", encoding="utf-8")
    with pytest.raises(ScriptError) as raised:
        sync(source, home)
    assert str(raised.value) == (
        "~/.claude/skills/alpha was edited after the last install; "
        "move the edit into authoring/ or rerun with --force"
    )
    assert installed.read_text(encoding="utf-8") == "edited in place\n"


def test_runtime_artifacts_do_not_count_as_edits(source: Path, home: Path) -> None:
    sync(source, home)
    installed = home / ".claude/skills/alpha"
    for name in (
        "node_modules",
        ".mypy_cache",
        ".cache",
        ".turbo",
        "venv",
        "coverage",
        "dist",
        "build",
    ):
        artifact = installed / name / "result"
        artifact.parent.mkdir()
        artifact.write_text("generated\n", encoding="utf-8")
    for name in (".coverage", ".coverage.123", "app.tsbuildinfo"):
        (installed / name).write_text("generated\n", encoding="utf-8")
    summary = sync(source, home)
    assert (
        summary
        == f"ok: 2 skills, {DIRS} agent dirs; 0 added, 0 updated, 0 removed, 0 adopted"
    )


def test_retired_skill_is_removed_and_other_skills_stay(
    source: Path, home: Path
) -> None:
    sync(source, home)
    mine = write_skill(home / ".claude/skills", "mine")
    shutil.rmtree(source / "beta")
    summary = sync(source, home)
    assert (
        summary
        == f"ok: 1 skills, {DIRS} agent dirs; 0 added, 0 updated, {DIRS} removed, 0 adopted"
    )
    assert not any((home / target / "beta").exists() for target in TARGETS)
    assert (mine / "SKILL.md").is_file()


def test_retired_skill_in_shared_target_is_removed_once(
    source: Path, home: Path
) -> None:
    canonical = home / ".agents/skills"
    canonical.mkdir(parents=True)
    alias = home / ".config/agents/skills"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(canonical, target_is_directory=True)

    sync(source, home)
    shutil.rmtree(source / "beta")

    summary = sync(source, home)
    assert (
        summary
        == "ok: 1 skills, 4 agent dirs; 0 added, 0 updated, 4 removed, 0 adopted"
    )
    assert not (canonical / "beta").exists()
    manifest = json.loads((home / "state/manifest.json").read_text(encoding="utf-8"))
    assert (
        manifest["targets"][".agents/skills"]
        == manifest["targets"][".config/agents/skills"]
    )


def test_cli_dry_run_reads_home_and_prints_one_line(tmp_path: Path) -> None:
    skill_count = len(list(SOURCE.glob("*/SKILL.md")))
    result = run("--dry-run", home=tmp_path)
    assert result.returncode == 0
    assert result.stdout == (
        f"dry run: {skill_count} skills, {DIRS} agent dirs; "
        f"{skill_count * DIRS} to add, 0 to update, 0 to remove, 0 to adopt\n"
    )
    assert not (tmp_path / ".claude").exists()


def test_cli_preview_matches_install_from_current_authoring(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in ("_common.py", "flatten_skills.py", "install_skills.py"):
        shutil.copy2(SCRIPT.parent / name, scripts / name)

    write_skill(repo / "authoring/devtools", "alpha", body="new")
    generated = write_skill(repo / "skills", "alpha", body="old")
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=10)
    subprocess.run(
        ["git", "add", "authoring/devtools/alpha/SKILL.md"],
        cwd=repo,
        check=True,
        timeout=10,
    )
    home = tmp_path / "home"
    installed = home / ".agents/skills/alpha"
    manifest = home / "state/install-skills/manifest.json"
    install(generated.parent, home, manifest, dry_run=False, force=False)
    original_manifest = manifest.read_text(encoding="utf-8")

    result = run("--dry-run", home=home, script=scripts / "install_skills.py")

    assert result.returncode == 0
    assert result.stdout == (
        "dry run: 1 skills, 5 agent dirs; 0 to add, 5 to update, "
        "0 to remove, 0 to adopt\n"
    )
    assert (generated / "SKILL.md").read_text(encoding="utf-8") == ("# alpha\n\nold\n")
    assert (installed / "SKILL.md").read_text(encoding="utf-8") == ("# alpha\n\nold\n")
    assert manifest.read_text(encoding="utf-8") == original_manifest

    applied = run(home=home, script=scripts / "install_skills.py")

    assert applied.returncode == 0
    assert applied.stdout == (
        "ok: 1 skills, 5 agent dirs; 0 added, 5 updated, 0 removed, 0 adopted\n"
    )
    assert (generated / "SKILL.md").read_text(encoding="utf-8") == ("# alpha\n\nnew\n")
    assert (installed / "SKILL.md").read_text(encoding="utf-8") == ("# alpha\n\nnew\n")


def test_cli_unreadable_manifest_reports_error_and_hint(tmp_path: Path) -> None:
    manifest = tmp_path / "state" / "install-skills" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("not json", encoding="utf-8")
    result = run("--dry-run", home=tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith(f"error: cannot read manifest {manifest}: ")
    assert result.stderr.endswith("\nrerun with --verbose for details\n")


def test_cli_unknown_flag_is_usage_error(tmp_path: Path) -> None:
    result = run("--no-such-flag", home=tmp_path)
    assert result.returncode == 2
    assert "usage: just install-skills" in result.stderr

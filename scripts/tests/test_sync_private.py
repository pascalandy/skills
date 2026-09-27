"""The private clone through its CLI, with bare repositories standing in for GitHub."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import GIT_IDENTITY, SCRIPTS, commit, private_remote, skill


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def checkout(parent: Path, name: str) -> Path:
    """A public checkout whose origin is skills.git, as on each machine."""
    repo = parent / name
    subprocess.run(
        ["git", "clone", "-q", str(parent / "skills.git"), str(repo)], check=True
    )
    return repo


@pytest.fixture
def machines(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Two public checkouts of skills.git and the private remote beside it."""
    public = tmp_path / "public"
    (public / "scripts").mkdir(parents=True)
    for name in ("_common.py", "sync_private.py"):
        shutil.copy2(SCRIPTS / name, public / "scripts" / name)
    (public / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(public)], check=True)
    commit(public)
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(public), str(tmp_path / "skills.git")],
        check=True,
    )
    return (
        checkout(tmp_path, "one"),
        checkout(tmp_path, "two"),
        private_remote(tmp_path),
    )


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_IDENTITY, "HOME": str(repo.parent / "home")}
    env.pop("XDG_CONFIG_HOME", None)
    return subprocess.run(
        ["uv", "run", str(repo / "scripts/sync_private.py"), *args],
        check=False,
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def quiet(result: subprocess.CompletedProcess[str]) -> tuple[int, str, str]:
    return result.returncode, result.stdout, result.stderr


def test_clones_then_saves_edits_every_machine_receives(
    machines: tuple[Path, Path, Path],
) -> None:
    one, two, remote = machines

    assert quiet(run(one)) == (0, "", "")
    assert quiet(run(two)) == (0, "", "")
    (one / "_skills_private/content/secret/SKILL.md").write_text("from one\n")
    skill(one / "_skills_private/content", "added")
    assert quiet(run(one)) == (0, "", "")
    assert quiet(run(two)) == (0, "", "")

    received = two / "_skills_private/content"
    assert (received / "secret/SKILL.md").read_text() == "from one\n"
    assert (received / "added/SKILL.md").is_file()
    assert git(remote, "log", "-1", "--format=%s").startswith(
        "🧰 skill: private: save edits from "
    )
    assert git(one, "status", "--porcelain") == ""


def test_conflicting_edits_stop_with_the_edit_kept_as_a_commit(
    machines: tuple[Path, Path, Path],
) -> None:
    one, two, remote = machines
    for repo in (one, two):
        assert run(repo).returncode == 0
    (one / "_skills_private/content/secret/SKILL.md").write_text("from one\n")
    assert run(one).returncode == 0
    secret = two / "_skills_private/content/secret/SKILL.md"
    secret.write_text("from two\n")

    result = run(two)

    assert result.returncode == 1
    assert "private edits on " in result.stderr
    assert "conflict with GitHub" in result.stderr
    assert secret.read_text() == "from two\n"
    assert git(two / "_skills_private", "status", "--porcelain") == ""
    assert not (two / "_skills_private/.git/rebase-merge").exists()
    assert git(remote, "show", "main:content/secret/SKILL.md") == "from one"


def test_leaves_a_folder_that_is_not_a_clone_untouched(
    machines: tuple[Path, Path, Path],
) -> None:
    one, _, _ = machines
    kept = skill(one / "_skills_private/content", "local") / "SKILL.md"

    result = run(one)

    assert result.returncode == 1
    assert "is not a clone of the private repository" in result.stderr
    assert kept.read_text() == "# local\n\nold\n"
    assert not (one / "_skills_private/.git").exists()


def test_dry_run_names_the_clone_and_changes_nothing(
    machines: tuple[Path, Path, Path],
) -> None:
    one, _, remote = machines

    result = run(one, "--dry-run")

    assert quiet(result) == (
        0,
        f"would clone {remote} into {one / '_skills_private'}\n",
        "",
    )
    assert not (one / "_skills_private").exists()

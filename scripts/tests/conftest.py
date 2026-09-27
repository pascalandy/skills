"""Isolated repositories for the installer and discovery CLIs."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent


def skill(root: Path, name: str, body: str = "old") -> Path:
    package = root / name
    package.mkdir(parents=True, exist_ok=True)
    (package / "SKILL.md").write_text(f"# {name}\n\n{body}\n", encoding="utf-8")
    return package


def commit(repo: Path) -> None:
    """Stage everything and commit it, so git history publishes the names."""
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "publish",
        ],
        cwd=repo,
        check=True,
    )


@pytest.fixture
def sandbox(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in (
        "_common.py",
        "flatten_skills.py",
        "install_skills.py",
        "discover_skills.py",
    ):
        shutil.copy2(SCRIPTS / name, scripts / name)
    (repo / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    skill(repo / "authoring/content", "alpha")
    skill(repo / "skills", "alpha")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    commit(repo)
    return repo, tmp_path / "home"

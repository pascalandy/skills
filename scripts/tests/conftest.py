"""Isolated repositories for the installer, discovery, and sync CLIs."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent
# A child given a scratch HOME, in a terminal without the XDG variables, would
# make mise's shims, such as uv, read ~/.config/mise/config.toml as an untrusted
# project config, or look up tool versions on GitHub and warn on stderr, so
# mise keeps its real folders, as in verify-skills. mise reads an empty value as
# unset, and caches under ~/Library/Caches on macOS
for variable, xdg, default in (
    ("MISE_CONFIG_DIR", "XDG_CONFIG_HOME", ".config"),
    ("MISE_DATA_DIR", "XDG_DATA_HOME", ".local/share"),
    ("MISE_STATE_DIR", "XDG_STATE_HOME", ".local/state"),
    (
        "MISE_CACHE_DIR",
        "XDG_CACHE_HOME",
        "Library/Caches" if sys.platform == "darwin" else ".cache",
    ),
):
    if not os.environ.get(variable):
        base = os.environ.get(xdg) or str(Path.home() / default)
        os.environ[variable] = str(Path(base) / "mise")
# Tests replace HOME, which hides the global git config, so commits the scripts
# make need an identity from the environment.
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


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


def private_remote(parent: Path) -> Path:
    """A bare skills-private.git beside skills.git, holding the skill secret,
    the way GitHub holds the private repository."""
    remote = parent / "skills-private.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True
    )
    seed = parent / "private-seed"
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    (seed / ".gitignore").write_text("fleet.toml\n")
    skill(seed / "content", "secret")
    commit(seed)
    subprocess.run(["git", "push", "-q", str(remote), "main"], cwd=seed, check=True)
    shutil.rmtree(seed)
    return remote


@pytest.fixture
def sandbox(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    for name in (
        "_cli.py",
        "_common.py",
        "compile_skills.py",
        "install_skills.py",
        "discover_skills.py",
        "sync.py",
        "sync_private.py",
    ):
        shutil.copy2(SCRIPTS / name, scripts / name)
    (repo / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    skill(repo / "authoring/content", "alpha")
    skill(repo / "skills", "alpha")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    commit(repo)
    return repo, tmp_path / "home"

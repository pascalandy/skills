"""just sync through its CLI, with a bare repository standing in for GitHub."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from conftest import commit, skill

# The commit waiting on GitHub edits the skill alpha and swaps the private sync
# for this stub, so a test sees whether the sync ran the code the pull brought
PULLED_PRIVATE_SYNC = """from pathlib import Path

(Path(__file__).resolve().parent.parent / "pulled-private-sync-ran").touch()
"""


def run(repo: Path, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HOME": str(home),
        "UV_CACHE_DIR": str(home.parent / "uv-cache"),
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    # Keep the caller's git settings, such as pull.rebase, out of the pull
    env.pop("XDG_CONFIG_HOME", None)
    result = subprocess.run(
        ["uv", "run", str(repo / "scripts/sync.py"), *args],
        check=False,
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def on_feature_branch(repo: Path) -> None:
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)


@pytest.fixture
def behind(sandbox: tuple[Path, Path], tmp_path: Path) -> tuple[Path, Path]:
    """A main checkout one commit behind its origin; that commit changes alpha and the private sync."""
    seed, home = sandbox
    subprocess.run(["git", "branch", "-q", "-M", "main"], cwd=seed, check=True)
    origin = tmp_path / "skills.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)], check=True)
    repo = tmp_path / "machine"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True)
    (seed / "scripts/sync_private.py").write_text(PULLED_PRIVATE_SYNC)
    skill(seed / "authoring/content", "alpha", "pulled")
    commit(seed)
    subprocess.run(["git", "push", "-q", str(origin), "main"], cwd=seed, check=True)
    return repo, home


def test_pulls_then_runs_the_pulled_private_sync_and_installs(
    behind: tuple[Path, Path],
) -> None:
    repo, home = behind
    before = git(repo, "rev-parse", "--short=7", "HEAD")

    result = run(repo, home)

    lines = result.stdout.splitlines()
    assert (result.returncode, result.stderr) == (0, "")
    assert (
        lines[0]
        == f"pull\tmain\t{before}..{git(repo, 'rev-parse', '--short=7', 'HEAD')}"
    )
    assert "add\t~/.claude/skills/alpha" in lines
    assert (repo / "pulled-private-sync-ran").is_file()
    installed = home / ".claude/skills/alpha/SKILL.md"
    assert installed.read_text() == "# alpha\n\npulled\n"


def test_a_blocked_pull_shows_gits_reason_and_installs_nothing(
    behind: tuple[Path, Path],
) -> None:
    repo, home = behind
    (repo / "authoring/content/alpha/SKILL.md").write_text("an uncommitted edit\n")

    result = run(repo, home)

    assert (result.returncode, result.stdout) == (1, "")
    assert "authoring/content/alpha/SKILL.md" in result.stderr
    assert result.stderr.endswith("then rerun just sync\n")
    assert not (repo / "pulled-private-sync-ran").exists()
    assert not (home / ".claude").exists()


def test_refuses_a_checkout_off_main_before_pulling_or_installing(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    on_feature_branch(repo)

    result = run(repo, home)

    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "",
        "error: this checkout is on feature; switch to main, then rerun just sync\n",
    )
    assert not (repo / "_skills_private").exists()
    assert not (home / ".claude").exists()


def test_previews_this_checkout_without_pulling(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    # Off main and without a remote, any pull would fail
    on_feature_branch(repo)

    preview = run(repo, home, "--dry-run")
    check = run(repo, home, "--check")

    assert (preview.returncode, preview.stderr) == (0, "")
    # The profile, and so the target list, depends on the host
    assert "add\t~/.claude/skills/alpha" in preview.stdout.splitlines()
    # Nothing is installed yet, so the check lists the work on stderr
    assert (check.returncode, check.stdout) == (1, "")
    assert check.stderr.startswith(preview.stdout)
    assert not (repo / "_skills_private").exists()
    assert not (home / ".claude").exists()


def test_a_fetch_that_cannot_reach_origin_exits_75_before_installing(
    behind: tuple[Path, Path],
) -> None:
    repo, home = behind
    # Nothing listens on port 9, so git reports a refused connection
    git(repo, "remote", "set-url", "origin", "http://127.0.0.1:9/skills.git")

    result = run(repo, home, "--timeout", "30s")

    assert (result.returncode, result.stdout) == (75, "")
    assert result.stderr.startswith("error: could not fetch main: ")
    assert result.stderr.endswith("retry: just sync --timeout 30s\n")
    assert not (home / ".claude").exists()

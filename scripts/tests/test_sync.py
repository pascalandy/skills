"""just sync through its CLI: the branch guard, and previews that skip the pulls."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run(repo: Path, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HOME": str(home),
        "UV_CACHE_DIR": str(home.parent / "uv-cache"),
    }
    return subprocess.run(
        ["uv", "run", str(repo / "scripts/sync.py"), *args],
        check=False,
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def on_feature_branch(repo: Path) -> None:
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)


def test_refuses_a_checkout_off_main_before_pulling_or_installing(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    on_feature_branch(repo)

    result = run(repo, home)

    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "",
        (
            "error: this checkout is on feature; switch to main, then rerun just sync\n"
            "rerun with --verbose for details\n"
        ),
    )
    assert not (repo / "_skills_private").exists()
    assert not (home / ".claude").exists()


def test_dry_run_previews_this_checkout_without_pulling(
    sandbox: tuple[Path, Path],
) -> None:
    repo, home = sandbox
    # Off main and without a remote, any pull would fail
    on_feature_branch(repo)

    result = run(repo, home, "--dry-run")

    assert (result.returncode, result.stderr) == (0, "")
    # The profile, and so the target count, depends on the host
    assert result.stdout.startswith("preview: ")
    assert "; skills=1, commands=0; " in result.stdout
    assert not (repo / "_skills_private").exists()
    assert not (home / ".claude").exists()

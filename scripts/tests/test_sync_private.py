"""The private clone through its CLI, with bare repositories standing in for GitHub."""

from __future__ import annotations

import fcntl
import json
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
    """A public checkout whose origin is skills.git, in its own projects folder,
    as on each machine."""
    repo = parent / name / "skills"
    subprocess.run(
        ["git", "clone", "-q", str(parent / "skills.git"), str(repo)], check=True
    )
    return repo


@pytest.fixture
def machines(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Two public checkouts of skills.git and the private remote beside it."""
    public = tmp_path / "public"
    (public / "scripts").mkdir(parents=True)
    for name in ("_cli.py", "_common.py", "sync_private.py"):
        shutil.copy2(SCRIPTS / name, public / "scripts" / name)
    (public / ".gitignore").write_text("__pycache__/\n")
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
    result = subprocess.run(
        ["uv", "run", str(repo / "scripts/sync_private.py"), *args],
        check=False,
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result


def changed(*changes: list[str]) -> str:
    return (
        json.dumps({"ok": True, "changes": list(changes)}, separators=(",", ":")) + "\n"
    )


def quiet(result: subprocess.CompletedProcess[str]) -> tuple[int, str, str]:
    return result.returncode, result.stdout, result.stderr


def private(repo: Path) -> Path:
    return repo.parent / "skills-private"


def merge(remote: Path, tmp_path: Path) -> str:
    """Land a commit on the private main, the way a merged PR does."""
    work = tmp_path / "pr"
    git(tmp_path, "clone", "-q", str(remote), str(work))
    (work / "authoring/content/secret/SKILL.md").write_text("merged\n")
    commit(work)
    git(work, "push", "-q", "origin", "main")
    return git(work, "rev-parse", "--short=7", "HEAD")


def test_clones_beside_the_checkout_then_pulls_what_github_merged(
    machines: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    one, two, remote = machines

    clone = ["clone", "skills-private", str(remote)]
    assert quiet(run(one)) == (0, changed(clone), "")
    assert quiet(run(two)) == (0, changed(clone), "")
    assert quiet(run(two)) == (0, '{"ok":true}\n', ""), "a current clone is a no-op"
    before = git(private(two), "rev-parse", "--short=7", "HEAD")
    after = merge(remote, tmp_path)
    assert quiet(run(two, "-n")) == (0, '{"ok":true}\n', "")
    assert quiet(run(two)) == (
        0,
        changed(["pull", "skills-private", f"{before}..{after}"]),
        "",
    )

    secret = private(two) / "authoring/content/secret/SKILL.md"
    assert secret.read_text() == "merged\n"
    assert not (two / "skills-private").exists()
    assert git(one, "status", "--porcelain") == ""


@pytest.mark.parametrize("edit", ["uncommitted", "branch", "commit", "diverged"])
def test_a_local_change_stops_the_pull_untouched(
    machines: tuple[Path, Path, Path], tmp_path: Path, edit: str
) -> None:
    """Private skills change through a PR, so the clone never commits or pushes."""
    one, _, remote = machines
    assert run(one).returncode == 0
    clone = private(one)
    secret = clone / "authoring/content/secret/SKILL.md"
    if edit == "branch":
        git(clone, "switch", "-q", "-c", "feature")
    else:
        secret.write_text("from one\n")
    if edit in ("commit", "diverged"):
        commit(clone)
    if edit == "diverged":
        merge(remote, tmp_path)
    github = git(remote, "rev-parse", "main")
    head = git(clone, "rev-parse", "HEAD")

    result = run(one)
    # A dry run finds the same without the network, from the last fetch
    preview = run(one, "--dry-run")

    assert (result.returncode, result.stdout) == (1, "")
    assert (preview.returncode, preview.stdout) == (1, "")
    error = json.loads(result.stderr.splitlines()[-1])["errors"][0]
    previewed = json.loads(preview.stderr.splitlines()[-1])["errors"][0]
    assert error.startswith(str(clone))
    assert {
        "uncommitted": "has uncommitted edits;",
        "branch": "is on feature;",
        "commit": "has 1 commit GitHub's main lacks;",
        "diverged": "has 1 commit GitHub's main lacks;",
    }[edit] in error
    assert previewed == error.replace("GitHub's main", "its origin/main")
    assert "changes" not in json.loads(result.stderr.splitlines()[-1])
    assert git(clone, "rev-parse", "HEAD") == head
    assert git(remote, "rev-parse", "main") == github
    if edit != "branch":
        assert secret.read_text() == "from one\n"


def test_a_stale_origin_main_does_not_block_a_clone_at_githubs_main(
    machines: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    """The old code failed here: it compared with origin/main before fetching."""
    one, _, remote = machines
    assert run(one).returncode == 0
    clone = private(one)
    stale = git(clone, "rev-parse", "origin/main")
    merge(remote, tmp_path)
    # Fast-forward to GitHub's main without moving origin/main
    git(clone, "fetch", "-q", "--refmap=", "origin", "main")
    git(clone, "merge", "-q", "--ff-only", "FETCH_HEAD")
    assert git(clone, "rev-parse", "origin/main") == stale

    result = run(one)

    assert quiet(result) == (0, '{"ok":true}\n', "")
    assert git(clone, "rev-parse", "HEAD") == git(remote, "rev-parse", "main")


def test_a_dry_run_without_origin_main_stops_instead_of_passing(
    machines: tuple[Path, Path, Path],
) -> None:
    """The old code failed here: a failed comparison counted as no commits."""
    one, _, _ = machines
    assert run(one).returncode == 0
    clone = private(one)
    git(clone, "update-ref", "-d", "refs/remotes/origin/main")

    result = run(one, "--dry-run")

    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr)["errors"] == [
        (
            f"{clone} cannot compare with its origin/main; fetch it with "
            f"git -C {clone} fetch origin main, then rerun"
        )
    ]


def test_leaves_a_folder_that_is_not_a_clone_untouched(
    machines: tuple[Path, Path, Path],
) -> None:
    one, _, _ = machines
    kept = skill(private(one) / "authoring/content", "local") / "SKILL.md"

    result = run(one)

    assert result.returncode == 1
    assert "is not a clone of the private repository" in result.stderr
    assert kept.read_text() == "# local\n\nold\n"
    assert not (private(one) / ".git").exists()


def test_dry_run_names_the_clone_and_changes_nothing(
    machines: tuple[Path, Path, Path],
) -> None:
    one, _, remote = machines

    result = run(one, "--dry-run")

    assert quiet(result) == (0, changed(["clone", "skills-private", str(remote)]), "")
    assert not private(one).exists()


def test_another_sync_holding_the_lock_past_the_timeout_exits_75(
    machines: tuple[Path, Path, Path],
) -> None:
    one, _, _ = machines
    lock = one / ".git/sync-private.lock"

    with lock.open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        result = run(one, "--timeout", "1s")

    assert (result.returncode, result.stdout) == (75, "")
    assert json.loads(result.stderr) == {
        "ok": False,
        "errors": [f"another run still holds {lock} after 1s"],
        "retry": "scripts/sync_private.py --timeout 1s",
    }
    assert not private(one).exists()


def test_a_network_failure_exits_75_and_a_missing_repository_exits_1(
    machines: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    one, _, _ = machines
    # Nothing listens on port 9, so git reports a refused connection
    git(one, "remote", "set-url", "origin", "http://127.0.0.1:9/skills.git")
    offline = run(one)
    git(one, "remote", "set-url", "origin", str(tmp_path / "absent/skills.git"))
    missing = run(one)

    assert (offline.returncode, offline.stdout) == (75, "")
    answer = json.loads(offline.stderr.splitlines()[-1])
    assert answer["errors"][0].startswith(
        "could not clone http://127.0.0.1:9/skills-private.git: "
    )
    assert answer["retry"] == "scripts/sync_private.py"
    assert (missing.returncode, missing.stdout) == (1, "")
    assert json.loads(missing.stderr.splitlines()[-1])["errors"][0].endswith(
        "; check that the private repository exists and you can read it"
    )

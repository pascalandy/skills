"""The private clone through its CLI, with bare repositories standing in for GitHub."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import GIT_IDENTITY, SCRIPTS, commit, private_remote, skill

HOST = socket.gethostname().split(".")[0]


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
    for name in ("_cli.py", "_common.py", "sync_private.py"):
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


def test_clones_then_saves_edits_every_machine_receives(
    machines: tuple[Path, Path, Path],
) -> None:
    one, two, remote = machines

    clone = ["clone", "_skills_private", str(remote)]
    assert quiet(run(one)) == (0, changed(clone), "")
    assert quiet(run(two)) == (0, changed(clone), "")
    assert quiet(run(two)) == (0, '{"ok":true}\n', ""), "a current clone is a no-op"
    (one / "_skills_private/content/secret/SKILL.md").write_text("from one\n")
    skill(one / "_skills_private/content", "added")
    commit = ["commit", "_skills_private", f"save edits from {HOST}"]
    assert quiet(run(one, "-n")) == (0, changed(commit), "")
    push = ["push", "_skills_private", "1 commit"]
    assert quiet(run(one)) == (0, changed(commit, push), "")
    before = git(two / "_skills_private", "rev-parse", "--short=7", "HEAD")
    after = git(remote, "rev-parse", "--short=7", "main")
    pull = ["pull", "_skills_private", f"{before}..{after}"]
    assert quiet(run(two)) == (0, changed(pull), "")

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
    assert json.loads(result.stderr.splitlines()[-1])["changes"] == [
        ["commit", "_skills_private", f"save edits from {HOST}"]
    ]
    assert secret.read_text() == "from two\n"
    assert git(two / "_skills_private", "status", "--porcelain") == ""
    assert not (two / "_skills_private/.git/rebase-merge").exists()
    assert git(remote, "show", "main:content/secret/SKILL.md") == "from one"


# Where the stop lands: before git add, right after git commit returns, or
# before the pull; the receipt lists the commit only once it landed
@pytest.mark.parametrize(
    ("before", "after", "committed"),
    [("add", None, False), (None, "commit", True), ("pull", None, True)],
    ids=["add", "commit", "pull"],
)
@pytest.mark.parametrize(
    "failure,code", [("Interrupted(130)", 130), ("RuntimeError('boom')", 1)]
)
def test_a_stop_after_saving_edits_keeps_the_commit_receipt(
    machines: tuple[Path, Path, Path],
    failure: str,
    code: int,
    before: str | None,
    after: str | None,
    committed: bool,
) -> None:
    one, _, _ = machines
    assert run(one).returncode == 0
    private = one / "_skills_private"
    start = git(private, "rev-parse", "HEAD")
    (private / "content/secret/SKILL.md").write_text("saved edits\n")
    driver = f"""
import sys
sys.path.insert(0, sys.argv[1])
import sync_private
from _cli import Interrupted
original = sync_private.git
def stopped(*args, **kwargs):
    if args[0] == {before!r}:
        raise {failure}
    result = original(*args, **kwargs)
    if args[0] == {after!r}:
        raise {failure}
    return result
sync_private.git = stopped
raise SystemExit(sync_private.main([]))
"""
    result = subprocess.run(
        [sys.executable, "-c", driver, str(one / "scripts")],
        cwd=one,
        env={**os.environ, **GIT_IDENTITY, "HOME": str(one.parent / "home")},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert (result.returncode, result.stdout) == (code, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    if committed:
        assert answer["changes"] == [
            ["commit", "_skills_private", f"save edits from {HOST}"]
        ]
        assert git(private, "show", "HEAD:content/secret/SKILL.md") == "saved edits"
    else:
        assert "changes" not in answer
        assert git(private, "rev-parse", "HEAD") == start


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

    assert quiet(result) == (0, changed(["clone", "_skills_private", str(remote)]), "")
    assert not (one / "_skills_private").exists()


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
    assert not (one / "_skills_private").exists()


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

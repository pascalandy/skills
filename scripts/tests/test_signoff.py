"""just signoff through its CLI, against a bare origin and a fake gh."""

from __future__ import annotations

import json
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from fake_github import Sandbox


def signed(head: str) -> str:
    return f'{{"ok":true,"changes":[["signoff","{head[:7]}"]]}}\n'


@pytest.fixture
def github(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path, "signoff.py")


@pytest.mark.parametrize("quota", [False, True], ids=["normal", "temp-quota"])
def test_signs_off_the_pushed_head_after_the_checks(
    github: Sandbox, tmp_path: Path, quota: bool
) -> None:
    check = github.work / "scripts/check.py"
    # Exercise real pytest capture and tmp_path, which the normal fake check
    # does not need. Temporary test repositories must not inherit a parent.
    check.write_text(
        "import pathlib, subprocess, sys, tempfile\n"
        "with tempfile.TemporaryDirectory() as folder:\n"
        "    probe = pathlib.Path(folder) / 'test_scratch.py'\n"
        "    probe.write_text('''import socket, subprocess\n"
        "def test_check_scratch_is_outside_git_and_supports_sockets(tmp_path):\n"
        "    assert subprocess.run(['git', 'rev-parse', '--git-dir'], cwd=tmp_path, capture_output=True).returncode != 0\n"
        "    with socket.socket(socket.AF_UNIX) as sock:\n"
        "        sock.bind(str(tmp_path / 'socket'))\n"
        "''')\n"
        "    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', str(probe)], cwd=folder, timeout=30, capture_output=True, text=True)\n"
        "    if result.returncode:\n"
        "        sys.stderr.write(result.stdout + result.stderr)\n"
        "        sys.exit(result.returncode)\n" + check.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    github.git("add", "scripts/check.py")
    github.git("commit", "-qm", "exercise check scratch space")
    github.git("push", "-q", "origin", "feature")
    head = github.git("rev-parse", "HEAD")
    if quota:
        startup = tmp_path / "startup"
        startup.mkdir()
        blocked = tmp_path / "full-temp"
        (startup / "sitecustomize.py").write_text(
            "import errno, os, sys, tempfile\n"
            "from pathlib import Path\n"
            "tempfile.tempdir = os.environ['TMPDIR']\n"
            "def reject(event, args):\n"
            "    if event in ('tempfile.mkdtemp', 'tempfile.mkstemp') "
            f"and Path(args[0]).is_relative_to({str(blocked)!r}):\n"
            "        raise OSError(errno.EDQUOT, 'Disk quota exceeded', args[0])\n"
            "sys.addaudithook(reject)\n",
            encoding="utf-8",
        )
        github.env["PYTHONPATH"] = str(startup)
        github.env.update(TMPDIR=str(blocked), TMP=str(blocked), TEMP=str(blocked))

    with tempfile.TemporaryDirectory(prefix="t-", dir="/var/tmp") as normal:
        if not quota:
            github.env.update(TMPDIR=normal, TMP=normal, TEMP=normal)
        result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, signed(head)), result.stderr
    assert github.statuses() == {head: "success"}
    assert github.checked() == [github.git("rev-parse", "HEAD^{tree}")]
    assert github.git("status", "--porcelain") == ""
    assert github.git("worktree", "list", "--porcelain").count("worktree ") == 2


def test_failed_worktree_add_names_the_destination_and_limits_git_output(
    github: Sandbox, tmp_path: Path
) -> None:
    attempted = tmp_path / "attempted"
    real_git = shutil.which("git")
    shim = tmp_path / "bin/git"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "if 'worktree' in args and 'add' in args:\n"
        f"    Path({str(attempted)!r}).write_text(args[-2])\n"
        "    print('\\n'.join(f'error: unable to write file {i}' "
        "for i in range(100)), file=sys.stderr)\n"
        "    sys.exit(1)\n"
        f"os.execv({real_git!r}, [{real_git!r}, *args])\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (1, "")
    error = json.loads(result.stderr)["errors"][0]
    assert "git worktree add failed" in error
    assert attempted.read_text(encoding="utf-8") in error
    assert "error: unable to write file 0" in error
    assert "error: unable to write file 99" not in error
    assert len(error.splitlines()) <= 10
    assert github.statuses() == {}
    assert github.checks_run() == 0


def test_a_signed_off_head_needs_no_new_run(github: Sandbox) -> None:
    github.sign(github.git("rev-parse", "HEAD"))

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, '{"ok":true}\n')
    assert github.checks_run() == 0


def test_a_failing_check_signs_nothing(github: Sandbox) -> None:
    result = github.run("signoff.py", FAKE_CHECK_EXIT="1")

    assert result.returncode == 1
    assert '{"ok":false,"errors":["lint failed"]}' in result.stderr
    assert "just check failed" in result.stderr
    assert github.statuses() == {}


@pytest.mark.parametrize(("status", "code"), [(429, 75), (503, 75), (401, 1), (403, 1)])
def test_github_http_failures_keep_their_retryability(
    github: Sandbox, status: int, code: int
) -> None:
    github.hook("api", f"echo 'gh: API request failed (HTTP {status})' >&2; exit 1")

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (code, "")
    assert f"HTTP {status}" in result.stderr
    assert github.statuses() == {}
    assert github.checks_run() == 0


def test_refuses_a_head_github_lacks_before_the_checks(github: Sandbox) -> None:
    github.commit("unpushed")

    result = github.run("signoff.py")

    assert result.returncode == 1
    assert "run: git push origin HEAD:feature" in result.stderr
    assert github.checks_run() == 0


def test_refuses_untracked_files_and_keeps_them(github: Sandbox) -> None:
    (github.work / "notes.txt").write_text("draft\n")

    result = github.run("signoff.py")

    assert result.returncode == 1
    assert "untracked files: notes.txt" in result.stderr
    assert (github.work / "notes.txt").read_text() == "draft\n"
    assert github.checks_run() == 0


@pytest.mark.parametrize(
    "change",
    [
        "git switch -q --detach HEAD~1",
        "echo edited > feature",
    ],
    ids=["checkout-moves", "file-edited"],
)
def test_checks_the_pushed_commit_whatever_happens_in_the_checkout(
    github: Sandbox, change: str
) -> None:
    head = github.git("rev-parse", "HEAD")
    tree = github.git("rev-parse", "HEAD^{tree}")

    result = github.run(
        "signoff.py", FAKE_CHECK_HOOK=f"cd {shlex.quote(str(github.work))} && {change}"
    )

    assert (result.returncode, result.stdout) == (0, signed(head))
    assert github.checked() == [tree]
    assert github.statuses() == {head: "success"}


def test_checks_the_pushed_commit_despite_a_replace_ref(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    tree = github.git("rev-parse", "HEAD^{tree}")
    # It would hand the checks the parent's files under HEAD's name
    github.git("replace", head, f"{head}~1")

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, signed(head))
    assert github.checked() == [tree]


def test_signs_nothing_when_github_moves_during_the_checks(github: Sandbox) -> None:
    result = github.run(
        "signoff.py", FAKE_CHECK_HOOK=github.push_elsewhere("feature", "news")
    )

    assert result.returncode == 1
    assert "origin/feature moved" in result.stderr
    assert '{"ok":true}' not in result.stderr, "the check's verdict is not signoff's"
    assert github.statuses() == {}


@pytest.mark.parametrize(
    "upstream",
    [
        ["--unset-upstream"],
        # A branch made from origin/main tracks main
        ["--set-upstream-to=origin/main"],
    ],
)
def test_compares_head_with_origin_branch_whatever_the_upstream(
    github: Sandbox, upstream: list[str]
) -> None:
    head = github.git("rev-parse", "HEAD")
    github.git("branch", *upstream)

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, signed(head))
    assert github.statuses() == {head: "success"}


def test_a_dry_run_prints_the_signoff_without_checking(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")

    result = github.run("signoff.py", "--dry-run")

    assert (result.returncode, result.stdout) == (0, signed(head))
    assert github.statuses() == {}
    assert github.checks_run() == 0

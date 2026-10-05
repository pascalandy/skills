"""just signoff through its CLI, against a bare origin and a fake gh."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
from fake_github import Sandbox


@pytest.fixture
def github(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path, "signoff.py")


def test_signs_off_the_pushed_head_after_the_checks(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, f"signoff\t{head[:7]}\n")
    assert github.statuses() == {head: "success"}
    assert github.checked() == [github.git("rev-parse", "HEAD^{tree}")]


def test_a_signed_off_head_needs_no_new_run(github: Sandbox) -> None:
    github.sign(github.git("rev-parse", "HEAD"))

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, "")
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

    assert (result.returncode, result.stdout) == (0, f"signoff\t{head[:7]}\n")
    assert github.checked() == [tree]
    assert github.statuses() == {head: "success"}


def test_checks_the_pushed_commit_despite_a_replace_ref(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    tree = github.git("rev-parse", "HEAD^{tree}")
    # It would hand the checks the parent's files under HEAD's name
    github.git("replace", head, f"{head}~1")

    result = github.run("signoff.py")

    assert (result.returncode, result.stdout) == (0, f"signoff\t{head[:7]}\n")
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

    assert (result.returncode, result.stdout) == (0, f"signoff\t{head[:7]}\n")
    assert github.statuses() == {head: "success"}


def test_a_dry_run_prints_the_signoff_without_checking(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")

    result = github.run("signoff.py", "--dry-run")

    assert (result.returncode, result.stdout) == (0, f"signoff\t{head[:7]}\n")
    assert github.statuses() == {}
    assert github.checks_run() == 0

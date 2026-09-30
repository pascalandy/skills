"""just merge through its CLI, against a bare origin and a fake gh."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest
from fake_github import Sandbox


@pytest.fixture
def github(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path, "signoff.py", "merge.py")


def test_merges_a_signed_off_head_without_new_checks(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (
        0,
        f"merge\t#7\t{head[:7]}\nsynced\tmbp\n",
    )
    assert github.main_subject() == "✨ feat: add feature (#7)"
    assert github.git("--git-dir", str(github.origin), "diff", "main", head) == ""
    assert github.checks_run() == 0
    assert github.deploys() == [github.main.resolve()]


def test_signs_off_an_unsigned_head_once_then_merges(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (
        0,
        f"signoff\t{head[:7]}\nmerge\t#7\t{head[:7]}\nsynced\tmbp\n",
    )
    assert github.statuses() == {head: "success"}
    assert github.checks_run() == 1
    assert github.main_subject() == "✨ feat: add feature (#7)"


@pytest.mark.parametrize(
    ("fields", "fix"),
    [
        ({"isDraft": True}, "run: gh pr ready 7"),
        ({"baseRefName": "lower-layer"}, "gh stack merge <stack> --yes --squash"),
        (
            {"state": "MERGED", "baseRefName": "lower-layer"},
            "PR #7 was merged into lower-layer, not main",
        ),
    ],
)
def test_refuses_a_pr_that_cannot_merge_as_is_before_the_checks(
    github: Sandbox, fields: dict[str, object], fix: str
) -> None:
    github.open_pr(**fields)

    result = github.run("merge.py")

    assert result.returncode == 1
    assert fix in result.stderr
    assert github.checks_run() == 0
    assert github.main_subject() == "seed"


def test_refuses_a_branch_without_main_tip_before_the_checks(
    github: Sandbox,
) -> None:
    github.open_pr()
    github.sh(github.push_elsewhere("main", "news"))

    result = github.run("merge.py")

    assert result.returncode == 1
    assert "run: git merge origin/main, git push, then just merge" in result.stderr
    assert github.checks_run() == 0
    assert github.main_subject() == "news"


def test_merges_nothing_when_the_pr_moves_after_the_signoff(github: Sandbox) -> None:
    github.open_pr()
    github.hook("signoff", github.push_elsewhere("feature", "late"))

    result = github.run("merge.py")

    assert result.returncode == 1
    assert "rerun just merge to check the new head" in result.stderr
    assert github.main_subject() == "seed"
    assert github.deploys() == []


def test_warns_when_main_moves_just_before_the_merge(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)
    github.hook("pr merge", github.push_elsewhere("main", "news"))

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (0, f"merge\t#7\t{head[:7]}\n")
    assert "holds a tree the checks did not run on" in result.stderr
    assert github.main_subject() == "✨ feat: add feature (#7)"
    assert github.deploys() == []


def test_a_merge_call_lost_to_the_network_stays_retryable(github: Sandbox) -> None:
    github.open_pr()
    github.sign(github.git("rev-parse", "HEAD"))
    github.hook("pr merge", "echo 'error connecting to api.github.com' >&2; exit 1")

    result = github.run("merge.py")

    assert result.returncode == 75
    assert "error connecting to api.github.com" in result.stderr
    assert github.main_subject() == "seed"


def test_a_rerun_after_the_merge_only_deploys_again(github: Sandbox) -> None:
    github.open_pr()
    github.sign(github.git("rev-parse", "HEAD"))
    assert github.run("merge.py").returncode == 0
    merged = github.git("--git-dir", str(github.origin), "rev-parse", "main")

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (0, "synced\tmbp\n")
    assert github.git("--git-dir", str(github.origin), "rev-parse", "main") == merged
    assert len(github.deploys()) == 2


def test_a_failed_deploy_warns_without_failing_the_merge(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)

    result = github.run("merge.py", FAKE_DEPLOY_EXIT="75")

    assert (result.returncode, result.stdout) == (0, f"merge\t#7\t{head[:7]}\n")
    assert "the merge landed, but just deploy did not reach" in result.stderr
    assert github.main_subject() == "✨ feat: add feature (#7)"


@pytest.mark.parametrize("rerun", [False, True], ids=["after-merge", "rerun"])
def test_a_failed_deploy_gate_warns_without_hiding_the_merge(
    github: Sandbox, rerun: bool
) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)
    if rerun:
        assert github.run("merge.py").returncode == 0
        github.git("remote", "set-url", "origin", str(github.work / "missing-origin"))
    else:
        github.hook(
            "pr merge",
            "git remote set-url origin "
            + shlex.quote(str(github.work / "missing-origin")),
        )
    deployed = github.deploys()

    result = github.run("merge.py")

    output = "" if rerun else f"merge\t#7\t{head[:7]}\n"
    assert (result.returncode, result.stdout) == (0, output)
    assert "the merge landed, but just deploy" in result.stderr
    assert "git fetch origin failed" in result.stderr
    assert github.main_subject() == "✨ feat: add feature (#7)"
    assert github.deploys() == deployed


@pytest.mark.parametrize(
    "unsafe",
    [
        "echo '# wip' >> scripts/sync_fleet.py && git commit -qam wip",
        "echo '# wip' >> scripts/sync_fleet.py",
        "echo '# wip' >> scripts/sync_fleet.py && printf 'broken index' > .git/index",
    ],
    ids=["unpushed-commit", "changed-scripts", "unreadable-status"],
)
def test_deploys_nothing_from_an_unsafe_main_checkout(
    github: Sandbox, unsafe: str
) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)
    github.sh(f"cd {shlex.quote(str(github.main))} && {unsafe}")

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (0, f"merge\t#7\t{head[:7]}\n")
    assert "just merge did not deploy" in result.stderr
    assert github.main_subject() == "✨ feat: add feature (#7)"
    assert github.deploys() == []


def test_a_dry_run_changes_nothing(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()

    result = github.run("merge.py", "--dry-run")

    assert (result.returncode, result.stdout) == (
        0,
        f"signoff\t{head[:7]}\nmerge\t#7\t{head[:7]}\n",
    )
    assert github.statuses() == {}
    assert github.checks_run() == 0
    assert github.main_subject() == "seed"
    assert github.deploys() == []

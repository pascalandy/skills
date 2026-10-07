"""just merge through its CLI, against a bare origin and a fake gh."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
from fake_github import Sandbox

SYNCED = ["sync", "mbp", "abc1234"]


def changed(*changes: list[str]) -> str:
    return (
        json.dumps({"ok": True, "changes": list(changes)}, separators=(",", ":")) + "\n"
    )


def landed(result: subprocess.CompletedProcess[str], head: str | None) -> list[str]:
    """A run that merged but did not deploy: exit 1, and the errors of an answer
    that lists the merge of `head`, or nothing on a rerun."""
    assert (result.returncode, result.stdout) == (1, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    assert answer.get("changes") == ([["merge", "#7", head[:7]]] if head else None)
    return answer["errors"]


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
        changed(["merge", "#7", head[:7]], SYNCED),
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
        changed(["signoff", head[:7]], ["merge", "#7", head[:7]], SYNCED),
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
        (
            {
                "state": "MERGED",
                "baseRefName": "lower-layer",
                "mergeCommit": {"oid": "f" * 40},
            },
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


def test_fails_when_main_moves_just_before_the_merge(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)
    github.hook("pr merge", github.push_elsewhere("main", "news"))

    result = github.run("merge.py")

    [error] = landed(result, head)
    assert error.startswith("the merge landed, but main at ")
    assert "holds a tree the checks did not run on" in error
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


def test_reads_the_deploy_of_a_main_checkout_from_before_490(
    github: Sandbox,
) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)

    result = github.run("merge.py", FAKE_DEPLOY_LEGACY="1")

    assert (result.returncode, result.stdout) == (
        0,
        changed(["merge", "#7", head[:7]], ["synced", "mbp", "abc1234"]),
    )


def test_a_rerun_after_the_merge_only_deploys_again(github: Sandbox) -> None:
    github.open_pr()
    github.sign(github.git("rev-parse", "HEAD"))
    assert github.run("merge.py").returncode == 0
    merged = github.git("--git-dir", str(github.origin), "rev-parse", "main")

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (0, changed(SYNCED))
    assert github.git("--git-dir", str(github.origin), "rev-parse", "main") == merged
    assert len(github.deploys()) == 2


def test_deploys_from_the_scripts_main_checkout_whatever_the_cwd(
    github: Sandbox, tmp_path: Path
) -> None:
    github.open_pr()
    github.sign(github.git("rev-parse", "HEAD"))
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()

    result = subprocess.run(
        [sys.executable, str(github.work / "scripts/merge.py")],
        cwd=unrelated,
        env=github.env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert github.deploys() == [github.main.resolve()]


def test_a_rerun_deploys_a_stack_layer_that_landed_on_main(github: Sandbox) -> None:
    github.open_pr()
    github.sign(github.git("rev-parse", "HEAD"))
    assert github.run("merge.py").returncode == 0
    # gh stack merge leaves the layer's base pointing at the layer below it
    state = github.state()
    state["prs"][0]["baseRefName"] = "lower-layer"
    github.save(state)

    result = github.run("merge.py")

    assert (result.returncode, result.stdout) == (0, changed(SYNCED))
    assert len(github.deploys()) == 2


def test_a_failed_deploy_fails_the_run_and_lists_what_landed(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()
    github.sign(head)

    result = github.run("merge.py", FAKE_DEPLOY_EXIT="75")

    assert landed(result, head) == [
        "the merge landed, but just deploy did not reach every machine; fix what "
        + "its answer above says, then run just deploy"
    ]
    assert github.main_subject() == "✨ feat: add feature (#7)"


@pytest.mark.parametrize("rerun", [False, True], ids=["after-merge", "rerun"])
def test_a_failed_deploy_gate_fails_without_hiding_the_merge(
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

    [error] = landed(result, None if rerun else head)
    assert error.startswith("the merge landed, but just deploy could not run: ")
    assert "git fetch origin failed" in error
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

    [error] = landed(result, head)
    assert error.startswith("the merge landed, but it was not deployed: ")
    assert github.main_subject() == "✨ feat: add feature (#7)"
    assert github.deploys() == []


def test_a_dry_run_changes_nothing(github: Sandbox) -> None:
    head = github.git("rev-parse", "HEAD")
    github.open_pr()

    result = github.run("merge.py", "--dry-run")

    assert (result.returncode, result.stdout) == (
        0,
        changed(["signoff", head[:7]], ["merge", "#7", head[:7]]),
    )
    assert github.statuses() == {}
    assert github.checks_run() == 0
    assert github.main_subject() == "seed"
    assert github.deploys() == []

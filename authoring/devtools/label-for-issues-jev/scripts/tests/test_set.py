"""set: the agent's decision on one issue, canonical labels only, never stale."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from labeltest import CANONICAL, Harness, issue

RUNS = ("label-for-issues-jev", "runs")


def review(harness: Harness, *labels: str, catalog: list[str] | None = None) -> None:
    """#1 is in review: whether a decision is open is uncertain."""
    if catalog is not None:
        harness.add_repo("o/r", labels=catalog)
    harness.issues(issue(1, labels=labels), issue(2, title="Closed", state="CLOSED"))
    harness.fake.overrides = {"Crash on start": {"open_decision": 0.5}}
    assert harness.live("--state", "all").code == 0


def set_logs(harness: Harness) -> list[dict]:
    """Logs in the order they were written; names only order to the second."""
    paths = harness.state.joinpath(*RUNS).glob("*.set-*.json")
    ordered = sorted(paths, key=lambda path: path.stat().st_mtime_ns)
    return [json.loads(Path(path).read_text()) for path in ordered]


def test_set_writes_reads_back_and_logs(harness: Harness) -> None:
    review(harness)

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 0, result.stderr
    assert result.stdout.startswith("set #1: added 1-needs-triage; log: ")
    assert harness.labels_of(1) == ["1-needs-triage"]
    assert harness.edits() == [
        ["issue", "edit", "1", "-R", "o/r", "--add-label", "1-needs-triage"]
    ]
    [log] = set_logs(harness)
    assert (log["outcome"], log["added"], log["removed"]) == (
        "set",
        ["1-needs-triage"],
        [],
    )


def test_adding_into_a_filled_family_replaces_it(harness: Harness) -> None:
    review(harness, "2-type:bug", "3-pty:p2")

    result = harness.run("set", "last", "1", "--add", "2-type:task")

    assert result.code == 0, result.stderr
    assert harness.labels_of(1) == ["3-pty:p2", "2-type:task"]
    assert harness.edits()[0][-4:] == [
        "--add-label",
        "2-type:task",
        "--remove-label",
        "2-type:bug",
    ]


def test_apply_and_earlier_sets_do_not_make_it_stale(harness: Harness) -> None:
    review(harness)
    assert harness.run("apply", "last").code == 0

    first = harness.run("set", "last", "1", "--add", "1-needs-triage")
    second = harness.run("set", "last", "1", "--add", "2-type:task")

    assert (first.code, second.code) == (0, 0), second.stderr
    assert harness.labels_of(1) == ["3-pty:p2", "1-needs-triage", "2-type:task"]


@pytest.mark.parametrize(
    ("kind", "label", "reason"),
    [
        ("IssueComment", None, "new comment"),
        ("LabeledEvent", "3-pty:p1", "3-pty:p1 changed outside jevlabel"),
        ("RenamedTitleEvent", None, "title changed"),
        ("AssignedEvent", None, "updated outside jevlabel"),
    ],
)
def test_a_change_since_the_run_makes_it_stale(
    harness: Harness, kind: str, label: str | None, reason: str
) -> None:
    review(harness)
    harness.change(1, kind, "2026-10-01T00:00:00Z", label=label)

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 1
    assert f"error: #1: stale: {reason} since run " in result.stderr
    assert harness.edits() == []


def test_a_proposed_label_that_a_person_added_is_stale(harness: Harness) -> None:
    review(harness)
    harness.change(1, "LabeledEvent", "2026-10-01T00:00:00Z", label="3-pty:p2")

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 1
    assert "error: #1: stale: 3-pty:p2 changed outside jevlabel" in result.stderr


def test_a_label_changed_within_the_snapshot_second_is_stale(harness: Harness) -> None:
    review(harness)
    snapshot = harness.found(1)["updatedAt"]
    harness.change(1, "LabeledEvent", snapshot, label="3-pty:p1")

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 1
    assert "error: #1: stale: 3-pty:p1 changed outside jevlabel" in result.stderr


def test_a_person_repeating_an_own_write_is_stale(harness: Harness) -> None:
    review(harness)
    assert harness.run("apply", "last").code == 0
    assert harness.run("set", "last", "1", "--add", "3-pty:p1").code == 0
    harness.change(1, "LabeledEvent", "2026-10-01T00:00:00Z", label="3-pty:p2")

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 1
    assert "error: #1: stale: 3-pty:p2 added outside jevlabel" in result.stderr


def test_a_closed_issue_is_stale(harness: Harness) -> None:
    review(harness)
    harness.found(1)["state"] = "CLOSED"

    result = harness.run("set", "last", "1", "--add", "1-needs-triage", "--json")

    assert result.code == 1
    assert result.json()["outcome"] == "stale"
    assert "error: #1: stale: closed since run " in result.stderr


@pytest.mark.parametrize(
    ("args", "problem"),
    [
        ([], "name at least one --add or --remove label"),
        (["--add", "needs-triage"], "needs-triage is not a canonical label"),
        (["--add", "4-epic:member"], "4-epic:member depends on parent links"),
        (["--add", "1-wip-by-agent"], "1-wip-by-agent marks started work"),
        (
            ["--add", "1-needs-info", "--remove", "1-needs-info"],
            "both added and removed",
        ),
        (
            ["--add", "1-needs-info", "--add", "1-needs-triage"],
            "add one state label at most",
        ),
        (
            ["--add", "1-ready-for-agent"],
            "adding 1-ready-for-agent needs --reason with the readiness review",
        ),
        (
            ["--add", "0-impediment", "--reason", " "],
            "adding 0-impediment needs --reason",
        ),
    ],
)
def test_a_bad_decision_is_refused_before_any_gh_call(
    harness: Harness, args: list[str], problem: str
) -> None:
    result = harness.run("set", "last", "1", *args)

    assert result.code == 2
    assert problem in result.stderr
    assert harness.calls() == []


def test_a_reason_is_logged_with_the_decision(harness: Harness) -> None:
    review(harness)
    reason = "readiness review 2026-09-28 by Claude: scope clear, no blockers"

    result = harness.run(
        "set", "last", "1", "--add", "1-ready-for-agent", "--reason", reason
    )

    assert result.code == 0, result.stderr
    assert [log["reason"] for log in set_logs(harness)] == [reason]


def test_dry_run_writes_nothing(harness: Harness) -> None:
    review(harness, "1-needs-info")

    result = harness.run("set", "last", "1", "--add", "1-needs-triage", "--dry-run")

    assert result.code == 0, result.stderr
    assert result.stdout.strip() == (
        "set #1 --dry-run: would add 1-needs-triage and remove 1-needs-info; "
        "nothing written"
    )
    assert harness.edits() == []
    assert set_logs(harness) == []


def test_nothing_to_change_writes_nothing(harness: Harness) -> None:
    review(harness, "1-needs-triage")

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 0, result.stderr
    assert result.stdout.strip() == "set #1: nothing to change"
    assert harness.edits() == []


@pytest.mark.parametrize(
    ("labels", "args", "problem"),
    [
        (
            ("2-type:chore",),
            ["--add", "2-type:task"],
            "its 2-type:chore label is not canonical",
        ),
        (("4-epic:parent",), ["--add", "2-type:task"], "it is an epic parent"),
        (
            ("1-needs-triage",),
            ["--remove", "1-needs-triage"],
            "it would have no state label",
        ),
    ],
)
def test_a_family_conflict_is_refused(
    harness: Harness, labels: tuple[str, ...], args: list[str], problem: str
) -> None:
    review(harness, *labels, catalog=[*CANONICAL, "2-type:chore"])

    result = harness.run("set", "last", "1", *args)

    assert result.code == 1
    assert f"error: #1: conflict: {problem}" in result.stderr
    assert harness.edits() == []


def test_an_issue_the_run_skipped_is_refused(harness: Harness) -> None:
    review(harness)

    result = harness.run("set", "last", "2", "--add", "1-needs-triage")

    assert result.code == 1
    assert "skipped #2 (closed)" in result.stderr


def test_a_label_the_repository_lacks_points_to_labels(harness: Harness) -> None:
    review(harness, catalog=[n for n in CANONICAL if n != "1-needs-triage"])

    result = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert result.code == 1
    assert "create it with `jevlabel labels -R o/r`" in result.stderr
    assert harness.edits() == []


def test_a_failed_write_is_logged_and_a_retry_finishes(harness: Harness) -> None:
    review(harness)
    harness.world["fail_edit"] = True

    failed = harness.run("set", "last", "1", "--add", "1-needs-triage")
    harness.world["fail_edit"] = False
    retried = harness.run("set", "last", "1", "--add", "1-needs-triage")

    assert failed.code == 1
    assert "`gh issue edit` failed: HTTP 502: Bad Gateway" in failed.stderr
    assert retried.code == 0, retried.stderr
    assert [log["outcome"] for log in set_logs(harness)] == ["failed", "set"]
    assert harness.labels_of(1) == ["1-needs-triage"]

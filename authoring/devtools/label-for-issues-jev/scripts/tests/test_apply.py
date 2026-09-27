"""apply: only routine issues, only additions, reread first, verified after."""

from __future__ import annotations

import json
from pathlib import Path

from labeltest import Harness, issue

ROUTINE_ADD = ["2-type:bug", "1-needs-info", "3-pty:p2"]


def two_issues_one_routine(harness: Harness) -> None:
    """#1 is routine (missing repro steps); #2 is review (only nominated ready)."""
    harness.issues(issue(1), issue(2, title="Ready one"))
    harness.fake.overrides = {"Crash on start": {"bug_repro": 0.05}}
    assert harness.live().code == 0


def test_apply_adds_routine_labels_and_leaves_review_issues(harness: Harness) -> None:
    two_issues_one_routine(harness)

    result = harness.run("apply", "last", "--json")

    assert result.code == 0, result.stderr
    assert harness.labels_of(1) == ROUTINE_ADD
    assert harness.labels_of(2) == []
    assert harness.edits() == [
        ["issue", "edit", "1", "-R", "o/r", "--add-label", ",".join(ROUTINE_ADD)]
    ]
    log = json.loads(Path(result.json()["path"]).read_text())
    assert log["results"] == [
        {"number": 1, "labels": ROUTINE_ADD, "outcome": "applied", "detail": ""}
    ]


def test_dry_run_changes_nothing(harness: Harness) -> None:
    two_issues_one_routine(harness)

    result = harness.run("apply", "last", "--dry-run")

    assert result.code == 0, result.stderr
    assert "1 would-apply; 3 labels; nothing written" in result.stdout
    assert harness.edits() == []
    assert harness.labels_of(1) == []


def test_applying_twice_writes_once(harness: Harness) -> None:
    two_issues_one_routine(harness)

    harness.run("apply", "last")
    again = harness.run("apply", "last")

    assert again.code == 0, again.stderr
    assert "1 already" in again.stdout
    assert harness.edits() == []


def test_an_issue_changed_since_the_run_is_stale(harness: Harness) -> None:
    two_issues_one_routine(harness)
    harness.world["repos"]["o/r"]["issues"][0]["updatedAt"] = "2026-09-02T00:00:00Z"

    result = harness.run("apply", "last", "--json")

    assert result.code == 0
    assert result.json()["results"][0]["outcome"] == "stale"
    assert harness.edits() == []


def test_a_family_filled_meanwhile_is_a_conflict(harness: Harness) -> None:
    two_issues_one_routine(harness)
    harness.world["repos"]["o/r"]["issues"][0]["labels"] = [{"name": "1-needs-triage"}]

    result = harness.run("apply", "last", "--json")

    assert result.json()["results"][0] == {
        "number": 1,
        "labels": [],
        "outcome": "conflict",
        "detail": "its family already has a label: 1-needs-info",
    }
    assert harness.edits() == []


def test_a_failed_write_exits_1_and_keeps_the_log(harness: Harness) -> None:
    two_issues_one_routine(harness)
    harness.world["fail_edit"] = True

    result = harness.run("apply", "last")

    assert result.code == 1
    assert "error: #1: `gh issue edit` failed: HTTP 502: Bad Gateway" in result.stderr
    assert "1 of 1 issues failed" in result.stderr
    logs = list(
        (harness.state / "label-for-issues-jev" / "runs").glob("*.apply-*.json")
    )
    assert len(logs) == 1


def test_apply_can_target_selected_issues(harness: Harness) -> None:
    harness.issues(issue(1), issue(3, title="Third"))
    harness.fake.overrides = {
        "Crash on start": {"bug_repro": 0.05},
        "Third": {"bug_repro": 0.05},
    }
    assert harness.live().code == 0

    result = harness.run("apply", "last", "--issue", "3")

    assert result.code == 0, result.stderr
    assert [edit[2] for edit in harness.edits()] == ["3"]


def test_apply_names_an_unknown_run(harness: Harness) -> None:
    result = harness.run("apply", "20990101T000000Z-o-r")

    assert result.code == 1
    assert "no run record '20990101T000000Z-o-r'" in result.stderr


def test_one_unreadable_issue_does_not_stop_the_others(harness: Harness) -> None:
    harness.issues(issue(1), issue(3, title="Third"))
    harness.fake.overrides = {
        "Crash on start": {"bug_repro": 0.05},
        "Third": {"bug_repro": 0.05},
    }
    assert harness.live().code == 0
    harness.world["repos"]["o/r"]["issues"].pop(0)

    result = harness.run("apply", "last", "--json")

    assert result.code == 1
    outcomes = {r["number"]: r["outcome"] for r in result.json()["results"]}
    assert outcomes == {1: "failed", 3: "applied"}
    assert harness.labels_of(3) == ROUTINE_ADD
    assert "error: #1: `gh issue view` failed" in result.stderr
    logs = list(
        (harness.state / "label-for-issues-jev" / "runs").glob("*.apply-*.json")
    )
    assert len(logs) == 1

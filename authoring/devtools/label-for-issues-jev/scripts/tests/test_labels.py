"""labels: create missing canonical labels, fix exact names, report look-alikes."""

from __future__ import annotations

from pathlib import Path

from labeltest import CANONICAL, META, Harness, issue


def logs(harness: Harness) -> list[Path]:
    return sorted((harness.state / "label-for-issues-jev" / "labels").glob("*.json"))


def without(*names: str) -> list[str]:
    return [name for name in CANONICAL if name not in names]


def test_labels_creates_missing_ones_and_fixes_exact_names(harness: Harness) -> None:
    harness.add_repo(
        "o/r",
        labels=without("1-needs-info", "3-pty:p3"),
        meta={"2-type:bug": {"color": "FFFFFF", "description": "Old words"}},
    )

    result = harness.run("labels", "-R", "o/r", "--json")

    assert result.code == 0, result.stderr
    changed = {
        r["name"]: r["outcome"]
        for r in result.json()["results"]
        if r["outcome"] != "ok"
    }
    assert changed == {
        "1-needs-info": "created",
        "2-type:bug": "fixed",
        "3-pty:p3": "created",
    }
    assert [call[:3] for call in harness.writes()] == [
        ["label", "create", "1-needs-info"],
        ["label", "edit", "2-type:bug"],
        ["label", "create", "3-pty:p3"],
    ]
    meta = harness.world["repos"]["o/r"]["label_meta"]
    for name in ("1-needs-info", "2-type:bug", "3-pty:p3"):
        assert meta[name] == META[name]
    assert len(logs(harness)) == 1


def test_dry_run_writes_nothing(harness: Harness) -> None:
    harness.add_repo("o/r", labels=without("1-needs-info"))

    result = harness.run("labels", "-R", "o/r", "--dry-run")

    assert result.code == 0, result.stderr
    assert (
        result.stdout.strip()
        == "labels o/r --dry-run: 1 would-create, 15 ok; nothing written"
    )
    assert harness.writes() == []
    assert logs(harness) == []


def test_running_twice_writes_once(harness: Harness) -> None:
    harness.add_repo("o/r", labels=without("1-needs-info"))

    harness.run("labels", "-R", "o/r")
    again = harness.run("labels", "-R", "o/r")

    assert again.code == 0, again.stderr
    assert again.stdout.strip() == "labels o/r: 16 ok"
    assert harness.writes() == []


def test_near_duplicates_are_reported_and_never_touched(harness: Harness) -> None:
    harness.add_repo(
        "o/r",
        labels=[*CANONICAL, "bug", "Priority: P1", "wayfinder:task"],
        issues=[issue(3, labels=("bug",)), issue(4)],
    )

    result = harness.run("labels", "-R", "o/r", "--json")

    assert result.code == 0, result.stderr
    assert result.json()["lookalikes"] == [
        {
            "name": "Priority: P1",
            "canonical": "3-pty:p1",
            "kind": "near duplicate",
            "issues": [],
        },
        {
            "name": "bug",
            "canonical": "2-type:bug",
            "kind": "near duplicate",
            "issues": [3],
        },
    ]
    assert "warning: bug looks like 2-type:bug (issues: #3)" in result.stderr
    assert harness.writes() == []


def test_a_case_variant_blocks_its_canonical_label(harness: Harness) -> None:
    labels = ["2-Type:Bug" if name == "2-type:bug" else name for name in CANONICAL]
    harness.add_repo("o/r", labels=labels)

    result = harness.run("labels", "-R", "o/r")

    assert result.code == 1
    assert (
        "error: 2-type:bug: blocked: 2-Type:Bug holds its name in another case"
        in result.stderr
    )
    assert "rename a case variant only after the user approves" in result.stderr
    assert "error: not in place: 2-type:bug; see the output" in result.stderr
    assert harness.writes() == []


def test_a_failed_write_exits_1_and_keeps_the_log(harness: Harness) -> None:
    harness.add_repo("o/r", labels=without("1-needs-info"))
    harness.world["fail_label"] = True

    result = harness.run("labels", "-R", "o/r", "--json")

    assert result.code == 1
    assert (
        "error: 1-needs-info: failed: `gh label create` failed: HTTP 502: Bad Gateway"
        in result.stderr
    )
    assert result.json()["counts"]["failed"] == 1
    assert len(logs(harness)) == 1

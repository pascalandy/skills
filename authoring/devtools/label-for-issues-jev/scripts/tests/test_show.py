"""show: one issue's thread, links, and what the run found; it never writes."""

from __future__ import annotations

import tomllib
from labeltest import Harness, comment, issue

BODY = """The app crashes on start.

Blocked by #5 and #6. Then ship.
Epic note: #12 is blocked by #13.

## Blocked by

- [#3], because the parser lands first
- https://github.com/o/r/issues/4

Then #11 follows.

[#9]: https://github.com/o/r/issues/9
"""


def linked(number: int, title: str, state: str = "OPEN", kind: str = "issues") -> dict:
    url = f"https://github.com/o/r/{kind}/{number}"
    return {"number": number, "title": title, "state": state, "url": url}


def one_review_issue(harness: Harness) -> None:
    """#1 is in review because whether a decision is open is uncertain (0.5)."""
    thread = (
        comment("I can reproduce it", author="alice", number=1),
        comment("Parser first", author="pascal", association="OWNER", number=2),
        comment("Coverage report", author="codecov", number=3),
    )
    first = issue(1, body=BODY, comments=thread)
    first |= {"parent": 7, "blocked_by": [8], "pull_requests": [10]}
    harness.issues(
        first,
        issue(3, title="Parser"),
        issue(4, title="Old", state="CLOSED"),
        issue(5, title="Merged fix", state="MERGED", kind="pull"),
        issue(7, title="Epic", labels=("4-epic:parent",)),
        issue(8, title="Native blocker"),
        issue(10, title="Closing fix", kind="pull"),
        issue(11, title="Later"),
    )
    harness.fake.overrides = {"Crash on start": {"open_decision": 0.5}}
    assert harness.live("--issue", "1").code == 0


def test_show_prints_the_thread_links_and_the_run(harness: Harness) -> None:
    one_review_issue(harness)
    band = tomllib.loads(harness.questions.read_text())["open_decision"]

    view = harness.run("show", "last", "--issue", "1", "--json").json()

    assert [(c["author"], c["role"]) for c in view["comments"]] == [
        ("alice", "reporter"),
        ("pascal", "maintainer"),
        ("codecov", "bot"),
    ]
    triage = view["triage"]
    assert (triage["queue"], triage["stale"]) == ("review", None)
    assert triage["reasons"] == ["unclear whether 1-needs-triage applies"]
    assert triage["fill"] == ["2-type:bug", "3-pty:p2"]
    answer = triage["medium_answers"][0]
    assert len(triage["medium_answers"]) == 1
    assert {key: answer[key] for key in ("id", "value", "no", "yes")} == {
        "id": "open_decision",
        "value": 0.5,
        "no": band["no"],
        "yes": band["yes"],
    }
    assert answer["question"] == band["instructions"]
    assert view["links"] == {
        "parent": [linked(7, "Epic")],
        "sub_issues": [],
        "blocked_by": [
            {**linked(8, "Native blocker"), "source": "relationship"},
            {**linked(5, "Merged fix", "MERGED", "pull"), "source": "body"},
            {
                "number": 6,
                "title": "",
                "state": "NOT FOUND",
                "url": "",
                "source": "body",
            },
            {**linked(3, "Parser"), "source": "body"},
            {**linked(4, "Old", "CLOSED"), "source": "body"},
        ],
        "blocking": [],
        "pull_requests": [linked(10, "Closing fix", kind="pull")],
    }
    assert harness.writes() == []


def test_show_reads_as_text(harness: Harness) -> None:
    one_review_issue(harness)

    result = harness.run("show", "last", "--issue", "1")

    assert result.code == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[:3] == [
        "#1 Crash on start",
        "https://github.com/o/r/issues/1",
        "state: open; labels: none",
    ]
    assert lines[3].endswith(": review; unchanged since the run")
    assert "  reason: unclear whether 1-needs-triage applies" in lines
    assert "blocked by #3 (open, named in the body): Parser" in lines
    assert "parent #7 (open): Epic" in lines
    assert "comment 2 · maintainer · pascal" in lines


def test_show_names_a_change_since_the_run(harness: Harness) -> None:
    one_review_issue(harness)
    harness.change(1, "IssueComment", "2026-10-01T00:00:00Z")

    view = harness.run("show", "last", "--issue", "1", "--json").json()

    assert view["triage"]["stale"] == "new comment"


def test_an_issue_closed_before_the_run_is_not_stale(harness: Harness) -> None:
    harness.issues(issue(2, title="Closed", state="CLOSED"))
    assert harness.live("--state", "all").code == 0

    triage = harness.run("show", "last", "--issue", "2", "--json").json()["triage"]

    assert (triage["queue"], triage["stale"]) == ("skip", None)


def test_show_reads_an_issue_outside_the_run(harness: Harness) -> None:
    one_review_issue(harness)

    result = harness.run("show", "last", "--issue", "3", "--json")

    assert result.code == 0, result.stderr
    assert (result.json()["title"], result.json()["triage"]) == ("Parser", None)


def test_show_refuses_a_pull_request(harness: Harness) -> None:
    one_review_issue(harness)

    result = harness.run("show", "last", "--issue", "5")

    assert result.code == 1
    assert "error: #5 is a pull request" in result.stderr

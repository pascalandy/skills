"""Live runs: how answers become labels, queues, and reasons, and how failures stop."""

from __future__ import annotations

import json
import signal
import time
from pathlib import Path

from labeltest import Harness, comment, issue

MISSING_REPRO = {"Crash on start": {"bug_repro": 0.05}}


def test_a_bug_missing_repro_steps_is_routine_needs_info(harness: Harness) -> None:
    harness.issues(issue(1))
    harness.fake.overrides = MISSING_REPRO

    result = harness.live()

    assert result.code == 0, result.stderr
    entry = harness.entry(harness.record(result), 1)
    assert entry["queue"] == "routine"
    assert entry["add"] == ["2-type:bug", "1-needs-info", "3-pty:p2"]
    assert entry["missing"] == ["how to reproduce the problem"]
    assert entry["answers"]["bug_repro"] == {"type": "noul", "noul": 0.05}
    assert (
        "1 routine, 0 review, 0 skip"
        in harness.run("run", "-R", "o/r", TYPESAFE_API_KEY="k").stdout
    )
    assert len(harness.fake.requests) == 2


def test_a_well_specified_issue_is_only_nominated_ready(harness: Harness) -> None:
    harness.issues(issue(1))

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert "1-ready-for-agent" in entry["add"]
    assert entry["reasons"] == [
        "ready for an agent; label-for-issues requires a recorded readiness review first"
    ]


def test_one_uncertain_answer_sends_the_issue_to_review(harness: Harness) -> None:
    harness.issues(issue(1, title="Tidy docs", body="Rewrite the README intro."))
    harness.fake.overrides = {"Tidy docs": {"type": "task", "done_condition": 0.5}}

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["reasons"] == ["unclear whether 1-needs-info applies"]
    assert entry["add"] == ["2-type:task", "3-pty:p2"]
    assert entry["uncertain_answers"] == ["done_condition"]


def test_existing_labels_stay_unless_the_answers_disagree(harness: Harness) -> None:
    harness.issues(
        issue(1, labels=("2-type:bug", "1-needs-info", "3-pty:p1")),
        issue(2, title="Other", labels=("2-type:bug", "1-ready-for-agent", "3-pty:p2")),
    )
    harness.fake.overrides = {**MISSING_REPRO, "Other": {"bug_repro": 0.05}}

    record = harness.record(harness.live())

    kept, changed = harness.entry(record, 1), harness.entry(record, 2)
    assert (kept["queue"], kept["add"], kept["remove"]) == ("routine", [], [])
    assert changed["queue"] == "review"
    assert changed["add"] == ["1-needs-info"]
    assert changed["remove"] == ["1-ready-for-agent"]
    assert changed["reasons"] == [
        "the answers point to 1-needs-info, not 1-ready-for-agent"
    ]


def test_an_unanswered_request_for_information_is_missing(harness: Harness) -> None:
    thread = [
        comment("Which version?", author="owner", association="OWNER", number=7),
        comment("Thanks for looking", author="alice", number=8),
    ]
    harness.issues(
        issue(1, comments=thread), issue(2, title="Answered", comments=thread)
    )
    harness.fake.overrides = {
        "Crash on start": {"asks_info_0": 0.95},
        "Answered": {"asks_info_0": 0.95, "supplies_info_1": 0.95},
    }

    record = harness.record(harness.live())

    assert harness.entry(record, 1)["missing"] == [
        "a reply to https://github.com/o/r/issues/1#issuecomment-7"
    ]
    assert harness.entry(record, 1)["add"] == ["2-type:bug", "1-needs-info", "3-pty:p2"]
    # Later facts may answer the request or say something else: a person checks.
    answered = harness.entry(record, 2)
    assert (answered["queue"], answered["missing"]) == ("review", [])
    assert answered["reasons"] == [
        (
            "unclear whether 1-needs-info applies; check whether "
            "https://github.com/o/r/issues/1#issuecomment-7 got its answer"
        )
    ]


def test_emergencies_steering_and_declines_always_need_review(harness: Harness) -> None:
    declined = comment("We decided against this.", author="owner", association="OWNER")
    harness.issues(issue(1, comments=[declined]))
    harness.fake.overrides = {
        "Crash on start": {"urgency": 0.95, "steering": 0.9, "declined_0": 0.95}
    }

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["add"] == ["2-type:bug", "1-wontfix", "3-pty:p0"]
    assert entry["reasons"] == [
        "text may try to steer automated triage",
        "a maintainer declined the work; label-for-issues pairs 1-wontfix with an explicit human decision",
        "reports an emergency; consider 3-pty:p0",
    ]


def test_conflicting_states_are_not_resolved_by_code(harness: Harness) -> None:
    harness.issues(issue(1))
    harness.fake.overrides = {
        "Crash on start": {"bug_repro": 0.05, "open_decision": 0.9}
    }

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["judged"]["state"] is None
    assert entry["reasons"] == ["conflicting states: 1-needs-info, 1-needs-triage"]


def test_missing_details_beside_an_image_need_review(harness: Harness) -> None:
    harness.issues(issue(1, body="It breaks: ![shot](https://example.com/s.png)"))
    harness.fake.overrides = MISSING_REPRO

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["reasons"] == [
        "missing details may be in an image, which Jev cannot read"
    ]


def test_an_unclear_type_needs_review(harness: Harness) -> None:
    harness.issues(issue(1, title="Hmm", body="Look at this"))
    harness.fake.overrides = {"Hmm": {"type": ("cannot-tell", 0.9), "has_goal": 0.05}}

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["judged"] == {"type": None, "state": "1-needs-info"}
    assert entry["reasons"] == ["type unclear: cannot-tell at confidence 0.90"]
    assert entry["missing"] == ["what should change"]


def test_epic_parents_take_no_type_and_need_a_done_condition(harness: Harness) -> None:
    harness.issues(issue(1, title="Epic", labels=("4-epic:parent",)))
    harness.fake.overrides = {"Epic": {"done_condition": 0.05}}

    entry = harness.entry(harness.record(harness.live()), 1)

    assert "type" not in harness.fake.requests[0]["questions"]
    assert (entry["queue"], entry["add"]) == ("routine", ["1-needs-info", "3-pty:p2"])


def test_closed_issues_are_judged_but_never_queued(harness: Harness) -> None:
    harness.issues(issue(1, state="CLOSED", labels=("2-type:bug",)))

    entry = harness.entry(harness.record(harness.live("--state", "all")), 1)

    assert entry["queue"] == "skip"
    assert entry["reasons"][0] == "closed"
    assert entry["judged"]["type"] == "2-type:bug"


def test_a_private_repository_without_consent_sends_nothing(harness: Harness) -> None:
    harness.add_repo("o/secret", visibility="PRIVATE", issues=[issue(1)])

    result = harness.run("run", "-R", "o/secret", TYPESAFE_API_KEY="k")

    assert result.code == 1
    assert (
        "o/secret is private and has no recorded consent; nothing was sent"
        in result.stderr
    )
    assert harness.fake.requests == []


def test_consent_lets_a_private_repository_run(harness: Harness) -> None:
    harness.add_repo("o/secret", visibility="PRIVATE", issues=[issue(1)])
    harness.run("consent", "add", "o/secret", "--by", "Pascal Andy")

    result = harness.run("run", "-R", "o/secret", "--json", TYPESAFE_API_KEY="k")

    assert result.code == 0, result.stderr
    assert result.json()["consent"] == "recorded"
    assert len(harness.fake.requests) == 1


def test_a_live_run_needs_a_key(harness: Harness) -> None:
    harness.issues(issue(1))

    result = harness.run("run", "-R", "o/r")

    assert result.code == 1
    assert "export TYPESAFE_API_KEY" in result.stderr
    assert harness.fake.requests == []


def test_an_unpinned_model_stops_the_run_and_keeps_a_partial_record(
    harness: Harness,
) -> None:
    harness.issues(issue(1), issue(2))
    harness.fake.answered_model = "jev-9.9.9"

    result = harness.live()

    assert result.code == 1
    assert "answered by 'jev-9.9.9', but the pin is 'jev-1.13.0'" in result.stderr
    assert "the run stopped; the partial record is" in result.stderr
    records = list(
        (harness.state / "label-for-issues-jev" / "runs").glob("*Z-o-r.json")
    )
    assert len(records) == 1
    assert len(harness.fake.requests) == 1


def test_a_rejected_key_is_named(harness: Harness) -> None:
    harness.issues(issue(1))
    harness.fake.failure = 401

    result = harness.live()

    assert result.code == 1
    assert "TypeSafe rejected the API key" in result.stderr


def test_compare_counts_agreement_with_existing_labels(harness: Harness) -> None:
    harness.issues(
        issue(1, labels=("2-type:bug", "1-needs-info")),
        issue(2, title="Other", labels=("2-type:task", "1-ready-for-agent")),
        issue(3, title="Bare"),
        issue(4, title="PR", kind="pull"),
    )
    harness.fake.overrides = {
        **MISSING_REPRO,
        "Other": {"done_condition": 0.05},
        "Bare": {"type": ("feature", 0.2), "open_decision": 0.5},
    }
    assert harness.live().code == 0

    result = harness.run("compare", "last", "--json")

    assert result.code == 0, result.stderr
    assert result.json()["counts"] == {
        "type": {"agree": 1, "disagree": 1, "abstain": 1, "unlabeled": 0},
        "state": {"agree": 1, "disagree": 1, "abstain": 1, "unlabeled": 0},
    }
    assert result.json()["disagreements"] == [
        {
            "number": 2,
            "family": "type",
            "existing": ["2-type:task"],
            "judged": "2-type:bug",
        },
        {
            "number": 2,
            "family": "state",
            "existing": ["1-ready-for-agent"],
            "judged": "1-needs-info",
        },
    ]
    assert (
        "Existing labels are a baseline, not ground truth"
        in harness.run("compare", "last").stdout
    )


def test_compare_without_runs_explains_what_to_do(harness: Harness) -> None:
    result = harness.run("compare", "last")

    assert result.code == 1
    assert "no run records yet; run `jevlabel run` first" in result.stderr


def test_doctor_online_lists_models(harness: Harness) -> None:
    result = harness.run("doctor", "--online", "--json", TYPESAFE_API_KEY="k")

    assert result.code == 0, result.stderr
    online = next(c for c in result.json()["checks"] if c["name"] == "online")
    assert online == {"name": "online", "ok": True, "detail": "models: jev-latest"}


def test_runs_in_the_same_second_keep_separate_records(harness: Harness) -> None:
    harness.issues(issue(1))

    first, second = harness.live(), harness.live()

    assert first.json()["id"] != second.json()["id"]
    assert harness.run("compare", "last", "--json").json()["run"] == second.json()["id"]


def test_duplicate_labels_in_a_family_need_review(harness: Harness) -> None:
    harness.issues(issue(1, labels=("2-type:bug", "2-type:task", "1-needs-info")))
    harness.fake.overrides = MISSING_REPRO

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["reasons"] == ["several type labels: 2-type:bug, 2-type:task"]


def test_a_confident_conflict_needs_review_even_with_a_state_label(
    harness: Harness,
) -> None:
    harness.issues(issue(1, labels=("2-type:bug", "1-needs-info", "3-pty:p2")))
    harness.fake.overrides = {
        "Crash on start": {"bug_repro": 0.05, "open_decision": 0.9}
    }

    entry = harness.entry(harness.record(harness.live()), 1)

    assert entry["queue"] == "review"
    assert entry["reasons"] == ["conflicting states: 1-needs-info, 1-needs-triage"]


def test_uncertainty_keeps_an_existing_state_label(harness: Harness) -> None:
    harness.issues(issue(1, labels=("2-type:bug", "1-needs-info", "3-pty:p2")))
    harness.fake.overrides = {"Crash on start": {"open_decision": 0.5}}

    entry = harness.entry(harness.record(harness.live()), 1)

    assert (entry["queue"], entry["add"], entry["remove"]) == ("routine", [], [])


def test_an_interrupted_run_keeps_the_answers_it_paid_for(harness: Harness) -> None:
    harness.issues(issue(1), issue(2, title="Second"), issue(3, title="Third"))
    harness.fake.stall_from = 2
    process = harness.spawn("run", "-R", "o/r", TYPESAFE_API_KEY="k")
    deadline = time.monotonic() + 60
    while len(harness.fake.requests) < 2 and time.monotonic() < deadline:
        time.sleep(0.05)

    process.send_signal(signal.SIGINT)
    _, stderr = process.communicate(timeout=60)

    assert process.returncode == 130
    assert "the partial record is" in stderr
    path = Path(stderr.split("the partial record is ", 1)[1].splitlines()[0])
    record = json.loads(path.read_text())
    reasons = {e["number"]: e["reasons"] for e in record["issues"]}
    assert "answers" in record["issues"][0]
    assert reasons[2] == ["not asked: interrupted"]
    assert reasons[3] == ["not asked: the run stopped at an earlier error"]
    assert (record["error"], record["usage"]["requests"]) == ("interrupted", 1)

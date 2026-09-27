"""doctor, consent, and the checks that keep questions and vocabulary honest."""

from __future__ import annotations

import tomllib
from labeltest import Harness, issue


def checks(result_json: dict) -> dict[str, bool]:
    return {check["name"]: check["ok"] for check in result_json["checks"]}


def test_doctor_reports_every_check_and_fails_without_a_key(harness: Harness) -> None:
    result = harness.run("doctor", "-R", "o/r", "--json")

    assert result.code == 1
    assert checks(result.json()) == {
        "gh": True,
        "vocabulary": True,
        "questions": True,
        "key": False,
        "consent": True,
        "repository": True,
        "labels": True,
    }
    assert "error: key: TYPESAFE_API_KEY is not set" in result.stderr


def test_doctor_passes_with_a_key(harness: Harness) -> None:
    result = harness.run("doctor", "-R", "o/r", TYPESAFE_API_KEY="test-key")

    assert result.code == 0, result.stderr
    assert (
        result.stdout.strip()
        == "ok: gh, vocabulary, questions, key, consent, repository, labels"
    )


def test_doctor_names_missing_labels_and_the_setup_skill(harness: Harness) -> None:
    harness.add_repo("o/r", labels=["bug"])

    result = harness.run("doctor", "-R", "o/r", TYPESAFE_API_KEY="k")

    assert result.code == 1
    assert "error: labels: o/r lacks 0-impediment" in result.stderr
    assert "label-for-issues" in result.stderr


def test_private_repository_needs_recorded_consent(harness: Harness) -> None:
    harness.add_repo("o/secret", visibility="PRIVATE")

    before = harness.run("doctor", "-R", "o/secret", TYPESAFE_API_KEY="k")
    added = harness.run("consent", "add", "o/secret", "--by", "Pascal Andy")
    after = harness.run("doctor", "-R", "o/secret", TYPESAFE_API_KEY="k")

    assert before.code == 1
    assert "o/secret is private and has no recorded consent" in before.stderr
    assert "jevlabel consent add o/secret" in before.stderr
    assert added.code == 0 and added.stdout.startswith("approved o/secret")
    assert after.code == 0, after.stderr


def test_consent_round_trip_writes_readable_toml(harness: Harness) -> None:
    harness.run("consent", "add", "o/b", "--by", 'Pat "P" Doe')
    harness.run("consent", "add", "o/a", "--by", "Sam")

    listed = harness.run("consent", "list", "--json").json()["consent"]
    removed = harness.run("consent", "remove", "o/b")
    again = harness.run("consent", "remove", "o/b")

    assert [entry["repo"] for entry in listed] == ["o/a", "o/b"]
    assert listed[1]["approved_by"] == 'Pat "P" Doe'
    assert listed[1]["terms"] == "typesafe-2026-09-26"
    assert (removed.stdout.strip(), again.stdout.strip()) == (
        "removed consent for o/b",
        "o/b had no consent",
    )
    stored = tomllib.loads(
        (harness.config / "label-for-issues-jev" / "consent.toml").read_text()
    )
    assert list(stored) == ["o/a"]


def test_consent_add_requires_who_approved(harness: Harness) -> None:
    assert harness.run("consent", "add", "o/r").code == 2
    assert harness.run("consent", "add").code == 2


def test_consent_under_older_terms_is_not_valid(harness: Harness) -> None:
    harness.add_repo("o/secret", visibility="PRIVATE")
    path = harness.config / "label-for-issues-jev" / "consent.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        '["o/secret"]\napproved_by = "Sam"\napproved_on = "2026-01-01"\nterms = "old"\n'
    )

    result = harness.run("doctor", "-R", "o/secret", TYPESAFE_API_KEY="k")

    assert result.code == 1
    assert (
        "names terms 'old', but the current terms are 'typesafe-2026-09-26'"
        in result.stderr
    )


def test_questions_must_keep_a_no_match_option(harness: Harness) -> None:
    text = harness.questions.read_text()
    harness.questions.write_text(text.replace("cannot-tell = ", "unsure = "))
    harness.issues(issue(1))

    result = harness.run("run", "-R", "o/r", "--dry-run")

    assert result.code == 1
    assert "questions.toml: type: criteria must be exactly" in result.stderr


def test_questions_may_only_name_paths_that_code_builds(harness: Harness) -> None:
    text = harness.questions.read_text()
    harness.questions.write_text(
        text.replace("`issue` ask for", "`issue.labels` ask for")
    )

    result = harness.run("run", "-R", "o/r", "--dry-run")

    assert result.code == 1
    assert (
        "type: `issue.labels` is not a path in the state code builds" in result.stderr
    )


def test_questions_need_ordered_thresholds(harness: Harness) -> None:
    text = harness.questions.read_text()
    harness.questions.write_text(
        text.replace("yes = 0.8\nno = 0.2", "yes = 0.2\nno = 0.8", 1)
    )

    result = harness.run("run", "-R", "o/r", "--dry-run")

    assert result.code == 1
    assert "has_goal: thresholds need 0 < no < yes < 1" in result.stderr


def test_vocabulary_drift_stops_every_run(harness: Harness) -> None:
    vocabulary = harness.engine.parents[2] / "label-for-issues" / "SKILL.md"
    vocabulary.write_text(
        vocabulary.read_text().replace('"1-needs-info"', '"1-need-info"')
    )

    result = harness.run("run", "-R", "o/r", "--dry-run")

    assert result.code == 1
    assert "label-for-issues no longer defines 1-needs-info" in result.stderr

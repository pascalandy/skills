"""run --dry-run: which issues are asked, and exactly what each request would send."""

from __future__ import annotations

from labeltest import Harness, comment, issue


def test_help_needs_no_network(harness: Harness) -> None:
    bare = harness.run()
    detail = harness.run("run", "--help")

    assert (bare.code, detail.code) == (0, 0)
    assert "commands:" in bare.stdout and "--dry-run" in detail.stdout
    assert harness.calls() == []


def test_preview_writes_the_payload_and_skips_pull_requests_and_agent_work(
    harness: Harness,
) -> None:
    harness.issues(
        issue(1),
        issue(2, kind="pull"),
        issue(3, labels=("1-wip-by-agent",)),
    )

    result = harness.run("run", "-R", "o/r", "--dry-run", "--json")

    assert result.code == 0, result.stderr
    preview = harness.preview(result)
    skips = {i["number"]: i["skip"] for i in preview["issues"]}
    assert skips == {
        1: None,
        2: "pull request",
        3: "an agent is working on it (1-wip-by-agent)",
    }
    assert preview["estimated"]["requests"] == 1
    assert preview["model"] == "jev-1.13.0"
    assert harness.request_for(preview, 1)["request"]["state"]["issue"] == {
        "title": "Crash on start",
        "body": "The app crashes when I run `app start`.",
    }


def test_state_keeps_people_and_drops_bots_hidden_and_managed_comments(
    harness: Harness,
) -> None:
    harness.issues(
        issue(
            1,
            body="See ![screen](https://example.com/a.png)",
            comments=[
                comment("Which version?", author="owner", association="OWNER"),
                comment("v2.1", author="alice"),
                comment("CI passed", author="github-actions"),
                comment("spam", author="mallory", minimized=True),
                comment("<!-- label-for-issues:decision -->\n## #1 · Old triage"),
                comment("Same here", author="carol"),
            ],
        )
    )

    preview = harness.preview(harness.run("run", "-R", "o/r", "--dry-run", "--json"))

    item = harness.request_for(preview, 1)
    assert item["request"]["state"]["comments"] == [
        {"author_role": "maintainer", "body": "Which version?"},
        {"author_role": "reporter", "body": "v2.1"},
        {"author_role": "other", "body": "Same here"},
    ]
    assert item["facts"]["has_images"] is True
    assert item["facts"]["managed_comment"] is True
    questions = item["request"]["questions"]
    assert {q for q in questions if q.startswith("declined")} == {"declined_0"}
    assert {"asks_info_2", "supplies_info_2", "type", "steering"} <= set(questions)
    assert questions["asks_info_1"]["instructions"] == (
        "Does `comments[1].body` ask for specific information that the issue is missing?"
    )


def test_epic_parent_gets_no_type_question(harness: Harness) -> None:
    harness.issues(issue(1, labels=("4-epic:parent",)))

    preview = harness.preview(harness.run("run", "-R", "o/r", "--dry-run", "--json"))

    assert "type" not in harness.request_for(preview, 1)["request"]["questions"]


def test_long_threads_drop_the_oldest_comments_from_others_first(
    harness: Harness,
) -> None:
    thread = [
        comment(f"maintainer note {n}", author="owner", association="OWNER", number=n)
        for n in range(5)
    ] + [comment(f"me too {n}", number=100 + n) for n in range(55)]
    harness.issues(issue(1, comments=thread))

    preview = harness.preview(harness.run("run", "-R", "o/r", "--dry-run", "--json"))

    item = harness.request_for(preview, 1)
    bodies = [c["body"] for c in item["request"]["state"]["comments"]]
    assert item["facts"]["comments_sent"] == 40
    assert item["facts"]["comments_omitted"] == 20
    assert bodies[:5] == [f"maintainer note {n}" for n in range(5)]
    assert bodies[5] == "me too 20" and bodies[-1] == "me too 54"


def test_a_huge_body_is_truncated_to_fit_one_request(harness: Harness) -> None:
    harness.issues(issue(1, body="word " * 60_000))

    preview = harness.preview(harness.run("run", "-R", "o/r", "--dry-run", "--json"))

    item = harness.request_for(preview, 1)
    assert item["facts"]["body_truncated"] is True
    assert item["request"]["state"]["issue"]["body"].endswith("\n[truncated]")
    assert item["estimated_tokens"] <= 60_000


def test_a_full_comment_page_is_refetched_in_full(harness: Harness) -> None:
    harness.issues(issue(1, comments=[comment(f"c{n}") for n in range(120)]), issue(2))

    result = harness.run("run", "-R", "o/r", "--dry-run", "--json")

    assert result.code == 0, result.stderr
    views = [call for call in harness.calls() if call[:2] == ["issue", "view"]]
    assert [call[2] for call in views] == ["1"]


def test_request_cap_skips_later_issues(harness: Harness) -> None:
    harness.issues(issue(1), issue(2), issue(3, labels=("1-wip-by-agent",)))

    preview = harness.preview(
        harness.run("run", "-R", "o/r", "--dry-run", "--max-requests", "1", "--json")
    )

    skips = {i["number"]: i["skip"] for i in preview["issues"]}
    assert skips[1] is None
    assert skips[2] == "request cap of 1 reached"
    assert preview["estimated"]["requests"] == 1


def test_selected_issues_are_fetched_one_by_one(harness: Harness) -> None:
    harness.issues(issue(1), issue(2), issue(3))

    result = harness.run(
        "run",
        "-R",
        "o/r",
        "--issue",
        "3",
        "--issue",
        "1",
        "--issue",
        "3",
        "--dry-run",
        "--json",
    )

    assert [i["number"] for i in result.json()["issues"]] == [3, 1]
    assert [c[:3] for c in harness.calls() if c[0] == "issue"] == [
        ["issue", "view", "3"],
        ["issue", "view", "1"],
    ]


def test_missing_canonical_labels_warn_but_still_preview(harness: Harness) -> None:
    harness.add_repo("o/r", labels=["bug"], issues=[issue(1)])

    result = harness.run("run", "-R", "o/r", "--dry-run", "--json")

    assert result.code == 0
    assert "warning: o/r lacks canonical labels" in result.stderr
    assert "1-needs-info" in result.json()["missing_labels"]


def test_private_repositories_preview_without_consent(harness: Harness) -> None:
    harness.add_repo("o/secret", visibility="PRIVATE", issues=[issue(1)])

    result = harness.run("run", "-R", "o/secret", "--dry-run", "--json")

    assert result.code == 0, result.stderr
    assert result.json()["consent"] == "o/secret is private and has no recorded consent"


def test_bad_arguments_exit_2(harness: Harness) -> None:
    assert harness.run("run", "-R", "not-a-repo", "--dry-run").code == 2
    assert harness.run("run", "-R", "o/r", "--max-requests", "0", "--dry-run").code == 2
    assert harness.run("run", "--dry-run").code == 2


def test_gh_failures_name_the_command(harness: Harness) -> None:
    result = harness.run("run", "-R", "o/missing", "--dry-run")

    assert result.code == 1
    assert "error: `gh repo view` failed" in result.stderr
    assert "rerun with --verbose for details" in result.stderr

"""Story counts retain the facts visible at each instant, including across restarts."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

import github
import oracles
import pipeline
import pytest
import t3
from test_live import HC, W, live_run
from test_record import fake_env

if TYPE_CHECKING:
    from playwright.sync_api import Browser


@pytest.mark.parametrize(
    "original, edited, before, after",
    [
        ("closed #10. Resolves #11.", "Closes #11.", 2, 1),
        # A native link has no edit timestamp until a body revision names it.
        ("Closes #11.", "Closes #10. Closes #11.", 1, 2),
        ("", "Closes #11.", 1, 1),
        ("Closes typo-owner/no-such-repo#1. Closes #11.", "Closes #11.", 1, 1),
    ],
)
def test_an_edit_and_a_legacy_cache_keep_the_counts_already_shown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    chromium: Browser,
    original: str,
    edited: str,
    before: int,
    after: int,
) -> None:
    for name, value in fake_env(tmp_path).items():
        monkeypatch.setenv(name, value)
    db = live_run(tmp_path)
    now = time.time()
    edited_at = pipeline.t3_time(now + 1)
    phase = 0
    reader = github.gh_reader(10)

    def read(args: list[str]) -> dict:
        result = reader(args)
        repository = (result.get("data") or {}).get("repository") or {}
        pr = repository.get("p21") or repository.get("e21")
        if pr:
            pr["body"] = (original, edited, "Closes #10.")[phase]
            pr["mergedAt"] = pr["closedAt"] = (
                pipeline.t3_time(now + 2) if phase else None
            )
            pr["closingIssuesReferences"]["nodes"] = [
                {"number": n, "repository": {"nameWithOwner": W}}
                for n in (
                    [10, 11] if original else [],
                    [11] if after == 1 else [10, 11],
                    [10],
                )[phase]
            ]
            pr["userContentEdits"] = {
                "nodes": [
                    *(
                        [
                            {
                                "editedAt": pipeline.t3_time(now + 130),
                                "diff": "Closes #10.",
                            }
                        ]
                        if phase == 2
                        else []
                    ),
                    *([{"editedAt": edited_at, "diff": edited}] if phase else []),
                    {"editedAt": pr["createdAt"], "diff": original},
                ],
            }
            pr["lastEditedAt"] = pr["userContentEdits"]["nodes"][0]["editedAt"]
        return result

    con = t3.connect(db.path, 5)
    try:
        snap, _ = t3.load(con, [HC])
        gh = github.Cached(read)

        def page(facts: github.Facts, at: float) -> dict:
            data, _ = pipeline.page_data(
                snap, facts.at(pipeline.t3_time(at)), [HC], now=at
            )
            return data["brigades"][0]

        shown = page(gh, now)
        assert oracles.story_counts_at(shown, now)["cook-1.1"] == before
        if not original:
            assert shown["cooks"]["cook-1.1"]["prs"] == 1
        phase = 1
        gh.refresh()
        final = page(gh, now + 120)
        assert oracles.story_counts_at(final, now)["cook-1.1"] == before
        assert oracles.story_counts_at(final, now + 120)["cook-1.1"] == after

        # The old service cached this closed PR forever without its edit history.
        legacy = gh.dump()
        legacy["prs"][f"{W}#21"] = {
            k: v for k, v in legacy["prs"][f"{W}#21"].items() if k != "refHistory"
        }
        cache = tmp_path / "github.json"
        cache.write_text(json.dumps(legacy), encoding="utf-8")
        restarted = page(github.Cached(read, cache), now + 120)
        fresh = page(github.Cached(read), now + 120)
        for at in (now, now + github.DELAY, now + 120):
            expected = before if at < now + 1 + github.DELAY else after
            assert oracles.story_counts_at(restarted, at)["cook-1.1"] == expected
            assert oracles.story_counts_at(fresh, at)["cook-1.1"] == expected

        artifact = tmp_path / "replay.html"
        artifact.write_text(
            pipeline.render_page({"generated": "", "brigades": [fresh]}, {}),
            encoding="utf-8",
        )
        browser_page = chromium.new_page()
        try:
            browser_page.goto(artifact.as_uri())
            for at, count in ((now, before), (now + 120, after), (now, before)):
                expected = "1 Story" if count == 1 else "2 Stories"
                browser_page.evaluate("at => seek(at, false)", at)
                assert browser_page.locator(".f2m-stories").all_text_contents() == [
                    expected
                ]
        finally:
            browser_page.close()

        phase = 2  # A merged PR's body remains editable.
        gh.refresh()
        later = page(gh, now + 240)
        assert oracles.story_counts_at(later, now + 120)["cook-1.1"] == after
        assert oracles.story_counts_at(later, now + 240)["cook-1.1"] == 2
    finally:
        con.close()
        db.con.close()


@pytest.mark.parametrize(
    "message, temporary, missing",
    [
        (
            "GraphQL: Could not resolve to a Repository with the name 'missing'.",
            False,
            True,
        ),
        ("HTTP 401: Bad credentials", False, False),
        ("HTTP 502: Bad Gateway", True, False),
    ],
)
def test_optional_reference_lookup_preserves_genuine_read_errors(
    message: str, temporary: bool, missing: bool
) -> None:
    def read(args: list[str]) -> dict:
        assert args[:2] == ["repo", "view"]
        raise github.ReadError(message, temporary=temporary)

    gh = github.GitHub(read)
    ref = ("example-owner/missing", 1)
    if missing:
        assert gh.issue(*ref) is None
        assert github.Recorded(gh.dump()).stories_of([ref]) == []
    else:
        with pytest.raises(github.ReadError):
            gh.issue(*ref)
    # A repository used as the source of a PR is always a strict lookup.
    with pytest.raises(github.ReadError):
        gh.load_prs([ref])


def test_recorded_reassignment_moves_the_count_and_metadata() -> None:
    recording = Path(__file__).parent / "recordings" / "0ba0.json.gz"
    brigade = pipeline.recording_data(t3.load_recording(recording))["brigades"][0]
    before = oracles.story_counts_at(
        brigade, 1792367596.0
    )  # 2026-10-18 19:53:16 Montreal
    after = oracles.story_counts_at(brigade, 1792367598.0)
    assert (before["cook-2.1"], before["cook-3.1"]) == (3, 0)
    assert (after["cook-2.1"], after["cook-3.1"]) == (2, 1)
    final = oracles.story_counts_at(brigade, brigade["end"])
    assert (final["cook-2.1"], final["cook-3.1"]) == (2, 3)
    assert final == {
        slot: len(info["stories"]) for slot, info in brigade["cooks"].items()
    }


def test_existing_pr_keeps_revision_order_when_history_arrives_at_one_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in fake_env(tmp_path).items():
        monkeypatch.setenv(name, value)
    db = live_run(tmp_path)
    con = t3.connect(db.path, 5)
    try:
        snap, _ = t3.load(con, [HC])
        gh = github.Cached(github.gh_reader(10))
        gh.load_prs([(W, 21)])
        gh.prs[(W, 21)]["refHistory"] = [
            ["2026-01-01T00:01:00.000Z", [[W, 11]]],
            ["2026-01-01T00:01:01.000Z", [[W, 10], [W, 11]]],
        ]
        data, _ = pipeline.page_data(snap, gh, [HC], now=time.time())
        brigade = data["brigades"][0]
        assert oracles.story_counts_at(brigade, brigade["end"])["cook-1.1"] == 2
        assert len(brigade["cooks"]["cook-1.1"]["stories"]) == 2
    finally:
        con.close()
        db.con.close()

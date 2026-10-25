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
    "original, edited, before, after, paginated",
    [
        ("closed #10. Resolves #11.", "Closes #11.", 2, 1, False),
        ("closed #10. Resolves #11.", "Closes #11.", 2, 1, True),
        # A native link has no edit timestamp until a body revision names it.
        ("Closes #11.", "Closes #10. Closes #11.", 1, 2, False),
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
    paginated: bool,
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
        pr = repository.get("p21") or repository.get("pullRequest")
        if pr:
            pr["body"] = (original, edited, "Closes #10.")[phase]
            pr["mergedAt"] = pr["closedAt"] = (
                pipeline.t3_time(now + 2) if phase else None
            )
            pr["closingIssuesReferences"]["nodes"] = [
                {"number": n, "repository": {"nameWithOwner": W}}
                for n in ([10, 11], [11] if after == 1 else [10, 11], [10])[phase]
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
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
            if paginated and phase:
                edits = pr["userContentEdits"]
                if "after:" in " ".join(args):
                    edits["nodes"] = edits["nodes"][1:]
                else:
                    edits["nodes"] = edits["nodes"][:1]
                    edits["pageInfo"] = {"hasNextPage": True, "endCursor": "older"}
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

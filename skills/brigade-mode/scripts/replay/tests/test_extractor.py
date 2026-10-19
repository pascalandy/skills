"""The extractor on recorded runs and on the cases its rules name."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import board
import github
import pipeline
import pytest
import t3
from github import Recorded
from test_replay import COOK, HC, HEADS, fact, launches

HERE = Path(__file__).resolve().parent
RECORDINGS = {p.name.split(".")[0]: p for p in (HERE / "recordings").glob("*.json.gz")}


def recording(id4: str) -> dict:
    return t3.load_recording(RECORDINGS[id4])


def cook_frames(data: dict) -> list[tuple[float, str, str | None]]:
    return [
        (f[0], f[2], f[4]) for f in data["brigades"][0]["frames"] if f[1] == "cook-1.1"
    ]


def test_cook_idles_only_after_120_seconds_without_a_new_turn() -> None:
    events = [
        *launches(),
        fact(10, "cook", COOK, "run_start", detail={"run": "1"}),
        fact(20, "cook", COOK, "run_end", detail={"run": "1", "state": "completed"}),
    ]
    start = board.R.ts("2026-01-01T00:00:00Z")
    before = cook_frames(board.build(events, set(), {}, {}, HEADS, now=start + 100))
    after = cook_frames(board.build(events, set(), {}, {}, HEADS, now=start + 200))
    assert before[-1][1] == "active"  # 80 s after its turn: still on the job
    assert after[-1] == (start + 140, "wait", "idle")
    assert after[: len(before)] == before  # a later replay keeps what the page showed


def test_head_chef_shows_in_align_before_any_chef() -> None:
    events = [fact(0, "pascal", HC, "pascal_msg", detail={"intent": "reply"})]
    data = board.build(events, set(), {}, {}, HEADS)
    brigade = data["brigades"][0]
    assert brigade["batches"] == [] and brigade["cooks"] == {}
    assert [f[2] for f in brigade["frames"] if f[1] == "hc"] == ["active"]


def test_a_thread_naming_another_run_is_no_head_chef() -> None:
    snap = t3.Snapshot()
    snap.apply(
        [
            1,
            "2026-01-01T00:00:00.000Z",
            "thread",
            "import:x-7952",
            {"title": t3.parse_title("Head Chef 91c4 status reconciliation")},
        ]
    )
    data, _ = pipeline.page_data(snap, Recorded({}), ["import:x-7952"])
    assert data["brigades"] == []


def test_watch_toml_slots_register_every_batch_of_0ba0() -> None:
    rec = recording("0ba0")
    data = pipeline.recording_data(rec)
    assert [b["id"] for b in data["brigades"][0]["batches"]] == [
        f"batch-{n}" for n in range(1, 8)
    ]
    # registered before any Chef: the Head Chef aligns with its seven queued batches
    first = next(
        r[0]
        for r in rec["records"]
        if r[2] == "item" and r[4] and r[4].get("tool") == "launch"
    )
    early = pipeline.recording_data(rec, upto=first - 1)["brigades"][0]
    assert len(early["batches"]) == 7 and early["cooks"] == {}
    assert {f[2] for f in early["frames"] if f[1].startswith("batch-")} == {"todo"}


@pytest.mark.parametrize("id4", sorted(RECORDINGS))
def test_recorded_run_replays_into_a_page(id4: str) -> None:
    rec = recording(id4)
    data = pipeline.recording_data(rec)
    (brigade,) = data["brigades"]
    assert brigade["id"] == id4 and brigade["batches"]
    pipeline.render_page(data, {})


@pytest.mark.parametrize(
    "id4, final",
    [("66ab", "done"), ("91c4", "done")],
)
def test_finished_runs_end_where_their_head_chef_closed(id4: str, final: str) -> None:
    if id4 not in RECORDINGS:
        pytest.skip(f"no recording of {id4}")
    brigade = pipeline.recording_data(recording(id4))["brigades"][0]
    assert brigade["final"] == final


def test_replay_command_reads_a_recording(tmp_path: Path) -> None:
    out = tmp_path / "page.html"
    done = subprocess.run(
        [
            sys.executable,
            str(HERE.parent / "replay.py"),
            "--recording",
            str(RECORDINGS["66ab"]),
            "-o",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["changes"] == [["write", str(out)]]
    assert "Head Chef" in out.read_text(encoding="utf-8")


def test_a_merge_shows_85_seconds_after_github_had_it() -> None:
    gh = Recorded(recording("0ba0")["github"])
    ref, p = next((r, p) for r, p in sorted(gh.prs.items()) if p["merged"])
    shown = board.R.ts(p["merged"]) + github.DELAY
    before = gh.at(pipeline.t3_time(shown - 0.001)).pr(*ref)
    assert before and before["merged"] is None
    after = gh.at(pipeline.t3_time(shown)).pr(*ref)
    assert after and board.R.ts(after["merged"]) == shown


def test_no_frame_shows_before_its_fact() -> None:
    events = [*launches(), fact(4, "cook", COOK, "run_start", detail={"run": "1"})]
    events[-1]["time"] = "2026-01-01T00:00:04.949Z"
    frames = cook_frames(board.build(events, set(), {}, {}, HEADS))
    active = next(f[0] for f in frames if f[1] == "active")
    assert active == board.R.ts("2026-01-01T00:00:05Z")  # a tenth up, never down


def test_an_item_naming_two_prs_waits_on_pascal_until_both_are_done() -> None:
    events = [
        *launches(),
        fact(
            3,
            "head_chef",
            HC,
            "ask_pascal",
            detail={"items": ["item"], "irefs": [["#1", "o/r#2"]]},
        ),
        fact(5, "pascal", HC, "pascal_github", pr="o/r#1"),
        fact(7, "pascal", HC, "pascal_github", pr="o/r#2"),
    ]
    frames = board.build(events, set(), {}, {}, HEADS)["brigades"][0]["frames"]
    start = board.R.ts("2026-01-01T00:00:00Z")

    def hc(second: float) -> str:
        return [f[2] for f in frames if f[1] == "hc" and f[0] <= start + second][-1]

    assert [hc(4), hc(6), hc(8)] == ["you", "you", "active"]


@pytest.mark.parametrize(
    "text, src, dst, kind",
    [
        (
            "❓ Cook 1.1 abcd · look question. I'm still building on my defaults below.",
            "cook",
            "chef",
            "question_note",
        ),
        ("⚠️ Incident · Cook 4.1 abcd, om1", "cook", "chef", "incident"),
        (
            "Chef 4 abcd · ⚠️ incident on om1. The batch continues.",
            "chef",
            "head_chef",
            "incident",
        ),
        (
            "Chef 4 abcd · 🔀 progress: Stack A landed.",
            "chef",
            "head_chef",
            "status_note",
        ),
        (
            "Chef 4 abcd · ⏳ 0/2. Both Cooks are building.",
            "chef",
            "head_chef",
            "status_note",
        ),
        ("Chef 1: 📍 1/6 received for #197", "chef", "cook", "progress_note"),
        ("Chef 4 abcd · 🦄 a symbol no rule reads", "chef", "head_chef", "info"),
        # free text: an issue reference, a code span or a Cook's emoji header opens no notice
        ("Cook 1.1 abcd · #79 finding, no blocker", "cook", "chef", "info"),
        ("Chef 2 abcd → Cook 2.2: `origin/main` moved", "chef", "cook", "info"),
        ("🧑‍🍳 Cook 1.1 abcd started M09-T1", "cook", "chef", "info"),
    ],
)
def test_notices_outside_the_messages_table_have_a_kind(
    text: str, src: str, dst: str, kind: str
) -> None:
    sig = t3.signature(text)
    assert t3.classify(sig, src, dst) == kind
    assert (kind == "info" and "🦄" not in text) == ("lead" not in sig)

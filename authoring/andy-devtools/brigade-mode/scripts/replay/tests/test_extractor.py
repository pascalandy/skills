"""The extractor on recorded runs and on the cases its rules name."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import board
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

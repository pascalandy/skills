"""The oracles on every recorded run, and proof that they catch a replay that looks ahead."""

from __future__ import annotations

import json
import subprocess
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any

import board
import facts
import github
import oracles
import pytest
import t3

HERE = Path(__file__).resolve().parent
RECORDINGS = {p.name.split(".")[0]: p for p in (HERE / "recordings").glob("*.json.gz")}


@pytest.mark.parametrize("id4", sorted(RECORDINGS))
def test_recorded_run_meets_every_oracle(id4: str) -> None:
    report = oracles.report(t3.load_recording(RECORDINGS[id4]))
    assert [row for row in oracles.rows(report) if not row["pass"]] == []
    assert all(c["cause"] for c in report["titles"]["disagreements"])


@pytest.mark.parametrize("mutation", ["round to the nearest tenth", "keep the stamp"])
def test_prefix_oracle_catches_a_replay_that_looks_ahead(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    if mutation == "round to the nearest tenth":
        monkeypatch.setattr(board, "tenth", lambda t: round(t, 1))
    else:  # a fact shows at its own stamp, before its record arrived
        monkeypatch.setattr(t3, "later", lambda fact, arrived: fact or arrived)
    report = oracles.report(t3.load_recording(RECORDINGS["0ba0"]))
    assert report["prefix"]["status"] > 0


def test_prefix_oracle_catches_a_github_fact_the_service_learns_late(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(github, "DELAY", 0.0)  # merges show as GitHub stamps them
    report = oracles.report(t3.load_recording(RECORDINGS["0ba0"]))
    assert report["prefix"]["detail"] > 0
    assert not next(r for r in oracles.rows(report) if r["oracle"] == 1)["pass"]


def test_prefix_oracle_catches_a_change_only_the_final_replay_shows() -> None:
    run = oracles.Run(t3.load_recording(RECORDINGS["0ba0"]))
    frames = run.final["frames"]
    (_, a), (_, b) = max(
        (
            pair
            for pair in pairwise(oracles.sequences(run.rec))
            if "hc" in oracles.state_at(frames, pair[0][1])
        ),
        key=lambda pair: pair[1][1] - pair[0][1],
    )
    state = oracles.state_at(frames, a)["hc"]
    mid = (a + b) / 2  # red for a tenth of a second, inside one page's window
    blip = [[mid, "hc", "you", *state[1:]], [mid + 0.1, "hc", *state]]
    run.final["frames"] = sorted(frames + blip, key=lambda f: f[0])
    assert oracles.prefix_consistency(run)["status"] > 0


def test_registry_oracle_catches_an_extractor_that_drops_merges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ev = facts.Brigade.ev

    def no_merge(self: facts.Brigade, *args: Any, **kwargs: Any) -> None:
        if args[3] != "pr_merge":  # time, role, thread, kind
            ev(self, *args, **kwargs)

    monkeypatch.setattr(facts.Brigade, "ev", no_merge)
    run = oracles.Run(t3.load_recording(RECORDINGS["0ba0"]))
    assert oracles.registries_and_merges(run)["misses"]


def test_oracles_command_writes_the_table(tmp_path: Path) -> None:
    out = tmp_path / "oracles.md"
    done = subprocess.run(
        [
            sys.executable,
            str(HERE.parent / "oracles.py"),
            str(RECORDINGS["0ba0"]),
            "-o",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    answer = json.loads(done.stdout)
    assert answer["changes"] == [["write", str(out)]]
    assert {row["oracle"] for row in answer["rows"]} == {1, 2, 3, 4, 5, 6}
    assert "| 0ba0 | 1 prefix consistency |" in out.read_text(encoding="utf-8")

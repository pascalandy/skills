"""Exercise the snapshot that the dashboard recipes build and check."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from headchefs import snapshot

if TYPE_CHECKING:
    from playwright.sync_api import Browser

CLI = Path(__file__).resolve().parents[1] / "headchefs_dashboard.py"


def test_cook_keeps_head_chef_active_without_entering_their_time_total(
    tmp_path: Path,
) -> None:
    database = tmp_path / "statev2.sqlite"
    artifact = tmp_path / "dashboard.html"
    preview = tmp_path / "dashboard.preview.html"
    launch = datetime.now(UTC) - timedelta(hours=3)
    with closing(sqlite3.connect(database)) as db:
        db.executescript("""
            create table orchestration_v2_projection_threads(
                thread_id, title, created_at, archived_at, deleted_at, payload_json);
            create table orchestration_v2_projection_runs(
                thread_id, ordinal, status, completed_at, payload_json);
            create table orchestration_v2_projection_turn_items(
                thread_id, type, status, payload_json);
            create table orchestration_v2_projection_subagents(thread_id, child_thread_id);
            insert into orchestration_v2_projection_subagents values ('root-abcd', 'cook');
            """)
        db.executemany(
            "insert into orchestration_v2_projection_threads values(?, ?, ?, ?, null, ?)",
            [
                (
                    "root-abcd",
                    "Head Chef abcd",
                    launch.isoformat(),
                    None,
                    json.dumps(
                        {"settledAt": (launch + timedelta(hours=2)).isoformat()}
                    ),
                ),
                ("cook", "Cook 1.1", launch.isoformat(), None, "{}"),
                (
                    "another-root-abcd",
                    "Head Chef abcd · Archive",
                    (launch - timedelta(minutes=10)).isoformat(),
                    (launch + timedelta(hours=1)).isoformat(),
                    "{}",
                ),
                (
                    "waiting-bcde",
                    "Head Chef bcde 1/2 ⏳ Open",
                    (launch - timedelta(days=95)).isoformat(),
                    None,
                    "{}",
                ),
                ("queued-cdef", "Head Chef cdef", launch.isoformat(), None, "{}"),
            ],
        )
        db.executemany(
            "insert into orchestration_v2_projection_runs values(?, ?, ?, ?, ?)",
            [
                (
                    thread,
                    ordinal,
                    "completed" if end is not None else "running",
                    (launch + timedelta(minutes=end)).isoformat()
                    if end is not None
                    else None,
                    json.dumps(
                        {"startedAt": (launch + timedelta(minutes=start)).isoformat()}
                    ),
                )
                for thread, ordinal, start, end in (
                    ("root-abcd", 1, 60, 120),
                    ("root-abcd", 2, 90, 150),
                    ("cook", 1, 105, None),
                    ("another-root-abcd", 1, 20, 30),
                    ("waiting-bcde", 1, -95 * 1440 + 10, -95 * 1440 + 30),
                )
            ],
        )
        db.commit()

    def command(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args, "--artifact", str(artifact)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    built = command("build", "--db", str(database))
    assert built.returncode == 0, built.stderr
    summary = json.loads(built.stdout)
    assert summary["active"] == ["abcd", "cdef", "bcde"]
    assert summary["inactive"] == 1
    assert not artifact.exists()
    page = preview.read_text()
    embedded = re.search(r"^const snapshot=(.*);$", page, re.MULTILINE)
    assert embedded is not None
    data = json.loads(embedded[1])
    chart = data["chefs"][0]["chart"]
    assert chart["active"] == 5_400_000
    assert chart["idle"] == chart["cutoff"] - chart["start"] - 5_400_000
    waiting = next(chef for chef in data["chefs"] if chef["id"] == "bcde")
    assert waiting["lastActivity"] < waiting["chart"]["cutoff"] == data["reference"]
    assert waiting["chart"]["active"] == 1_200_000
    queued = next(chef for chef in data["chefs"] if chef["id"] == "cdef")
    assert queued["chart"]["active"] == 0
    assert command("check").returncode == 0

    preview.write_text(page.replace('"active":5400000', '"active":5400001', 1))
    rejected = command("check")
    assert rejected.returncode == 1
    assert not rejected.stdout
    assert not json.loads(rejected.stderr.splitlines()[-1])["ok"]


def test_selected_bar_shows_a_summary_without_listing_parallel_runs(
    tmp_path: Path, chromium: Browser
) -> None:
    from playwright.sync_api import expect

    hour = 3_600_000
    rows: list[snapshot.Row] = [{"style": lane, "items": []} for lane in snapshot.LANES]
    rows[0]["items"].append(
        {"start": 0, "end": hour, "style": "head", "label": "Session de préparation"}
    )
    rows[2]["items"].append(
        {"start": 0, "end": hour, "style": "plan", "label": "Travail en parallèle"}
    )
    chef: snapshot.Chef = {
        "id": "abcd",
        "title": "Head Chef abcd",
        "state": "Actif",
        "isActive": True,
        "lastActivity": hour,
        "chart": {"start": 0, "cutoff": hour, "active": hour, "idle": 0, "rows": rows},
    }
    artifact = tmp_path / "dashboard.html"
    artifact.write_text(
        snapshot.render({"reference": hour, "chefs": [chef]}), encoding="utf-8"
    )

    page = chromium.new_page()
    try:
        page.goto(artifact.as_uri())
        page.get_by_role("group", name="Runs du Head Chef", exact=True).locator(
            ".mark"
        ).hover()
        expect(page.get_by_role("status")).to_contain_text("Session de préparation")
        expect(page.get_by_role("status")).to_contain_text("1 h")
        expect(page.get_by_role("table")).to_have_count(0)
    finally:
        page.close()

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
from zoneinfo import ZoneInfo

import pytest
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


def _local(clock: str) -> datetime:
    hours, minutes = map(int, clock.split(":"))
    return datetime(2026, 11, 24, hours, minutes, tzinfo=ZoneInfo("America/Montreal"))


def _ms(clock: str) -> int:
    return int(_local(clock).timestamp() * 1000)


def _brigade(database: Path) -> sqlite3.Connection:
    db = sqlite3.connect(database)
    db.executescript("""
        create table orchestration_v2_projection_threads(
            thread_id, title, created_at, archived_at, deleted_at, payload_json);
        create table orchestration_v2_projection_runs(
            thread_id, ordinal, status, completed_at, payload_json);
        create table orchestration_v2_projection_turn_items(
            thread_id, type, status, payload_json);
        create table orchestration_v2_projection_subagents(thread_id, child_thread_id);
        insert into orchestration_v2_projection_subagents values
            ('root-abcd', 'cook-a'), ('root-abcd', 'cook-b'), ('root-abcd', 'dog');
        """)
    db.executemany(
        "insert into orchestration_v2_projection_threads values(?, ?, ?, null, null, ?)",
        [
            ("root-abcd", "Head Chef abcd", _local("10:10").isoformat(), "{}"),
            ("cook-a", "Cook 1.1", _local("10:10").isoformat(), "{}"),
            ("cook-b", "Cook 1.2", _local("10:10").isoformat(), "{}"),
            ("dog", "Watchdog abcd", _local("10:10").isoformat(), "{}"),
            (
                "done-bcde",
                "Head Chef bcde ⛳",
                _local("08:00").isoformat(),
                json.dumps({"settledAt": _local("09:00").isoformat()}),
            ),
        ],
    )
    db.executemany(
        "insert into orchestration_v2_projection_runs values(?, ?, ?, ?, ?)",
        [
            (
                thread,
                ordinal,
                "running" if end is None else "completed",
                None if end is None else _local(end).isoformat(),
                json.dumps({"startedAt": _local(start).isoformat()}),
            )
            for thread, ordinal, start, end in (
                ("root-abcd", 1, "10:10", "10:45"),
                ("cook-a", 1, "10:30", "10:50"),
                ("cook-a", 2, "10:40", "11:10"),
                ("cook-a", 3, "11:10", "11:15"),
                ("cook-b", 1, "12:05", None),
                ("dog", 1, "10:20", "12:10"),
                ("done-bcde", 1, "08:00", "08:40"),
            )
        ],
    )
    db.commit()
    return db


def test_half_hour_readout_counts_each_agent_once_and_skips_waits(
    tmp_path: Path, chromium: Browser
) -> None:
    captured = _local("12:17")
    with closing(_brigade(tmp_path / "statev2.sqlite")) as db:
        first = snapshot.capture(db, captured=captured)
        # A page built before agent counts existed still loads, and its wait carries forward.
        legacy = json.loads(json.dumps(first))
        for chef in legacy["chefs"]:
            del chef["chart"]["concurrency"]
            del chef["chart"]["workers"]
        legacy["chefs"][0]["chart"]["rows"][1]["items"] = [
            {
                "start": _ms("11:20"),
                "end": _ms("11:50"),
                "style": "wait",
                "label": "Revue",
            }
        ]
        legacy_page = snapshot.render(legacy)
        current = snapshot.capture(
            db, snapshot.read_snapshot(legacy_page), captured=captured
        )

    chef = current["chefs"][0]
    assert chef["chart"]["rows"][1]["items"][0]["start"] == _ms("11:20")
    assert chef["chart"].get("concurrency") == [
        [_ms("10:10"), 1],
        [_ms("10:30"), 2],
        [_ms("10:45"), 1],
        [_ms("11:15"), 0],
        [_ms("12:05"), 1],
    ]
    forged = json.loads(json.dumps(current))
    forged["chefs"][0]["chart"]["concurrency"][0][1] = 3
    with pytest.raises(snapshot.SnapshotError, match="counts differ from the runs"):
        snapshot.validate(forged)

    legacy_view = chromium.new_page()
    legacy_view.set_content(legacy_page)
    assert legacy_view.locator(".activity:visible").count() == 0
    assert legacy_view.locator(".active-list [data-cooks]").inner_text() == "—"
    page = chromium.new_page(has_touch=True, viewport={"width": 1100, "height": 900})
    page.set_content(snapshot.render(current))
    readout = page.locator(".active-list .activity output")
    slider = page.locator(".active-list .activity input")
    assert page.locator(".latest-archive .activity input").is_visible()
    assert readout.inner_text().split("\n") == [
        "0,7 agent actif",
        "24 nov. 2026, 12h00–12h17",
    ]

    slider.focus()
    expected = {
        "ArrowLeft": "0 agent actif",
        "Home": "1 agent actif",
        "ArrowRight": "1,5 agent actif",
        "End": "0,7 agent actif",
    }
    for key, text in expected.items():
        page.keyboard.press(key)
        assert readout.locator("strong").inner_text() == text, key
    page.keyboard.press("ArrowLeft")
    assert "0 agent actif en moyenne" in (slider.get_attribute("aria-valuetext") or "")

    cell = page.locator(".active-list .activity").bounding_box()
    assert cell is not None

    def x(clock: str) -> float:
        span = _ms("12:17") - _ms("10:10")
        return cell["x"] + cell["width"] * (_ms(clock) - _ms("10:10")) / span

    page.mouse.move(x("11:05"), cell["y"] + 20)
    assert readout.inner_text().split("\n") == [
        "0,5 agent actif",
        "24 nov. 2026, 11h00–11h30",
    ]
    page.touchscreen.tap(x("11:40"), cell["y"] + 20)
    assert readout.inner_text().split("\n") == [
        "0 agent actif",
        "24 nov. 2026, 11h30–12h00",
    ]


def test_role_totals_count_each_cook_and_qa_thread_once_and_skip_other_roles(
    tmp_path: Path, chromium: Browser
) -> None:
    with closing(_brigade(tmp_path / "statev2.sqlite")) as db:
        db.execute(
            "update orchestration_v2_projection_threads set title=? where thread_id='cook-a'",
            ("🧑‍🍳 Cook 1.1 abcd 🍳 Watchdog handoff",),
        )
        db.executemany(
            "insert into orchestration_v2_projection_subagents values(?, ?)",
            [
                ("root-abcd", "qa-1"),
                ("qa-1", "qa-worker"),
                ("root-abcd", "qa-recheck"),
                ("qa-1", "qa-review"),
                ("qa-1", "qa-wait"),
                ("qa-1", "qa-tool"),
                ("root-abcd", "planner"),
                ("root-abcd", "chef"),
                ("root-abcd", "loop"),
                ("root-abcd", "luna"),
                ("cook-a", "side"),
                ("cook-a", "cook-prefixed-helper"),
                ("cook-a", "cook-prefixed-task"),
            ],
        )
        db.executemany(
            "insert into orchestration_v2_projection_threads values(?, ?, ?, null, null, '{}')",
            [
                (thread, title, _local("10:10").isoformat())
                for thread, title in (
                    ("qa-1", "🧪 QA 1b · Head Chef abcd"),
                    ("qa-worker", "QA1 worker · Watchdog handoff"),
                    ("qa-recheck", "🧪 QA recheck"),
                    ("qa-review", "QA1 review"),
                    ("qa-wait", "QA Wait"),
                    ("qa-tool", "QA 1 tool-call"),
                    ("planner", "📐 Planner · W1"),
                    ("chef", "🚥 Chef 1 abcd [0/1] 🍳 lot"),
                    ("loop", "👀 loop-1 · Cook 1.1 abcd"),
                    ("luna", "🌙 Luna"),
                    ("side", "🔧 verify · Cook 1.1 abcd"),
                    ("cook-prefixed-helper", "🔧 Cook 1.1 · verify"),
                    ("cook-prefixed-task", "Cook 1.1 code proof"),
                )
            ],
        )
        db.executemany(
            "insert into orchestration_v2_projection_runs values(?, ?, 'completed', ?, ?)",
            [
                (
                    thread,
                    ordinal,
                    _local(end).isoformat(),
                    json.dumps({"startedAt": _local(start).isoformat()}),
                )
                for thread, ordinal, start, end in (
                    ("qa-1", 1, "11:00", "11:30"),
                    ("qa-1", 2, "11:20", "11:40"),
                    ("qa-worker", 1, "11:25", "11:35"),
                    ("qa-recheck", 1, "11:40", "11:45"),
                    ("qa-review", 1, "11:40", "11:55"),
                    ("qa-wait", 1, "11:45", "12:00"),
                    ("qa-tool", 1, "11:45", "12:00"),
                    ("planner", 1, "10:15", "10:25"),
                    ("chef", 1, "10:12", "12:00"),
                    ("loop", 1, "11:00", "11:20"),
                    ("luna", 1, "10:30", "11:00"),
                    ("side", 1, "10:50", "11:00"),
                    ("cook-prefixed-helper", 1, "11:15", "11:45"),
                    ("cook-prefixed-task", 1, "11:15", "11:45"),
                )
            ],
        )
        db.commit()
        current = snapshot.capture(db, captured=_local("12:17"))

    chart = current["chefs"][0]["chart"]
    minute = 60_000
    assert chart["active"] == 35 * minute
    # Cook 1.1 overlaps itself from 10:30 to 11:15 and Cook 1.2 runs 12:05 to capture.
    # QA adds 40 minutes for QA 1, 10 for its worker and 5 for the recheck.
    assert chart.get("workers") == {"cooks": 57 * minute, "qa": 55 * minute}
    qa_runs = next(row["items"] for row in chart["rows"] if row["style"] == "qa")
    assert qa_runs[0]["label"] == "QA 1"
    forged = json.loads(json.dumps(current))
    forged["chefs"][0]["chart"]["workers"]["qa"] = -1
    with pytest.raises(snapshot.SnapshotError):
        snapshot.validate(forged)

    page = chromium.new_page()
    page.set_content(snapshot.render(current))
    totals = page.locator(".active-list .chef-totals")
    assert totals.locator("dt").all_inner_texts() == ["HF", "Cooks", "QA"]
    assert totals.locator("dd").all_inner_texts() == [
        "0,58 h actives · 1,53 h inactives",
        "0,95 h actives",
        "0,92 h actives",
    ]


def test_worker_totals_do_not_extend_the_archived_head_chef_timeline(
    tmp_path: Path,
) -> None:
    with closing(_brigade(tmp_path / "statev2.sqlite")) as db:
        db.execute(
            "update orchestration_v2_projection_threads set title='Head Chef abcd ⛳' where thread_id='root-abcd'"
        )
        db.execute(
            "update orchestration_v2_projection_threads set title='Cook 1.1 Watchdog handoff' where thread_id='cook-a'"
        )
        db.execute(
            "update orchestration_v2_projection_runs set status='cancelled' where thread_id='cook-b'"
        )
        db.commit()
        current = snapshot.capture(db, captured=_local("12:17"))

    chef = next(chef for chef in current["chefs"] if chef["id"] == "abcd")
    chart = chef["chart"]
    assert chef.get("isActive") is False
    assert chart["cutoff"] == _ms("10:45")
    assert chart["idle"] == 0
    assert chart.get("workers") == {"cooks": 45 * 60_000, "qa": 0}


def test_touch_steps_reach_each_window_of_a_dense_timeline(chromium: Browser) -> None:
    start = int(datetime(2026, 10, 22, 0, 15, tzinfo=UTC).timestamp() * 1000)
    cutoff = int(datetime(2026, 11, 1, 7, 30, tzinfo=UTC).timestamp() * 1000)
    run = cutoff - 90 * 60_000
    rows: list[snapshot.Row] = [{"style": lane, "items": []} for lane in snapshot.LANES]
    rows[0]["items"].append(
        {"start": run, "end": run + 60_000, "style": "head", "label": "Travail bref"}
    )
    chef: snapshot.Chef = {
        "id": "abcd",
        "title": "Head Chef abcd",
        "state": "Actif",
        "isActive": True,
        "lastActivity": run + 60_000,
        "chart": {
            "start": start,
            "cutoff": cutoff,
            "active": 60_000,
            "idle": cutoff - start - 60_000,
            "rows": rows,
            "concurrency": [[start, 0], [run, 1], [run + 60_000, 0]],
        },
    }
    page = chromium.new_page(has_touch=True, viewport={"width": 390, "height": 850})
    try:
        page.set_content(snapshot.render({"reference": cutoff, "chefs": [chef]}))
        previous = page.get_by_role("button", name="Tranche précédente")
        following = page.get_by_role("button", name="Tranche suivante")
        slider = page.get_by_role("slider")
        readout = page.locator(".activity output")
        assert following.is_disabled(timeout=1500)
        previous.scroll_into_view_if_needed()
        box = previous.bounding_box()
        assert box is not None
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        page.touchscreen.tap(x, y)
        page.touchscreen.tap(x, y)
        assert previous.bounding_box() == box
        second = "1 nov. 2026, 01h00 (UTC−05:00)–01h30 (UTC−05:00)"
        assert readout.inner_text().split("\n") == ["<0,1 agent actif", second]
        assert second in (slider.get_attribute("aria-valuetext") or "")
        announcement = page.locator(".activity [role='status']")
        assert (
            announcement.text_content()
            == f"moins de 0,1 agent actif en moyenne, {second}"
        )
        page.touchscreen.tap(x, y)
        crossing = "01h30 (UTC−04:00)–01h00 (UTC−05:00)"
        assert crossing in readout.inner_text()
        page.touchscreen.tap(x, y)
        assert readout.inner_text().split("\n") == [
            "0 agent actif",
            "1 nov. 2026, 01h00 (UTC−04:00)–01h30 (UTC−04:00)",
        ]
        following.tap()
        assert crossing in readout.inner_text()
    finally:
        page.close()


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

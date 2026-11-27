"""Capture the Head Chefs Gantt from T3 and render the standalone dashboard."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Literal, NotRequired, TypedDict, cast
from zoneinfo import ZoneInfo

MONTREAL = ZoneInfo("America/Montreal")
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
MILLISECOND = timedelta(milliseconds=1)
HISTORY_DAYS = 90

Lane = Literal["head", "wait", "production", "parallel", "qa", "review"]
LANES: tuple[Lane, ...] = ("head", "wait", "production", "parallel", "qa", "review")
Worker = Literal["cooks", "qa"]
COOK_STYLES = {
    "1": "cook1-1",
    "2": "cook2-1",
    "3": "cook3-1",
    "4": "cook4-1",
    "5": "cook5-1",
}
HEAD_CHEF = re.compile(r"^Head Chef ([0-9a-z]{4})\b", re.IGNORECASE)
SNAPSHOT_LINE = re.compile(r"^const snapshot=(.*);$", re.MULTILINE)
TEMPLATE = Path(__file__).with_name("template.html")
MARKER = 'const snapshot={"reference":0,"chefs":[]};'


class Interval(TypedDict):
    start: int
    end: int
    style: str
    label: str
    running: NotRequired[bool]
    short: NotRequired[str]


class Row(TypedDict):
    style: Lane
    items: list[Interval]


class Workers(TypedDict):
    """Active milliseconds per role since launch; each thread's runs count once."""

    cooks: int
    qa: int


class Chart(TypedDict):
    start: int
    cutoff: int
    active: int
    idle: int
    rows: list[Row]
    concurrency: NotRequired[list[list[int]]]
    workers: NotRequired[Workers]


class Chef(TypedDict):
    id: str
    title: str
    state: str
    isActive: NotRequired[bool]
    lastActivity: int
    chart: Chart


class Snapshot(TypedDict):
    reference: int
    chefs: list[Chef]


Role = tuple[Lane, str, str, Worker | None]
HEAD_ROLE: Role = ("head", "head", "Head Chef", None)


class SnapshotError(ValueError):
    """The capture or the embedded dashboard data cannot be used."""


def _milliseconds(moment: datetime) -> int:
    return (moment - EPOCH) // MILLISECOND


def _timestamp(value: str) -> int:
    try:
        return _milliseconds(datetime.fromisoformat(value))
    except (TypeError, ValueError) as error:
        raise SnapshotError("T3 contains an invalid timestamp") from error


def _launched_threads(db: sqlite3.Connection, parent: str) -> Iterator[str]:
    for (output,) in db.execute(
        """
        select json_extract(payload_json, '$.output')
        from orchestration_v2_projection_turn_items
        where thread_id=? and type='dynamic_tool' and status='completed'
          and json_extract(payload_json, '$.toolName') like '%__t3_thread_launch'
        """,
        (parent,),
    ):
        result = json.loads(output or "{}")
        if not isinstance(result, dict):
            continue
        child = result.get("structuredContent")
        if not child:
            try:
                child = json.loads(result.get("content") or "null")
            except (TypeError, ValueError):
                continue
        if isinstance(child, dict) and isinstance(child.get("threadId"), str):
            yield child["threadId"]


def _relatives(
    db: sqlite3.Connection,
    root: str,
    known_threads: set[str],
    delegated: dict[str, set[str]],
) -> set[str]:
    found, queue = set(), [root]
    while queue:
        thread = queue.pop()
        if thread in found or thread not in known_threads:
            continue
        found.add(thread)
        queue.extend(delegated.get(thread, ()))
        queue.extend(_launched_threads(db, thread))
    return found


def _role(title: str) -> Role | None:
    if re.search(r"Watchdog|Queuer", title, re.IGNORECASE):
        return None

    cook = re.match(r"^[^\w]*Cook (\d+)\.(\d+)", title)
    if cook:
        batch, number = cook.groups()
        paint = COOK_STYLES.get(batch, ("cook2-1", "cook3-1")[int(number) % 2])
        worker = None if title[cook.end() :].lstrip().startswith("·") else "cooks"
        return "production", paint, f"Cook {batch}.{number}", worker
    if re.match(r"^[^\w]*Planner\b", title):
        return "production", "plan", "Planner", None
    qa = re.match(r"^[^\w]*QA(?:\s+(\d+))?", title)
    if qa:
        return "qa", "qa", f"QA {qa[1]}" if qa[1] else "QA", "qa"
    chef = re.match(r"^[^\w]*Chef (\d+)", title)
    if chef:
        return "production", "cook4-1", f"Chef {chef[1]}", None
    if re.search(r"loop|revue|review|design", title, re.IGNORECASE):
        return "review", "review", title, None
    return "review", "review", "Sous-agent", None


def _work_intervals(
    db: sqlite3.Connection, thread: str, reference: int, kickoff: int, role: Role
) -> Iterator[tuple[Lane, Interval]]:
    lane, style, label, _ = role
    for ordinal, status, started, completed in db.execute(
        """
        select ordinal, status, json_extract(payload_json, '$.startedAt'), completed_at
        from orchestration_v2_projection_runs
        where thread_id=? order by ordinal
        """,
        (thread,),
    ):
        if not started:
            continue
        if completed:
            completed_at = _timestamp(completed)
            running = completed_at > reference
            end = min(completed_at, reference)
        elif status in ("running", "waiting"):
            running = True
            end = reference
        else:
            continue
        start = max(_timestamp(started), kickoff)
        if end <= start:
            continue
        item: Interval = {
            "start": start,
            "end": end,
            "running": running,
            "style": style,
            "label": f"Run {ordinal} du Head Chef" if lane == "head" else label,
        }
        if lane in ("production", "qa"):
            item["short"] = label
        yield lane, item


def _interval_order(interval: Interval) -> tuple[int, int, str]:
    return interval["start"], interval["end"], interval["label"]


def _covered(intervals: list[Interval]) -> int:
    total, end = 0, 0
    for interval in intervals:
        if interval["end"] > end:
            total += interval["end"] - max(end, interval["start"])
            end = interval["end"]
    return total


def _merge(spans: list[tuple[int, int]]) -> list[list[int]]:
    """Join one thread's overlapping or touching runs into disjoint spans."""
    merged: list[list[int]] = []
    for begin, end in sorted(spans):
        if merged and begin <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([begin, end])
    return merged


def _concurrency(
    threads: list[list[tuple[int, int]]], start: int, cutoff: int
) -> list[list[int]]:
    """Return `[time, agents]` pairs where the count of busy threads changes.

    Each thread counts once while any of its runs is open, so overlapping or
    touching runs of one thread never count twice.
    """
    changes: defaultdict[int, int] = defaultdict(int)
    for spans in threads:
        for begin, end in _merge(spans):
            changes[begin] += 1
            changes[end] -= 1
    points, agents = [[start, 0]], 0
    for moment in sorted(changes):
        agents += changes[moment]
        if moment >= cutoff:
            break
        if agents == points[-1][1]:
            continue
        if moment == points[-1][0]:
            points[-1][1] = agents
        else:
            points.append([moment, agents])
    return points


def _distribute_production(rows: dict[Lane, list[Interval]], kickoff: int) -> None:
    end_of_main = kickoff
    production = rows["production"]
    rows["production"] = []
    for item in production:
        if item["start"] < end_of_main:
            rows["parallel"].append(item)
        else:
            rows["production"].append(item)
            end_of_main = item["end"]


def _capture(
    db: sqlite3.Connection, moment: datetime, previous: Snapshot | None
) -> Snapshot:
    reference = _milliseconds(moment)
    history_start = moment.astimezone(MONTREAL).date() - timedelta(
        days=HISTORY_DAYS - 1
    )
    oldest = _milliseconds(datetime.combine(history_start, time.min, MONTREAL))
    threads: dict[str, tuple[str, str, str | None, str | None]] = {
        thread: (title, created, archived, settled)
        for thread, title, created, archived, settled in db.execute(
            """
            select thread_id, title, created_at, archived_at,
                   json_extract(payload_json, '$.settledAt')
            from orchestration_v2_projection_threads where deleted_at is null
            """
        )
    }
    delegated: dict[str, set[str]] = defaultdict(set)
    for parent, child in db.execute(
        """
        select json_extract(payload_json, '$.lineage.parentThreadId'), thread_id
        from orchestration_v2_projection_threads
        where deleted_at is null
          and json_extract(payload_json, '$.lineage.relationshipToParent')='subagent'
        union
        select thread_id, child_thread_id from orchestration_v2_projection_subagents
        where child_thread_id is not null
        """
    ):
        if parent:
            delegated[parent].add(child)

    previous_chefs = previous["chefs"] if previous else []
    annotations = {
        (chef["id"].lower(), chef["chart"]["start"]): (chef["title"], row["items"])
        for chef in previous_chefs
        for row in chef["chart"]["rows"]
        if row["style"] == "wait" and row["items"]
    }
    known_threads = set(threads)
    chefs: list[Chef] = []
    for root, (title, created, archived, settled) in threads.items():
        heading = HEAD_CHEF.match(title)
        if not heading or not root.lower().endswith(short_id := heading[1].lower()):
            continue

        kickoff = _timestamp(created)
        if kickoff >= reference:
            continue
        rows: dict[Lane, list[Interval]] = {lane: [] for lane in LANES}
        spans_by_thread: list[list[tuple[int, int]]] = []
        workers: Workers = {"cooks": 0, "qa": 0}
        for thread in sorted(_relatives(db, root, known_threads, delegated)):
            role = HEAD_ROLE if thread == root else _role(threads[thread][0])
            if role is None:
                continue
            spans: list[tuple[int, int]] = []
            spans_by_thread.append(spans)
            for lane, item in _work_intervals(db, thread, reference, kickoff, role):
                rows[lane].append(item)
                spans.append((item["start"], item["end"]))
            if worker := role[3]:
                workers[worker] += sum(end - begin for begin, end in _merge(spans))
        state = "Arrêté" if "⏹" in title else "Terminé" if "⛳" in title else "En pause"
        running = any(item.get("running") for items in rows.values() for item in items)
        is_open = not (archived or settled) and state == "En pause"
        is_active = running or is_open
        if not is_active and not rows["head"]:
            continue
        manual = annotations.get((short_id, kickoff))
        if manual:
            title, waits = manual
            rows["wait"] = [
                item
                for item in waits
                if kickoff <= item["start"] < item["end"] <= reference
            ]

        last = max(
            (item["end"] for items in rows.values() for item in items), default=kickoff
        )
        if not is_active and last < oldest:
            continue
        for items in rows.values():
            items.sort(key=_interval_order)
        _distribute_production(rows, kickoff)
        active = _covered(rows["head"])
        cutoff = reference if is_active else last

        chefs.append(
            {
                "id": short_id,
                "title": title,
                "state": state,
                "isActive": is_active,
                "lastActivity": last,
                "chart": {
                    "start": kickoff,
                    "cutoff": cutoff,
                    "active": active,
                    "idle": cutoff - kickoff - active,
                    "rows": [{"style": lane, "items": rows[lane]} for lane in LANES],
                    "concurrency": _concurrency(spans_by_thread, kickoff, cutoff),
                    "workers": workers,
                },
            }
        )
    chefs.sort(key=lambda chef: (-chef["lastActivity"], chef["id"]))
    return {"reference": reference, "chefs": chefs}


def capture(
    db: sqlite3.Connection,
    previous: Snapshot | None = None,
    *,
    captured: datetime | None = None,
) -> Snapshot:
    """Read one consistent SQLite view and keep manual waits from the previous page."""
    db.execute("begin")
    try:
        snapshot = _capture(db, captured or datetime.now(UTC), previous)
    finally:
        db.rollback()
    validate(snapshot)
    return snapshot


def _running(chef: Chef) -> bool:
    return any(
        item.get("running") for row in chef["chart"]["rows"] for item in row["items"]
    )


def _is_active(chef: Chef) -> bool:
    if "isActive" in chef:
        return chef["isActive"]
    return _running(chef)


def _validate_chart(chef: Chef, reference: int) -> None:
    chart = chef["chart"]
    start, cutoff = chart["start"], chart["cutoff"]
    if not all(
        type(value) is int for value in (start, cutoff, chart["active"], chart["idle"])
    ):
        raise SnapshotError("chart bounds and totals must be integer milliseconds")
    if not start < cutoff <= reference:
        raise SnapshotError("chart bounds exceed the snapshot")
    if "isActive" in chef and type(chef["isActive"]) is not bool:
        raise SnapshotError("the Head Chef activity flag must be boolean")
    if tuple(row["style"] for row in chart["rows"]) != LANES:
        raise SnapshotError("chart lanes are missing or out of order")
    head_runs = chart["rows"][0]["items"]
    last = start
    for row in chart["rows"]:
        items = row["items"]
        if items != sorted(items, key=_interval_order):
            raise SnapshotError("chart intervals are out of order")
        for item in items:
            if type(item["start"]) is not int or type(item["end"]) is not int:
                raise SnapshotError("interval bounds must be integer milliseconds")
            if not start <= item["start"] < item["end"] <= cutoff:
                raise SnapshotError("interval bounds exceed the chart")
            if not isinstance(item["label"], str) or not isinstance(item["style"], str):
                raise SnapshotError("interval label and style must be strings")
            if "short" in item and not isinstance(item["short"], str):
                raise SnapshotError("interval short name must be a string")
            if "running" in item and type(item["running"]) is not bool:
                raise SnapshotError("interval running flag must be boolean")
            if item.get("running") and item["end"] != reference:
                raise SnapshotError("active interval does not reach the snapshot time")
            last = max(last, item["end"])
    is_active = _is_active(chef)
    if not is_active and (_running(chef) or not head_runs):
        raise SnapshotError("inactive chart must have completed Head Chef activity")
    if last != chef["lastActivity"] or cutoff != (reference if is_active else last):
        raise SnapshotError("chart end differs from the activity window")
    active = _covered(head_runs)
    if chart["active"] != active or chart["idle"] != cutoff - start - active:
        raise SnapshotError("active and idle totals do not match the Head Chef's runs")
    if "concurrency" in chart:
        _validate_concurrency(chart, chart["concurrency"])
    if "workers" in chart:
        workers = chart["workers"]
        if not isinstance(workers, dict) or set(workers) != {"cooks", "qa"}:
            raise SnapshotError("role totals must name the Cooks and QA")
        if any(type(total) is not int or total < 0 for total in workers.values()):
            raise SnapshotError("role totals must be non-negative integer milliseconds")


def _validate_concurrency(chart: Chart, points: list[list[int]]) -> None:
    """Check the agent counts against the runs drawn in the chart.

    A count is positive exactly where some run is drawn, outside the manual
    waits, and never exceeds the number of runs drawn at that moment.
    """
    if not isinstance(points, list) or not points:
        raise SnapshotError("agent counts must be a non-empty list")
    previous: list[int] | None = None
    for point in points:
        if not (
            isinstance(point, list)
            and len(point) == 2
            and all(type(value) is int for value in point)
        ):
            raise SnapshotError("agent counts must be [time, agents] integer pairs")
        if point[1] < 0 or not point[0] < chart["cutoff"]:
            raise SnapshotError("agent counts exceed the chart")
        if previous and (point[0] <= previous[0] or point[1] == previous[1]):
            raise SnapshotError("agent counts must change at increasing times")
        previous = point
    if points[0][0] != chart["start"]:
        raise SnapshotError("agent counts must begin at the chart start")
    changes: defaultdict[int, int] = defaultdict(int)
    for row in chart["rows"]:
        if row["style"] != "wait":
            for item in row["items"]:
                changes[item["start"]] += 1
                changes[item["end"]] -= 1
    moments = sorted({*changes, *(point[0] for point in points)})
    drawn, index = 0, 0
    for moment in moments:
        if moment >= chart["cutoff"]:
            break
        drawn += changes[moment]
        while index + 1 < len(points) and points[index + 1][0] <= moment:
            index += 1
        agents = points[index][1]
        if (agents > 0) != (drawn > 0) or agents > drawn:
            raise SnapshotError("agent counts differ from the runs in the chart")


def validate(snapshot: Snapshot) -> None:
    """Check the chart bounds, ongoing runs, active/idle partition, and role totals."""
    try:
        reference = snapshot["reference"]
        if type(reference) is not int or reference < 0:
            raise SnapshotError("snapshot time must be an integer in milliseconds")
        if not isinstance(snapshot["chefs"], list):
            raise SnapshotError("snapshot must contain a Head Chef list")
        for chef in snapshot["chefs"]:
            short_id = chef["id"]
            if not re.fullmatch(r"[0-9a-z]{4}", short_id, re.IGNORECASE):
                raise SnapshotError("snapshot has an invalid Head Chef ID")
            if not isinstance(chef["title"], str) or not isinstance(chef["state"], str):
                raise SnapshotError("Head Chef title and state must be strings")
            try:
                _validate_chart(chef, reference)
            except SnapshotError as error:
                raise SnapshotError(f"Head Chef {short_id}: {error}") from error
    except (KeyError, IndexError, TypeError) as error:
        raise SnapshotError("snapshot has an invalid data shape") from error


def read_snapshot(source: str) -> Snapshot:
    matches = SNAPSHOT_LINE.findall(source)
    if len(matches) != 1:
        raise SnapshotError("dashboard must contain one embedded snapshot")
    try:
        snapshot = cast(Snapshot, json.loads(matches[0]))
    except json.JSONDecodeError as error:
        raise SnapshotError("dashboard snapshot is not valid JSON") from error
    validate(snapshot)
    return snapshot


def render(snapshot: Snapshot) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count(MARKER) != 1:
        raise SnapshotError("dashboard template must contain one empty snapshot marker")
    encoded = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    return template.replace(MARKER, f"const snapshot={encoded};", 1)


def summary(snapshot: Snapshot) -> dict[str, object]:
    reference = snapshot["reference"]
    active = [chef["id"] for chef in snapshot["chefs"] if _is_active(chef)]
    return {
        "reference": reference,
        "capture_montreal": (EPOCH + reference * MILLISECOND)
        .astimezone(MONTREAL)
        .isoformat(timespec="milliseconds"),
        "active": active,
        "inactive": len(snapshot["chefs"]) - len(active),
    }

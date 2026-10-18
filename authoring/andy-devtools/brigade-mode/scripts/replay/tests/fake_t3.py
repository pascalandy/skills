"""A small T3 database written the way T3 writes it: events, plus the projection they fold into.

Tests build a run here instead of reading Pascal's live database.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA = """
create table orchestration_events (
  sequence integer primary key autoincrement, event_id text not null unique,
  aggregate_kind text not null, stream_id text not null, stream_version integer not null,
  event_type text not null, occurred_at text not null, command_id text,
  causation_event_id text, correlation_id text, actor_kind text not null,
  payload_json text not null, metadata_json text not null,
  application_event_version integer not null default 1);
create table orchestration_v2_projection_threads (
  thread_id text primary key, project_id text not null, title text not null,
  created_at text not null, updated_at text not null, payload_json text not null);
create table orchestration_v2_projection_turn_items (
  turn_item_id text primary key, thread_id text not null, ordinal integer not null,
  type text not null, status text not null, updated_at text not null, payload_json text not null);
create table orchestration_v2_projection_runs (
  run_id text primary key, thread_id text not null, ordinal integer not null,
  status text not null, requested_at text not null, completed_at text, payload_json text not null);
create table orchestration_v2_projection_subagents (
  subagent_id text primary key, thread_id text not null, status text not null,
  started_at text, completed_at text, updated_at text not null, payload_json text not null);
create table projection_projects (project_id text primary key, workspace_root text not null);
"""


class FakeT3:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.con = sqlite3.connect(path)
        self.con.executescript(SCHEMA)
        self.clock = datetime(2026, 1, 1, tzinfo=UTC)
        self.ordinals: dict[str, int] = {}
        self.versions: dict[str, int] = {}
        self.items: dict[str, dict] = {}

    def now(self, seconds: float = 0) -> str:
        self.clock += timedelta(seconds=seconds)
        return self.clock.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def event(self, stream: str, event_type: str, payload: dict) -> None:
        self.versions[stream] = self.versions.get(stream, 0) + 1
        self.con.execute(
            "insert into orchestration_events (event_id, aggregate_kind, stream_id, stream_version, "
            "event_type, occurred_at, actor_kind, payload_json, metadata_json, application_event_version) "
            "values (?, 'thread', ?, ?, ?, ?, 'server', ?, '{}', 2)",
            (
                f"e{self.versions[stream]}-{stream}",
                stream,
                self.versions[stream],
                event_type,
                self.now(),
                json.dumps(payload),
            ),
        )
        self.con.commit()

    def project(self, project_id: str, root: str) -> None:
        self.con.execute(
            "insert into projection_projects values (?, ?)", (project_id, root)
        )
        self.con.commit()

    def thread(self, thread_id: str, title: str, project: str = "p-home") -> None:
        at = self.now(1)
        payload = {
            "id": thread_id,
            "projectId": project,
            "title": title,
            "createdAt": at,
            "updatedAt": at,
            "archivedAt": None,
            "lineage": {"parentThreadId": None},
        }
        self.event(thread_id, "thread.created", payload)
        self.con.execute(
            "insert or replace into orchestration_v2_projection_threads values (?, ?, ?, ?, ?, ?)",
            (thread_id, project, title, at, at, json.dumps(payload)),
        )
        self.con.commit()

    def item(
        self,
        thread: str,
        item_id: str,
        typ: str,
        status: str = "completed",
        **fields: Any,
    ) -> None:
        """Write one update of a turn item; a later call with the same id updates it."""
        at = self.now(1)
        old = self.items.get(item_id)
        if old is None:
            self.ordinals[thread] = self.ordinals.get(thread, 0) + 1
        payload = {
            **(old or {}),
            "id": item_id,
            "threadId": thread,
            "ordinal": old["ordinal"] if old else self.ordinals[thread],
            "type": typ,
            "status": status,
            "startedAt": old["startedAt"] if old else at,
            "completedAt": at if status == "completed" else None,
            "updatedAt": at,
            **fields,
        }
        self.items[item_id] = payload
        self.event(thread, "turn-item.updated", payload)
        self.con.execute(
            "insert or replace into orchestration_v2_projection_turn_items values (?, ?, ?, ?, ?, ?, ?)",
            (item_id, thread, payload["ordinal"], typ, status, at, json.dumps(payload)),
        )
        self.con.commit()

    def tool(
        self,
        thread: str,
        item_id: str,
        name: str,
        input: dict,
        output: dict | None = None,
    ) -> None:
        out = {"content": json.dumps(output)} if output is not None else None
        self.item(
            thread,
            item_id,
            "dynamic_tool",
            toolName=f"mcp__t3-code__{name}",
            input=input,
            output=out,
        )
        if name == "t3_thread_update" and input.get("action") == "rename":
            # T3 renames in its projection and writes no thread event
            target = input.get("threadId") or thread
            row = self.con.execute(
                "select payload_json from orchestration_v2_projection_threads where thread_id=?",
                (target,),
            ).fetchone()
            payload = {**json.loads(row[0]), "title": input["title"]}
            self.con.execute(
                "update orchestration_v2_projection_threads set title=?, payload_json=? where thread_id=?",
                (input["title"], json.dumps(payload), target),
            )
            self.con.commit()

    def run(self, thread: str, ordinal: int, status: str) -> None:
        at = self.now(1)
        run_id = f"run:{thread}:{ordinal}"
        row = self.con.execute(
            "select payload_json from orchestration_v2_projection_runs where run_id=?",
            (run_id,),
        ).fetchone()
        old = json.loads(row[0]) if row else {}
        payload = {
            "id": run_id,
            "threadId": thread,
            "ordinal": ordinal,
            "status": status,
            "requestedAt": old.get("requestedAt", at),
            "startedAt": old.get("startedAt", at),
            "completedAt": at if status == "completed" else None,
        }
        self.event(thread, "run.updated", payload)
        self.con.execute(
            "insert or replace into orchestration_v2_projection_runs values (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                thread,
                ordinal,
                status,
                payload["requestedAt"],
                payload["completedAt"],
                json.dumps(payload),
            ),
        )
        self.con.commit()

    def subagent(self, thread: str, task: str, status: str) -> None:
        at = self.now(1)
        row = self.con.execute(
            "select payload_json from orchestration_v2_projection_subagents where subagent_id=?",
            (task,),
        ).fetchone()
        old = json.loads(row[0]) if row else {}
        payload = {
            "id": task,
            "threadId": thread,
            "status": status,
            "startedAt": old.get("startedAt", at),
            "completedAt": at if status == "completed" else None,
            "prompt": "PLANTED FREE TEXT in a barrage prompt",
        }
        self.event(thread, "subagent.updated", payload)
        self.con.execute(
            "insert or replace into orchestration_v2_projection_subagents values (?, ?, ?, ?, ?, ?, ?)",
            (
                task,
                thread,
                status,
                payload["startedAt"],
                payload["completedAt"],
                at,
                json.dumps(payload),
            ),
        )
        self.con.commit()

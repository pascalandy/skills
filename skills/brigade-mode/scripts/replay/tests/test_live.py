"""The live service on a T3 database copy: its fold, its reads, its page, its restarts."""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import github
import live
import oracles
import pipeline
import pytest
import t3
from fake_t3 import FakeT3
from test_record import fake_env

if TYPE_CHECKING:
    from playwright.sync_api import Browser

HERE = Path(__file__).resolve().parent
HC = "00000000-0000-4000-8000-00000000abcd"
CHEF, COOK = "mcp:chef-one", "mcp:cook-one"
W = "example-owner/widget"
ASK = f"Lot prêt.\n🙋 merge #21 https://github.com/{W}/pull/21"
YOU_RED = "rgb(208, 59, 59)"  # --you: red belongs to "waits on you" alone


def head_chef(db: FakeT3) -> None:
    """A Head Chef that launched one Chef."""
    db.project("p-home", "/home/example/projects")
    db.project("p-widget", "/home/example/projects/widget")
    db.thread(HC, "Kick off a brigade")
    db.run(HC, 1, "running")
    db.item(
        HC, "u1", "user_message", createdBy="user", text="$brigade-mode ; carpaccio"
    )
    db.tool(
        HC,
        "rn",
        "t3_thread_update",
        {"action": "rename", "title": "Head Chef abcd 0/1 🟢 widget"},
    )
    db.thread(CHEF, "🚥 Chef 1 abcd ⏳ widget", "p-widget")
    db.tool(
        HC,
        "l1",
        "t3_thread_launch",
        {
            "title": "🚥 Chef 1 abcd ⏳ widget",
            "projectId": "p-widget",
            "message": "Batch: 1, Epic #9 in repository /home/example/projects/widget\nRelease: no",
        },
        {"threadId": CHEF},
    )
    db.run(HC, 1, "completed")


def cook(db: FakeT3) -> None:
    """The Chef launches its Cook, which links an open PR."""
    db.thread(COOK, "🧑‍🍳 Cook 1.1 abcd 🍳 widget", "p-widget")
    db.tool(
        CHEF,
        "l2",
        "t3_thread_launch",
        {
            "title": "🧑‍🍳 Cook 1.1 abcd 🍳 widget",
            "projectId": "p-widget",
            "message": "Story #11",
        },
        {"threadId": COOK},
    )
    db.run(COOK, 1, "running")
    db.tool(COOK, "k1", "link_pull_request", {"url": f"https://github.com/{W}/pull/21"})


def pr_event(db: FakeT3, state: str) -> None:
    db.event(
        COOK,
        t3.PR_EVENT,
        {
            "repository": W,
            "number": 21,
            "snapshot": {"state": state, "mergedAt": None, "closedAt": None},
        },
    )


def fold(snap: t3.Snapshot) -> tuple:
    return snap.threads, snap.items, snap.runs, snap.subagents, snap.titled


def test_follower_folds_what_load_reads(tmp_path: Path) -> None:
    db = FakeT3(tmp_path / "t3.sqlite")
    head_chef(db)
    con = t3.connect(db.path, 5)
    follower = t3.Follower(con, lambda: "")
    try:
        assert follower.changed()
        follower.read()
        assert follower.heads == [HC] and COOK not in follower.members
        assert fold(follower.snap) == fold(t3.load(con, [HC], follower.seq)[0])
        cook(db)  # a thread launched after the first read joins with its whole stream
        pr_event(db, "open")
        assert follower.changed()
        assert follower.read() == set()  # T3's first view of a PR changes nothing
        assert COOK in follower.members
        assert fold(follower.snap) == fold(t3.load(con, [HC], follower.seq)[0])
        pr_event(db, "closed")
        assert follower.changed()
        assert follower.read() == {
            W
        }  # a PR T3 saw change state: read its repository now
        assert not follower.changed()
    finally:
        con.close()
        db.con.close()


def test_an_older_run_shows_until_its_head_chef_ends_it(tmp_path: Path) -> None:
    db = FakeT3(tmp_path / "t3.sqlite")
    head_chef(db)  # created 2026-01-01, titled 🟢
    con = t3.connect(db.path, 5)
    try:
        assert t3.head_chefs(con, "2026-06-01") == []
        assert t3.head_chefs(con, "2026-06-01", unfinished=True) == [HC]
        db.tool(
            HC,
            "rn2",
            "t3_thread_update",
            {"action": "rename", "title": "Head Chef abcd 1/1 ⛳ widget"},
        )
        assert t3.head_chefs(con, "2026-06-01", unfinished=True) == []
    finally:
        con.close()
        db.con.close()


def test_no_read_transaction_stays_open_between_reads(tmp_path: Path) -> None:
    db = FakeT3(tmp_path / "t3.sqlite", wal=True)
    db.con.execute("pragma busy_timeout = 100")
    head_chef(db)
    con = t3.connect(db.path, 5)
    follower = t3.Follower(con, lambda: "")
    try:
        follower.changed()
        follower.read()
        cook(db)
        follower.changed()
        follower.read()
        db.item(HC, "a1", "assistant_message", text="more")
        # TRUNCATE empties the log only when no reader holds it
        assert db.con.execute("pragma wal_checkpoint(truncate)").fetchone() == (0, 0, 0)
        con.execute("begin")
        con.execute("select count(*) from orchestration_events").fetchall()
        db.item(HC, "a2", "assistant_message", text="more")
        held = db.con.execute("pragma wal_checkpoint(truncate)").fetchone()
        con.execute("commit")
        assert held[0] == 1  # the check has teeth: a held read blocks it
    finally:
        con.close()
        db.con.close()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get(port: int, path: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as error:
        with error:  # an error response holds its socket until closed
            body = error.read()
        return error.code, json.loads(body) if body.startswith(b"{") else {}


def start(tmp_path: Path, db: FakeT3, script: Path) -> tuple[subprocess.Popen, int]:
    """live.py on the database copy, with the fake gh and an empty home."""
    env = {**os.environ, **fake_env(tmp_path)}
    port = free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            str(script),
            "--db",
            str(db.path),
            "--port",
            str(port),
            "--days",
            "1",
            "--cache",
            str(tmp_path / "gh.json"),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        assert proc.poll() is None, proc.communicate()
        try:
            if get(port, "/healthz")[1].get("version"):
                return proc, port
        except OSError:
            pass
        time.sleep(0.2)
    proc.kill()
    raise AssertionError(f"no page in 30 s: {proc.communicate()}")


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        proc.communicate(timeout=10)


def live_run(tmp_path: Path) -> FakeT3:
    """The run as T3 holds it now: started ten minutes ago, its Cook at work."""
    db = FakeT3(
        tmp_path / "t3.sqlite", start=datetime.now(UTC).replace(microsecond=0), wal=True
    )
    db.clock = db.clock.fromtimestamp(time.time() - 600, UTC)
    head_chef(db)
    cook(db)
    return db


@pytest.fixture
def chromium() -> Iterator[Browser]:
    sync_api = pytest.importorskip("playwright.sync_api")
    executable = os.environ.get("CHECK_PAGE_BROWSER") or next(
        (
            p
            for p in map(
                shutil.which, ("chromium", "chromium-browser", "google-chrome")
            )
            if p
        ),
        None,
    )
    with sync_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(executable_path=executable)
        except sync_api.Error as error:
            first = str(error).strip().splitlines()[0]
            pytest.skip(
                f"Chromium is missing, so the live page was not opened: {first}; run: uv run --with playwright==1.63.0 playwright install chromium"
            )
        yield browser
        browser.close()


def test_page_repaints_within_seconds_of_a_new_event(
    tmp_path: Path, chromium: Browser
) -> None:
    db = live_run(tmp_path)
    proc, port = start(tmp_path, db, HERE.parent / "live.py")
    try:
        page = chromium.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{port}/")
        page.wait_for_function(
            "document.querySelector('#live').textContent.startsWith('Live: data')"
        )
        assert page.text_content("[data-you]") == ""

        def repaint(write, condition: str) -> float:
            db.clock = datetime.now(UTC)
            started = time.monotonic()
            write()
            page.wait_for_function(condition, timeout=10_000)
            return time.monotonic() - started

        lags = [
            # the Head Chef asks Pascal: red within seconds
            repaint(
                lambda: db.item(HC, "a1", "assistant_message", text=ASK),
                "document.querySelector('[data-you]').textContent.startsWith('Waits on you')",
            ),
            # his reply ends the wait
            repaint(
                lambda: db.item(HC, "u2", "user_message", createdBy="user", text="oui"),
                "document.querySelector('[data-you]').textContent === ''",
            ),
        ]
        print(f"T3 event to page: {', '.join(f'{x:.2f} s' for x in lags)}")
        assert max(lags) < 5

        status, health = get(port, "/healthz")
        assert status == 200 and health["ok"] and health["unparsed"] == 0
        assert health["seq"] > 0 and health["age"] < 5
        status, body = get(port, f"/data.json?v={health['version']}")
        assert "data" not in body and body["version"] == health["version"]

        # GitHub goes down while T3 reports the PR closed: the page keeps its data and says so
        (tmp_path / "gh-down").touch()
        pr_event(db, "open")
        pr_event(db, "closed")
        page.wait_for_function(
            "document.querySelector('#live').textContent.includes('GitHub read failed')",
            timeout=10_000,
        )
        assert page.get_attribute("#live", "data-stale") is not None
        assert (
            page.eval_on_selector("#live", "el => getComputedStyle(el).color")
            != YOU_RED
        )
        assert page.text_content("[data-title]")
        status, health = get(port, "/healthz")
        assert status == 200 and "HTTP 502" in health["errors"]["github"]
        assert errors == []

        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/healthz", method="POST"
        )
        with pytest.raises(urllib.error.HTTPError) as refused:
            urllib.request.urlopen(request, timeout=5)
        refused.value.close()
        assert refused.value.code == 501
        assert get(port, "/nothing")[0] == 404
    finally:
        stop(proc)
        db.con.close()


@pytest.mark.parametrize("changed", ["scripts/replay/board.js", "references/model.py"])
def test_service_stops_when_its_code_changes(tmp_path: Path, changed: str) -> None:
    app = tmp_path / "brigade-mode"  # the skill package, as a deploy installs it
    shutil.copytree(
        HERE.parents[2], app, ignore=shutil.ignore_patterns("tests", "__pycache__")
    )
    db = live_run(tmp_path)
    proc, _ = start(tmp_path, db, app / "scripts" / "replay" / "live.py")
    try:
        code = app / changed
        code.write_text(code.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        out, _ = proc.communicate(timeout=10)
        assert proc.returncode == 0
        assert json.loads(out.splitlines()[-1])["stopped"] == "its code changed"
    finally:
        stop(proc)
        db.con.close()


def test_data_age_counts_only_data_that_matches_t3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in fake_env(tmp_path).items():
        monkeypatch.setenv(name, value)
    db = live_run(tmp_path)
    con = t3.connect(db.path, 5)
    con.isolation_level = None
    state = live.State()
    service = live.Service(con, github.Cached(github.gh_reader(10)), 1, state)
    try:
        now = time.time()
        (tmp_path / "gh-down").touch()  # the first page needs GitHub facts
        service.tick(now)
        assert state.published.version == 0 and state.read is None
        assert "HTTP 502" in state.failures["github_new"].message
        (tmp_path / "gh-down").unlink()
        service.tick(now + pipeline.POLL)  # GitHub gets one read per turn
        assert state.published.version == 0
        service.tick(now + pipeline.GITHUB_EVERY)
        assert state.published.version == 1 and state.read is not None
        assert state.failures == {}
    finally:
        con.close()
        db.con.close()


def test_a_failed_t3_read_keeps_the_last_page_and_reads_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in fake_env(tmp_path).items():
        monkeypatch.setenv(name, value)
    db = live_run(tmp_path)
    con = t3.connect(db.path, 5)
    con.isolation_level = None
    state = live.State()
    service = live.Service(con, github.Cached(github.gh_reader(10)), 1, state)
    heads, broken = t3.head_chefs, [True]

    def flaky(*args: object, **kwargs: object) -> list[str]:
        if broken:
            raise sqlite3.OperationalError("database disk image is malformed")
        return heads(*args, **kwargs)  # type: ignore[arg-type]

    try:
        now = time.time()
        service.tick(now)
        first = state.published
        assert first.data["brigades"]
        monkeypatch.setattr(t3, "head_chefs", flaky)
        db.item(HC, "a1", "assistant_message", text=ASK)
        service.tick(now + 2)
        service.tick(now + 2 + live.CLOCK_EVERY)
        assert state.published is first and "malformed" in state.failures["t3"].message
        assert not state.health(now + 2 + live.CLOCK_EVERY)[0]
        broken.clear()
        service.tick(now + 4 + live.CLOCK_EVERY)  # the failed read is read again
        assert state.published.version == first.version + 1
        assert state.published.data["brigades"] and "t3" not in state.failures
    finally:
        con.close()
        db.con.close()


def test_github_errors_wait_their_turn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in fake_env(tmp_path).items():
        monkeypatch.setenv(name, value)
    gh_read, reads, limited = github.gh_reader(10), [], []

    def read(args: list[str]) -> dict:
        reads.append(args)
        if limited and args[:2] == ["api", "graphql"]:
            error = {"type": "RATE_LIMITED", "message": "API rate limit exceeded"}
            return {"data": None, "errors": [error]}
        return gh_read(args)

    db = live_run(tmp_path)
    con = t3.connect(db.path, 5)
    con.isolation_level = None
    state = live.State()
    service = live.Service(con, github.Cached(read), 1, state)
    # a merge waits a whole turn, a poll and a timed-out read, still before it shows
    assert pipeline.LAG < github.DELAY
    try:
        now = time.time()
        service.tick(now)
        assert state.published.version == 1
        limited.append(True)
        before = len(reads)
        for t in range(int(pipeline.GITHUB_EVERY), 120, int(pipeline.POLL)):
            assert service.tick(now + t) is None  # the service stays up
        assert len(reads) == before + 1  # one failed read in 60 s, not one per poll
        assert "rate limit" in state.failures["github"].message
        service.tick(now + 120)
        assert len(reads) == before + 2
    finally:
        con.close()
        db.con.close()


def test_a_github_outage_never_rewrites_what_the_page_showed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in fake_env(tmp_path).items():
        monkeypatch.setenv(name, value)
    gh_read, down, merged = github.gh_reader(10), [], []

    def read(args: list[str]) -> dict:
        if down and args[:2] == ["api", "graphql"]:
            error = {"type": "RATE_LIMITED", "message": "API rate limit exceeded"}
            return {"data": None, "errors": [error]}
        answer = gh_read(args)
        pr = ((answer.get("data") or {}).get("repository") or {}).get("p21")
        if merged and pr:
            pr["mergedAt"] = pr["closedAt"] = merged[0]
        return answer

    db = live_run(tmp_path)
    con = t3.connect(db.path, 5)
    con.isolation_level = None
    state = live.State()
    service = live.Service(con, github.Cached(read), 1, state)
    try:
        now = time.time()
        service.tick(now)
        merged.append(pipeline.t3_time(now + 1))  # Pascal merges PR 21
        down.append(True)  # and the next read of open items fails
        shown: dict[int, tuple[float, list]] = {}
        for t in range(2, 120, 2):
            service.tick(now + t)
            p = state.published
            shown.setdefault(p.version, (now + t, p.data["brigades"][0]["frames"]))
        assert state.read is not None and state.read <= now + github.DELAY
        assert not state.health(now + 118)[0]
        down.clear()
        service.tick(now + 120)  # the read that finds the merge
        final = state.published.data["brigades"][0]["frames"]
        assert oracles.state_at(final, now + 120)["cook-1.1"][2] == "shipped"
        for at, frames in shown.values():
            assert oracles.state_at(frames, at) == oracles.state_at(final, at)
    finally:
        con.close()
        db.con.close()


@pytest.mark.parametrize(
    ("flag", "value"), [("--cache", "t3.sqlite-wal"), ("--timeout", "30s")]
)
def test_live_refuses_settings_that_break_its_promises(
    tmp_path: Path, flag: str, value: str
) -> None:
    db = live_run(tmp_path)  # its open writer keeps the -wal file
    wal = tmp_path / "t3.sqlite-wal"
    before = wal.read_bytes()
    try:
        done = subprocess.run(
            [
                sys.executable,
                str(HERE.parent / "live.py"),
                *("--db", str(db.path), "--port", str(free_port())),
                flag,
                str(tmp_path / value) if flag == "--cache" else value,
            ],
            capture_output=True,
            text=True,
            env={**os.environ, **fake_env(tmp_path)},
            timeout=30,
            check=False,
        )
        assert done.returncode == 2 and done.stdout == ""
        assert wal.read_bytes() == before
    finally:
        db.con.close()


def test_live_settings_cannot_close_the_page_script() -> None:
    error = "</script><script>alert(1)</script>"  # an error string from T3 or gh
    page = pipeline.render_page({"generated": "", "brigades": []}, {}, {"error": error})
    assert error not in page and page.count("</script>") == 1

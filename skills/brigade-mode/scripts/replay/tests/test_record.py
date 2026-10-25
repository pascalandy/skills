"""The recorder end to end on a synthetic T3 database, and the committed recordings."""

from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import record
import t3
from fake_t3 import FakeT3

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "record.py"
RECORDINGS = sorted((HERE / "recordings").glob("*.json.gz"))
HC = "00000000-0000-4000-8000-00000000abcd"
CHEF, COOK = "mcp:chef-one", "mcp:cook-one"
PLANTED = "PLANTED FREE TEXT"

WATCH = """cd /home/example/.cache/brigade-abcd/head-chef && cat > watch.toml.tmp <<'EOF'
parentThreadId = "00000000-0000-4000-8000-00000000abcd"
subject = "PLANTED FREE TEXT"

[[slots]]
slot = "head-chef"
threadId = "00000000-0000-4000-8000-00000000abcd"
workFolder = "/home/example/.cache/brigade-abcd/head-chef"
lastReceivedPhase = "🟢"

[[slots]]
slot = "chef-1"
threadId = ""
lastReceivedPhase = "queued"
batchName = "Epic 3 #9 PLANTED FREE TEXT"
repository = "/home/example/projects/widget"

[[slots]]
slot = "chef-2"
threadId = ""
lastReceivedPhase = "queued"
batchName = "Epic 7 secret-thing#4"
repository = "/home/example/projects/secret-thing"
EOF
mv watch.toml.tmp watch.toml"""


def build(path: Path) -> None:
    """A Head Chef that registers two batches, launches one Chef and its Cook, which ships a PR."""
    db = FakeT3(path)
    projects = path.parent / "projects"
    (projects / "widget").mkdir(parents=True)
    (projects / "widget" / ".git").write_text(
        "gitdir: ../worktrees/widget\n", encoding="utf-8"
    )
    db.project("p-home", str(projects))
    db.project("p-widget", str(projects / "widget"))
    db.thread(HC, "Kick off a brigade PLANTED FREE TEXT")
    db.run(HC, 1, "running")
    db.item(
        HC,
        "u1",
        "user_message",
        createdBy="user",
        text=f"$brigade-mode ; carpaccio {PLANTED}",
    )
    db.tool(
        HC,
        "rn",
        "t3_thread_update",
        {"action": "rename", "title": f"Head Chef abcd 0/2 🟢 {PLANTED}"},
    )
    db.item(HC, "w1", "command_execution", input=WATCH)
    db.thread(CHEF, f"🚥 Chef 1 abcd ⏳ {PLANTED}", "p-widget")
    db.tool(
        HC,
        "l1",
        "t3_thread_launch",
        {
            "title": f"🚥 Chef 1 abcd ⏳ {PLANTED}",
            "projectId": "p-widget",
            "message": f"Batch: 1, Epic #9 in repository /home/example/projects/widget\nRelease: no\n{PLANTED}",
        },
        {"threadId": CHEF},
    )
    db.thread(COOK, f"🧑‍🍳 Cook 1.1 abcd 🍳 {PLANTED}", "p-widget")
    db.tool(
        CHEF,
        "l2",
        "t3_thread_launch",
        {
            "title": "🧑‍🍳 Cook 1.1 abcd 🍳 x",
            "projectId": "p-widget",
            "message": "Story #10",
        },
        {"threadId": COOK},
    )
    db.run(COOK, 1, "running")
    db.tool(
        COOK,
        "k1",
        "link_pull_request",
        {"url": "https://github.com/example-owner/widget/pull/20"},
    )
    task = (
        "node:delegated-task:command%3Amcp%3Axyz%3Adelegate-task%3Aabcd-1.1-manic-1-1"
    )
    db.tool(
        COOK,
        "d1",
        "delegate_task",
        {"title": "👀 manic-1 · Cook 1.1 abcd", "task": PLANTED},
        {"taskId": task},
    )
    db.subagent(COOK, task, "running")
    db.subagent(COOK, task, "completed")
    db.tool(
        COOK,
        "s1",
        "t3_thread_send",
        {
            "threadId": CHEF,
            "message": f"🍽️ Stack ready · Cook 1.1 abcd\nPR: #20 1a2b3c4, checks pass\n{PLANTED}",
        },
    )
    db.run(COOK, 1, "completed")
    db.item(
        HC,
        "a1",
        "assistant_message",
        text=f"Lot prêt.\n🙋 merge #20 https://github.com/example-owner/widget/pull/20 {PLANTED}",
    )
    # talks about the run, but its threadId does not end with abcd: not its Head Chef
    db.thread("import:claudeAgent:0000-xyz9", "Head Chef abcd status reconciliation")
    db.con.close()  # tests read the file; an open connection warns under -W error


def fake_env(tmp_path: Path) -> dict[str, str]:
    """A gh that answers from canned facts, down while tmp_path/gh-down exists,
    and an empty home, so no real work folder is read."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{HERE / "fake_gh.py"}" "$@"\n')
    gh.chmod(0o755)
    return {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(tmp_path),
        "FAKE_GH_DOWN": str(tmp_path / "gh-down"),
    }


def run_record(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **fake_env(tmp_path)}
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_recording_keeps_the_run_and_drops_free_text(tmp_path: Path) -> None:
    build(tmp_path / "t3.sqlite")
    out = tmp_path / "abcd.json.gz"
    done = run_record(
        tmp_path,
        "--brigade",
        "abcd",
        "--db",
        str(tmp_path / "t3.sqlite"),
        "-o",
        str(out),
    )
    assert done.returncode == 0, done.stderr
    answer = json.loads(done.stdout)
    assert answer["ok"] and answer["changes"] == [["write", str(out)]]
    text = gzip.decompress(out.read_bytes()).decode()
    assert PLANTED not in text and "/home/" not in text and "secret-thing" not in text
    data = t3.load_recording(out)
    assert record.check_recording(data) == []
    assert data["brigade"] == "abcd" and data["head"] == HC
    assert set(data["github"]["repositories"]) == {"example-owner/widget", "private-A"}

    snap = t3.fold(data["records"])
    assert "p-home" not in snap.projects
    assert snap.projects["p-widget"] == "example-owner/widget"
    assert set(snap.threads) == {HC, CHEF, COOK}  # the import thread is no Head Chef
    assert snap.title(HC) == {
        "role": "head_chef",
        "id4": "abcd",
        "status": "🟢",
        "n": [0, 2],
    }
    assert snap.head_chef_since(HC)
    tools = {i.get("tool") for i in snap.items.values()}
    assert {"launch", "link", "delegate", "send", "rename"} <= tools
    send = next(i for i in snap.items.values() if i.get("tool") == "send")
    assert send["handoffs"] == [["stack_ready"]] and send["checks"] == "pass"
    assert t3.classify(send, "cook", "chef") == "stack_ready"
    watch = next(i["watch"] for i in snap.items.values() if i.get("watch"))
    assert watch["full"]["chef-1"]["refs"] == [["example-owner/widget", 9]]
    assert watch["full"]["chef-2"]["refs"] == [["private-A", 4]]
    ask = next(i for i in snap.items.values() if i["type"] == "assistant_message")
    assert ask["items"] == ["merge"]
    assert data["github"]["prs"]["example-owner/widget#20"]["refs"] == [
        ["example-owner/widget", 10]
    ]
    assert ["private-A", 4] in data["github"]["prs"]["example-owner/widget#20"][
        "refHistory"
    ][0][1]
    assert data["github"]["issues"]["example-owner/widget#9"]["epic"] == 3


def test_unknown_brigade_is_a_usage_error(tmp_path: Path) -> None:
    build(tmp_path / "t3.sqlite")
    done = run_record(
        tmp_path, "--brigade", "xyz9", "--db", str(tmp_path / "t3.sqlite")
    )
    assert done.returncode == 2 and done.stdout == ""
    assert "names 0 Head Chefs" in json.loads(done.stderr.splitlines()[-1])["errors"][0]


@pytest.mark.parametrize("end", ["", "-wal"])
def test_output_never_overwrites_the_database(tmp_path: Path, end: str) -> None:
    db = tmp_path / "t3.sqlite"
    build(db)
    target = db.with_name(db.name + end)
    target.touch()
    before = target.read_bytes()
    done = run_record(tmp_path, "--brigade", "abcd", "--db", str(db), "-o", str(target))
    assert done.returncode == 2 and done.stdout == ""
    assert "would overwrite T3's database" in done.stderr
    assert target.read_bytes() == before


def test_whitelist_refuses_free_text() -> None:
    assert t3.whitelist_errors([1, None, "item", "i1", {"thread": "x", "type": "a b"}])
    assert t3.whitelist_errors([1, None, "item", "i1", {"thread": "x", "text": "a"}])
    assert not t3.whitelist_errors(
        [1, None, "item", "i1", {"thread": "x", "type": "user_message"}]
    )


@pytest.mark.parametrize(
    "command, full, blocks, mentions",
    [
        (WATCH, {"head-chef", "chef-1", "chef-2"}, set(), set()),
        (
            "python3 - watch.toml <<'PY'\ns+='''\n[[slots]]\nslot = \"chef-3\"\nthreadId = \"mcp:x\"\n'''\nopen(p,'w').write(s)\nPY",
            set(),
            {"chef-3"},
            {"chef-3"},
        ),
        (
            'sed -i \'s/^lastReceivedPhase = "❓"/lastReceivedPhase = "⏳"/\' watch.toml',
            set(),
            set(),
            set(),
        ),
        (
            "awk '/^slot = \"chef-2\"/ {s=1} {print}' watch.toml > w && mv w watch.toml",
            set(),
            set(),
            {"chef-2"},
        ),
    ],
)
def test_watch_writes(
    command: str, full: set[str], blocks: set[str], mentions: set[str]
) -> None:
    w = t3.watch_write(command)
    assert w is not None and w["write"]
    assert set(w.get("full", {})) == full
    assert set(w.get("blocks", {})) == blocks
    assert set(w.get("mentions", [])) == mentions


@pytest.mark.parametrize("path", RECORDINGS, ids=lambda p: p.name)
def test_committed_recording_fits_the_whitelist(path: Path) -> None:
    data = t3.load_recording(path)
    assert record.check_recording(data) == []
    snap = t3.fold(data["records"])
    assert snap.head_chef_since(data["head"]), (
        "the recorded Head Chef keeps its id4 title"
    )
    assert data["head"][-4:] == path.name.split(".")[0]


def test_fold_keeps_when_each_fact_arrived() -> None:
    item = {
        "thread": "t",
        "ordinal": 1,
        "type": "dynamic_tool",
        "status": "running",
        "start": "2026-01-01T00:00:00.000Z",
        "end": None,
    }
    done = {**item, "status": "completed", "end": "2026-01-01T00:00:01.000Z"}
    snap = t3.fold(
        [
            [1, "2026-01-01T00:00:00.500Z", "item", "i1", item],
            [2, "2026-01-01T00:00:01.300Z", "item", "i1", done],
            [3, "2026-01-01T00:00:09.000Z", "item", "i1", done],
        ]
    )
    folded = snap.items["i1"]
    assert t3.plain(folded) == done
    # its end is stamped before the record that carries it arrived: the page waits for the record
    assert folded["seen"] == "2026-01-01T00:00:00.500Z"
    assert t3.later(folded["end"], folded["endSeen"]) == "2026-01-01T00:00:01.300Z"

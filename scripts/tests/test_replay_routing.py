"""just replay-routing through its CLI, with a stub codex that replays scripted events."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import SCRIPTS

ROOT = SCRIPTS.parent

# Prints the events scripted for the request on stdin, one JSON object per line.
# {"sleep": N} pauses, so a test can see whether the replay stopped the run.
STUB_CODEX = """#!/usr/bin/env python3
import json, os, subprocess, sys, time
args = sys.argv[1:]
request = sys.stdin.read()
scratch = args[args.index("-C") + 1]
status = subprocess.run(["git", "status", "--porcelain"], cwd=scratch,
                        capture_output=True, text=True).stdout
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps({"args": args, "request": request, "status": status}) + "\\n")
for event in json.load(open(os.environ["STUB_EVENTS"]))[request]:
    if "sleep" in event:
        time.sleep(event["sleep"])
        continue
    print(json.dumps(event), flush=True)
"""

TABLE = """# Routing cases

| Request | Reads | Opens with |
|---|---|---|
| `make it convert` | `playbooks/cro.md` | `Route: cro` |
| `fix my build` | none | |
| `improve it` | no route | |
| `ask the other mode` | manual | |
"""


def command(cmd: str) -> dict:
    return {
        "type": "item.started",
        "item": {"type": "command_execution", "command": cmd},
    }


def message(text: str) -> dict:
    return {"type": "item.completed", "item": {"type": "agent_message", "text": text}}


DONE = {"type": "turn.completed"}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A checkout with the script, one compiled skill, a stub codex, and an installed copy."""
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    for name in ("replay_routing.py", "_cli.py", "_common.py"):
        shutil.copy2(SCRIPTS / name, root / "scripts" / name)
    skill = root / "skills/demo"
    (skill / "playbooks").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text(
        '---\nname: "demo"\ndescription: "Use for demos."\n---\n\n'
        "Route to [cro](playbooks/cro.md) or [seo](playbooks/seo.md).\n"
    )
    (skill / "playbooks/cro.md").write_text("CRO steps.\n")
    (skill / "playbooks/seo.md").write_text("SEO steps.\n")
    (skill / "references/routing-cases.md").write_text(TABLE)
    installed = tmp_path / "codex-home/skills/demo/SKILL.md"
    installed.parent.mkdir(parents=True)
    installed.write_text("installed copy\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "codex").write_text(STUB_CODEX)
    (bin_dir / "codex").chmod(0o755)
    return root


def replay(
    repo: Path, events: dict[str, list[dict]], *args: str, path: str | None = None
) -> subprocess.CompletedProcess[str]:
    scripted = repo.parent / "events.json"
    scripted.write_text(json.dumps(events))
    env = {
        **os.environ,
        "PATH": path
        if path is not None
        else f"{repo.parent / 'bin'}{os.pathsep}{os.environ['PATH']}",
        "CODEX_HOME": str(repo.parent / "codex-home"),
        "HOME": str(repo.parent / "home"),
        "STUB_EVENTS": str(scripted),
        "STUB_LOG": str(repo.parent / "codex.log"),
        "TMPDIR": str(repo.parent),
    }
    return subprocess.run(
        [sys.executable, str(repo / "scripts/replay_routing.py"), "demo", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def calls(repo: Path) -> list[dict]:
    log = repo.parent / "codex.log"
    return (
        [json.loads(line) for line in log.read_text().splitlines()]
        if log.exists()
        else []
    )


SKILL_MD = "cat .agents/skills/demo/SKILL.md"
CRO = "cat .agents/skills/demo/playbooks/cro.md"
SEO = "cat .agents/skills/demo/playbooks/seo.md"


def test_each_row_passes_and_a_routed_run_stops_before_its_work(repo: Path) -> None:
    events = {
        "make it convert": [
            command(SKILL_MD),
            message("Route: cro\nReading the playbook."),
            command(CRO),
            {"sleep": 60},
            DONE,
        ],
        "fix my build": [message("Fixed build.sh."), DONE],
        "improve it": [command(SKILL_MD), message("cro or seo?"), DONE],
    }

    started = time.monotonic()
    result = replay(repo, events)

    assert (result.returncode, result.stderr) == (0, "")
    assert result.stdout.splitlines() == [
        "pass\t1\tmake it convert",
        "pass\t2\tfix my build",
        "pass\t3\timprove it",
        "skip\t4\task the other mode\tmanual",
    ]
    assert time.monotonic() - started < 30
    first = calls(repo)[0]
    assert first["status"] == ""
    assert (
        f'skills.config=[{{path="{repo.parent}/codex-home/skills/demo/SKILL.md",enabled=false}}]'
        in first["args"]
    )
    assert 'model_reasoning_effort="low"' in first["args"]
    assert sorted(call["request"] for call in calls(repo)) == [
        "fix my build",
        "improve it",
        "make it convert",
    ]


@pytest.mark.parametrize(
    ("events", "reason"),
    [
        (
            [
                command(SKILL_MD),
                message("Route: seo"),
                command(SEO),
                {"sleep": 60},
                DONE,
            ],
            (
                "opened playbooks/seo.md where playbooks/cro.md was expected; "
                "opened SKILL.md, playbooks/seo.md"
            ),
        ),
        (
            [command(SKILL_MD), command(CRO), message("Here is my advice."), DONE],
            "first message opens with 'Here is my advice.'; opened SKILL.md, playbooks/cro.md",
        ),
        (
            [command(SKILL_MD), message("Route: cro"), DONE],
            "finished without opening playbooks/cro.md; opened SKILL.md",
        ),
    ],
)
def test_a_row_that_misroutes_fails_with_what_the_agent_opened(
    repo: Path, events: list[dict], reason: str
) -> None:
    result = replay(repo, {"make it convert": events}, "--case", "1")

    assert (result.returncode, result.stdout) == (1, "")
    line, rerun = result.stderr.splitlines()[-2:]
    assert line.startswith(f"error: fail\t1\tmake it convert\t{reason}; events ")
    assert Path(line.rsplit("events ", 1)[1]).is_file()
    assert rerun.endswith(
        "1 of 1 rows failed; rerun them with: just replay-routing demo --case 1"
    )


def test_a_row_that_must_not_route_fails_on_the_first_playbook(repo: Path) -> None:
    events = {
        "fix my build": [command(SKILL_MD), {"sleep": 60}, DONE],
        "improve it": [command(SKILL_MD), command(SEO), {"sleep": 60}, DONE],
    }

    result = replay(repo, events, "--case", "2", "--case", "3")

    assert result.returncode == 1
    assert [line.split("; events")[0] for line in result.stderr.splitlines()[:2]] == [
        "error: fail\t2\tfix my build\tloaded the skill: opened SKILL.md; opened SKILL.md",
        "error: fail\t3\timprove it\topened playbooks/seo.md; opened SKILL.md, playbooks/seo.md",
    ]


def test_a_missing_codex_fails_before_any_row(repo: Path) -> None:
    result = replay(repo, {}, path="/usr/bin:/bin")

    assert (result.returncode, result.stdout) == (1, "")
    assert "codex not found on PATH; install the Codex CLI, then rerun" in result.stderr
    assert calls(repo) == []


def test_a_row_naming_a_file_skill_md_does_not_link_is_a_usage_error(
    repo: Path,
) -> None:
    cases = repo / "skills/demo/references/routing-cases.md"
    cases.write_text(TABLE.replace("`playbooks/cro.md`", "`playbooks/cr0.md`"))

    result = replay(repo, {}, "--dry-run")

    assert result.returncode == 2
    assert (
        "row 1 expects playbooks/cr0.md, which SKILL.md does not link to"
        in result.stderr
    )


@pytest.mark.parametrize(("skill", "rows"), [("corey-mode", 13), ("andy-mode", 25)])
def test_the_routing_tables_in_this_repository_parse(skill: str, rows: int) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "replay_routing.py"), skill, "--dry-run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert (result.returncode, result.stderr) == (0, "")
    assert len(result.stdout.splitlines()) == rows

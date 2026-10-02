#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Replay a skill's routing cases through headless Codex, stopping each run once it routes."""

from __future__ import annotations

import argparse
import json
import logging
import os
import posixpath
import re
import shutil
import signal
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from _cli import Parser, ScriptError, UsageError, duration, exit_codes
from _common import run_git, run_script, send, stop

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
CASES = "references/routing-cases.md"
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "replay",
    "GIT_AUTHOR_EMAIL": "replay@example.com",
    "GIT_COMMITTER_NAME": "replay",
    "GIT_COMMITTER_EMAIL": "replay@example.com",
}

EPILOG = f"""\
Each row runs in a fresh scratch Git project that holds a copy of the compiled
skill in .agents/skills/<skill>/, with every installed copy disabled. The run
stops as soon as the row passes or fails, so the agent never does the work.

The table, in <skill>/{CASES} unless --cases names another file, has three
columns:

  | Request | Reads | Opens with |

Request is the prompt, in backticks. Reads lists the route files the agent must
open, in order, as backticked paths from the skill folder, such as
`playbooks/cro/cro.md`; a route file is SKILL.md or a file SKILL.md links to.
`none` means the skill must not load, `no route` means it may read SKILL.md but
no other route file, and `manual` skips the row. Opens with, when set, is the
start of the agent's first message.

A run prints one line per row: pass or skip, the row number, and the request.
When a row fails, stderr names each failed row, what the agent opened, and the
path of its saved events, then the command that reruns those rows.

examples:
  just replay-routing corey-mode --project authoring/corey-mode/tests/routing-project
  just replay-routing andy-mode --case 3 --case 7
  just replay-routing andy-mode --dry-run"""

EXIT_CODES = exit_codes(
    {
        0: "every row passed or was skipped",
        1: "a row failed, or codex could not start",
    }
)

HEADER = ("request", "reads", "opens with")
CELL_RE = re.compile(r"`([^`]+)`")
LINK_RE = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")

log = logging.getLogger("replay-routing")

# Running Codex sessions, stopped on an interrupt so none keeps working unwatched
LIVE: set[subprocess.Popen[str]] = set()

Kind = Literal["route", "none", "no route", "manual"]
KINDS: dict[str, Kind] = {"none": "none", "no route": "no route", "manual": "manual"}


@dataclass(frozen=True)
class Case:
    number: int
    request: str
    kind: Kind
    reads: tuple[str, ...]
    opens_with: str

    def describe(self) -> str:
        return ", ".join(self.reads) if self.kind == "route" else self.kind


@dataclass
class Run:
    """What the agent did so far: route files opened, in order, and its first message."""

    opened: list[str] = field(default_factory=list)
    first_message: str | None = None
    finished: bool = False
    error: str = ""

    def routes(self) -> list[str]:
        return [path for path in self.opened if path != "SKILL.md"]


def route_files(skill: Path) -> set[str]:
    """SKILL.md and every local file it links to, as paths from the skill folder."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    found = {"SKILL.md"}
    for target in LINK_RE.findall(text):
        if "://" in target or target.startswith("/"):
            continue
        found.add(posixpath.normpath(target))
    return found


def parse_cases(path: Path, routes: set[str]) -> list[Case]:
    """The rows of the Request | Reads | Opens with table in `path`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    cells = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    start = next(
        (i for i, row in enumerate(cells) if tuple(c.lower() for c in row) == HEADER),
        None,
    )
    if start is None:
        raise UsageError(f"{path} has no | Request | Reads | Opens with | table")
    body = []
    for line, row in zip(lines[start + 2 :], cells[start + 2 :], strict=True):
        if not line.lstrip().startswith("|"):
            break
        body.append(row)
    cases: list[Case] = []
    for number, row in enumerate(body, start=1):
        if len(row) != 3:
            raise UsageError(f"{path}: row {number} has {len(row)} cells, not 3")
        request = CELL_RE.findall(row[0])
        reads_cell = row[1].lower()
        reads = tuple(posixpath.normpath(p) for p in CELL_RE.findall(row[1]))
        kind = KINDS.get(reads_cell, "route")
        if kind != "route":
            reads = ()
        if len(request) != 1 or (kind == "route" and not reads):
            raise UsageError(
                f"{path}: row {number} needs one backticked request and backticked "
                "route files, none, no route, or manual"
            )
        if unknown := [p for p in reads if p not in routes]:
            raise UsageError(
                f"{path}: row {number} expects {', '.join(unknown)}, which SKILL.md "
                "does not link to"
            )
        opens = CELL_RE.findall(row[2])
        cases.append(Case(number, request[0], kind, reads, opens[0] if opens else ""))
    return cases


def opened_in(command: str, name: str, routes: set[str]) -> list[str]:
    """Route files a shell command names, in the order it names them."""
    hits = []
    for route in routes:
        needle = posixpath.normpath(f"skills/{name}/{route}")
        if (index := command.find(needle)) >= 0:
            hits.append((index, route))
    return [route for _, route in sorted(hits)]


def verdict(case: Case, run: Run) -> str | None:
    """An empty reason when the row passed, a reason when it failed, None while undecided."""
    routes = run.routes()
    if case.kind == "route":
        for expected, actual in zip(case.reads, routes, strict=False):
            if actual != expected:
                return f"opened {actual} where {expected} was expected"
        routed = len(routes) >= len(case.reads)
        if routed and (not case.opens_with or run.first_message is not None):
            return opener(case, run)
        if run.finished:
            missing = ", ".join(case.reads[len(routes) :]) or "its first message"
            return run.error or f"finished without opening {missing}"
        return None
    if case.kind == "none" and run.opened:
        return f"loaded the skill: opened {run.opened[0]}"
    if case.kind == "no route" and routes:
        return f"opened {routes[0]}"
    if run.finished:
        return run.error or opener(case, run)
    return None


def opener(case: Case, run: Run) -> str:
    first = (run.first_message or "").strip().splitlines()[:1]
    if case.opens_with and not (first and first[0].startswith(case.opens_with)):
        return f"first message opens with {first[0] if first else 'nothing'!r}"
    return ""


def installed_copies(name: str) -> list[Path]:
    codex_home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    candidates = (codex_home / "skills", Path.home() / ".agents/skills")
    return [
        p / name / "SKILL.md" for p in candidates if (p / name / "SKILL.md").is_file()
    ]


def prepare(work: Path, skill: Path, project: Path | None) -> Path:
    """A scratch Git project with `project`'s files and an untracked copy of the skill."""
    scratch = work / "project"
    if project:
        shutil.copytree(project, scratch)
    scratch.mkdir(exist_ok=True)
    env = {**os.environ, **GIT_IDENTITY}
    for args in (
        ("init", "-q"),
        ("add", "-A"),
        ("commit", "-q", "--allow-empty", "-m", "seed"),
    ):
        done = run_git(*args, cwd=scratch, env=env)
        if done.returncode:
            raise ScriptError(
                f"could not seed the scratch project: {done.stderr.strip()}"
            )
    copy = scratch / ".agents/skills" / skill.name
    shutil.copytree(skill, copy, ignore=shutil.ignore_patterns("__pycache__"))
    # The tested agent then sees no uncommitted change from the copy
    (copy / ".gitignore").write_text("*\n", encoding="utf-8")
    return scratch


def codex_command(scratch: Path, name: str, args: argparse.Namespace) -> list[str]:
    command = ["codex", "exec", "--json", "--ephemeral", "-s", "workspace-write"]
    command += ["-C", str(scratch), "-c", f'model_reasoning_effort="{args.effort}"']
    if args.model:
        command += ["-m", args.model]
    if copies := installed_copies(name):
        entries = ",".join(f'{{path="{p}",enabled=false}}' for p in copies)
        command += ["-c", f"skills.config=[{entries}]"]
    return [*command, "-"]


def replay(case: Case, skill: Path, routes: set[str], args: argparse.Namespace) -> str:
    """One line for the row: pass, or fail with the reason and the saved events."""
    if case.kind == "manual":
        return f"skip\t{case.number}\t{case.request}\tmanual"
    work = Path(tempfile.mkdtemp(prefix=f"replay-{skill.name}-{case.number}-"))
    events = work / "events.jsonl"
    scratch = prepare(work, skill, args.project)
    run = Run()
    reason: str | None = None
    timed_out = threading.Event()

    with (
        events.open("w", encoding="utf-8") as saved,
        (work / "stderr.txt").open("w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            codex_command(scratch, skill.name, args),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        LIVE.add(process)
        assert process.stdin and process.stdout
        process.stdin.write(case.request)
        process.stdin.close()

        def expire() -> None:
            timed_out.set()
            send(process, signal.SIGTERM, group=True)

        timer = threading.Timer(args.timeout, expire)
        timer.start()
        log.info("replay row %d: %s", case.number, case.request)
        try:
            for line in process.stdout:
                saved.write(line)
                read(line, skill.name, routes, run)
                if (reason := verdict(case, run)) is not None:
                    break
        finally:
            timer.cancel()
            if process.poll() is None:
                stop(process, group=True)
            process.wait()
            LIVE.discard(process)
    if reason is None and timed_out.is_set():
        reason = f"no verdict within {args.timeout:g}s"
    if reason is None:
        run.finished = True
        if not run.error and process.returncode:
            run.error = f"codex exited {process.returncode}; see {work / 'stderr.txt'}"
        reason = verdict(case, run) or ""
    if not reason:
        shutil.rmtree(work, ignore_errors=True)
        return f"pass\t{case.number}\t{case.request}"
    opened = ", ".join(run.opened) or "nothing"
    return f"fail\t{case.number}\t{case.request}\t{reason}; opened {opened}; events {events}"


def read(line: str, name: str, routes: set[str], run: Run) -> None:
    """Fold one Codex JSON event into `run`."""
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return
    item = event.get("item") or {}
    if item.get("type") == "command_execution":
        for route in opened_in(str(item.get("command", "")), name, routes):
            if route not in run.opened:
                run.opened.append(route)
    elif event.get("type") == "item.completed" and item.get("type") == "agent_message":
        if run.first_message is None:
            run.first_message = str(item.get("text", ""))
    elif event.get("type") == "turn.completed":
        run.finished = True
    elif event.get("type") in ("turn.failed", "error"):
        message = (event.get("error") or {}).get("message") or event.get("message")
        run.error = f"codex reported: {message}"
        run.finished = True


def work(args: argparse.Namespace) -> str:
    skill = SKILLS / args.skill
    if not (skill / "SKILL.md").is_file():
        raise UsageError(
            f"no compiled skill {args.skill} in skills/; run just compile-skills"
        )
    cases_file = args.cases or skill / CASES
    if not cases_file.is_file():
        raise UsageError(f"no routing cases at {cases_file}; pass --cases FILE")
    routes = route_files(skill)
    cases = parse_cases(cases_file, routes)
    if args.case:
        missing = sorted(set(args.case) - {case.number for case in cases})
        if missing:
            raise UsageError(f"{cases_file} has no row {missing[0]}")
        cases = [case for case in cases if case.number in args.case]
    if args.jobs < 1:
        raise UsageError(f"--jobs must be at least 1, not {args.jobs}")
    if args.dry_run:
        return "\n".join(
            f"case\t{c.number}\t{c.describe()}\t{c.request}" for c in cases
        )
    if shutil.which("codex") is None:
        raise ScriptError("codex not found on PATH; install the Codex CLI, then rerun")
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        try:
            lines = list(pool.map(lambda c: replay(c, skill, routes, args), cases))
        except BaseException:
            for process in list(LIVE):
                send(process, signal.SIGTERM, group=True)
            raise
    if failed := [line for line in lines if line.startswith("fail\t")]:
        rerun = ["just replay-routing", args.skill]
        rerun += [f"--cases {args.cases}"] if args.cases else []
        rerun += [f"--project {args.project}"] if args.project else []
        rerun += [f"--case {line.split(chr(9))[1]}" for line in failed]
        raise ScriptError(
            *failed,
            f"{len(failed)} of {len(lines)} rows failed; rerun them with: "
            + " ".join(rerun),
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just replay-routing",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument("skill", help="a compiled skill in skills/, such as corey-mode")
    parser.add_argument(
        "--cases", type=Path, help=f"the routing table (default: <skill>/{CASES})"
    )
    parser.add_argument(
        "--project",
        type=Path,
        help="a folder whose files seed each scratch project (default: an empty one)",
    )
    parser.add_argument(
        "--case",
        type=int,
        action="append",
        default=[],
        metavar="N",
        help="replay only row N of the table; repeatable",
    )
    parser.add_argument("--model", help="the Codex model (default: Codex's own)")
    parser.add_argument(
        "--effort", default="low", help="the reasoning effort (default: low)"
    )
    parser.add_argument(
        "--jobs", type=int, default=4, help="rows replayed at once (default: 4)"
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="10m",
        help="how long one row may run (default: 10m)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="list the rows a run would replay, without starting Codex",
    )
    return run_script(parser, work, argv, debug="REPLAY_ROUTING_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

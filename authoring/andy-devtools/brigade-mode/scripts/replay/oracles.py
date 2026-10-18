#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Check recorded runs against oracles other than the replay's own rules."""

from __future__ import annotations

# >>> cli-block: canonical copy in scripts/_cli.py; do not edit a pasted copy
import argparse
import json
import logging
import os
import re
import shlex
import signal
import sys
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, NoReturn, TextIO

USAGE = 2
TEMPORARY = 75
INTERRUPTED = 128 + signal.SIGINT
TERMINATED = 128 + signal.SIGTERM


class ScriptError(Exception):
    """An expected failure; each argument is one message that says what to fix.

    `detail` is text printed on stderr before the answer; `report` holds the
    fields the answer carries beside `errors`, such as `changes`.
    """

    code = 1

    def __init__(
        self, *messages: str, detail: str = "", report: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(*messages)
        self.detail = detail
        self.report = dict(report or {})


class UsageError(ScriptError):
    """A bad argument the parser cannot catch, such as an unknown name."""

    code = USAGE


class TemporaryError(ScriptError):
    """A failure a later retry may fix: an outage, a timeout, or a held lock."""

    code = TEMPORARY


class Interrupted(KeyboardInterrupt):
    """SIGINT or SIGTERM arrived; `code` is 130 or 143."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def exit_codes(specific: Mapping[int, str]) -> dict[int, str]:
    """Every code a script returns, in order, for its --help and its tests.

    `specific` adds codes or renames 1; 0, 1, 2, 130, and 143 are always there.
    """
    codes = {
        0: "success",
        1: "failure",
        USAGE: "bad usage",
        INTERRUPTED: "interrupted (SIGINT)",
        TERMINATED: "terminated (SIGTERM)",
        **specific,
    }
    reserved = [
        code for code in codes if code >= 124 and code not in (INTERRUPTED, TERMINATED)
    ]
    if reserved:
        raise ValueError(f"exit codes {reserved} are reserved for the shell and OS")
    return dict(sorted(codes.items()))


class Parser(argparse.ArgumentParser):
    """argparse without abbreviated options, whose help ends with the exit codes
    and whose usage errors print short usage and the help hint, then exit 2;
    run_script() makes them answer in JSON instead."""

    def __init__(
        self, *, exit_codes: Mapping[int, str], epilog: str = "", **kwargs: Any
    ) -> None:
        table = "\n".join(
            f"  {code:<4} {meaning}" for code, meaning in exit_codes.items()
        )
        kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
        super().__init__(
            epilog=f"{epilog}\n\nexit codes:\n{table}".lstrip("\n"),
            allow_abbrev=False,
            **kwargs,
        )
        self.exit_codes = dict(exit_codes)

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(USAGE, f"error: {message}\nrun '{self.prog} --help'\n")


def answer(code: int, fields: Mapping[str, Any]) -> int:
    """Print the one JSON line a script answers with, and return `code`.

    `ok` comes first and is true exactly when `code` is 0, whatever `fields`
    says. Success goes to stdout; a failure goes to stderr, after its
    diagnostics, and leaves stdout empty (docs/references/script-output.md).
    """
    body = {"ok": code == 0, **fields}
    body["ok"] = code == 0
    line = json.dumps(body, separators=(",", ":"))
    print(line, file=sys.stderr if code else sys.stdout)
    return code


def given(
    argv: Sequence[str], *flags: str, parser: argparse.ArgumentParser | None = None
) -> bool:
    """Whether one of `flags` comes before `--`, where options end; use it to let
    -h and --help win over every other argument.

    With `parser`, a bundle of its flag letters counts too, such as -vh for
    -v -h; a bundle holding an option that takes a value never does.
    """
    letters = {flag[1] for flag in flags if len(flag) == 2 and flag[1] != "-"}
    bundled = flag_letters(parser) if parser is not None and letters else set()
    for arg in argv:
        if arg == "--":
            return False
        if arg in flags:
            return True
        bundle = set(arg[1:]) if re.fullmatch(r"-[A-Za-z]{2,}", arg) else set()
        if bundle & letters and bundle <= bundled:
            return True
    return False


def flag_letters(parser: argparse.ArgumentParser) -> set[str]:
    """The one-letter options of `parser` and its commands that take no value."""
    letters: set[str] = set()
    parsers = [parser]
    while parsers:
        each = parsers.pop()
        for option, action in each._option_string_actions.items():
            if len(option) == 2 and option[1] != "-" and action.nargs == 0:
                letters.add(option[1])
        for action in each._actions:
            if isinstance(action, argparse._SubParsersAction):
                parsers.extend(action.choices.values())
    return letters


@contextmanager
def signals_interrupt() -> Iterator[None]:
    """Raise Interrupted(130) on SIGINT and Interrupted(143) on SIGTERM.

    The first signal ignores any repeat, so cleanup in `finally` blocks runs to
    the end. Handlers need the main thread; elsewhere this changes nothing.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    handled = (signal.SIGINT, signal.SIGTERM)
    previous = {number: signal.getsignal(number) for number in handled}
    fired = False

    def interrupt(number: int, _frame: object) -> None:
        nonlocal fired
        fired = True
        for each in handled:
            signal.signal(each, signal.SIG_IGN)
        raise Interrupted(128 + number)

    for number in handled:
        signal.signal(number, interrupt)
    try:
        yield
    finally:
        if not fired:
            for number, handler in previous.items():
                signal.signal(number, handler)


def env_flag(name: str) -> bool:
    """Whether an environment switch such as SYNC_FLEET_DEBUG is on: set, and not 0."""
    return os.environ.get(name, "") not in ("", "0")


def color_enabled(stream: TextIO, disabled: bool = False) -> bool:
    """Color only on a terminal, and never with --no-color, NO_COLOR, or TERM=dumb."""
    return (
        not disabled
        and not os.environ.get("NO_COLOR")
        and os.environ.get("TERM") != "dumb"
        and stream.isatty()
    )


DURATION = re.compile(r"(\d+(?:\.\d+)?)([smh]?)")


def duration(text: str) -> float:
    """Seconds from `30s`, `5m`, `2h`, or bare seconds; use it as an argparse type."""
    match = DURATION.fullmatch(text.strip())
    if match is None or float(match[1]) <= 0:
        raise argparse.ArgumentTypeError(
            f"invalid duration {text!r}; use a positive number of seconds, or 30s, 5m, 2h"
        )
    return float(match[1]) * {"": 1, "s": 1, "m": 60, "h": 3600}[match[2]]


def command_parsers(parser: argparse.ArgumentParser) -> list[argparse.ArgumentParser]:
    """The parser of every command below `parser`, at any depth."""
    found: list[argparse.ArgumentParser] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for command in dict.fromkeys(action.choices.values()):
                found += [command, *command_parsers(command)]
    return found


def named_command(
    parser: argparse.ArgumentParser, argv: Sequence[str]
) -> argparse.ArgumentParser:
    """The deepest command `argv` names, whose help -h asks for."""
    for arg in argv:
        if arg == "--":
            break
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction) and arg in action.choices:
                parser = action.choices[arg]
                break
    return parser


def usage_error_for(parser: argparse.ArgumentParser) -> Callable[[str], NoReturn]:
    """The error method of `parser`: a usage error whose help hint names it, so
    a command's mistake points to that command's help."""

    def error(message: str) -> NoReturn:
        raise UsageError(message, report={"help": f"{parser.prog} --help"})

    return error


def run_script(
    parser: Parser,
    work: Callable[[argparse.Namespace], Mapping[str, Any]],
    argv: Sequence[str] | None = None,
    *,
    debug: str | None = None,
) -> int:
    """Parse arguments, run `work`, and answer its outcome in one JSON line with
    its exit code, as docs/references/script-output.md describes.

    Every outcome answers, even a usage error, a bug, or an interrupt. `work`
    returns the data beside `ok`, usually {}, and raises ScriptError,
    UsageError, or TemporaryError for expected failures. `debug` names the
    script's <NAME>_DEBUG variable and adds --debug; without it the script never
    prints a traceback. Call it from `main()` and pass the result to `SystemExit`.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    # A command's parser takes -v and --debug too, after the command; SUPPRESS
    # keeps a flag given before it
    for each in (parser, *command_parsers(parser)):
        default = False if each is parser else argparse.SUPPRESS
        if "-v" not in each._option_string_actions:
            each.add_argument(
                "-v",
                "--verbose",
                action="store_true",
                default=default,
                help="print progress and step details on stderr",
            )
        if debug and "--debug" not in each._option_string_actions:
            each.add_argument(
                "--debug",
                action="store_true",
                default=default,
                help=f"print internals, timings, and tracebacks on stderr; also {debug}=1",
            )
        # Parser.error prints usage errors itself; raising sends each one
        # through answer_failure(). The root reports unknown arguments, which
        # belong to the command argv names
        named = named_command(parser, argv) if each is parser else each
        each.error = usage_error_for(named)  # pyright: ignore[reportAttributeAccessIssue]
    if given(argv, "-h", "--help", parser=parser):
        named_command(parser, argv).print_help()
        return 0

    command = shlex.join([*parser.prog.split(), *argv])
    tracing = False
    with signals_interrupt():
        try:
            args = parser.parse_args(argv)
            tracing = debug is not None and (args.debug or env_flag(debug))
            logging.basicConfig(
                format="%(message)s",
                level=logging.DEBUG
                if tracing
                else logging.INFO
                if args.verbose
                else logging.WARNING,
                stream=sys.stderr,
                force=True,
            )
            return answer(0, work(args))
        except KeyboardInterrupt as stop:
            code = getattr(stop, "code", INTERRUPTED)
            word = "interrupted" if code == INTERRUPTED else "terminated"
            return answer(code, {"errors": [word]})
        except ScriptError as error:
            return answer_failure(error, parser, command)
        except Exception as error:
            # The traceback comes first, so the answer ends stderr
            logging.getLogger(__name__).debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(f"{type(error).__name__}: {error}")
            return answer_failure(
                unexpected, parser, command, rerun=bool(debug) and not tracing
            )


def answer_failure(
    error: ScriptError, parser: Parser, command: str, rerun: bool = False
) -> int:
    """Answer a failure on stderr, after its detail, and return its exit code.
    Hints name the command to run next: help for a usage error, retry for a
    temporary failure, and rerun with --debug for a bug."""
    messages = [str(message) for message in error.args]
    hints: dict[str, str] = {}
    if isinstance(error, UsageError) and "help" not in error.report:
        hints["help"] = f"{parser.prog} --help"
    elif isinstance(error, TemporaryError) and messages:
        hints["retry"] = command
    elif rerun:
        hints["rerun"] = f"{command} --debug"
    if error.detail:
        print(error.detail, file=sys.stderr)
    return answer(error.code, {"errors": messages, **error.report, **hints})


# <<< cli-block

import bisect
import math
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from zoneinfo import ZoneInfo

import board
import facts
import github
import pipeline
import statuses
import t3

HERE = Path(__file__).resolve().parent
RECORDINGS = HERE / "tests" / "recordings"
POLL = 2.0  # seconds between two reads of PRAGMA data_version
GITHUB_CADENCE = 60.0  # seconds between two reads of a repository's open items
GITHUB_TIMEOUT = 20.0  # the live service's longest GitHub read
# The oldest GitHub facts the live service may hold: a merge right after one
# read waits for the next one, up to a poll late, and its timeout
LAG = GITHUB_CADENCE + GITHUB_TIMEOUT + 2 * POLL
SETTLE = 120.0  # oracle 2: a thread retitles only when it enters a phase or ends a turn
EPSILON = 0.001
MONTREAL = ZoneInfo("America/Montreal")
Points = list[tuple[float, str | None]]


def state_at(frames: list[list], t: float) -> dict[str, tuple]:
    """Every node's (state, step, note) at `t`, as the page's stateAt() reads its frames."""
    out: dict[str, tuple] = {}
    for f in frames:
        if f[0] > t:
            break
        out[f[1]] = (f[2], f[3], f[4])
    return out


@dataclass
class Run:
    """One recording, its final replay, and the facts the oracles read."""

    rec: dict
    snap: t3.Snapshot = field(init=False)
    events: list[dict] = field(init=False)
    final: dict = field(init=False)

    def __post_init__(self) -> None:
        self.head = self.rec["head"]
        self.id4 = self.rec["brigade"]
        self.snap = t3.fold(self.rec["records"])
        self.gh = github.Recorded(self.rec["github"])
        self.brigade = facts.Brigade(self.snap, self.gh, self.head)
        self.brigade.walk()
        self.threads = self.brigade.threads
        self.events = facts.extract(self.snap, self.gh, [self.head])
        self.end = max(statuses.ts(r[1]) for r in self.rec["records"] if r[1])
        self.final = self.page(None, self.end)

    def page(self, upto: int | None, now: float, lag: float | None = None) -> dict:
        known = None if lag is None else now - lag
        data = pipeline.recording_data(self.rec, upto=upto, now=now, known=known)
        return data["brigades"][0] if data["brigades"] else {}

    def deltas(self) -> list[dict]:
        _, deltas = statuses.replay(
            statuses.synthetic(self.events), {self.id4: self.head}
        )
        return deltas

    def slot(self, thread: str) -> str:
        return self.threads.get(thread, {}).get("slot") or thread


def sequences(rec: dict) -> list[tuple[int, float]]:
    """Each recorded sequence with its time, in order; a project record has none."""
    seen: dict[int, float] = {}
    for seq, at, *_ in rec["records"]:
        if seq and at:
            seen.setdefault(seq, statuses.ts(at))
    return sorted(seen.items())


def prefix_consistency(run: Run) -> dict:
    """Oracle 1, with oracle 5's recompute times measured on the way.

    The page as of sequence N holds from N's time until the next sequence
    arrives; every node it shows must match the final replay at each instant
    of that window, and the final replay may show no state but todo on a node
    the page lacks. Each page knows GitHub as the live service does at
    worst, LAG seconds late, and shows each fact github.DELAY after GitHub
    had it, so a fact the service learns late still shows on time.
    """
    seqs = sequences(run.rec)
    checked = status = detail = missing = 0
    examples: list[dict] = []
    recompute: list[float] = []
    final = run.final.get("frames", [])
    changes = sorted({f[0] for f in final})  # every instant the final replay moves
    for i, (seq, t_n) in enumerate(seqs):
        t_next = seqs[i + 1][1] if i + 1 < len(seqs) else run.end + EPSILON
        if t_next <= t_n:
            continue  # the next sequence shares this instant: no page showed this one alone
        now = t_next - EPSILON
        started = time.perf_counter()
        live = run.page(seq, now, LAG)
        recompute.append(time.perf_counter() - started)
        if not live:
            continue  # no Head Chef yet: nothing drawn
        frames = live["frames"]
        # each instant either page moves, so a change only one side shows is checked
        theirs_move = changes[
            bisect.bisect_right(changes, t_n) : bisect.bisect_left(changes, t_next)
        ]
        for t in sorted(
            {t_n, now, *theirs_move, *(f[0] for f in frames if t_n < f[0] < t_next)}
        ):
            mine, theirs = state_at(frames, t), state_at(final, t)
            for node in theirs.keys() - mine.keys():
                if (
                    theirs[node][0] != "todo"
                ):  # the final board lays out every slot as todo
                    missing += 1
                    examples.append({"seq": seq, "t": t, "node": node, "live": None})
            for node, value in mine.items():
                checked += 1
                other = theirs.get(node)
                if other is None or other[0] != value[0]:
                    status += 1
                    examples.append({"seq": seq, "t": t, "node": node, "live": value})
                elif other != value:
                    detail += 1
    return {
        "sequences": len(seqs),
        "checked": checked,
        "status": status,
        "detail": detail,
        "missing": missing,
        "examples": examples[:10],
        "recompute": recompute,
    }


def segments(points: Points, end: float) -> list[tuple[float, float, str | None]]:
    """Piecewise-constant segments [start, stop) from change points."""
    pts = sorted(points)
    stops = [t for t, _ in pts[1:]] + [end]
    return [(a, b, v) for (a, v), b in zip(pts, stops) if b > a]


def cause(
    titles: Points, mine: Points, at: float, title: str | None, status: str | None
) -> str:
    """Which side moved first before `at`, and whether the other caught up before moving on."""

    def catch_up(points: Points, other: Points, value: str | None) -> float | None:
        until = next((t for t, _ in other if t > at), math.inf)
        return next((t for t, v in points if at < t <= until and v == value), None)

    since_title = max(t for t, _ in titles if t <= at)
    since_replay = max(t for t, _ in mine if t <= at)
    if since_replay >= since_title:
        late = catch_up(titles, mine, status)
        return (
            f"title late {late - since_replay:.0f} s"
            if late
            else f"title never showed {status}"
        )
    late = catch_up(mine, titles, title)
    return (
        f"replay late {late - since_title:.0f} s"
        if late
        else f"replay never showed {title}"
    )


def title_agreement(run: Run, window: float = SETTLE) -> dict:
    """Oracle 2: time each thread's title status and replayed status agree, once both
    have held for `window` seconds."""
    model: dict[str, Points] = defaultdict(list)
    for d in run.deltas():
        if d["k"] == "status":
            model[d["th"]].append((d["t"], d["v"]))
    agree = disagree = 0.0
    cases: list[dict] = []
    for tid in run.threads:
        titles = [
            (statuses.ts(at), (title or {}).get("status"))
            for at, title in run.snap.titles(tid)
        ]
        mine = model.get(tid, [])
        if not titles or not mine:
            continue
        changes = sorted({t for t, _ in titles} | {t for t, _ in mine} | {run.end})
        for a, b in pairwise(changes):
            start = a + window
            if start >= b:
                continue
            title = next((v for t, v in reversed(titles) if t <= a), None)
            status = next((v for t, v in reversed(mine) if t <= a), None)
            if title is None or status is None:
                continue  # a title without a status emoji, or a thread before its first status
            if title == status:
                agree += b - start
                continue
            disagree += b - start
            cases.append(
                {
                    "thread": run.slot(tid),
                    "from": start,
                    "seconds": round(b - start),
                    "title": title,
                    "replay": status,
                    "cause": cause(titles, mine, a, title, status),
                }
            )
    total = agree + disagree
    return {
        "window": window,
        "rate": agree / total if total else 1.0,
        "seconds": round(total),
        "disagreements": cases,
    }


def recorded_threads(run: Run) -> dict[str, tuple[str, str]]:
    """Each thread of the run with its role and slot, from the launch calls T3
    recorded and the titles they gave, not from the extractor's walk."""
    found = {run.head: ("head_chef", "hc")}
    for tid in run.snap.threads:
        for item in run.snap.thread_items(tid):
            title, child = item.get("title") or {}, item.get("child")
            if item.get("tool") != "launch" or not child:
                continue
            b, c = title.get("b"), title.get("c")
            if title.get("role") == "cook" and b is not None and c is not None:
                found.setdefault(child, ("cook", f"cook-{b}.{c}"))
            elif title.get("role") == "chef" and b is not None:
                found.setdefault(child, ("chef", f"chef-{b}"))
    return found


def registries_and_merges(run: Run) -> dict:
    """Oracle 3: registered slots show queued until launched; a Cook shows shipped
    exactly once GitHub merged all its PRs; every slot a watch.toml on disk plans
    is registered in the transcript.

    Its facts come from the recording, not from the extractor: the threads
    each launch named, the watch.toml writes, launches and PR links T3
    recorded, and GitHub's merge times, which a page shows github.DELAY late. Each check reads the page at
    the tenth of a second it first shows a fact.
    """
    final = run.final.get("frames", [])
    registered: dict[str, float] = {}
    launched: dict[str, float] = {}
    linked: dict[str, float] = {}  # PR -> the first link, by any thread
    owner: dict[str, tuple[float, str]] = {}  # PR -> the first Cook that links it
    threads = recorded_threads(run)
    for tid, (role, slot) in threads.items():
        for item in run.snap.thread_items(tid):
            when = t3.later(item["start"], item.get("seen"))
            if when is None:
                continue  # an item with no time shows nowhere
            at = statuses.ts(when)
            w = item.get("watch")
            if w and role in ("head_chef", "chef"):
                prefix = "chef-" if role == "head_chef" else "cook-"
                for name in {*(w.get("full") or {}), *(w.get("blocks") or {})}:
                    if name.startswith(prefix):
                        registered[name] = min(at, registered.get(name, at))
            if item.get("tool") == "launch" and item.get("child") in threads:
                end = (
                    t3.later(item["end"], item.get("endSeen")) if item["end"] else None
                )
                child, t = threads[item["child"]][1], statuses.ts(end) if end else at
                launched[child] = min(t, launched.get(child, t))
            if item.get("tool") == "link":
                pr = github.key((item["pr"][0], int(item["pr"][1])))
                linked[pr] = min(at, linked.get(pr, at))
                if role == "cook":
                    first = (at, slot)
                    owner[pr] = min(first, owner.get(pr, first))
    checks, misses = 0, []

    def node_of(slot: str) -> str:
        return f"batch-{board.batch_of(slot)}" if slot.startswith("chef-") else slot

    def expect(t: float, node: str, ok: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            misses.append({"t": t, "node": node, "expected": what})

    for slot, t in registered.items():
        t = board.tenth(t)
        if slot not in launched or launched[slot] > t:
            state = state_at(final, t).get(node_of(slot))
            expect(
                t,
                node_of(slot),
                bool(state) and state[0] in ("todo", "stopped"),
                "queued",
            )
    for slot, t in launched.items():
        state = state_at(final, board.tenth(t)).get(node_of(slot))
        expect(t, node_of(slot), bool(state) and state[0] != "todo", "launched")
    # each Cook's PRs as GitHub has them: None while one is open, a closed one left out
    shown: dict[str, list[float | None]] = defaultdict(list)
    for pr, (_, slot) in owner.items():
        p = run.rec["github"]["prs"].get(pr)
        if p and p["merged"]:
            merged = statuses.ts(github.delayed(p["merged"]))
            shown[slot].append(max(merged, linked[pr]))
        elif p and not p["closed"]:
            shown[slot].append(None)
    for slot, times in shown.items():
        if None in times:
            continue
        shipped = max(t for t in times if t is not None)
        after = state_at(final, board.tenth(shipped)).get(slot)
        before = state_at(final, shipped - EPSILON).get(slot)
        expect(shipped, slot, bool(after) and after[2] == "shipped", "shipped")
        expect(shipped, slot, not before or before[2] != "shipped", "not shipped yet")
    for folder, info in (run.rec.get("disk") or {}).items():
        for slot in info["plan"]:
            if slot != "head-chef":
                expect(
                    run.end,
                    slot,
                    slot in registered,
                    f"registered, as {folder}/watch.toml plans",
                )
    return {"checks": checks, "misses": misses}


def answers(run: Run) -> dict:
    """Oracle 4: each answer Pascal gave a Head Chef titled ❓ came after red on the page.

    An answer is his reply in the Head Chef's thread, or a merge or close on
    GitHub of a PR or issue the Head Chef's asks name, while its title shows ❓.
    """
    final = run.final.get("frames", [])
    titles = [
        (statuses.ts(at), (t or {}).get("status"))
        for at, t in run.snap.titles(run.head)
    ]
    asking = [(a, b) for a, b, v in segments(titles, run.end + 1) if v == "❓"]
    main = run.brigade.main_repo()
    found: list[tuple[float, str]] = []
    refs: set[tuple[str, int]] = set()
    for item in run.snap.thread_items(run.head):
        if item["type"] == "user_message" and item["intent"] != "slash":
            found.append((statuses.ts(item["start"]), "reply"))
        elif item["type"] == "assistant_message":
            for ref in (x for r in item.get("refs") or [] for x in r):
                repo, n = ref.rsplit("#", 1)
                owner = repo or main
                if owner:
                    refs.add((owner, int(n)))
    for repo, n in sorted(refs):
        run.gh.item(repo, n)  # a recording that lacks the item fails here
        # his answer's own time, before the delay the page shows it with
        x = run.gh.items[(repo, n)] or {}
        when: str | None = x.get("merged") or x.get("closed")
        if when:
            found.append((statuses.ts(when), "github"))
    counts: Counter[str] = Counter()
    misses = []
    for t, how in sorted(found):
        if not any(a < t < b for a, b in asking):
            continue
        counts[how] += 1
        hc = state_at(final, t - EPSILON).get("hc")
        if not hc or hc[0] != "you":
            misses.append({"t": t, "how": how})
    return {"answers": dict(counts), "misses": misses}


def p95(values: Iterable[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def freshness(recompute: list[float]) -> dict:
    """Oracle 5 for T3: the p95 of a from-scratch recompute, plus the worst-case poll wait."""
    return {"recompute": p95(recompute), "p95": p95(recompute) + POLL}


def coverage(run: Run) -> dict:
    """Oracle 6: messages whose leading symbol no rule reads, and unread watch.toml writes."""
    found = pipeline.unparsed(run.events)
    return {"unclassified": found["messages"], "unread": found["watch"]}


def report(rec: dict) -> dict:
    """Every oracle's numbers for one recording."""
    run = Run(rec)
    prefix = prefix_consistency(run)
    return {
        "run": run.id4,
        "main": run.brigade.main_repo(),
        "prefix": {k: v for k, v in prefix.items() if k != "recompute"},
        "titles": title_agreement(run),
        "registries": registries_and_merges(run),
        "answers": answers(run),
        "freshness": freshness(prefix["recompute"]),
        "coverage": coverage(run),
    }


def tracked(rec: dict, repo: str) -> tuple[list[int], list[int]]:
    """The PR and issue numbers a recording tracks in one of its repositories."""

    def numbers(part: str) -> list[int]:
        found = (k.rsplit("#", 1) for k, v in rec["github"].get(part, {}).items() if v)
        return sorted(int(n) for name, n in found if name == repo)

    return numbers("prs"), numbers("issues")


def github_query(
    gh: github.GitHub, repo: str, prs: list[int], issues: list[int], rounds: int
) -> float:
    """Oracle 5 for GitHub: p95 seconds of one query that reads every tracked PR
    and issue of `repo`, the worst case of the live service's per-repository read."""
    body = " ".join(
        [f"p{n}: pullRequest(number:{n}){{{github.PR_FIELDS}}}" for n in prs]
        + [f"i{n}: issue(number:{n}){{{github.ISSUE_FIELDS}}}" for n in issues]
    )
    times = []
    for _ in range(rounds):
        started = time.perf_counter()
        gh.repo_query(repo, body, missing_ok=True)
        times.append(time.perf_counter() - started)
    return p95(times)


def rows(r: dict) -> list[dict]:
    """The PR table's rows for one report: run, oracle, number, threshold, pass."""
    p, ti, rg, an, fr, cv = (
        r[k]
        for k in ("prefix", "titles", "registries", "answers", "freshness", "coverage")
    )
    out = [
        (
            1,
            "prefix consistency",
            f"{p['status']} status and {p['detail']} detail mismatches in {p['checked']} checks over {p['sequences']} sequences; {p['missing']} final-only states",
            "0, 0 and 0",
            p["status"] == 0 and p["detail"] == 0 and p["missing"] == 0,
        ),
        (
            2,
            "titles",
            f"{ti['rate']:.4f} of {ti['seconds']} s agree after a {ti['window']:.0f} s settle window; {len(ti['disagreements'])} disagreements",
            "≥ 0.99",
            ti["rate"] >= 0.99,
        ),
        (
            3,
            "registries and merges",
            f"{len(rg['misses'])} misses in {rg['checks']} checks",
            "0",
            not rg["misses"],
        ),
        (
            4,
            "answers after red",
            f"{len(an['misses'])} misses in {sum(an['answers'].values())} answers ({', '.join(f'{v} {k}' for k, v in sorted(an['answers'].items())) or 'none'})",
            "0",
            not an["misses"],
        ),
        (
            5,
            "freshness, T3",
            f"p95 {fr['p95']:.3f} s: recompute {fr['recompute']:.3f} s + {POLL:.0f} s poll",
            "< 5 s",
            fr["p95"] < 5,
        ),
    ]
    if "github" in r:
        g = r["github"]
        out.append(
            (
                5,
                "freshness, GitHub",
                f"{github.DELAY + POLL:.1f} s: shown {github.DELAY:.0f} s after GitHub + {POLL:.0f} s poll; the service lags at most {LAG:.0f} s, with a p95 query of {g['p95']:.2f} s for {g['prs']} PRs and {g['issues']} issues",
                "< 90 s",
                github.DELAY + POLL < 90
                and LAG < github.DELAY
                and g["p95"] < GITHUB_TIMEOUT,
            )
        )
    out.append(
        (
            6,
            "parser coverage",
            f"{len(cv['unclassified'])} unclassified messages, {len(cv['unread'])} unread watch.toml writes",
            "0 and 0",
            not cv["unclassified"] and not cv["unread"],
        )
    )
    return [
        {
            "run": r["run"],
            "oracle": n,
            "name": name,
            "number": number,
            "threshold": threshold,
            "pass": ok,
        }
        for n, name, number, threshold, ok in out
    ]


def montreal(t: float) -> str:
    return datetime.fromtimestamp(t, MONTREAL).strftime("%Y-%m-%d %H:%M:%S")


def markdown(reports: list[dict]) -> str:
    """The PR description's table, then oracle 2's disagreements with their causes."""
    lines = ["| Run | Oracle | Number | Threshold | Result |", "|---|---|---|---|---|"]
    for r in reports:
        for row in rows(r):
            lines.append(
                f"| {row['run']} | {row['oracle']} {row['name']} | {row['number']} | {row['threshold']} | {'pass' if row['pass'] else 'fail'} |"
            )
    lines += [
        "",
        f"Oracle 2 disagreements after the {SETTLE:.0f} s settle window, times in America/Montreal:",
        "",
        "| Run | Thread | From | Seconds | Title | Replay | Cause |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in reports:
        for c in r["titles"]["disagreements"]:
            lines.append(
                f"| {r['run']} | {c['thread']} | {montreal(c['from'])} | {c['seconds']} | {c['title']} | {c['replay']} | {c['cause']} |"
            )
    return "\n".join(lines) + "\n"


def work(args: argparse.Namespace) -> dict:
    paths = [Path(p).expanduser() for p in args.recording] or sorted(
        RECORDINGS.glob("*.json.gz")
    )
    names = dict(args.repo)
    reports = []
    gh = github.GitHub(github.gh_reader(args.timeout)) if args.github else None
    for path in paths:
        try:
            rec = t3.load_recording(path)
        except (OSError, ValueError) as error:
            raise UsageError(f"cannot read recording {path}: {error}") from error
        logging.getLogger(__name__).info("Checking %s", path.name)
        r = report(rec)
        if gh:
            main = r["main"]
            real = names.get(r["run"]) or (
                None if main.startswith("private-") else main
            )
            if not real:
                raise UsageError(
                    f"name the private repository of run {r['run']}: --repo {r['run']}=OWNER/NAME"
                )
            prs, issues = tracked(rec, main)
            try:
                r["github"] = {
                    "p95": github_query(gh, real, prs, issues, args.rounds),
                    "prs": len(prs),
                    "issues": len(issues),
                }
            except github.ReadError as error:
                cls = TemporaryError if error.temporary else ScriptError
                raise cls(f"GitHub read failed for {real}: {error}") from error
        reports.append(r)
    table = [row for r in reports for row in rows(r)]
    changes = []
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown(reports), encoding="utf-8")
        changes.append(["write", str(out)])
    failed = [
        f"{row['run']} oracle {row['oracle']} {row['name']}: {row['number']}; needs {row['threshold']}"
        for row in table
        if not row["pass"]
    ]
    if failed:
        raise ScriptError(*failed, report={"rows": table, "changes": changes})
    return {"rows": table, "changes": changes}


def repo_name(value: str) -> tuple[str, str]:
    run, sep, repo = value.partition("=")
    if not sep or not re.fullmatch(r"[0-9a-z]{4}", run) or repo.count("/") != 1:
        raise argparse.ArgumentTypeError(
            "--repo needs ID4=OWNER/NAME, such as 66ab=example/widget"
        )
    return run, repo


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        prog="oracles.py",
        description=__doc__,
        exit_codes=exit_codes({75: "temporary GitHub read failure, safe to retry"}),
        epilog="""Each recording is checked by six oracles, each against facts the replay's rules
do not produce:
  1. prefix consistency: the page as of each sequence N matches the final replay
     at every instant until N+1
  2. titles: carpaccio's own titles agree with the replay's statuses once both
     held for the settle window; each disagreement names its cause
  3. registries and merges: registered slots show queued until launched, a Cook
     shows shipped once GitHub merged all its PRs, watch.toml plans are registered
  4. answers after red: each answer to a Head Chef titled ❓ came after red
  5. freshness: from-scratch recompute p95 plus the 2 s poll; with --github, the
     85 s GitHub delay plus the poll, once the 60 s cadence, a 20 s timeout and
     the p95 of one live query per repository fit in the delay
  6. parser coverage: messages no rule reads, watch.toml writes left unread
A row that misses its threshold fails the command.

examples:
  uv run scripts/replay/oracles.py
  uv run scripts/replay/oracles.py -o oracles.md
  uv run scripts/replay/oracles.py --github --repo 66ab=example/widget scripts/replay/tests/recordings/66ab.json.gz""",
    )
    parser.add_argument(
        "recording",
        nargs="*",
        help="recording files (default: every recording in scripts/replay/tests/recordings)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write the Markdown table and oracle 2's disagreements to this file",
    )
    parser.add_argument(
        "--github",
        action="store_true",
        help="also time oracle 5's GitHub query, read live with gh",
    )
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        type=repo_name,
        metavar="ID4=OWNER/NAME",
        help="the real repository of a run whose main repository the recording names private-A",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=20,
        help="GitHub queries per repository (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=30.0,
        help="timeout per GitHub read (default: 30s)",
    )
    return run_script(parser, work, argv, debug="ORACLES_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

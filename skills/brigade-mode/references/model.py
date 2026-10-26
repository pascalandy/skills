#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Brigade carpaccio title statuses as math.

A status is computed, never chosen: status(thread) = f(its own facts, the SET
of its children's kinds). Each f only asks "does some child have kind k" or
"are all children in K", so the set of kinds present decides the status,
whatever the number of children. Enumerating every subset is exhaustive for
these modeled rules. Counters count slots, including repeated phases. A
replaced thread is archived and leaves the tree, so it is not a kind.

`just check --only brigade-carpaccio` runs it; run `model.py --help` for its flags.
"""

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

from itertools import combinations, product

EPILOG = """\
Enumerates every Chef and Head Chef case the rules admit, computes each status
and checks it against the properties. Answers {"ok":true} on stdout when every
property and counter holds and every Chef status is reachable. Otherwise stdout
stays empty and the last line of stderr names each broken property under
"errors". --verbose prints the case counts, up to 20 broken cases and the
parent-child grids on stderr.

examples:
  uv run authoring/andy/brigade-mode/references/model.py
  uv run authoring/andy/brigade-mode/references/model.py --verbose
  just check --only brigade-carpaccio"""

EXIT_CODES = exit_codes(
    {0: "every property holds", 1: "a property, a counter or a status broke"}
)

log = logging.getLogger("model")

# ---------------------------------------------------------------- Cook ---
# A Cook's status is its phase. A Cook whose cards the PM cut leaves its Chef's count.
COOK = {
    "build": "🍳",  # implements, barrages, docs, fixes
    "ask": "⏸️",  # waits on its Chef's answer
    "served": "🍽️",  # stack handed up, retro not done
    "close": "🧹",  # retro or cleanup
    "done": "🍽️",  # stack merged, retro done, T3 settlement confirmed: final
    "stopped": "⏹️",  # the whole batch stopped: final
    "cut_close": "🧹",  # its cards were cut, cleaning up; out of the count
    "cut_stopped": "⏹️",
    "queued": None,  # slot assigned, no thread running yet: not launched, or being relaunched
    # never launched; starts once the served stacks it names, in its batch, merged and deployed
    "queued_after_merge": None,
}
COOK_FINAL = {"done", "stopped", "cut_stopped"}
COOK_IN = {
    "build",
    "ask",
    "served",
    "close",
    "done",
    "stopped",
    "queued",
    "queued_after_merge",
}

# The after-merge exception (#785): a slot that waits for the merge of served
# stacks stays counted but does not hold that merge back. It never names another
# waiting slot; the Plan sends such a chain to a later batch.
AFTER_MERGE = {"queued_after_merge"}

# ---------------------------------------------------------------- Chef ---
# merged: every stack in scope merged; for a batch without PRs, its own work done.
# released: the release done, not required, or cut by the PM.
# checks, merge: passed or said for the frozen heads; true for a batch without PRs.
# partial: a merge round merged and deployed the stacks waiting slots named and
# spent its approval; other stacks of the batch have not merged.
CHEF_FACTS = (
    "question",
    "checks",
    "merge",
    "merged",
    "released",
    "closed",
    "stopped",
    "partial",
)


def ready(f, kinds):
    """Every counted slot served, merged in an earlier round or waits for this merge.

    Only the first round has slots that wait: after it, each is a launch to make.
    """
    inscope = kinds & COOK_IN
    waits = set() if f["partial"] else AFTER_MERGE
    return "served" in inscope and inscope <= {"served", "done"} | waits


def chef_status(f, kinds):
    """First line that applies wins."""
    if f["question"]:
        return "⏸️"  # waits on the Head Chef
    if kinds & {"build", "ask"}:
        return "⏳"  # a Cook builds or asks
    if f["stopped"] or (f["merged"] and f["released"]):
        if not kinds <= COOK_FINAL or not f["closed"]:
            return "🧹"  # retros and cleanup
        return "⛳" if f["merged"] and f["released"] else "⏹️"
    if f["merge"]:
        return "🔀"  # merges, then releases
    if ready(f, kinds) and f["checks"]:
        return "🍽️"  # batch ready, x/x but for slots waiting for this merge
    return "⏳"  # validates or works alone


def chef_coherent(f, kinds):
    inscope = kinds & COOK_IN
    rules = [
        not f["released"] or f["merged"],
        not f["merged"] or f["merge"],
        not f["merge"] or f["checks"],
        not f["closed"] or f["stopped"] or (f["merged"] and f["released"]),
        not f["closed"] or not f["question"],
        # retro comes after the release, after a stop, or after the merge round of its stack
        not (inscope & {"close", "done"})
        or f["stopped"]
        or (f["merged"] and f["released"])
        or f["partial"],
        # an in-scope Cook ends stopped only when the whole batch stops
        "stopped" not in inscope or f["stopped"],
        # a Cook whose stack merged ends 🍽️, even after a Stop
        "stopped" not in inscope or not (f["merged"] and f["released"]),
        # merging needs every Cook served at the time, but for slots waiting for this
        # merge, which need a stack to wait for; a fix sends one back to build
        not f["merge"]
        or f["merged"]
        or f["partial"]
        or (
            inscope <= {"served", "build", "ask"} | AFTER_MERGE
            and inscope - AFTER_MERGE
        ),
        # a round spends its approval: the next round needs one for its own heads,
        # given once every Cook left has served
        not (f["partial"] and f["merge"]) or ready(f, kinds),
        # rounds end when every stack merged; a slot still waiting has no merged stack
        not f["merged"] or not (f["partial"] or "queued_after_merge" in kinds),
        # no counted Cook, no merge to run (batch without PRs works alone)
        inscope or not f["merge"] or f["merged"],
        # a Stop turns unlaunched slots into stopped ones; nothing merges with a slot
        # unlaunched, but for slots waiting for this merge
        not (kinds & {"queued", "queued_after_merge"}) or not f["stopped"],
        "queued" not in kinds or not f["merge"],
    ]
    return all(rules)


def counter(phases):
    inscope = [phase for phase in phases if phase in COOK_IN]
    x = sum(phase in {"served", "done"} for phase in inscope)
    return x, len(inscope)


def batch_counter(phases):
    inscope = [phase for phase in phases if phase != "⏹️cut"]
    return sum(phase == "⛳" for phase in inscope), len(inscope)


def chef_properties(f, kinds, s):
    x, y = counter(kinds)
    broken = []
    if s in {"⛳", "⏹️"} and not kinds <= COOK_FINAL:
        broken.append("C1 final over a live Cook")
    if s == "⛳" and x != y:
        broken.append("C2 x/x needed")
    # only a slot waiting for this merge, before any round merged, stays unserved
    waiting = set() if f["partial"] else {"queued_after_merge"}
    if s in {"🍽️", "🔀"} and (kinds & COOK_IN) - {"served", "done"} - waiting:
        broken.append(
            "C7 ready or merges past a slot that does not wait for this merge"
        )
    if s in {"🍽️", "🔀"} and not f["merged"] and "served" not in kinds:
        broken.append("C8 ready or merges with no served stack")
    if s in {"🔀", "🧹"} and kinds & {"build", "ask"}:
        broken.append("C3 merges or closes while a Cook builds or asks")
    if "ask" in kinds and s not in {"⏳", "⏸️"}:
        broken.append("C4 a Cook's question has no owner")
    if s == "⛳" and not (f["merged"] and f["released"]):
        broken.append("C5 delivered without delivery")
    if s == "⏹️" and not (f["stopped"] and not (f["merged"] and f["released"])):
        broken.append("C6 stopped without a stop, or over a delivered batch")
    return broken


# ----------------------------------------------------------- Head Chef ---
# A Chef as the Head Chef sees it: its status, plus who owns its wait.
CHEF_KINDS = {
    "⏳": "⏳",
    "🔀": "🔀",
    "🧹": "🧹",
    "🍽️review": "🍽️",  # batch ready, waits on the PM's review
    "🍽️answer": "🍽️",  # batch ready, the Head Chef answers from the requirements or specs
    "🍽️held": "🍽️",  # the PM holds it
    "⏸️answer": "⏸️",  # question the Head Chef answers itself
    "⏸️escalated": "⏸️",  # question that needs the PM
    "⛳": "⛳",
    "⏹️cut": "⏹️",  # the PM cut the whole batch
    "⏹️stop": "⏹️",  # the PM said Stop
    "queued": None,  # batch registered, Chef not launched yet
}
CHEF_FINAL = {"⛳", "⏹️cut", "⏹️stop"}
# pm_item: an open PM item of the Head Chef's own: Align or added work, a scope cut,
# a reserved action, a fact only the PM knows, a fault it cannot repair (items 1, 3 to 6 and 8).
HC_FACTS = ("pm_item", "own", "stop")


def hc_items(h, kinds):
    progress = bool(kinds & {"⏳", "🔀", "🧹", "⏸️answer", "🍽️answer"}) or h["own"]
    items = set()
    if h["pm_item"]:
        items.add("own item")
    if "🍽️review" in kinds:
        items.add("review")
    if "⏸️escalated" in kinds:
        items.add("question")
    if "🍽️held" in kinds and not progress:
        items.add("hold")  # D3 a: once nothing else progresses
    return items


def hc_status(h, kinds):
    """First line that applies wins."""
    if hc_items(h, kinds):
        return "❓"  # the PM owes an answer
    if h["own"] or kinds & {"⏸️answer", "🍽️answer"}:
        return "🟢"  # works, or answers a Chef
    if not kinds <= CHEF_FINAL:
        return "⏳"  # a Chef is not final
    # D2 b: a cut batch leaves the count, so the rest can end ⛳ x/x
    return "⛳" if "⛳" in kinds and not h["stop"] else "⏹️"


def hc_coherent(h, kinds):
    rules = [
        "⏹️stop" not in kinds or h["stop"],
        kinds or h["stop"] or h["own"] or h["pm_item"],
        # a Stop records queued batches as stopped; at rest a queued batch waits on a live one or the Head Chef
        "queued" not in kinds or not h["stop"],
        "queued" not in kinds
        or h["own"]
        or h["pm_item"]
        or bool(kinds - {"queued"} - CHEF_FINAL),
    ]
    return all(rules)


def hc_properties(h, kinds, s):
    broken = []
    items = hc_items(h, kinds)
    if s in {"⛳", "⏹️"} and not kinds <= CHEF_FINAL:
        broken.append("H1 final over a live Chef")
    if s == "⛳" and (h["stop"] or "⏹️stop" in kinds or "⛳" not in kinds):
        broken.append("H2 delivered after a Stop or with nothing delivered")
    if (s == "❓") != bool(items):
        broken.append("H3 ❓ without a PM item, or a PM item without ❓")
    if kinds & {"⏸️answer", "🍽️answer", "⏸️escalated"} and s not in {"🟢", "❓"}:
        broken.append("H4 a Chef's question has no owner")
    if "🍽️review" in kinds and s != "❓":
        broken.append("H5 a ready batch does not reach the PM")
    if s == "⏳" and not kinds & {"⏳", "🔀", "🧹", "🍽️held"}:
        broken.append("H6 monitors nothing")
    return broken


# ------------------------------------------------------------- checking ---
def subsets(universe):
    u = sorted(universe)
    for r in range(len(u) + 1):
        yield from (set(c) for c in combinations(u, r))


def check():
    report = {
        "chef_cases": 0,
        "hc_cases": 0,
        "broken": [],
        "chef_cook": set(),
        "hc_chef": set(),
    }
    chef_seen = set()
    for vals in product((False, True), repeat=len(CHEF_FACTS)):
        f = dict(zip(CHEF_FACTS, vals))
        for kinds in subsets(COOK):
            if not chef_coherent(f, kinds):
                continue
            report["chef_cases"] += 1
            s = chef_status(f, kinds)
            chef_seen.add(s)
            for b in chef_properties(f, kinds, s):
                report["broken"].append(("Chef", b, f, sorted(kinds), s))
            for k in kinds:
                if COOK[k]:  # a queued slot has no row
                    report["chef_cook"].add((s, COOK[k]))
    for vals in product((False, True), repeat=len(HC_FACTS)):
        h = dict(zip(HC_FACTS, vals))
        for kinds in subsets(CHEF_KINDS):
            if not hc_coherent(h, kinds):
                continue
            report["hc_cases"] += 1
            s = hc_status(h, kinds)
            for b in hc_properties(h, kinds, s):
                report["broken"].append(("Head Chef", b, h, sorted(kinds), s))
            for k in kinds:
                if CHEF_KINDS[k]:
                    report["hc_chef"].add((s, CHEF_KINDS[k]))
    missing = {CHEF_KINDS[k] for k in CHEF_KINDS if CHEF_KINDS[k]} - chef_seen
    return report, missing


def counter_errors():
    cases = [
        (counter(["served", "served", "build"]), (2, 3)),
        (counter(["served", "cut_stopped"]), (1, 1)),
        (counter(["served", "queued_after_merge"]), (1, 2)),
        (batch_counter(["⛳", "⛳", "⏹️cut", "🔀"]), (2, 3)),
    ]
    return [(actual, expected) for actual, expected in cases if actual != expected]


# The acceptance cases of #785 by name: the true Chef facts, one phase per Cook
# slot, then the Chef status, or None when the rules refuse the state.
SCENARIOS = [
    (
        "a served stack merges before the slot that waits for it",
        {"checks", "merge"},
        ["served", "queued_after_merge"],
        "🔀",
    ),
    (
        "a batch is ready below x/x only by slots that wait for its merge",
        {"checks"},
        ["served", "queued_after_merge"],
        "🍽️",
    ),
    (
        "waiting slots alone have no stack to merge",
        {"checks", "merge"},
        ["queued_after_merge"],
        None,
    ),
    (
        "waiting slots alone are not a ready batch",
        {"checks"},
        ["queued_after_merge"],
        "⏳",
    ),
    (
        "an ordinary queued slot refuses the merge",
        {"checks", "merge"},
        ["served", "queued"],
        None,
    ),
    ("an ordinary queued slot holds readiness", {"checks"}, ["served", "queued"], "⏳"),
    ("a building slot holds the merge", {"checks", "merge"}, ["served", "build"], "⏳"),
    ("an asking slot holds the merge", {"checks", "merge"}, ["served", "ask"], "⏳"),
    (
        "two served stacks merge in one round before their waiting slots",
        {"checks", "merge"},
        ["served", "served", "queued_after_merge", "queued_after_merge"],
        "🔀",
    ),
    (
        "after the round, a waiting slot is a launch to make",
        {"partial"},
        ["done", "queued_after_merge"],
        "⏳",
    ),
    (
        "after the round, the merged Cook is done and the launched slot builds",
        {"partial"},
        ["done", "build"],
        "⏳",
    ),
    (
        "both launched slots build after the round",
        {"partial"},
        ["done", "done", "build", "build"],
        "⏳",
    ),
    (
        "the launched slot serves at new heads",
        {"partial", "checks"},
        ["done", "served"],
        "🍽️",
    ),
    (
        "the first round's approval never covers the launched slot",
        {"partial", "checks", "merge"},
        ["done", "build"],
        None,
    ),
    (
        "the second round merges on an approval of its own heads",
        {"partial", "checks", "merge"},
        ["done", "served"],
        "🔀",
    ),
    (
        "a slot waiting on a launched slot is a chain and holds the merge",
        {"partial", "checks", "merge"},
        ["done", "served", "queued_after_merge"],
        None,
    ),
    (
        "every stack merged leaves no slot waiting",
        {"checks", "merge", "merged", "released", "closed"},
        ["done", "queued_after_merge"],
        None,
    ),
    (
        "delivered once the second round merged and deployed",
        {"checks", "merge", "merged", "released", "closed"},
        ["done", "done"],
        "⛳",
    ),
]


def scenario_errors():
    errors = []
    for name, true, phases, expected in SCENARIOS:
        f = {fact: fact in true for fact in CHEF_FACTS}
        kinds = set(phases)
        actual = chef_status(f, kinds) if chef_coherent(f, kinds) else None
        if actual != expected:
            errors.append((name, actual, expected))
    return errors


HC_ROWS, CHEF_COLS = (
    ["🟢", "⏳", "❓", "⛳", "⏹️"],
    ["⏳", "🔀", "🧹", "🍽️", "⏸️", "⛳", "⏹️"],
)
COOK_COLS = ["🍳", "🧹", "🍽️", "⏸️", "⏹️"]


def grid(rows, cols, pairs):
    out = ["| | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for r in rows:
        out.append(
            f"| {r} | "
            + " | ".join("✅" if (r, c) in pairs else "❌" for c in cols)
            + " |"
        )
    return "\n".join(out)


def case(facts, kinds, status):
    true = ", ".join(name for name, value in facts.items() if value) or "none"
    return f"facts {true}, child kinds {', '.join(kinds) or 'none'}, status {status}"


def problems(report, missing, count_errors, cases):
    """One message per broken property, unreachable status set, counter and case."""
    groups = {}
    for role, prop, facts, kinds, status in report["broken"]:
        groups.setdefault((role, prop), []).append(case(facts, kinds, status))
    errors = [
        f"{role} {prop}: {len(cases)} case{'s' * (len(cases) != 1)}, such as {cases[0]}"
        for (role, prop), cases in groups.items()
    ]
    if missing:
        errors.append(f"no Chef case reaches {', '.join(sorted(missing))}")
    errors += [
        f"counter gave {actual}, expected {expected}"
        for actual, expected in count_errors
    ]
    errors += [
        f"case {name!r} gave {actual or 'refused'}, expected {expected or 'refused'}"
        for name, actual, expected in cases
    ]
    return errors


def verify(_args: argparse.Namespace) -> dict[str, Any]:
    report, missing = check()
    count_errors = counter_errors()
    log.info(
        "Chef cases: %d, Head Chef cases: %d", report["chef_cases"], report["hc_cases"]
    )
    for role, prop, facts, kinds, status in report["broken"][:20]:
        log.info("broken: %s %s: %s", role, prop, case(facts, kinds, status))
    log.info("\nChef x Cook\n%s", grid(CHEF_COLS, COOK_COLS, report["chef_cook"]))
    log.info("\nHead Chef x Chef\n%s", grid(HC_ROWS, CHEF_COLS, report["hc_chef"]))
    errors = problems(report, missing, count_errors, scenario_errors())
    if errors:
        raise ScriptError(*errors)
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        prog="model.py",
        description="Check carpaccio's title statuses as math.",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    return run_script(parser, verify, argv)


if __name__ == "__main__":
    raise SystemExit(main())

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check the dependency graph of a wave file and write it as one JSON file.

Each brief of the wave file has one fenced `json` block, as
references/wave-file.md defines. The script reads those blocks and fails when:
a brief has no valid block, an ID is unknown or dropped, the graph has a cycle,
or two tasks that can run at the same time have a common path in `touches`.

It also checks the `Executor` of the wave, its epics and its tasks: a value
the wave or an epic declares must agree with its tasks, a brief never says
`tbd`, and an open human task never waits for an unfinished agent or QA task of
the same wave. A wave file with `skill_version` 3.0.0 or later must give each
of these `Executor` values.

It writes the graph beside the wave file, as `<wave file name>.graph.json`:
`nodes` (each block with its kind and state), `edges` (blocker, blocked and
why), `batches` (the IDs that can run at the same time, in execution order) and
`gates` (for each blocking QA task, the tasks that it blocks).

Answers in one JSON line: {"ok":true,"file":"...","longest_chain":4,"widths":[2,1,1,1],
"changes":[["write","..."]]}. `longest_chain` counts the batches and `widths` gives the IDs of each
batch. `changes` is absent when the file is already up to date.

With --hitl, it reads every wave file of a waves folder, writes nothing, fails
on an invalid or missing `Executor`, and answers `waves`: for each wave its `executor`, its `unresolved` items (human
tasks that are not done or dropped, and each `tbd`) and `agent_ready`.
"""

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

from pathlib import Path

EPILOG = """\
examples:
  uv run scripts/plan_graph.py plan/waves/W02-user-onboarding.md
  uv run scripts/plan_graph.py --check plan/waves/W02-user-onboarding.md
  uv run scripts/plan_graph.py --dry-run plan/waves/W02-user-onboarding.md
  uv run scripts/plan_graph.py --hitl plan/waves"""

EXIT_CODES = exit_codes(
    {1: "a brief or the graph has an error, or --check found a stale graph file"}
)

log = logging.getLogger("plan_graph")

HEADING = re.compile(r"^#{1,6} ")
BRIEF = re.compile(r"^#### (?P<id>E\d+-(?P<kind>T|QA)\d+): ")
STATE = re.compile(r"^- Kind:.*\bState: (?P<state>\S+)")
TASK_KEYS = {"id", "blocked_by", "needs", "touches"}
QA_KEYS = {"id", "verifies", "needs"}
WILDCARD = re.compile(r"[*?]")
STATES = re.compile(r"todo|done|dropped|carried→W\d+[A-Z]?")
EXECUTOR = re.compile(r"\bExecutor: (?P<executor>[^·]*?)\s*(?:·|$)")
EPIC = re.compile(r"^### (?P<id>E\d+)(?P<continued> \(continued from [^)]*\))?[: ]")
EPIC_EXECUTOR = re.compile(r"^- Executor: (?P<executor>.*?)\s*$")
EXECUTORS = {"agent", "human", "tbd"}
FINISHED = {"done", "dropped"}


def briefs_in(text: str) -> tuple[dict[str, dict[str, Any]], list[int]]:
    """Each brief of a wave file by ID: its line, kind, state and raw json block.
    Then the lines of the level-4 headings that are not a brief heading, and
    of a json fence that never closes."""
    briefs: dict[str, dict[str, Any]] = {}
    malformed: list[int] = []
    current: dict[str, Any] | None = None
    block: list[str] | None = None
    opened = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if block is not None:
            if line.strip() == "```":
                if current is not None:
                    current["blocks"].append("\n".join(block))
                block = None
            else:
                block.append(line)
            continue
        if line.strip() == "```json":
            block = []
            opened = number
        elif (
            current is not None
            and current["blocks"]
            and line.strip()
            and not HEADING.match(line)
        ):
            current.setdefault("after", number)
        elif HEADING.match(line):
            found = BRIEF.match(line)
            current = None
            if line.startswith("#### ") and not found:
                malformed.append(number)
            if found:
                current = {
                    "line": number,
                    "qa": found["kind"] == "QA",
                    "state": "todo",
                    "blocks": [],
                    "duplicate": found["id"] in briefs,
                }
                briefs[found["id"]] = current
        elif current is not None and (state := STATE.match(line)):
            current["state"] = state["state"]
            if executor := EXECUTOR.search(line):
                current["executor"] = executor["executor"]
    if block is not None:
        malformed.append(opened)
    return briefs, malformed


def front_matter(text: str) -> dict[str, str]:
    """The `key: value` lines of the front matter, without comments or quotes."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    found: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, colon, value = line.partition(":")
        if colon:
            found[key.strip()] = value.split("#")[0].strip().strip("\"'")
    return found


def epics_in(text: str) -> dict[str, dict[str, Any]]:
    """Each epic heading of a wave file by ID: its line, whether it continues
    an epic of an earlier wave, and the `Executor` line of its entry."""
    epics: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        if HEADING.match(line):
            found = EPIC.match(line)
            current = None
            if found:
                current = {"line": number, "continued": bool(found["continued"])}
                epics.setdefault(found["id"], current)
        elif current is not None and (executor := EPIC_EXECUTOR.match(line)):
            current["executor"] = executor["executor"]
    return epics


def version_of(text: str) -> tuple[int, ...]:
    """The `skill_version` of a wave file as numbers; (0,) when it has none."""
    numbers = re.findall(r"\d+", front_matter(text).get("skill_version", ""))
    return tuple(int(number) for number in numbers) or (0,)


def epic_of(brief_id: str) -> str:
    return brief_id.split("-")[0]


def declaration_errors(
    wave_file: Path, text: str, briefs: Mapping[str, dict[str, Any]]
) -> list[str]:
    """What is wrong with each `Executor` value of the wave, its epics and its
    tasks. An explicit value always counts; only a file of version 3.0.0 or
    later must give each one."""
    errors: list[str] = []
    front = front_matter(text)
    epics = epics_in(text)
    required = version_of(text) >= (3,)
    wave = front.get("executor")
    if wave is None and required:
        errors.append(
            f"{wave_file}:1: the front matter has no `executor`; "
            "add `executor: agent`, `human` or `tbd`"
        )
    elif wave is not None and wave not in EXECUTORS:
        errors.append(
            f"{wave_file}:1: `executor` is {wave!r}; write agent, human or tbd"
        )
    for epic_id, epic in epics.items():
        where = f"{wave_file}:{epic['line']}: {epic_id}"
        value = epic.get("executor")
        if value is None and required and not epic["continued"]:
            errors.append(
                f"{where} has no `- Executor:` line; add `agent`, `human` or `tbd`"
            )
        elif value is not None and value not in EXECUTORS:
            errors.append(f"{where} has `Executor: {value}`; write agent, human or tbd")
    for brief_id, brief in briefs.items():
        if brief["qa"]:
            continue
        where = f"{wave_file}:{brief['line']}: {brief_id}"
        value = brief.get("executor")
        if value == "tbd":
            errors.append(
                f"{where} has `Executor: tbd`; make it a spike or a human task, "
                "or move it to a later wave"
            )
        elif value is None and required:
            errors.append(f"{where} has no `Executor`; add `agent` or `human`")
        elif value is not None and value not in ("agent", "human"):
            errors.append(f"{where} has `Executor: {value}`; write agent or human")
    return errors


def executor_errors(
    wave_file: Path,
    text: str,
    briefs: Mapping[str, dict[str, Any]],
    before: Mapping[str, set[str]],
) -> list[str]:
    """The declaration errors, then, in an active wave, what makes a declared
    `Executor` disagree with its tasks or a human task wait for agent work."""
    errors = declaration_errors(wave_file, text, briefs)
    front = front_matter(text)
    epics = epics_in(text)
    wave = front.get("executor")
    if front.get("status") != "active":
        return errors

    human = {
        brief_id
        for brief_id, brief in briefs.items()
        if brief.get("executor") == "human" and brief["state"] in ("todo", "done")
    }
    declared = [("the wave", f"{wave_file}:1", wave, human)]
    declared += [
        (
            epic_id,
            f"{wave_file}:{epic['line']}",
            epic.get("executor"),
            {brief_id for brief_id in human if epic_of(brief_id) == epic_id},
        )
        for epic_id, epic in epics.items()
    ]
    human_epics = {
        epic_id for epic_id, epic in epics.items() if epic.get("executor") == "human"
    }
    for name, where, value, own in declared:
        if value == "agent" and own:
            errors.append(
                f"{where}: {name} declares `agent` but has the human tasks "
                f"{sorted(own)}; declare `human`"
            )
        if value == "human" and not own:
            errors.append(
                f"{where}: {name} declares `human` but has no human task that is "
                "todo or done; add the human task or declare `agent`"
            )
    if wave == "agent" and human_epics:
        errors.append(
            f"{wave_file}:1: the wave declares `agent` but has the human epics "
            f"{sorted(human_epics)}; declare `human`"
        )
    for brief_id in sorted(human):
        if briefs[brief_id]["state"] in FINISHED:
            continue
        waiting = sorted(
            blocker
            for blocker in before.get(brief_id, set())
            if briefs[blocker]["state"] not in FINISHED
            and (briefs[blocker]["qa"] or briefs[blocker].get("executor") == "agent")
        )
        if waiting:
            errors.append(
                f"{wave_file}:{briefs[brief_id]['line']}: {brief_id} is a human task "
                f"that waits for the unfinished agent or QA tasks {waiting} of the "
                "same wave, and agents start the wave only after its human tasks; "
                "move it to a later wave"
            )
    return errors


def hitl(args: argparse.Namespace) -> Mapping[str, Any]:
    """The unresolved human and `tbd` items of each wave file in a folder."""
    folder = Path(args.wave_file)
    if not folder.is_dir():
        raise UsageError(
            f"{folder} is not a folder; with --hitl, give the waves folder, "
            "such as plan/waves"
        )
    waves = []
    errors: list[str] = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front = front_matter(text)
        briefs = briefs_in(text)[0]
        epics = epics_in(text)
        # The deadlock rule needs the graph; the graph check runs it before handoff.
        errors += executor_errors(path, text, briefs, {})
        unresolved: list[dict[str, str]] = []
        wave = front.get("executor", "unknown")
        if wave == "tbd":
            unresolved.append({"id": front.get("id", path.stem), "executor": "tbd"})
        for epic_id, epic in epics.items():
            if epic.get("executor") == "tbd":
                unresolved.append({"id": epic_id, "executor": "tbd"})
        for brief_id, brief in briefs.items():
            value = brief.get("executor")
            state = brief["state"]
            if brief["qa"] or state.startswith("carried"):
                continue
            if value == "human" and state not in FINISHED:
                unresolved.append({"id": brief_id, "executor": value, "state": state})
        waves.append(
            {
                "wave": front.get("id", path.stem),
                "file": str(path),
                "status": front.get("status", "unknown"),
                "executor": wave,
                "epics": {
                    epic_id: epic.get("executor", "unknown")
                    for epic_id, epic in epics.items()
                    if not epic["continued"]
                },
                "unresolved": unresolved,
                "agent_ready": not unresolved,
            }
        )
    if not waves:
        raise UsageError(f"{folder} has no wave file; give the waves folder")
    if errors:
        raise ScriptError(*errors)
    return {"waves": waves}


def is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def pairs_problem(value: object, first: str, second: str) -> str | None:
    """Why `value` is not a list of objects with two non-empty text keys."""
    if not isinstance(value, list):
        return "must be a list"
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {first, second}
            or not all(is_text(part) for part in item.values())
        ):
            return f'each item must be {{"{first}": "...", "{second}": "..."}}'
    return None


def texts_problem(value: object) -> str | None:
    if not isinstance(value, list) or not all(is_text(item) for item in value):
        return "must be a list of non-empty strings"
    return None


def touches_problem(value: object) -> str | None:
    if problem := texts_problem(value):
        return problem
    assert isinstance(value, list)
    wrong = [path for path in value if WILDCARD.search(path.removesuffix("/**"))]
    if wrong:
        return f"has {wrong}; write each entry as a path or as `dir/**`"
    return None


def graph_of(brief_id: str, brief: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """The parsed json block of one brief, and what is wrong with it."""
    if len(brief["blocks"]) != 1:
        return {}, [f"has {len(brief['blocks'])} json blocks; give it exactly one"]
    if "after" in brief:
        return {}, [f"has text after its json block, at line {brief['after']}; move it"]
    if not STATES.fullmatch(brief["state"]):
        return {}, [
            f"has the state {brief['state']!r}; write todo, done, dropped or carried→WNN"
        ]
    try:
        data = json.loads(brief["blocks"][0])
    except json.JSONDecodeError as error:
        return {}, [f"json block is invalid: {error}"]
    if not isinstance(data, dict):
        return {}, ["json block must be an object"]
    keys = QA_KEYS if brief["qa"] else TASK_KEYS
    problems = []
    if set(data) != keys:
        problems.append(f"json block must have exactly the keys {sorted(keys)}")
        return {}, problems
    if data["id"] != brief_id:
        problems.append(f'"id" is {data["id"]!r}; it must equal the heading')
    checks = [("needs", pairs_problem(data["needs"], "what", "check"))]
    if brief["qa"]:
        checks.append(("verifies", texts_problem(data["verifies"])))
        if data["verifies"] == []:
            checks.append(("verifies", "must name at least one task"))
    else:
        checks.append(("blocked_by", pairs_problem(data["blocked_by"], "id", "why")))
        checks.append(("touches", touches_problem(data["touches"])))
    problems += [f'"{key}" {problem}' for key, problem in checks if problem]
    return (data if not problems else {}), problems


def other_wave_briefs(wave_file: Path) -> dict[str, dict[str, Any]]:
    """The briefs of the other wave files in the same folder, by ID."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(wave_file.parent.glob("*.md")):
        if path.resolve() != wave_file.resolve():
            found.update(briefs_in(path.read_text(encoding="utf-8"))[0])
    return found


def overlap(first: str, second: str) -> bool:
    """Whether two `touches` entries, each a path or `dir/**`, share a path."""
    first, second = first.removeprefix("./"), second.removeprefix("./")
    if not first.endswith("/**") and not second.endswith("/**"):
        return first == second
    a, b = first.removesuffix("**"), second.removesuffix("**")
    if first.endswith("/**") and second.endswith("/**"):
        return a.startswith(b) or b.startswith(a)
    folder, path = (a, b) if first.endswith("/**") else (b, a)
    return path.startswith(folder)


def cycle_in(blockers: Mapping[str, list[str]]) -> list[str] | None:
    """One cycle of the graph as a list of IDs, or None."""
    done: set[str] = set()
    for start in blockers:
        path: list[str] = []
        stack = [(start, iter(blockers[start]))]
        path.append(start)
        while stack:
            node, rest = stack[-1]
            following = next(rest, None)
            if following is None:
                done.add(node)
                stack.pop()
                path.pop()
            elif following in path:
                return [*path[path.index(following) :], following]
            elif following not in done:
                path.append(following)
                stack.append((following, iter(blockers[following])))
    return None


def check(args: argparse.Namespace) -> Mapping[str, Any]:
    wave_file = Path(args.wave_file)
    if not wave_file.is_file():
        raise UsageError(f"{wave_file} is not a file; give the path of a wave file")
    text = wave_file.read_text(encoding="utf-8")
    briefs, malformed = briefs_in(text)
    if malformed:
        raise ScriptError(
            *(
                f"{wave_file}:{line}: this line is not a brief heading such as "
                "`#### E04-T01: <title>`, or opens a json fence that never closes; "
                "correct it"
                for line in malformed
            )
        )
    if not briefs:
        raise ScriptError(
            f"{wave_file} has no brief; a brief starts with a heading such as "
            "`#### E04-T01: <title>`"
        )
    errors: list[str] = []
    graphs: dict[str, dict[str, Any]] = {}
    for brief_id, brief in briefs.items():
        where = f"{wave_file}:{brief['line']}: {brief_id}"
        if brief["duplicate"]:
            errors.append(f"{where} has more than one brief; keep one")
        graph, problems = graph_of(brief_id, brief)
        errors += [f"{where} {problem}" for problem in problems]
        if graph:
            graphs[brief_id] = graph
    if errors:
        raise ScriptError(*errors)

    elsewhere = other_wave_briefs(wave_file)
    blockers: dict[str, list[str]] = {}
    gates: dict[str, list[str]] = {}
    for brief_id, graph in graphs.items():
        where = f"{wave_file}:{briefs[brief_id]['line']}: {brief_id}"
        named = (
            graph["verifies"]
            if briefs[brief_id]["qa"]
            else [edge["id"] for edge in graph["blocked_by"]]
        )
        blockers[brief_id] = []
        for blocker in named:
            if blocker == brief_id:
                errors.append(f"{where} names itself as a blocker; remove it")
                continue
            other = briefs.get(blocker) or elsewhere.get(blocker)
            if other is None:
                errors.append(
                    f"{where} names {blocker}, which no wave file in "
                    f"{wave_file.parent} defines; correct the ID"
                )
                continue
            if briefs[brief_id]["state"] == "todo" and other["state"] == "dropped":
                errors.append(
                    f"{where} is blocked by {blocker}, which is dropped; "
                    "remove the blocker or name the task that replaces it"
                )
            if briefs[brief_id]["qa"] and other["qa"]:
                errors.append(f"{where} verifies {blocker}, a QA task; name tasks only")
            elif other["qa"]:
                gates.setdefault(blocker, []).append(brief_id)
            if blocker in briefs:
                blockers[brief_id].append(blocker)
    if errors:
        raise ScriptError(*errors)
    if cycle := cycle_in(blockers):
        raise ScriptError(
            f"{wave_file}: cycle {' → '.join(cycle)}; remove one `blocked_by` of it"
        )

    depth: dict[str, int] = {}

    def depth_of(brief_id: str) -> int:
        if brief_id not in depth:
            depth[brief_id] = 1 + max(map(depth_of, blockers[brief_id]), default=-1)
        return depth[brief_id]

    before: dict[str, set[str]] = {}

    def before_of(brief_id: str) -> set[str]:
        if brief_id not in before:
            before[brief_id] = set(blockers[brief_id]).union(
                *(before_of(blocker) for blocker in blockers[brief_id])
            )
        return before[brief_id]

    for brief_id in sorted(blockers, key=depth_of):
        before_of(brief_id)
    open_tasks = [
        brief_id
        for brief_id, brief in briefs.items()
        if not brief["qa"] and brief["state"] == "todo"
    ]
    for index, first in enumerate(open_tasks):
        for second in open_tasks[index + 1 :]:
            if first in before[second] or second in before[first]:
                continue
            shared = sorted(
                {
                    f"`{a}` and `{b}`" if a != b else f"`{a}`"
                    for a in graphs[first]["touches"]
                    for b in graphs[second]["touches"]
                    if overlap(a, b)
                }
            )
            if shared:
                errors.append(
                    f"{wave_file}: {first} and {second} can run at the same time "
                    f"and both touch {', '.join(shared)}; add {first} to the "
                    f"`blocked_by` of {second}, or correct `touches`"
                )
    errors += executor_errors(wave_file, text, briefs, before)
    if errors:
        raise ScriptError(*errors)

    batches: list[list[str]] = [[] for _ in range(max(depth.values()) + 1)]
    for brief_id in briefs:
        batches[depth[brief_id]].append(brief_id)
    log.info("%d briefs, %d batches", len(briefs), len(batches))
    shape = {"longest_chain": len(batches), "widths": [len(batch) for batch in batches]}

    nodes = [
        {
            **graphs[brief_id],
            "kind": "qa" if brief["qa"] else "task",
            "state": brief["state"],
        }
        for brief_id, brief in briefs.items()
    ]
    edges = [
        {"from": blocker, "to": brief_id, "why": why}
        for brief_id, graph in graphs.items()
        for blocker, why in (
            [(verified, "verifies") for verified in graph["verifies"]]
            if briefs[brief_id]["qa"]
            else [(edge["id"], edge["why"]) for edge in graph["blocked_by"]]
        )
    ]
    content = (
        json.dumps(
            {
                "wave_file": wave_file.name,
                "nodes": nodes,
                "edges": edges,
                "batches": batches,
                "gates": gates,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    graph_file = wave_file.with_suffix(".graph.json")
    if graph_file.is_file() and graph_file.read_text(encoding="utf-8") == content:
        return {"file": str(graph_file), **shape}
    report = {"file": str(graph_file), **shape, "changes": [["write", str(graph_file)]]}
    if args.check:
        raise ScriptError(
            f"{graph_file} does not match the briefs; run "
            f"`uv run {Path(__file__).resolve()} {wave_file}` to write it",
            report=report,
        )
    if not args.dry_run:
        graph_file.write_text(content, encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(exit_codes=EXIT_CODES, description=__doc__, epilog=EPILOG)
    parser.add_argument(
        "wave_file",
        metavar="path",
        help="the wave file, such as plan/waves/W02-x.md; with --hitl, the waves folder",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--hitl",
        action="store_true",
        help="write nothing; report the unresolved human and tbd items of each wave",
    )
    mode.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="check the briefs and answer the same, without writing the graph file",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="write nothing, and fail when the graph file does not match the briefs",
    )
    return run_script(parser, lambda args: (hitl if args.hitl else check)(args), argv)


if __name__ == "__main__":
    raise SystemExit(main())

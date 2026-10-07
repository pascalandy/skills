#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Verify transcript through its public CLI and retain structured evidence."""

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

    `detail` is text printed on stderr before the messages; `report` is the
    object `--json` prints on stderr beside them.
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
    and whose usage errors print short usage and the help hint, then exit 2.

    With `json_errors` set, a usage error is one JSON object on stderr instead.
    """

    json_errors = False

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
        if self.json_errors:
            failure = {"errors": [message], "help": f"{self.prog} --help"}
            self.exit(USAGE, json.dumps(failure, indent=2) + "\n")
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
    -h and --help win over every other argument, or to spot --json early.

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


def usage_error(message: str) -> NoReturn:
    raise UsageError(message)


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

import hashlib
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

__version__ = "3.0.0"
CANONICAL_YOUTUBE_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
# Selected by the transcript README's Test videos rule
TEST_PROFILE = "sonnet"
EXIT_CODES = exit_codes({1: "a feature failed, or the verifier could not run"})
EVIDENCE_NAMESPACE = "eval-transcript"
RUN_MARKER = ".verify-transcript-run"
DOCTOR_HINT = "run 'verify-transcript doctor -v' and fix what it reports"

log = logging.getLogger("verify-transcript")
FEATURE_AREAS = (
    "interface",
    "youtube",
    "zoom",
    "summaries",
    "configuration",
    "diagnostics",
    "dry-runs",
)

Layout = Literal["source", "applied"]
Verdict = Literal["PASS", "FAIL"]
# "answer" is the one JSON line transcript answers with: stdout on exit 0, the
# last line of stderr otherwise. "text" is help or version on stdout
OutputKind = Literal["answer", "text"]
SurfaceKind = Literal["command", "option", "behavior"]
ProbeKind = Literal[
    "help-version",
    "structured-recovery",
    "transcript-only-dry-run",
    "prompts",
    "profiles",
    "models",
    "doctor-youtube",
    "doctor-zoom",
    "youtube-dry-run-summary",
    "zoom-dry-run",
    "youtube-real-summary",
]


class VerificationError(RuntimeError):
    """Describe an actionable verifier failure before feature execution."""

    def __init__(self, code: str, message: str, hint: str, exit_code: int = 1):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.exit_code = exit_code

    @property
    def line(self) -> str:
        """The message, then the hint that fixes it, as one error."""
        hint = self.hint.rstrip(".")
        return f"{self.message.rstrip('.')}; {hint[:1].lower()}{hint[1:]}"


@dataclass(frozen=True)
class LocatedSkill:
    directory: Path
    transcript_script: Path
    layout: Layout


@dataclass(frozen=True)
class FeatureSpec:
    id: str
    title: str
    areas: tuple[str, ...]
    default: bool
    probe: ProbeKind
    timeout_seconds: int = 30

    @property
    def paid(self) -> bool:
        return self.probe == "youtube-real-summary"


@dataclass(frozen=True)
class OutputExpectation:
    kind: OutputKind
    exit_codes: tuple[int, ...]
    # A real run streams its result folder on stderr before it answers
    events: bool = False


@dataclass(frozen=True)
class CommandPlan:
    id: str
    args: tuple[str, ...]
    output_dir: Path | None = None
    expectation: OutputExpectation = OutputExpectation("answer", (0,))


@dataclass(frozen=True)
class PublicSurface:
    id: str
    kind: SurfaceKind
    token: str | None = None
    owners: tuple[str, ...] = ()
    exclusion_reason: str | None = None


@dataclass(frozen=True)
class HelpContract:
    id: str
    args: tuple[str, ...]
    choices: frozenset[str]
    options: frozenset[str]


@dataclass(frozen=True)
class CapturedProcess:
    argv: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


@dataclass(frozen=True)
class RunContext:
    run_id: str
    located: LocatedSkill
    scratch_dir: Path
    evidence_dir: Path
    allow_paid: bool
    youtube_url: str


# Options every transcript command accepts, before or after its name
GLOBAL_OPTIONS = frozenset(
    {"--help", "--verbose", "--debug", "--no-color", "--no-progress"}
)

RUN_OPTIONS = GLOBAL_OPTIONS | {
    "--dry-run",
    "--effort",
    "--model",
    "--no-summary",
    "--open",
    "--output-dir",
    "--preview",
    "--profile",
    "--prompt",
    "--provider",
    "--timeout",
}

HELP_CONTRACTS = (
    HelpContract(
        "root-help",
        ("--help",),
        frozenset({"run", "list", "doctor", "help"}),
        GLOBAL_OPTIONS | {"--version"},
    ),
    HelpContract(
        "run-help",
        ("run", "--help"),
        frozenset({"youtube", "zoom"}),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "youtube-help",
        ("run", "youtube", "--help"),
        frozenset(),
        RUN_OPTIONS | {"--url"},
    ),
    HelpContract(
        "zoom-help",
        ("run", "zoom", "--help"),
        frozenset(),
        RUN_OPTIONS | {"--latest", "--path"},
    ),
    HelpContract(
        "list-help",
        ("list", "--help"),
        frozenset({"profiles", "prompts", "models"}),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "prompts-help",
        ("list", "prompts", "--help"),
        frozenset(),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "profiles-help",
        ("list", "profiles", "--help"),
        frozenset(),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "models-help",
        ("list", "models", "--help"),
        frozenset(),
        GLOBAL_OPTIONS | {"--provider"},
    ),
    HelpContract(
        "doctor-help",
        ("doctor", "--help"),
        frozenset(),
        GLOBAL_OPTIONS | {"--no-summary", "--source"},
    ),
    HelpContract(
        "help-help",
        ("help", "--help"),
        frozenset(),
        GLOBAL_OPTIONS,
    ),
)

PUBLIC_SURFACES = (
    PublicSurface(
        "command.run",
        "command",
        "run",
        ("youtube.dry-run-summary", "zoom.dry-run"),
    ),
    PublicSurface(
        "command.list",
        "command",
        "list",
        (
            "configuration.profiles",
            "configuration.prompts",
            "configuration.models",
        ),
    ),
    PublicSurface(
        "command.doctor",
        "command",
        "doctor",
        ("diagnostics.youtube", "diagnostics.zoom"),
    ),
    PublicSurface(
        "command.youtube",
        "command",
        "youtube",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface("command.zoom", "command", "zoom", ("zoom.dry-run",)),
    PublicSurface(
        "command.prompts",
        "command",
        "prompts",
        ("configuration.prompts",),
    ),
    PublicSurface(
        "command.profiles",
        "command",
        "profiles",
        ("configuration.profiles",),
    ),
    PublicSurface(
        "command.models",
        "command",
        "models",
        ("configuration.models",),
    ),
    PublicSurface("command.help", "command", "help", ("interface.help-version",)),
    PublicSurface("option.help", "option", "--help", ("interface.help-version",)),
    PublicSurface("option.version", "option", "--version", ("interface.help-version",)),
    PublicSurface("option.url", "option", "--url", ("youtube.dry-run-summary",)),
    PublicSurface(
        "option.latest",
        "option",
        "--latest",
        exclusion_reason="Requires reading the user's private Zoom directory",
    ),
    PublicSurface("option.path", "option", "--path", ("zoom.dry-run",)),
    PublicSurface(
        "option.source",
        "option",
        "--source",
        ("diagnostics.youtube", "diagnostics.zoom"),
    ),
    PublicSurface(
        "option.no-summary",
        "option",
        "--no-summary",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.profile",
        "option",
        "--profile",
        ("youtube.dry-run-summary", "zoom.dry-run", "youtube.real-summary"),
    ),
    PublicSurface(
        "option.provider",
        "option",
        "--provider",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.prompt",
        "option",
        "--prompt",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.model",
        "option",
        "--model",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.effort",
        "option",
        "--effort",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.output-dir",
        "option",
        "--output-dir",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.dry-run",
        "option",
        "--dry-run",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.timeout",
        "option",
        "--timeout",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.open", "option", "--open", exclusion_reason="Would open Finder"
    ),
    PublicSurface(
        "option.preview",
        "option",
        "--preview",
        exclusion_reason="Would render an interactive preview",
    ),
    PublicSurface(
        "option.debug",
        "option",
        "--debug",
        exclusion_reason=(
            "Only adds internals, timings, and tracebacks on stderr; "
            "transcript contract tests compare every verbosity level"
        ),
    ),
    PublicSurface(
        "option.verbose",
        "option",
        "--verbose",
        exclusion_reason=(
            "Only adds progress lines on stderr; "
            "transcript contract tests compare every verbosity level"
        ),
    ),
    PublicSurface(
        "option.no-color",
        "option",
        "--no-color",
        exclusion_reason=(
            "Only changes terminal rendering; "
            "transcript contract tests drive it on a pseudo-terminal"
        ),
    ),
    PublicSurface(
        "option.no-progress",
        "option",
        "--no-progress",
        exclusion_reason=(
            "Only hides the terminal spinner; "
            "transcript contract tests drive it on a pseudo-terminal"
        ),
    ),
    PublicSurface(
        "stream.text-stdout",
        "behavior",
        owners=("interface.help-version",),
    ),
    PublicSurface(
        "stream.success-json-stdout",
        "behavior",
        owners=("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "stream.invalid-json-stderr",
        "behavior",
        owners=("interface.structured-recovery",),
    ),
    PublicSurface(
        "stream.runtime-json-stderr",
        "behavior",
        exclusion_reason=(
            "Runtime JSON failures require injected external failures and are covered by unit tests"
        ),
    ),
    PublicSurface("exit.success", "behavior", owners=("interface.help-version",)),
    PublicSurface(
        "exit.runtime-failure",
        "behavior",
        exclusion_reason=(
            "Runtime exit paths require injected external failures and are covered by unit tests"
        ),
    ),
    PublicSurface(
        "exit.invalid-input",
        "behavior",
        owners=("interface.structured-recovery",),
    ),
    PublicSurface(
        "exit.interrupted",
        "behavior",
        exclusion_reason="Requires sending a process signal and is covered by unit tests",
    ),
    PublicSurface(
        "exit.temporary",
        "behavior",
        exclusion_reason=(
            "Requires an injected network failure and is covered by unit tests"
        ),
    ),
    PublicSurface(
        "publication.summary-success",
        "behavior",
        owners=("youtube.real-summary",),
    ),
    PublicSurface(
        "transcription.upload-completion",
        "behavior",
        owners=("youtube.real-summary",),
    ),
    PublicSurface(
        "transcription.upload-timeouts",
        "behavior",
        exclusion_reason=(
            "Slow and interrupted uploads are covered by transcript "
            "TestDeepgramContract tests without paid calls"
        ),
    ),
    PublicSurface(
        "publication.transcript-only",
        "behavior",
        exclusion_reason="Requires a paid Deepgram call and is covered by unit tests",
    ),
    PublicSurface(
        "publication.summary-failure",
        "behavior",
        exclusion_reason="Requires a forced provider failure and is covered by unit tests",
    ),
    PublicSurface(
        "publication.transaction-and-collisions",
        "behavior",
        exclusion_reason="Covered by deterministic unit tests without paid work",
    ),
)


FEATURES = (
    FeatureSpec(
        id="interface.help-version",
        title="CLI help and version",
        areas=("interface",),
        default=True,
        probe="help-version",
    ),
    FeatureSpec(
        id="interface.structured-recovery",
        title="Structured CLI recovery",
        areas=("interface", "configuration", "youtube"),
        default=True,
        probe="structured-recovery",
    ),
    FeatureSpec(
        id="dry-runs.transcript-only",
        title="Transcript-only plans",
        areas=("dry-runs", "configuration", "summaries", "youtube", "zoom"),
        default=True,
        probe="transcript-only-dry-run",
    ),
    FeatureSpec(
        id="configuration.prompts",
        title="Bundled prompt discovery",
        areas=("configuration", "summaries"),
        default=True,
        probe="prompts",
    ),
    FeatureSpec(
        id="configuration.profiles",
        title="Inference profile discovery",
        areas=("configuration", "summaries"),
        default=True,
        probe="profiles",
    ),
    FeatureSpec(
        id="configuration.models",
        title="Summary model discovery",
        areas=("configuration", "summaries"),
        default=True,
        probe="models",
    ),
    FeatureSpec(
        id="diagnostics.youtube",
        title="YouTube diagnostics",
        areas=("diagnostics", "youtube"),
        default=True,
        probe="doctor-youtube",
    ),
    FeatureSpec(
        id="diagnostics.zoom",
        title="Zoom diagnostics",
        areas=("diagnostics", "zoom"),
        default=True,
        probe="doctor-zoom",
    ),
    FeatureSpec(
        id="youtube.dry-run-summary",
        title="YouTube summary plan",
        areas=("youtube", "summaries", "configuration", "dry-runs"),
        default=True,
        probe="youtube-dry-run-summary",
    ),
    FeatureSpec(
        id="zoom.dry-run",
        title="Zoom source plan",
        areas=("zoom", "summaries", "configuration", "dry-runs"),
        default=True,
        probe="zoom-dry-run",
    ),
    FeatureSpec(
        id="youtube.real-summary",
        title="Real YouTube transcription and summary",
        areas=("youtube", "summaries"),
        default=False,
        probe="youtube-real-summary",
        timeout_seconds=620,
    ),
)


def verify_skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def locate_transcript_skill(skill_dir: Path) -> LocatedSkill:
    """Locate the transcript skill in categorized source or flat applied layouts."""
    candidates: tuple[tuple[Layout, Path], ...] = (
        ("source", skill_dir.parent.parent / "andy" / "transcript"),
        ("applied", skill_dir.parent / "transcript"),
    )
    attempted = []
    for layout, candidate in candidates:
        resolved = candidate.resolve()
        attempted.append(str(resolved))
        script = resolved / "scripts" / "transcript.py"
        if (resolved / "SKILL.md").is_file() and script.is_file():
            return LocatedSkill(resolved, script, layout)
    raise VerificationError(
        "transcript_skill_not_found",
        "Could not locate the transcript skill beside verify-transcript.",
        "Expected a categorized source or flat applied layout. Checked: "
        + ", ".join(attempted),
    )


def select_features(
    requested: tuple[str, ...], select_all: bool, allow_paid: bool
) -> tuple[FeatureSpec, ...]:
    """Resolve feature selection and reject paid work without dual intent."""
    by_id = {feature.id: feature for feature in FEATURES}
    if select_all and requested:
        raise VerificationError(
            "invalid_selection",
            "--all cannot be combined with --feature.",
            "Use --all or repeat --feature with exact feature IDs.",
            exit_code=2,
        )
    unknown = sorted(set(requested) - by_id.keys())
    if unknown:
        raise VerificationError(
            "unknown_feature",
            "Unknown feature ID: " + ", ".join(unknown),
            "Run 'verify-transcript features' and use one of features[].id.",
            exit_code=2,
        )
    if select_all:
        selected = FEATURES
    elif requested:
        selected = tuple(by_id[feature_id] for feature_id in dict.fromkeys(requested))
    else:
        selected = tuple(feature for feature in FEATURES if feature.default)
    paid = [feature.id for feature in selected if feature.paid]
    if paid and not allow_paid:
        raise VerificationError(
            "paid_intent_required",
            "Paid feature selection requires --allow-paid: " + ", ".join(paid),
            "Follow the transcript README's Test videos rule, then repeat with --allow-paid.",
            exit_code=2,
        )
    return selected


def _slug(feature_id: str) -> str:
    return feature_id.replace(".", "-")


def _zoom_fixture(context: RunContext) -> Path:
    meeting = context.scratch_dir / "input" / "zoom-meeting"
    meeting.mkdir(parents=True, exist_ok=True)
    (meeting / "audio_only.m4a").touch()
    return meeting


def build_commands(
    feature: FeatureSpec, context: RunContext
) -> tuple[CommandPlan, ...]:
    """Build fixed public commands from the typed feature registry."""
    output_dir = context.scratch_dir / "output" / _slug(feature.id)
    if feature.probe == "help-version":
        text_output = OutputExpectation("text", (0,))
        return tuple(
            CommandPlan(contract.id, contract.args, expectation=text_output)
            for contract in HELP_CONTRACTS
        ) + (CommandPlan("version", ("--version",), expectation=text_output),)
    if feature.probe == "structured-recovery":
        error_output = OutputExpectation("answer", (2,))
        plans = (
            (
                "invalid-usage",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--unknown-option",
                ),
            ),
            (
                "invalid-source",
                ("run", "youtube", "--url", "https://example.com/video"),
            ),
            (
                "invalid-configuration",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--provider",
                    "codex",
                    "--model",
                    "",
                    "--effort",
                    "low",
                ),
            ),
        )
        return tuple(
            CommandPlan(
                plan_id,
                (
                    *args,
                    "--output-dir",
                    str(output_dir / plan_id),
                    "--dry-run",
                ),
                output_dir / plan_id,
                error_output,
            )
            for plan_id, args in plans
        )
    if feature.probe == "transcript-only-dry-run":
        youtube_output = output_dir / "youtube"
        zoom_output = output_dir / "zoom"
        return (
            CommandPlan(
                "youtube-transcript-only",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--no-summary",
                    "--output-dir",
                    str(youtube_output),
                    "--timeout",
                    "42",
                    "--dry-run",
                ),
                youtube_output,
            ),
            CommandPlan(
                "zoom-transcript-only",
                (
                    "run",
                    "zoom",
                    "--path",
                    str(_zoom_fixture(context)),
                    "--no-summary",
                    "--output-dir",
                    str(zoom_output),
                    "--timeout",
                    "43",
                    "--dry-run",
                ),
                zoom_output,
            ),
        )
    if feature.probe == "prompts":
        return (CommandPlan("prompts", ("list", "prompts")),)
    if feature.probe == "profiles":
        return (CommandPlan("profiles", ("list", "profiles")),)
    if feature.probe == "models":
        return (
            CommandPlan(
                "models-claude",
                ("list", "models", "--provider", "claude"),
            ),
            CommandPlan(
                "models-codex",
                ("list", "models", "--provider", "codex"),
            ),
            CommandPlan(
                "models-openrouter",
                ("list", "models", "--provider", "openrouter"),
            ),
        )
    if feature.probe == "doctor-youtube":
        return (
            CommandPlan(
                "doctor-youtube",
                ("doctor", "--source", "youtube"),
                expectation=OutputExpectation("answer", (0, 1)),
            ),
        )
    if feature.probe == "doctor-zoom":
        return (
            CommandPlan(
                "doctor-zoom",
                ("doctor", "--source", "zoom"),
                expectation=OutputExpectation("answer", (0, 1)),
            ),
        )
    if feature.probe == "youtube-dry-run-summary":
        return (
            CommandPlan(
                "youtube-dry-run-summary",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--profile",
                    "glm",
                    "--prompt",
                    "summary_with_quotes",
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                ),
                output_dir,
            ),
        )
    if feature.probe == "zoom-dry-run":
        return (
            CommandPlan(
                "zoom-dry-run",
                (
                    "run",
                    "zoom",
                    "--path",
                    str(_zoom_fixture(context)),
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                ),
                output_dir,
            ),
        )
    if feature.probe == "youtube-real-summary":
        return (
            CommandPlan(
                "youtube-real-summary",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--profile",
                    TEST_PROFILE,
                    "--prompt",
                    "short_summary",
                    "--output-dir",
                    str(output_dir),
                ),
                output_dir,
                OutputExpectation("answer", (0,), events=True),
            ),
        )
    raise AssertionError(f"Unhandled probe: {feature.probe}")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def assert_safe_command(
    feature: FeatureSpec, plan: CommandPlan, context: RunContext
) -> None:
    """Recheck payment and output confinement immediately before execution."""
    args = plan.args
    if not args:
        raise VerificationError(
            "unsafe_command",
            f"{feature.id} has an empty transcript command.",
            "Fix the registry before running this feature.",
        )
    forbidden = sorted({"--open", "--preview"}.intersection(args))
    if forbidden:
        raise VerificationError(
            "unsafe_side_effect",
            f"{feature.id} requests a GUI side effect: {', '.join(forbidden)}",
            "Remove GUI flags from verification commands.",
        )
    if plan.expectation.kind == "text":
        if args != ("--version",) and args[-1] != "--help":
            raise VerificationError(
                "unsafe_command",
                f"{feature.id} requests unrecognized text output.",
                "Text verification is limited to transcript help and version output.",
            )
        return
    if args[0] != "run":
        return
    if "--output-dir" not in args or plan.output_dir is None:
        raise VerificationError(
            "unsafe_output",
            f"{feature.id} has no eval-owned output directory.",
            "Every transcript run must set --output-dir under the current scratch root.",
        )
    output_arg = Path(args[args.index("--output-dir") + 1])
    if output_arg.resolve() != plan.output_dir.resolve() or not _is_within(
        output_arg, context.scratch_dir
    ):
        raise VerificationError(
            "unsafe_output",
            f"{feature.id} output escapes the eval scratch root: {output_arg}",
            "Use the output path created by verify-transcript for this run.",
        )
    is_paid_command = "--dry-run" not in args
    if is_paid_command != feature.paid:
        raise VerificationError(
            "invalid_cost_classification",
            f"{feature.id} paid classification does not match its command.",
            "Fix the typed feature registry before running this feature.",
        )
    if is_paid_command and not context.allow_paid:
        raise VerificationError(
            "paid_intent_required",
            f"{feature.id} reached the paid boundary without --allow-paid.",
            "Follow the transcript README's Test videos rule, then repeat with --allow-paid.",
            exit_code=2,
        )


def run_process(
    argv: tuple[str, ...], cwd: Path, timeout_seconds: int
) -> CapturedProcess:
    """Run one process group so timeout and interruption teardown are bounded."""
    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    except KeyboardInterrupt:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise
    return CapturedProcess(
        argv=argv,
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=round(time.monotonic() - started, 3),
        timed_out=timed_out,
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _parse_json_document(content: str, stream: str) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise AssertionError(f"transcript returned invalid JSON on {stream}") from error
    if not isinstance(payload, dict):
        raise TypeError(f"transcript returned non-object JSON on {stream}")
    return payload


def _reported_error(stderr: str) -> str:
    """`: <errors>` from the answer that ends transcript's stderr, or nothing."""
    try:
        payload = json.loads(stderr.splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return ""
    errors = payload.get("errors") if isinstance(payload, dict) else None
    if not isinstance(errors, list) or not all(isinstance(e, str) for e in errors):
        return ""
    return f": {'; '.join(errors)}" if errors else ""


def parse_expected_output(
    process: CapturedProcess, expectation: OutputExpectation
) -> dict[str, object]:
    """Parse only the declared public stream and enforce its exit contract.

    Help and version are text on stdout. Every other command answers in one
    JSON line whose `ok` agrees with the exit code: alone on stdout on exit 0,
    and ending stderr otherwise (docs/references/script-output.md).
    """
    if process.exit_code not in expectation.exit_codes:
        raise AssertionError(
            f"transcript exited {process.exit_code}; expected {expectation.exit_codes}"
            + _reported_error(process.stderr)
        )
    if expectation.kind == "text":
        _require(not process.stderr, "text command wrote to stderr")
        _require(bool(process.stdout.strip()), "text output is empty")
        return {"text": process.stdout}
    if process.exit_code == 0:
        _require(
            expectation.events or not process.stderr,
            "a successful command wrote to stderr",
        )
        _require(process.stdout.count("\n") == 1, "stdout is not one JSON line")
        payload = _parse_json_document(process.stdout, "stdout")
    else:
        _require(not process.stdout, "a failed command wrote to stdout")
        _require(bool(process.stderr.strip()), "a failed command left stderr empty")
        payload = _parse_json_document(process.stderr.splitlines()[-1], "stderr")
    _require(
        payload.get("ok") is (process.exit_code == 0),
        "the answer's ok disagrees with the exit code",
    )
    return payload


def capture_command(
    feature: FeatureSpec,
    plan: CommandPlan,
    context: RunContext,
) -> tuple[CapturedProcess, dict[str, object]]:
    assert_safe_command(feature, plan, context)
    # --quiet keeps uv's own setup lines, such as "Installed 12 packages", off
    # stderr; a fresh checkout triggers them, and they are not transcript's output
    argv = (
        "uv",
        "run",
        "--quiet",
        str(context.located.transcript_script),
        *plan.args,
    )
    command_dir = context.evidence_dir / "cases" / _slug(feature.id) / plan.id
    _write_json(
        command_dir / "command.json",
        {
            "argv": argv,
            "cwd": str(context.scratch_dir),
            "timeout_seconds": feature.timeout_seconds,
        },
    )
    process = run_process(argv, context.scratch_dir, feature.timeout_seconds)
    command_dir.mkdir(parents=True, exist_ok=True)
    (command_dir / "stdout.txt").write_text(process.stdout, encoding="utf-8")
    (command_dir / "stderr.txt").write_text(process.stderr, encoding="utf-8")
    _write_json(
        command_dir / "process.json",
        {
            "exit_code": process.exit_code,
            "duration_seconds": process.duration_seconds,
            "timed_out": process.timed_out,
        },
    )
    payload = parse_expected_output(process, plan.expectation)
    _write_json(command_dir / "parsed.json", payload)
    return process, payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _validate_doctor(
    feature: FeatureSpec,
    process: CapturedProcess,
    payload: dict[str, object],
) -> dict[str, object]:
    """A ready doctor answers ok alone; an unready one names each failed check of
    its own source with its fix."""
    if feature.probe == "doctor-youtube":
        expected_checks = {
            "deepgram_credential",
            "claude",
            "pi",
            "ffmpeg",
            "ffprobe",
            "yt_dlp",
            "youtube_browser",
        }
    else:
        expected_checks = {"deepgram_credential", "claude", "pi", "zoom_recordings"}
    readiness_ok = process.exit_code == 0
    if readiness_ok:
        _require(payload == {"ok": True}, "a ready doctor answered more than ok")
        return {"readiness_ok": True, "failed_checks": []}
    errors = payload.get("errors")
    _require(
        isinstance(errors, list)
        and bool(errors)
        and all(isinstance(error, str) for error in errors),
        "an unready doctor answered no errors",
    )
    failed = [error.split(":", 1)[0] for error in errors]
    _require(
        set(failed) <= expected_checks,
        f"doctor source is invalid: it reported {', '.join(failed)}",
    )
    _require(all("; fix: " in error for error in errors), "a doctor error names no fix")
    return {"readiness_ok": False, "failed_checks": failed}


def _validate_dry_run(
    feature: FeatureSpec,
    plan: CommandPlan,
    process: CapturedProcess,
    payload: dict[str, object],
) -> dict[str, object]:
    _require(process.exit_code == 0, f"{feature.id} exited {process.exit_code}")
    _require(payload.get("ok") is True, f"{feature.id} did not report ok")
    _require(
        payload.get("timeout_seconds") == 570.0,
        f"{feature.id} did not resolve the default timeout",
    )
    _require(plan.output_dir is not None, f"{feature.id} has no planned output")
    _require(
        Path(str(payload.get("output_dir"))).resolve() == plan.output_dir.resolve(),
        f"{feature.id} reported the wrong output directory",
    )
    _require(not plan.output_dir.exists(), f"{feature.id} created its output directory")
    source = payload.get("source")
    summary = payload.get("summary")
    _require(isinstance(source, dict), f"{feature.id} source is missing")
    _require(isinstance(summary, dict), f"{feature.id} summary is missing")
    if feature.probe == "youtube-dry-run-summary":
        _require(source.get("kind") == "youtube", "YouTube dry-run source is invalid")
        expected_url = plan.args[plan.args.index("--url") + 1]
        _require(source.get("url") == expected_url, "YouTube dry-run URL is invalid")
        _require(summary.get("enabled") is True, "summary plan is disabled")
        _require(summary.get("profile") == "glm", "summary profile is invalid")
        _require(summary.get("provider") == "openrouter", "summary provider is invalid")
        _require(
            summary.get("model") == "z-ai/glm-5.3-flash",
            "summary model is invalid",
        )
        _require(summary.get("effort") == "medium", "summary effort is invalid")
        _require(
            summary.get("prompt") == "summary_with_quotes",
            "summary prompt is invalid",
        )
    else:
        _require(source.get("kind") == "zoom", "Zoom dry-run source is invalid")
        expected_meeting = Path(plan.args[plan.args.index("--path") + 1]).resolve()
        _require(
            Path(str(source.get("path"))).resolve() == expected_meeting,
            "Zoom dry-run folder is invalid",
        )
        _require(
            Path(str(source.get("audio"))).resolve()
            == expected_meeting / "audio_only.m4a",
            "Zoom dry-run audio is invalid",
        )
        _require(summary.get("enabled") is True, "Zoom summary plan is disabled")
        _require(summary.get("profile") == "opus", "Zoom summary profile is invalid")
        _require(
            summary.get("provider") == "claude", "Zoom summary provider is invalid"
        )
        _require(
            summary.get("model") == "claude-opus-5-5", "Zoom summary model is invalid"
        )
        _require(summary.get("effort") == "high", "Zoom summary effort is invalid")
        _require(
            summary.get("prompt") == "synthese-rencontre",
            "Zoom summary prompt is invalid",
        )
    return {"source": source, "summary": summary}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Each file a YouTube run saves, by the end of its name
ARTIFACT_NAMES = {
    "metadata": "meta.txt",
    "transcript": "raw_transcript.txt",
    "sentences": "raw_sentences.txt",
    "json": "raw_transcript.json",
    "summary": ".md",
}


def _artifacts(files: object) -> dict[str, Path]:
    """The files a run answered with, by kind; each kind once."""
    _require(
        isinstance(files, list) and all(isinstance(path, str) for path in files),
        "real run answered no files",
    )
    artifacts: dict[str, Path] = {}
    for path in files:
        kinds = [kind for kind, end in ARTIFACT_NAMES.items() if path.endswith(end)]
        _require(len(kinds) == 1, f"real run answered an unknown file: {path}")
        _require(kinds[0] not in artifacts, f"real run answered two {kinds[0]} files")
        artifacts[kinds[0]] = Path(path).resolve()
    _require(
        artifacts.keys() == ARTIFACT_NAMES.keys(), "real run file set is incomplete"
    )
    return artifacts


def _validate_e2e(
    feature: FeatureSpec,
    plan: CommandPlan,
    process: CapturedProcess,
    payload: dict[str, object],
    context: RunContext,
) -> dict[str, object]:
    _require(process.exit_code == 0, f"{feature.id} exited {process.exit_code}")
    _require(payload.get("ok") is True, "real run did not report success")
    artifacts = _artifacts(payload.get("files"))
    _require(plan.output_dir is not None, "real run has no isolated output root")
    published_dir = artifacts["metadata"].parent
    _require(
        _is_within(published_dir, plan.output_dir), "published output escaped isolation"
    )
    _require(
        any(
            Path(line).resolve() == published_dir
            for line in process.stderr.splitlines()
            if line.startswith("/")
        ),
        "real run did not stream its result folder on stderr",
    )
    manifest: dict[str, object] = {}
    for kind, artifact in sorted(artifacts.items()):
        _require(artifact.parent == published_dir, f"{kind} escaped published output")
        _require(artifact.is_file(), f"{kind} artifact does not exist")
        size = artifact.stat().st_size
        _require(size > 0, f"{kind} artifact is empty")
        manifest[kind] = {
            "name": artifact.name,
            "bytes": size,
            "sha256": _sha256(artifact),
        }
    transcript_json = json.loads(artifacts["json"].read_text(encoding="utf-8"))
    _require(
        isinstance(transcript_json, list) and bool(transcript_json),
        "raw transcript JSON is not a non-empty paragraph list",
    )
    metadata = artifacts["metadata"].read_text(encoding="utf-8")
    url = plan.args[plan.args.index("--url") + 1]
    _require(
        f"Source: {url}" in metadata.splitlines(),
        "metadata does not name the YouTube URL",
    )
    _require(
        "Summary status: succeeded" in metadata, "metadata summary status is invalid"
    )
    model = re.search(r"^Claude: (\S+) \(reasoning: \w+\)$", metadata, re.MULTILINE)
    _require(
        model is not None and TEST_PROFILE in model.group(1),
        f"real summary did not use the {TEST_PROFILE} test profile",
    )
    upload = re.search(
        r"^Audio upload: complete \(([1-9]\d*) bytes\)$", metadata, re.MULTILINE
    )
    _require(upload is not None, "metadata does not confirm a complete audio upload")
    audio_upload = {"status": "complete", "bytes": int(upload.group(1))}
    manifest_path = (
        context.evidence_dir / "cases" / _slug(feature.id) / "artifacts.json"
    )
    _write_json(
        manifest_path,
        {
            "published_dir_name": published_dir.name,
            "artifacts": manifest,
            "raw_transcript_items": len(transcript_json),
            "summary_status": "succeeded",
            "audio_upload": audio_upload,
        },
    )
    return {
        "artifact_manifest": str(manifest_path),
        "artifact_count": len(manifest),
        "raw_transcript_items": len(transcript_json),
        "summary_status": "succeeded",
        "audio_upload": audio_upload,
    }


def _help_section(text: str, heading: str) -> str:
    marker = f"{heading}:\n"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("\n\n", 1)[0]


def _help_options(text: str) -> frozenset[str]:
    declarations = re.split(r"\n[Ee]xamples:\n", text, maxsplit=1)[0]
    return frozenset(
        re.findall(
            r"^  (?:-[A-Za-z], )?(--[a-z][a-z-]*)",
            declarations,
            flags=re.MULTILINE,
        )
    )


def _help_choices(text: str) -> frozenset[str]:
    positional = _help_section(text, "positional arguments")
    return frozenset(
        re.findall(r"^    ([a-z][a-z-]*)\s{2,}\S", positional, flags=re.MULTILINE)
    )


def _validate_help_version(
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
) -> dict[str, object]:
    contracts = {contract.id: contract for contract in HELP_CONTRACTS}
    observed = {}
    version = None
    for plan, (process, payload) in zip(commands, captures, strict=True):
        text = payload.get("text")
        _require(isinstance(text, str), f"{plan.id} returned no text")
        if plan.id == "version":
            _require(
                re.fullmatch(r"transcript \d+\.\d+\.\d+\n", text) is not None,
                "transcript version output is invalid",
            )
            version = text.strip().split()[-1]
            continue
        contract = contracts[plan.id]
        options = _help_options(text)
        choices = _help_choices(text)
        _require(
            options == contract.options,
            f"{plan.id} options changed: {sorted(options)}",
        )
        _require(
            choices == contract.choices,
            f"{plan.id} choices changed: {sorted(choices)}",
        )
        _require(process.exit_code == 0, f"{plan.id} did not exit successfully")
        observed[plan.id] = {
            "options": sorted(options),
            "choices": sorted(choices),
        }
    _require(version is not None, "transcript version was not observed")
    return {"version": version, "help": observed}


def _validate_structured_recovery(
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
) -> dict[str, object]:
    """Each invalid run answers one error naming what failed, the command that
    fixes it when one exists, and the help of the command it came from."""
    expected_errors = {
        "invalid-usage": "unrecognized arguments: --unknown-option",
        "invalid-source": "Invalid YouTube URL: https://example.com/video; fix: ",
        "invalid-configuration": ("; fix: transcript list models --provider codex"),
    }
    observations = {}
    for plan, (_process, payload) in zip(commands, captures, strict=True):
        errors = payload.get("errors")
        _require(
            isinstance(errors, list)
            and len(errors) == 1
            and isinstance(errors[0], str),
            f"{plan.id} returned no single error",
        )
        (error,) = errors
        _require(
            expected_errors[plan.id] in error, f"{plan.id} returned the wrong error"
        )
        _require(
            payload.get("help") == "transcript run youtube --help",
            f"{plan.id} returned no help command",
        )
        if plan.id == "invalid-configuration":
            _require("--list-models" not in error, "model recovery uses legacy syntax")
        _require(
            plan.output_dir is not None and not plan.output_dir.exists(),
            f"{plan.id} created its output directory",
        )
        observations[plan.id] = {"error": error, "help": payload["help"]}
    return {"errors": observations}


def _validate_transcript_only(
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
) -> dict[str, object]:
    plans = {}
    for plan, (_process, payload) in zip(commands, captures, strict=True):
        _require(payload.get("ok") is True, f"{plan.id} did not report success")
        _require(plan.output_dir is not None, f"{plan.id} has no isolated output")
        _require(
            Path(str(payload.get("output_dir"))).resolve() == plan.output_dir.resolve(),
            f"{plan.id} reported the wrong output directory",
        )
        _require(
            not plan.output_dir.exists(), f"{plan.id} created its output directory"
        )
        summary = payload.get("summary")
        _require(
            summary
            == {
                "enabled": False,
                "profile": None,
                "provider": None,
                "model": None,
                "effort": None,
                "prompt": None,
            },
            f"{plan.id} did not disable summary settings",
        )
        source = payload.get("source")
        _require(isinstance(source, dict), f"{plan.id} returned no source")
        if plan.id == "youtube-transcript-only":
            _require(source.get("kind") == "youtube", "YouTube source is invalid")
            expected_timeout = 42.0
        else:
            _require(source.get("kind") == "zoom", "Zoom source is invalid")
            meeting = Path(plan.args[plan.args.index("--path") + 1]).resolve()
            _require(
                Path(str(source.get("path"))).resolve() == meeting,
                "Zoom folder is invalid",
            )
            _require(
                Path(str(source.get("audio"))).resolve() == meeting / "audio_only.m4a",
                "Zoom audio is invalid",
            )
            expected_timeout = 43.0
        _require(
            payload.get("timeout_seconds") == expected_timeout,
            f"{plan.id} did not resolve its timeout override",
        )
        plans[plan.id] = {
            "source": source,
            "summary": summary,
            "timeout_seconds": expected_timeout,
        }
    return {"plans": plans}


def validate_feature(
    feature: FeatureSpec,
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
    context: RunContext,
) -> dict[str, object]:
    """Validate one public behavior after all of its commands are captured."""
    if feature.probe == "help-version":
        return _validate_help_version(commands, captures)
    if feature.probe == "structured-recovery":
        return _validate_structured_recovery(commands, captures)
    if feature.probe == "transcript-only-dry-run":
        return _validate_transcript_only(commands, captures)
    if feature.probe == "prompts":
        process, payload = captures[0]
        prompts = payload.get("prompts")
        _require(process.exit_code == 0, "prompt discovery failed")
        _require(isinstance(prompts, list), "prompt discovery returned no list")
        discovered = {
            prompt.get("name"): prompt.get("input_kind")
            for prompt in prompts
            if isinstance(prompt, dict)
        }
        expected = {
            "follow_along_note": "plain",
            "short_summary": "plain",
            "summary_with_quotes": "timestamped",
        }
        _require(
            all(
                discovered.get(name) == input_kind
                for name, input_kind in expected.items()
            ),
            "prompt discovery is missing a bundled prompt or input kind",
        )
        return {"prompts": expected}
    if feature.probe == "models":
        providers = []
        for process, payload in captures:
            _require(process.exit_code == 0, "model discovery failed")
            provider = payload.get("provider")
            models = payload.get("models")
            _require(
                provider in {"claude", "codex", "openrouter"},
                "model provider is invalid",
            )
            _require(isinstance(models, list) and bool(models), "model list is empty")
            _require(payload.get("default") in models, "default model is not suggested")
            providers.append(provider)
        _require(
            set(providers) == {"claude", "codex", "openrouter"},
            "provider coverage is incomplete",
        )
        return {"providers": sorted(providers)}
    if feature.probe == "profiles":
        process, payload = captures[0]
        _require(process.exit_code == 0, "profile discovery failed")
        _require(payload.get("default") == "opus", "default profile is invalid")
        profiles = payload.get("profiles")
        _require(isinstance(profiles, list) and bool(profiles), "profile list is empty")
        for profile in profiles:
            _require(
                isinstance(profile, dict)
                and all(
                    isinstance(profile.get(key), str) and bool(profile[key].strip())
                    for key in ("name", "provider", "model", "effort")
                ),
                f"profile has missing or empty fields: {profile!r}",
            )
        names = [profile["name"] for profile in profiles]
        _require(len(set(names)) == len(names), f"duplicate profile names: {names!r}")
        _require(payload["default"] in names, "default profile is not listed")
        _require(TEST_PROFILE in names, f"test profile is not listed: {TEST_PROFILE}")
        return {"default": payload["default"], "profiles": names}
    if feature.probe in {"doctor-youtube", "doctor-zoom"}:
        return _validate_doctor(feature, *captures[0])
    if feature.probe in {"youtube-dry-run-summary", "zoom-dry-run"}:
        return _validate_dry_run(feature, commands[0], *captures[0])
    if feature.probe == "youtube-real-summary":
        return _validate_e2e(feature, commands[0], *captures[0], context)
    raise AssertionError(f"Unhandled probe: {feature.probe}")


def run_feature(feature: FeatureSpec, context: RunContext) -> dict[str, object]:
    evidence = context.evidence_dir / "cases" / _slug(feature.id)
    try:
        commands = build_commands(feature, context)
        captures = tuple(capture_command(feature, plan, context) for plan in commands)
        observations = validate_feature(feature, commands, captures, context)
    except (
        AssertionError,
        OSError,
        TypeError,
        VerificationError,
        json.JSONDecodeError,
    ) as error:
        result: dict[str, object] = {
            "id": feature.id,
            "title": feature.title,
            "verdict": "FAIL",
            "paid": feature.paid,
            "evidence": str(evidence),
            "error": {
                "code": (
                    error.code
                    if isinstance(error, VerificationError)
                    else "verification_failed"
                ),
                "message": str(error),
            },
        }
    else:
        result = {
            "id": feature.id,
            "title": feature.title,
            "verdict": "PASS",
            "paid": feature.paid,
            "evidence": str(evidence),
            "observations": observations,
        }
    _write_json(evidence / "result.json", result)
    return result


def create_scratch(run_id: str) -> Path:
    scratch = Path(tempfile.mkdtemp(prefix=f"verify-transcript-{run_id}-")).resolve()
    (scratch / RUN_MARKER).write_text(run_id + "\n", encoding="utf-8")
    return scratch


def safe_cleanup(scratch: Path, run_id: str) -> None:
    """Remove only the marked temporary directory created by this run."""
    resolved = scratch.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    marker = resolved / RUN_MARKER
    if not _is_within(resolved, temp_root):
        raise VerificationError(
            "unsafe_cleanup",
            f"Refusing cleanup outside the system temporary directory: {resolved}",
            "Remove the scratch directory manually after checking its contents.",
        )
    if not resolved.name.startswith(f"verify-transcript-{run_id}-"):
        raise VerificationError(
            "unsafe_cleanup",
            f"Refusing cleanup of an unexpected directory name: {resolved.name}",
            "Remove the scratch directory manually after checking its contents.",
        )
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != run_id:
        raise VerificationError(
            "unsafe_cleanup",
            f"Refusing cleanup without the current run marker: {resolved}",
            "Remove the scratch directory manually after checking its contents.",
        )
    shutil.rmtree(resolved)


def default_evidence_root() -> Path:
    state_home = Path(os.getenv("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_home / EVIDENCE_NAMESPACE / "runs"


def new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def run_verification(
    selected: tuple[FeatureSpec, ...],
    located: LocatedSkill,
    evidence_root: Path,
    allow_paid: bool,
    youtube_url: str,
) -> dict[str, object]:
    """Run selected features, clean scratch, and retain the final report."""
    run_id = new_run_id()
    evidence_dir = evidence_root.expanduser().resolve() / run_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    try:
        scratch = create_scratch(run_id)
        context = RunContext(
            run_id=run_id,
            located=located,
            scratch_dir=scratch,
            evidence_dir=evidence_dir,
            allow_paid=allow_paid,
            youtube_url=youtube_url,
        )
        results: list[dict[str, object]] = []
        cleanup_error: VerificationError | None = None
        try:
            for feature in selected:
                results.append(run_feature(feature, context))
                log.info(f"{results[-1]['verdict']} {feature.id}")
        finally:
            try:
                safe_cleanup(scratch, run_id)
            except VerificationError as error:
                cleanup_error = error
        passed = sum(result["verdict"] == "PASS" for result in results)
        failed = len(results) - passed
        if cleanup_error is not None:
            failed += 1
        ok = failed == 0
        report: dict[str, object] = {
            "schema_version": 1,
            "ok": ok,
            "verdict": "PASS" if ok else "FAIL",
            "run_id": run_id,
            "layout": located.layout,
            "transcript_skill_dir": str(located.directory),
            "paid_authorized": allow_paid,
            "evidence_dir": str(evidence_dir),
            "counts": {"passed": passed, "failed": failed},
            "scratch_removed": not scratch.exists(),
            "features": results,
        }
        if cleanup_error is not None:
            report["cleanup_error"] = {
                "code": cleanup_error.code,
                "message": cleanup_error.message,
                "hint": cleanup_error.hint,
            }
        _write_json(evidence_dir / "result.json", report)
        return report
    except (KeyboardInterrupt, OSError) as error:
        if isinstance(error, KeyboardInterrupt):
            code = getattr(error, "code", INTERRUPTED)
            message = "interrupted" if code == INTERRUPTED else "terminated"
        else:
            code = 1
            message = f"{error}; {DOCTOR_HINT}"
        failure = ScriptError(
            message,
            report={
                "files": sorted(
                    str(path) for path in evidence_dir.rglob("*") if path.is_file()
                )
            },
        )
        failure.code = code
        raise failure from error


def feature_documents(skill_dir: Path, query: str | None) -> list[dict[str, str]]:
    """Search the checked-in Feature Map by filename, title, or body text."""
    normalized = query.casefold() if query else None
    documents = []
    for path in sorted((skill_dir / "features").glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        haystack = f"{path.stem}\n{text}".casefold()
        if normalized and normalized not in haystack:
            continue
        lines = text.splitlines()
        title = next((line[2:] for line in lines if line.startswith("# ")), path.stem)
        summary = next(
            (
                line
                for line in lines[1:]
                if line and not line.startswith("#") and not line.startswith("<!--")
            ),
            "",
        )
        documents.append(
            {
                "id": path.stem,
                "title": title,
                "summary": summary,
                "path": str(Path("features") / path.name),
            }
        )
    return documents


def feature_entries(skill_dir: Path, query: str | None) -> list[dict[str, object]]:
    """Return exact selectable feature IDs with their Feature Map pages."""
    normalized = query.casefold() if query else None
    entries = []
    for feature in FEATURES:
        page_paths = [Path("features") / f"{area}.md" for area in feature.areas]
        missing = [
            page_path
            for page_path in page_paths
            if not (skill_dir / page_path).is_file()
        ]
        if missing:
            raise OSError("Missing Feature Map pages: " + ", ".join(map(str, missing)))
        haystack = "\n".join((feature.id, feature.title, *feature.areas)).casefold()
        if normalized and normalized not in haystack:
            continue
        paid_flag = " --allow-paid" if feature.paid else ""
        entries.append(
            {
                "id": feature.id,
                "title": feature.title,
                "default": feature.default,
                "paid": feature.paid,
                "areas": list(feature.areas),
                "pages": [str(page_path) for page_path in page_paths],
                "verify_command": (
                    f"verify-transcript verify --feature {feature.id}{paid_flag}"
                ),
            }
        )
    if normalized and not entries:
        documents = feature_documents(skill_dir, None)
        matching_areas = {
            document["id"]
            for document in documents
            if normalized
            in "\n".join(
                (document["id"], document["title"], document["summary"])
            ).casefold()
        }
        if not matching_areas:
            matching_areas = {
                document["id"] for document in feature_documents(skill_dir, query)
            }
        matching_ids = {
            feature.id
            for feature in FEATURES
            if matching_areas.intersection(feature.areas)
        }
        return [
            entry
            for entry in feature_entries(skill_dir, None)
            if entry["id"] in matching_ids
        ]
    return entries


def doctor_checks(skill_dir: Path) -> list[dict[str, str]]:
    """Each check of the verifier's own setup; a failed one names its fix."""
    checks = []
    try:
        located = locate_transcript_skill(skill_dir)
    except VerificationError as error:
        checks.append(
            {
                "name": "transcript_skill",
                "status": "fail",
                "message": error.message.rstrip("."),
                "fix": f"install transcript beside verify-transcript. {error.hint}",
            }
        )
    else:
        checks.append(
            {
                "name": "transcript_skill",
                "status": "pass",
                "message": f"Found {located.layout} layout at {located.directory}",
            }
        )
    uv_path = shutil.which("uv")
    if uv_path:
        checks.append(
            {"name": "uv", "status": "pass", "message": f"uv is at {uv_path}"}
        )
    else:
        checks.append(
            {
                "name": "uv",
                "status": "fail",
                "message": "uv is not on PATH",
                "fix": "install uv: https://docs.astral.sh/uv/getting-started/installation/",
            }
        )
    feature_dir = skill_dir / "features"
    missing = [
        area for area in FEATURE_AREAS if not (feature_dir / f"{area}.md").is_file()
    ]
    if missing:
        checks.append(
            {
                "name": "feature_map",
                "status": "fail",
                "message": "Missing feature pages: " + ", ".join(missing),
                "fix": "reinstall the verify-transcript skill",
            }
        )
    else:
        checks.append(
            {
                "name": "feature_map",
                "status": "pass",
                "message": f"All {len(FEATURE_AREAS)} feature pages are available",
            }
        )
    return checks


def run_doctor(skill_dir: Path) -> dict[str, object]:
    """List every check with -v, and fail with one error per failed check."""
    checks = doctor_checks(skill_dir)
    for check in checks:
        log.info(f"[{check['status'].upper()}] {check['name']}: {check['message']}")
    failed = [check for check in checks if check["status"] == "fail"]
    if failed:
        raise ScriptError(
            *(
                f"{check['name']}: {check['message']}; fix: {check['fix']}"
                for check in failed
            )
        )
    return {}


def search_features(skill_dir: Path, query: str | None) -> dict[str, object]:
    """The selectable features and Feature Map pages that match `query`."""
    entries = feature_entries(skill_dir, query)
    documents = feature_documents(skill_dir, query)
    if query is not None and not (entries or documents):
        raise ScriptError(
            f"no feature or Feature Map page matches {query!r}; "
            "run 'verify-transcript features' to list them all"
        )
    return {"features": entries, "documents": documents}


def run_verify(args: argparse.Namespace, skill_dir: Path) -> dict[str, object]:
    """Run the selected features and answer the run's result.json; a failed
    feature is one error, with the command that reruns it."""
    selected = select_features(tuple(args.feature), args.all, args.allow_paid)
    paid_selected = any(feature.paid for feature in selected)
    if args.youtube_url != CANONICAL_YOUTUBE_URL and not paid_selected:
        raise VerificationError(
            "unused_option",
            "--youtube-url only applies to a selected paid YouTube feature.",
            "Select youtube.real-summary and add --allow-paid, or omit --youtube-url.",
            exit_code=USAGE,
        )
    report = run_verification(
        selected=selected,
        located=locate_transcript_skill(skill_dir),
        evidence_root=args.evidence_root,
        allow_paid=args.allow_paid,
        youtube_url=args.youtube_url,
    )
    result = {"file": str(Path(str(report["evidence_dir"])) / "result.json")}
    if report["ok"]:
        return result
    paid_options = f" --allow-paid --youtube-url {shlex.quote(args.youtube_url)}"
    errors = [
        f"{feature['id']}: {feature['error']['message']}; rerun: verify-transcript "
        f"verify --feature {feature['id']}{paid_options if feature['paid'] else ''}"
        for feature in report["features"]
        if feature["verdict"] == "FAIL"
    ]
    if cleanup := report.get("cleanup_error"):
        errors.append(f"cleanup: {cleanup['message']}; {cleanup['hint']}")
    raise ScriptError(*errors, report=result)


def build_parser() -> Parser:
    parser = Parser(
        prog="verify-transcript",
        exit_codes=EXIT_CODES,
        description=(
            "Verify transcript through its public CLI and retain evidence. "
            "Each command answers in one JSON line."
        ),
        epilog="""examples:
  verify-transcript verify
  verify-transcript features zoom
  verify-transcript verify --feature youtube.real-summary --allow-paid""",
    )
    parser.add_argument(
        "--version", action="version", version=f"verify-transcript {__version__}"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser(
        "doctor", help="Check that this verifier can run", exit_codes=EXIT_CODES
    )
    features = commands.add_parser(
        "features", help="Search the transcript Feature Map", exit_codes=EXIT_CODES
    )
    features.add_argument("query", nargs="?", help="Case-insensitive search text")

    verify = commands.add_parser(
        "verify", help="Run public-interface verification", exit_codes=EXIT_CODES
    )
    verify.add_argument("--feature", action="append", default=[], metavar="ID")
    verify.add_argument(
        "--all", action="store_true", help="Select free and paid features"
    )
    verify.add_argument(
        "--allow-paid",
        action="store_true",
        help="Authorize paid calls already selected with --feature or --all",
    )
    verify.add_argument(
        "--youtube-url",
        default=CANONICAL_YOUTUBE_URL,
        metavar="URL",
        help="Override the canonical URL for the selected real YouTube feature",
    )
    verify.add_argument(
        "--evidence-root",
        type=Path,
        default=default_evidence_root(),
        metavar="DIR",
        help="Parent for retained per-run evidence",
    )
    return parser


def work(args: argparse.Namespace) -> dict[str, object]:
    """Run the command `args` names and return the fields beside `ok`."""
    skill_dir = verify_skill_dir()
    try:
        if args.command == "doctor":
            return run_doctor(skill_dir)
        if args.command == "features":
            return search_features(skill_dir, args.query)
        return run_verify(args, skill_dir)
    except VerificationError as error:
        failure = UsageError if error.exit_code == USAGE else ScriptError
        raise failure(error.line) from error
    except OSError as error:
        raise ScriptError(f"{error}; {DOCTOR_HINT}") from error


def main(argv: list[str] | None = None) -> int:
    """Run one command and answer it in one JSON line; return its exit code."""
    argv = list(sys.argv[1:] if argv is None else argv) or ["--help"]
    try:
        return run_script(build_parser(), work, argv)
    except SystemExit as stop:
        # --version prints its line and exits, as --help does
        return stop.code if isinstance(stop.code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())

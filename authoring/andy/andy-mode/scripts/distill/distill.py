# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tiktoken",
# ]
# ///
"""Distill a local text file through a named prompt using Claude, Codex, or OpenCode.

Reads an input file and a prompt file, runs the prompt against the selected
LLM provider CLI, writes the distilled output to a timestamped folder beside
the input, and answers in one JSON line with the path of the distilled file.

See ``help.md`` for the full user-facing documentation. This script is
intentionally thin: prompt content lives in the ``distill-prompt`` route of
andy-mode, and this tool resolves a named stem to its ``prompt.md`` file.
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
    print(
        json.dumps(body, separators=(",", ":")), file=sys.stderr if code else sys.stdout
    )
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


def usage_error(message: str) -> NoReturn:
    raise UsageError(message)


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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print progress and step details on stderr",
    )
    if debug:
        parser.add_argument(
            "--debug",
            action="store_true",
            help=f"print internals, timings, and tracebacks on stderr; also {debug}=1",
        )
    if given(argv, "-h", "--help", parser=parser):
        parser.print_help()
        return 0

    # Parser.error, in the pasted cli block, prints usage errors itself;
    # raising sends this one through answer_failure()
    parser.error = usage_error
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
    if isinstance(error, UsageError):
        hints["help"] = f"{parser.prog} --help"
    elif isinstance(error, TemporaryError) and messages:
        hints["retry"] = command
    elif rerun:
        hints["rerun"] = f"{command} --debug"
    if error.detail:
        print(error.detail, file=sys.stderr)
    return answer(error.code, {"errors": messages, **error.report, **hints})


# <<< cli-block

import platform
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import tiktoken

if TYPE_CHECKING:
    from _typeshed import SupportsWrite

__version__ = "1.0.0"

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
ANDY_DIR = SCRIPT_DIR.parent.parent
HELP_MD_PATH = ANDY_DIR / "references" / "distill" / "help.md"
PROMPTS_DIR = ANDY_DIR / "references" / "distill-prompt"

PROVIDER_CLAUDE = "claude"
PROVIDER_CODEX = "codex"
PROVIDER_OPENCODE = "opencode"
VALID_PROVIDERS: tuple[str, ...] = (
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
    PROVIDER_OPENCODE,
)
DEFAULT_PROVIDER = PROVIDER_CLAUDE

VALID_CLAUDE_MODELS: tuple[str, ...] = (
    "claude-opus-4-6",
    "claude-sonnet-4-6",
)
DEFAULT_CLAUDE_MODEL = "claude-opus-4-6"

# Models that default to 'low' effort (faster, cheaper)
SONNET_MODELS: tuple[str, ...] = ("claude-sonnet-4-6",)

VALID_CODEX_MODELS: tuple[str, ...] = ("gpt-5.4",)
DEFAULT_CODEX_MODEL = "gpt-5.4"

VALID_OPENCODE_MODELS: tuple[str, ...] = (
    "1-glm",
    "2-luna",
    "3-sol",
    "4-astra",
    "5-qwen",
)
DEFAULT_OPENCODE_MODEL = "1-glm"

CANONICAL_EFFORTS: tuple[str, ...] = ("low", "medium", "high", "max")
DEFAULT_EFFORT = "high"
DEFAULT_PROMPT = "follow_along_note"

# Canonical -> vendor ETL
EFFORT_ETL: dict[str, dict[str, str]] = {
    PROVIDER_CLAUDE: {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "max": "max",
    },
    PROVIDER_CODEX: {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "max": "xhigh",
    },
}

# Safe input-token limits per provider (input + prompt combined).
CONTEXT_LIMITS: dict[str, int] = {
    PROVIDER_CLAUDE: 600_000,
    PROVIDER_CODEX: 450_000,
    PROVIDER_OPENCODE: 250_000,
}

LLM_CLI_TIMEOUT_SECONDS = 600  # 10 minutes
LLM_MAX_RETRIES = 3

# Exit codes
EXIT_GENERIC_ERROR = 1
EXIT_INPUT_NOT_FOUND = 3
EXIT_PROMPT_NOT_FOUND = 4
EXIT_PROVIDER_MISSING = 5
EXIT_LLM_FAILED = 6
EXIT_OUTPUT_NOT_WRITABLE = 7
EXIT_CODES = exit_codes(
    {
        EXIT_INPUT_NOT_FOUND: "input file missing or unreadable",
        EXIT_PROMPT_NOT_FOUND: "unknown prompt stem",
        EXIT_PROVIDER_MISSING: "provider CLI not on PATH",
        EXIT_LLM_FAILED: "LLM call failed, or the input is too large",
        EXIT_OUTPUT_NOT_WRITABLE: "output folder not writable",
    }
)

# Overhead tokens for the user-message framing ("Based on this content:\n\n")
USER_MESSAGE_OVERHEAD = "Based on this content:\n\n"

log = logging.getLogger("distill")


# -------------------------------------------------------------------------
# Errors
# -------------------------------------------------------------------------


class DistillError(ScriptError):
    """Base class for distill-specific failures; `code` is the exit code."""

    code = EXIT_GENERIC_ERROR


class InputFileError(DistillError):
    code = EXIT_INPUT_NOT_FOUND


class PromptFileError(DistillError):
    code = EXIT_PROMPT_NOT_FOUND


class ProviderMissingError(DistillError):
    code = EXIT_PROVIDER_MISSING


class LLMCallError(DistillError):
    code = EXIT_LLM_FAILED


class OutputDirError(DistillError):
    code = EXIT_OUTPUT_NOT_WRITABLE


# -------------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedPlan:
    """Fully-resolved inputs ready for execution or dry-run display."""

    input_path: Path
    input_text: str
    input_tokens: int
    prompt_path: Path
    prompt_text: str
    prompt_name: str
    provider: str
    provider_cli_path: Path
    model: str
    effort_canonical: str
    effort_vendor: str
    output_parent: Path
    slug: str
    run_folder_name: str
    run_folder_path: Path


# -------------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------------


def retry_request[T](
    func: Callable[[], T],
    *,
    max_attempts: int = LLM_MAX_RETRIES,
    initial_delay: float = 1.0,
) -> T:
    """Execute ``func`` with exponential backoff retry logic.

    Args:
        func: Zero-argument callable to execute.
        max_attempts: Maximum number of tries (must be >= 1).
        initial_delay: Seconds to wait before the first retry.

    Returns:
        The return value of ``func`` on the first successful call.

    Raises:
        Exception: Re-raises the last exception after all attempts are exhausted.
    """
    delay = initial_delay
    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1:
                log.info("retry %d/%d", attempt, max_attempts)
            return func()
        except Exception:
            if attempt == max_attempts:
                log.info("failed after %d attempts", max_attempts)
                raise
            log.info("failed, retrying in %ss", delay)
            time.sleep(delay)
            delay *= 2

    raise RuntimeError("retry_request called with max_attempts < 1")


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken's cl100k_base encoding.

    This is OpenAI-native. For Claude it is an approximation, typically
    within 5-10% of anthropic's own count.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def ensure_cli_available(command_name: str) -> Path:
    """Return the resolved path to ``command_name``, or raise ProviderMissingError."""
    path = shutil.which(command_name)
    if not path:
        raise ProviderMissingError(
            f"Required CLI '{command_name}' was not found on PATH. "
            f"Install it and try again."
        )
    return Path(path)


def open_folder_in_finder(path: Path) -> None:
    """Open a folder in Finder on macOS; no-op elsewhere."""
    if platform.system() != "Darwin":
        return
    subprocess.run(["open", str(path)], check=False)


# -------------------------------------------------------------------------
# Help rendering (custom --help action)
# -------------------------------------------------------------------------


class DistillParser(Parser):
    """The shared parser, whose --help renders help.md instead of argparse's help.

    It uses glow when installed, and plain Markdown otherwise.
    """

    def print_help(self, file: SupportsWrite[str] | None = None) -> None:
        if not HELP_MD_PATH.is_file():
            super().print_help(file)
            return
        if file is None and shutil.which("glow"):
            sys.stdout.flush()
            if subprocess.run(["glow", str(HELP_MD_PATH)], check=False).returncode == 0:
                return
        (file or sys.stdout).write(HELP_MD_PATH.read_text(encoding="utf-8"))


# -------------------------------------------------------------------------
# Argument parsing
# -------------------------------------------------------------------------


def build_parser() -> DistillParser:
    parser = DistillParser(
        prog="distill.py",
        description="Distill a local text file through a named prompt.",
        exit_codes=EXIT_CODES,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"distill {__version__}",
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=str,
        help="Path to the local text file to distill.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        metavar="STEM",
        help=f"Prompt stem from distill-prompt (default: {DEFAULT_PROMPT}).",
    )

    parser.add_argument(
        "--provider",
        choices=VALID_PROVIDERS,
        default=None,
        help=f"LLM provider (default: {DEFAULT_PROVIDER}).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        metavar="MODEL",
        help=(
            f"Model name. Defaults: claude={DEFAULT_CLAUDE_MODEL}, "
            f"codex={DEFAULT_CODEX_MODEL}, opencode={DEFAULT_OPENCODE_MODEL}."
        ),
    )
    parser.add_argument(
        "--effort",
        choices=CANONICAL_EFFORTS,
        default=None,
        help=(f"Reasoning effort. Defaults: {DEFAULT_EFFORT} (low for Sonnet models)."),
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        metavar="DIR",
        help="Parent directory for the timestamped run folder.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the output folder in Finder on macOS.",
    )

    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available distill prompts and exit.",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List supported models and exit.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve all inputs and answer the plan without calling the LLM.",
    )

    return parser


def check_args(args: argparse.Namespace) -> None:
    """Reject argument combinations the parser cannot catch."""
    provider = args.provider or DEFAULT_PROVIDER

    if provider == PROVIDER_OPENCODE and args.effort is not None:
        raise UsageError("--effort is not supported with --provider opencode")

    # Validate: if not using a discovery command, input is required
    if not args.list_models and not args.list_prompts and not args.input:
        raise UsageError(
            "missing positional argument 'input' "
            "(or use --list-prompts / --list-models)"
        )


# -------------------------------------------------------------------------
# Resolution helpers
# -------------------------------------------------------------------------


def resolve_input_file(raw: str) -> tuple[Path, str]:
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise InputFileError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise InputFileError(f"Input path is not a regular file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InputFileError(
            f"Input file is not valid UTF-8 text: {path} ({exc})"
        ) from exc
    except OSError as exc:
        raise InputFileError(f"Cannot read input file {path}: {exc}") from exc
    return path, text


def normalize_prompt_stem(raw: str) -> str:
    """Normalize a user-facing prompt stem to canonical underscore form."""
    stem = raw.strip().lower()
    stem = stem.removesuffix(".md")
    stem = stem.replace("-", "_")
    return stem


def resolve_prompt(raw: str) -> tuple[Path, str, str]:
    """Resolve a prompt stem to ``references/distill-prompt/<folder>/prompt.md``."""
    prompt_name = normalize_prompt_stem(raw)
    prompt_dir = PROMPTS_DIR / prompt_name.replace("_", "-")
    prompt_path = prompt_dir / "prompt.md"

    if not prompt_path.exists() or not prompt_path.is_file():
        raise PromptFileError(
            f"Unknown prompt stem: {raw}. Run with --list-prompts to see the list."
        )

    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise PromptFileError(f"Cannot read prompt file {prompt_path}: {exc}") from exc

    return prompt_path, prompt_text, prompt_name


def resolve_model(provider: str, raw_model: str | None) -> str:
    if provider == PROVIDER_CLAUDE:
        model = (raw_model or DEFAULT_CLAUDE_MODEL).strip()
        if model not in VALID_CLAUDE_MODELS:
            raise UsageError(
                (
                    f"Invalid claude model: {model}. "
                    f"Valid: {', '.join(VALID_CLAUDE_MODELS)}. "
                    f"Run with --list-models --provider claude to see the list."
                ),
            )
        return model

    if provider == PROVIDER_CODEX:
        model = (raw_model or DEFAULT_CODEX_MODEL).strip()
        if model not in VALID_CODEX_MODELS:
            raise UsageError(
                (
                    f"Invalid codex model: {model}. "
                    f"Valid: {', '.join(VALID_CODEX_MODELS)}. "
                    f"Run with --list-models --provider codex to see the list."
                ),
            )
        return model

    model = (raw_model or DEFAULT_OPENCODE_MODEL).strip()
    if model not in VALID_OPENCODE_MODELS:
        raise UsageError(
            (
                f"Invalid opencode model: {model}. "
                f"Valid: {', '.join(VALID_OPENCODE_MODELS)}. "
                f"Run with --list-models --provider opencode to see the list."
            ),
        )
    return model


def translate_effort(provider: str, canonical: str) -> str:
    return EFFORT_ETL[provider][canonical]


def check_context_size(provider: str, input_text: str, prompt_text: str) -> int:
    input_tokens = count_tokens(input_text)
    prompt_tokens = count_tokens(prompt_text)
    overhead_tokens = count_tokens(USER_MESSAGE_OVERHEAD)
    total = input_tokens + prompt_tokens + overhead_tokens

    limit = CONTEXT_LIMITS[provider]
    if total > limit:
        raise LLMCallError(
            f"Input too large for {provider}: {total:,} tokens "
            f"(input {input_tokens:,} + prompt {prompt_tokens:,} "
            f"+ overhead {overhead_tokens:,}) exceeds safe limit "
            f"of {limit:,}. Reduce input size or split the file."
        )
    return input_tokens


def derive_slug(input_path: Path) -> str:
    """Input filename stem, with minimal sanitization for filesystem safety."""
    stem = input_path.stem
    # Replace path separators and control chars with underscores; keep unicode.
    sanitized = "".join(
        "_" if ch in ("/", "\\", ":", "\n", "\r", "\t") else ch for ch in stem
    )
    sanitized = sanitized.strip()
    return sanitized or "input"


def make_run_folder_path(
    output_parent: Path, slug: str, prompt_name: str
) -> tuple[Path, str]:
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    run_folder_name = f"{slug}_{timestamp}_{prompt_name}"
    return output_parent / run_folder_name, run_folder_name


def validate_output_parent(parent: Path, *, create: bool) -> Path:
    """Return a resolved, writable output parent directory.

    When ``create`` is True (real runs), missing directories are created
    and a probe file verifies writability. When ``create`` is False
    (dry-run), the filesystem is not mutated: writability is inferred
    from ``os.access`` on the nearest existing ancestor.
    """
    parent = parent.expanduser().resolve()

    if parent.exists():
        if not parent.is_dir():
            raise OutputDirError(f"Output parent is not a directory: {parent}")
        if create:
            probe = parent / ".distill-write-probe"
            try:
                probe.touch()
                probe.unlink()
            except OSError as exc:
                raise OutputDirError(
                    f"Output parent is not writable: {parent} ({exc})"
                ) from exc
        else:
            if not os.access(parent, os.W_OK):
                raise OutputDirError(f"Output parent is not writable: {parent}")
        return parent

    # Parent does not exist yet
    if create:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputDirError(
                f"Cannot create output parent {parent}: {exc}"
            ) from exc
        return parent

    # Dry-run: walk up to the nearest existing ancestor and check it
    ancestor = parent.parent
    while not ancestor.exists():
        if ancestor == ancestor.parent:  # reached filesystem root
            raise OutputDirError(
                f"Cannot create output parent {parent}: no existing ancestor"
            )
        ancestor = ancestor.parent
    if not ancestor.is_dir() or not os.access(ancestor, os.W_OK):
        raise OutputDirError(
            f"Cannot create output parent {parent}: ancestor {ancestor} not writable"
        )
    return parent


def build_plan(args: argparse.Namespace) -> ResolvedPlan:
    input_path, input_text = resolve_input_file(args.input)
    prompt_path, prompt_text, prompt_name = resolve_prompt(args.prompt)

    provider: str = args.provider or DEFAULT_PROVIDER
    provider_cli_path = ensure_cli_available(provider)

    model = resolve_model(provider, args.model)

    # Determine effort: use explicit value, or default based on model.
    if provider == PROVIDER_OPENCODE:
        effort_canonical = "agent-defined"
        effort_vendor = "agent-defined"
    elif args.effort is not None:
        effort_canonical = args.effort
        effort_vendor = translate_effort(provider, effort_canonical)
    elif model in SONNET_MODELS:
        effort_canonical = "low"
        effort_vendor = translate_effort(provider, effort_canonical)
    else:
        effort_canonical = DEFAULT_EFFORT
        effort_vendor = translate_effort(provider, effort_canonical)

    input_tokens = check_context_size(provider, input_text, prompt_text)

    create_output_dir = not bool(args.dry_run)
    if args.output_dir:
        output_parent = validate_output_parent(
            Path(args.output_dir), create=create_output_dir
        )
    else:
        output_parent = validate_output_parent(
            input_path.parent, create=create_output_dir
        )

    slug = derive_slug(input_path)
    run_folder_path, run_folder_name = make_run_folder_path(
        output_parent, slug, prompt_name
    )

    return ResolvedPlan(
        input_path=input_path,
        input_text=input_text,
        input_tokens=input_tokens,
        prompt_path=prompt_path,
        prompt_text=prompt_text,
        prompt_name=prompt_name,
        provider=provider,
        provider_cli_path=provider_cli_path,
        model=model,
        effort_canonical=effort_canonical,
        effort_vendor=effort_vendor,
        output_parent=output_parent,
        slug=slug,
        run_folder_name=run_folder_name,
        run_folder_path=run_folder_path,
    )


# -------------------------------------------------------------------------
# Discovery commands
# -------------------------------------------------------------------------


def list_models(provider_filter: str | None) -> dict[str, list[str]]:
    """Each provider's models with its default first, or only `provider_filter`'s."""
    catalog = (
        (PROVIDER_CLAUDE, VALID_CLAUDE_MODELS, DEFAULT_CLAUDE_MODEL),
        (PROVIDER_CODEX, VALID_CODEX_MODELS, DEFAULT_CODEX_MODEL),
        (PROVIDER_OPENCODE, VALID_OPENCODE_MODELS, DEFAULT_OPENCODE_MODEL),
    )
    return {
        provider: [default, *(model for model in models if model != default)]
        for provider, models, default in catalog
        if provider_filter in (None, provider)
    }


def list_prompt_names() -> list[str]:
    prompt_names: list[str] = []
    for child in sorted(PROMPTS_DIR.iterdir()):
        if not child.is_dir():
            continue
        if (child / "prompt.md").is_file():
            prompt_names.append(child.name.replace("-", "_"))
    return prompt_names


# -------------------------------------------------------------------------
# Dry-run answer
# -------------------------------------------------------------------------


def dry_run_answer(plan: ResolvedPlan) -> dict[str, Any]:
    """The resolved plan, and the file a real run would write."""
    return {
        "file": str(plan.run_folder_path / f"{plan.slug}_{plan.prompt_name}.md"),
        "prompt": plan.prompt_name,
        "prompt_file": str(plan.prompt_path),
        "provider": plan.provider,
        "model": plan.model,
        "effort": plan.effort_canonical,
        "input_tokens": plan.input_tokens,
    }


# -------------------------------------------------------------------------
# Provider callers
# -------------------------------------------------------------------------


def run_claude(
    plan: ResolvedPlan,
    output_file: Path,
) -> dict[str, int | str]:
    """Invoke the claude CLI and write the distilled output to ``output_file``.

    Returns a dict of usage stats for meta.yml.
    """
    user_message = f"{USER_MESSAGE_OVERHEAD}{plan.input_text}"

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "claude",
                "-p",
                "--dangerously-skip-permissions",
                "--model",
                plan.model,
                "--effort",
                plan.effort_vendor,
                "--tools",
                "",
                "--output-format",
                "json",
                "--system-prompt",
                plan.prompt_text,
                user_message,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=LLM_CLI_TIMEOUT_SECONDS,
        )

    try:
        result = retry_request(_run, max_attempts=LLM_MAX_RETRIES)
    except subprocess.TimeoutExpired as exc:
        raise LLMCallError(
            f"claude CLI timed out after {LLM_CLI_TIMEOUT_SECONDS}s. "
            f"Input may be too large or the model overloaded."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        raise LLMCallError(f"claude CLI failed: {details}") from exc

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LLMCallError(f"Failed to parse claude JSON response: {exc}") from exc

    if "result" not in response:
        raise LLMCallError(
            f"Unexpected claude JSON schema. Expected 'result' field. "
            f"Got keys: {sorted(response.keys())}"
        )

    content = str(response["result"]).strip()
    if not content:
        raise LLMCallError("claude returned empty result content.")

    output_file.write_text(content + "\n", encoding="utf-8")

    usage = response.get("usage", {}) or {}
    input_tokens = int(
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    output_tokens = int(usage.get("output_tokens", 0))

    return {
        "provider": PROVIDER_CLAUDE,
        "model": plan.model,
        "effort_canonical": plan.effort_canonical,
        "effort_vendor": plan.effort_vendor,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def run_codex(
    plan: ResolvedPlan,
    output_file: Path,
) -> dict[str, int | str]:
    """Invoke the codex CLI and write the distilled output to ``output_file``."""
    user_message = (
        f"{plan.prompt_text.strip()}\n\n{USER_MESSAGE_OVERHEAD}{plan.input_text}"
    )
    tmp_output = output_file.parent / ".tmp_codex_last_message.md"

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "codex",
                "exec",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--model",
                plan.model,
                "--config",
                f'model_reasoning_effort="{plan.effort_vendor}"',
                "--output-last-message",
                str(tmp_output),
                "-",
            ],
            input=user_message,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
            timeout=LLM_CLI_TIMEOUT_SECONDS,
            stderr=subprocess.DEVNULL,
        )

    try:
        result = retry_request(_run, max_attempts=LLM_MAX_RETRIES)
    except subprocess.TimeoutExpired as exc:
        raise LLMCallError(
            f"codex CLI timed out after {LLM_CLI_TIMEOUT_SECONDS}s. "
            f"Input may be too large or the model overloaded."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stdout or str(exc)).strip()
        raise LLMCallError(f"codex CLI failed: {details}") from exc

    content = ""
    if tmp_output.exists():
        content = tmp_output.read_text(encoding="utf-8").strip()
        tmp_output.unlink(missing_ok=True)
    if not content:
        content = (result.stdout or "").strip()
    if not content:
        raise LLMCallError("codex returned empty output.")

    output_file.write_text(content + "\n", encoding="utf-8")

    return {
        "provider": PROVIDER_CODEX,
        "model": plan.model,
        "effort_canonical": plan.effort_canonical,
        "effort_vendor": plan.effort_vendor,
    }


def run_opencode(
    plan: ResolvedPlan,
    output_file: Path,
) -> dict[str, int | str]:
    """Invoke the opencode CLI and write the distilled output to ``output_file``."""
    user_message = (
        f"{plan.prompt_text.strip()}\n\n{USER_MESSAGE_OVERHEAD}{plan.input_text}"
    )

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "opencode",
                "run",
                "--agent",
                plan.model,
                "--format",
                "json",
                "-",
            ],
            input=user_message,
            capture_output=True,
            text=True,
            check=True,
            timeout=LLM_CLI_TIMEOUT_SECONDS,
        )

    try:
        result = retry_request(_run, max_attempts=LLM_MAX_RETRIES)
    except subprocess.TimeoutExpired as exc:
        raise LLMCallError(
            f"opencode CLI timed out after {LLM_CLI_TIMEOUT_SECONDS}s. "
            f"Input may be too large or the agent overloaded."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or str(exc)).strip()
        raise LLMCallError(f"opencode CLI failed: {details}") from exc

    chunks: list[str] = []
    total_tokens = 0
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0] not in "[{":
            continue

        try:
            event = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise LLMCallError(f"Failed to parse opencode JSON event: {exc}") from exc

        event_type = event.get("type")
        if event_type == "text":
            part = event.get("part", {})
            text = part.get("text") if isinstance(part, dict) else None
            if isinstance(text, str) and text:
                chunks.append(text)
            continue

        if event_type == "step_finish":
            part = event.get("part", {})
            tokens = part.get("tokens") if isinstance(part, dict) else None
            if isinstance(tokens, dict):
                total = tokens.get("total")
                if isinstance(total, int):
                    total_tokens = total

    content = "\n".join(chunk.strip() for chunk in chunks if chunk.strip()).strip()
    if not content:
        raise LLMCallError("opencode returned empty output.")

    output_file.write_text(content + "\n", encoding="utf-8")

    return {
        "provider": PROVIDER_OPENCODE,
        "model": plan.model,
        "effort_canonical": plan.effort_canonical,
        "effort_vendor": plan.effort_vendor,
        "total_tokens": total_tokens,
    }


def run_llm(plan: ResolvedPlan, output_file: Path) -> dict[str, int | str]:
    if plan.provider == PROVIDER_CLAUDE:
        return run_claude(plan, output_file)
    if plan.provider == PROVIDER_CODEX:
        return run_codex(plan, output_file)
    return run_opencode(plan, output_file)


# -------------------------------------------------------------------------
# Meta writer
# -------------------------------------------------------------------------


def write_meta(
    run_folder: Path,
    plan: ResolvedPlan,
    usage: dict[str, int | str],
    started_at: datetime,
    duration_seconds: float,
    output_file: Path,
) -> None:
    lines: list[str] = [
        f"file: {output_file.name}",
        f"original_file: {plan.input_path}",
        f"date: {started_at.isoformat(timespec='seconds')}",
        f"prompt: {plan.prompt_name}",
        f"prompt_file: {plan.prompt_path}",
        f"provider: {plan.provider}",
        f"model: {plan.model}",
        f"effort: {plan.effort_canonical} → {plan.effort_vendor} ({plan.provider})",
        f"duration: {duration_seconds:.1f}s",
        f"input_tokens: {plan.input_tokens:,}",
    ]

    if plan.provider == PROVIDER_CLAUDE:
        total_tokens = usage.get("total_tokens")
        output_tokens = usage.get("output_tokens")
        if isinstance(total_tokens, int):
            lines.append(f"total_tokens: {total_tokens:,}")
        if isinstance(output_tokens, int):
            lines.append(f"output_tokens: {output_tokens:,}")
    elif plan.provider == PROVIDER_OPENCODE:
        total_tokens = usage.get("total_tokens")
        if isinstance(total_tokens, int) and total_tokens > 0:
            lines.append(f"total_tokens: {total_tokens:,}")

    lines.append(f"distill_version: {__version__}")

    meta_file = run_folder / f"{plan.slug}_meta.yml"
    meta_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------


def execute_plan(plan: ResolvedPlan, open_finder: bool) -> Path:
    """Run the LLM, write output + meta, optionally open Finder.

    Returns the path to the distilled output.
    """
    run_folder_path = plan.run_folder_path
    while True:
        try:
            run_folder_path.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            time.sleep(1.05)
            run_folder_path, _ = make_run_folder_path(
                plan.output_parent,
                derive_slug(plan.input_path),
                plan.prompt_name,
            )
        except OSError as exc:
            raise OutputDirError(
                f"Cannot create run folder {run_folder_path}: {exc}"
            ) from exc

    output_file = run_folder_path / f"{plan.slug}_{plan.prompt_name}.md"
    copied_input_file = run_folder_path / f"{plan.slug}_raw{plan.input_path.suffix}"
    shutil.copy2(plan.input_path, copied_input_file)

    log.info(
        "distilling %s with %s via %s (%s, effort=%s)",
        plan.input_path.name,
        plan.prompt_name,
        plan.provider,
        plan.model,
        plan.effort_canonical,
    )

    started_at = datetime.now().astimezone()
    t0 = time.monotonic()
    try:
        usage = run_llm(plan, output_file)
        duration = time.monotonic() - t0
        write_meta(
            run_folder_path,
            plan,
            usage,
            started_at,
            duration,
            output_file,
        )
    # A model call may have been paid for, so the files it left stay listed
    except ScriptError as error:
        error.report["files"] = sorted(map(str, run_folder_path.iterdir()))
        raise
    except KeyboardInterrupt as stop:
        code = getattr(stop, "code", INTERRUPTED)
        stopped = ScriptError(
            "interrupted" if code == INTERRUPTED else "terminated",
            report={"files": sorted(map(str, run_folder_path.iterdir()))},
        )
        stopped.code = code
        raise stopped from stop
    except Exception as error:
        log.debug("unexpected failure", exc_info=True)
        raise ScriptError(
            f"{type(error).__name__}: {error}; see the traceback with --debug",
            report={"files": sorted(map(str, run_folder_path.iterdir()))},
        ) from error

    log.info("wrote %s in %.1fs", output_file, duration)

    if open_finder:
        open_folder_in_finder(run_folder_path)

    return output_file


def distill(args: argparse.Namespace) -> dict[str, Any]:
    """Run the command `args` names and return the data beside `ok`."""
    check_args(args)
    if args.list_models:
        # args.provider is None when the user did not pass --provider,
        # so None means "show all", and an explicit value filters.
        return {"models": list_models(args.provider)}

    if args.list_prompts:
        return {"prompts": list_prompt_names()}

    plan = build_plan(args)
    if args.dry_run:
        return dry_run_answer(plan)

    return {"file": str(execute_plan(plan, open_finder=not args.no_open))}


def main(argv: Sequence[str] | None = None) -> int:
    return run_script(build_parser(), distill, argv, debug="DISTILL_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

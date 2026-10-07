#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check a skill folder against the writing-for-agents best practices a script can verify."""

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

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import unquote

PROG = "validate_skill.py"

EPILOG = """\
Checks the best practices marked (validator) in writing-for-agents/SKILL.md:
SKILL.md and the Markdown files it links directly inside the skill folder.
A clean skill answers {"ok":true} on stdout. Otherwise the {"ok":false,...}
line that ends stderr lists each finding under errors, as
"path:line: error|warning: BP_NN Title: message". A warning fails too: fix
it, or tell the user why it stays.

examples:
  uv run path/to/writing-for-agents/scripts/validate_skill.py ../processing-pdfs
  uv run path/to/writing-for-agents/scripts/validate_skill.py --errors-only ~/.agents/skills/*
  uv run path/to/writing-for-agents/scripts/validate_skill.py --exclude vendor/playbooks vendor"""

# Titles match the BP lines in SKILL.md; a test keeps them in sync
BP_TITLES = {
    "BP_01": "Progressive disclosure",
    "BP_07": "No dated text",
    "BP_12": "Links resolve",
    "BP_13": "Name",
    "BP_14": "Description is a trigger",
    "BP_15": "SKILL.md under 500 lines",
    "BP_16": "Contents list",
    "BP_21": "Invoke by a word",
}

# Limits from the Agent Skills specification and the strictest agent platforms
NAME_MAX = 64
DESCRIPTION_MAX = 1024
SKILL_MAX = 500
RESERVED_WORDS = ("anthropic", "claude")
CONTENTS_THRESHOLD = 100
CONTENTS_SEARCH_LINES = 25

NAME_CHARS_RE = re.compile(r"[a-z0-9-]+")
XML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
# A description that limits firing to an invocation must use the BP_21 form
INVOKE_ONLY_RE = re.compile(r"use only when\b.*\b(?:invok|mention)", re.IGNORECASE)
INVOKE_FORM_RE = re.compile(r"Use only when explicitly invoked as `[^`]+`")
ACTOR_RE = re.compile(r"\bthe user\b", re.IGNORECASE)
KEY_RE = re.compile(r"(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)")
BLOCK_INDICATORS = {">", "|", ">-", "|-", ">+", "|+"}
QUOTED_RE = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^']|'')*'")
COMMENT_RE = re.compile(r"(?:^|\s+)#.*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
# Inline links and reference definitions; a bare target may hold one level of parentheses
DESTINATION = r"(?:<(?P<angle>[^<>\n]*)>|(?P<bare>(?:[^()\s]|\([^()\s]*\))+))"
LINK_RE = re.compile(
    rf"!?\[[^\]]*\]\(\s*{DESTINATION}(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\)))?\s*\)"
)
REFERENCE_DEF_RE = re.compile(rf"^ {{0,3}}\[[^\]]+\]:\s*{DESTINATION}")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_PATH_RE = re.compile(
    r"(?:[A-Za-z0-9_.-]+\\)+[A-Za-z0-9_.-]+\.(?:md|py|sh|js|ts|json|ya?ml|toml|txt)\b"
)
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|"
    "December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec"
)
DATED_RE = re.compile(
    rf"\b(?:before|after|until|as of)\s+(?:(?:{MONTHS})\.?\s+)?(?:\d{{1,2}},?\s+)?"
    r"(?:19|20)\d{2}(?:-\d{2}){0,2}\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*)")
CONTENTS_RE = re.compile(
    r"^\s*(?:#{1,6}\s*|\*\*)?(?:table of )?contents\b", re.IGNORECASE
)

Level = Literal["error", "warning"]

EXIT_CODES = exit_codes(
    {
        1: "at least one finding; with --errors-only, at least one error",
        USAGE: "bad usage: a folder is missing or has no SKILL.md",
    }
)

log = logging.getLogger("validate_skill")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    level: Level
    bp: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.level}: {self.bp} {BP_TITLES[self.bp]}: {self.message}"


@dataclass(frozen=True)
class Field:
    value: str
    line: int


@dataclass(frozen=True)
class Prose:
    """A Markdown line outside fenced code; `masked` blanks its inline code spans."""

    number: int
    raw: str
    masked: str
    headings: tuple[str, ...]


def scalar(raw: str, block: bool) -> str:
    """The string a YAML scalar holds: block text as written, quoted text unescaped,
    plain text without its trailing comment."""
    if block:
        return raw
    if quoted := QUOTED_RE.match(raw):
        text = quoted.group(0)[1:-1]
        if quoted.group(0)[0] == "'":
            return text.replace("''", "'")
        return text.replace('\\"', '"').replace("\\\\", "\\")
    return COMMENT_RE.sub("", raw)


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, Field], int]:
    """Read top-level `key: value` pairs; return them and the index of the first body line."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, 0
    raw: dict[str, tuple[str, int, bool]] = {}
    key: str | None = None
    for index in range(1, end):
        line = lines[index]
        if line.startswith("#"):
            continue
        match = KEY_RE.fullmatch(line) if not line[:1].isspace() else None
        if match:
            key = name = match.group("key")
            value = match.group("value").strip()
            block = COMMENT_RE.sub("", value) in BLOCK_INDICATORS
            raw[name] = ("" if block else value, index + 1, block)
        elif key and line.strip():
            value, number, block = raw[key]
            raw[key] = (f"{value} {line.strip()}".strip(), number, block)
    fields = {k: Field(scalar(v, block), n) for k, (v, n, block) in raw.items()}
    return fields, end + 1


def prose_lines(lines: list[str], start: int) -> list[Prose]:
    """Lines outside fenced code, numbered from 1, with the headings each sits under."""
    result: list[Prose] = []
    fence: str | None = None
    headings: list[tuple[int, str]] = []
    for index in range(start, len(lines)):
        line = lines[index]
        match = FENCE_RE.match(line)
        if fence:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        if heading := HEADING_RE.match(line):
            level = len(heading["hashes"])
            headings = [h for h in headings if h[0] < level] + [
                (level, heading["text"])
            ]
        masked = INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
        result.append(
            Prose(index + 1, line, masked, tuple(text for _, text in headings))
        )
    return result


def check_name(skill: Path, skill_md: Path, fields: dict[str, Field]) -> list[Finding]:
    field = fields.get("name")
    if field is None or not field.value:
        return [
            Finding(
                skill_md,
                field.line if field else 1,
                "error",
                "BP_13",
                "name is missing",
            )
        ]
    name = field.value
    problems: list[str] = []
    if len(name) > NAME_MAX:
        problems.append(f"name '{name}' is longer than {NAME_MAX} characters")
    if not NAME_CHARS_RE.fullmatch(name):
        problems.append(
            f"name '{name}' may only use lowercase letters, digits, and hyphens"
        )
    if name.startswith("-") or name.endswith("-") or "--" in name:
        problems.append(f"name '{name}' starts or ends with a hyphen or contains '--'")
    if name != skill.resolve().name:
        problems.append(
            f"name '{name}' does not match the folder name '{skill.resolve().name}'"
        )
    problems += [
        f"name '{name}' contains the reserved word '{word}'"
        for word in RESERVED_WORDS
        if word in name.lower()
    ]
    return [
        Finding(skill_md, field.line, "error", "BP_13", problem) for problem in problems
    ]


def check_description(skill_md: Path, fields: dict[str, Field]) -> list[Finding]:
    field = fields.get("description")
    if field is None or not field.value:
        return [
            Finding(
                skill_md,
                field.line if field else 1,
                "error",
                "BP_14",
                "description is missing",
            )
        ]
    findings: list[Finding] = []
    if len(field.value) > DESCRIPTION_MAX:
        findings.append(
            Finding(
                skill_md,
                field.line,
                "error",
                "BP_14",
                f"description has {len(field.value)} characters; the limit is {DESCRIPTION_MAX}",
            )
        )
    if tag := XML_TAG_RE.search(field.value):
        findings.append(
            Finding(
                skill_md,
                field.line,
                "error",
                "BP_14",
                f"description contains the XML tag '{tag.group(0)}'",
            )
        )
    invocation = field.value.partition(". ")[0]
    if INVOKE_ONLY_RE.match(invocation):
        if not INVOKE_FORM_RE.match(invocation):
            findings.append(
                Finding(
                    skill_md,
                    field.line,
                    "warning",
                    "BP_21",
                    "start with 'Use only when explicitly invoked as `word`', the word in backticks",
                )
            )
        if ACTOR_RE.search(invocation):
            findings.append(
                Finding(
                    skill_md,
                    field.line,
                    "warning",
                    "BP_21",
                    "names an actor, 'the user'; a delegated prompt would be refused",
                )
            )
    return findings


def link_targets(prose: list[Prose]) -> list[tuple[Prose, str]]:
    found: list[tuple[Prose, str]] = []
    for line in prose:
        matches = [*LINK_RE.finditer(line.masked)]
        if definition := REFERENCE_DEF_RE.match(line.masked):
            matches.append(definition)
        found += [
            (line, m["angle"] if m["angle"] is not None else m["bare"]) for m in matches
        ]
    return found


def resolve_local(skill: Path, source: Path, target: str) -> Path | None:
    """The file a relative link reaches inside the skill, or None for URLs, anchors, and outside paths."""
    if SCHEME_RE.match(target) or target.startswith(("#", "/")):
        return None
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return None
    resolved = (source.parent / path).resolve()
    return resolved if resolved.is_relative_to(skill.resolve()) else None


def check_document(
    skill: Path, path: Path, prose: list[Prose], is_skill_md: bool
) -> list[Finding]:
    findings: list[Finding] = []
    for line, target in link_targets(prose):
        if "\\" in target:
            findings.append(
                Finding(
                    path,
                    line.number,
                    "error",
                    "BP_12",
                    f"link '{target}' uses backslashes",
                )
            )
            continue
        resolved = resolve_local(skill, path, target)
        if resolved is None:
            continue
        if not resolved.exists():
            findings.append(
                Finding(
                    path,
                    line.number,
                    "error",
                    "BP_12",
                    f"link to missing file '{target}'",
                )
            )
        elif (
            not is_skill_md and resolved.suffix == ".md" and resolved.name != "SKILL.md"
        ):
            findings.append(
                Finding(
                    path,
                    line.number,
                    "warning",
                    "BP_01",
                    f"links to reference file '{target}'; link it from SKILL.md instead",
                )
            )
    for line in prose:
        # Link targets were checked above; this catches paths in prose and inline code
        for match in WINDOWS_PATH_RE.finditer(LINK_RE.sub(" ", line.raw)):
            findings.append(
                Finding(
                    path,
                    line.number,
                    "error",
                    "BP_12",
                    f"path '{match.group(0)}' uses backslashes",
                )
            )
        if any("old pattern" in heading.lower() for heading in line.headings):
            continue
        for match in DATED_RE.finditer(line.masked):
            findings.append(
                Finding(
                    path,
                    line.number,
                    "warning",
                    "BP_07",
                    f"dated text '{match.group(0)}'; keep the current method and move the old one to 'Old patterns'",
                )
            )
    return findings


def check_contents(path: Path, lines: list[str]) -> list[Finding]:
    if len(lines) <= CONTENTS_THRESHOLD or any(
        CONTENTS_RE.match(line) for line in lines[:CONTENTS_SEARCH_LINES]
    ):
        return []
    message = f"{len(lines)} lines and no Contents list; ask the user before adding one"
    return [Finding(path, 1, "warning", "BP_16", message)]


def validate(skill: Path) -> list[Finding]:
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        raise UsageError(f"{skill} has no SKILL.md; pass a skill folder")
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    fields, body_start = parse_frontmatter(lines)
    findings = check_name(skill, skill_md, fields) + check_description(skill_md, fields)
    if len(lines) > SKILL_MAX:
        findings.append(
            Finding(
                skill_md,
                SKILL_MAX + 1,
                "error",
                "BP_15",
                f"file has {len(lines)} lines; the limit is {SKILL_MAX}",
            )
        )
    prose = prose_lines(lines, body_start)
    findings += check_document(skill, skill_md, prose, is_skill_md=True)
    references: dict[Path, Path] = {}
    for _, target in link_targets(prose):
        resolved = resolve_local(skill, skill_md, target)
        if (
            resolved
            and resolved.is_file()
            and resolved.suffix == ".md"
            and resolved != skill_md.resolve()
        ):
            references.setdefault(
                resolved, skill / resolved.relative_to(skill.resolve())
            )
    for path in references.values():
        reference_lines = path.read_text(encoding="utf-8").splitlines()
        findings += check_document(
            skill, path, prose_lines(reference_lines, 0), is_skill_md=False
        )
        findings += check_contents(path, reference_lines)
    return sorted(findings, key=lambda f: (str(f.path), f.line, f.bp, f.message))


def build_parser() -> Parser:
    parser = Parser(
        prog=PROG, description=__doc__, exit_codes=EXIT_CODES, epilog=EPILOG
    )
    parser.add_argument(
        "folders",
        nargs="+",
        type=Path,
        metavar="SKILL_FOLDER",
        help="a folder holding SKILL.md",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help="skip findings in files under PATH, such as text copied from another repository; repeatable",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="fail on errors only and leave warnings to -v, for a sweep of skills "
        "whose warnings were accepted, such as just check",
    )
    return parser


def check(args: argparse.Namespace) -> dict[str, Any]:
    """Validate each folder; raise ScriptError with one message per finding that fails."""
    findings = [finding for folder in args.folders for finding in validate(folder)]
    excluded = [path.resolve() for path in args.exclude]
    failing: list[str] = []
    for finding in findings:
        if any(finding.path.resolve().is_relative_to(path) for path in excluded):
            continue
        if args.errors_only and finding.level == "warning":
            log.info("%s", finding)
        else:
            failing.append(str(finding))
    if failing:
        raise ScriptError(*failing)
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    return run_script(build_parser(), check, argv)


if __name__ == "__main__":
    sys.exit(main())

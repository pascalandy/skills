# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Set up, audit, and gate the Rust guardrails this skill describes.

init   writes the lint profile into Cargo.toml, plus clippy.toml, deny.toml,
       a justfile `check` recipe, lefthook.yml, a copy of this script under
       scripts/, and the exception rule in AGENTS.md. Files the project already
       has keep their content; a rerun changes nothing.
audit  compares every manifest's [lints] with the profile, and reports what
       the `check` recipe lacks. --violations also runs Clippy with the whole
       profile and counts findings per lint, so lints at zero go on first.
diff   lists the exceptions a change adds: unsafe, #[allow], #[expect],
       #[ignore], #[should_panic], removed tests or assertions, new
       dependencies, edited guardrail files, TODOs without an issue, and new
       shortcuts such as unwrap() that the project does not deny yet. It
       compares the working tree with HEAD, so a committed, approved exception
       stops counting; --base lists what the branch's commits add. It fails
       when it finds one, unless --report is given.

init and audit read the skill's assets, so run them from the skill copy. The
project copy runs diff. Answers in one JSON line: init lists `changes`; audit
lists `manifests`, `files`, and `check_recipe`; diff lists `exceptions` and
`notes`, each as [kind, location, detail].
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

import difflib
import fnmatch
import hashlib
import posixpath
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"
LOG = logging.getLogger("rust_guard")
# The first docstring line marks a copy init wrote; init never replaces a
# scripts/rust_guard.py without it, since that file belongs to the project
MARKER = "Set up, audit, and gate the Rust guardrails this skill describes."

AGENTS_START = "<!-- rust-guard:start -->"
AGENTS_END = "<!-- rust-guard:end -->"

# Files whose edit changes what the gate checks, matched by name at any depth.
# Loosening one silently loosens every later check
PROTECTED_NAMES = frozenset(
    {
        "clippy.toml",
        ".clippy.toml",
        "deny.toml",
        "rustfmt.toml",
        ".rustfmt.toml",
        "rust-toolchain",
        "rust-toolchain.toml",
        "justfile",
        "Justfile",
        ".justfile",
        "lefthook.yml",
        "lefthook.yaml",
        ".lefthook.yml",
        ".gitlab-ci.yml",
        ".travis.yml",
        ".woodpecker.yml",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
        "Jenkinsfile",
    }
)
PROTECTED_SUFFIXES = (".cargo/config.toml", ".cargo/config", "scripts/rust_guard.py")
PROTECTED_DIRS = (
    ".github/workflows/",
    ".gitlab/",
    ".circleci/",
    ".buildkite/",
    ".woodpecker/",
    ".forgejo/workflows/",
    ".gitea/workflows/",
)
DEPENDENCY_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")

# Each pattern runs on code with strings and comments removed. `ratchet` names
# the Clippy lint that, once denied, makes the pattern Clippy's job instead
# Attributes are compared whole, with whitespace removed, so one rustfmt split
# over several lines or one more lint in an existing #[expect(...)] still shows
ATTRIBUTES = (
    ("allow", re.compile(r"\ballow\(")),
    ("expect", re.compile(r"\bexpect\(")),
    ("ignore", re.compile(r"\bignore\b")),
    ("should_panic", re.compile(r"\bshould_panic\b")),
)
INNER_CFG_TEST = re.compile(r"#!\[\s*cfg\s*\(\s*test\s*\)\s*\]")
DOC_LINE = re.compile(r"^\s*//[/!](?!/)(.*)$")
UNSAFE = re.compile(r"\bunsafe\b")
# A cfg on a test item that is not cfg(test) can switch the test off
DISABLING_CFG = re.compile(r"#!?\[cfg(?:_attr)?\((?!test\)\])")
TEST_MODULE = re.compile(r"#\[cfg\(test\)\](?:pub(?:\([^)]*\))?)?mod\w+;")


@dataclass(frozen=True)
class Pattern:
    kind: str
    regex: re.Pattern[str]
    ratchet: str = ""
    tests_exempt: bool = False


PATTERNS = (
    # Shortcuts a project may not deny yet: new ones are flagged while the
    # existing ones stay (the ratchet). clippy.toml lets tests use the first three
    Pattern("unwrap_used", re.compile(r"\.unwrap\(\)"), "unwrap_used", True),
    Pattern("expect_used", re.compile(r"\.expect\("), "expect_used", True),
    Pattern("panic", re.compile(r"\bpanic!\s*[(\[{]"), "panic", True),
    Pattern("todo", re.compile(r"\btodo!\s*[(\[{]"), "todo"),
    Pattern("unimplemented", re.compile(r"\bunimplemented!\s*[(\[{]"), "unimplemented"),
    Pattern("dbg_macro", re.compile(r"\bdbg!\s*[(\[{]"), "dbg_macro"),
)
# Counted, not blocked: no lint catches them reliably, so the reviewer judges
NOTES = (
    ("clone", re.compile(r"\.clone\(\)")),
    (
        "arc_mutex",
        re.compile(
            r"Arc<\s*(?:std::sync::|tokio::sync::|parking_lot::)?(?:Mutex|RwLock)\b"
        ),
    ),
)
TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
ISSUE_LINK = re.compile(r"#\d+|https?://")
TEST_ATTR = re.compile(r"#\[\s*(?:[\w:]+::)?test\b")
TEST_FN = re.compile(r"\bfn\s+(\w+)")
CFG_TEST = re.compile(r"#\[\s*cfg\s*\(\s*test\s*\)\s*\]")
ASSERTION = re.compile(r"\b(?:debug_)?assert(?:_eq|_ne|_matches)?!\s*[(\[{]")
TOKENS = re.compile(
    r"""(?P<raw>b?r(?P<hashes>\#*)".*?"(?P=hashes))"""  # raw strings, closed on this line
    r"""|(?P<string>b?"(?:\\.|[^"\\])*"?)"""  # strings, possibly continued
    r"""|(?P<char>b?'(?:\\.|[^'\\])')"""  # char literals; a lifetime has no closing quote
    r"""|(?P<block>/\*.*?\*/)"""  # block comments closed on this line
    r"""|(?P<line>//.*)"""  # the line comment
)


def split_line(line: str, keep: bool = False) -> tuple[str, str]:
    """The line's code, with literals emptied and block comments blanked, and
    the text of its `//` comment. One left-to-right pass, so a quote inside a
    comment and `//` inside a string are read for what they are."""
    code: list[str] = []
    comment = ""
    position = 0
    for token in TOKENS.finditer(line):
        code.append(line[position : token.start()])
        position = token.end()
        if token["line"] is not None:
            comment = token["line"][2:]
            break
        if token["block"] is not None:
            code.append(" ")
        elif keep:
            digest = hashlib.sha1(token[0].encode()).hexdigest()[:10]
            code.append(f'"{digest}"')
        else:
            code.append('""')
    else:
        code.append(line[position:])
    return "".join(code), comment


def code_only(line: str) -> str:
    """The line without string and char literals, then without its comments."""
    return split_line(line)[0]


def comment_of(line: str) -> str:
    """The text of the line's `//` comment, ignoring `//` inside strings."""
    return split_line(line)[1]


def attributes(text: str) -> list[tuple[int, str, str, str]]:
    """Each attribute in the file as (first line, text without whitespace, the
    item it is attached to), read across lines on code without strings and
    comments. The item is the head of the next code after the attribute stack,
    such as `pubfnload_schema()->Schema`, so a moved attribute reads as new."""
    # literals become digests: `target_os = "linux"` and `"windows"` differ
    code = [split_line(line, keep=True)[0] for line in text.splitlines()]
    found: list[tuple[int, str, str, str]] = []
    raw = text.splitlines()
    line_of: list[int] = []
    joined = ""
    for number, line in enumerate(code, 1):
        joined += line + "\n"
        line_of += [number] * (len(line) + 1)
    index = 0
    while (index := joined.find("#", index)) != -1:
        open_at = index + 1 + (joined[index + 1 : index + 2] == "!")
        if joined[open_at : open_at + 1] != "[":
            index += 1
            continue
        depth = 0
        end = len(joined) - 1
        for position in range(open_at, len(joined)):
            depth += {"[": 1, "]": -1}.get(joined[position], 0)
            if depth == 0:
                end = position
                break
        item = ""
        if joined[index + 1 : index + 2] != "!":
            rest = joined[end + 1 :]
            while True:
                rest = rest.lstrip()
                if not re.match(r"#!?\[", rest):
                    break
                depth = 0
                for position, char in enumerate(rest):
                    depth += {"[": 1, "]": -1}.get(char, 0)
                    if char == "]" and depth == 0:
                        rest = rest[position + 1 :]
                        break
                else:
                    rest = ""
            item = re.sub(r"\s+", "", item_head(rest))[:120]
        shown = " ".join(
            line.strip()
            for line in raw[line_of[index] - 1 : line_of[min(end, len(line_of) - 1)]]
        )
        found.append(
            (line_of[index], re.sub(r"\s+", "", joined[index : end + 1]), item, shown)
        )
        index = end + 1
    return found


def item_head(rest: str) -> str:
    """The start of the item after an attribute stack, up to its body or the
    end of a field or variant: the first `{`, `;`, `,`, or `}` outside
    parentheses and brackets."""
    depth = 0
    for position, char in enumerate(rest):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif depth <= 0 and char in "{;,}":
            return rest[:position]
    return rest


def read_raw(path: Path) -> str:
    with path.open(newline="") as handle:
        return handle.read()


def write_raw(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        handle.write(text)


def profile() -> dict[str, dict[str, str]]:
    """The lint profile, as [lints] tables keyed by tool."""
    source = ASSETS / "lints.toml"
    if not source.is_file():
        raise UsageError(
            "init and audit need the skill's assets; run them from the skill copy, "
            "such as uv run <skill>/scripts/rust_guard.py audit"
        )
    return tomllib.loads(source.read_text())["lints"]


def read_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise ScriptError(f"{path}: invalid TOML: {error}") from error


def root_of(path: str) -> Path:
    root = Path(path).resolve()
    if not (root / "Cargo.toml").is_file():
        raise UsageError(
            f"{root} has no Cargo.toml; run from the crate or workspace root, or pass its path"
        )
    return root


def members(root: Path, manifest: dict[str, Any]) -> list[Path]:
    """Manifest paths of the declared workspace members, root package included."""
    found: list[Path] = []
    if "package" in manifest:
        found.append(root / "Cargo.toml")
    workspace = manifest.get("workspace", {})
    excluded = {
        folder.resolve()
        for pattern in workspace.get("exclude", [])
        for folder in expand(root, pattern)
    }
    for pattern in workspace.get("members", []):
        for match in expand(root, pattern):
            folder = match.resolve()
            candidate = folder / "Cargo.toml"
            if (
                not any(folder.is_relative_to(other) for other in excluded)
                and candidate.is_file()
                and candidate not in found
            ):
                found.append(candidate)
    return found


def expand(root: Path, pattern: str) -> list[Path]:
    """Folders a workspace `members` or `exclude` entry names. A plain path,
    such as ".", is taken as is, since Path.glob refuses some of them."""
    if not any(char in pattern for char in "*?["):
        return [root / pattern]
    return sorted(root.glob(pattern))


def lint_level(value: Any) -> str:
    return value.get("level", "") if isinstance(value, dict) else str(value)


def effective_lints(
    manifest: dict[str, Any], workspace: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    lints = manifest.get("lints", {})
    if lints.get("workspace") is True:
        return workspace.get("workspace", {}).get("lints", {})
    if "workspace" in manifest and "package" not in manifest:
        return manifest["workspace"].get("lints", {})
    return lints


def missing_lints(lints: dict[str, dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for tool, table in profile().items():
        for name, level in table.items():
            have = lint_level(lints.get(tool, {}).get(name))
            if have not in (level, "forbid"):
                missing.append(name if tool == "rust" else f"{tool}::{name}")
    return missing


def run(
    command: list[str],
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    LOG.debug("run: %s (in %s)", shlex.join(command), cwd)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            env=env,
        )
    except FileNotFoundError as error:
        raise ScriptError(
            f"{command[0]} is not installed; install it as the skill's Prerequisites section says"
        ) from error
    if check and result.returncode != 0:
        raise ScriptError(
            f"`{shlex.join(command)}` failed with exit code {result.returncode}",
            detail=result.stderr.strip(),
        )
    return result


def recipe_steps(text: str) -> list[str]:
    """The commands of the `check` recipe in a justfile, without comments,
    quiet or error-ignoring prefixes, or indentation."""
    body = re.search(
        r"^@?check(?:\s+[^:=\n]*)?:(?!=)[^\n]*\n((?:[ \t]+[^\n]*\n?|\n)*)",
        text,
        re.MULTILINE,
    )
    steps = [
        line.strip().removeprefix("@").strip()
        for line in (body[1] if body else "").splitlines()
    ]
    return [step for step in steps if step and not step.startswith("#")]


def check_recipe(root: Path) -> tuple[Path | None, list[str]]:
    """The project's justfile, and the gate steps its `check` recipe lacks.

    The gate is every step of the skill's recipe, with its exact arguments.
    A step that passes --report to the guard counts as missing the guard.
    """
    gate = recipe_steps((ASSETS / "justfile").read_text())
    for name in ("justfile", "Justfile", ".justfile"):
        path = root / name
        if path.is_file():
            steps = [
                step
                for step in recipe_steps(path.read_text())
                if "--report" not in step
            ]
            return path, [step for step in gate if step not in steps]
    return None, gate


def tests_may_panic(root: Path) -> bool:
    """Whether the project's Clippy config lets tests unwrap, expect, and panic,
    as the profile's tests need once those lints are denied."""
    for name in ("clippy.toml", ".clippy.toml"):
        path = root / name
        if path.is_file():
            try:
                config = tomllib.loads(path.read_text())
            except tomllib.TOMLDecodeError:
                return False
            keys = (
                "allow-unwrap-in-tests",
                "allow-expect-in-tests",
                "allow-panic-in-tests",
            )
            return all(config.get(key) is True for key in keys)
    return False


def lefthook_config(root: Path) -> Path | None:
    for name in ("lefthook.yml", "lefthook.yaml", ".lefthook.yml"):
        if (root / name).is_file():
            return root / name
    return None


def hook_lacks_guard(root: Path) -> Path | None:
    """The project's lefthook config when its pre-commit hook does not run the
    staged guard in blocking mode; None when it does or when there is none."""
    path = lefthook_config(root)
    if path is None:
        return None
    section = re.search(
        r"^pre-commit:[^\n]*\n((?:[ \t][^\n]*\n?|\n)*)", path.read_text(), re.MULTILINE
    )
    lines = (section[1] if section else "").splitlines()
    indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    top = min(indents, default=0)
    hook_keys = {"skip", "only", "files", "glob", "exclude", "root"}
    if any(
        len(line) - len(line.lstrip()) == top
        and line.strip().split(":", 1)[0] in hook_keys
        for line in lines
        if line.strip()
    ):
        return path
    for index, line in enumerate(lines):
        if (
            "rust_guard.py diff --staged" in line
            and "--report" not in line
            and not line.lstrip().startswith("#")
            and not narrowed(lines, index)
        ):
            return None
    return path


def narrowed(lines: list[str], index: int) -> bool:
    """Whether the lefthook command holding line `index` limits the files or the
    folder it runs on, so a staged manifest or CI edit could skip the guard."""
    indent = len(lines[index]) - len(lines[index].lstrip())
    start = index
    while start > 0 and (
        not lines[start - 1].strip()
        or len(lines[start - 1]) - len(lines[start - 1].lstrip()) >= indent
    ):
        start -= 1
    end = index
    while end + 1 < len(lines) and (
        not lines[end + 1].strip()
        or len(lines[end + 1]) - len(lines[end + 1].lstrip()) >= indent
    ):
        end += 1
    keys = {"glob", "files", "root", "exclude", "file_types", "only", "skip"}
    return any(
        len(line) - len(line.lstrip()) == indent
        and line.strip().split(":", 1)[0].lstrip("- ") in keys
        for line in lines[start : end + 1]
    )


# init ---------------------------------------------------------------------


def nested_hook_hint(top: Path, prefix: str) -> str:
    """What to add to the repository-root lefthook config for a nested crate.
    `exceptions` runs from the root, so it also sees root CI and hook edits."""
    return (
        f"lefthook reads its config at the git root {top}: there, add a pre-commit command "
        f"`exceptions` running `uv run {prefix}/scripts/rust_guard.py diff --staged` with no `root:`, "
        f"and give the `fmt` and pre-push `check` commands of {ASSETS / 'lefthook.yml'} the setting `root: {prefix}/`"
    )


def git_root(folder: Path) -> Path | None:
    found = run(["git", "rev-parse", "--show-toplevel"], folder, check=False)
    return Path(found.stdout.strip()).resolve() if found.returncode == 0 else None


def lint_block(workspace: bool) -> str:
    profile()
    text = (ASSETS / "lints.toml").read_text()
    return text.replace("[lints.", "[workspace.lints.") if workspace else text


def append(text: str, block: str) -> str:
    newline = "\r\n" if "\r\n" in text else "\n"
    return (
        text.rstrip("\r\n")
        + newline * 2
        + block.replace("\n", newline).rstrip(newline)
        + newline
    )


def plan_init(root: Path) -> list[tuple[str, str, Path, str]]:
    """Each change init would make, as (action, object, path, new text)."""
    plans: list[tuple[str, str, Path, str]] = []
    manifest_path = root / "Cargo.toml"
    manifest = read_toml(manifest_path)
    original = read_raw(manifest_path)
    text = original
    is_workspace = "workspace" in manifest
    if is_workspace and "lints" not in manifest["workspace"]:
        text = append(text, lint_block(workspace=True))
    if "package" in manifest and "lints" not in manifest:
        text = append(
            text,
            "[lints]\nworkspace = true\n"
            if is_workspace
            else lint_block(workspace=False),
        )
    if text != original:
        plans.append(("update", "Cargo.toml", manifest_path, text))
    for member in members(root, manifest):
        if member == manifest_path or "lints" in read_toml(member):
            continue
        member_text = append(read_raw(member), "[lints]\nworkspace = true\n")
        plans.append(
            ("update", member.relative_to(root).as_posix(), member, member_text)
        )
    nested = git_root(root) not in (None, root)
    for name in ("clippy.toml", "deny.toml", "justfile", "lefthook.yml"):
        if name == "lefthook.yml" and nested:
            continue
        target = root / name
        alternates = {
            "clippy.toml": (".clippy.toml",),
            "justfile": ("Justfile", ".justfile"),
            "lefthook.yml": ("lefthook.yaml", ".lefthook.yml"),
        }.get(name, ())
        exists = target.exists() or any((root / other).exists() for other in alternates)
        if not exists:
            plans.append(("create", name, target, (ASSETS / name).read_text()))
    guard = root / "scripts" / "rust_guard.py"
    source = Path(__file__).read_text()
    if not guard.exists():
        plans.append(("create", "scripts/rust_guard.py", guard, source))
    elif guard.read_text() != source:
        plans.append(("update", "scripts/rust_guard.py", guard, source))
    agents = root / "AGENTS.md"
    section = (ASSETS / "agents-section.md").read_text().strip("\n")
    block = f"{AGENTS_START}\n{section}\n{AGENTS_END}\n"
    if not agents.exists():
        plans.append(("create", "AGENTS.md", agents, block))
    else:
        current = read_raw(agents)
        if AGENTS_START in current and AGENTS_END not in current:
            raise ScriptError(
                f"{agents} has {AGENTS_START} without {AGENTS_END}; add the end marker after the section, then rerun init"
            )
        if AGENTS_START in current:
            pattern = re.compile(
                re.escape(AGENTS_START) + r".*?" + re.escape(AGENTS_END) + r"\r?\n?",
                re.DOTALL,
            )
            updated = pattern.sub(lambda _match: block, current, count=1)
        else:
            updated = append(current, block)
        if updated != current:
            plans.append(("update", "AGENTS.md", agents, updated))
    return plans


def init(args: argparse.Namespace) -> dict[str, Any]:
    profile()
    root = root_of(args.path)
    recipe, lacking = check_recipe(root)
    if recipe is not None and lacking:
        raise ScriptError(
            f"the `check` recipe in {recipe.name} does not run the whole gate; "
            f"it lacks: {'; '.join(lacking)}. Copy the recipe in {ASSETS / 'justfile'} into it, then rerun init"
        )
    top = git_root(root) or root
    hook = hook_lacks_guard(top)
    if hook is not None:
        hint = (
            f"add the commands in {ASSETS / 'lefthook.yml'} to it"
            if top == root
            else nested_hook_hint(top, root.relative_to(top).as_posix())
        )
        raise ScriptError(
            f"{hook} has no pre-commit command running `rust_guard.py diff --staged` without --report; {hint}, then rerun init"
        )
    guard = root / "scripts" / "rust_guard.py"
    if guard.exists() and MARKER not in guard.read_text():
        raise ScriptError(
            f"{guard} exists and is not a copy of this script; rename it, then rerun init"
        )
    plans = plan_init(root)
    changes: list[list[str]] = []
    if not (root / "Cargo.lock").exists():
        # First, so a failure (offline, bad manifest) leaves nothing half-written
        changes.append(["create", "Cargo.lock", "cargo generate-lockfile"])
        if not args.dry_run:
            run(["cargo", "generate-lockfile"], root)
    for action, name, path, text in plans:
        changes.append([action, name])
        if not args.dry_run:
            write_raw(path, text)
    fields: dict[str, Any] = {"changes": changes} if changes else {}
    top = git_root(root)
    if top is not None and top != root:
        prefix = root.relative_to(top).as_posix()
        fields["notes"] = [nested_hook_hint(top, prefix)]
    return fields


# audit --------------------------------------------------------------------


def probe_config(root: Path, scratch: Path) -> Path:
    """A Clippy config folder for the audit probe: the project's config plus
    the test allowances branch B adds, so a lint whose only findings sit in
    tests counts zero."""
    text = ""
    for name in ("clippy.toml", ".clippy.toml"):
        if (root / name).is_file():
            text = (root / name).read_text()
            break
    try:
        config = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        config = {}
    for key in (
        "allow-unwrap-in-tests",
        "allow-expect-in-tests",
        "allow-panic-in-tests",
    ):
        if key not in config:
            text = f"{key} = true\n" + text
    (scratch / "clippy.toml").write_text(text)
    return scratch


def violations(root: Path) -> dict[str, int]:
    """Clippy findings for every profile lint, zeros included, with the whole
    profile at warn. A build that fails yields no counts, since a lint that
    never ran found nothing."""
    flags: list[str] = []
    names: list[str] = []
    for tool, table in profile().items():
        for name in table:
            flags += ["-W", f"clippy::{name}" if tool == "clippy" else name]
            names.append(name)
    scratch = Path(tempfile.mkdtemp(prefix="rust-guard-"))
    result = run(
        [
            "cargo",
            "clippy",
            "--workspace",
            "--all-targets",
            "--all-features",
            "--message-format=json",
            "--quiet",
            "--",
            "--cap-lints=warn",
            *flags,
        ],
        root,
        check=False,
        env={**os.environ, "CLIPPY_CONF_DIR": str(probe_config(root, scratch))},
    )
    shutil.rmtree(scratch, ignore_errors=True)
    counts = count_findings(result.stdout)
    if result.returncode != 0 or not build_succeeded(result.stdout):
        raise ScriptError(
            "Clippy did not finish, so the counts would be wrong; fix the build, then rerun audit --violations",
            detail=result.stderr.strip(),
        )
    # `forbid` rejects an existing #[allow(unsafe_code)], which a warn-level
    # probe never reports: count those overrides as findings
    overrides = re.compile(
        r"#!?\[[^\]]*?\b(?:allow|expect|warn)\s*\([^\]]*\bunsafe_code\b"
    )
    for source in root.rglob("*.rs"):
        if "target" not in source.relative_to(root).parts:
            text = source.read_text(errors="replace")
            code = "\n".join(code_only(line) for line in text.splitlines())
            counts["unsafe_code"] = counts.get("unsafe_code", 0) + len(
                overrides.findall(code)
            )
    return {name: counts.get(name, 0) for name in names}


def build_succeeded(stream: str) -> bool:
    for line in stream.splitlines():
        if line.startswith("{"):
            record = json.loads(line)
            if record.get("reason") == "build-finished":
                return bool(record.get("success"))
    return False


def count_findings(stream: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    seen: set[tuple[str, str, str, int, int]] = set()
    for line in stream.splitlines():
        if not line.startswith("{"):
            continue
        record = json.loads(line)
        message = record.get("message") or {}
        code = (message.get("code") or {}).get("code")
        if record.get("reason") != "compiler-message" or not code:
            continue
        spans = message.get("spans") or [{}]
        key = (
            code,
            record.get("package_id", ""),
            spans[0].get("file_name", ""),
            spans[0].get("line_start", 0),
            spans[0].get("column_start", 0),
        )
        if key in seen:
            continue
        seen.add(key)
        name = code.removeprefix("clippy::")
        if code == "E0133" and message.get("level") == "warning":
            name = "unsafe_op_in_unsafe_fn"
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def audit(args: argparse.Namespace) -> dict[str, Any]:
    profile()
    root = root_of(args.path)
    root_manifest = read_toml(root / "Cargo.toml")
    report: list[dict[str, Any]] = []
    for path in members(root, root_manifest) or [root / "Cargo.toml"]:
        entry: dict[str, Any] = {"path": path.relative_to(root).as_posix()}
        manifest = read_toml(path)
        if (
            "workspace" in root_manifest
            and "package" in manifest
            and path != root / "Cargo.toml"
            and manifest.get("lints", {}).get("workspace") is not True
        ):
            entry["inherits"] = False
        entry["missing"] = missing_lints(effective_lints(manifest, root_manifest))
        report.append(entry)
    names = {
        "Cargo.lock": ("Cargo.lock",),
        "clippy.toml": ("clippy.toml", ".clippy.toml"),
        "deny.toml": ("deny.toml",),
        "lefthook.yml": ("lefthook.yml", "lefthook.yaml", ".lefthook.yml"),
        "AGENTS.md": ("AGENTS.md",),
        "scripts/rust_guard.py": ("scripts/rust_guard.py",),
    }
    top = git_root(root) or root
    files = {
        name: any(
            (top if name == "lefthook.yml" else root).joinpath(each).exists()
            for each in alternates
        )
        for name, alternates in names.items()
    }
    recipe, lacking = check_recipe(root)
    fields: dict[str, Any] = {
        "manifests": report,
        "files": files,
        "check_recipe": {"path": recipe.name if recipe else None, "lacks": lacking},
        "hook_runs_guard": (top := git_root(root) or root) is not None
        and lefthook_config(top) is not None
        and hook_lacks_guard(top) is None,
        "tests_may_panic": tests_may_panic(root),
    }
    if args.violations:
        fields["violations"] = violations(root)
    return fields


# diff ---------------------------------------------------------------------


@dataclass
class FileChange:
    """One file's side of a change: its text before and after, and the
    numbers of the lines the change added (new side) and removed (old side)."""

    name: str
    old: str = ""
    new: str = ""
    added: list[int] = field(default_factory=list)
    removed: list[int] = field(default_factory=list)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", "-c", "core.quotePath=false", *args], root, check=check)


def has_head(root: Path) -> bool:
    return (
        git(root, "rev-parse", "--verify", "--quiet", "HEAD", check=False).returncode
        == 0
    )


def empty_tree(root: Path) -> str:
    return git(root, "hash-object", "-t", "tree", os.devnull).stdout.strip()


def revision(root: Path, base: str | None) -> str:
    """What the working tree is compared with: the merge base with `base`, so a
    pull request lists only its own changes; else HEAD; else the empty tree."""
    if base:
        git(root, "rev-parse", "--verify", f"{base}^{{commit}}")
        return git(root, "merge-base", base, "HEAD").stdout.strip()
    return "HEAD" if has_head(root) else empty_tree(root)


def changed_files(
    root: Path, rev: str | None, committed: bool = False
) -> list[FileChange]:
    """Every file the change touches, with both sides read in full. `rev` None
    means the staged change. With `committed`, HEAD against `rev`, as a pull
    request shows it; otherwise the working tree against `rev`, untracked
    files included."""
    if rev is None:
        source = ["--cached"]
    elif committed:
        source = [rev, "HEAD"]
    else:
        source = [rev]
    listing = git(root, "diff", "--no-renames", "--name-only", "-z", *source).stdout
    names = [name for name in listing.split("\0") if name]
    if rev is not None and not committed:
        others = git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout
        names += [name for name in others.split("\0") if name and name not in names]
    old_ref = "HEAD" if rev is None else rev
    unborn = not has_head(root) and rev in (None, empty_tree(root))
    changes: list[FileChange] = []
    for name in names:
        change = FileChange(name)
        if not unborn:
            shown = git(root, "show", f"{old_ref}:{name}", check=False)
            change.old = shown.stdout if shown.returncode == 0 else ""
        if rev is None or committed:
            shown = git(
                root, "show", f"{'HEAD' if committed else ''}:{name}", check=False
            )
            change.new = shown.stdout if shown.returncode == 0 else ""
        else:
            path = root / name
            change.new = path.read_text(errors="replace") if path.is_file() else ""
        changes.append(change)
        hunks = git(
            root,
            "diff",
            "--no-renames",
            "--no-color",
            "--no-ext-diff",
            "-U0",
            *source,
            "--",
            name,
        ).stdout
        if not hunks:
            change.added = list(range(1, len(change.new.splitlines()) + 1))
            change.removed = list(range(1, len(change.old.splitlines()) + 1))
            continue
        for header in re.finditer(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", hunks, re.MULTILINE
        ):
            old_start, old_count, new_start, new_count = header.groups()
            old_n = 1 if old_count is None else int(old_count)
            new_n = 1 if new_count is None else int(new_count)
            change.removed += range(int(old_start), int(old_start) + old_n)
            change.added += range(int(new_start), int(new_start) + new_n)
    return changes


def test_lines(text: str) -> set[int]:
    """Line numbers inside a `#[cfg(test)]` item or a `#[test]` function,
    found by matching braces on code without strings and comments."""
    inside: set[int] = set()
    pending = False
    depth = 0
    start_depth: int | None = None
    for number, line in enumerate(text.splitlines(), 1):
        code = code_only(line)
        if start_depth is None and (CFG_TEST.search(code) or TEST_ATTR.search(code)):
            pending = True
        if pending or start_depth is not None:
            inside.add(number)
        for char in code:
            if char == "{":
                if pending and start_depth is None:
                    start_depth = depth
                    pending = False
                depth += 1
            elif char == "}":
                depth -= 1
                if start_depth is not None and depth == start_depth:
                    start_depth = None
        if pending and code.rstrip().endswith(";"):
            pending = False  # `#[cfg(test)] use …;` covers only that line
    return inside


def block_after(lines: list[str], number: int) -> str:
    """Code of the brace block that opens at or after line `number`."""
    depth = 0
    opened = False
    taken: list[str] = []
    for line in lines[number - 1 :]:
        code = code_only(line)
        taken.append(code)
        for char in code:
            if char == "{":
                depth += 1
                opened = True
            elif char == "}":
                depth -= 1
                if opened and depth == 0:
                    return "\n".join(taken)
        if not opened and code.rstrip().endswith(";"):
            return ""
    return "\n".join(taken)


def module_had_tests(
    name: str, item: str, old: str, text_of: Callable[[str], str]
) -> bool:
    """Whether module `item`, a key such as `modparse`, held tests before the
    change, inline in file `name` or in its own file."""
    found = re.match(r"(?:pub(?:\([^)]*\))?)?mod(\w+)$", item)
    if not found:
        return False
    old_lines = old.splitlines()
    for number, line in enumerate(old_lines, 1):
        flat = re.sub(r"\s+", "", code_only(line))
        if re.match(r"(?:pub(?:\([^)]*\))?)?mod" + found[1] + r"\{", flat):
            return bool(TEST_ATTR.search(block_after(old_lines, number)))
    path = Path(name)
    roots = {"lib", "main", "mod"}
    folder = (
        path.parent
        if path.stem in roots
        or path.parent.name in ("tests", "examples", "benches", "bin")
        else path.parent / path.stem
    )
    return any(
        TEST_ATTR.search(
            "".join(code_only(line) for line in text_of(each.as_posix()).splitlines())
        )
        for each in (folder / f"{found[1]}.rs", folder / found[1] / "mod.rs")
    )


def runnable_doctests(text: str) -> int:
    """Rust code fences in doc comments that rustdoc compiles as tests."""
    allowed = {"rust", "should_panic", "compile_fail", "test_harness"}
    count = 0
    inside = False
    for line in text.splitlines():
        found = DOC_LINE.match(line)
        if not found:
            continue
        fence = re.match(r"^\s*```(.*)$", found[1])
        if not fence:
            continue
        if inside:
            inside = False
            continue
        inside = True
        tokens = [each for each in re.split(r"[\s,]+", fence[1].strip()) if each]
        if all(each in allowed or each.startswith("edition") for each in tokens):
            count += 1
    return count


def doc_text(line: str) -> str:
    """The text of a `///` or `//!` doc comment line; empty for other lines."""
    found = DOC_LINE.match(line)
    return found[1] if found else ""


def unsafe_lines(text: str) -> set[int]:
    """Line numbers holding the `unsafe` keyword or inside the braces it opens."""
    inside: set[int] = set()
    pending = False
    depth = 0
    start_depth: int | None = None
    for number, line in enumerate(text.splitlines(), 1):
        code = code_only(line)
        if UNSAFE.search(code):
            inside.add(number)
            if start_depth is None:
                pending = True
        if start_depth is not None:
            inside.add(number)
        for char in code:
            if char == "{":
                if pending and start_depth is None:
                    start_depth = depth
                    pending = False
                depth += 1
            elif char == "}":
                depth -= 1
                if start_depth is not None and depth == start_depth:
                    start_depth = None
        if pending and code.rstrip().endswith(";"):
            pending = False
    return inside


def declared_for_tests(
    name: str, text_of: Callable[[str], str], paths: set[str] | None = None
) -> bool:
    """Whether a parent module declares file `name` as `#[cfg(test)] mod x;`.
    Under `tests/`, every integration test file counts as a parent."""
    path = Path(name)
    stem = path.parent.name if path.stem == "mod" else path.stem
    folder = path.parent.parent if path.stem == "mod" else path.parent
    parents = [folder / "lib.rs", folder / "main.rs", folder / "mod.rs"]
    if folder.name:
        parents.append(folder.parent / f"{folder.name}.rs")
    if folder.name == "tests" and paths is not None:
        parents += sorted(
            Path(each)
            for each in paths
            if posixpath.dirname(each) == folder.as_posix() and each.endswith(".rs")
        )
    pattern = re.compile(
        r"#\[cfg\(test\)\](?:pub(?:\([^)]*\))?)?mod" + re.escape(stem) + ";"
    )
    for parent in parents:
        text = text_of(parent.as_posix())
        code = re.sub(
            r"\s+", "", "".join(code_only(line) for line in text.splitlines())
        )
        if pattern.search(code):
            return True
    return False


def manifest_for(
    root: Path, name: str, text_of: Callable[[str], str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The manifest owning file `name`, and the workspace root manifest."""
    folder = Path(name).parent
    owner: dict[str, Any] = {}
    workspace: dict[str, Any] = {}
    while True:
        candidate = (folder / "Cargo.toml").as_posix().removeprefix("./")
        text = text_of(candidate)
        if text:
            try:
                parsed = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                parsed = {}
            if not owner and "package" in parsed:
                owner = parsed
            if "workspace" in parsed:
                workspace = parsed
                owner = owner or parsed
                break
        if folder == Path("."):
            break
        folder = folder.parent
    return owner, workspace


def workspace_folder(name: str, text_of: Callable[[str], str]) -> str | None:
    """Repository folder of the workspace root above manifest `name`, or None."""
    folder = posixpath.dirname(name)
    while True:
        text = text_of(posixpath.join(folder, "Cargo.toml"))
        if text and re.search(r"^\[workspace\]", text, re.MULTILINE):
            return folder
        if not folder:
            return None
        folder = posixpath.dirname(folder)


def flat_lints(manifest: dict[str, Any]) -> dict[str, str]:
    """Every lint setting, priority included, as `[workspace.]lints.tool.name`."""
    flat: dict[str, str] = {}
    tables = (
        ("lints", manifest.get("lints", {})),
        ("workspace.lints", manifest.get("workspace", {}).get("lints", {})),
    )
    for prefix, lints in tables:
        for tool, table in lints.items():
            if isinstance(table, dict):
                for lint, value in table.items():
                    flat[f"{prefix}.{tool}.{lint}"] = (
                        value
                        if isinstance(value, str)
                        else json.dumps(value, sort_keys=True)
                    )
            else:
                flat[f"{prefix}.{tool}"] = json.dumps(table)
    return flat


def dependency_names(manifest: dict[str, Any]) -> set[str]:
    """Each dependency as `table.key=package`, so a renamed package shows."""
    names: set[str] = set()
    scopes = [("", manifest), ("workspace.", manifest.get("workspace", {}))]
    scopes += [
        (f"target.{target}.", table)
        for target, table in manifest.get("target", {}).items()
    ]
    for prefix, scope in scopes:
        for kind in DEPENDENCY_TABLES:
            for key, spec in scope.get(kind, {}).items():
                package = spec.get("package", key) if isinstance(spec, dict) else key
                names.add(f"{prefix}{kind}.{key}={package}")
    for registry, table in manifest.get("patch", {}).items():
        for key, spec in table.items():
            names.add(f"patch.{registry}.{key}={json.dumps(spec, sort_keys=True)}")
    for key, spec in manifest.get("replace", {}).items():
        names.add(f"replace.{key}={json.dumps(spec, sort_keys=True)}")
    return names


def manifest_exceptions(
    change: FileChange, workspace: dict[str, Any]
) -> list[list[str]]:
    try:
        old = tomllib.loads(change.old) if change.old else {}
        new = tomllib.loads(change.new) if change.new else {}
    except tomllib.TOMLDecodeError as error:
        return [["manifest", change.name, f"invalid TOML: {error}"]]
    found: list[list[str]] = []
    if not new:
        return found
    for added in sorted(dependency_names(new) - dependency_names(old)):
        found.append(["dependency", change.name, added])
    was, now = flat_lints(old), flat_lints(new)
    changed = [
        f"{key}: {was.get(key, 'unset')} -> {now.get(key, 'unset')}"
        for key in sorted(was.keys() | now.keys())
        if was.get(key) != now.get(key)
        and not (key == "lints.workspace" and now.get(key) == "true")
    ]
    if changed:
        found.append(["lints", change.name, "; ".join(changed)])
    workspace_lints = workspace.get("workspace", {}).get("lints")
    if (
        new
        and not old
        and "package" in new
        and "workspace" not in new
        and workspace_lints
        and new.get("lints", {}).get("workspace") is not True
    ):
        found.append(
            ["lints", change.name, "member does not set [lints] workspace = true"]
        )
    discovery = [
        ("package", "autotests"),
        ("package", "autobenches"),
        ("package", "autobins"),
        ("lib", "test"),
        ("lib", "doctest"),
        ("lib", "harness"),
    ]
    switched = [
        ".".join(keys) for keys in discovery if old and dig(old, keys) != dig(new, keys)
    ]
    for target in ("test", "bin"):
        if old and old.get(target) != new.get(target):
            switched.append(f"[[{target}]]")
    if switched:
        found.append(["test_discovery", change.name, ", ".join(switched) + " changed"])
    for scope in ("package", "workspace"):
        shear = (scope, "metadata", "cargo-shear")
        if dig(old, shear) != dig(new, shear):
            found.append(
                ["shear_ignore", change.name, f"[{scope}.metadata.cargo-shear] changed"]
            )
    return found


def dig(table: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        table = table.get(key, {}) if isinstance(table, dict) else {}
    return table


def glob_match(pattern: str, path: str) -> bool:
    """Whether folder `path` matches a Cargo workspace glob, `*` within one
    segment and `**` across segments."""
    parts, names = pattern.split("/"), path.split("/")
    if "**" in parts:
        cut = parts.index("**")
        head, tail = parts[:cut], parts[cut + 1 :]
        return (
            len(names) >= len(head) + len(tail)
            and all(map(fnmatch.fnmatchcase, names[: len(head)], head))
            and all(map(fnmatch.fnmatchcase, names[len(names) - len(tail) :], tail))
        )
    return len(parts) == len(names) and all(map(fnmatch.fnmatchcase, names, parts))


def tree_members(folder: str, manifest: dict[str, Any], paths: set[str]) -> set[str]:
    """Member manifests, as repository paths, that `manifest` at `folder`
    declares, matched against the files of one side of the change."""

    def under(path: str) -> str | None:
        if not folder:
            return path
        return path[len(folder) + 1 :] if path.startswith(folder + "/") else None

    workspace = manifest.get("workspace", {})
    found: set[str] = set()
    if "package" in manifest:
        found.add(posixpath.join(folder, "Cargo.toml"))
    excludes = [posixpath.normpath(each) for each in workspace.get("exclude", [])]
    patterns = [posixpath.normpath(each) for each in workspace.get("members", [])]
    for path in paths:
        if posixpath.basename(path) != "Cargo.toml":
            continue
        relative = under(posixpath.dirname(path))
        if relative is None:
            continue
        relative = relative or "."
        segments = relative.split("/")
        if any(
            glob_match(each, "/".join(segments[:size]))
            for each in excludes
            for size in range(1, len(segments) + 1)
        ):
            continue
        if any(glob_match(each, relative) for each in patterns):
            found.add(path)
    return found


def package_name(text: str) -> str:
    try:
        return str(tomllib.loads(text).get("package", {}).get("name", ""))
    except tomllib.TOMLDecodeError:
        return ""


def joined_members(
    change: FileChange,
    text_of: Callable[[str], str],
    old_paths: set[str],
    new_paths: set[str],
    old_of: Callable[[str], str] | None = None,
) -> list[list[str]]:
    """Members a changed workspace root drops, and members it now declares
    that do not inherit its lints, even when their own files did not change.
    Membership comes from the files of each side, never the working tree."""
    try:
        old = tomllib.loads(change.old) if change.old else {}
        new = tomllib.loads(change.new) if change.new else {}
    except tomllib.TOMLDecodeError:
        return []
    found: list[list[str]] = []
    folder = posixpath.dirname(change.name)
    before = tree_members(folder, old, old_paths) if "workspace" in old else set()
    after = tree_members(folder, new, new_paths) if "workspace" in new else set()
    renamed = {package_name(text_of(each)) for each in after - before} - {""}
    gone = sorted(
        posixpath.dirname(each) or "."
        for each in before - after
        if old_of is None or package_name(old_of(each)) not in renamed
    )
    if gone:
        found.append(["members_removed", change.name, ", ".join(gone)])
    if "workspace" not in new or not new["workspace"].get("lints"):
        return found
    for relative in sorted(after - before):
        if relative == change.name:
            continue
        text = text_of(relative)
        if not text:
            continue
        try:
            manifest = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            continue
        if manifest.get("lints", {}).get("workspace") is not True:
            found.append(
                ["lints", relative, "member does not set [lints] workspace = true"]
            )
    return found


def protected(name: str) -> bool:
    return (
        Path(name).name in PROTECTED_NAMES
        or name.endswith(PROTECTED_SUFFIXES)
        or name.startswith(PROTECTED_DIRS)
    )


def matches(
    text: str, lines: list[int], exempt: set[int], regex: re.Pattern[str]
) -> list[int]:
    """Line numbers among `lines`, outside `exempt`, once per match on the
    line's code."""
    all_lines = text.splitlines()
    return [
        number
        for number in lines
        if number <= len(all_lines) and number not in exempt
        for _ in regex.finditer(code_only(all_lines[number - 1]))
    ]


def test_names(text: str, lines: list[int]) -> set[str]:
    """Names of the test functions whose `#[test]` line is among `lines`."""
    all_lines = text.splitlines()
    names: set[str] = set()
    for number in lines:
        if number <= len(all_lines) and TEST_ATTR.search(
            code_only(all_lines[number - 1])
        ):
            for following in all_lines[number - 1 : number + 5]:
                found = TEST_FN.search(code_only(following))
                if found:
                    names.add(found[1])
                    break
    return names


def diff(args: argparse.Namespace) -> dict[str, Any]:
    start = Path(args.path).resolve()
    root = Path(git(start, "rev-parse", "--show-toplevel").stdout.strip())
    rev = None if args.staged else revision(root, args.base)
    committed = args.base is not None
    changes = changed_files(root, rev, committed)
    by_name = {change.name: change for change in changes}

    def new_text(name: str) -> str:
        if name in by_name:
            return by_name[name].new
        if args.staged or committed:
            shown = git(
                root, "show", f"{'HEAD' if committed else ''}:{name}", check=False
            )
            return shown.stdout if shown.returncode == 0 else ""
        path = root / name
        return path.read_text(errors="replace") if path.is_file() else ""

    def old_text(name: str) -> str:
        if name in by_name:
            return by_name[name].old
        shown = git(root, "show", f"{rev or 'HEAD'}:{name}", check=False)
        return shown.stdout if shown.returncode == 0 else ""

    old_ref = rev or "HEAD"
    new_ref = "HEAD" if committed else ("index" if args.staged else "worktree")
    listed: dict[str, set[str]] = {}

    def tree_paths(ref: str) -> set[str]:
        """Files on one side of the change: a commit, the index, or the working tree."""
        if ref not in listed:
            if ref == "worktree":
                command = [
                    "ls-files",
                    "-z",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                ]
            elif ref == "index":
                command = ["ls-files", "-z", "--cached"]
            else:
                command = ["ls-tree", "-r", "-z", "--name-only", ref]
            found = git(root, *command, check=False)
            names = {name for name in found.stdout.split("\0") if name}
            if ref == "worktree":
                names = {name for name in names if (root / name).is_file()}
            listed[ref] = names if found.returncode == 0 else set()
        return listed[ref]

    exceptions: list[list[str]] = []
    notes: dict[str, int] = {}
    removed_tests: set[str] = set()
    added_tests: set[str] = set()
    assertions = 0
    doctests = 0
    test_modules = 0
    gated_modules = 0
    was: dict[tuple[str, str], int] = {}
    was_unsafe: dict[str, int] = {}
    for change in changes:
        if not change.name.endswith(".rs"):
            continue
        for _, attribute, item, _ in attributes(change.old):
            was[(attribute, item)] = was.get((attribute, item), 0) + 1
        old_unsafe = unsafe_lines(change.old)
        old_lines = change.old.splitlines()
        for number in change.removed:
            text = code_only(old_lines[number - 1]) if number <= len(old_lines) else ""
            if number in old_unsafe and text.strip() not in ("", "}"):
                key = re.sub(r"\s+", "", text)
                was_unsafe[key] = was_unsafe.get(key, 0) + 1
    for change in sorted(changes, key=lambda each: each.name):
        name = change.name
        if protected(name):
            exceptions.append(["protected", name, "edits a file the gate depends on"])
        if Path(name).name == "Cargo.toml":
            _, workspace = manifest_for(root, name, new_text)
            top = workspace_folder(name, new_text)
            if top is not None and name not in tree_members(
                top, workspace, tree_paths(new_ref) | {name}
            ):
                workspace = {}
            exceptions += manifest_exceptions(change, workspace)
            exceptions += joined_members(
                change, new_text, tree_paths(old_ref), tree_paths(new_ref), old_text
            )
        if not name.endswith(".rs"):
            continue
        owner, workspace = manifest_for(root, name, new_text)
        lints = effective_lints(owner, workspace)
        new_lines = change.new.splitlines()
        old_tests, new_tests = test_lines(change.old), test_lines(change.new)
        if INNER_CFG_TEST.search(
            "".join(code_only(line) for line in change.old.splitlines()[:50])
        ):
            old_tests = set(range(1, len(change.old.splitlines()) + 1))
        if INNER_CFG_TEST.search(
            "".join(code_only(line) for line in change.new.splitlines()[:50])
        ):
            new_tests = set(range(1, len(change.new.splitlines()) + 1))
        if declared_for_tests(name, old_text, tree_paths(old_ref)):
            old_tests = set(range(1, len(change.old.splitlines()) + 1))
        if declared_for_tests(name, new_text, tree_paths(new_ref)):
            new_tests = set(range(1, len(change.new.splitlines()) + 1))
        old_code = "".join(code_only(line) for line in change.old.splitlines())
        had_tests = bool(TEST_ATTR.search(old_code))
        old_flat = re.sub(r"\s+", "", old_code)
        new_attributes = attributes(change.new)
        for number, attribute, item, shown in new_attributes:
            if was.get((attribute, item), 0):
                was[(attribute, item)] -= 1
                continue
            for kind, regex in ATTRIBUTES:
                if regex.search(attribute):
                    exceptions.append([kind, f"{name}:{number}", shown])
                    break
            else:
                inner = attribute.startswith("#![cfg(") and had_tests
                stack = [
                    other
                    for line, other, other_item, _ in new_attributes
                    if other_item == item and abs(line - number) <= 10
                ]
                on_test = any(
                    TEST_ATTR.search(other) or CFG_TEST.search(other) for other in stack
                ) or module_had_tests(name, item, change.old, old_text)
                existed = bool(item) and item in old_flat
                if DISABLING_CFG.match(attribute) and (inner or (on_test and existed)):
                    exceptions.append(["tests_disabled", f"{name}:{number}", shown])
        new_unsafe = unsafe_lines(change.new)
        for number in change.added:
            text = code_only(new_lines[number - 1]) if number <= len(new_lines) else ""
            if number in new_unsafe and text.strip() not in ("", "}"):
                key = re.sub(r"\s+", "", text)
                if was_unsafe.get(key, 0):
                    was_unsafe[key] -= 1
                else:
                    exceptions.append(
                        ["unsafe", f"{name}:{number}", new_lines[number - 1].strip()]
                    )
        old_modules = len(
            TEST_MODULE.findall(
                re.sub(
                    r"\s+",
                    "",
                    "".join(code_only(line) for line in change.old.splitlines()),
                )
            )
        )
        new_modules = len(
            TEST_MODULE.findall(
                re.sub(
                    r"\s+",
                    "",
                    "".join(code_only(line) for line in change.new.splitlines()),
                )
            )
        )
        old_cfg, new_cfg = (
            sum(
                1
                for _, attribute, item, _ in attributes(text)
                if CFG_TEST.search(attribute)
                and re.match(r"(?:pub(?:\([^)]*\))?)?mod\w", item)
            )
            for text in (change.old, change.new)
        )
        gated_modules += new_cfg - old_cfg
        test_modules += new_modules - old_modules
        for pattern in PATTERNS:
            if pattern.ratchet and lint_level(
                lints.get("clippy", {}).get(pattern.ratchet)
            ) in ("deny", "forbid"):
                continue
            new_exempt = new_tests if pattern.tests_exempt else set()
            old_exempt = old_tests if pattern.tests_exempt else set()
            added = matches(change.new, change.added, new_exempt, pattern.regex)
            removed = matches(change.old, change.removed, old_exempt, pattern.regex)
            # A net count per file, so moving or reformatting a line that
            # already held the pattern adds nothing
            for number in added[len(removed) :] if len(added) > len(removed) else []:
                exceptions.append(
                    [pattern.kind, f"{name}:{number}", new_lines[number - 1].strip()]
                )
        was_todo: dict[str, int] = {}
        old_lines = change.old.splitlines()
        for number in change.removed:
            comment = (
                comment_of(old_lines[number - 1]) if number <= len(old_lines) else ""
            )
            if TODO.search(comment) and not ISSUE_LINK.search(comment):
                was_todo[comment.strip()] = was_todo.get(comment.strip(), 0) + 1
        for number in change.added:
            line = new_lines[number - 1] if number <= len(new_lines) else ""
            comment = comment_of(line)
            todo = TODO.search(comment)
            if not todo or ISSUE_LINK.search(comment):
                continue
            if was_todo.get(comment.strip(), 0):
                was_todo[comment.strip()] -= 1
                continue
            exceptions.append(
                [
                    "todo",
                    f"{name}:{number}",
                    f"{todo[1]} without an issue link: {line.strip()}",
                ]
            )
        for kind, regex in NOTES:
            delta = len(matches(change.new, change.added, set(), regex)) - len(
                matches(change.old, change.removed, set(), regex)
            )
            notes[kind] = notes.get(kind, 0) + delta
        removed_tests |= test_names(change.old, change.removed)
        added_tests |= test_names(change.new, change.added)
        assertions += len(matches(change.new, change.added, set(), ASSERTION))
        assertions -= len(matches(change.old, change.removed, set(), ASSERTION))
        old_lines = change.old.splitlines()
        added_docs = [
            doc_text(new_lines[n - 1]) for n in change.added if n <= len(new_lines)
        ]
        removed_docs = [
            doc_text(old_lines[n - 1]) for n in change.removed if n <= len(old_lines)
        ]
        assertions += sum(len(ASSERTION.findall(code_only(doc))) for doc in added_docs)
        assertions -= sum(
            len(ASSERTION.findall(code_only(doc))) for doc in removed_docs
        )
        doctests += runnable_doctests(change.new) - runnable_doctests(change.old)
    if gated_modules < 0:
        exceptions.append(
            ["tests_disabled", ".", f"{-gated_modules} fewer #[cfg(test)] modules"]
        )
    if test_modules < 0:
        exceptions.append(
            [
                "test_module_removed",
                ".",
                f"{-test_modules} fewer #[cfg(test)] mod declarations",
            ]
        )
    if doctests < 0:
        exceptions.append(
            ["doctest_disabled", ".", f"{-doctests} fewer runnable doctests"]
        )
    gone = sorted(removed_tests - added_tests)
    if gone:
        exceptions.append(["tests_removed", ".", ", ".join(gone)])
    if assertions < 0:
        exceptions.append(
            ["assertions_removed", ".", f"{-assertions} fewer assertions"]
        )
    exceptions = [
        list(each) for each in dict.fromkeys(tuple(each) for each in exceptions)
    ]
    fields: dict[str, Any] = {}
    if exceptions:
        fields["exceptions"] = exceptions
    note_list = [
        [kind, ".", f"+{count}; check the design, as references/shortcuts.md says"]
        for kind, count in sorted(notes.items())
        if count > 0
    ]
    if note_list:
        fields["notes"] = note_list
    if exceptions and not args.report:
        raise ScriptError(
            f"{len(exceptions)} exception(s) need explicit approval before they stay; "
            "stop and ask; once approved, commit the change, and list it in the PR with "
            "diff --base <base branch> --report",
            report=fields,
        )
    return fields


EXIT_CODES = exit_codes({1: "failure, or diff found exceptions without --report"})
EPILOG = """examples:
  uv run <skill>/scripts/rust_guard.py init --dry-run
  uv run <skill>/scripts/rust_guard.py audit --violations path/to/crate
  uv run scripts/rust_guard.py diff
  uv run scripts/rust_guard.py diff --staged
  uv run scripts/rust_guard.py diff --base origin/main --report"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        exit_codes=EXIT_CODES, description=__doc__, epilog=EPILOG, prog="rust_guard.py"
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")
    helps = {
        "init": "write the guardrails into a crate or workspace; a rerun changes nothing",
        "audit": "list what the project lacks against the lint profile",
        "diff": "list the exceptions a change adds; fails when it finds one",
    }
    sub = {
        name: commands.add_parser(
            name, help=text, description=text, exit_codes=EXIT_CODES
        )
        for name, text in helps.items()
    }
    for each in sub.values():
        each.add_argument(
            "path", nargs="?", default=".", help="crate or workspace root (default: .)"
        )
    sub["init"].add_argument(
        "-n", "--dry-run", action="store_true", help="list the changes without writing"
    )
    sub["audit"].add_argument(
        "--violations",
        action="store_true",
        help="also run Clippy and count findings per profile lint",
    )
    where = sub["diff"].add_mutually_exclusive_group()
    where.add_argument(
        "--base",
        help="list what the commits since the merge base with this revision add, such as "
        "origin/main for a pull request; uncommitted changes are ignored "
        "(default: compare the working tree with HEAD, or the empty tree before the first commit)",
    )
    where.add_argument(
        "--staged",
        action="store_true",
        help="check the staged changes only, for a pre-commit hook",
    )
    sub["diff"].add_argument(
        "--report",
        action="store_true",
        help="list exceptions without failing; use only after explicit approval",
    )
    work = {"init": init, "audit": audit, "diff": diff}
    argv = list(sys.argv[1:] if argv is None else argv)
    leading = 0
    while leading < len(argv) and argv[leading] in ("-v", "--verbose", "--debug"):
        leading += 1
    if argv[leading : leading + 1] == ["help"]:
        argv = [*argv[:leading], *argv[leading + 1 : leading + 2], "--help"]
    command = next((arg for arg in argv if not arg.startswith("-")), None)
    options = argv[: argv.index("--")] if "--" in argv else argv
    if (
        command is not None
        and command not in work
        and "--" not in argv[: argv.index(command)]
        and not {"-h", "--help"} & set(options)
    ):
        close = difflib.get_close_matches(command, list(work), n=1)
        hint = f"; did you mean '{close[0]}'?" if close else ""
        return answer(
            USAGE,
            {
                "errors": [f"unknown command '{command}'{hint}"],
                "help": "rust_guard.py --help",
            },
        )
    return run_script(
        parser, lambda args: work[args.command](args), argv, debug="RUST_GUARD_DEBUG"
    )


if __name__ == "__main__":
    raise SystemExit(main())

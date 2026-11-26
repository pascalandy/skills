# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Set up, audit, and gate the Rust guardrails this skill describes.

init   writes the lint profile into Cargo.toml, plus clippy.toml, deny.toml,
       a justfile `check` recipe, lefthook.yml, a copy of this script under
       scripts/, and the exception rule in AGENTS.md. Files the project already
       has keep their content; a rerun changes nothing.
audit  compares every manifest's [lints] with the profile and lists what the
       project lacks. --violations also runs Clippy with the whole profile and
       counts the findings per lint, so lints at zero can be turned on now.
diff   lists the exceptions a change adds: unsafe, #[allow], #[expect],
       #[ignore], #[should_panic], removed tests or assertions, new
       dependencies, edited lint or CI files, and TODOs without an issue. It
       fails when it finds one, unless --report is given after explicit approval.

Answers in one JSON line. init lists `changes`; audit lists `manifests` and
`files`; diff lists `exceptions` and `notes`, each as [kind, location, detail].
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

import glob
import subprocess
from pathlib import Path

import tomllib

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets"
LOG = logging.getLogger("rust_guard")

AGENTS_START = "<!-- rust-guard:start -->"
AGENTS_END = "<!-- rust-guard:end -->"

# Files whose edit changes what the gate checks. A change to any of them is an
# exception, because loosening one silently loosens every later check
PROTECTED = (
    "clippy.toml",
    ".clippy.toml",
    "deny.toml",
    "rustfmt.toml",
    ".rustfmt.toml",
    "rust-toolchain",
    "rust-toolchain.toml",
    "justfile",
    "Justfile",
    "lefthook.yml",
    ".cargo/config.toml",
    "scripts/rust_guard.py",
)
PROTECTED_DIRS = (".github/workflows/",)
DEPENDENCY_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")

EXCEPTION_PATTERNS = (
    ("unsafe", re.compile(r"\bunsafe\b")),
    ("allow", re.compile(r"#!?\[\s*allow\s*\(")),
    ("expect", re.compile(r"#!?\[\s*expect\s*\(")),
    ("ignore", re.compile(r"#\[\s*ignore\b")),
    ("should_panic", re.compile(r"#\[\s*should_panic\b")),
)
TODO = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
ISSUE_LINK = re.compile(r"#\d+|https?://")
TEST_ATTR = re.compile(r"#\[\s*(?:[\w:]+::)?test\b")
ASSERTION = re.compile(r"\b(?:debug_)?assert(?:_eq|_ne|_matches)?!\s*\(")
TEST_CONTEXT = re.compile(r"#\[\s*cfg\s*\(\s*test\s*\)\s*\]")
TEST_DIRS = ("tests/", "benches/", "examples/")
# Shortcuts a project may not deny yet; diff flags new ones so existing debt
# stays as it is while additions stop (the ratchet)
RATCHET = (
    ("unwrap_used", re.compile(r"\.unwrap\(\)")),
    ("expect_used", re.compile(r"\.expect\(")),
    ("panic", re.compile(r"\bpanic!\s*\(")),
    ("todo", re.compile(r"\btodo!\s*\(")),
    ("unimplemented", re.compile(r"\bunimplemented!\s*\(")),
    ("dbg_macro", re.compile(r"\bdbg!\s*\(")),
)
# Counted, not blocked: no lint catches them reliably, so the reviewer judges
NOTE_PATTERNS = (
    ("clone", re.compile(r"\.clone\(\)")),
    (
        "arc_mutex",
        re.compile(
            r"Arc<\s*(?:std::sync::|tokio::sync::|parking_lot::)?(?:Mutex|RwLock)\b"
        ),
    ),
)


def profile() -> dict[str, dict[str, str]]:
    """The lint profile, as [lints] tables keyed by tool."""
    return tomllib.loads((ASSETS / "lints.toml").read_text())["lints"]


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
    """Manifest paths of the workspace members, root package included."""
    found: list[Path] = []
    if "package" in manifest:
        found.append(root / "Cargo.toml")
    workspace = manifest.get("workspace", {})
    excluded = {(root / item).resolve() for item in workspace.get("exclude", [])}
    for pattern in workspace.get("members", []):
        for match in sorted(glob.glob(str(root / pattern))):
            folder = Path(match).resolve()
            candidate = folder / "Cargo.toml"
            if (
                folder not in excluded
                and candidate.is_file()
                and candidate not in found
            ):
                found.append(candidate)
    return found


def lint_level(value: Any) -> str:
    return value.get("level", "") if isinstance(value, dict) else str(value)


def effective_lints(
    path: Path, root_manifest: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    lints = read_toml(path).get("lints", {})
    if lints.get("workspace") is True:
        return root_manifest.get("workspace", {}).get("lints", {})
    return lints


def missing_lints(lints: dict[str, dict[str, Any]]) -> list[str]:
    wanted = profile()
    return [
        f"{tool}::{name}" if tool != "rust" else name
        for tool, table in wanted.items()
        for name, level in table.items()
        if lint_level(lints.get(tool, {}).get(name)) not in ("deny", "forbid")
        or (level == "forbid" and lint_level(lints.get(tool, {}).get(name)) != "forbid")
    ]


def denied(lints: dict[str, dict[str, Any]], name: str) -> bool:
    return lint_level(lints.get("clippy", {}).get(name)) in ("deny", "forbid")


def run(
    command: list[str], cwd: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    LOG.debug("run: %s (in %s)", shlex.join(command), cwd)
    try:
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, check=False
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


# init ---------------------------------------------------------------------


def lint_block(workspace: bool) -> str:
    text = (ASSETS / "lints.toml").read_text()
    return text.replace("[lints.", "[workspace.lints.") if workspace else text


def plan_init(root: Path) -> list[tuple[str, str, Path, str]]:
    """Each change init would make, as (action, object, path, new text)."""
    plans: list[tuple[str, str, Path, str]] = []
    manifest_path = root / "Cargo.toml"
    manifest = read_toml(manifest_path)
    original = manifest_path.read_text()
    text = original
    is_workspace = "workspace" in manifest
    if is_workspace and "lints" not in manifest["workspace"]:
        text = text.rstrip("\n") + "\n\n" + lint_block(workspace=True)
    if "package" in manifest and "lints" not in manifest:
        block = (
            "[lints]\nworkspace = true\n"
            if is_workspace
            else lint_block(workspace=False)
        )
        text = text.rstrip("\n") + "\n\n" + block
    if text != original:
        plans.append(("update", "Cargo.toml", manifest_path, text))
    for member in members(root, manifest):
        if member == manifest_path or "lints" in read_toml(member):
            continue
        member_text = (
            member.read_text().rstrip("\n") + "\n\n[lints]\nworkspace = true\n"
        )
        plans.append(("update", str(member.relative_to(root)), member, member_text))
    for name in ("clippy.toml", "deny.toml", "justfile", "lefthook.yml"):
        target = root / name
        if not target.exists() and not (
            name == "justfile" and (root / "Justfile").exists()
        ):
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
        current = agents.read_text()
        pattern = re.compile(
            re.escape(AGENTS_START) + r".*?" + re.escape(AGENTS_END) + r"\n?", re.DOTALL
        )
        if AGENTS_START in current:
            updated = pattern.sub(lambda _match: block, current, count=1)
        else:
            updated = current.rstrip("\n") + "\n\n" + block
        if updated != current:
            plans.append(("update", "AGENTS.md", agents, updated))
    return plans


def init(args: argparse.Namespace) -> dict[str, Any]:
    root = root_of(args.path)
    for recipe in (root / "justfile", root / "Justfile"):
        if recipe.exists() and not re.search(
            r"^check\b[^:]*:", recipe.read_text(), re.MULTILINE
        ):
            raise ScriptError(
                f"{recipe.name} has no `check` recipe; copy the one in {ASSETS / 'justfile'} into it, then rerun init"
            )
    changes: list[list[str]] = []
    for action, name, path, text in plan_init(root):
        changes.append([action, name])
        if not args.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    if not (root / "Cargo.lock").exists():
        changes.append(["create", "Cargo.lock", "cargo generate-lockfile"])
        if not args.dry_run:
            run(["cargo", "generate-lockfile"], root)
    return {"changes": changes} if changes else {}


# audit --------------------------------------------------------------------


def violations(root: Path) -> dict[str, int]:
    """Clippy findings per profile lint, with the whole profile at warn."""
    flags: list[str] = []
    for tool, table in profile().items():
        for name in table:
            flags += ["-W", f"clippy::{name}" if tool == "clippy" else name]
    result = run(
        [
            "cargo",
            "clippy",
            "--all-targets",
            "--all-features",
            "--message-format=json",
            "--quiet",
            "--",
            *flags,
        ],
        root,
        check=False,
    )
    return count_findings(result.stdout)


def count_findings(stream: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    seen: set[tuple[str, str, int]] = set()
    for line in stream.splitlines():
        if not line.startswith("{"):
            continue
        record = json.loads(line)
        message = record.get("message") or {}
        code = (message.get("code") or {}).get("code")
        if record.get("reason") != "compiler-message" or not code:
            continue
        spans = message.get("spans") or [{}]
        key = (code, spans[0].get("file_name", ""), spans[0].get("line_start", 0))
        if key in seen:
            continue
        seen.add(key)
        name = code.removeprefix("clippy::")
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def audit(args: argparse.Namespace) -> dict[str, Any]:
    root = root_of(args.path)
    root_manifest = read_toml(root / "Cargo.toml")
    report: list[dict[str, Any]] = []
    for path in members(root, root_manifest) or [root / "Cargo.toml"]:
        entry: dict[str, Any] = {"path": str(path.relative_to(root))}
        manifest = read_toml(path)
        if "workspace" in root_manifest and "lints" not in manifest:
            entry["inherits"] = False
        entry["missing"] = missing_lints(effective_lints(path, root_manifest))
        report.append(entry)
    files = {
        name: (root / name).exists()
        for name in (
            "Cargo.lock",
            "clippy.toml",
            "deny.toml",
            "justfile",
            "lefthook.yml",
            "AGENTS.md",
            "scripts/rust_guard.py",
        )
    }
    answer_fields: dict[str, Any] = {"manifests": report, "files": files}
    if args.violations:
        answer_fields["violations"] = violations(root)
    return answer_fields


# diff ---------------------------------------------------------------------


def git(root: Path, *args: str) -> str:
    return run(["git", *args], root).stdout


def base_revision(root: Path, base: str | None) -> str:
    if base:
        return git(root, "rev-parse", "--verify", f"{base}^{{commit}}").strip()
    for candidate in ("origin/HEAD", "origin/main", "origin/master", "main", "master"):
        found = run(["git", "merge-base", "HEAD", candidate], root, check=False)
        if found.returncode == 0:
            return found.stdout.strip()
    raise UsageError("cannot find the default branch; pass --base <rev>")


def changed_lines(
    root: Path, revision: str | None, staged: bool
) -> dict[str, tuple[list[tuple[int, str]], list[str]]]:
    """Added lines with their new line numbers, and removed lines, per file."""
    command = ["diff", "--no-color", "--no-ext-diff", "-U0"]
    command += ["--cached"] if staged else [revision or "HEAD"]
    files: dict[str, tuple[list[tuple[int, str]], list[str]]] = {}
    current: str | None = None
    line_number = 0
    for line in git(root, *command).splitlines():
        if line.startswith("+++ "):
            current = None if line == "+++ /dev/null" else line[6:]
            if current is not None:
                files.setdefault(current, ([], []))
        elif line.startswith("--- "):
            old = line[6:] if line != "--- /dev/null" else None
            if old is not None:
                files.setdefault(old, ([], []))
                current = old
        elif line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            line_number = int(match[1]) if match else 0
        elif line.startswith("+") and current is not None:
            files[current][0].append((line_number, line[1:]))
            line_number += 1
        elif line.startswith("-") and current is not None:
            files[current][1].append(line[1:])
    if not staged:
        for name in git(
            root, "ls-files", "--others", "--exclude-standard"
        ).splitlines():
            path = root / name
            if path.is_file():
                try:
                    text = path.read_text()
                except UnicodeDecodeError:
                    continue
                files[name] = (
                    [
                        (number, text_line)
                        for number, text_line in enumerate(text.splitlines(), 1)
                    ],
                    [],
                )
    return files


def old_text(root: Path, revision: str | None, staged: bool, name: str) -> str:
    spec = f"HEAD:{name}" if staged else f"{revision}:{name}"
    shown = run(["git", "show", spec], root, check=False)
    return shown.stdout if shown.returncode == 0 else ""


def new_text(root: Path, staged: bool, name: str) -> str:
    if staged:
        shown = run(["git", "show", f":{name}"], root, check=False)
        return shown.stdout if shown.returncode == 0 else ""
    path = root / name
    return path.read_text() if path.is_file() else ""


def dependency_names(manifest: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    tables = [manifest, manifest.get("workspace", {})]
    tables += list(manifest.get("target", {}).values())
    for table in tables:
        for kind in DEPENDENCY_TABLES:
            names.update(f"{kind}.{name}" for name in table.get(kind, {}))
    return names


def manifest_exceptions(name: str, before: str, after: str) -> list[list[str]]:
    try:
        old = tomllib.loads(before) if before else {}
        new = tomllib.loads(after) if after else {}
    except tomllib.TOMLDecodeError as error:
        return [["manifest", name, f"invalid TOML: {error}"]]
    found: list[list[str]] = []
    for added in sorted(dependency_names(new) - dependency_names(old)):
        found.append(["dependency", name, added])
    if old:
        was, now = flat_lints(old), flat_lints(new)
        changed = [
            f"{key}: {was.get(key, 'unset')} -> {now.get(key, 'unset')}"
            for key in sorted(was.keys() | now.keys())
            if was.get(key) != now.get(key)
        ]
        if changed:
            found.append(["lints", name, "; ".join(changed)])
    return found


def flat_lints(manifest: dict[str, Any]) -> dict[str, str]:
    """Every lint setting in a manifest as `[workspace.]lints.tool.name` -> level."""
    flat: dict[str, str] = {}
    for prefix, lints in (
        ("lints", manifest.get("lints", {})),
        ("workspace.lints", manifest.get("workspace", {}).get("lints", {})),
    ):
        for tool, table in lints.items():
            if isinstance(table, dict):
                for lint, value in table.items():
                    flat[f"{prefix}.{tool}.{lint}"] = lint_level(value)
            else:
                flat[f"{prefix}.{tool}"] = str(table).lower()
    return flat


def in_test_context(name: str, text: str, number: int) -> bool:
    if name.startswith(TEST_DIRS) or "/tests/" in name:
        return True
    lines = text.splitlines()
    for index, line in enumerate(lines[: number - 1], 1):
        if TEST_CONTEXT.search(line):
            return index < number
    return False


def diff(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(git(Path(args.path).resolve(), "rev-parse", "--show-toplevel").strip())
    revision = None if args.staged else base_revision(root, args.base)
    root_manifest_path = root / "Cargo.toml"
    root_manifest = (
        read_toml(root_manifest_path) if root_manifest_path.is_file() else {}
    )
    lints = root_manifest.get("workspace", {}).get("lints") or root_manifest.get(
        "lints", {}
    )
    exceptions: list[list[str]] = []
    notes: list[list[str]] = []
    tests_delta = 0
    assertions_delta = 0
    note_counts: dict[str, int] = {}
    for name, (added, removed) in sorted(
        changed_lines(root, revision, args.staged).items()
    ):
        if name in PROTECTED or name.startswith(PROTECTED_DIRS):
            exceptions.append(["protected", name, "edits a file the gate depends on"])
        if name.endswith("Cargo.toml"):
            exceptions += manifest_exceptions(
                name,
                old_text(root, revision, args.staged, name),
                new_text(root, args.staged, name),
            )
        if not name.endswith(".rs"):
            continue
        text = new_text(root, args.staged, name)
        for number, line in added:
            code = line.split("//", 1)[0]
            location = f"{name}:{number}"
            for kind, pattern in EXCEPTION_PATTERNS:
                if pattern.search(code):
                    exceptions.append([kind, location, line.strip()])
            todo = TODO.search(line)
            if todo and not ISSUE_LINK.search(line):
                exceptions.append(
                    [
                        "todo",
                        location,
                        f"{todo[1]} without an issue link: {line.strip()}",
                    ]
                )
            if not in_test_context(name, text, number):
                for lint, pattern in RATCHET:
                    if not denied(lints, lint) and pattern.search(code):
                        exceptions.append([lint, location, line.strip()])
            for kind, pattern in NOTE_PATTERNS:
                note_counts[kind] = note_counts.get(kind, 0) + len(
                    pattern.findall(code)
                )
        for line in removed:
            code = line.split("//", 1)[0]
            for kind, pattern in NOTE_PATTERNS:
                note_counts[kind] = note_counts.get(kind, 0) - len(
                    pattern.findall(code)
                )
        tests_delta += sum(bool(TEST_ATTR.search(line)) for _, line in added) - sum(
            bool(TEST_ATTR.search(line)) for line in removed
        )
        assertions_delta += sum(
            len(ASSERTION.findall(line)) for _, line in added
        ) - sum(len(ASSERTION.findall(line)) for line in removed)
    if tests_delta < 0:
        exceptions.append(
            ["tests_removed", ".", f"{-tests_delta} fewer test functions"]
        )
    if assertions_delta < 0:
        exceptions.append(
            ["assertions_removed", ".", f"{-assertions_delta} fewer assertions"]
        )
    for kind, count in sorted(note_counts.items()):
        if count > 0:
            notes.append(
                [
                    kind,
                    ".",
                    f"+{count}; check the design, as references/shortcuts.md says",
                ]
            )
    fields: dict[str, Any] = {}
    if exceptions:
        fields["exceptions"] = exceptions
    if notes:
        fields["notes"] = notes
    if exceptions and not args.report:
        raise ScriptError(
            f"{len(exceptions)} exception(s) need explicit approval before they stay; "
            "stop and ask, then rerun with --report and paste the list into the PR",
            report=fields,
        )
    return fields


EXIT_CODES = exit_codes({1: "failure, or diff found exceptions without --report"})
EPILOG = """examples:
  uv run scripts/rust_guard.py init --dry-run
  uv run scripts/rust_guard.py audit --violations path/to/crate
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
        help="compare the working tree with this revision (default: merge-base with the default branch)",
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
    return run_script(
        parser, lambda args: work[args.command](args), argv, debug="RUST_GUARD_DEBUG"
    )


if __name__ == "__main__":
    raise SystemExit(main())

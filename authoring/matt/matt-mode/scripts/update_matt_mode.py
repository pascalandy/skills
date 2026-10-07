"""Update or verify Matt mode's vendored upstream source files."""

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
            return answer(code, {"errors": [word], **carried(stop)})
        except ScriptError as error:
            return answer_failure(error, parser, command)
        except Exception as error:
            # The traceback comes first, so the answer ends stderr
            logging.getLogger(__name__).debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(
                f"{type(error).__name__}: {error}", report=carried(error)
            )
            return answer_failure(
                unexpected, parser, command, rerun=bool(debug) and not tracing
            )


def carried(error: BaseException) -> dict[str, Any]:
    """The `report` an exception carries, such as the changes a run already
    made before an interrupt or a bug, or {} when it carries none."""
    report = getattr(error, "report", None)
    return dict(report) if isinstance(report, Mapping) else {}


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
import posixpath
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

log = logging.getLogger("update-matt-mode")
EXIT_CODES = exit_codes(
    {
        0: "the imports match the lock, or the update succeeded",
        1: "they differ, or it failed",
    }
)

TOOLS = Path(__file__).resolve().parent
DEFAULT_ROOT = TOOLS.parent.parent
LOCK_PATH = PurePosixPath("matt-mode/upstream-lock.json")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
SKILL_CALL = re.compile(
    r"\b(?:call|calls|calling)\s+the Skill tool(?:\s+twice)?\s*,?\s*"
    r'(?:with|for)\s+(?P<names>"[a-z0-9-]+"'
    r'(?:\s*(?:,\s*(?:and\s+)?|and\s+)"[a-z0-9-]+")*)',
    re.IGNORECASE,
)
QUOTED_NAME = re.compile(r'"([a-z0-9-]+)"')
MARKDOWN_TARGET = re.compile(
    r"(?P<prefix>\]\()(?P<open><)?(?P<target>[^)\s>]+)(?P<close>>)?"
    r"(?P<tail>(?:\s+[^)]*)?\))"
)


class ImportError(ScriptError):
    """A user-correctable import or integrity error."""


@dataclass(frozen=True)
class LockMapping:
    name: str
    kind: str
    source: PurePosixPath
    destination: PurePosixPath
    entry: str
    exclude: tuple[PurePosixPath, ...]


@dataclass(frozen=True)
class FileRecord:
    source: PurePosixPath
    destination: PurePosixPath
    source_sha256: str
    rendered_sha256: str
    content: bytes


@dataclass(frozen=True)
class Registry:
    repository: str
    revision: str
    mappings: tuple[LockMapping, ...]
    handoffs: dict[str, str]
    files: tuple[FileRecord, ...]


# How to restore a generated file that is missing
REGENERATE = (
    "; regenerate with: update_matt_mode.py update --upstream DIR --revision SHA"
)


def fail(message: str) -> NoReturn:
    raise ImportError(message)


def safe_relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        fail(f"{label} is not a safe relative path: {value!r}")
    return path


def expect_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"lock file is missing: {path}")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(f"cannot read lock file {path}: {error}")
    if not isinstance(value, dict):
        fail(f"lock file must contain a JSON object: {path}")
    return value


def parse_registry(root: Path) -> Registry:
    lock_path = root / LOCK_PATH
    current = root
    for part in LOCK_PATH.parts:
        current /= part
        if current.is_symlink():
            fail(f"lock path contains a symlink: {current}")
    raw = load_json(lock_path)
    if raw.get("schema_version") != 1:
        fail("lock schema_version must be 1")
    repository = expect_string(raw.get("repository"), "repository")
    revision = expect_string(raw.get("revision"), "revision")
    if FULL_SHA.fullmatch(revision) is None:
        fail("lock revision must be a full lowercase Git SHA")

    raw_mappings = raw.get("mappings")
    if not isinstance(raw_mappings, list) or not raw_mappings:
        fail("lock mappings must be a non-empty list")
    mappings: list[LockMapping] = []
    names: set[str] = set()
    sources: set[PurePosixPath] = set()
    destinations: set[PurePosixPath] = set()
    for index, item in enumerate(raw_mappings):
        label = f"mappings[{index}]"
        if not isinstance(item, dict):
            fail(f"{label} must be an object")
        name = expect_string(item.get("name"), f"{label}.name")
        kind = expect_string(item.get("kind"), f"{label}.kind")
        if kind not in {"internal", "shared"}:
            fail(f"{label}.kind must be internal or shared")
        source = safe_relative(item.get("source"), f"{label}.source")
        destination = safe_relative(item.get("destination"), f"{label}.destination")
        entry = expect_string(item.get("entry"), f"{label}.entry")
        if PurePosixPath(entry).name != entry or not entry.endswith(".md"):
            fail(f"{label}.entry must be one Markdown filename")
        raw_exclude = item.get("exclude")
        if not isinstance(raw_exclude, list):
            fail(f"{label}.exclude must be a list")
        exclude = tuple(
            safe_relative(value, f"{label}.exclude") for value in raw_exclude
        )
        if "SKILL.md" in {str(path) for path in exclude}:
            fail(f"{label}.exclude cannot omit SKILL.md")
        if name in names:
            fail(f"duplicate mapping name: {name}")
        if source in sources:
            fail(f"duplicate mapping source: {source}")
        if destination in destinations:
            fail(f"duplicate mapping destination: {destination}")
        names.add(name)
        sources.add(source)
        destinations.add(destination)
        mappings.append(LockMapping(name, kind, source, destination, entry, exclude))

    raw_handoffs = raw.get("handoffs", {})
    if not isinstance(raw_handoffs, dict):
        fail("lock handoffs must be an object")
    handoffs: dict[str, str] = {}
    for raw_name, raw_target in raw_handoffs.items():
        name = expect_string(raw_name, "handoff name")
        target = expect_string(raw_target, f"handoffs[{name!r}]")
        if name in names:
            fail(f"handoff name conflicts with mapping name: {name}")
        handoffs[name] = target

    raw_files = raw.get("files")
    if not isinstance(raw_files, list):
        fail("lock files must be a list")
    files: list[FileRecord] = []
    file_destinations: set[PurePosixPath] = set()
    for index, item in enumerate(raw_files):
        label = f"files[{index}]"
        if not isinstance(item, dict):
            fail(f"{label} must be an object")
        source = safe_relative(item.get("source"), f"{label}.source")
        destination = safe_relative(item.get("destination"), f"{label}.destination")
        source_sha = expect_string(item.get("source_sha256"), f"{label}.source_sha256")
        rendered_sha = expect_string(
            item.get("rendered_sha256"), f"{label}.rendered_sha256"
        )
        for field_name, digest in (
            ("source_sha256", source_sha),
            ("rendered_sha256", rendered_sha),
        ):
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                fail(f"{label}.{field_name} must be a lowercase SHA256")
        if destination in file_destinations:
            fail(f"duplicate file destination: {destination}")
        file_destinations.add(destination)
        files.append(FileRecord(source, destination, source_sha, rendered_sha, b""))

    return Registry(repository, revision, tuple(mappings), handoffs, tuple(files))


def run_git(checkout: Path, *args: str, binary: bool = False) -> bytes | str:
    command = ["git", "-C", str(checkout), *args]
    try:
        result = subprocess.run(command, capture_output=True, check=False)
    except OSError as error:
        fail(f"cannot run git: {error}")
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"git {' '.join(args)} failed: {detail or 'unknown error'}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict").strip()


def verify_revision(checkout: Path, revision: str) -> None:
    if FULL_SHA.fullmatch(revision) is None:
        fail("--revision must be a full lowercase Git SHA")
    if not checkout.is_dir():
        fail(f"upstream checkout is not a directory: {checkout}")
    resolved = run_git(checkout, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if resolved != revision:
        fail(f"revision does not resolve to the requested commit: {revision}")


def git_tree(checkout: Path, revision: str, source: PurePosixPath) -> list[str]:
    raw = run_git(
        checkout,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        revision,
        "--",
        str(source),
        binary=True,
    )
    assert isinstance(raw, bytes)
    paths: list[str] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, encoded_path = record.split(b"\t", 1)
            mode, object_type, _object_id = metadata.decode("ascii").split(" ")
            path = encoded_path.decode("utf-8")
        except (ValueError, UnicodeError):
            fail(f"cannot parse Git tree entry below {source}")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            fail(f"unsupported Git tree entry {path}: {mode} {object_type}")
        paths.append(path)
    return sorted(paths)


def git_blob(checkout: Path, revision: str, source: PurePosixPath) -> bytes:
    raw = run_git(checkout, "show", f"{revision}:{source}", binary=True)
    assert isinstance(raw, bytes)
    return raw


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def strip_frontmatter(
    content: bytes, source: PurePosixPath, *, keep_description: bool
) -> bytes:
    """The entry's body. A route keeps only its upstream description, which
    `just remote-skills` lists under matt-mode."""
    if not content.startswith(b"---\n"):
        fail(f"source entry has no opening frontmatter: {source}")
    end = content.find(b"\n---\n", 4)
    if end < 0:
        fail(f"source entry has unterminated frontmatter: {source}")
    body = content[end + len(b"\n---\n") :]
    if not keep_description:
        return body
    lines = content[4:end].split(b"\n")
    for index, line in enumerate(lines):
        if not line.startswith(b"description:"):
            continue
        value = line.removeprefix(b"description:").strip()
        following = next((later for later in lines[index + 1 :] if later.strip()), b"")
        # A folded, literal, or wrapped value would need a YAML parser to keep
        if (
            value
            and value[:1] not in (b">", b"|")
            and following[:1] not in (b" ", b"\t")
        ):
            return b"---\n" + line + b"\n---\n" + body
        break
    fail(f"source entry needs a one-line description: {source}")


def render_markdown(
    content: bytes,
    source: PurePosixPath,
    destination: PurePosixPath,
    entry_destinations: dict[PurePosixPath, PurePosixPath],
) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        fail(f"source Markdown is not UTF-8: {source}: {error}")

    def rewrite(match: re.Match[str]) -> str:
        if bool(match.group("open")) != bool(match.group("close")):
            return match.group(0)
        target = match.group("target")
        path_text, separator, fragment = target.partition("#")
        if (
            not path_text
            or path_text.startswith("/")
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path_text)
        ):
            return match.group(0)
        source_target = PurePosixPath(
            posixpath.normpath(str(source.parent / PurePosixPath(path_text)))
        )
        destination_target = entry_destinations.get(source_target)
        if destination_target is None:
            return match.group(0)
        if destination.parts[0] != destination_target.parts[0]:
            fail(
                "cross-package renamed-entry link requires maintainer classification: "
                f"{source} -> {source_target}"
            )
        rendered_target = posixpath.relpath(
            str(destination_target), start=str(destination.parent)
        )
        if path_text.startswith("./") and not rendered_target.startswith("."):
            rendered_target = f"./{rendered_target}"
        if separator:
            rendered_target = f"{rendered_target}#{fragment}"
        return (
            match.group("prefix")
            + (match.group("open") or "")
            + rendered_target
            + (match.group("close") or "")
            + match.group("tail")
        )

    return MARKDOWN_TARGET.sub(rewrite, text).encode("utf-8")


def skill_dependencies(content: bytes) -> set[str]:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        fail(f"source SKILL.md is not UTF-8: {error}")
    dependencies: set[str] = set()
    for match in SKILL_CALL.finditer(text):
        dependencies.update(QUOTED_NAME.findall(match.group("names")))
    return dependencies


def build_plan(
    checkout: Path, revision: str, registry: Registry
) -> tuple[FileRecord, ...]:
    verify_revision(checkout, revision)
    records: list[FileRecord] = []
    known_names = {mapping.name for mapping in registry.mappings} | set(
        registry.handoffs
    )
    entry_destinations = {
        mapping.source / "SKILL.md": mapping.destination / mapping.entry
        for mapping in registry.mappings
    }
    destinations: set[PurePosixPath] = set()
    found_dependencies: set[str] = set()

    license_source = PurePosixPath("LICENSE")
    if git_tree(checkout, revision, license_source) != ["LICENSE"]:
        fail("upstream LICENSE is missing or is not a regular file")
    license_content = git_blob(checkout, revision, license_source)
    license_destination = PurePosixPath("matt-mode/references/LICENSE")
    records.append(
        FileRecord(
            license_source,
            license_destination,
            sha256(license_content),
            sha256(license_content),
            license_content,
        )
    )
    destinations.add(license_destination)

    for mapping in registry.mappings:
        paths = git_tree(checkout, revision, mapping.source)
        if not paths:
            fail(f"mapped source directory is missing or empty: {mapping.source}")
        expected_entry = mapping.source / "SKILL.md"
        if str(expected_entry) not in paths:
            fail(f"mapped source entry is missing: {expected_entry}")
        prefix = f"{mapping.source}/"
        relative_paths = [
            safe_relative(
                path.removeprefix(prefix), f"source file below {mapping.source}"
            )
            for path in paths
        ]
        nested_skills = [
            path
            for path in relative_paths
            if path.name == "SKILL.md" and path.parts != ("SKILL.md",)
        ]
        if nested_skills:
            names = ", ".join(str(path) for path in nested_skills)
            fail(
                f"new nested Skill source requires maintainer classification: {mapping.name}: {names}"
            )
        excluded = set(mapping.exclude)
        missing_exclusions = excluded - set(relative_paths)
        if missing_exclusions:
            names = ", ".join(str(path) for path in sorted(missing_exclusions))
            fail(f"declared metadata exclusion is missing: {mapping.name}: {names}")

        for source_path, relative in zip(paths, relative_paths, strict=True):
            if relative in excluded:
                continue
            source = PurePosixPath(source_path)
            raw = git_blob(checkout, revision, source)
            if relative.suffix.lower() == ".md":
                found_dependencies.update(skill_dependencies(raw))
            if relative.parts == ("SKILL.md",):
                destination = mapping.destination / mapping.entry
                rendered = render_markdown(
                    strip_frontmatter(
                        raw, source, keep_description=mapping.kind == "internal"
                    ),
                    source,
                    destination,
                    entry_destinations,
                )
            else:
                destination = mapping.destination / relative
                rendered = (
                    render_markdown(raw, source, destination, entry_destinations)
                    if relative.suffix.lower() == ".md"
                    else raw
                )
            if destination in destinations:
                fail(f"colliding generated destination: {destination}")
            destinations.add(destination)
            records.append(
                FileRecord(
                    source,
                    destination,
                    sha256(raw),
                    sha256(rendered),
                    rendered,
                )
            )

    unknown = found_dependencies - known_names
    if unknown:
        fail(
            "unclassified Skill dependencies: "
            + ", ".join(sorted(unknown))
            + "; add mappings or classify them before updating"
        )
    return tuple(sorted(records, key=lambda record: str(record.destination)))


def lock_document(
    registry: Registry, revision: str, files: Sequence[FileRecord]
) -> bytes:
    value = {
        "schema_version": 1,
        "repository": registry.repository,
        "revision": revision,
        "mappings": [
            {
                "name": mapping.name,
                "kind": mapping.kind,
                "source": str(mapping.source),
                "destination": str(mapping.destination),
                "entry": mapping.entry,
                "exclude": [str(path) for path in mapping.exclude],
            }
            for mapping in registry.mappings
        ],
        "handoffs": registry.handoffs,
        "files": [
            {
                "source": str(record.source),
                "destination": str(record.destination),
                "source_sha256": record.source_sha256,
                "rendered_sha256": record.rendered_sha256,
            }
            for record in files
        ],
    }
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def local_path(root: Path, relative: PurePosixPath) -> Path:
    return root.joinpath(*relative.parts)


def reject_symlink_path(root: Path, relative: PurePosixPath) -> None:
    current = root
    if current.is_symlink():
        fail(f"bucket root cannot be a symlink: {root}")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            fail(f"generated path contains a symlink: {current}")


def current_digest(path: Path) -> str | None:
    try:
        if not path.exists():
            return None
        if not path.is_file():
            fail(f"generated path is not a regular file: {path}")
        return sha256(path.read_bytes())
    except OSError as error:
        fail(f"cannot inspect generated file {path}: {error}")


def preflight_update(
    root: Path, registry: Registry, planned: Sequence[FileRecord]
) -> tuple[list[FileRecord], list[PurePosixPath]]:
    old_by_destination = {record.destination: record for record in registry.files}
    new_by_destination = {record.destination: record for record in planned}
    writes: list[FileRecord] = []

    for destination, record in new_by_destination.items():
        reject_symlink_path(root, destination)
        path = local_path(root, destination)
        digest = current_digest(path)
        accepted = {record.rendered_sha256}
        old = old_by_destination.get(destination)
        if old is not None:
            accepted.add(old.rendered_sha256)
        if digest is not None and digest not in accepted:
            fail(
                f"refusing to overwrite locally modified generated file: {destination}"
            )
        if digest != record.rendered_sha256:
            writes.append(record)

    removals: list[PurePosixPath] = []
    for destination, old in old_by_destination.items():
        if destination in new_by_destination:
            continue
        reject_symlink_path(root, destination)
        path = local_path(root, destination)
        digest = current_digest(path)
        if digest is None:
            continue
        if digest != old.rendered_sha256:
            fail(f"refusing to delete locally modified generated file: {destination}")
        removals.append(destination)
    return sorted(writes, key=lambda item: str(item.destination)), sorted(removals)


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except OSError as error:
        try:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        except OSError:
            pass
        fail(f"cannot write {path}: {error}")


def prune_empty_parents(path: Path, stop: Path) -> None:
    parent = path.parent
    while parent != stop:
        try:
            parent.rmdir()
        except OSError:
            return
        parent = parent.parent


def generated_inventory(root: Path, registry: Registry) -> set[PurePosixPath]:
    inventory: set[PurePosixPath] = set()
    generated_roots = {
        PurePosixPath("matt-mode/playbooks")
        if mapping.kind == "internal"
        else mapping.destination
        for mapping in registry.mappings
    }
    for generated_root in sorted(generated_roots):
        directory = local_path(root, generated_root)
        reject_symlink_path(root, generated_root)
        if not directory.exists():
            continue
        if not directory.is_dir():
            fail(f"generated directory is not a directory: {generated_root}")
        for path in directory.rglob("*"):
            relative = PurePosixPath(path.relative_to(root).as_posix())
            reject_symlink_path(root, relative)
            if path.is_file():
                inventory.add(relative)
            elif not path.is_dir():
                fail(f"unsupported generated filesystem entry: {relative}")
    license_path = local_path(root, PurePosixPath("matt-mode/references/LICENSE"))
    if license_path.exists():
        inventory.add(PurePosixPath("matt-mode/references/LICENSE"))
    return inventory


def verify_imports(root: Path, upstream: Path | None = None) -> list[str]:
    try:
        registry = parse_registry(root)
    except ImportError as error:
        return [str(error)]
    errors: list[str] = []
    expected = {record.destination: record for record in registry.files}
    for destination, record in expected.items():
        try:
            reject_symlink_path(root, destination)
            digest = current_digest(local_path(root, destination))
        except ImportError as error:
            errors.append(str(error))
            continue
        if digest is None:
            errors.append(f"missing generated file: {destination}{REGENERATE}")
        elif digest != record.rendered_sha256:
            errors.append(
                f"changed generated file: {destination}; restore it from git, or "
                "move your edit out of it, then rerun check"
            )
    try:
        actual = generated_inventory(root, registry)
    except ImportError as error:
        errors.append(str(error))
        actual = set()
    for destination in sorted(actual - set(expected)):
        errors.append(
            f"untracked generated file: {destination}; move or delete it, then "
            "rerun check"
        )

    if upstream is not None:
        try:
            planned = build_plan(upstream, registry.revision, registry)
            planned_by_destination = {record.destination: record for record in planned}
            if set(planned_by_destination) != set(expected):
                missing = sorted(set(planned_by_destination) - set(expected))
                stale = sorted(set(expected) - set(planned_by_destination))
                for destination in missing:
                    errors.append(f"lock omits upstream file: {destination}")
                for destination in stale:
                    errors.append(f"lock contains stale upstream file: {destination}")
            for destination in sorted(set(expected) & set(planned_by_destination)):
                locked = expected[destination]
                source = planned_by_destination[destination]
                if locked.source != source.source:
                    errors.append(f"source path mismatch for {destination}")
                if locked.source_sha256 != source.source_sha256:
                    errors.append(f"source hash mismatch for {destination}")
                if locked.rendered_sha256 != source.rendered_sha256:
                    errors.append(f"rendered hash mismatch for {destination}")
        except ImportError as error:
            errors.append(str(error))
    return sorted(set(errors))


def command_check(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.absolute()
    errors = verify_imports(root, args.upstream.resolve() if args.upstream else None)
    if errors:
        raise ScriptError(*errors)
    registry = parse_registry(root)
    log.info(
        "Matt mode imports match %s (%d files)", registry.revision, len(registry.files)
    )
    return {}


def command_update(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.absolute()
    registry = parse_registry(root)
    planned = build_plan(args.upstream.resolve(), args.revision, registry)
    writes, removals = preflight_update(root, registry, planned)
    lock_content = lock_document(registry, args.revision, planned)
    lock_file = local_path(root, LOCK_PATH)
    try:
        existing_lock = lock_file.read_bytes()
    except OSError as error:
        fail(f"cannot read lock file {lock_file}: {error}")
    lock_changed = existing_lock != lock_content

    if not writes and not removals and not lock_changed:
        log.info("Matt mode is already at %s", args.revision)
        return {}

    changes = [
        [
            "update" if local_path(root, record.destination).exists() else "add",
            str(record.destination),
        ]
        for record in writes
    ]
    changes += [["remove", str(destination)] for destination in removals]
    if lock_changed:
        changes.append(["update", str(LOCK_PATH)])
    if args.dry_run:
        log.info(
            "would update Matt mode from %s to %s", registry.revision, args.revision
        )
        return {"changes": changes}

    # Each change is listed once done, so a failure answers what already changed
    done: list[list[str]] = []
    try:
        for record, change in zip(writes, changes):
            atomic_write(local_path(root, record.destination), record.content)
            done.append(change)
        for destination, change in zip(removals, changes[len(writes) :]):
            path = local_path(root, destination)
            try:
                path.unlink()
            except OSError as error:
                fail(f"cannot remove stale generated file {destination}: {error}")
            prune_empty_parents(path, root)
            done.append(change)
        atomic_write(lock_file, lock_content)
    except ScriptError as error:
        raise ImportError(*error.args, report={"changes": done}) from error
    except OSError as error:
        raise ImportError(
            f"cannot write Matt mode: {error}; fix that path, then rerun update",
            report={"changes": done},
        ) from error
    log.info("updated Matt mode from %s to %s", registry.revision, args.revision)
    return {"changes": changes}


def parser() -> Parser:
    result = Parser(
        prog="update_matt_mode.py",
        description="Verify or update Matt mode's pinned upstream imports.",
        exit_codes=EXIT_CODES,
    )
    subparsers = result.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser(
        "check",
        help="verify the lock and generated files without network access",
        exit_codes=EXIT_CODES,
    )
    check.add_argument(
        "--upstream",
        type=Path,
        help="local Git checkout used to reconstruct the pinned revision",
    )
    check.add_argument(
        "--root", type=Path, default=DEFAULT_ROOT, help="Matt skill bucket root"
    )
    check.set_defaults(handler=command_check)

    update = subparsers.add_parser(
        "update",
        help="render one immutable upstream Git revision",
        exit_codes=EXIT_CODES,
    )
    update.add_argument(
        "--upstream", type=Path, required=True, help="local Git checkout"
    )
    update.add_argument(
        "--revision", required=True, help="full immutable upstream commit SHA"
    )
    update.add_argument(
        "--dry-run",
        action="store_true",
        help="answer the changes a real run makes, without writing",
    )
    update.add_argument(
        "--root", type=Path, default=DEFAULT_ROOT, help="Matt skill bucket root"
    )
    update.set_defaults(handler=command_update)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    return run_script(parser(), lambda args: args.handler(args), argv)


if __name__ == "__main__":
    raise SystemExit(main())

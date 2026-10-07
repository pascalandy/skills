# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Import Corey Haines' marketing skills as corey-mode playbooks, or verify them."""

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
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

log = logging.getLogger("update_corey_mode")

PACKAGE = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/coreyhaines31/marketingskills"
LOCK = PurePosixPath("upstream-lock.json")
PLAYBOOKS = PurePosixPath("playbooks")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
FULL_HASH = re.compile(r"[0-9a-f]{64}")
LINK = re.compile(r"(?P<head>\]\()(?P<target>[^)\s]+)(?P<tail>(?:\s+[^)]*)?\))")
ROUTE = re.compile(r"^\|\s*\[`(?P<name>[^`]+)`\]\((?P<target>[^)]+)\)\s*\|")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

REGENERATE = (
    "regenerate with: update_corey_mode.py update --upstream DIR --revision SHA"
)
ONE_ROW = "give each folder in playbooks/ exactly one row in SKILL.md"

EPILOG = """\
Each run answers in one JSON line: {"ok":true} on stdout, with "changes" when
update writes files or, with --dry-run, would write them; or
{"ok":false,"errors":[...]} as the last line of stderr.

examples:
  update_corey_mode.py check
  update_corey_mode.py check --upstream DIR
  update_corey_mode.py update --upstream DIR --revision SHA --dry-run
  update_corey_mode.py update --upstream DIR --revision SHA"""

EXIT_CODES = exit_codes(
    {
        0: "success, including a no-op",
        1: "the package drifted from the lock or the upstream, or the update failed",
    }
)


@dataclass(frozen=True)
class Rendered:
    source: PurePosixPath
    content: bytes


Plan = dict[PurePosixPath, Rendered]


@dataclass(frozen=True)
class Locked:
    revision: str
    hashes: dict[PurePosixPath, str]


def destination(source: PurePosixPath) -> PurePosixPath | None:
    """Where an upstream file lives in the package, or None when it stays out."""
    if source == PurePosixPath("LICENSE"):
        return PurePosixPath("references/LICENSE")
    parts = source.parts
    if len(parts) < 3 or parts[0] != "skills" or "evals" in parts[2:-1]:
        return None
    name = parts[1]
    if parts[2:] == ("SKILL.md",):
        return PLAYBOOKS / name / f"{name}.md"
    return PLAYBOOKS.joinpath(name, *parts[2:])


def upstream_files(upstream: Path) -> set[PurePosixPath]:
    if not (upstream / "skills").is_dir() or not (upstream / "LICENSE").is_file():
        raise ScriptError(
            f"{upstream} is not a marketingskills checkout: it needs skills/ and "
            "LICENSE; pass --upstream the snapshot folder, such as "
            "$OPENSRC_HOME/repos/github.com/coreyhaines31/marketingskills/main"
        )
    return {
        PurePosixPath(path.relative_to(upstream).as_posix())
        for path in upstream.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(upstream).parts)
    }


def rewrite_links(
    text: str,
    source: PurePosixPath,
    target_of: dict[PurePosixPath, PurePosixPath],
    files: set[PurePosixPath],
    revision: str,
) -> str:
    """Point each link at the package copy, or at GitHub when the file stays out.

    A link that is already broken upstream keeps its text.
    """
    folders = {parent for path in files for parent in path.parents}
    here = target_of[source].parent

    def replace(match: re.Match[str]) -> str:
        path, hash_, anchor = match["target"].partition("#")
        if not path or SCHEME.match(path) or path.startswith("/"):
            return match[0]
        resolved = PurePosixPath(posixpath.normpath(str(source.parent / path)))
        if resolved.parts[:1] == ("..",):
            return match[0]
        local = target_of.get(resolved)
        if local is not None:
            if posixpath.normpath(str(here / path)) == str(local):
                return match[0]
            new = posixpath.relpath(str(local), str(here))
        elif resolved in files:
            new = f"{REPOSITORY}/blob/{revision}/{resolved}"
        elif resolved in folders:
            new = f"{REPOSITORY}/tree/{revision}/{resolved}"
        else:
            return match[0]
        return f"{match['head']}{new}{hash_}{anchor}{match['tail']}"

    return LINK.sub(replace, text)


def render(upstream: Path, revision: str) -> Plan:
    files = upstream_files(upstream)
    target_of = {
        source: dest for source in files if (dest := destination(source)) is not None
    }
    clashes = len(target_of) - len(set(target_of.values()))
    if clashes:
        raise ScriptError(f"{clashes} upstream files map to the same package path")
    plan: Plan = {}
    for source, dest in target_of.items():
        content = (upstream / source).read_bytes()
        if source.suffix == ".md":
            text = rewrite_links(
                content.decode("utf-8"), source, target_of, files, revision
            )
            content = text.encode("utf-8")
        plan[dest] = Rendered(source, content)
    return plan


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def lock_document(plan: Plan, revision: str) -> bytes:
    document = {
        "schema_version": 1,
        "repository": REPOSITORY,
        "revision": revision,
        "files": {
            str(dest): {"source": str(item.source), "sha256": sha256(item.content)}
            for dest, item in sorted(plan.items())
        },
    }
    return (json.dumps(document, indent=2) + "\n").encode("utf-8")


def read_lock(package: Path) -> Locked | None:
    """Parse the lock, refusing any path the importer would not write itself."""
    path = package / LOCK

    def invalid(reason: str) -> NoReturn:
        raise ScriptError(
            f"{path}: invalid lock: {reason}; restore a valid {LOCK}, then run: "
            f"update_corey_mode.py check --package {package}"
        )

    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as error:
        invalid(str(error))
    if not isinstance(raw, dict):
        invalid("expected a JSON object")
    if raw.get("schema_version") != 1:
        invalid("schema_version must be 1")
    if raw.get("repository") != REPOSITORY:
        invalid(f"repository must be {REPOSITORY}")
    revision = raw.get("revision")
    if not isinstance(revision, str) or not FULL_SHA.fullmatch(revision):
        invalid("revision must be a full 40-character SHA")
    files = raw.get("files")
    if not isinstance(files, dict) or not files:
        invalid("files must be a non-empty object")
    hashes: dict[PurePosixPath, str] = {}
    for dest, entry in files.items():
        if not isinstance(entry, dict):
            invalid(f"invalid file record: {dest!r}")
        source, digest = entry.get("source"), entry.get("sha256")
        target = PurePosixPath(dest)
        if (
            not isinstance(source, str)
            or ".." in target.parts
            or str(target) != dest
            or destination(PurePosixPath(source)) != target
        ):
            invalid(f"{dest!r} is not where the importer writes {source!r}")
        if not isinstance(digest, str) or not FULL_HASH.fullmatch(digest):
            invalid(f"{dest}: sha256 must be a 64-character hash")
        hashes[target] = digest
    return Locked(revision, hashes)


def owned(package: Path, lock: Locked | None) -> set[PurePosixPath]:
    """Files the importer writes: everything in the lock and under playbooks/."""
    paths = set(lock.hashes) if lock else set()
    if (package / PLAYBOOKS).is_dir():
        paths |= {
            PurePosixPath(path.relative_to(package).as_posix())
            for path in (package / PLAYBOOKS).rglob("*")
            if path.is_file()
        }
    return paths


def update(
    package: Path, upstream: Path, revision: str, dry_run: bool
) -> list[list[str]]:
    plan = render(upstream, revision)
    log.info("rendered %d files from %s at %s", len(plan), upstream, revision)
    lock = read_lock(package)
    files = {dest: item.content for dest, item in plan.items()}
    files[LOCK] = lock_document(plan, revision)
    # Each change is listed once done, so a failure answers what already changed
    changes: list[list[str]] = []
    try:
        for dest in sorted(owned(package, lock) - set(plan)):
            if not dry_run:
                (package / dest).unlink(missing_ok=True)
            changes.append(["delete", str(dest)])
        for dest, content in sorted(files.items()):
            path = package / dest
            if path.is_file() and path.read_bytes() == content:
                continue
            change = ["update" if path.exists() else "add", str(dest)]
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            changes.append(change)
        if not dry_run and (package / PLAYBOOKS).is_dir():
            for folder in sorted((package / PLAYBOOKS).rglob("*"), reverse=True):
                if folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
    except OSError as error:
        raise ScriptError(
            f"could not write the package: {error}; fix that path, then rerun the update",
            report={"changes": changes},
        ) from error
    return changes


def markdown_links(text: str) -> list[str]:
    links: list[str] = []
    in_code = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_code = not in_code
        elif not in_code:
            links += [match["target"] for match in LINK.finditer(line)]
    return links


def check_routes(package: Path) -> list[str]:
    problems: list[str] = []
    rows = [
        match
        for line in (package / "SKILL.md").read_text(encoding="utf-8").splitlines()
        if (match := ROUTE.match(line))
    ]
    names = [row["name"] for row in rows]
    for name in sorted({name for name in names if names.count(name) > 1}):
        problems.append(f"duplicate route: {name}")
    for row in rows:
        expected = f"{PLAYBOOKS}/{row['name']}/{row['name']}.md"
        if row["target"] != expected:
            problems.append(
                f"route {row['name']} links to {row['target']}, not {expected}"
            )
    folders = (
        {path.name for path in (package / PLAYBOOKS).iterdir() if path.is_dir()}
        if (package / PLAYBOOKS).is_dir()
        else set()
    )
    for name in sorted(set(names) - folders):
        problems.append(f"route without a playbook: {name}")
    for name in sorted(folders - set(names)):
        problems.append(f"playbook without a route: {name}")
    return problems


def check(package: Path, upstream: Path | None) -> None:
    lock = read_lock(package)
    if lock is None:
        raise ScriptError(
            f"{package / LOCK} is missing; import upstream with: "
            "update_corey_mode.py update --upstream DIR --revision SHA"
        )
    stale: list[str] = []
    entries = lock.hashes
    for dest, digest in sorted(entries.items()):
        path = package / dest
        if not path.is_file():
            stale.append(f"missing: {dest}")
        elif sha256(path.read_bytes()) != digest:
            stale.append(f"changed: {dest}")
    log.info("checked %d generated files against the lock", len(entries))
    for dest in sorted(owned(package, lock) - entries.keys()):
        stale.append(f"not in the lock: {dest}")
    for path in sorted(package.rglob("SKILL.md")):
        if path != package / "SKILL.md":
            stale.append(f"nested SKILL.md: {path.relative_to(package)}")
    links: list[str] = []
    for path in sorted(package.rglob("*.md")):
        relative = PurePosixPath(path.relative_to(package).as_posix())
        if relative in entries:
            continue
        for target in markdown_links(path.read_text(encoding="utf-8")):
            link = target.partition("#")[0]
            if link and not SCHEME.match(link) and not (path.parent / link).exists():
                links.append(f"broken link in {relative}: {target}")
    if upstream is not None:
        revision = lock.revision
        plan = render(upstream, revision)
        log.info("rebuilt %d files from %s at %s", len(plan), upstream, revision)
        if lock_document(plan, revision) != (package / LOCK).read_bytes():
            stale.append(f"{LOCK} differs from a fresh render of {upstream}")
        for dest, item in sorted(plan.items()):
            path = package / dest
            if not path.is_file() or path.read_bytes() != item.content:
                stale.append(f"differs from upstream: {dest}")
    problems = [f"{problem}; {REGENERATE}" for problem in stale]
    problems += [f"{problem}; {ONE_ROW}" for problem in check_routes(package)]
    problems += links
    if problems:
        raise ScriptError(*problems)


def full_sha(value: str) -> str:
    if not FULL_SHA.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"must be a full 40-character SHA, got {value!r}"
        )
    return value


def parser() -> Parser:
    """The root parser, with one parser per command."""
    result = Parser(
        prog="update_corey_mode.py",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    commands = result.add_subparsers(dest="command", required=True)

    def subcommand(
        name: str, summary: str, description: str
    ) -> argparse.ArgumentParser:
        return commands.add_parser(
            name,
            help=summary,
            description=description,
            epilog=EPILOG,
            exit_codes=EXIT_CODES,
        )

    check_command = subcommand(
        "check",
        "verify the playbooks against the lock, offline by default",
        "Verify the playbooks, the lock, and the route table.",
    )
    check_command.add_argument(
        "--upstream", type=Path, help="upstream folder to rebuild the files from"
    )
    update_command = subcommand(
        "update",
        "import one upstream revision",
        "Rewrite playbooks/, references/LICENSE, and the lock.",
    )
    update_command.add_argument(
        "--upstream", type=Path, required=True, help="upstream folder to import"
    )
    update_command.add_argument(
        "--revision",
        type=full_sha,
        required=True,
        help="full commit SHA of that folder",
    )
    update_command.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="answer the changes a run would make, and write nothing",
    )
    for command in (check_command, update_command):
        command.add_argument(
            "--package", type=Path, default=PACKAGE, help="corey-mode package folder"
        )
    return result


def work(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "update":
        changes = update(args.package, args.upstream, args.revision, args.dry_run)
        return {"changes": changes} if changes else {}
    check(args.package, args.upstream)
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    return run_script(parser(), work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

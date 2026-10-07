#!/usr/bin/env python3
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

import errno
import fcntl
import hashlib
import platform
import pty
import select
import shutil
import struct
import subprocess
import tempfile
import termios
import textwrap
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

SCHEMA = "video-archive.verification/v1"
OWNER_SCHEMA = "video-archive.verification-owner/v1"
PAUSE_ENV = "VIDEO_ARCHIVE_VERIFY_PAUSE_AFTER_PREPARED_SECONDS"
FEATURES = (
    "conversion",
    "ordering",
    "open-source",
    "changing-source",
    "lock-contention",
    "dependencies",
    "mixed-batch",
    "original-fallback",
    "cleanup-pending",
    "interruption",
    "output-contracts",
    "collision",
    "recovery",
    "parallel-batch",
)
MEDIA_SUFFIXES = {".mkv", ".mov", ".mp4"}
ANSI_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
COLOR_PATTERN = re.compile(r"\x1b\[[0-9;]*m")

CheckStatus = Literal["passed", "failed", "skipped", "unmet"]

log = logging.getLogger("verify-video-archive")


@dataclass(frozen=True)
class ScenarioPaths:
    root: Path
    home: Path
    inputs: tuple[Path, Path]
    archive: Path
    state_root: Path
    state: Path
    journal: Path
    journal_file: Path
    scratch: Path
    evidence: Path
    bridge: Path


@dataclass(frozen=True)
class Check:
    id: str
    status: CheckStatus
    summary: str
    expected: object
    observed: object
    evidence: tuple[str, ...] = ()


def now() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with temporary.open("x", encoding="utf-8") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def load_manifest(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve(strict=True)
    raw = cast(object, json.loads(resolved.read_text(encoding="utf-8")))
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise ValueError(f"unsupported verification manifest: {resolved}")
    return cast(dict[str, object], raw)


def save_manifest(path: Path, manifest: dict[str, object]) -> None:
    manifest["updated_at"] = now()
    atomic_json(path, manifest)


def require_text(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"manifest field {key!r} is missing")
    return value


def evidence_path(manifest_path: Path, reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    root = manifest_path.parent.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"evidence reference escapes the bundle: {reference}")
    return resolved


def evidence_reference(manifest_path: Path, path: Path) -> str:
    return str(path.resolve().relative_to(manifest_path.parent.resolve()))


def manifest_paths(
    manifest: Mapping[str, object], feature: str, manifest_path: Path | None = None
) -> ScenarioPaths:
    raw_scenarios = manifest.get("scenario_paths")
    if not isinstance(raw_scenarios, dict):
        raise TypeError("manifest scenario_paths is missing")
    raw = raw_scenarios.get(feature)
    if not isinstance(raw, dict):
        raise TypeError(f"manifest paths for {feature!r} are missing")
    data = cast(dict[str, object], raw)
    inputs = data.get("inputs")
    if (
        not isinstance(inputs, list)
        or len(inputs) != 2
        or not all(isinstance(item, str) for item in inputs)
    ):
        raise ValueError(f"manifest inputs for {feature!r} are invalid")
    evidence = Path(require_text(data, "evidence"))
    if not evidence.is_absolute():
        if manifest_path is None:
            raise ValueError("manifest_path is required for relative evidence paths")
        evidence = manifest_path.parent / evidence
    return ScenarioPaths(
        root=Path(require_text(data, "root")),
        home=Path(require_text(data, "home")),
        inputs=(Path(cast(str, inputs[0])), Path(cast(str, inputs[1]))),
        archive=Path(require_text(data, "archive")),
        state_root=Path(require_text(data, "state_root")),
        state=Path(require_text(data, "state")),
        journal=Path(require_text(data, "journal")),
        journal_file=Path(require_text(data, "journal_file")),
        scratch=Path(require_text(data, "scratch")),
        evidence=evidence,
        bridge=Path(require_text(data, "bridge")),
    )


def make_scenario_paths(
    run_root: Path, evidence_root: Path, checkout: Path, feature: str
) -> ScenarioPaths:
    root = run_root / "scenarios" / feature
    home = root / "home"
    inputs = (
        home / "Documents" / "screenshots",
        home / "Documents" / "screenvids",
    )
    archive = home / "Documents" / "screenvids_archived"
    state_root = root / "state"
    state = state_root / "video-archive"
    journal = root / "journal"
    journal_file = journal / "video-archive.log"
    scratch = root / "scratch"
    evidence = evidence_root / "scenarios" / feature
    bridge = home / ".local" / "bin" / "video-archive"
    for directory in (*inputs, archive, state, journal, scratch, evidence):
        directory.mkdir(parents=True, exist_ok=False)
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.symlink_to(checkout / "dot_local" / "bin" / "executable_video-archive")
    journal_file.touch()
    (state / "video-archive.log").symlink_to(journal_file)
    return ScenarioPaths(
        root,
        home,
        inputs,
        archive,
        state_root,
        state,
        journal,
        journal_file,
        scratch,
        evidence,
        bridge,
    )


def make_variant_paths(
    parent: ScenarioPaths, checkout: Path, label: str
) -> ScenarioPaths:
    root = parent.root / "variants" / label
    home = root / "home"
    inputs = (
        home / "Documents" / "screenshots",
        home / "Documents" / "screenvids",
    )
    archive = home / "Documents" / "screenvids_archived"
    state_root = root / "state"
    state = state_root / "video-archive"
    journal = root / "journal"
    journal_file = journal / "video-archive.log"
    scratch = root / "scratch"
    evidence = parent.evidence / "variants" / label
    bridge = home / ".local" / "bin" / "video-archive"
    for directory in (*inputs, archive, state, journal, scratch, evidence):
        directory.mkdir(parents=True, exist_ok=False)
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.symlink_to(checkout / "dot_local" / "bin" / "executable_video-archive")
    journal_file.touch()
    (state / "video-archive.log").symlink_to(journal_file)
    return ScenarioPaths(
        root,
        home,
        inputs,
        archive,
        state_root,
        state,
        journal,
        journal_file,
        scratch,
        evidence,
        bridge,
    )


def git_identity(checkout: Path) -> dict[str, object]:
    revision = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    diff = subprocess.run(
        ["git", "-C", str(checkout), "diff", "--binary", "HEAD", "--"],
        capture_output=True,
        check=True,
    ).stdout
    identity = hashlib.sha256(status.encode() + b"\0" + diff)
    untracked: list[dict[str, object]] = []
    for line in status.splitlines():
        if not line.startswith("?? "):
            continue
        relative = line[3:]
        path = checkout / relative
        if not path.is_file():
            continue
        digest = sha256(path)
        identity.update(relative.encode())
        identity.update(digest.encode())
        untracked.append({"path": relative, "sha256": digest})
    return {
        "revision": revision,
        "dirty": bool(status),
        "porcelain": status.splitlines(),
        "identity_sha256": identity.hexdigest(),
        "untracked": untracked,
    }


def cpu_model() -> str:
    if platform.system() == "Darwin":
        result = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    elif platform.system() == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                name, separator, value = line.partition(":")
                if separator and name.strip() in {"model name", "Hardware"}:
                    return value.strip()
        except OSError:
            pass
    return platform.processor() or platform.machine() or "unknown"


def file_identity(checkout: Path) -> list[dict[str, object]]:
    patterns = (
        "justfile",
        "dot_local/bin/executable_video-archive",
        "dot_local/share/video-archive/video_archive.py",
        "dot_local/share/video-archive/video_archive_media.py",
        "dot_local/share/video-archive/video_archive_model.py",
        "dot_local/share/video-archive/video_archive_output.py",
        "dot_local/share/video-archive/video_archive_resources.py",
        "dot_local/share/video-archive/video_archive_store.py",
    )
    result: list[dict[str, object]] = []
    for relative in patterns:
        path = checkout / relative
        if path.is_file():
            result.append(
                {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}
            )
    return result


def verifier_identity() -> dict[str, object]:
    package = Path(__file__).resolve().parent.parent
    files = [
        {
            "path": path.relative_to(package).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(package.rglob("*"))
        if path.is_file()
        and not path.is_symlink()
        and not any(
            part in {"__pycache__", ".pytest_cache", ".ruff_cache"}
            for part in path.relative_to(package).parts
        )
        and path.suffix not in {".pyc", ".pyo"}
    ]
    revision: str | None = None
    root = subprocess.run(
        ["git", "-C", str(package), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if root.returncode == 0:
        repository = Path(root.stdout.strip()).resolve()
        relative = package.relative_to(repository)
        if relative in (
            Path("authoring/verify-loops/verify-video-archive"),
            Path("skills/verify-video-archive"),
        ):
            revision = subprocess.run(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
    return {"package": str(package), "revision": revision, "files": files}


def launch(checkout: Path, evidence_parent: Path | None) -> Path:
    checkout = checkout.expanduser().resolve(strict=True)
    if not (checkout / "justfile").is_file():
        raise ValueError(f"checkout has no justfile: {checkout}")
    run_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"
    run_root = Path(
        tempfile.mkdtemp(prefix=f"verify-video-archive-run-{run_id}-")
    ).resolve()
    if evidence_parent is None:
        evidence_root = Path(
            tempfile.mkdtemp(prefix=f"verify-video-archive-evidence-{run_id}-")
        ).resolve()
    else:
        parent = evidence_parent.expanduser().resolve()
        parent.mkdir(parents=True, exist_ok=True)
        evidence_root = parent / run_id
        evidence_root.mkdir()
    if evidence_root == run_root or run_root in evidence_root.parents:
        raise ValueError("evidence must be outside the disposable run root")
    owner_token = uuid.uuid4().hex
    atomic_json(
        run_root / "owner.json",
        {"schema": OWNER_SCHEMA, "run_id": run_id, "token": owner_token},
    )
    scenario_paths = {
        feature: asdict(make_scenario_paths(run_root, evidence_root, checkout, feature))
        for feature in FEATURES
    }
    normalized_paths: dict[str, dict[str, object]] = {}
    for feature, raw in scenario_paths.items():
        values: dict[str, object] = {}
        for key, value in cast(dict[str, object], raw).items():
            if isinstance(value, tuple):
                values[key] = [str(item) for item in value]
            elif key == "evidence":
                values[key] = str(cast(Path, value).relative_to(evidence_root))
            else:
                values[key] = str(value)
        normalized_paths[feature] = values
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "run_id": run_id,
        "owner_token": owner_token,
        "created_at": now(),
        "updated_at": now(),
        "phase": "launched",
        "checkout": str(checkout),
        "git": git_identity(checkout),
        "tested_files": file_identity(checkout),
        "verifier": verifier_identity(),
        "platform": {
            "hostname": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "cpu_model": cpu_model(),
            "logical_cpus": os.cpu_count(),
            "python": sys.version,
        },
        "paths": {"run_root": str(run_root), "evidence": "."},
        "scenario_paths": normalized_paths,
        "doctor": [],
        "invocations": [],
        "scenarios": {},
        "summary": {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "unmet": 0,
            "verdict": "unmet",
        },
        "cleanup": {"status": "pending"},
    }
    manifest_path = evidence_root / "manifest.json"
    save_manifest(manifest_path, manifest)
    return manifest_path


def version(command: str, *args: str) -> dict[str, object]:
    path = shutil.which(command)
    if path is None:
        return {"path": None, "version": None}
    result = subprocess.run([path, *args], capture_output=True, text=True, check=False)
    output = (result.stdout or result.stderr).splitlines()
    return {
        "path": path,
        "version": output[0] if output else "",
        "exit_status": result.returncode,
    }


def check(
    check_id: str,
    condition: bool,
    summary: str,
    expected: object,
    observed: object,
    *,
    unavailable: bool = False,
    evidence: Sequence[str] = (),
) -> Check:
    status: CheckStatus = (
        "passed" if condition else ("unmet" if unavailable else "failed")
    )
    return Check(check_id, status, summary, expected, observed, tuple(evidence))


def doctor(manifest_path: Path) -> list[Check]:
    manifest = load_manifest(manifest_path)
    checkout = Path(require_text(manifest, "checkout"))
    tools = {
        "python": {
            "path": sys.executable,
            "version": platform.python_version(),
            "exit_status": 0,
        },
        "just": version("just", "--version"),
        "ffmpeg": version("ffmpeg", "-version"),
        "ffprobe": version("ffprobe", "-version"),
        "git": version("git", "--version"),
        "lsof": version("lsof", "-v"),
    }
    encoder = (
        subprocess.run(
            [cast(str, tools["ffmpeg"]["path"]), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            check=False,
        )
        if tools["ffmpeg"]["path"]
        else None
    )
    checks = [
        check(
            "doctor.platform",
            platform.system() in {"Darwin", "Linux"},
            "The real-media archive verifier supports macOS and Linux",
            "Darwin or Linux",
            platform.system(),
            unavailable=True,
        ),
        check(
            "doctor.python",
            sys.version_info >= (3, 11),
            "Python is new enough for the archive command",
            ">=3.11",
            platform.python_version(),
            unavailable=True,
        ),
        check(
            "doctor.just",
            tools["just"]["path"] is not None,
            "Just is available",
            "resolved executable",
            tools["just"]["path"],
            unavailable=True,
        ),
        check(
            "doctor.ffmpeg",
            tools["ffmpeg"]["path"] is not None,
            "FFmpeg is available",
            "resolved executable",
            tools["ffmpeg"]["path"],
            unavailable=True,
        ),
        check(
            "doctor.ffprobe",
            tools["ffprobe"]["path"] is not None,
            "FFprobe is available",
            "resolved executable",
            tools["ffprobe"]["path"],
            unavailable=True,
        ),
        check(
            "doctor.libx265",
            encoder is not None
            and encoder.returncode == 0
            and "libx265" in encoder.stdout,
            "FFmpeg exposes libx265",
            "libx265 encoder",
            "available"
            if encoder is not None and "libx265" in encoder.stdout
            else "missing",
            unavailable=True,
        ),
        check(
            "doctor.lsof",
            tools["lsof"]["path"] is not None,
            "The open-file inspector is available",
            "resolved lsof executable",
            tools["lsof"]["path"],
            unavailable=True,
        ),
        check(
            "doctor.wrapper",
            (checkout / "dot_local/bin/executable_video-archive").is_file(),
            "The checkout wrapper exists",
            "checkout wrapper",
            str(checkout / "dot_local/bin/executable_video-archive"),
            unavailable=True,
        ),
    ]
    manifest["tools"] = tools
    manifest["doctor"] = [asdict(item) for item in checks]
    manifest["phase"] = "doctor"
    save_manifest(manifest_path, manifest)
    return checks


def child_environment(
    paths: ScenarioPaths,
    *,
    no_color: bool = True,
    pause_seconds: float | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    environment = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP", "DOTFILES_SOURCE"):
        environment.pop(key, None)
    overrides = {
        "HOME": str(paths.home),
        "XDG_STATE_HOME": str(paths.state_root),
        "XDG_CACHE_HOME": str(paths.scratch / "cache"),
        "XDG_CONFIG_HOME": str(paths.scratch / "config"),
        "TMPDIR": str(paths.scratch / "tmp"),
    }
    if no_color:
        overrides["NO_COLOR"] = "1"
    else:
        environment.pop("NO_COLOR", None)
    if pause_seconds is not None:
        overrides[PAUSE_ENV] = str(pause_seconds)
    for directory in (
        paths.scratch / "cache",
        paths.scratch / "config",
        paths.scratch / "tmp",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    environment.update(overrides)
    return environment, overrides


def append_invocation(manifest: dict[str, object], record: dict[str, object]) -> None:
    raw = manifest.setdefault("invocations", [])
    if not isinstance(raw, list):
        raise TypeError("manifest invocations is invalid")
    raw.append(record)


def run_command(
    manifest: dict[str, object],
    manifest_path: Path,
    paths: ScenarioPaths,
    label: str,
    argv: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None = None,
    environment_overrides: Mapping[str, str] | None = None,
    timeout: float = 180.0,
    measure_resources: bool = False,
) -> dict[str, object]:
    directory = (
        paths.evidence
        / "commands"
        / f"{len(cast(list[object], manifest['invocations'])):03d}-{label}"
    )
    directory.mkdir(parents=True)
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    started = now()
    started_monotonic = time.monotonic()
    with (
        stdout_path.open("w", encoding="utf-8") as stdout,
        stderr_path.open("w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            env=dict(environment) if environment is not None else None,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        pgid = os.getpgid(process.pid)
        timed_out = False
        deadline = time.monotonic() + timeout
        resource_usage: dict[str, object] = {
            "sample_count": 0,
            "peak_rss_bytes": 0,
            "peak_cpu_percent": 0.0,
            "cpu_seconds": 0.0,
            "peak_media_processes": 0,
            "media_backend_sessions": {
                "status": "not_applicable",
                "reason": "software-x265 uses no hardware encoder session",
                "peak": 0,
            },
        }
        last_sample = time.monotonic()
        while process.poll() is None and time.monotonic() < deadline:
            if measure_resources:
                current = time.monotonic()
                sample = process_tree_sample(process.pid)
                cpu_percent = cast(float, sample["cpu_percent"])
                resource_usage["sample_count"] = (
                    cast(int, resource_usage["sample_count"]) + 1
                )
                resource_usage["peak_rss_bytes"] = max(
                    cast(int, resource_usage["peak_rss_bytes"]),
                    cast(int, sample["rss_bytes"]),
                )
                resource_usage["peak_cpu_percent"] = max(
                    cast(float, resource_usage["peak_cpu_percent"]), cpu_percent
                )
                resource_usage["cpu_seconds"] = cast(
                    float, resource_usage["cpu_seconds"]
                ) + cpu_percent / 100 * (current - last_sample)
                resource_usage["peak_media_processes"] = max(
                    cast(int, resource_usage["peak_media_processes"]),
                    cast(int, sample["media_processes"]),
                )
                last_sample = current
            time.sleep(0.05)
        if process.poll() is None:
            timed_out = True
            os.killpg(pgid, signal.SIGTERM)
            try:
                returncode = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(pgid, signal.SIGKILL)
                returncode = process.wait()
        else:
            returncode = process.wait()
    record: dict[str, object] = {
        "label": label,
        "argv": list(argv),
        "cwd": str(cwd),
        "environment_overrides": dict(environment_overrides or {}),
        "pid": process.pid,
        "process_group": pgid,
        "started_at": started,
        "finished_at": now(),
        "exit_status": returncode,
        "timed_out": timed_out,
        "stdout": evidence_reference(manifest_path, stdout_path),
        "stderr": evidence_reference(manifest_path, stderr_path),
    }
    if measure_resources:
        resource_usage["wall_seconds"] = time.monotonic() - started_monotonic
        record["resources"] = resource_usage
    append_invocation(manifest, record)
    save_manifest(manifest_path, manifest)
    return record


def ffmpeg_fixture(
    manifest: dict[str, object],
    manifest_path: Path,
    paths: ScenarioPaths,
    name: str,
    *,
    compact: bool = False,
    duration: int = 2,
    size: str = "160x90",
) -> Path:
    destination = paths.inputs[0] / name
    if compact:
        argv = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:size=64x64:rate=1:duration=1",
            "-frames:v",
            "1",
            "-c:v",
            "libx265",
            "-preset",
            "veryslow",
            "-crf",
            "51",
            "-tag:v",
            "hvc1",
            "-an",
            "-movflags",
            "+faststart",
            str(destination),
        ]
    else:
        argv = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"testsrc2=size={size}:rate=12:duration={duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:sample_rate=48000:duration={duration}",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "ffv1",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ]
    record = run_command(
        manifest, manifest_path, paths, f"generate-{name}", argv, cwd=paths.scratch
    )
    if record["exit_status"] != 0 or not destination.is_file():
        raise RuntimeError(f"fixture generation failed for {name}")
    return destination


def archive_operations(paths: ScenarioPaths) -> list[dict[str, object]]:
    operations: list[dict[str, object]] = []
    for path in sorted(paths.state.glob("archives/*/operations/*.json")):
        raw = cast(object, json.loads(path.read_text(encoding="utf-8")))
        if isinstance(raw, dict):
            operation = cast(dict[str, object], raw)
            operation["_record_path"] = str(path)
            operations.append(operation)
    return operations


def just_argv(manifest: Mapping[str, object]) -> list[str]:
    tools = manifest.get("tools")
    just = None
    if isinstance(tools, dict):
        raw_just = tools.get("just")
        if isinstance(raw_just, dict):
            just = raw_just.get("path")
    executable = just if isinstance(just, str) and just else shutil.which("just")
    if executable is None:
        raise RuntimeError("just is unavailable")
    checkout = Path(require_text(manifest, "checkout"))
    return [executable, "--justfile", str(checkout / "justfile"), "convert-video"]


def run_just(
    manifest: dict[str, object],
    manifest_path: Path,
    paths: ScenarioPaths,
    label: str,
    *extra_args: str,
    environment: Mapping[str, str] | None = None,
    environment_overrides: Mapping[str, str] | None = None,
    measure_resources: bool = False,
) -> dict[str, object]:
    if environment is None:
        environment, overrides = child_environment(paths, no_color=True)
    else:
        overrides = dict(environment_overrides or {})
    return run_command(
        manifest,
        manifest_path,
        paths,
        label,
        [*just_argv(manifest), *extra_args],
        cwd=Path(require_text(manifest, "checkout")),
        environment=environment,
        environment_overrides=overrides,
        measure_resources=measure_resources,
    )


def process_tree_sample(root_pid: int) -> dict[str, object]:
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,%cpu=,rss=,comm="],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return {
            "rss_bytes": 0,
            "cpu_percent": 0.0,
            "media_processes": 0,
            "media_pids": [],
            "pids": [],
        }
    rows: dict[int, tuple[int, float, int, str]] = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 4)
        if len(fields) != 5:
            continue
        try:
            pid = int(fields[0])
            rows[pid] = (int(fields[1]), float(fields[2]), int(fields[3]), fields[4])
        except ValueError:
            continue
    selected = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, (parent, _cpu, _rss, _command) in rows.items():
            if pid not in selected and parent in selected:
                selected.add(pid)
                changed = True
    existing = [pid for pid in selected if pid in rows]
    media_pids = [
        pid for pid in existing if Path(rows[pid][3]).name in {"ffmpeg", "ffprobe"}
    ]
    return {
        "rss_bytes": sum(rows[pid][2] * 1024 for pid in existing),
        "cpu_percent": sum(rows[pid][1] for pid in existing),
        "media_processes": len(media_pids),
        "media_pids": sorted(media_pids),
        "pids": sorted(existing),
    }


def run_just_pty(
    manifest: dict[str, object],
    manifest_path: Path,
    paths: ScenarioPaths,
    label: str,
    *,
    width: int = 92,
    no_color: bool = False,
    interrupt_on: str | None = None,
    cleanup_pending: bool = False,
    mutate_on: str | None = None,
    mutate_path: Path | None = None,
    timeout: float = 180.0,
) -> dict[str, object]:
    pause_seconds = 1.5 if cleanup_pending else None
    environment, overrides = child_environment(
        paths, no_color=no_color, pause_seconds=pause_seconds
    )
    environment["TERM"] = "xterm-256color"
    overrides["TERM"] = "xterm-256color"
    argv = just_argv(manifest)
    directory = (
        paths.evidence
        / "commands"
        / f"{len(cast(list[object], manifest['invocations'])):03d}-{label}"
    )
    directory.mkdir(parents=True)
    terminal_path = directory / "terminal.txt"
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, width, 0, 0))
    started = now()
    transcript = bytearray()
    signals: list[str] = []
    input_mode: int | None = None
    mutated = False
    process = subprocess.Popen(
        argv,
        cwd=Path(require_text(manifest, "checkout")),
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=slave,
        stderr=slave,
        start_new_session=True,
    )
    os.close(slave)
    pgid = os.getpgid(process.pid)
    deadline = time.monotonic() + timeout
    timed_out = False
    eof = False
    returncode = process.poll()
    try:
        while True:
            ready, _, _ = select.select([master], [], [], 0.05)
            if ready:
                try:
                    chunk = os.read(master, 65_536)
                    if chunk:
                        transcript.extend(chunk)
                    else:
                        eof = True
                except OSError as error:
                    if error.errno == errno.EIO:
                        eof = True
                    else:
                        raise
            text = transcript.decode("utf-8", errors="replace")
            if interrupt_on is not None and not signals and interrupt_on in text:
                os.killpg(pgid, signal.SIGINT)
                signals.append("SIGINT")
            if (
                mutate_on is not None
                and mutate_path is not None
                and not mutated
                and mutate_on in text
            ):
                with mutate_path.open("ab") as source:
                    source.write(b"source changed by verification driver")
                    source.flush()
                    os.fsync(source.fileno())
                mutated = True
            if cleanup_pending and input_mode is None:
                prepared = [
                    item
                    for item in archive_operations(paths)
                    if item.get("state") == "prepared"
                ]
                if prepared:
                    input_mode = paths.inputs[0].stat().st_mode
                    paths.inputs[0].chmod(0o555)
            returncode = process.poll()
            if returncode is not None and (eof or not ready):
                break
            if time.monotonic() >= deadline:
                timed_out = True
                os.killpg(pgid, signal.SIGTERM)
                signals.append("SIGTERM")
                try:
                    returncode = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(pgid, signal.SIGKILL)
                    signals.append("SIGKILL")
                    returncode = process.wait()
                break
        if process.poll() is None:
            returncode = process.wait(timeout=5)
    finally:
        os.close(master)
        if input_mode is not None:
            paths.inputs[0].chmod(input_mode)
    terminal_path.write_bytes(bytes(transcript))
    record: dict[str, object] = {
        "label": label,
        "argv": argv,
        "cwd": require_text(manifest, "checkout"),
        "environment_overrides": overrides,
        "pid": process.pid,
        "process_group": pgid,
        "terminal_width": width,
        "pty": True,
        "started_at": started,
        "finished_at": now(),
        "exit_status": returncode,
        "timed_out": timed_out,
        "signals": signals,
        "source_mutated": mutated,
        "stdout": evidence_reference(manifest_path, terminal_path),
        "stderr": evidence_reference(manifest_path, terminal_path),
    }
    append_invocation(manifest, record)
    save_manifest(manifest_path, manifest)
    return record


def verify_media(
    manifest: dict[str, object],
    manifest_path: Path,
    paths: ScenarioPaths,
    media: Path,
    label: str,
) -> dict[str, object]:
    probe = run_command(
        manifest,
        manifest_path,
        paths,
        f"probe-{label}",
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(media),
        ],
        cwd=paths.scratch,
    )
    decode = run_command(
        manifest,
        manifest_path,
        paths,
        f"decode-{label}",
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-xerror",
            "-i",
            str(media),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0?",
            "-f",
            "null",
            "-",
        ],
        cwd=paths.scratch,
    )
    facts: dict[str, object] = {
        "path": str(media),
        "bytes": media.stat().st_size if media.exists() else None,
        "sha256": sha256(media) if media.exists() else None,
        "probe_exit_status": probe["exit_status"],
        "decode_exit_status": decode["exit_status"],
        "probe_stdout": probe["stdout"],
    }
    if probe["exit_status"] == 0:
        raw = cast(
            object,
            json.loads(
                evidence_path(manifest_path, cast(str, probe["stdout"])).read_text(
                    encoding="utf-8"
                )
            ),
        )
        if isinstance(raw, dict):
            facts["ffprobe"] = raw
    return facts


def copy_evidence_tree(
    paths: ScenarioPaths, phase: str, manifest_path: Path
) -> list[dict[str, object]]:
    destination_root = paths.evidence / "files" / phase
    records: list[dict[str, object]] = []
    roots = {
        "input-screenshots": paths.inputs[0],
        "input-screenvids": paths.inputs[1],
        "archive": paths.archive,
        "state": paths.state,
        "journal": paths.journal,
    }
    for label, root in roots.items():
        for source in sorted(root.rglob("*")):
            if not source.is_file() or source.is_symlink():
                continue
            relative = source.relative_to(root)
            destination = destination_root / label / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            records.append(
                {
                    "area": label,
                    "path": str(relative),
                    "bytes": source.stat().st_size,
                    "sha256": sha256(source),
                    "retained": evidence_reference(manifest_path, destination),
                }
            )
    atomic_json(destination_root / "inventory.json", records)
    return records


def operation_archive(operation: Mapping[str, object]) -> Path | None:
    destination = operation.get("destination")
    return Path(destination) if isinstance(destination, str) else None


def successful_archive_checks(
    manifest: dict[str, object],
    manifest_path: Path,
    paths: ScenarioPaths,
    operations: Sequence[Mapping[str, object]],
    prefix: str,
) -> list[Check]:
    checks: list[Check] = []
    for index, operation in enumerate(operations):
        destination = operation_archive(operation)
        exists = destination is not None and destination.is_file()
        facts = (
            verify_media(
                manifest, manifest_path, paths, destination, f"{prefix}-{index}"
            )
            if exists and destination is not None
            else {"path": str(destination), "missing": True}
        )
        expected_hash = operation.get("archive_sha256")
        hash_matches = exists and facts.get("sha256") == expected_hash
        readable = (
            facts.get("probe_exit_status") == 0 and facts.get("decode_exit_status") == 0
        )
        checks.append(
            check(
                f"{prefix}.archive.{index}.reopened",
                bool(exists and hash_matches and readable),
                "The published archive reopens, decodes, and matches its durable hash",
                {"exists": True, "hash_matches": True, "probe": 0, "decode": 0},
                facts,
                evidence=(cast(str, facts.get("probe_stdout", "")),),
            )
        )
    return checks


def invocation_text(manifest_path: Path, invocation: Mapping[str, object]) -> str:
    return evidence_path(manifest_path, require_text(invocation, "stdout")).read_text(
        encoding="utf-8", errors="replace"
    )


def journal_text(paths: ScenarioPaths) -> str:
    return paths.journal_file.read_text(encoding="utf-8", errors="replace")


def has_terminal_controls(value: str) -> bool:
    return ANSI_PATTERN.search(value) is not None


def has_color_controls(value: str) -> bool:
    return COLOR_PATTERN.search(value) is not None


def scenario_conversion(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(
        manifest,
        manifest_path,
        paths,
        "conversion.mkv",
        duration=10,
        size="640x360",
    )
    source_size = source.stat().st_size
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just_pty(manifest, manifest_path, paths, "conversion")
    operations = archive_operations(paths)
    transcript = invocation_text(manifest_path, invocation)
    journal = journal_text(paths)
    checks = [
        check(
            "conversion.exit",
            invocation["exit_status"] == 0,
            "Just exits successfully",
            0,
            invocation["exit_status"],
        ),
        check(
            "conversion.operation",
            len(operations) == 1
            and operations[0].get("kind") == "converted"
            and operations[0].get("state") == "complete",
            "The real command completes one converted operation",
            {"count": 1, "kind": "converted", "state": "complete"},
            operations,
        ),
        check(
            "conversion.source-removed",
            not source.exists(),
            "The source is removed only after successful publication",
            False,
            source.exists(),
        ),
        check(
            "conversion.pty-output",
            invocation.get("pty") is True
            and "encoding" in transcript
            and "success · converted" in transcript
            and "\x1b[32m" in transcript,
            "The PTY shows measured encoding and an explicit green converted result",
            "encoding plus green success · converted",
            transcript,
            evidence=(cast(str, invocation["stdout"]),),
        ),
        check(
            "conversion.journal-plain-stages",
            not has_terminal_controls(journal)
            and all(
                stage in journal
                for stage in (
                    "inspection",
                    "audio analysis",
                    "encoding",
                    "candidate verification",
                    "publication",
                    "archive verification",
                    "source cleanup",
                )
            ),
            "The journal retains every applicable stage without terminal controls",
            "plain canonical stages",
            journal,
            evidence=(
                evidence_reference(
                    manifest_path,
                    paths.evidence
                    / "files"
                    / "after"
                    / "journal"
                    / "video-archive.log",
                ),
            ),
        ),
    ]
    if operations:
        destination = operation_archive(operations[0])
        checks.append(
            check(
                "conversion.smaller",
                destination is not None and destination.stat().st_size < source_size,
                "The converted archive is smaller than the source",
                f"< {source_size}",
                destination.stat().st_size
                if destination and destination.exists()
                else None,
            )
        )
        checks.extend(
            successful_archive_checks(
                manifest, manifest_path, paths, operations, "conversion"
            )
        )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_ordering(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    older = ffmpeg_fixture(manifest, manifest_path, paths, "z-older.mkv")
    time.sleep(0.05)
    newer = ffmpeg_fixture(manifest, manifest_path, paths, "a-newer.mkv")
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just(manifest, manifest_path, paths, "ordering")
    operations = archive_operations(paths)
    observed = [Path(cast(str, item["source"])).name for item in operations]
    checks = [
        check(
            "ordering.exit",
            invocation["exit_status"] == 0,
            "The ordered batch exits successfully",
            0,
            invocation["exit_status"],
        ),
        check(
            "ordering.source-timestamp",
            observed == [older.name, newer.name],
            "The source timestamp takes precedence over lexical path order",
            [older.name, newer.name],
            observed,
            evidence=(cast(str, invocation["stdout"]),),
        ),
    ]
    checks.extend(
        successful_archive_checks(
            manifest, manifest_path, paths, operations, "ordering"
        )
    )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_open_source(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(manifest, manifest_path, paths, "open-source.mkv")
    source_hash = sha256(source)
    copy_evidence_tree(paths, "before", manifest_path)
    with source.open("rb"):
        invocation = run_just(manifest, manifest_path, paths, "open-source")
    transcript = invocation_text(manifest_path, invocation)
    checks = [
        check(
            "open-source.exit",
            invocation["exit_status"] == 1,
            "An open source makes the batch exit nonzero",
            1,
            invocation["exit_status"],
        ),
        check(
            "open-source.detected",
            "source is open in another process" in transcript,
            "The command reports the open source",
            "source is open in another process",
            transcript,
            evidence=(cast(str, invocation["stdout"]),),
        ),
        check(
            "open-source.retained",
            source.is_file() and sha256(source) == source_hash,
            "The open source remains byte-identical",
            source_hash,
            sha256(source) if source.exists() else None,
        ),
        check(
            "open-source.not-published",
            not archive_operations(paths),
            "An open source creates no durable operation",
            [],
            archive_operations(paths),
        ),
    ]
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_changing_source(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(
        manifest,
        manifest_path,
        paths,
        "changing-source.mkv",
        duration=20,
        size="640x360",
    )
    source_hash = sha256(source)
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just_pty(
        manifest,
        manifest_path,
        paths,
        "changing-source",
        no_color=True,
        mutate_on="encoding",
        mutate_path=source,
    )
    transcript = invocation_text(manifest_path, invocation)
    checks = [
        check(
            "changing-source.exit",
            invocation["exit_status"] == 1,
            "A source change makes the batch exit nonzero",
            1,
            invocation["exit_status"],
        ),
        check(
            "changing-source.detected",
            invocation.get("source_mutated") is True
            and "source changed during conversion" in transcript,
            "The command detects the source change during conversion",
            "mutated and detected",
            {
                "mutated": invocation.get("source_mutated"),
                "transcript": transcript,
            },
            evidence=(cast(str, invocation["stdout"]),),
        ),
        check(
            "changing-source.retained",
            source.is_file() and sha256(source) != source_hash,
            "The changed source remains in the input folder",
            "present with changed hash",
            sha256(source) if source.exists() else None,
        ),
        check(
            "changing-source.not-published",
            not archive_operations(paths),
            "A changed source creates no durable publication",
            [],
            archive_operations(paths),
        ),
    ]
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_lock_contention(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(manifest, manifest_path, paths, "locked.mkv")
    source_hash = sha256(source)
    lock_path = paths.archive / ".video-archive.lock"
    copy_evidence_tree(paths, "before", manifest_path)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        invocation = run_just(manifest, manifest_path, paths, "lock-contention")
    transcript = evidence_path(
        manifest_path, require_text(invocation, "stderr")
    ).read_text(encoding="utf-8", errors="replace")
    checks = [
        check(
            "lock-contention.exit",
            invocation["exit_status"] == 75,
            "Archive lock contention exits with the temporary-failure status",
            75,
            invocation["exit_status"],
        ),
        check(
            "lock-contention.reported",
            "another video archive run is active" in transcript,
            "The command reports the active archive run",
            "another video archive run is active",
            transcript,
            evidence=(cast(str, invocation["stderr"]),),
        ),
        check(
            "lock-contention.source-retained",
            source.is_file() and sha256(source) == source_hash,
            "Lock contention keeps the source byte-identical",
            source_hash,
            sha256(source) if source.exists() else None,
        ),
        check(
            "lock-contention.not-published",
            not archive_operations(paths),
            "Lock contention creates no operation",
            [],
            archive_operations(paths),
        ),
    ]
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def dependency_environment(
    paths: ScenarioPaths,
    label: str,
    commands: Sequence[str],
    *,
    ffmpeg_without_x265: bool = False,
) -> tuple[dict[str, str], dict[str, str]]:
    environment, overrides = child_environment(paths, no_color=True)
    tool_root = paths.scratch / f"path-{label}"
    tool_root.mkdir()
    for command in commands:
        source = sys.executable if command == "python3" else shutil.which(command)
        if source is None:
            raise RuntimeError(f"cannot build dependency fixture without {command}")
        (tool_root / command).symlink_to(source)
    if ffmpeg_without_x265:
        fake_ffmpeg = tool_root / "ffmpeg"
        fake_ffmpeg.write_text("#!/bin/sh\necho 'Encoders:'\n", encoding="utf-8")
        fake_ffmpeg.chmod(0o755)
    overrides["PATH"] = str(tool_root)
    environment["PATH"] = str(tool_root)
    return environment, overrides


def scenario_dependencies(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(manifest, manifest_path, paths, "dependencies.mkv")
    source_hash = sha256(source)
    cases = (
        (
            "python",
            ("bash", "ffmpeg", "ffprobe", "lsof"),
            False,
            "Python 3.11 or newer is required",
        ),
        (
            "ffmpeg",
            ("bash", "python3", "ffprobe", "lsof"),
            False,
            "missing media executable(s): ffmpeg",
        ),
        (
            "ffprobe",
            ("bash", "python3", "ffmpeg", "lsof"),
            False,
            "missing media executable(s): ffprobe",
        ),
        (
            "libx265",
            ("bash", "python3", "ffprobe", "lsof"),
            True,
            "FFmpeg lacks the libx265 encoder",
        ),
        (
            "lsof",
            ("bash", "python3", "ffmpeg", "ffprobe"),
            False,
            "missing open-file inspection tool: lsof",
        ),
    )
    copy_evidence_tree(paths, "before", manifest_path)
    checks: list[Check] = []
    for label, commands, fake_ffmpeg, expected in cases:
        environment, overrides = dependency_environment(
            paths,
            label,
            commands,
            ffmpeg_without_x265=fake_ffmpeg,
        )
        invocation = run_just(
            manifest,
            manifest_path,
            paths,
            f"missing-{label}",
            environment=environment,
            environment_overrides=overrides,
        )
        stderr = evidence_path(
            manifest_path, require_text(invocation, "stderr")
        ).read_text(encoding="utf-8", errors="replace")
        checks.append(
            check(
                f"dependencies.{label}",
                invocation["exit_status"] != 0
                and expected in stderr
                and source.is_file()
                and sha256(source) == source_hash
                and not (paths.archive / ".video-archive-owner.json").exists()
                and not archive_operations(paths),
                f"Missing {label} fails before archive or source mutation",
                {"nonzero": True, "message": expected, "source_retained": True},
                {
                    "exit_status": invocation["exit_status"],
                    "stderr": stderr,
                    "source_sha256": sha256(source) if source.exists() else None,
                },
                evidence=(cast(str, invocation["stderr"]),),
            )
        )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_mixed_batch(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    first = ffmpeg_fixture(manifest, manifest_path, paths, "01-valid.mkv")
    corrupt = paths.inputs[0] / "02-corrupt-client-demo-final.mp4"
    corrupt.write_bytes(b"not a media file\x00verification")
    corrupt_hash = sha256(corrupt)
    last = ffmpeg_fixture(manifest, manifest_path, paths, "03-valid.mkv")
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just_pty(manifest, manifest_path, paths, "mixed-batch", width=48)
    operations = archive_operations(paths)
    transcript = evidence_path(
        manifest_path, cast(str, invocation["stdout"])
    ).read_text(encoding="utf-8")
    order = [transcript.find(name) for name in (first.name, corrupt.name, last.name)]
    checks = [
        check(
            "mixed.exit",
            invocation["exit_status"] == 1,
            "A file-local media failure makes the batch nonzero",
            1,
            invocation["exit_status"],
        ),
        check(
            "mixed.continues",
            len(operations) == 2
            and all(item.get("state") == "complete" for item in operations),
            "Both valid files publish despite the corrupt file between them",
            2,
            operations,
        ),
        check(
            "mixed.order",
            all(position >= 0 for position in order) and order == sorted(order),
            "The transcript records valid, corrupt, valid processing order",
            [first.name, corrupt.name, last.name],
            order,
            evidence=(cast(str, invocation["stdout"]),),
        ),
        check(
            "mixed.failed-source-retained",
            corrupt.is_file() and sha256(corrupt) == corrupt_hash,
            "The corrupt source remains byte-identical",
            corrupt_hash,
            sha256(corrupt) if corrupt.exists() else None,
        ),
        check(
            "mixed.successful-sources-removed",
            not first.exists() and not last.exists(),
            "Both successful sources are removed",
            False,
            {first.name: first.exists(), last.name: last.exists()},
        ),
        check(
            "mixed.narrow-pty",
            invocation.get("terminal_width") == 48
            and "[2/3]" in transcript
            and "demo-final.mp4" in transcript
            and "failure · failed" in transcript
            and "\x1b[31m" in transcript,
            "The narrow PTY preserves counts, filename suffix, and red failure text",
            "48 columns with [2/3], filename suffix, and red failure · failed",
            transcript,
            evidence=(cast(str, invocation["stdout"]),),
        ),
    ]
    checks.extend(
        successful_archive_checks(manifest, manifest_path, paths, operations, "mixed")
    )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_original_fallback(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(
        manifest, manifest_path, paths, "fallback.mp4", compact=True
    )
    source_hash = sha256(source)
    source_size = source.stat().st_size
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just_pty(
        manifest, manifest_path, paths, "original-fallback", no_color=True
    )
    operations = archive_operations(paths)
    destination = operation_archive(operations[0]) if operations else None
    archive_hash = sha256(destination) if destination and destination.exists() else None
    transcript = invocation_text(manifest_path, invocation)
    checks = [
        check(
            "fallback.exit",
            invocation["exit_status"] == 0,
            "Just exits successfully",
            0,
            invocation["exit_status"],
        ),
        check(
            "fallback.operation",
            len(operations) == 1
            and operations[0].get("kind") == "original"
            and operations[0].get("state") == "complete",
            "The real command selects original preservation",
            {"count": 1, "kind": "original", "state": "complete"},
            operations,
        ),
        check(
            "fallback.byte-identical",
            destination is not None
            and destination.stat().st_size == source_size
            and archive_hash == source_hash,
            "The archived original is byte-identical",
            {"bytes": source_size, "sha256": source_hash},
            {
                "bytes": destination.stat().st_size
                if destination and destination.exists()
                else None,
                "sha256": archive_hash,
            },
        ),
        check(
            "fallback.source-removed",
            not source.exists(),
            "The source is removed after verified original publication",
            False,
            source.exists(),
        ),
        check(
            "fallback.no-color-pty",
            invocation.get("pty") is True
            and not has_color_controls(transcript)
            and "[OK] success · original archived" in transcript
            and "original preservation" in journal_text(paths),
            "NO_COLOR keeps explicit original fallback labels and stages",
            "plain [OK] success · original archived",
            transcript,
            evidence=(cast(str, invocation["stdout"]),),
        ),
    ]
    if operations:
        checks.extend(
            successful_archive_checks(
                manifest, manifest_path, paths, operations, "fallback"
            )
        )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_cleanup_pending(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(manifest, manifest_path, paths, "cleanup-pending.mkv")
    source_hash = sha256(source)
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just_pty(
        manifest,
        manifest_path,
        paths,
        "cleanup-pending",
        cleanup_pending=True,
    )
    operations = archive_operations(paths)
    transcript = invocation_text(manifest_path, invocation)
    pending = [item for item in operations if item.get("state") == "cleanup_pending"]
    checks = [
        check(
            "cleanup-pending.exit",
            invocation["exit_status"] == 1,
            "A verified publication with unresolved source removal exits one",
            1,
            invocation["exit_status"],
        ),
        check(
            "cleanup-pending.operation",
            len(pending) == 1,
            "The durable operation records cleanup pending",
            1,
            pending,
        ),
        check(
            "cleanup-pending.source-retained",
            source.is_file() and sha256(source) == source_hash,
            "The unresolved source remains byte-identical",
            source_hash,
            sha256(source) if source.exists() else None,
        ),
        check(
            "cleanup-pending.pty-output",
            invocation.get("pty") is True
            and "unresolved · cleanup pending" in transcript
            and "Unresolved: cleanup-pending.mkv:" in transcript,
            "The PTY keeps the cleanup-pending outcome and reason in scrollback",
            "unresolved · cleanup pending with reason",
            transcript,
            evidence=(cast(str, invocation["stdout"]),),
        ),
    ]
    checks.extend(
        successful_archive_checks(
            manifest, manifest_path, paths, pending, "cleanup-pending"
        )
    )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_interruption(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(
        manifest,
        manifest_path,
        paths,
        "interrupted-client-walkthrough.mkv",
        duration=30,
        size="640x360",
    )
    source_hash = sha256(source)
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just_pty(
        manifest,
        manifest_path,
        paths,
        "interruption",
        interrupt_on="encoding",
        timeout=60,
    )
    transcript = invocation_text(manifest_path, invocation)
    operations = archive_operations(paths)
    checks = [
        check(
            "interruption.exit",
            invocation["exit_status"] == 130,
            "SIGINT during encoding exits 130",
            130,
            invocation["exit_status"],
        ),
        check(
            "interruption.signal",
            invocation.get("signals") == ["SIGINT"],
            "The verifier sends one SIGINT to its owned process group",
            ["SIGINT"],
            invocation.get("signals"),
        ),
        check(
            "interruption.source-retained",
            source.is_file() and sha256(source) == source_hash,
            "The interrupted source remains byte-identical",
            source_hash,
            sha256(source) if source.exists() else None,
        ),
        check(
            "interruption.not-published",
            not operations
            and not any(
                item.is_file() and not item.name.startswith(".video-archive")
                for item in paths.archive.iterdir()
            ),
            "No archive reports success before publication and verification",
            "no operation or published archive",
            operations,
        ),
        check(
            "interruption.pty-output",
            "encoding" in transcript
            and "■ interrupted" in transcript
            and "Outcomes:" in transcript,
            "The PTY retains the interrupted item and final summary",
            "encoding, interrupted outcome, and summary",
            transcript,
            evidence=(cast(str, invocation["stdout"]),),
        ),
    ]
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_output_contracts(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    ffmpeg_fixture(manifest, manifest_path, paths, "redirected.mkv")
    redirected = run_just(manifest, manifest_path, paths, "redirected")
    redirected_stdout = invocation_text(manifest_path, redirected)
    redirected_stderr = evidence_path(
        manifest_path, require_text(redirected, "stderr")
    ).read_text(encoding="utf-8", errors="replace")

    ffmpeg_fixture(manifest, manifest_path, paths, "json.mkv")
    # -v adds the progress lines and results that a redirected run keeps quiet.
    json_invocation = run_just(manifest, manifest_path, paths, "json", "--json", "-v")
    json_stdout = invocation_text(manifest_path, json_invocation)
    json_stderr = evidence_path(
        manifest_path, require_text(json_invocation, "stderr")
    ).read_text(encoding="utf-8", errors="replace")
    try:
        document = cast(object, json.loads(json_stdout))
    except json.JSONDecodeError:
        document = None
    archived = redirected_stdout.splitlines()
    checks = [
        check(
            "output.redirected",
            redirected["exit_status"] == 0
            and not has_terminal_controls(redirected_stdout)
            and "\r" not in redirected_stdout
            and len(archived) == 1
            and archived[0].endswith(".mp4")
            and Path(archived[0]).is_file()
            and not redirected_stderr,
            "Redirected stdout lists the archived file; stderr stays quiet",
            "one archived path on stdout and empty stderr",
            {"stdout": redirected_stdout, "stderr": redirected_stderr},
            evidence=(
                cast(str, redirected["stdout"]),
                cast(str, redirected["stderr"]),
            ),
        ),
        check(
            "output.json",
            json_invocation["exit_status"] == 0
            and isinstance(document, dict)
            and document.get("schema") == "video-archive.batch/v1"
            and document.get("outcomes", {}).get("converted") == 1,
            "JSON mode writes one schema-valid batch document on stdout",
            {"schema": "video-archive.batch/v1", "converted": 1},
            document,
            evidence=(cast(str, json_invocation["stdout"]),),
        ),
        check(
            "output.json-stderr",
            not has_terminal_controls(json_stderr)
            and "encoding" in json_stderr
            and "success · converted" in json_stderr,
            "With -v, JSON progress and the outcome stay plain on stderr",
            "plain progress and durable outcome on stderr",
            json_stderr,
            evidence=(cast(str, json_invocation["stderr"]),),
        ),
        check(
            "output.journal-plain",
            not has_terminal_controls(journal_text(paths)),
            "The combined journal contains no terminal controls",
            "plain text",
            journal_text(paths),
        ),
    ]
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def scenario_collision(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(manifest, manifest_path, paths, "collision.mkv")
    occupied = paths.archive / "collision.mp4"
    shutil.copy2(source, occupied)
    occupied_hash = sha256(occupied)
    copy_evidence_tree(paths, "before", manifest_path)
    invocation = run_just(manifest, manifest_path, paths, "collision")
    operations = archive_operations(paths)
    destination = operation_archive(operations[0]) if operations else None
    checks = [
        check(
            "collision.exit",
            invocation["exit_status"] == 0,
            "Just exits successfully",
            0,
            invocation["exit_status"],
        ),
        check(
            "collision.existing-preserved",
            occupied.is_file() and sha256(occupied) == occupied_hash,
            "The occupied destination is not replaced",
            occupied_hash,
            sha256(occupied) if occupied.exists() else None,
        ),
        check(
            "collision.suffixed",
            destination is not None and destination.name == "collision (2).mp4",
            "The archive uses the next suffix",
            "collision (2).mp4",
            destination.name if destination else None,
        ),
        check(
            "collision.source-removed",
            not source.exists(),
            "The successful source is removed",
            False,
            source.exists(),
        ),
    ]
    if operations:
        checks.extend(
            successful_archive_checks(
                manifest, manifest_path, paths, operations, "collision"
            )
        )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def interrupted_invocation(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> tuple[dict[str, object], dict[str, object]]:
    environment, overrides = child_environment(paths, no_color=True, pause_seconds=60)
    argv = just_argv(manifest)
    directory = (
        paths.evidence
        / "commands"
        / f"{len(cast(list[object], manifest['invocations'])):03d}-recovery-interrupted"
    )
    directory.mkdir(parents=True)
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    started = now()
    with (
        stdout_path.open("w", encoding="utf-8") as stdout,
        stderr_path.open("w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            argv,
            cwd=Path(require_text(manifest, "checkout")),
            env=environment,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        pgid = os.getpgid(process.pid)
        deadline = time.monotonic() + 180
        observed: dict[str, object] | None = None
        while time.monotonic() < deadline:
            operations = archive_operations(paths)
            prepared = [item for item in operations if item.get("state") == "prepared"]
            if prepared:
                observed = dict(prepared[0])
                break
            returncode = process.poll()
            if returncode is not None:
                raise RuntimeError(
                    f"archive exited before a prepared record was observed: {returncode}"
                )
            time.sleep(0.05)
        if observed is None:
            os.killpg(pgid, signal.SIGTERM)
            process.wait(timeout=5)
            raise RuntimeError("timed out waiting for a prepared operation record")
        os.killpg(pgid, signal.SIGSTOP)
        time.sleep(0.1)
        stable = archive_operations(paths)
        stable_match = next(
            (
                item
                for item in stable
                if item.get("operation_id") == observed.get("operation_id")
            ),
            None,
        )
        if stable_match is None or stable_match.get("state") != "prepared":
            os.killpg(pgid, signal.SIGCONT)
            os.killpg(pgid, signal.SIGTERM)
            process.wait(timeout=5)
            raise RuntimeError(
                "prepared operation did not remain stable after stopping the owned group"
            )
        snapshot_path = paths.evidence / "interrupted-operation.json"
        atomic_json(snapshot_path, stable_match)
        os.killpg(pgid, signal.SIGKILL)
        returncode = process.wait(timeout=5)
    record: dict[str, object] = {
        "label": "recovery-interrupted",
        "argv": argv,
        "cwd": require_text(manifest, "checkout"),
        "environment_overrides": overrides,
        "pid": process.pid,
        "process_group": pgid,
        "started_at": started,
        "finished_at": now(),
        "exit_status": returncode,
        "signals": ["SIGSTOP", "SIGKILL"],
        "stdout": evidence_reference(manifest_path, stdout_path),
        "stderr": evidence_reference(manifest_path, stderr_path),
        "operation_snapshot": evidence_reference(manifest_path, snapshot_path),
    }
    append_invocation(manifest, record)
    save_manifest(manifest_path, manifest)
    return record, stable_match


def scenario_recovery(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    source = ffmpeg_fixture(manifest, manifest_path, paths, "recovery.mkv")
    source_hash = sha256(source)
    copy_evidence_tree(paths, "before", manifest_path)
    interrupted, operation = interrupted_invocation(manifest, manifest_path, paths)
    candidate = Path(cast(str, operation["candidate"]))
    destination = Path(cast(str, operation["destination"]))
    interruption_checks = [
        check(
            "recovery.owned-group-stopped",
            interrupted["exit_status"] != 0,
            "The verifier stops only its owned process group",
            "nonzero signal exit",
            interrupted["exit_status"],
            evidence=(cast(str, interrupted["operation_snapshot"]),),
        ),
        check(
            "recovery.durable-prepared",
            operation.get("state") == "prepared" and candidate.is_file(),
            "A durable prepared operation and candidate exist before recovery",
            "prepared with candidate",
            operation,
        ),
        check(
            "recovery.source-retained",
            source.is_file() and sha256(source) == source_hash,
            "The interrupted source remains byte-identical",
            source_hash,
            sha256(source) if source.exists() else None,
        ),
        check(
            "recovery.not-published",
            not destination.exists(),
            "The paused publication has not created its destination",
            False,
            destination.exists(),
        ),
    ]
    copy_evidence_tree(paths, "interrupted", manifest_path)
    resumed = run_just(manifest, manifest_path, paths, "recovery-resumed")
    operations = archive_operations(paths)
    same = next(
        (
            item
            for item in operations
            if item.get("operation_id") == operation.get("operation_id")
        ),
        None,
    )
    archives = [
        item
        for item in paths.archive.iterdir()
        if item.is_file()
        and not item.name.startswith(".video-archive")
        and not item.name.startswith(".recovery.video-archive")
    ]
    checks = interruption_checks + [
        check(
            "recovery.resumed-exit",
            resumed["exit_status"] == 0,
            "The second real Just invocation succeeds",
            0,
            resumed["exit_status"],
        ),
        check(
            "recovery.same-operation",
            same is not None and same.get("state") == "complete",
            "Recovery completes the same durable operation",
            {"operation_id": operation.get("operation_id"), "state": "complete"},
            same,
        ),
        check(
            "recovery.no-duplicate",
            len(archives) == 1 and destination in archives,
            "Recovery publishes exactly one destination",
            [str(destination)],
            [str(item) for item in archives],
        ),
        check(
            "recovery.source-removed",
            not source.exists(),
            "Recovery removes the source after archive verification",
            False,
            source.exists(),
        ),
    ]
    if same is not None:
        checks.extend(
            successful_archive_checks(
                manifest, manifest_path, paths, [same], "recovery"
            )
        )
    copy_evidence_tree(paths, "after", manifest_path)
    return checks


def create_real_batch(seed: Path, paths: ScenarioPaths, count: int = 100) -> None:
    for index in range(count):
        shutil.copy2(seed, paths.inputs[0] / f"batch-{index:03d}.mkv")


def invocation_json(
    manifest_path: Path, invocation: Mapping[str, object]
) -> dict[str, object]:
    raw = cast(object, json.loads(invocation_text(manifest_path, invocation)))
    if not isinstance(raw, dict):
        raise TypeError("archive JSON output is not an object")
    return cast(dict[str, object], raw)


def batch_observation(
    paths: ScenarioPaths,
    invocation: Mapping[str, object],
    document: Mapping[str, object],
    expected_count: int = 100,
) -> dict[str, object]:
    outcomes = document.get("outcomes")
    results = document.get("results")
    scheduling = document.get("scheduling")
    resources = invocation.get("resources")
    return {
        "exit_status": invocation.get("exit_status"),
        "result_count": len(results) if isinstance(results, list) else None,
        "outcome_count": (
            sum(value for value in outcomes.values() if isinstance(value, int))
            if isinstance(outcomes, dict)
            else None
        ),
        "operation_count": len(archive_operations(paths)),
        "source_count": sum(
            1 for root in paths.inputs for path in root.iterdir() if path.is_file()
        ),
        "archive_count": sum(
            1
            for path in paths.archive.iterdir()
            if path.is_file() and not path.name.startswith(".video-archive")
        ),
        "scheduling": scheduling,
        "resources": resources,
        "throughput_videos_per_second": (
            expected_count / cast(float, resources["wall_seconds"])
            if isinstance(resources, dict)
            and isinstance(resources.get("wall_seconds"), int | float)
            and resources["wall_seconds"] > 0
            else None
        ),
    }


def pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def interrupt_parallel_batch(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> tuple[dict[str, object], dict[str, object]]:
    environment, overrides = child_environment(paths, no_color=True)
    argv = [*just_argv(manifest), "--json"]
    directory = (
        paths.evidence
        / "commands"
        / f"{len(cast(list[object], manifest['invocations'])):03d}-parallel-interruption"
    )
    directory.mkdir(parents=True)
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    started = now()
    started_monotonic = time.monotonic()
    with (
        stdout_path.open("w", encoding="utf-8") as stdout,
        stderr_path.open("w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            argv,
            cwd=Path(require_text(manifest, "checkout")),
            env=environment,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        pgid = os.getpgid(process.pid)
        deadline = time.monotonic() + 180
        sample: dict[str, object] = {}
        while time.monotonic() < deadline:
            stderr.flush()
            text = stderr_path.read_text(encoding="utf-8", errors="replace")
            if "encoding" in text:
                sample = process_tree_sample(process.pid)
                if sample.get("media_pids"):
                    break
            if process.poll() is not None:
                raise RuntimeError(
                    f"parallel batch exited before interruption: {process.returncode}"
                )
            time.sleep(0.05)
        if not sample:
            os.killpg(pgid, signal.SIGTERM)
            process.wait(timeout=5)
            raise RuntimeError("timed out waiting for parallel encoding")
        lock_probe = run_just(
            manifest, manifest_path, paths, "parallel-lock-probe", "--json"
        )
        media_pids = cast(list[int], sample["media_pids"])
        interrupted_at = time.monotonic()
        os.killpg(pgid, signal.SIGINT)
        try:
            returncode = process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(pgid, signal.SIGTERM)
            returncode = process.wait(timeout=5)
    latency = time.monotonic() - interrupted_at
    lingering = [pid for pid in media_pids if pid_exists(pid)]
    record: dict[str, object] = {
        "label": "parallel-interruption",
        "argv": argv,
        "cwd": require_text(manifest, "checkout"),
        "environment_overrides": overrides,
        "pid": process.pid,
        "process_group": pgid,
        "started_at": started,
        "finished_at": now(),
        "wall_seconds": time.monotonic() - started_monotonic,
        "exit_status": returncode,
        "signals": ["SIGINT"],
        "interrupt_latency_seconds": latency,
        "owned_media_pids_before": media_pids,
        "owned_media_pids_after": lingering,
        "lock_probe_exit_status": lock_probe["exit_status"],
        "stdout": evidence_reference(manifest_path, stdout_path),
        "stderr": evidence_reference(manifest_path, stderr_path),
    }
    append_invocation(manifest, record)
    save_manifest(manifest_path, manifest)
    return record, lock_probe


def scenario_parallel_batch(
    manifest: dict[str, object], manifest_path: Path, paths: ScenarioPaths
) -> list[Check]:
    checkout = Path(require_text(manifest, "checkout"))
    seed = ffmpeg_fixture(
        manifest,
        manifest_path,
        paths,
        "parallel-seed.mkv",
        duration=1,
        size="96x64",
    )
    recovery_seed = ffmpeg_fixture(
        manifest,
        manifest_path,
        paths,
        "parallel-recovery-seed.mkv",
        duration=5,
        size="320x180",
    )
    representative_seed = ffmpeg_fixture(
        manifest,
        manifest_path,
        paths,
        "parallel-representative-seed.mkv",
        duration=3,
        size="1280x720",
    )
    variants = {
        label: make_variant_paths(paths, checkout, label)
        for label in ("serial", "normal", "maximum", "recovery", "representative")
    }
    for label, variant in variants.items():
        if label == "representative":
            create_real_batch(representative_seed, variant, count=6)
        else:
            create_real_batch(recovery_seed if label == "recovery" else seed, variant)
            copy_evidence_tree(variant, "before", manifest_path)

    invocations = {
        "serial": run_just(
            manifest,
            manifest_path,
            variants["serial"],
            "parallel-serial",
            "--jobs",
            "1",
            "--json",
            measure_resources=True,
        ),
        "normal": run_just(
            manifest,
            manifest_path,
            variants["normal"],
            "parallel-normal",
            "--json",
            measure_resources=True,
        ),
        "maximum": run_just(
            manifest,
            manifest_path,
            variants["maximum"],
            "parallel-maximum",
            "--resource-mode",
            "maximum",
            "--json",
            measure_resources=True,
        ),
        "representative": run_just(
            manifest,
            manifest_path,
            variants["representative"],
            "parallel-representative-maximum",
            "--resource-mode",
            "maximum",
            "--json",
            measure_resources=True,
        ),
    }
    documents = {
        label: invocation_json(manifest_path, invocation)
        for label, invocation in invocations.items()
    }
    observations = {
        label: batch_observation(
            variants[label],
            invocations[label],
            document,
            expected_count=6 if label == "representative" else 100,
        )
        for label, document in documents.items()
    }
    checks: list[Check] = []
    for label in ("serial", "normal", "maximum"):
        observation = observations[label]
        scheduling = observation.get("scheduling")
        resources = observation.get("resources")
        selected = (
            scheduling.get("selected_jobs") if isinstance(scheduling, dict) else None
        )
        peak = (
            resources.get("peak_media_processes")
            if isinstance(resources, dict)
            else None
        )
        checks.extend(
            [
                check(
                    f"parallel.{label}.accounting",
                    observation["exit_status"] == 0
                    and observation["result_count"] == 100
                    and observation["outcome_count"] == 100
                    and observation["operation_count"] == 100
                    and observation["source_count"] == 0
                    and observation["archive_count"] == 100,
                    f"The {label} run has one final result and archive per source",
                    {
                        "exit_status": 0,
                        "results": 100,
                        "outcomes": 100,
                        "operations": 100,
                        "sources": 0,
                        "archives": 100,
                    },
                    observation,
                    evidence=(cast(str, invocations[label]["stdout"]),),
                ),
                check(
                    f"parallel.{label}.bounded",
                    isinstance(selected, int)
                    and isinstance(peak, int)
                    and 1 <= peak <= selected
                    and (selected == 1 or peak > 1),
                    f"The {label} run stays within its selected worker limit",
                    "1 <= observed media processes <= selected jobs",
                    {"selected_jobs": selected, "peak_media_processes": peak},
                ),
                check(
                    f"parallel.{label}.measurement",
                    isinstance(resources, dict)
                    and cast(int, resources.get("sample_count", 0)) > 0
                    and cast(int, resources.get("peak_rss_bytes", 0)) > 0
                    and cast(float, resources.get("cpu_seconds", 0.0)) > 0
                    and observation["throughput_videos_per_second"] is not None,
                    f"The {label} run records throughput, memory, CPU, and sessions",
                    "positive measured resources and throughput",
                    observation,
                ),
            ]
        )
        copy_evidence_tree(variants[label], "after", manifest_path)

    representative = observations["representative"]
    representative_scheduling = representative.get("scheduling")
    representative_resources = representative.get("resources")
    representative_selected = (
        representative_scheduling.get("selected_jobs")
        if isinstance(representative_scheduling, dict)
        else None
    )
    representative_peak = (
        representative_resources.get("peak_media_processes")
        if isinstance(representative_resources, dict)
        else None
    )
    checks.append(
        check(
            "parallel.representative-resource-load",
            representative["exit_status"] == 0
            and representative["result_count"] == 6
            and representative["outcome_count"] == 6
            and representative["operation_count"] == 6
            and representative["source_count"] == 0
            and representative["archive_count"] == 6
            and isinstance(representative_selected, int)
            and isinstance(representative_peak, int)
            and 1 <= representative_peak <= representative_selected
            and (representative_selected == 1 or representative_peak > 1)
            and isinstance(representative_resources, dict)
            and cast(int, representative_resources.get("peak_rss_bytes", 0)) > 0
            and cast(float, representative_resources.get("cpu_seconds", 0.0)) > 0,
            "Representative 1280x720 work uses the selected safe worker limit",
            {
                "exit_status": 0,
                "results": 6,
                "bounded_by_selected_jobs": True,
                "measured_resources": True,
            },
            representative,
            evidence=(cast(str, invocations["representative"]["stdout"]),),
        )
    )

    interrupted, lock_probe = interrupt_parallel_batch(
        manifest, manifest_path, variants["recovery"]
    )
    interrupted_document = invocation_json(manifest_path, interrupted)
    interrupted_outcomes = interrupted_document.get("outcomes")
    interrupted_results = interrupted_document.get("results")
    interrupted_total = (
        sum(value for value in interrupted_outcomes.values() if isinstance(value, int))
        if isinstance(interrupted_outcomes, dict)
        else None
    )
    resumed = run_just(
        manifest,
        manifest_path,
        variants["recovery"],
        "parallel-recovery",
        "--json",
        measure_resources=True,
    )
    resumed_document = invocation_json(manifest_path, resumed)
    operations = archive_operations(variants["recovery"])
    archives = [
        path
        for path in variants["recovery"].archive.iterdir()
        if path.is_file() and not path.name.startswith(".video-archive")
    ]
    remaining_sources = [
        path
        for root in variants["recovery"].inputs
        for path in root.iterdir()
        if path.is_file()
    ]
    checks.extend(
        [
            check(
                "parallel.interruption",
                interrupted["exit_status"] == 130
                and cast(float, interrupted["interrupt_latency_seconds"]) <= 10
                and bool(interrupted["owned_media_pids_before"])
                and not interrupted["owned_media_pids_after"],
                "SIGINT exits 130 within ten seconds and leaves no owned media child",
                {"exit_status": 130, "latency_at_most": 10, "lingering": []},
                interrupted,
                evidence=(
                    cast(str, interrupted["stdout"]),
                    cast(str, interrupted["stderr"]),
                ),
            ),
            check(
                "parallel.interrupted-accounting",
                isinstance(interrupted_results, list)
                and len(interrupted_results) == 100
                and interrupted_total == 100,
                "The interrupted run writes one final result per discovered source",
                {"results": 100, "outcomes": 100},
                {
                    "results": len(interrupted_results)
                    if isinstance(interrupted_results, list)
                    else None,
                    "outcomes": interrupted_total,
                },
            ),
            check(
                "parallel.lock-contention",
                lock_probe["exit_status"] == 75,
                "A second real invocation exits 75 while the first owns the archive",
                75,
                lock_probe["exit_status"],
                evidence=(cast(str, lock_probe["stderr"]),),
            ),
            check(
                "parallel.recovery",
                resumed["exit_status"] == 0
                and len(operations) == 100
                and all(item.get("state") == "complete" for item in operations)
                and len(archives) == 100
                and len({path.name for path in archives}) == 100
                and not remaining_sources,
                "Recovery completes all sources without duplicate publication",
                {
                    "exit_status": 0,
                    "operations": 100,
                    "archives": 100,
                    "sources": 0,
                },
                {
                    "exit_status": resumed["exit_status"],
                    "operations": len(operations),
                    "archives": len(archives),
                    "sources": len(remaining_sources),
                    "resumed_results": len(
                        cast(list[object], resumed_document.get("results", []))
                    ),
                },
                evidence=(cast(str, resumed["stdout"]),),
            ),
        ]
    )
    checks.extend(
        successful_archive_checks(
            manifest,
            manifest_path,
            variants["recovery"],
            operations,
            "parallel-recovery",
        )
    )
    copy_evidence_tree(variants["recovery"], "after", manifest_path)
    return checks


SCENARIO_FUNCTIONS = {
    "conversion": scenario_conversion,
    "ordering": scenario_ordering,
    "open-source": scenario_open_source,
    "changing-source": scenario_changing_source,
    "lock-contention": scenario_lock_contention,
    "dependencies": scenario_dependencies,
    "mixed-batch": scenario_mixed_batch,
    "original-fallback": scenario_original_fallback,
    "cleanup-pending": scenario_cleanup_pending,
    "interruption": scenario_interruption,
    "output-contracts": scenario_output_contracts,
    "collision": scenario_collision,
    "recovery": scenario_recovery,
    "parallel-batch": scenario_parallel_batch,
}


def all_checks(manifest: Mapping[str, object]) -> list[Mapping[str, object]]:
    """Doctor's checks, then each driven scenario's, as the manifest holds them."""
    checks: list[Mapping[str, object]] = []
    raw_doctor = manifest.get("doctor", [])
    if isinstance(raw_doctor, list):
        checks.extend(cast(list[Mapping[str, object]], raw_doctor))
    raw_scenarios = manifest.get("scenarios", {})
    if isinstance(raw_scenarios, dict):
        for raw in raw_scenarios.values():
            if isinstance(raw, dict) and isinstance(raw.get("checks"), list):
                checks.extend(cast(list[Mapping[str, object]], raw["checks"]))
    return checks


def recompute_summary(manifest: dict[str, object]) -> None:
    checks = all_checks(manifest)
    counts = {status: 0 for status in ("passed", "failed", "skipped", "unmet")}
    for item in checks:
        status = item.get("status")
        if isinstance(status, str) and status in counts:
            counts[status] += 1
    verdict = "passed"
    if counts["failed"]:
        verdict = "failed"
    elif counts["unmet"] or counts["skipped"]:
        verdict = "unmet"
    manifest["summary"] = {**counts, "verdict": verdict}


def drive(manifest_path: Path, selected: str) -> dict[str, object]:
    manifest = load_manifest(manifest_path)
    doctor_checks = manifest.get("doctor")
    if not isinstance(doctor_checks, list) or not doctor_checks:
        raise ValueError("run doctor before drive")
    platform_ready = all(
        isinstance(item, dict) and item.get("status") == "passed"
        for item in doctor_checks
    )
    features = FEATURES if selected == "all" else (selected,)
    scenarios = manifest.setdefault("scenarios", {})
    if not isinstance(scenarios, dict):
        raise TypeError("manifest scenarios is invalid")
    for feature in features:
        log.info("driving %s", feature)
        paths = manifest_paths(manifest, feature, manifest_path)
        started = now()
        if not platform_ready:
            result_checks = [
                Check(
                    f"{feature}.platform",
                    "skipped",
                    "The real-media scenario was not run because doctor found an unmet requirement",
                    "all doctor checks passed",
                    "scenario not started",
                )
            ]
        else:
            try:
                result_checks = SCENARIO_FUNCTIONS[feature](
                    manifest, manifest_path, paths
                )
            except (
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
                subprocess.SubprocessError,
            ) as error:
                copy_evidence_tree(paths, "failure", manifest_path)
                result_checks = [
                    Check(
                        f"{feature}.driver",
                        "failed",
                        "The scenario driver completed without an internal error",
                        "completed",
                        str(error),
                    )
                ]
        scenarios[feature] = {
            "started_at": started,
            "finished_at": now(),
            "checks": [asdict(item) for item in result_checks],
        }
        save_manifest(manifest_path, manifest)
    manifest["phase"] = "driven"
    recompute_summary(manifest)
    save_manifest(manifest_path, manifest)
    return cast(dict[str, object], manifest["summary"])


def evidence(manifest_path: Path) -> dict[str, object]:
    manifest = load_manifest(manifest_path)
    missing: list[str] = []
    invocations = manifest.get("invocations", [])
    if isinstance(invocations, list):
        for raw in invocations:
            if not isinstance(raw, dict):
                continue
            for key in ("stdout", "stderr"):
                value = raw.get(key)
                if (
                    isinstance(value, str)
                    and not evidence_path(manifest_path, value).is_file()
                ):
                    missing.append(value)
            snapshot = raw.get("operation_snapshot")
            if (
                isinstance(snapshot, str)
                and not evidence_path(manifest_path, snapshot).is_file()
            ):
                missing.append(snapshot)
    prior_inventory = manifest.get("evidence_files", [])
    if isinstance(prior_inventory, list):
        for raw in prior_inventory:
            if not isinstance(raw, dict):
                continue
            reference = raw.get("path")
            expected_hash = raw.get("sha256")
            if not isinstance(reference, str):
                continue
            path = evidence_path(manifest_path, reference)
            if not path.is_file() or (
                isinstance(expected_hash, str) and sha256(path) != expected_hash
            ):
                missing.append(reference)
    if not missing:
        evidence_files: list[dict[str, object]] = []
        for path in sorted(manifest_path.parent.rglob("*")):
            if not path.is_file() or path == manifest_path:
                continue
            evidence_files.append(
                {
                    "path": evidence_reference(manifest_path, path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        manifest["evidence_files"] = evidence_files
    recompute_summary(manifest)
    summary = cast(dict[str, object], manifest["summary"])
    summary["evidence_missing"] = missing
    if missing:
        summary["verdict"] = "failed"
    if manifest.get("phase") != "cleaned":
        manifest["phase"] = "evidence"
    save_manifest(manifest_path, manifest)
    return summary


def cleanup(manifest_path: Path) -> dict[str, object]:
    manifest = load_manifest(manifest_path)
    paths = manifest.get("paths")
    if not isinstance(paths, dict):
        raise TypeError("manifest paths is invalid")
    run_root = Path(require_text(cast(dict[str, object], paths), "run_root"))
    evidence_root = evidence_path(
        manifest_path, require_text(cast(dict[str, object], paths), "evidence")
    )
    if not run_root.exists():
        result = {
            "status": "already-removed",
            "run_root": str(run_root),
            "evidence_survived": manifest_path.is_file(),
        }
        manifest["cleanup"] = result
        save_manifest(manifest_path, manifest)
        return result
    if run_root.is_symlink() or not run_root.name.startswith(
        "verify-video-archive-run-"
    ):
        raise ValueError(f"refusing cleanup of unowned path: {run_root}")
    resolved = run_root.resolve(strict=True)
    if (
        resolved != run_root
        or evidence_root == resolved
        or resolved in evidence_root.parents
    ):
        raise ValueError("refusing cleanup because ownership paths are unsafe")
    owner_path = run_root / "owner.json"
    owner = cast(object, json.loads(owner_path.read_text(encoding="utf-8")))
    if not isinstance(owner, dict):
        raise TypeError("run ownership marker is invalid")
    if (
        owner.get("schema") != OWNER_SCHEMA
        or owner.get("run_id") != manifest.get("run_id")
        or owner.get("token") != manifest.get("owner_token")
    ):
        raise ValueError("run ownership marker does not match the manifest")
    shutil.rmtree(run_root)
    result = {
        "status": "removed",
        "run_root": str(run_root),
        "evidence_survived": manifest_path.is_file(),
        "finished_at": now(),
    }
    manifest["cleanup"] = result
    manifest["phase"] = "cleaned"
    save_manifest(manifest_path, manifest)
    return result


def run_all(
    checkout: Path, evidence_parent: Path | None, selected: str
) -> tuple[Path, dict[str, object]]:
    manifest_path = launch(checkout, evidence_parent)
    try:
        doctor(manifest_path)
        drive(manifest_path, selected)
        summary = evidence(manifest_path)
        cleanup(manifest_path)
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        # The manifest of a run that stopped midway stays readable
        raise ScriptError(str(error), report={"file": str(manifest_path)}) from error
    except KeyboardInterrupt as stop:
        code = getattr(stop, "code", INTERRUPTED)
        error = ScriptError(
            "interrupted" if code == INTERRUPTED else "terminated",
            report={"file": str(manifest_path)},
        )
        error.code = code
        raise error from stop
    return manifest_path, summary


EPILOG = """\
commands:
  launch --checkout DIR [--evidence-root DIR]
      create a run; answers {"ok":true,"file":"MANIFEST"}
  doctor --manifest MANIFEST
      check the platform and tools; answers {"ok":true}
  drive --manifest MANIFEST [--feature all|FEATURE]
      run scenarios through just convert-video; answers {"ok":true}
  evidence --manifest MANIFEST
      recheck the retained files and hashes; answers {"ok":true}
  cleanup --manifest MANIFEST
      remove the run root; answers {"ok":true,"changes":[["remove","RUN_ROOT"]]}
  run --checkout DIR [--evidence-root DIR] [--feature all|FEATURE]
      launch, doctor, drive, evidence, and cleanup in one run; answers
      {"ok":true,"file":"MANIFEST"}

A check that did not pass fails the command: stdout stays empty and stderr ends
with {"ok":false,"errors":["ID STATUS: SUMMARY; expected E, observed O",...]},
one error per check, and run adds "file". Read each check's expected and observed values in MANIFEST, or
add -v to print them on stderr.

examples:
  verify-video-archive launch --checkout ~/dotfiles
  verify-video-archive drive --manifest MANIFEST --feature conversion -v
  verify-video-archive run --checkout ~/dotfiles --feature all

features:
""" + textwrap.fill(
    ", ".join(FEATURES), width=79, initial_indent="  ", subsequent_indent="  "
)
EXIT_CODES = exit_codes(
    {
        0: "every check passed, or the command finished",
        1: "a check did not pass, or the verifier could not run",
    }
)


def parser() -> Parser:
    root = Parser(
        prog="verify-video-archive",
        description="Drive the checkout video archive through just convert-video.",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    subparsers = root.add_subparsers(
        dest="command", required=True, parser_class=argparse.ArgumentParser
    )

    def command(name: str) -> argparse.ArgumentParser:
        return subparsers.add_parser(name, allow_abbrev=False)

    launch_parser = command("launch")
    launch_parser.add_argument("--checkout", type=Path, required=True)
    launch_parser.add_argument("--evidence-root", type=Path)
    doctor_parser = command("doctor")
    doctor_parser.add_argument("--manifest", type=Path, required=True)
    drive_parser = command("drive")
    drive_parser.add_argument("--manifest", type=Path, required=True)
    drive_parser.add_argument("--feature", choices=("all", *FEATURES), default="all")
    evidence_parser = command("evidence")
    evidence_parser.add_argument("--manifest", type=Path, required=True)
    cleanup_parser = command("cleanup")
    cleanup_parser.add_argument("--manifest", type=Path, required=True)
    run_parser = command("run")
    run_parser.add_argument("--checkout", type=Path, required=True)
    run_parser.add_argument("--evidence-root", type=Path)
    run_parser.add_argument("--feature", choices=("all", *FEATURES), default="all")
    return root


def require_passed(
    checks: Sequence[Mapping[str, object]],
    missing: Sequence[str] = (),
    manifest_path: Path | None = None,
) -> None:
    """Fail with one error per check that did not pass and per missing evidence
    file; -v prints every check with its expected and observed values."""
    errors: list[str] = []
    for item in checks:
        expected = json.dumps(item.get("expected"), default=str)
        observed = json.dumps(item.get("observed"), default=str)
        line = f"{item.get('id')} {item.get('status')}: {item.get('summary')}"
        log.info("%s; expected %s; observed %s", line, expected, observed)
        if item.get("status") != "passed":
            # The summary names what the check wants, so the observed value says why
            errors.append(
                f"{line}; expected {expected[:200]}, observed {observed[:200]}"
            )
    errors += [
        f"{item} is missing or changed in the evidence bundle" for item in missing
    ]
    if errors:
        report = {"file": str(manifest_path)} if manifest_path else None
        raise ScriptError(*errors, report=report)


def verify(args: argparse.Namespace) -> dict[str, object]:
    """Run one command; the manifest holds every check, the answer the verdict."""
    if args.command == "launch":
        return {"file": str(launch(args.checkout, args.evidence_root))}
    if args.command == "doctor":
        require_passed([asdict(item) for item in doctor(args.manifest)])
    elif args.command == "drive":
        drive(args.manifest, args.feature)
        require_passed(all_checks(load_manifest(args.manifest)))
    elif args.command == "evidence":
        summary = evidence(args.manifest)
        require_passed(
            all_checks(load_manifest(args.manifest)),
            cast(list[str], summary["evidence_missing"]),
        )
    elif args.command == "cleanup":
        result = cleanup(args.manifest)
        if result["status"] == "removed":
            return {"changes": [["remove", result["run_root"]]]}
    else:
        manifest_path, summary = run_all(
            args.checkout, args.evidence_root, args.feature
        )
        require_passed(
            all_checks(load_manifest(manifest_path)),
            cast(list[str], summary["evidence_missing"]),
            manifest_path,
        )
        return {"file": str(manifest_path)}
    return {}


def work(args: argparse.Namespace) -> dict[str, object]:
    try:
        return verify(args)
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        raise ScriptError(str(error)) from error


def main(argv: Sequence[str] | None = None) -> int:
    return run_script(parser(), work, argv, debug="VERIFY_VIDEO_ARCHIVE_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

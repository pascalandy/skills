"""Shared entry point for scripts/ CLIs, built on the contract in _cli.py."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import shlex
import sys
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from _cli import (
    INTERRUPTED,
    ScriptError,
    TemporaryError,
    UsageError,
    env_flag,
    signals_interrupt,
    wants_help,
)

log = logging.getLogger(__name__)


def swap(fresh: Path, destination: Path, previous: Path) -> None:
    """Replace a directory and restore the old one if interrupted mid-swap."""
    try:
        if destination.exists():
            destination.rename(previous)
        fresh.rename(destination)
    except BaseException:
        if previous.exists() and not destination.exists():
            previous.rename(destination)
        raise


@contextmanager
def exclusive(path: Path) -> Iterator[None]:
    """Hold the lock at `path` for the block, waiting for any other holder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def run_script(
    parser: argparse.ArgumentParser,
    work: Callable[[argparse.Namespace], str],
    argv: Sequence[str] | None = None,
    *,
    debug: str | None = None,
) -> int:
    """Parse arguments, run `work`, and turn its outcome into output and an exit code.

    `work` returns what stdout holds on success, or "" for nothing, and raises
    ScriptError, UsageError, or TemporaryError for expected failures. A failure
    leaves stdout empty. `debug` names the script's <NAME>_DEBUG variable and
    adds --debug; without it the script never prints a traceback. Call it from
    `main()` and pass the result to `SystemExit`.
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
    if wants_help(argv):
        parser.print_help()
        return 0

    with signals_interrupt():
        try:
            args = parser.parse_args(argv)
        except SystemExit as stop:
            return stop.code if isinstance(stop.code, int) else 1
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
        command = shlex.join([*parser.prog.split(), *argv])
        try:
            output = work(args)
            if output:
                print(output)
            return 0
        except KeyboardInterrupt as stop:
            code = getattr(stop, "code", INTERRUPTED)
            print(
                "interrupted" if code == INTERRUPTED else "terminated", file=sys.stderr
            )
            return code
        except ScriptError as error:
            report(error, parser, getattr(args, "json", False), command)
            return error.code
        except Exception as error:
            unexpected = ScriptError(f"{type(error).__name__}: {error}")
            report(unexpected, parser, getattr(args, "json", False), command)
            log.debug("unexpected failure", exc_info=True)
            if debug and not tracing:
                print(f"rerun: {command} --debug", file=sys.stderr)
            return 1


def report(
    error: ScriptError, parser: argparse.ArgumentParser, as_json: bool, command: str
) -> None:
    """Print a failure on stderr: one JSON object under --json, else error lines."""
    messages = [str(message) for message in error.args]
    if as_json:
        print(
            json.dumps({**error.report, "errors": messages}, indent=2), file=sys.stderr
        )
        return
    if error.detail:
        print(error.detail, file=sys.stderr)
    if isinstance(error, UsageError):
        parser.print_usage(sys.stderr)
    for message in messages:
        print(f"error: {message}", file=sys.stderr)
    if isinstance(error, UsageError):
        print(f"run '{parser.prog} --help'", file=sys.stderr)
    elif isinstance(error, TemporaryError) and messages:
        print(f"retry: {command}", file=sys.stderr)

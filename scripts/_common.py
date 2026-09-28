"""Shared entry point for scripts/ CLIs, built on the contract in _cli.py."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

from _cli import (
    INTERRUPTED,
    Parser,
    ScriptError,
    TemporaryError,
    UsageError,
    env_flag,
    given,
    signals_interrupt,
)

log = logging.getLogger(__name__)

# git's messages when the network, not the repository or its credentials, failed
NETWORK_FAILURE = re.compile(
    r"could not resolve (host|hostname)"
    r"|failed to connect"
    r"|connection (refused|timed out|reset|closed)"
    r"|operation timed out"
    r"|network is unreachable"
    r"|no route to host"
    r"|host is down"
    r"|temporary failure in name resolution"
    r"|the remote end hung up unexpectedly"
    r"|early eof"
    r"|returned error: (429|5\d\d)",
    re.IGNORECASE,
)


def is_network_failure(message: str) -> bool:
    """Whether git's error names a network failure that a later retry may fix."""
    return NETWORK_FAILURE.search(message) is not None


# How long a child may clean up after SIGTERM before SIGKILL
GRACE = 10.0


def run(
    command: Sequence[str],
    *,
    input: str | None = None,
    timeout: float | None = None,
    **options: Any,
) -> subprocess.CompletedProcess[Any]:
    """subprocess.run that stops its child gently.

    On a timeout or an interrupt, the child gets SIGTERM, so it can remove its
    lock files and stop its own children, and SIGKILL only after GRACE seconds.
    Pass stdout and stderr as for Popen.
    """
    if input is not None:
        options["stdin"] = subprocess.PIPE
    with subprocess.Popen(command, **options) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except BaseException:
            stop(process)
            raise
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def send(process: subprocess.Popen[Any], number: int, group: bool = False) -> None:
    """Signal a child, or with `group` the process group of a child started in
    its own session; the group outlives a leader that exits first."""
    with suppress(ProcessLookupError):
        if group:
            os.killpg(process.pid, number)
        else:
            process.send_signal(number)


def stop(process: subprocess.Popen[Any], group: bool = False) -> None:
    """SIGTERM a child, then SIGKILL it after GRACE seconds. A descendant may
    still hold the pipes, so stop reading them GRACE seconds later."""
    send(process, signal.SIGTERM, group)
    try:
        process.communicate(timeout=GRACE)
        return
    except subprocess.TimeoutExpired:
        send(process, signal.SIGKILL, group)
    with suppress(subprocess.TimeoutExpired):
        process.communicate(timeout=GRACE)


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
def exclusive(path: Path, timeout: float) -> Iterator[None]:
    """Hold the lock at `path` for the block, waiting up to `timeout` seconds
    for another holder; raise TemporaryError when the wait runs out."""
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    with path.open("w") as handle:
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TemporaryError(
                        f"another run still holds {path} after {timeout:g}s"
                    ) from None
                time.sleep(0.1)
        yield


def run_script(
    parser: Parser,
    work: Callable[[argparse.Namespace], str],
    argv: Sequence[str] | None = None,
    *,
    debug: str | None = None,
) -> int:
    """Parse arguments, run `work`, and turn its outcome into output and an exit code.

    `work` returns what stdout holds on success, or "" for nothing, and raises
    ScriptError, UsageError, or TemporaryError for expected failures. A failure
    leaves stdout empty; under --json, it is one JSON object on stderr. `debug`
    names the script's <NAME>_DEBUG variable and adds --debug; without it the
    script never prints a traceback. Call it from `main()` and pass the result
    to `SystemExit`.
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
    if given(argv, "-h", "--help"):
        parser.print_help()
        return 0

    # Known before parsing, so even a usage error or an interrupt is JSON
    as_json = "--json" in parser._option_string_actions and given(argv, "--json")
    parser.json_errors = as_json
    command = shlex.join([*parser.prog.split(), *argv])
    tracing = False
    with signals_interrupt():
        try:
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
            output = work(args)
            if output:
                print(output)
            return 0
        except KeyboardInterrupt as stop:
            code = getattr(stop, "code", INTERRUPTED)
            word = "interrupted" if code == INTERRUPTED else "terminated"
            print(json.dumps({"errors": [word]}) if as_json else word, file=sys.stderr)
            return code
        except ScriptError as error:
            return report(error, parser, as_json, command)
        except Exception as error:
            # The traceback comes first, so the error, or its JSON object, ends stderr
            log.debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(f"{type(error).__name__}: {error}")
            return report(
                unexpected, parser, as_json, command, rerun=bool(debug) and not tracing
            )


def report(
    error: ScriptError,
    parser: Parser,
    as_json: bool,
    command: str,
    rerun: bool = False,
) -> int:
    """Print a failure on stderr, one JSON object under --json, and return its
    exit code. Hints name the command to run next: help for a usage error,
    retry for a temporary failure, and rerun with --debug for a bug."""
    messages = [str(message) for message in error.args]
    hints: dict[str, str] = {}
    if isinstance(error, UsageError):
        hints["help"] = f"{parser.prog} --help"
    elif isinstance(error, TemporaryError) and messages:
        hints["retry"] = command
    elif rerun:
        hints["rerun"] = f"{command} --debug"
    if as_json:
        failure = {**error.report, "errors": messages, **hints}
        print(json.dumps(failure, indent=2), file=sys.stderr)
        return error.code
    if error.detail:
        print(error.detail, file=sys.stderr)
    if isinstance(error, UsageError):
        parser.print_usage(sys.stderr)
    for message in messages:
        print(f"error: {message}", file=sys.stderr)
    for name, hint in hints.items():
        print(f"run '{hint}'" if name == "help" else f"{name}: {hint}", file=sys.stderr)
    return error.code

"""Shared entry point for scripts/ CLIs, built on the contract in _cli.py."""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any, NoReturn

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

# git's and gh's messages when the network, not the repository or its
# credentials, failed
NETWORK_FAILURE = re.compile(
    r"could not resolve (host|hostname)"
    r"|failed to connect"
    r"|connection (refused|timed out|reset|closed)"
    r"|operation timed out"
    r"|network is unreachable"
    r"|no route to host"
    r"|host is down"
    r"|temporary failure in name resolution"
    r"|closed by remote host"
    r"|broken pipe"
    r"|the remote end hung up unexpectedly"
    r"|early eof"
    r"|(?:returned error: |HTTP )(429|5\d\d)\b"
    r"|error connecting to",
    re.IGNORECASE,
)


def is_network_failure(message: str) -> bool:
    """Whether a git or gh error names a network failure that a later retry may fix."""
    return NETWORK_FAILURE.search(message) is not None


# A SKILL.md or command file's header
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


def unquote(value: str) -> str:
    """Read a one-line YAML scalar; a block scalar or broken quoting reads as empty."""
    if value.startswith('"'):
        try:
            return json.loads(value)
        except ValueError:
            return ""
    if value.startswith("'"):
        return value[1:-1].replace("''", "'") if value.endswith("'") else ""
    return "" if value.startswith(("|", ">")) else value


def frontmatter_value(text: str, key: str) -> str | None:
    """A top-level key's one-line value in a file's frontmatter, or None when the
    key is absent."""
    header = FRONTMATTER.match(text)
    pattern = rf"^{re.escape(key)}:[ \t]*(.*?)[ \t]*$"
    found = re.search(pattern, header.group(1), re.MULTILINE) if header else None
    return unquote(found.group(1)) if found else None


def frontmatter_description(text: str) -> str:
    """The description in a file's frontmatter, or "" when it has none."""
    return frontmatter_value(text, "description") or ""


KINDS = ("general", "dev")
UNKNOWN = "unknown"


def kind_of(text: str) -> str:
    """A SKILL.md's kind; a missing or unrecognized kind reads as UNKNOWN."""
    kind = frontmatter_value(text, "kind")
    return kind if kind in KINDS else UNKNOWN


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


def run_git(
    *args: str,
    cwd: Path,
    timeout: float | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run git in `cwd` and return its text output; a timeout is temporary."""
    if shutil.which("git") is None:
        raise ScriptError("git not found on PATH; install git and rerun")
    log.debug("git %s", shlex.join(args))
    try:
        return run(
            ["git", *args],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise TemporaryError(f"git {args[0]} took longer than {timeout:g}s") from None


def main_checkout(root: Path) -> Path:
    """The repository's first working tree, which its worktrees share; `root` when
    git cannot list the working trees."""
    if shutil.which("git") is None:
        return root
    listed = run_git("worktree", "list", "--porcelain", cwd=root)
    first = listed.stdout.partition("\n")[0]
    if listed.returncode or not first.startswith("worktree "):
        return root
    return Path(first.removeprefix("worktree ")).resolve()


def send(process: subprocess.Popen[Any], number: int, group: bool = False) -> None:
    """Signal a child, or with `group` the process group of a child started in
    its own session; the group outlives a leader that exits first. On macOS,
    killpg fails with EPERM when the group holds only an unreaped leader."""
    with suppress(ProcessLookupError, PermissionError):
        if group:
            os.killpg(process.pid, number)
        else:
            process.send_signal(number)


def stop(process: subprocess.Popen[Any], group: bool = False) -> None:
    """SIGTERM a child, then SIGKILL it after GRACE seconds. A descendant may
    still hold the pipes, so stop reading and close them GRACE seconds later."""
    send(process, signal.SIGTERM, group)
    try:
        process.communicate(timeout=GRACE)
        return
    except subprocess.TimeoutExpired:
        send(process, signal.SIGKILL, group)
    try:
        process.communicate(timeout=GRACE)
    except subprocess.TimeoutExpired:
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe is not None:
                pipe.close()


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


def answer(code: int, fields: Mapping[str, Any]) -> int:
    """Print the one JSON line a script answers with, and return `code`.

    `ok` comes first and is true exactly when `code` is 0, whatever `fields`
    says. Success goes to stdout; a failure goes to stderr, after its
    diagnostics, and leaves stdout empty.
    """
    body = {"ok": code == 0, **fields}
    body["ok"] = code == 0
    line = json.dumps(body, separators=(",", ":"))
    print(line, file=sys.stderr if code else sys.stdout)
    return code


# What a script older than #490 printed for each change: an action, a tab, and
# its object. A machine mid-deploy may still run one; #492 stops reading it
CHANGE_LINE = re.compile(r"(clone|commit|pull|push|add|update|remove|synced|ready)\t")


def parsed_answer(line: str) -> dict[str, Any] | None:
    """The JSON answer a line holds, whatever its key order, or None."""
    if line.startswith("{"):
        with suppress(ValueError):
            found = json.loads(line)
            if isinstance(found, dict) and isinstance(found.get("ok"), bool):
                return found
    return None


def answer_in(lines: Iterable[str]) -> dict[str, Any] | None:
    """The last JSON answer among a child's output lines, such as {"ok":true}."""
    for line in reversed(list(lines)):
        if (found := parsed_answer(line)) is not None:
            return found
    return None


def changes_in(lines: Iterable[str]) -> list[list[str]]:
    """The changes a child reports: the `changes` of each JSON answer it prints,
    or each change line of a script older than #490."""
    found: list[list[str]] = []
    for line in lines:
        if (answer := parsed_answer(line)) is not None:
            found += answer.get("changes", [])
        elif CHANGE_LINE.match(line):
            found.append(line.split("\t"))
    return found


def replay(output: str) -> None:
    """Forward a child's output to stderr with its last line ended, so the
    answer printed after it stays a line of its own."""
    if output:
        sys.stderr.write(output if output.endswith("\n") else f"{output}\n")


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
    # raising sends this one through report()
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
            return report(error, parser, command)
        except Exception as error:
            # The traceback comes first, so the answer ends stderr
            log.debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(f"{type(error).__name__}: {error}")
            return report(
                unexpected, parser, command, rerun=bool(debug) and not tracing
            )


def report(
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

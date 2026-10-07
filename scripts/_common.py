"""Shared helpers for scripts/ CLIs."""

from __future__ import annotations

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
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

from _cli import ScriptError, TemporaryError

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


def keep_changes(error: BaseException, changes: list[list[str]]) -> None:
    """List the changes a run already made ahead of those its error reports, so
    its answer keeps them whatever stopped it: a failure, an interrupt, or a bug.
    run_script() answers the `report` of any exception."""
    if not changes:
        return
    report = getattr(error, "report", None)
    if not isinstance(report, dict):
        report = {}
        error.report = report  # pyright: ignore[reportAttributeAccessIssue]
    report["changes"] = [*changes, *report.get("changes", [])]


@contextmanager
def receipt(changes: list[list[str]]) -> Iterator[None]:
    """Run a block that appends each change to `changes` as it happens, and
    keep them in the answer when the block stops early."""
    try:
        yield
    except BaseException as error:
        keep_changes(error, changes)
        raise


def replay(output: str) -> None:
    """Forward a child's output to stderr with its last line ended, so the
    answer printed after it stays a line of its own."""
    if output:
        sys.stderr.write(output if output.endswith("\n") else f"{output}\n")

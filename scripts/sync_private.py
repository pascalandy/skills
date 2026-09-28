#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Save, pull, and push the private skills repository cloned at _skills_private/.

The private repository's URL is this checkout's origin with skills renamed to
skills-private, and the public .gitignore keeps the clone out of the public
repository. A missing clone is cloned. Uncommitted edits are committed and
pushed, so no machine loses them. A folder that is not a clone or a clone off
main stops the run untouched; edits that conflict with GitHub stay committed
here and stop the run.
"""

from __future__ import annotations

import logging
import re
import socket
import subprocess
from pathlib import Path

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes
from _common import exclusive, is_network_failure, run_git, run_script

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "_skills_private"
LABEL = "_skills_private"
TIMEOUT = 300.0
EPILOG = """\
Each run prints one line per change: clone, commit, pull, or push, a tab,
_skills_private, a tab, and a detail. A dry run skips the network, so it
lists only the clone or commit a run would make.

examples:
  uv run scripts/sync_private.py
  uv run scripts/sync_private.py --dry-run
  uv run scripts/sync_private.py --timeout 30s"""
EXIT_CODES = exit_codes(
    {
        0: "the clone is saved and current, or nothing needed doing",
        1: "the folder needs you: not a clone, off main, or conflicting edits",
        75: "the network failed, or another sync held the lock; retry",
    }
)
log = logging.getLogger("sync-private")


def git(
    *args: str, cwd: Path = PRIVATE, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    return run_git(*args, cwd=cwd, timeout=timeout)


def last_line(result: subprocess.CompletedProcess[str]) -> str:
    lines = (result.stderr + result.stdout).strip().splitlines()
    return lines[-1] if lines else f"git exited {result.returncode}"


def failed(
    what: str, result: subprocess.CompletedProcess[str], fix: str
) -> ScriptError:
    """The error for a failed network step: temporary when the network failed."""
    reason = last_line(result)
    if is_network_failure(result.stderr):
        return TemporaryError(f"{what}: {reason}")
    return ScriptError(f"{what}: {reason}; {fix}")


def private_url() -> str:
    origin = git("remote", "get-url", "origin", cwd=ROOT).stdout.strip()
    url, found = re.subn(r"(?<=[/:])skills(\.git)?/?$", r"skills-private\1", origin)
    if not found:
        raise ScriptError(
            f"origin {origin or '(none)'} does not end in skills, so the private "
            "repository's URL is unknown; point it at the skills repository with "
            "git remote set-url origin <url>, then rerun"
        )
    return url


def is_clone() -> bool:
    return not PRIVATE.is_symlink() and (PRIVATE / ".git").is_dir()


def state() -> tuple[str, str]:
    """The clone's HEAD and one of clean, dirty, missing, or plain."""
    if not PRIVATE.exists() and not PRIVATE.is_symlink():
        return "-", "missing"
    if not is_clone():
        return "-", "plain"
    head = git("rev-parse", "-q", "--verify", "HEAD").stdout.strip() or "-"
    dirty = bool(git("status", "--porcelain").stdout.strip())
    return head, "dirty" if dirty else "clean"


def github_head(timeout: float = TIMEOUT) -> str:
    """The private repository's main on GitHub, which every machine should match."""
    if not is_clone():
        raise ScriptError(f"{PRIVATE} is not a clone of the private repository")
    listed = git("ls-remote", "--quiet", "origin", "refs/heads/main", timeout=timeout)
    if listed.returncode or not listed.stdout.strip():
        raise failed(
            "could not read the private repository",
            listed,
            f"check the origin remote in {PRIVATE}",
        )
    return listed.stdout.split()[0]


def sync(dry_run: bool = False, timeout: float = TIMEOUT) -> list[str]:
    """Clone, save, pull, and push; return one line per change. Runs from one
    repository take turns, each waiting up to `timeout` seconds."""
    if dry_run:
        return save_and_pull(dry_run=True, timeout=timeout)
    common = git("rev-parse", "--git-common-dir", cwd=ROOT).stdout.strip()
    with exclusive(ROOT / common / "sync-private.lock", timeout):
        return save_and_pull(dry_run=False, timeout=timeout)


def save_and_pull(dry_run: bool, timeout: float) -> list[str]:
    host = socket.gethostname().split(".")[0]
    _, status = state()
    if status == "missing":
        url = private_url()
        if not dry_run:
            log.info("clone %s", url)
            cloned = git(
                "clone", "--quiet", url, str(PRIVATE), cwd=ROOT, timeout=timeout
            )
            if cloned.returncode:
                raise failed(
                    f"could not clone {url}",
                    cloned,
                    "check that the private repository exists and you can read it",
                )
        return [f"clone\t{LABEL}\t{url}"]
    if status == "plain":
        raise ScriptError(
            f"{PRIVATE} is not a clone of the private repository; move it aside, "
            "then rerun to clone it"
        )
    branch = git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    if branch != "main":
        raise ScriptError(
            f"{PRIVATE} is on {branch or 'a detached HEAD'}; switch it to main, then rerun"
        )
    changes = [f"commit\t{LABEL}\tsave edits from {host}"] if status == "dirty" else []
    if dry_run:
        return changes
    if status == "dirty":
        for step in (
            ("add", "--all"),
            ("commit", "--quiet", "-m", f"🧰 skill: private: save edits from {host}"),
        ):
            done = git(*step)
            if done.returncode:
                raise ScriptError(
                    f"could not commit private edits: {last_line(done)}; see why with "
                    f"git -C {PRIVATE} commit, then rerun uv run scripts/sync_private.py"
                )
    before = git("rev-parse", "HEAD").stdout.strip()
    log.info("pull %s", LABEL)
    pulled = git("pull", "--rebase", "--quiet", timeout=timeout)
    if pulled.returncode:
        rebasing = any(
            (PRIVATE / git("rev-parse", "--git-path", part).stdout.strip()).exists()
            for part in ("rebase-merge", "rebase-apply")
        )
        if rebasing:
            git("rebase", "--abort")
            raise ScriptError(
                f"private edits on {host} conflict with GitHub; resolve them with "
                f"git pull --rebase in {PRIVATE}, then rerun"
            )
        raise failed(
            "could not pull the private repository",
            pulled,
            f"fix the clone at {PRIVATE}, then rerun",
        )
    after = git("rev-parse", "HEAD").stdout.strip()
    if after != before:
        changes.append(f"pull\t{LABEL}\t{before[:7]}..{after[:7]}")
    ahead = git("rev-list", "--count", "@{upstream}..HEAD").stdout.strip()
    if ahead not in ("", "0"):
        log.info("push %s", LABEL)
        pushed = git("push", "--quiet", timeout=timeout)
        if pushed.returncode:
            raise failed(
                f"could not push private edits from {host}",
                pushed,
                f"fix the clone at {PRIVATE}, then rerun",
            )
        changes.append(f"push\t{LABEL}\t{ahead} commit{'s' if ahead != '1' else ''}")
    log.debug("private repository at %s", after)
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="scripts/sync_private.py",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print the clone or commit a run would make without changing anything",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="5m",
        help="how long to wait for another sync, and for each clone, pull, or push (default: 5m)",
    )
    return run_script(
        parser,
        lambda args: "\n".join(sync(args.dry_run, args.timeout)),
        argv,
        debug="SYNC_PRIVATE_DEBUG",
    )


if __name__ == "__main__":
    raise SystemExit(main())

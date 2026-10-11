#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Clone or pull the private skills repository at skills-private/, beside the checkout.

The private repository's URL is this checkout's origin with skills renamed to
skills-private. A missing clone is cloned; a current one fast-forwards to
GitHub's main. Private skills change through a worktree of skills-private and
a PR, never in this clone, so a folder that is not a clone, a clone off main,
one with uncommitted edits, or one with commits GitHub lacks stops the run
untouched.
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes, run_script
from _common import exclusive, is_network_failure, main_checkout, run_git

ROOT = Path(__file__).resolve().parent.parent
# One clone per machine, next to the main checkout, which every worktree shares
PRIVATE = main_checkout(ROOT).parent / "skills-private"
# Every reader takes private packages from this folder of a private root. The
# sync still carries the whole clone, skill_archived/ included, which never installs
PACKAGES = "authoring"
LABEL = "skills-private"
TIMEOUT = 300.0
EPILOG = """\
A run answers {"ok":true,"changes":[...]}, one [action, skills-private,
detail] per change, where the action is clone or pull, and {"ok":true} when
nothing changes. A dry run skips the network, so it lists only the clone a run
would make.

examples:
  uv run scripts/sync_private.py
  uv run scripts/sync_private.py --dry-run
  uv run scripts/sync_private.py --timeout 30s"""
EXIT_CODES = exit_codes(
    {
        0: "the clone is current, or nothing needed doing",
        1: "the folder needs you: not a clone, off main, edited, or diverged",
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


def sync(dry_run: bool = False, timeout: float = TIMEOUT) -> list[list[str]]:
    """Clone or pull; return one [action, LABEL, detail] per change. Runs from one
    repository take turns, each waiting up to `timeout` seconds."""
    if dry_run:
        return clone_or_pull(dry_run=True, timeout=timeout)
    common = git("rev-parse", "--git-common-dir", cwd=ROOT).stdout.strip()
    with exclusive(ROOT / common / "sync-private.lock", timeout):
        return clone_or_pull(dry_run=False, timeout=timeout)


def clone_or_pull(dry_run: bool, timeout: float) -> list[list[str]]:
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
        return [["clone", LABEL, url]]
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
    if status == "dirty":
        raise ScriptError(
            f"{PRIVATE} has uncommitted edits; move them to a worktree of "
            "skills-private and open a PR, then rerun"
        )
    if dry_run:
        # Without the network, a dry run compares with the last fetch, which a
        # stale or missing origin/main makes refuse
        refuse_commits_beyond("origin/main", "its origin/main")
        return []
    before = git("rev-parse", "HEAD").stdout.strip()
    log.info("pull %s", LABEL)
    fetched = git("fetch", "--quiet", "origin", "main", timeout=timeout)
    if fetched.returncode:
        raise failed(
            "could not fetch the private repository",
            fetched,
            f"check the origin remote in {PRIVATE}",
        )
    refuse_commits_beyond("FETCH_HEAD", "GitHub's main")
    merged = git("merge", "--quiet", "--ff-only", "FETCH_HEAD")
    if merged.returncode:
        raise ScriptError(
            f"could not fast-forward {PRIVATE}: {last_line(merged)}; fix the clone, "
            "then rerun"
        )
    after = git("rev-parse", "HEAD").stdout.strip()
    log.debug("private repository at %s", after)
    return [["pull", LABEL, f"{before[:7]}..{after[:7]}"]] if after != before else []


def refuse_commits_beyond(ref: str, name: str) -> None:
    """Stop when main holds commits `ref` lacks, since only a merged PR changes it,
    or when the comparison fails."""
    counted = git("rev-list", "--count", f"{ref}..HEAD")
    ahead = counted.stdout.strip()
    if counted.returncode or not ahead.isdigit():
        raise ScriptError(
            f"{PRIVATE} cannot compare with {name}; fetch it with "
            f"git -C {PRIVATE} fetch origin main, then rerun"
        )
    if ahead != "0":
        raise ScriptError(
            f"{PRIVATE} has {ahead} commit{'s' if ahead != '1' else ''} {name} "
            "lacks; open a PR from a worktree of skills-private, then reset main to "
            "origin/main and rerun"
        )


def work(args: argparse.Namespace) -> dict[str, Any]:
    changes = sync(args.dry_run, args.timeout)
    return {"changes": changes} if changes else {}


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
        help="print the clone a run would make without changing anything",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="5m",
        help="how long to wait for another sync, and for each clone or fetch (default: 5m)",
    )
    return run_script(parser, work, argv, debug="SYNC_PRIVATE_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

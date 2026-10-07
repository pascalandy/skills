#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sync this machine: pull main, save and pull the private clone, then install.

It refuses a checkout off main and reaches only this machine; just sync-fleet
reaches the others. --dry-run and --check skip the pulls and preview the
current checkout.
"""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes, run_script
from _common import (
    answer_in,
    changes_in,
    is_network_failure,
    receipt,
    replay,
    run,
    run_git,
)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
EPILOG = """\
A run answers {"ok":true,"changes":[...]}: ["pull","main","OLD..NEW"] when
main moved, then the changes of scripts/sync_private.py and just
install-skills; {"ok":true} when nothing changed. When a step fails, its own
answer comes just before this one.

examples:
  just sync             # pull, save and pull the private clone, then install
  just sync --dry-run   # preview the install without pulling
  just sync --check     # exit 1 if this machine's skills differ from the checkout"""
EXIT_CODES = exit_codes(
    {
        0: "this machine is synced, or nothing needed doing",
        1: "a step failed: a checkout off main, a pull that cannot fast-forward, "
        "or an install conflict",
        75: "the network failed, or another sync or install held its lock; retry",
    }
)
log = logging.getLogger("sync")


def git(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    # Hooks stay off: just sync is this machine only; just sync-fleet reaches
    # the others
    env = os.environ | {"LEFTHOOK": "0"}
    return run_git(*args, cwd=ROOT, timeout=timeout, env=env)


def pull_main(timeout: float) -> list[list[str]]:
    """Fast-forward main to its upstream; return the change when it moved."""
    branch = git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    if branch != "main":
        raise ScriptError(
            f"this checkout is on {branch or 'a detached HEAD'}; "
            "switch to main, then rerun just sync"
        )
    log.info("fetch main")
    fetched = git("fetch", "--quiet", timeout=timeout)
    if fetched.returncode:
        reason = fetched.stderr.strip()
        if is_network_failure(reason):
            raise TemporaryError(f"could not fetch main: {reason}")
        raise ScriptError(
            f"could not fetch main: {reason}; fix origin, then rerun just sync"
        )
    before = git("rev-parse", "HEAD").stdout.strip()
    merged = git("merge", "--quiet", "--ff-only", "@{upstream}")
    if merged.returncode:
        raise ScriptError(
            "main cannot fast-forward to its upstream; commit, stash, or push the "
            "local changes git names above, then rerun just sync",
            detail=(merged.stderr + merged.stdout).strip(),
        )
    after = git("rev-parse", "HEAD").stdout.strip()
    return [["pull", "main", f"{before[:7]}..{after[:7]}"]] if after != before else []


def step(name: str, *command: str) -> list[list[str]]:
    """Run one step as its own process, so it runs the code the pull brought.

    Its stderr is replayed once it ends; the changes its answer lists are
    returned, or carried by the error when it fails.
    """
    log.info("run %s", name)
    log.debug("%s", shlex.join(command))
    # An interrupt passes SIGTERM on to the step, so it cleans up too
    finished = run(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    replay(finished.stderr)
    # A failed step, such as a private pull that conflicts after the edits were
    # committed, still answers what it changed
    failed = answer_in(finished.stderr.splitlines()) or {}
    report = {"changes": failed["changes"]} if failed.get("changes") else None
    if finished.returncode == 75:
        raise TemporaryError(f"{name} could not finish", report=report)
    if finished.returncode < 0:
        raise ScriptError(f"{name} was killed by signal {-finished.returncode}")
    if finished.returncode:
        raise ScriptError(
            f"{name} failed; fix what its answer above says, then rerun just sync",
            report=report,
        )
    return changes_in(finished.stdout.splitlines())


def sync(args: argparse.Namespace) -> dict[str, Any]:
    levels = [
        *(["--verbose"] if args.verbose else []),
        *(["--debug"] if log.isEnabledFor(logging.DEBUG) else []),
        "--timeout",
        f"{args.timeout:g}",
    ]
    changes: list[list[str]] = []
    # A failed step, an interrupt, or a bug still answers what the steps
    # before it changed
    with receipt(changes):
        if args.dry_run or args.check:
            flags = ["--dry-run" if args.dry_run else "--check"]
        else:
            changes += pull_main(args.timeout)
            changes += step(
                "scripts/sync_private.py",
                sys.executable,
                str(SCRIPTS / "sync_private.py"),
                *levels,
            )
            flags = []
        changes += step(
            "just install-skills",
            sys.executable,
            str(SCRIPTS / "install_skills.py"),
            *flags,
            *levels,
        )
    return {"changes": changes} if changes else {}


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just sync",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="skip the pulls and print the changes an install would make",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="skip the pulls; exit 1 if any installed skill differs from the checkout",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="5m",
        help="how long each network step or lock may take (default: 5m)",
    )
    return run_script(parser, sync, argv, debug="SYNC_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

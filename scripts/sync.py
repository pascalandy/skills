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
import os
import subprocess
import sys
from pathlib import Path

from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def step(*command: str, **env: str) -> None:
    """Run one step in its own process, printing its own output. A failure ends
    this run with the step's exit code, as the old recipe's set -e did."""
    finished = subprocess.run(command, cwd=ROOT, env=os.environ | env, check=False)
    if finished.returncode:
        raise SystemExit(finished.returncode)


def pull_main() -> None:
    branch = subprocess.run(
        ["git", "symbolic-ref", "--short", "-q", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if branch != "main":
        raise ScriptError(
            f"this checkout is on {branch or 'a detached HEAD'}; "
            "switch to main, then rerun just sync"
        )
    # Hooks stay off: just sync is this machine only; just sync-fleet reaches the others
    step("git", "pull", "--quiet", "--ff-only", LEFTHOOK="0")


def sync(args: argparse.Namespace) -> str:
    verbose = ["--verbose"] if args.verbose else []
    if args.dry_run or args.check:
        flags = ["--dry-run" if args.dry_run else "--check"]
    else:
        pull_main()
        # Later steps start new processes, so they run the code the pull brought
        step(sys.executable, str(SCRIPTS / "sync_private.py"), *verbose)
        flags = []
    # The installer is the last step, so its report and exit code are this run's
    installer = [sys.executable, str(SCRIPTS / "install_skills.py"), *flags, *verbose]
    os.execv(sys.executable, installer)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  just sync             # silent on success
  just sync --dry-run   # preview the install without pulling
  just sync --check     # exit 1 if this machine's skills differ from the checkout""",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="skip the pulls and preview the install without writing",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="skip the pulls; exit 1 if any installed skill differs from the checkout",
    )
    return run_script(parser, sync, argv)


if __name__ == "__main__":
    raise SystemExit(main())

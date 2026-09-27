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

import sync_private
from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "scripts" / "install_skills.py"


def pull() -> None:
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
    pulled = subprocess.run(
        ["git", "pull", "--quiet", "--ff-only"],
        cwd=ROOT,
        env={**os.environ, "LEFTHOOK": "0"},
        capture_output=True,
        text=True,
        check=False,
    )
    if pulled.returncode:
        raise ScriptError(f"could not pull main: {sync_private.last_line(pulled)}")


def sync(args: argparse.Namespace) -> str:
    if args.dry_run:
        flags = ["--dry-run"]
    elif args.check:
        flags = ["--check"]
    else:
        pull()
        sync_private.sync()
        flags = ["--quiet"]
    if args.verbose:
        flags.append("--verbose")
    # The installer is the last step, so its report and exit code are this run's
    os.execv(sys.executable, [sys.executable, str(INSTALLER), *flags])


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

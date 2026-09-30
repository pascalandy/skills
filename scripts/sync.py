#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sync this machine from GitHub's published main without moving the author checkout."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes
from _common import is_network_failure, run, run_git, run_script
from _published_checkout import author_root, published

ROOT = Path(__file__).resolve().parent.parent
EXIT_CODES = exit_codes(
    {
        0: "synced or current",
        1: "configuration or install failed",
        75: "network or lock temporary failure",
    }
)
EPILOG = """\
examples:
  just sync
  just sync --dry-run
  just sync --check"""
log = logging.getLogger("sync")


def github(root: Path, timeout: float) -> str:
    fetched = run_git("fetch", "--quiet", "origin", "main", cwd=root, timeout=timeout)
    if (
        fetched.returncode
        and "cannot lock ref 'refs/remotes/origin/main'" in fetched.stderr
    ):
        fetched = run_git(
            "fetch", "--quiet", "origin", "main", cwd=root, timeout=timeout
        )
    if fetched.returncode:
        if not (
            is_network_failure(fetched.stderr)
            or "cannot lock ref 'refs/remotes/origin/main'" in fetched.stderr
        ):
            raise ScriptError(
                f"could not fetch main: {fetched.stderr.strip()}; fix origin, then rerun just sync"
            )
        log.warning("warning: GitHub unavailable; using last fetched main")
    resolved = run_git(
        "rev-parse", "-q", "--verify", "refs/remotes/origin/main^{commit}", cwd=root
    )
    if not resolved.stdout.strip():
        raise TemporaryError(
            "GitHub's main is unknown here; reconnect and rerun just sync"
        )
    return resolved.stdout.strip()


def step(*command: str, cwd: Path) -> list[str]:
    result = run(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode:
        error = (result.stderr or result.stdout).strip().removeprefix("error: ")
        raise (TemporaryError if result.returncode == 75 else ScriptError)(
            error or f"published step exited {result.returncode}; rerun just sync"
        )
    if result.stderr and ("--verbose" in command or "--debug" in command):
        sys.stderr.write(result.stderr)
    return result.stdout.splitlines()


def sync(args: argparse.Namespace) -> str:
    root = author_root(args.author_root or ROOT)
    if args.worker:
        levels = [
            *(["--verbose"] if args.verbose else []),
            *(["--debug"] if log.isEnabledFor(logging.DEBUG) else []),
        ]
        flags = (
            ["--dry-run" if args.dry_run else "--check"]
            if args.dry_run or args.check
            else []
        )
        lines: list[str] = []
        if not flags:
            lines += step(
                sys.executable,
                str(ROOT / "scripts/sync_private.py"),
                "--root",
                str(root),
                "--timeout",
                f"{args.timeout:g}",
                *levels,
                cwd=ROOT,
            )
        lines += step(
            sys.executable,
            str(ROOT / "scripts/install_skills.py"),
            "--snapshot",
            *(
                ["--private-root", str(root / "_skills_private")]
                if (root / "_skills_private").exists()
                else []
            ),
            *flags,
            "--timeout",
            f"{args.timeout:g}",
            *levels,
            cwd=ROOT,
        )
        return "\n".join(lines)
    sha = github(root, args.timeout)
    with published(root, sha, args.timeout) as checkout:
        return "\n".join(
            step(
                sys.executable,
                str(checkout / "scripts/sync.py"),
                "--worker",
                "--author-root",
                str(root),
                *(["--dry-run"] if args.dry_run else ["--check"] if args.check else []),
                "--timeout",
                f"{args.timeout:g}",
                *(["--verbose"] if args.verbose else []),
                *(["--debug"] if log.isEnabledFor(logging.DEBUG) else []),
                cwd=checkout,
            )
        )


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just sync", description=__doc__, epilog=EPILOG, exit_codes=EXIT_CODES
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="preview published install without writing installed skills",
    )
    modes.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if installed skills differ from published sources",
    )
    parser.add_argument(
        "--author-root",
        type=Path,
        help="original checkout holding the existing private clone (for published worker)",
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help="execute from a published deployment checkout",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="5m",
        help="network and lock timeout (default: 5m)",
    )
    return run_script(parser, sync, argv, debug="SYNC_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

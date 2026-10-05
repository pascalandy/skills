#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sign off the pushed HEAD: run just check on it, then post a green signoff status.

main merges a PR only when its head commit carries that status. The checks run
on that commit in a temporary worktree, so nothing done in this checkout during
them changes what they test, and nothing is signed off when the branch on GitHub
moves meanwhile. A head that already carries the status needs no new run.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes
from _common import is_network_failure, run, run_git, run_script

ROOT = Path(__file__).resolve().parent.parent
EPILOG = """\
A run prints `signoff<TAB>SHA` when it signs off, and nothing when HEAD already
carries a green signoff.

examples:
  just signoff             # check the pushed HEAD, then sign it off
  just signoff --dry-run   # print what a run would sign off, without checking"""
EXIT_CODES = exit_codes(
    {
        0: "HEAD carries a green signoff",
        1: "a check failed, or HEAD is not a clean, pushed commit",
        75: "GitHub or the network failed; retry",
    }
)
# git replace refs could swap what a commit holds, so every git call here, and
# the checks, see each commit exactly as GitHub has it
EXACT = os.environ | {"GIT_NO_REPLACE_OBJECTS": "1"}
log = logging.getLogger("signoff")


def fail(message: str, reason: str) -> ScriptError:
    """The error for a failed git or gh call; a network failure is temporary."""
    error = TemporaryError if is_network_failure(reason) else ScriptError
    return error(f"{message}: {reason}")


def run_here(
    *args: str, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    return run_git(*args, cwd=ROOT, timeout=timeout, env=EXACT)


def git(*args: str, timeout: float | None = None) -> str:
    result = run_here(*args, timeout=timeout)
    if result.returncode:
        raise fail(f"git {args[0]} failed", result.stderr.strip())
    # Not strip: a porcelain status line can start with a space
    return result.stdout.rstrip()


def gh(*args: str, timeout: float) -> str:
    try:
        result = run(
            ("gh", *args),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise ScriptError(
            "gh not found; install the GitHub CLI: https://cli.github.com"
        ) from None
    except subprocess.TimeoutExpired:
        raise TemporaryError(f"gh {args[0]} took longer than {timeout:g}s") from None
    if result.returncode:
        raise fail(f"gh {' '.join(args[:2])} failed", result.stderr.strip())
    return result.stdout


def is_ancestor(commit: str, of: str) -> bool:
    return run_here("merge-base", "--is-ancestor", commit, of).returncode == 0


def branch() -> str:
    name = run_here("symbolic-ref", "--quiet", "--short", "HEAD")
    if name.returncode:
        raise ScriptError("HEAD is detached; check out the PR branch, then rerun")
    return name.stdout.strip()


def remote_tip(name: str, timeout: float) -> str:
    """Fetch origin/<name>; return its tip, or "" when GitHub has no such branch.

    A PR from the branch `name` shows origin/<name>, whatever the upstream: a
    branch made from origin/main tracks main, and gh stack push sets none.
    """
    # The remote-tracking ref, not FETCH_HEAD, which another fetch can overwrite;
    # a concurrent fetch can only move this ref to GitHub's newer tip
    tracking = f"refs/remotes/origin/{name}"
    refspec = f"+refs/heads/{name}:{tracking}"
    fetched = run_here("fetch", "--quiet", "origin", refspec, timeout=timeout)
    if fetched.returncode == 0:
        return git("rev-parse", tracking)
    if "couldn't find remote ref" in fetched.stderr:
        return ""
    raise fail("git fetch origin failed", fetched.stderr.strip())


def pushed_head(timeout: float) -> str:
    """HEAD, once it is exactly the commit GitHub holds for this branch."""
    name = branch()
    tip = remote_tip(name, timeout)
    head = git("rev-parse", "HEAD")
    if head == tip:
        return head
    if tip and is_ancestor(head, tip):
        raise ScriptError(
            f"GitHub has newer commits on origin/{name}; "
            f"run: git pull --ff-only origin {name}"
        )
    raise ScriptError(f"HEAD is not on GitHub; run: git push origin HEAD:{name}")


def require_clean_tree() -> None:
    """Refuse changed or untracked files, which the checks would test but GitHub lacks."""
    paths = [line[3:] for line in git("status", "--porcelain", "-uall").splitlines()]
    if paths:
        shown = ", ".join(paths[:5])
        if len(paths) > 5:
            shown += f", and {len(paths) - 5} more"
        raise ScriptError(
            f"the working tree has uncommitted or untracked files: {shown}; "
            "commit and push them, or remove them"
        )


def signed_off(sha: str, timeout: float) -> bool:
    """Whether GitHub shows a green signoff status on `sha`."""
    status = json.loads(
        gh("api", f"repos/{{owner}}/{{repo}}/commits/{sha}/status", timeout=timeout)
    )
    return any(
        each["context"] == "signoff" and each["state"] == "success"
        for each in status["statuses"]
    )


@contextmanager
def worktree_at(sha: str) -> Iterator[Path]:
    """A temporary worktree at `sha`, so nothing done in this checkout during the
    checks changes what they test."""
    with tempfile.TemporaryDirectory(prefix="signoff-") as parent:
        path = Path(parent) / "checkout"
        try:
            added = run_here(
                "-c",
                "core.hooksPath=/dev/null",
                "worktree",
                "add",
                "--quiet",
                "--detach",
                str(path),
                sha,
            )
            if added.returncode:
                raise ScriptError(f"git worktree add failed: {added.stderr.strip()}")
            yield path
        finally:
            run_here("worktree", "remove", "--force", str(path))


def check_and_sign(sha: str, timeout: float) -> None:
    """Run just check on `sha` in a worktree of its own, then sign off `sha` if
    GitHub still holds it."""
    name = branch()
    log.info("run just check on %s", sha[:7])
    with worktree_at(sha) as checkout:
        # Its stdout holds only its {"ok":true}, which would read as this
        # script's verdict; a failure's output and verdict stay on stderr
        check = (sys.executable, str(checkout / "scripts/check.py"))
        checked = run(check, cwd=checkout, env=EXACT, stdout=subprocess.DEVNULL)
    if checked.returncode:
        raise ScriptError(f"just check failed on {sha[:7]}; nothing was signed off")
    if remote_tip(name, timeout) != sha:
        raise ScriptError(
            f"origin/{name} moved from {sha[:7]} while the checks ran; "
            "nothing was signed off"
        )
    log.info("sign off %s", sha[:7])
    gh("signoff", "--commit", sha, timeout=timeout)


def signoff(args: argparse.Namespace) -> str:
    require_clean_tree()
    sha = pushed_head(args.timeout)
    if signed_off(sha, args.timeout):
        log.info("%s already carries a green signoff", sha[:7])
        return ""
    if not args.dry_run:
        check_and_sign(sha, args.timeout)
    return f"signoff\t{sha[:7]}"


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just signoff",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print what a run would sign off, without running the checks",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="1m",
        help="how long each call to GitHub may take (default: 1m)",
    )
    return run_script(parser, signoff, argv, debug="SIGNOFF_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

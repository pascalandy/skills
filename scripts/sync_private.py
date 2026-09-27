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

import argparse
import logging
import re
import socket
import subprocess
from pathlib import Path

from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "_skills_private"
log = logging.getLogger("sync-private")


def git(*args: str, cwd: Path = PRIVATE) -> subprocess.CompletedProcess[str]:
    log.debug("git %s", " ".join(args))
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def last_line(result: subprocess.CompletedProcess[str]) -> str:
    lines = (result.stderr + result.stdout).strip().splitlines()
    return lines[-1] if lines else f"git exited {result.returncode}"


def private_url() -> str:
    origin = git("remote", "get-url", "origin", cwd=ROOT).stdout.strip()
    url, found = re.subn(r"(?<=[/:])skills(\.git)?/?$", r"skills-private\1", origin)
    if not found:
        raise ScriptError(
            f"origin {origin or '(none)'} does not end in skills, so the private "
            "repository's URL is unknown"
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


def github_head() -> str:
    """The private repository's main on GitHub, which every machine should match."""
    if not is_clone():
        raise ScriptError(f"{PRIVATE} is not a clone of the private repository")
    listed = git("ls-remote", "--quiet", "origin", "refs/heads/main")
    if listed.returncode or not listed.stdout.strip():
        raise ScriptError(f"could not read the private repository: {last_line(listed)}")
    return listed.stdout.split()[0]


def sync(dry_run: bool = False) -> str:
    host = socket.gethostname().split(".")[0]
    _, status = state()
    if status == "missing":
        url = private_url()
        if dry_run:
            return f"would clone {url} into {PRIVATE}"
        cloned = git("clone", "--quiet", url, str(PRIVATE), cwd=ROOT)
        if cloned.returncode:
            raise ScriptError(f"could not clone {url}: {last_line(cloned)}")
        return ""
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
    if dry_run:
        return f"would commit private edits from {host}" if status == "dirty" else ""
    if status == "dirty":
        for step in (
            ("add", "--all"),
            ("commit", "--quiet", "-m", f"🧰 skill: private: save edits from {host}"),
        ):
            done = git(*step)
            if done.returncode:
                raise ScriptError(f"could not commit private edits: {last_line(done)}")
    pulled = git("pull", "--rebase", "--quiet")
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
        raise ScriptError(f"could not pull the private repository: {last_line(pulled)}")
    ahead = git("rev-list", "--count", "@{upstream}..HEAD").stdout.strip()
    if ahead not in ("", "0"):
        pushed = git("push", "--quiet")
        if pushed.returncode:
            raise ScriptError(
                f"could not push private edits from {host}: {last_line(pushed)}"
            )
    log.debug("private repository at %s", git("rev-parse", "HEAD").stdout.strip())
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  just sync                                # runs this, then installs
  uv run scripts/sync_private.py --dry-run # what a sync would clone or commit""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be cloned or committed without changing anything",
    )
    return run_script(parser, lambda args: sync(args.dry_run), argv)


if __name__ == "__main__":
    raise SystemExit(main())

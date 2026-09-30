#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Repository entrypoints dispatch to cached published code before importing it."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def refusal(root: Path, checkout: Path) -> str:
    """Why the cached checkout must not run, or "" when Git owns it clean."""
    registered = subprocess.run(
        ["git", "worktree", "list", "--porcelain", "-z"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\0")
    if checkout.is_symlink() or f"worktree {checkout}" not in registered:
        return f"{checkout} is not the owned worktree; move it aside"
    state = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if state:
        return f"published worktree {checkout} has edits; inspect them"
    return ""


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    mode, *arguments = sys.argv[1:]
    script = {"sync": "sync.py", "fleet": "sync_fleet.py", "hook": "sync_fleet.py"}[
        mode
    ]
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        sys.stderr.write(result.stderr)
        raise SystemExit(1)
    checkout = Path(result.stdout.strip()) / "published-deployment"
    source = checkout / "scripts" / script
    if not source.is_file():
        source = root / "scripts" / script
    elif problem := refusal(root, checkout):
        # Every checkout's hooks land here, so a broken cache never blocks git
        if mode == "hook":
            sys.stderr.write(f"warning: {problem}; the fleet does not sync\n")
            raise SystemExit(0)
        raise SystemExit(f"error: {problem}")
    os.execv(
        sys.executable,
        [
            sys.executable,
            str(source),
            "--author-root",
            str(root),
            *(["--hook"] if mode == "hook" else []),
            *arguments,
        ],
    )


if __name__ == "__main__":
    main()

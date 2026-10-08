#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check that every pasted copy of the cli block matches scripts/_cli.py."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from _cli import Parser, ScriptError, exit_codes, run_script

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "scripts" / "_cli.py"
BEGIN = "# >>> cli-block"
END = "# <<< cli-block"
SKIPPED = {"node_modules", ".venv", "venv", "__pycache__"}
BLOCK = re.compile(
    rf"^{re.escape(BEGIN)}.*?^{re.escape(END)}$\n?", re.MULTILINE | re.DOTALL
)

EPILOG = """\
A skill script pastes the block in scripts/_cli.py whole, from its
"# >>> cli-block" line through its "# <<< cli-block" line. Without --fix,
this changes nothing and lists each stale copy on stderr.

examples:
  uv run scripts/check_cli_block.py
  uv run scripts/check_cli_block.py --fix
  uv run scripts/check_cli_block.py --verbose"""

EXIT_CODES = exit_codes(
    {0: "every copy matches, or --fix updated them", 1: "a copy differs"}
)

log = logging.getLogger("check-cli-block")


def block(text: str, label: str) -> re.Match[str]:
    """The block in `text`, from its first marker line through its last."""
    match = BLOCK.search(text)
    if match is None:
        raise ScriptError(
            f"{label} has no whole cli block; paste scripts/_cli.py from "
            f"{BEGIN!r} through {END!r}"
        )
    return match


def copies() -> list[Path]:
    """Every file under authoring/ that pastes the block."""
    found: list[Path] = []
    for directory, subdirectories, files in os.walk(ROOT / "authoring"):
        subdirectories[:] = sorted(set(subdirectories) - SKIPPED)
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix != ".py":
                continue
            log.info("read %s", path.relative_to(ROOT))
            if BEGIN in path.read_text(encoding="utf-8"):
                found.append(path)
    return found


def check(fix: bool) -> dict[str, Any]:
    canonical = block(CANONICAL.read_text(encoding="utf-8"), "scripts/_cli.py")[0]
    stale: list[str] = []
    for path in copies():
        label = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        copy = block(text, label)
        if copy[0] == canonical:
            continue
        if fix:
            fixed = text[: copy.start()] + canonical + text[copy.end() :]
            path.write_text(fixed, encoding="utf-8")
        stale.append(label)
    if stale and not fix:
        raise ScriptError(
            f"{len(stale)} pasted cli block{'s differ' if len(stale) > 1 else ' differs'}"
            " from scripts/_cli.py; run: uv run scripts/check_cli_block.py --fix",
            detail="\n".join(f"update\t{label}" for label in stale),
        )
    return {"changes": [["update", label] for label in stale]} if stale else {}


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="scripts/check_cli_block.py",
        description="Check that every pasted copy of the cli block matches scripts/_cli.py",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="rewrite each stale copy and list each under changes",
    )
    return run_script(parser, lambda args: check(args.fix), argv)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the skill table that agents without these skills read on GitHub."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes
from _common import frontmatter_description, run_script

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TABLE = ROOT / "docs" / "references" / "remote-skills.md"
# Stated once above the table, so each row spends no tokens on a link
URL = (
    "https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md"
)

HEADER = """\
---
name: remote-skills
description: Use andy's skills remotely
---

<!-- Generated from skills/*/SKILL.md by `just remote-skills`; do not edit -->

URL: {url}

| Skill | Description |
|---|---|
"""

EPILOG = """\
The table reads skills/, so run just flatten-skills first. A run that changes
the table prints one line: add or update, then a tab and the table's path. A
dry run prints the same line and changes nothing; a run with nothing to change
prints nothing.

examples:
  just remote-skills
  just remote-skills --dry-run
  just remote-skills --check"""

EXIT_CODES = exit_codes(
    {
        0: "the table matches skills/, or now does",
        1: "a skill has no description, or --check found the table stale",
    }
)

log = logging.getLogger("remote-skills")


def render() -> str:
    """The page text: one row per skills/<name>/SKILL.md, in name order."""
    rows: list[str] = []
    errors: list[str] = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        name = path.parent.name
        log.info("read %s", path.relative_to(ROOT))
        description = frontmatter_description(path.read_text(encoding="utf-8"))
        # A quoted "\n" decodes to a real line break, which would split the row
        problem = (
            "has no description"
            if not description
            else "has a line break in its description"
            if "\n" in description or "\r" in description
            else ""
        )
        if problem:
            errors.append(
                f"{path.relative_to(ROOT)} {problem}; "
                "fix its source in authoring/, then run: just flatten-skills"
            )
            continue
        cell = description.replace("|", "\\|")
        rows.append(f"| {name} | {cell} |")
    if errors:
        raise ScriptError(*errors)
    if not rows:
        raise ScriptError(
            "no skills found at skills/<name>/SKILL.md; run: just flatten-skills"
        )
    return HEADER.replace("{url}", URL) + "\n".join(rows) + "\n"


def work(args: argparse.Namespace) -> str:
    table = render()
    current = TABLE.read_text(encoding="utf-8") if TABLE.is_file() else None
    if current == table:
        return ""
    line = f"{'add' if current is None else 'update'}\t{TABLE.relative_to(ROOT)}"
    if args.check:
        raise ScriptError(
            f"{TABLE.relative_to(ROOT)} differs from skills/; run: just remote-skills",
            detail=line,
        )
    if not args.dry_run:
        TABLE.write_text(table, encoding="utf-8")
    return line


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just remote-skills",
        description="Write the name and description of every skill in skills/ to "
        "docs/references/remote-skills.md",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print the change a run would make without making it",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="dry run that exits 1 when the table differs, printing the change on stderr",
    )
    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

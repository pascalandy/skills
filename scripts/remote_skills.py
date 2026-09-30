#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the skill tables that agents without these skills read on GitHub."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes
from _common import frontmatter_description, frontmatter_value, run_script

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DOCS = ROOT / "docs" / "references"
# Stated once per page, so each row spends no tokens on a link
URL = (
    "https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md"
)
# Each kind gets a section of remote-skills.md and a page of its own. A skill
# with any other kind, or none, is listed under Unknown on remote-skills.md only
KINDS = ("general", "dev")
UNKNOWN = "unknown"
TABLE_HEAD = "| Skill | Description |\n|---|---|\n"

EPILOG = """\
The tables read skills/, so run just flatten-skills first. A run prints one
line per page it changes: add or update, then a tab and the page's path. A dry
run prints the same lines and changes nothing; a run with nothing to change
prints nothing.

pages:
  docs/references/remote-skills.md          every skill, one section per kind
  docs/references/remote-skills-general.md  general skills only
  docs/references/remote-skills-dev.md      dev skills only

examples:
  just remote-skills
  just remote-skills --dry-run
  just remote-skills --check"""

EXIT_CODES = exit_codes(
    {
        0: "the tables match skills/, or now do",
        1: "a skill has no description, or --check found a table stale",
    }
)

log = logging.getLogger("remote-skills")


def rows_by_kind() -> dict[str, list[str]]:
    """One table row per skills/<name>/SKILL.md, in name order, keyed by kind."""
    rows: dict[str, list[str]] = {kind: [] for kind in (*KINDS, UNKNOWN)}
    errors: list[str] = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        log.info("read %s", path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        description = frontmatter_description(text)
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
        kind = frontmatter_value(text, "kind")
        cell = description.replace("|", "\\|")
        rows[kind if kind in KINDS else UNKNOWN].append(
            f"| {path.parent.name} | {cell} |\n"
        )
    if errors:
        raise ScriptError(*errors)
    if not any(rows.values()):
        raise ScriptError(
            "no skills found at skills/<name>/SKILL.md; run: just flatten-skills"
        )
    return rows


def page(name: str, description: str, body: str) -> str:
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n\n"
        "<!-- Generated from skills/*/SKILL.md by `just remote-skills`; do not edit -->\n\n"
        f"URL: {URL}\n\n{body}"
    )


def render() -> dict[Path, str]:
    """Each page's path and text."""
    rows = rows_by_kind()
    sections = [
        f"## {kind.capitalize()}\n\n{TABLE_HEAD}{''.join(kind_rows)}"
        for kind, kind_rows in rows.items()
        if kind != UNKNOWN or kind_rows
    ]
    pages = {
        DOCS / "remote-skills.md": page(
            "remote-skills", "Use andy's skills remotely", "\n".join(sections)
        )
    }
    for kind in KINDS:
        pages[DOCS / f"remote-skills-{kind}.md"] = page(
            f"remote-skills-{kind}",
            f"Use andy's {kind} skills remotely",
            TABLE_HEAD + "".join(rows[kind]),
        )
    return pages


def work(args: argparse.Namespace) -> str:
    lines: list[str] = []
    for path, text in render().items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == text:
            continue
        lines.append(
            f"{'add' if current is None else 'update'}\t{path.relative_to(ROOT)}"
        )
        if not (args.check or args.dry_run):
            path.write_text(text, encoding="utf-8")
    if args.check and lines:
        raise ScriptError(
            "the skill tables differ from skills/; run: just remote-skills",
            detail="\n".join(lines),
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just remote-skills",
        description="Write the name and description of every skill in skills/ to "
        "docs/references/remote-skills.md, grouped by kind, and one page per kind",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print the changes a run would make without making them",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="dry run that exits 1 when a table differs, printing the changes on stderr",
    )
    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

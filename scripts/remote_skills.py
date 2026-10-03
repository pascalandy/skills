#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the skill lists that agents without these skills read on GitHub."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes
from _common import (
    KINDS,
    UNKNOWN,
    frontmatter_description,
    frontmatter_value,
    kind_of,
    run_script,
)

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DOCS = ROOT / "docs" / "references"
# Stated once per page, so each bullet spends no tokens on a link
URL = (
    "https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md"
)
ROUTES = "A mode's routes run through that mode's SKILL.md."
TIERS = ("modes", "skills", "helpers")

EPILOG = """\
The lists read skills/, so run just compile-skills first. Each kind lists its
modes, each with its routes, then its skills, then its helpers. A mode is a
skill named *-mode with a playbooks/ folder, and each file or folder in
playbooks/ is a route; a skill with only one of the two fails the run. A skill
whose frontmatter sets role: "helper" lists under helpers.

A run prints one line per page it changes: add or update, then a tab and the
page's path. A dry run prints the same lines and changes nothing; a run with
nothing to change prints nothing.

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
        0: "the lists match skills/, or now do",
        1: "a skill breaks a listing rule, or --check found a list stale",
    }
)

log = logging.getLogger("remote-skills")


def problems(name: str, description: str, role: str | None, is_mode: bool) -> list[str]:
    """What keeps a skill off the lists, each phrased to follow its SKILL.md path."""
    found: list[str] = []
    if not description:
        found.append("has no description")
    # A quoted "\n" decodes to a real line break, which would split the bullet
    elif "\n" in description or "\r" in description:
        found.append("has a line break in its description")
    if name.endswith("-mode") and not is_mode:
        found.append("is named like a mode but has no playbooks/ folder beside it")
    if is_mode and not name.endswith("-mode"):
        found.append("has a playbooks/ folder beside it but no -mode name")
    if role is not None and role != "helper":
        found.append(f'has role "{role}", but the only role is "helper"')
    if role is not None and is_mode:
        found.append("is a mode, which always lists first, but sets a role")
    return found


def bullets_by_kind() -> dict[str, dict[str, list[str]]]:
    """One bullet per skills/<name>/SKILL.md, in name order, keyed by kind and
    tier. A mode's bullet nests its routes, one per entry in its playbooks/."""
    bullets = {kind: {tier: [] for tier in TIERS} for kind in (*KINDS, UNKNOWN)}
    errors: list[str] = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        log.info("read %s", path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        name = path.parent.name
        description = frontmatter_description(text)
        role = frontmatter_value(text, "role")
        playbooks = path.parent / "playbooks"
        if found := problems(name, description, role, playbooks.is_dir()):
            errors.extend(
                f"{path.relative_to(ROOT)} {problem}; "
                "fix its source in authoring/, then run: just compile-skills"
                for problem in found
            )
            continue
        # Hidden entries, such as the .DS_Store Finder drops, are not routes
        routes = (
            sorted(
                entry.name.removesuffix(".md")
                for entry in playbooks.iterdir()
                if not entry.name.startswith(".")
            )
            if playbooks.is_dir()
            else []
        )
        tier = "modes" if playbooks.is_dir() else "helpers" if role else "skills"
        bullets[kind_of(text)][tier].append(
            f"- `{name}`: {description}\n"
            + "".join(f"  - {route}\n" for route in routes)
        )
    if errors:
        raise ScriptError(*errors)
    if not any(any(tiers.values()) for tiers in bullets.values()):
        raise ScriptError(
            "no skills found at skills/<name>/SKILL.md; run: just compile-skills"
        )
    return bullets


def tiers_body(tiers: dict[str, list[str]], heading: str) -> str:
    """A heading and its bullets for each tier that has skills, in TIERS order."""
    return "\n".join(
        f"{heading} {tier.capitalize()}\n\n{''.join(lines)}"
        for tier, lines in tiers.items()
        if lines
    )


def page(name: str, description: str, body: str) -> str:
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n\n"
        "<!-- Generated from skills/*/SKILL.md by `just remote-skills`; do not edit -->\n\n"
        f"URL: {URL}\n\n{ROUTES}\n\n{body}"
    )


def render() -> dict[Path, str]:
    """Each page's path and text. Each kind gets a section of remote-skills.md
    and a page of its own; Unknown gets only a section, and only when it has
    skills."""
    bullets = bullets_by_kind()
    sections = [
        f"## {kind.capitalize()}\n\n{tiers_body(tiers, '###')}"
        for kind, tiers in bullets.items()
        if kind != UNKNOWN or any(tiers.values())
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
            tiers_body(bullets[kind], "##"),
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
            "the skill lists differ from skills/; run: just remote-skills",
            detail="\n".join(lines),
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just remote-skills",
        description="Write the name and description of every skill in skills/ to "
        "docs/references/remote-skills.md, grouped by kind with modes first, and one "
        "page per kind",
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
        help="dry run that exits 1 when a list differs, printing the changes on stderr",
    )
    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

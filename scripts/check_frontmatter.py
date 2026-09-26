#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check that SKILL.md frontmatter quotes string values with double quotes."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
AUTHORING = ROOT / "authoring"

EPILOG = """\
rule:
  Quote frontmatter string values and string list items with double quotes.
  Booleans, null, numbers, and inline mappings stay bare. This is a style
  check, not a full YAML parser.

examples:
  just check-frontmatter
  just check-frontmatter --verbose

exit codes: 0 ok, 1 style errors found, 2 bad usage, 130 interrupted"""

FRONTMATTER_DELIMITER = "---\n"
KEY_VALUE_RE = re.compile(r"^\s*(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$")
LIST_ITEM_RE = re.compile(r"^\s*-\s+(?P<value>.*)$")
BOOLEAN_OR_NULL = {"true", "false", "null", "~"}
NUMBER_RE = re.compile(r"^[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")

log = logging.getLogger("check-frontmatter")


def is_bare_scalar(value: str) -> bool:
    return value.lower() in BOOLEAN_OR_NULL or NUMBER_RE.match(value) is not None


def is_quoted(value: str) -> bool:
    return len(value) >= 2 and value.startswith('"') and value.endswith('"')


def inline_list_items(value: str) -> list[str]:
    """Split an inline list at commas outside double-quoted strings."""
    content = value[1:-1]
    items: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, char in enumerate(content):
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == "," and not quoted:
            items.append(content[start:index].strip())
            start = index + 1
    items.append(content[start:].strip())
    return items


def value_problem(value: str) -> str | None:
    """Return why a frontmatter value breaks the quoting rule, or None when it follows it."""
    value = value.strip()
    if not value or value.startswith("{"):
        return None
    if value.startswith("[") and value.endswith("]"):
        if any(
            item and not (is_quoted(item) or is_bare_scalar(item))
            for item in inline_list_items(value)
        ):
            return "inline list string items must be double-quoted"
        return None
    if value.startswith((">", "|")):
        return "uses a block scalar; use a double-quoted string instead"
    if value.startswith("'"):
        return "uses single quotes; use double quotes"
    if is_quoted(value) or is_bare_scalar(value):
        return None
    return "string value must be double-quoted"


def check_file(path: Path) -> list[str]:
    """Return one `path:line: problem` message per frontmatter style error."""
    label = path.relative_to(ROOT)
    parts = path.read_text(encoding="utf-8").split(FRONTMATTER_DELIMITER, 2)
    if len(parts) < 3 or parts[0]:
        return [f"{label}: frontmatter must open and close with a --- line"]

    errors: list[str] = []
    for line_number, line in enumerate(parts[1].splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if match := KEY_VALUE_RE.match(line):
            context = match["key"]
        elif match := LIST_ITEM_RE.match(line):
            context = "list item"
        else:
            continue
        if problem := value_problem(match["value"]):
            errors.append(f"{label}:{line_number}: {context} {problem}")
    return errors


def check() -> str:
    """Check every SKILL.md under authoring/ and return the summary line."""
    paths = sorted(AUTHORING.glob("**/SKILL.md"))
    if not paths:
        raise ScriptError("no SKILL.md files found under authoring/")
    errors: list[str] = []
    for path in paths:
        log.debug("check %s", path.relative_to(ROOT))
        errors.extend(check_file(path))
    if errors:
        raise ScriptError(*errors)
    return f"ok: {len(paths)} SKILL.md files"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just check-frontmatter",
        description="Check SKILL.md frontmatter quoting under authoring/",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return run_script(parser, lambda args: check(), argv)


if __name__ == "__main__":
    raise SystemExit(main())

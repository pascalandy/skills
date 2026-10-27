#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Flag bare semicolons and hashes in Mermaid sequence text, before it is lost."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Iterator
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes, run_script

ROOT = Path(__file__).resolve().parent.parent
EXIT_CODES = exit_codes({1: "bare sequence text characters or an unreadable input"})
EPILOG = """\
examples:
  just check-mermaid-sequence
  just check-mermaid-sequence --verbose
  uv run scripts/check_mermaid_sequence.py diagram.md
  uv run scripts/check_mermaid_sequence.py - < diagram.md"""

# This is a text guard, not a Mermaid syntax parser (#790).
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
ENTITY = re.compile(r"#\w+;")
MESSAGE = re.compile(
    r"[^\s:<>]+?\s*(?:-->>|->>|-->|->|--x|-x|--\)|-\))\s*"
    r"[+-]?\s*[^\s:<>]+\s*:\s*(.*)"
)
NOTE = re.compile(r"note\s+(?:over|left\s+of|right\s+of)\b[^:]*:\s*(.*)", re.IGNORECASE)
BLOCK = re.compile(r"(?:alt|else|opt|loop|par|and|critical|option|break)\b\s*(.*)")
log = logging.getLogger("mermaid-sequence")


def mermaid_blocks(text: str) -> Iterator[list[tuple[int, str]]]:
    """Top-level fenced sources, retaining their original Markdown line numbers."""
    fence = ""
    mermaid = False
    lines: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if fence:
            if re.fullmatch(
                r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line
            ):
                if mermaid:
                    yield lines
                fence = ""
            elif mermaid:
                lines.append((number, line))
        elif opening := FENCE.fullmatch(line):
            fence = opening[1]
            mermaid = opening[2].strip() == "mermaid"
            lines = []
    if fence and mermaid:
        yield lines


def sequence_lines(lines: list[tuple[int, str]]) -> list[tuple[int, str]] | None:
    """Find the declaration after optional YAML and Mermaid comment preludes."""
    yaml = False
    init = False
    first = True
    for index, (_, line) in enumerate(lines):
        text = line.strip()
        if not text:
            continue
        if first and text == "---":
            yaml = True
            first = False
            continue
        first = False
        if yaml:
            if text == "---":
                yaml = False
            continue
        if init:
            init = "}%%" not in text
            continue
        if text.startswith("%%"):
            init = text.startswith("%%{") and "}%%" not in text
            continue
        return lines[index + 1 :] if text == "sequenceDiagram" else None
    return None


def check_text(text: str, label: str) -> tuple[list[str], int]:
    errors: list[str] = []
    blocks = 0
    for source in mermaid_blocks(text):
        lines = sequence_lines(source)
        if lines is None:
            continue
        blocks += 1
        init = False
        for number, line in lines:
            text = line.strip()
            if init:
                init = "}%%" not in text
                continue
            if text.startswith("%%"):
                init = text.startswith("%%{") and "}%%" not in text
                continue
            for kind, pattern in (
                ("note", NOTE),
                ("block label", BLOCK),
                ("message", MESSAGE),
            ):
                if match := pattern.fullmatch(text):
                    bare = ENTITY.sub("", match[1])
                    characters = [char for char in (";", "#") if char in bare]
                    if characters:
                        errors.append(
                            f"{label}:{number}: bare {' and '.join(repr(c) for c in characters)} "
                            f"in sequence {kind}; write ';' as '#59;' and '#' as '#35;', "
                            "then rerun just check-mermaid-sequence"
                        )
                    break
    return errors, blocks


def check(args: argparse.Namespace) -> dict[str, object]:
    paths = args.files or sorted((ROOT / "authoring").rglob("*.md"))
    errors: list[str] = []
    files = blocks = 0
    for path in paths:
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        try:
            text = (
                sys.stdin.read()
                if str(path) == "-"
                else path.read_text(encoding="utf-8")
            )
        except OSError as error:
            errors.append(f"{label}: {error}; pass an existing readable Markdown file")
            continue
        found, count = check_text(text, label)
        errors.extend(found)
        files += bool(count)
        blocks += count
    log.info("checked %s files containing %s sequence blocks", files, blocks)
    if errors:
        raise ScriptError(*errors)
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just check-mermaid-sequence",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=exit_codes(
            {1: "bare sequence text characters or an unreadable input"}
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Markdown files, or - for stdin (default: all authoring/**/*.md)",
    )
    return run_script(parser, check, argv)


if __name__ == "__main__":
    raise SystemExit(main())

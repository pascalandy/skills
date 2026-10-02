#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check a skill folder against the writing-for-agents best practices a script can verify."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn
from urllib.parse import unquote

PROG = "validate_skill.py"

EPILOG = """\
Checks the best practices marked (validator) in writing-for-agents/SKILL.md:
SKILL.md and every Markdown file it links. A clean skill prints nothing.

exit codes:
  0  no errors; warnings may print
  1  at least one error
  2  usage error: a folder is missing or has no SKILL.md

examples:
  uv run path/to/writing-for-agents/scripts/validate_skill.py ../processing-pdfs
  uv run path/to/writing-for-agents/scripts/validate_skill.py ~/.agents/skills/*"""

# Titles match the BP lines in SKILL.md; a test keeps them in sync
BP_TITLES = {
    "BP_01": "Progressive disclosure",
    "BP_07": "No dated text",
    "BP_12": "Links resolve",
    "BP_13": "Name",
    "BP_14": "Description is a trigger",
    "BP_15": "SKILL.md under 500 lines",
    "BP_16": "Contents list",
}

# Limits from the Agent Skills specification and the strictest agent platforms
NAME_MAX = 64
DESCRIPTION_MAX = 1024
BODY_MAX = 500
RESERVED_WORDS = ("anthropic", "claude")
CONTENTS_THRESHOLD = 100
CONTENTS_SEARCH_LINES = 25

NAME_CHARS_RE = re.compile(r"[a-z0-9-]+")
XML_TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
KEY_RE = re.compile(r"(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)")
BLOCK_INDICATORS = {">", "|", ">-", "|-", ">+", "|+"}
QUOTED_RE = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^']|'')*'")
COMMENT_RE = re.compile(r"\s+#.*$")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
# Inline links and reference definitions; a bare target may hold one level of parentheses
DESTINATION = r"(?:<(?P<angle>[^<>\n]*)>|(?P<bare>(?:[^()\s]|\([^()\s]*\))+))"
LINK_RE = re.compile(
    rf"!?\[[^\]]*\]\(\s*{DESTINATION}(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^()]*\)))?\s*\)"
)
REFERENCE_DEF_RE = re.compile(rf"^ {{0,3}}\[[^\]]+\]:\s*{DESTINATION}")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_PATH_RE = re.compile(
    r"(?:[A-Za-z0-9_.-]+\\)+[A-Za-z0-9_.-]+\.(?:md|py|sh|js|ts|json|ya?ml|toml|txt)\b"
)
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|"
    "December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec"
)
DATED_RE = re.compile(
    rf"\b(?:before|after|until|as of)\s+(?:(?:{MONTHS})\.?\s+)?(?:\d{{1,2}},?\s+)?"
    r"(?:19|20)\d{2}(?:-\d{2}){0,2}\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*)")
CONTENTS_RE = re.compile(
    r"^\s*(?:#{1,6}\s*|\*\*)?(?:table of )?contents\b", re.IGNORECASE
)

Level = Literal["error", "warning"]


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(2, f"{PROG}: error: {message}\nrun '{PROG} --help'\n")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    level: Level
    bp: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.level}: {self.bp} {BP_TITLES[self.bp]}: {self.message}"


@dataclass(frozen=True)
class Field:
    value: str
    line: int


@dataclass(frozen=True)
class Prose:
    """A Markdown line outside fenced code; `masked` blanks its inline code spans."""

    number: int
    raw: str
    masked: str
    headings: tuple[str, ...]


def scalar(raw: str, block: bool) -> str:
    """The string a YAML scalar holds: block text as written, quoted text unescaped,
    plain text without its trailing comment."""
    if block:
        return raw
    if quoted := QUOTED_RE.match(raw):
        text = quoted.group(0)[1:-1]
        if quoted.group(0)[0] == "'":
            return text.replace("''", "'")
        return text.replace('\\"', '"').replace("\\\\", "\\")
    return COMMENT_RE.sub("", raw)


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, Field], int]:
    """Read top-level `key: value` pairs; return them and the index of the first body line."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, 0
    raw: dict[str, tuple[str, int, bool]] = {}
    key: str | None = None
    for index in range(1, end):
        line = lines[index]
        if line.startswith("#"):
            continue
        match = KEY_RE.fullmatch(line) if not line[:1].isspace() else None
        if match:
            key = name = match.group("key")
            value = match.group("value").strip()
            # A block scalar's text starts on the next line
            block = COMMENT_RE.sub("", value) in BLOCK_INDICATORS
            raw[name] = ("" if block else value, index + 1, block)
        elif key and line.strip():
            value, number, block = raw[key]
            raw[key] = (f"{value} {line.strip()}".strip(), number, block)
    fields = {k: Field(scalar(v, block), n) for k, (v, n, block) in raw.items()}
    return fields, end + 1


def prose_lines(lines: list[str], start: int) -> list[Prose]:
    """Lines outside fenced code, numbered from 1, with the headings each sits under."""
    result: list[Prose] = []
    fence: str | None = None
    headings: list[tuple[int, str]] = []
    for index in range(start, len(lines)):
        line = lines[index]
        match = FENCE_RE.match(line)
        if fence:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = None
            continue
        if match:
            fence = match.group(1)
            continue
        if heading := HEADING_RE.match(line):
            level = len(heading["hashes"])
            headings = [h for h in headings if h[0] < level] + [
                (level, heading["text"])
            ]
        masked = INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)
        result.append(
            Prose(index + 1, line, masked, tuple(text for _, text in headings))
        )
    return result


def check_name(skill: Path, skill_md: Path, fields: dict[str, Field]) -> list[Finding]:
    field = fields.get("name")
    if field is None or not field.value:
        return [
            Finding(
                skill_md,
                field.line if field else 1,
                "error",
                "BP_13",
                "name is missing",
            )
        ]
    name = field.value
    problems: list[str] = []
    if len(name) > NAME_MAX:
        problems.append(f"name '{name}' is longer than {NAME_MAX} characters")
    if not NAME_CHARS_RE.fullmatch(name):
        problems.append(
            f"name '{name}' may only use lowercase letters, digits, and hyphens"
        )
    if name.startswith("-") or name.endswith("-") or "--" in name:
        problems.append(f"name '{name}' starts or ends with a hyphen or contains '--'")
    if name != skill.resolve().name:
        problems.append(
            f"name '{name}' does not match the folder name '{skill.resolve().name}'"
        )
    problems += [
        f"name '{name}' contains the reserved word '{word}'"
        for word in RESERVED_WORDS
        if word in name.lower()
    ]
    return [
        Finding(skill_md, field.line, "error", "BP_13", problem) for problem in problems
    ]


def check_description(skill_md: Path, fields: dict[str, Field]) -> list[Finding]:
    field = fields.get("description")
    if field is None or not field.value:
        return [
            Finding(
                skill_md,
                field.line if field else 1,
                "error",
                "BP_14",
                "description is missing",
            )
        ]
    findings: list[Finding] = []
    if len(field.value) > DESCRIPTION_MAX:
        findings.append(
            Finding(
                skill_md,
                field.line,
                "error",
                "BP_14",
                f"description has {len(field.value)} characters; the limit is {DESCRIPTION_MAX}",
            )
        )
    if tag := XML_TAG_RE.search(field.value):
        findings.append(
            Finding(
                skill_md,
                field.line,
                "error",
                "BP_14",
                f"description contains the XML tag '{tag.group(0)}'",
            )
        )
    return findings


def link_targets(prose: list[Prose]) -> list[tuple[Prose, str]]:
    found: list[tuple[Prose, str]] = []
    for line in prose:
        matches = [*LINK_RE.finditer(line.masked)]
        if definition := REFERENCE_DEF_RE.match(line.masked):
            matches.append(definition)
        found += [
            (line, m["angle"] if m["angle"] is not None else m["bare"]) for m in matches
        ]
    return found


def resolve_local(skill: Path, source: Path, target: str) -> Path | None:
    """The file a relative link reaches inside the skill, or None for URLs, anchors, and outside paths."""
    if SCHEME_RE.match(target) or target.startswith(("#", "/")):
        return None
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return None
    resolved = (source.parent / path).resolve()
    return resolved if resolved.is_relative_to(skill.resolve()) else None


def check_document(
    skill: Path, path: Path, prose: list[Prose], is_skill_md: bool
) -> list[Finding]:
    findings: list[Finding] = []
    for line, target in link_targets(prose):
        if "\\" in target:
            findings.append(
                Finding(
                    path,
                    line.number,
                    "error",
                    "BP_12",
                    f"link '{target}' uses backslashes",
                )
            )
            continue
        resolved = resolve_local(skill, path, target)
        if resolved is None:
            continue
        if not resolved.exists():
            findings.append(
                Finding(
                    path,
                    line.number,
                    "error",
                    "BP_12",
                    f"link to missing file '{target}'",
                )
            )
        elif (
            not is_skill_md and resolved.suffix == ".md" and resolved.name != "SKILL.md"
        ):
            findings.append(
                Finding(
                    path,
                    line.number,
                    "warning",
                    "BP_01",
                    f"links to reference file '{target}'; link it from SKILL.md instead",
                )
            )
    for line in prose:
        # Link targets were checked above; this catches paths in prose and inline code
        for match in WINDOWS_PATH_RE.finditer(LINK_RE.sub(" ", line.raw)):
            findings.append(
                Finding(
                    path,
                    line.number,
                    "error",
                    "BP_12",
                    f"path '{match.group(0)}' uses backslashes",
                )
            )
        if any("old pattern" in heading.lower() for heading in line.headings):
            continue
        for match in DATED_RE.finditer(line.masked):
            findings.append(
                Finding(
                    path,
                    line.number,
                    "warning",
                    "BP_07",
                    f"dated text '{match.group(0)}'; keep the current method and move the old one to 'Old patterns'",
                )
            )
    return findings


def check_contents(path: Path, lines: list[str]) -> list[Finding]:
    if len(lines) <= CONTENTS_THRESHOLD or any(
        CONTENTS_RE.match(line) for line in lines[:CONTENTS_SEARCH_LINES]
    ):
        return []
    message = f"{len(lines)} lines and no Contents list; ask the user before adding one"
    return [Finding(path, 1, "warning", "BP_16", message)]


def validate(skill: Path) -> list[Finding]:
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        raise UsageError(f"{skill} has no SKILL.md; pass a skill folder")
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    fields, body_start = parse_frontmatter(lines)
    findings = check_name(skill, skill_md, fields) + check_description(skill_md, fields)
    if (body := len(lines) - body_start) > BODY_MAX:
        findings.append(
            Finding(
                skill_md,
                body_start + BODY_MAX + 1,
                "error",
                "BP_15",
                f"body has {body} lines; the limit is {BODY_MAX}",
            )
        )
    prose = prose_lines(lines, body_start)
    findings += check_document(skill, skill_md, prose, is_skill_md=True)
    references: dict[Path, Path] = {}
    for _, target in link_targets(prose):
        resolved = resolve_local(skill, skill_md, target)
        if (
            resolved
            and resolved.is_file()
            and resolved.suffix == ".md"
            and resolved != skill_md.resolve()
        ):
            references.setdefault(
                resolved, skill / resolved.relative_to(skill.resolve())
            )
    for path in references.values():
        reference_lines = path.read_text(encoding="utf-8").splitlines()
        findings += check_document(
            skill, path, prose_lines(reference_lines, 0), is_skill_md=False
        )
        findings += check_contents(path, reference_lines)
    return sorted(findings, key=lambda f: (str(f.path), f.line, f.bp, f.message))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = Parser(
        prog=PROG,
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "folders",
        nargs="+",
        type=Path,
        metavar="SKILL_FOLDER",
        help="a folder holding SKILL.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        findings = [finding for folder in args.folders for finding in validate(folder)]
    except UsageError as error:
        print(f"usage: {PROG} SKILL_FOLDER [SKILL_FOLDER ...]", file=sys.stderr)
        print(f"{PROG}: error: {error}", file=sys.stderr)
        print(f"run '{PROG} --help'", file=sys.stderr)
        return 2
    for finding in findings:
        print(finding)
    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())

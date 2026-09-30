#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the andy-mode route table and every bundled path it reaches."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

EPILOG = """\
Checks that each route in SKILL.md names one playbook, that route names stay
unique once case, spaces, hyphens, and underscores are ignored, that SKILL.md
exists only at the root, and that every relative link, anchor, and bundled
path in the package resolves. Success prints nothing.

exit codes:
  0  the package is valid
  1  a check failed; each problem is one line on stderr
  2  usage error

examples:
  uv run authoring/andy/andy-mode/scripts/check_andy_mode.py
  uv run authoring/andy/andy-mode/scripts/check_andy_mode.py /tmp/andy-mode-copy"""

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
EXTERNAL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ROUTE_CELL_RE = re.compile(r"^\[`([^`]+)`\]\(([^)\s]+)\)$")
ALIAS_RE = re.compile(r"`([^`]+)`")
PLACEHOLDER_CHARS = set("<>*{}$")


@dataclass(frozen=True)
class Route:
    family: str
    name: str
    aliases: tuple[str, ...]
    target: PurePosixPath


def normalize(name: str) -> str:
    """Fold a route name the way the router matches it."""
    return re.sub(r"[\s_-]+", "", name).lower()


def prose_lines(text: str) -> list[str]:
    """Return the lines outside fenced code blocks."""
    lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if fence is not None:
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
        lines.append(line)
    return lines


def split_code(line: str) -> tuple[str, list[str]]:
    """Return the line with code spans blanked, and the code span contents."""
    spans = [match.group(2).strip() for match in CODE_SPAN_RE.finditer(line)]
    return CODE_SPAN_RE.sub(" ", line), spans


def anchor_slug(heading: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "")
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for line in prose_lines(path.read_text(encoding="utf-8")):
        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = anchor_slug(match.group(2))
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        found.add(slug if seen == 0 else f"{slug}-{seen}")
    return found


def parse_routes(skill: Path, errors: list[str]) -> list[Route]:
    """Read every table row whose first cell links a route, grouped by `###` family."""
    routes: list[Route] = []
    family = ""
    for line in prose_lines(skill.read_text(encoding="utf-8")):
        if line.startswith("### "):
            family = line[4:].strip()
            continue
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        match = ROUTE_CELL_RE.match(cells[0])
        if not match:
            continue
        if not family:
            errors.append(f"SKILL.md: route {match.group(1)} has no family heading")
        aliases = tuple(ALIAS_RE.findall(cells[1])) if len(cells) > 1 else ()
        routes.append(
            Route(family, match.group(1), aliases, PurePosixPath(match.group(2)))
        )
    if not routes:
        errors.append("SKILL.md: no route table rows found")
    return routes


def check_routes(root: Path, routes: list[Route], errors: list[str]) -> None:
    owners: dict[str, str] = {}
    for route in routes:
        for name in (route.name, *route.aliases):
            key = normalize(name)
            if key in owners and owners[key] != route.name:
                errors.append(
                    f"SKILL.md: {name!r} matches both {owners[key]} and {route.name}"
                )
            owners.setdefault(key, route.name)
        playbook = PurePosixPath("playbooks", f"{route.name}.md")
        shared = PurePosixPath("..", route.name, "SKILL.md")
        if route.target not in (playbook, shared):
            errors.append(
                f"SKILL.md: route {route.name} must target {playbook} or {shared}, "
                f"not {route.target}"
            )
        elif not (root / route.target).is_file():
            errors.append(
                f"SKILL.md: route {route.name} target is missing: {route.target}"
            )

    routed = {
        route.target.name for route in routes if route.target.parent.name == "playbooks"
    }
    for playbook in sorted((root / "playbooks").glob("*.md")):
        if playbook.name not in routed:
            errors.append(f"playbooks/{playbook.name}: no route in SKILL.md reaches it")


def in_sibling_skill(target: Path, parent: Path) -> bool:
    """Whether a path sits inside a skill package next to andy-mode."""
    if not target.is_relative_to(parent):
        return False
    top = target.relative_to(parent).parts[:1]
    return bool(top) and (parent / top[0] / "SKILL.md").is_file()


def check_paths(root: Path, route_names: set[str], errors: list[str]) -> None:
    """Resolve relative links, their anchors, and bundled paths named in code spans."""
    home = root.resolve()
    anchor_cache: dict[Path, set[str]] = {}
    bundled = (
        "playbooks/",
        "scripts/",
        *(f"references/{name}/" for name in route_names),
    )
    for path in sorted(root.rglob("*.md")):
        label = path.relative_to(root).as_posix()
        for line in prose_lines(path.read_text(encoding="utf-8")):
            prose, spans = split_code(line)
            for raw in LINK_RE.findall(prose):
                if raw.startswith("//") or EXTERNAL_RE.match(raw):
                    continue
                # Quoted examples, such as chat-export artifacts, are not paths
                if PLACEHOLDER_CHARS & set(raw) or '"' in raw:
                    continue
                part, _, anchor = unquote(raw).partition("#")
                target = (path.parent / part).resolve() if part else path.resolve()
                if not target.is_relative_to(home) and not in_sibling_skill(
                    target, home.parent
                ):
                    errors.append(f"{label}: link leaves andy-mode: {raw}")
                    continue
                if not target.exists():
                    errors.append(f"{label}: unresolved link: {raw}")
                    continue
                if anchor and target.suffix == ".md":
                    if target not in anchor_cache:
                        anchor_cache[target] = anchors(target)
                    if anchor_slug(anchor) not in anchor_cache[target]:
                        errors.append(f"{label}: unresolved anchor: {raw}")
            for span in spans:
                token = span.partition("#")[0]
                if " " in token or PLACEHOLDER_CHARS & set(token):
                    continue
                if token.startswith(bundled) and not (root / token).exists():
                    errors.append(f"{label}: unresolved bundled path: {span}")


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return [f"{root}: SKILL.md is missing"]
    for nested in sorted(root.rglob("SKILL.md")):
        if nested != skill:
            errors.append(
                f"{nested.relative_to(root)}: only the root may be named SKILL.md"
            )
    routes = parse_routes(skill, errors)
    check_routes(root, routes, errors)
    names = {route.name for route in routes}
    names |= {path.stem for path in (root / "playbooks").glob("*.md")}
    check_paths(root, names, errors)
    return errors


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\nrun '{self.prog} --help'\n")
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="check_andy_mode.py",
        description=__doc__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="andy-mode package directory (default: this script's package)",
    )
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        parser.error(f"not a directory: {args.root}")
    errors = validate(args.root)
    for error in errors:
        sys.stderr.write(f"{error}\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

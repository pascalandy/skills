#!/usr/bin/env python3
"""Validate a scanner-safe, portable meta-skill layout."""

from __future__ import annotations

import argparse
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

FRONTMATTER_DELIMITER = "---"
LINK_START_RE = re.compile(r"!?\[(?:\\.|[^\]\\])*\]\(")
FENCE_START_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")
ROUTER_DESTINATION_CELL_RE = re.compile(r"^`(?P<path>[^`]+/MetaSkill\.md)`$")
ROUTER_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
EXTERNAL_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
FORBIDDEN_INSTALL_ROOT_RES = (
    re.compile(
        r"(?:~|\$HOME|\$\{HOME\}|/Users/[^/\s`]+|/home/[^/\s`]+|/root)/"
        r"(?:\.claude/skills|\.config/opencode/skills?|\.pi/agent/skills|"
        r"\.agents/skills|\.codex/skills|\.gemini/skills|\.config/amp/skills|"
        r"\.config/agents/skills|\.factory/skills)(?:/|\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:%USERPROFILE%|[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s`]+)[\\/]+"
        r"(?:\.claude[\\/]skills|\.config[\\/]opencode[\\/]skills?|"
        r"\.pi[\\/]agent[\\/]skills|\.agents[\\/]skills|\.codex[\\/]skills|"
        r"\.gemini[\\/]skills|\.config[\\/]amp[\\/]skills|"
        r"\.config[\\/]agents[\\/]skills|\.factory[\\/]skills)(?:[\\/]|\b)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:\$CODEX_HOME|\$\{CODEX_HOME\})[\\/]+skills(?:[\\/]|\b)"),
)


def relative_label(path: Path, root: Path) -> str:
    """Return a stable path label relative to the validated root."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_utf8(path: Path, label: str, errors: list[str]) -> str | None:
    """Read one required UTF-8 text file without leaking a traceback."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        errors.append(f"{label}: file is not valid UTF-8: {error}")
    except OSError as error:
        errors.append(f"{label}: cannot read file: {error}")
    return None


def split_frontmatter_text(
    text: str, label: str, errors: list[str]
) -> tuple[list[str], list[str]]:
    """Split a required, non-empty frontmatter block from an instruction body."""
    lines = text.splitlines()
    if not lines or lines[0] != FRONTMATTER_DELIMITER:
        errors.append(f"{label}: missing opening frontmatter delimiter")
        return [], []

    try:
        closing_index = lines.index(FRONTMATTER_DELIMITER, 1)
    except ValueError:
        errors.append(f"{label}: missing closing frontmatter delimiter")
        return lines[1:], []

    frontmatter = lines[1:closing_index]
    if not any(line.strip() for line in frontmatter):
        errors.append(f"{label}: frontmatter must not be empty")
    return frontmatter, lines[closing_index + 1 :]


def validate_instruction_file(
    path: Path,
    label: str,
    errors: list[str],
    *,
    require_router_bridge: bool = False,
) -> list[str]:
    """Require skill frontmatter, a body, and the root router bridge."""
    if not path.is_file() or path.is_symlink():
        return []

    text = read_utf8(path, label, errors)
    if text is None:
        return []
    frontmatter, body = split_frontmatter_text(text, label, errors)

    for required_key in ("name", "description"):
        matches = [
            match
            for line in frontmatter
            if (match := re.match(rf"^{required_key}:\s*(?P<value>.*)$", line))
        ]
        if not matches:
            errors.append(
                f"{label}: frontmatter is missing a non-empty {required_key} field"
            )
        elif len(matches) > 1:
            errors.append(
                f"{label}: frontmatter contains duplicate {required_key} fields"
            )
        else:
            value = matches[0].group("value").strip()
            if not value or value.startswith("#"):
                errors.append(
                    f"{label}: frontmatter is missing a non-empty {required_key} field"
                )

    if not any(line.strip() for line in body):
        errors.append(f"{label}: instruction body must not be empty")
    if require_router_bridge and "references/ROUTER.md" not in "\n".join(body):
        errors.append(
            f"{label}: root collection must direct readers to references/ROUTER.md"
        )
    return body


def split_router_row(row: str) -> list[str] | None:
    """Split a Markdown table row while preserving escaped and code-span pipes."""
    if not row.startswith("|") or not row.endswith("|"):
        return None

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    code_delimiter = ""
    content = row[1:-1]
    index = 0
    while index < len(content):
        character = content[index]
        if escaped:
            current.append(character)
            escaped = False
            index += 1
        elif character == "\\":
            current.append(character)
            escaped = True
            index += 1
        elif character == "`":
            run_end = index
            while run_end < len(content) and content[run_end] == "`":
                run_end += 1
            delimiter = content[index:run_end]
            current.append(delimiter)
            if not code_delimiter:
                code_delimiter = delimiter
            elif delimiter == code_delimiter:
                code_delimiter = ""
            index = run_end
        elif character == "|" and not code_delimiter:
            cells.append("".join(current).strip())
            current = []
            index += 1
        else:
            current.append(character)
            index += 1
    cells.append("".join(current).strip())
    return cells


def safe_posix_relative_path(value: str) -> PurePosixPath | None:
    """Return a portable, traversal-free POSIX path, or None when unsafe."""
    if not value or value in {".", ".."} or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return None
    return path


def markdown_posix_path(value: str) -> PurePosixPath | None:
    """Return a portable Markdown path; containment is checked after joining."""
    if not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts:
        return None
    return path


def local_path(root: Path, relative_path: PurePosixPath) -> Path:
    """Join a portable relative path to a local filesystem root."""
    return root.joinpath(*relative_path.parts)


def parse_router(root: Path, errors: list[str]) -> set[PurePosixPath]:
    """Validate the strict router table and return its mode destinations."""
    router = root / "references" / "ROUTER.md"
    if not router.is_file() or router.is_symlink():
        errors.append("references/ROUTER.md: required router is missing")
        return set()

    body = [
        line.strip()
        for line in validate_instruction_file(router, "references/ROUTER.md", errors)
        if line.strip()
    ]
    if len(body) < 5:
        errors.append(
            "references/ROUTER.md: expected a title, Routing heading, and routing table"
        )
        return set()
    if not re.fullmatch(r"# [^#].*", body[0]):
        errors.append("references/ROUTER.md: first body line must be one H1 title")
    if body[1] != "## Routing":
        errors.append("references/ROUTER.md: second body line must be '## Routing'")

    table_lines = body[2:]
    parsed_rows = [split_router_row(line) for line in table_lines]
    if any(row is None for row in parsed_rows):
        errors.append(
            "references/ROUTER.md: body must contain only the title, Routing heading, and table"
        )
        return set()
    rows = [row for row in parsed_rows if row is not None]
    header = rows[0]
    valid_headers = (
        ["Request Pattern", "Route To"],
        ["Precedence", "Request Pattern", "Route To"],
    )
    if header not in valid_headers:
        errors.append(
            "references/ROUTER.md: table header must be 'Request Pattern | Route To' "
            "or 'Precedence | Request Pattern | Route To'"
        )
    column_count = len(header)
    separator = rows[1]
    if len(separator) != column_count or not all(
        ROUTER_SEPARATOR_CELL_RE.fullmatch(cell) for cell in separator
    ):
        errors.append(
            "references/ROUTER.md: second table row must be a Markdown separator"
        )

    destinations: set[PurePosixPath] = set()
    precedence_values: list[int] = []
    for row_number, row in enumerate(rows[2:], start=1):
        if len(row) != column_count:
            errors.append(
                f"references/ROUTER.md: routing row {row_number} has {len(row)} columns; "
                f"expected {column_count}"
            )
            continue

        if header == valid_headers[1]:
            try:
                precedence = int(row[0])
            except ValueError:
                errors.append(
                    f"references/ROUTER.md: routing row {row_number} precedence must be an integer"
                )
            else:
                if precedence < 1:
                    errors.append(
                        f"references/ROUTER.md: routing row {row_number} precedence must be positive"
                    )
                precedence_values.append(precedence)
            request_pattern = row[1]
        else:
            request_pattern = row[0]
        if not request_pattern:
            errors.append(
                f"references/ROUTER.md: routing row {row_number} has an empty pattern"
            )

        destination_match = ROUTER_DESTINATION_CELL_RE.fullmatch(row[-1])
        if not destination_match:
            errors.append(
                "references/ROUTER.md: "
                f"routing row {row_number} Route To cell must contain only one backticked "
                "<Mode>/MetaSkill.md destination"
            )
            continue
        destination = safe_posix_relative_path(destination_match.group("path"))
        if destination is None or len(destination.parts) != 2:
            errors.append(
                f"references/ROUTER.md: unsafe router destination: "
                f"{destination_match.group('path')}"
            )
            continue
        if destination in destinations:
            errors.append(
                f"references/ROUTER.md: duplicate router destination: {destination.as_posix()}"
            )
            continue
        destinations.add(destination)
        destination_path = local_path(root / "references", destination)
        if not destination_path.is_file() or destination_path.is_symlink():
            errors.append(
                f"references/ROUTER.md: destination does not exist: {destination.as_posix()}"
            )

    if precedence_values and precedence_values != sorted(set(precedence_values)):
        errors.append(
            "references/ROUTER.md: precedence values must be unique and strictly increasing"
        )
    return destinations


def validate_root_anatomy(root: Path, errors: list[str]) -> None:
    """Validate collection and scanner anatomy."""
    expected_entries = {"SKILL.md", "references"}
    actual_entries = {path.name for path in root.iterdir()}
    for unexpected in sorted(actual_entries - expected_entries):
        errors.append(f"root contains forbidden entry: {unexpected}")
    for missing in sorted(expected_entries - actual_entries):
        errors.append(f"root is missing required entry: {missing}")

    skill = root / "SKILL.md"
    if not skill.is_file() or skill.is_symlink():
        errors.append("SKILL.md: root entrypoint is missing")
    else:
        validate_instruction_file(skill, "SKILL.md", errors, require_router_bridge=True)
    if not (root / "references").is_dir() or (root / "references").is_symlink():
        errors.append("references: required directory is missing")

    scanner_files = sorted(path for path in root.rglob("SKILL.md") if path.is_file())
    if scanner_files != [skill]:
        labels = (
            ", ".join(relative_label(path, root) for path in scanner_files) or "none"
        )
        errors.append(f"expected exactly one root SKILL.md; found: {labels}")


def validate_no_symlinks(root: Path, errors: list[str]) -> bool:
    """Reject symlinks so validation cannot read or route outside the root."""
    symlinks = sorted(path for path in root.rglob("*") if path.is_symlink())
    for path in symlinks:
        errors.append(
            f"{relative_label(path, root)}: symlinks are forbidden in meta-skills"
        )
    return not symlinks


def validate_modes(
    root: Path, routed_destinations: set[PurePosixPath], errors: list[str]
) -> int:
    """Validate mode roots and router coverage."""
    references = root / "references"
    if not references.is_dir() or references.is_symlink():
        return 0

    mode_dirs = sorted(
        path for path in references.iterdir() if path.is_dir() and not path.is_symlink()
    )
    mode_destinations = {
        PurePosixPath(path.name) / "MetaSkill.md" for path in mode_dirs
    }

    for missing_route in sorted(mode_destinations - routed_destinations):
        errors.append(
            f"references/ROUTER.md: mode is not routed: {missing_route.as_posix()}"
        )
    for extra_route in sorted(routed_destinations - mode_destinations):
        errors.append(
            f"references/ROUTER.md: route has no mode root: {extra_route.as_posix()}"
        )

    for mode_dir in mode_dirs:
        actual_entries = {path.name for path in mode_dir.iterdir()}
        allowed_entries = {"MetaSkill.md", "references"}
        for unexpected in sorted(actual_entries - allowed_entries):
            errors.append(
                f"references/{mode_dir.name}: mode root contains forbidden entry: {unexpected}"
            )
        meta_skill = mode_dir / "MetaSkill.md"
        if not meta_skill.is_file() or meta_skill.is_symlink():
            errors.append(
                f"references/{mode_dir.name}/MetaSkill.md: required mode file is missing"
            )
        else:
            validate_instruction_file(
                meta_skill, f"references/{mode_dir.name}/MetaSkill.md", errors
            )
        mode_references = mode_dir / "references"
        if mode_references.exists() and (
            not mode_references.is_dir() or mode_references.is_symlink()
        ):
            errors.append(
                f"references/{mode_dir.name}/references: expected a directory"
            )

    return len(mode_dirs)


def strip_inline_code(line: str) -> str:
    """Mask complete inline-code spans before scanning Markdown links."""
    characters = list(line)
    index = 0
    while index < len(line):
        if line[index] != "`":
            index += 1
            continue
        run_end = index
        while run_end < len(line) and line[run_end] == "`":
            run_end += 1
        delimiter = line[index:run_end]
        close = line.find(delimiter, run_end)
        if close < 0:
            index = run_end
            continue
        for position in range(index, close + len(delimiter)):
            characters[position] = " "
        index = close + len(delimiter)
    return "".join(characters)


def markdown_prose(text: str) -> str:
    """Return Markdown with fenced and inline code masked."""
    output: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in text.splitlines():
        if fence_character:
            closing = re.match(
                rf"^\s*{re.escape(fence_character)}{{{fence_length},}}\s*$", line
            )
            if closing:
                fence_character = ""
                fence_length = 0
            output.append("")
            continue

        opening = FENCE_START_RE.match(line)
        if opening:
            fence = opening.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            output.append("")
            continue
        output.append(strip_inline_code(line))
    return "\n".join(output)


def markdown_link_targets(text: str) -> list[str]:
    """Extract inline Markdown link and image destinations from prose."""
    prose = markdown_prose(text)
    targets: list[str] = []
    for match in LINK_START_RE.finditer(prose):
        index = match.end()
        while index < len(prose) and prose[index].isspace():
            index += 1
        if index < len(prose) and prose[index] == "<":
            start = index + 1
            index = start
            escaped = False
            while index < len(prose):
                character = prose[index]
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == ">":
                    targets.append(prose[start:index])
                    break
                index += 1
            continue

        start = index
        depth = 0
        escaped = False
        while index < len(prose):
            character = prose[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    targets.append(prose[start:index])
                    break
                depth -= 1
            elif character.isspace() and depth == 0:
                targets.append(prose[start:index])
                break
            index += 1
    return targets


def github_anchor_slug(value: str) -> str:
    """Normalize a heading or fragment to the validator's GitHub-style slug."""
    heading = re.sub(r"[`*_~]", "", value).strip().lower()
    return re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")


def heading_anchors(path: Path, label: str, errors: list[str]) -> set[str]:
    """Return approximate GitHub-style anchors for Markdown headings."""
    text = read_utf8(path, label, errors)
    if text is None:
        return set()
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for line in markdown_prose(text).splitlines():
        match = re.match(r"^\s*#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        slug = github_anchor_slug(match.group(1))
        duplicate_count = counts.get(slug, 0)
        counts[slug] = duplicate_count + 1
        anchors.add(slug if duplicate_count == 0 else f"{slug}-{duplicate_count}")
    return anchors


def validate_markdown_links(root: Path, errors: list[str]) -> int:
    """Require portable local Markdown file and anchor targets to resolve."""
    link_count = 0
    anchor_cache: dict[Path, set[str]] = {}
    resolved_root = root.resolve()
    for markdown_path in sorted(root.rglob("*.md")):
        label = relative_label(markdown_path, root)
        text = read_utf8(markdown_path, label, errors)
        if text is None:
            continue
        for raw_target in markdown_link_targets(text):
            target = re.sub(r"\\([\\`()\[\]<>])", r"\1", raw_target)
            if WINDOWS_ABSOLUTE_RE.match(target):
                errors.append(f"{label}: unsafe absolute Markdown link: {raw_target}")
                continue
            if target.startswith("//") or EXTERNAL_SCHEME_RE.match(target):
                continue
            link_count += 1
            path_part, separator, anchor = target.partition("#")
            decoded_path = unquote(path_part)
            if decoded_path:
                relative_target = markdown_posix_path(decoded_path)
                if relative_target is None:
                    errors.append(f"{label}: unsafe Markdown link: {raw_target}")
                    continue
                target_path = local_path(markdown_path.parent, relative_target)
            else:
                target_path = markdown_path

            resolved_target = target_path.resolve(strict=False)
            try:
                resolved_target.relative_to(resolved_root)
            except ValueError:
                errors.append(
                    f"{label}: unsafe Markdown link escapes meta-skill root: {raw_target}"
                )
                continue
            if not target_path.exists():
                errors.append(f"{label}: unresolved Markdown link: {raw_target}")
                continue
            if (
                separator
                and anchor
                and target_path.is_file()
                and target_path.suffix.lower() == ".md"
            ):
                normalized_anchor = github_anchor_slug(unquote(anchor))
                if target_path not in anchor_cache:
                    anchor_cache[target_path] = heading_anchors(
                        target_path, relative_label(target_path, root), errors
                    )
                if normalized_anchor not in anchor_cache[target_path]:
                    errors.append(f"{label}: unresolved Markdown anchor: {raw_target}")
    return link_count


def validate_portability(root: Path, errors: list[str]) -> None:
    """Reject bundled references to harness-specific skill install roots."""
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as error:
            errors.append(f"{relative_label(path, root)}: cannot read file: {error}")
            continue
        for pattern in FORBIDDEN_INSTALL_ROOT_RES:
            for match in pattern.finditer(text):
                errors.append(
                    f"{relative_label(path, root)}: forbidden harness-specific install root: "
                    f"{match.group(0)}"
                )


def validate_exclusive_siblings(
    root: Path, prefixes: list[str], errors: list[str]
) -> None:
    """Reject sibling directories reserved by the umbrella."""
    for prefix in sorted(set(prefixes)):
        for sibling in sorted(root.parent.iterdir()):
            if sibling.is_dir() and sibling != root and sibling.name.startswith(prefix):
                errors.append(
                    f"forbidden sibling directory matching prefix '{prefix}': {sibling.name}"
                )


def validate_asset_modes(
    root: Path,
    expected_executable: list[PurePosixPath],
    expected_non_executable: list[PurePosixPath],
    errors: list[str],
) -> int:
    """Validate chezmoi executable markers and explicitly declared asset modes."""
    executable_count = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        try:
            is_executable = bool(stat.S_IMODE(path.stat().st_mode) & 0o111)
        except OSError as error:
            errors.append(
                f"{relative_label(path, root)}: cannot inspect file mode: {error}"
            )
            continue
        if is_executable:
            executable_count += 1
        if path.name.startswith("executable_") and not is_executable:
            errors.append(
                f"{relative_label(path, root)}: executable_ source asset lacks an executable mode"
            )
        if path.suffix.lower() == ".md" and is_executable:
            errors.append(
                f"{relative_label(path, root)}: Markdown files must not be executable"
            )

    for relative_path in expected_executable:
        path = local_path(root, relative_path)
        if not path.is_file() or path.is_symlink():
            errors.append(
                f"expected executable asset is missing: {relative_path.as_posix()}"
            )
        elif not stat.S_IMODE(path.stat().st_mode) & 0o111:
            errors.append(
                f"expected executable asset is not executable: {relative_path.as_posix()}"
            )

    for relative_path in expected_non_executable:
        path = local_path(root, relative_path)
        if not path.is_file() or path.is_symlink():
            errors.append(
                f"expected non-executable asset is missing: {relative_path.as_posix()}"
            )
        elif stat.S_IMODE(path.stat().st_mode) & 0o111:
            errors.append(
                f"expected non-executable asset has an executable mode: {relative_path.as_posix()}"
            )
    return executable_count


def parse_relative_paths(
    values: list[str], option: str, parser: argparse.ArgumentParser
) -> list[PurePosixPath]:
    """Parse safe, portable root-relative CLI paths."""
    paths: list[PurePosixPath] = []
    for value in values:
        path = safe_posix_relative_path(value)
        if path is None:
            parser.error(f"{option} requires a portable path relative to ROOT: {value}")
        paths.append(path)
    return paths


def parse_exclusive_prefixes(
    values: list[str], parser: argparse.ArgumentParser
) -> list[str]:
    """Reject empty or path-shaped sibling prefixes."""
    for value in values:
        if (
            not value
            or value.strip() != value
            or value in {".", ".."}
            or "/" in value
            or "\\" in value
        ):
            parser.error(
                f"--exclusive-sibling-prefix requires a non-empty name prefix: {value!r}"
            )
    return values


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate meta-skill anatomy, routing, portability, links, exclusivity, "
            "and asset modes."
        )
    )
    parser.add_argument(
        "root", type=Path, metavar="ROOT", help="meta-skill root directory"
    )
    parser.add_argument(
        "--exclusive-sibling-prefix",
        action="append",
        default=[],
        metavar="PREFIX",
        help="reject sibling directories whose names start with PREFIX; repeatable",
    )
    parser.add_argument(
        "--expected-mode-count",
        type=int,
        metavar="COUNT",
        help="require exactly COUNT immediate mode directories under references/",
    )
    parser.add_argument(
        "--expect-executable",
        action="append",
        default=[],
        metavar="PATH",
        help="require a portable root-relative asset to exist and be executable; repeatable",
    )
    parser.add_argument(
        "--expect-non-executable",
        action="append",
        default=[],
        metavar="PATH",
        help="require a portable root-relative asset to exist without executable bits; repeatable",
    )
    return parser


def main() -> int:
    """Run all validation checks and return a conventional process status."""
    parser = build_parser()
    args = parser.parse_args()
    root: Path = args.root
    prefixes = parse_exclusive_prefixes(args.exclusive_sibling_prefix, parser)
    expected_executable = parse_relative_paths(
        args.expect_executable, "--expect-executable", parser
    )
    expected_non_executable = parse_relative_paths(
        args.expect_non_executable, "--expect-non-executable", parser
    )
    overlap = sorted(set(expected_executable) & set(expected_non_executable))
    if overlap:
        parser.error(
            "the same path cannot be both executable and non-executable: "
            + ", ".join(path.as_posix() for path in overlap)
        )
    if args.expected_mode_count is not None and args.expected_mode_count < 1:
        parser.error("--expected-mode-count must be at least 1")

    errors: list[str] = []
    mode_count = 0
    link_count = 0
    executable_count = 0
    if root.is_symlink():
        errors.append(f"meta-skill root must not be a symlink: {root.as_posix()}")
    elif not root.is_dir():
        errors.append(f"meta-skill root is not a directory: {root.as_posix()}")
    elif validate_no_symlinks(root, errors):
        try:
            validate_root_anatomy(root, errors)
            routed_destinations = parse_router(root, errors)
            mode_count = validate_modes(root, routed_destinations, errors)
            if (
                args.expected_mode_count is not None
                and mode_count != args.expected_mode_count
            ):
                errors.append(
                    f"expected {args.expected_mode_count} mode roots under references/; "
                    f"found {mode_count}"
                )
            link_count = validate_markdown_links(root, errors)
            validate_portability(root, errors)
            validate_exclusive_siblings(root, prefixes, errors)
            executable_count = validate_asset_modes(
                root, expected_executable, expected_non_executable, errors
            )
        except OSError as error:
            errors.append(
                f"filesystem error while validating {root.as_posix()}: {error}"
            )

    if errors:
        print(f"ERROR: meta-skill layout invalid: {root.as_posix()}", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"OK: meta-skill layout valid: {root.as_posix()} "
        f"(modes={mode_count}, scanner_skills=1, links={link_count}, "
        f"executables={executable_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

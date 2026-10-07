#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compile authoring packages into the published skills directory."""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import shutil
import stat
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from _cli import Parser, ScriptError, exit_codes
from _common import (
    FRONTMATTER,
    KINDS,
    UNKNOWN,
    frontmatter_value,
    kind_of,
    run,
    run_script,
    swap,
)

ROOT = Path(__file__).resolve().parent.parent
AUTHORING = ROOT / "authoring"
OUTPUT = ROOT / "skills"
COUNT = Path("docs/references/skill-count.md")
TOP_LEVEL = "(top level)"

EPILOG = """\
A run answers {"ok":true,"changes":[...]}, one [action, path] per skill it
changes, such as ["update","skills/andy-mode"], and {"ok":true} when nothing
changes. It also writes docs/references/skill-count.md, the skills per
category and kind, and lists that page when it changes. A dry run answers the
same and changes nothing; --check fails when a change is pending, with the
changes beside the error.

examples:
  just compile-skills
  just compile-skills --dry-run
  just compile-skills --check
  just compile-skills --verbose"""

EXIT_CODES = exit_codes(
    {
        0: "skills/ matches authoring/, or now does",
        1: "compile failed, or --check found changes",
    }
)

log = logging.getLogger("compile-skills")


def git(*args: str) -> bytes:
    """Run git in the repository and return its stdout."""
    executable = shutil.which("git")
    if executable is None:
        raise ScriptError("git not found on PATH; install git and rerun")
    result = run(
        [executable, *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    log.debug("git %s: exit %d", shlex.join(args), result.returncode)
    if result.returncode != 0:
        raise ScriptError(f"git {args[0]} failed: {result.stderr.decode().strip()}")
    return result.stdout


def git_files(directory: str) -> list[Path]:
    """List tracked and non-ignored untracked paths in a repository directory."""
    listed = git(
        "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", directory
    )
    return [Path(os.fsdecode(path)) for path in listed.split(b"\0") if path]


def collect() -> dict[str, list[tuple[Path, Path]]]:
    """Map each skill to the source files that compiling would copy.

    A package is a folder holding a SKILL.md, either directly under authoring/
    or inside a category folder there."""
    packages: dict[str, Path] = {}
    for entry in sorted(
        [*AUTHORING.glob("*/SKILL.md"), *AUTHORING.glob("*/*/SKILL.md")]
    ):
        package = entry.parent
        # The inner folder could be a skill or part of the outer one, so refuse to guess
        if package.parent != AUTHORING and (package.parent / "SKILL.md").is_file():
            raise ScriptError(
                f"{package.relative_to(ROOT)} is a package inside the package "
                f"{package.parent.relative_to(ROOT)}; move one of them"
            )
        if package.name in packages:
            raise ScriptError(
                f"duplicate skill name {package.name!r}: "
                f"{packages[package.name].relative_to(ROOT)} and {package.relative_to(ROOT)}; "
                "rename one package"
            )
        packages[package.name] = package

    if not packages:
        raise ScriptError(
            "no skill packages found at authoring/<skill>/SKILL.md "
            "or authoring/<category>/<skill>/SKILL.md"
        )
    files: dict[str, list[tuple[Path, Path]]] = {name: [] for name in packages}
    roots = set(packages.values())
    unpackaged: set[str] = set()
    for relative in git_files("authoring"):
        source = ROOT / relative
        if not (source.is_file() or source.is_symlink()):
            log.debug("skip %s (not a file)", relative)
            continue
        package = next((parent for parent in source.parents if parent in roots), None)
        if package is None:
            unpackaged.add(
                relative.as_posix()
                if len(relative.parts) <= 3
                else f"{Path(*relative.parts[:3]).as_posix()}/"
            )
            continue

        if source.is_symlink():
            raise ScriptError(
                f"skill source symlink is unsupported: {relative}; replace it with a file"
            )
        files[package.name].append((source, source.relative_to(package)))

    if unpackaged:
        raise ScriptError(
            f"files outside a skill package: {', '.join(sorted(unpackaged))}; "
            "add a SKILL.md or move them into a package"
        )
    for name, package in packages.items():
        if not any(relative == Path("SKILL.md") for _, relative in files[name]):
            raise ScriptError(
                f"skill entry point is missing or git-ignored: {package.relative_to(ROOT)}/SKILL.md"
            )
        log.debug("%s: %d files", package.relative_to(AUTHORING), len(files[name]))

    return files


def render(source: Path, inside: Path) -> bytes:
    """The bytes skills/ publishes for the package file at `inside`. A package's
    own SKILL.md without a kind gains `kind: "unknown"` at the end of its
    frontmatter, so a skill nobody classified shows up without failing a check."""
    data = source.read_bytes()
    if inside != Path("SKILL.md"):
        return data
    # Match CRLF sources too; a copy that gains the kind is published with LF
    text = data.decode("utf-8").replace("\r\n", "\n")
    header = FRONTMATTER.match(text)
    if header is None or frontmatter_value(text, "kind") is not None:
        return data
    end = header.end(1)
    return f'{text[:end]}\nkind: "{UNKNOWN}"{text[end:]}'.encode()


def publish(source: Path, inside: Path, destination: Path) -> None:
    """Write the bytes and executable bits skills/ publishes for a source file."""
    destination.write_bytes(render(source, inside))
    shutil.copymode(source, destination)


def build_expected() -> dict[Path, Path]:
    """Map each generated path to the source file that supplies its bytes and mode."""
    return {
        Path("skills") / name / relative: source
        for name, entries in collect().items()
        for source, relative in entries
    }


def changes(expected: dict[Path, Path]) -> list[list[str]]:
    """One [action, skills/<name>] per skill whose generated copy differs."""
    actual = {
        path
        for path in git_files("skills")
        if (ROOT / path).is_file() or (ROOT / path).is_symlink()
    }
    stale: dict[str, str] = {}
    for relative, source in sorted(expected.items()):
        destination = ROOT / relative
        if relative not in actual:
            reason = "missing file"
        elif any(
            parent.is_symlink()
            for parent in (destination, *destination.parents)
            if parent.is_relative_to(OUTPUT)
        ):
            reason = "symlink"
        elif render(source, Path(*relative.parts[2:])) != destination.read_bytes():
            reason = "changed content"
        elif (stat.S_IMODE(source.stat().st_mode) & 0o111) != (
            stat.S_IMODE(destination.stat().st_mode) & 0o111
        ):
            reason = "executable bit changed"
        else:
            continue
        log.info("%s: %s", relative, reason)
        stale[relative.parts[1]] = reason
    for relative in sorted(actual - expected.keys()):
        log.info(
            "%s: %s",
            relative,
            "symlink" if (ROOT / relative).is_symlink() else "extra file",
        )
        stale[relative.parts[1]] = "extra file"
    present = {path.parts[1] for path in actual}
    wanted = {path.parts[1] for path in expected}
    return [
        [
            "add"
            if name not in present
            else "remove"
            if name not in wanted
            else "update",
            f"skills/{name}",
        ]
        for name in sorted(stale)
    ]


def count_page(expected: dict[Path, Path], compiled: int) -> str:
    """The skill-count page: skills per authoring/ category and kind, then the
    authoring/ total beside the `compiled` count of skills/."""
    columns = (*KINDS, UNKNOWN)
    counts: dict[str, Counter[str]] = {}
    for relative, source in expected.items():
        if relative.parts[2:] != ("SKILL.md",):
            continue
        package = source.parent
        category = TOP_LEVEL if package.parent == AUTHORING else package.parent.name
        kind = kind_of(source.read_text(encoding="utf-8"))
        counts.setdefault(category, Counter())[kind] += 1
    total = sum(counts.values(), Counter())
    order = sorted(counts, key=lambda category: (category == TOP_LEVEL, category))

    def row(label: str, counter: Counter[str]) -> str:
        cells = [counter[kind] for kind in columns]
        return f"| {label} | {' | '.join(map(str, cells))} | {sum(cells)} |\n"

    return (
        "---\nname: skill-count\n"
        "description: How many skills authoring/ holds, by category and kind\n---\n\n"
        "<!-- Generated from authoring/ by `just compile-skills`; do not edit -->\n\n"
        f"| Category | {' | '.join(kind.capitalize() for kind in columns)} | Total |\n"
        f"|---|{'---|' * (len(columns) + 1)}\n"
        + "".join(row(category, counts[category]) for category in order)
        + row("**Total**", total)
        + f"\nauthoring {total.total()} · skills {compiled}\n"
    )


def compile_tree(*, dry_run: bool = False) -> list[list[str]]:
    """Rebuild skills/ and the skill-count page from authoring/ when they
    differ; return one change per skill or page, and change nothing on a dry
    run."""
    if OUTPUT.is_symlink() or (OUTPUT.exists() and not OUTPUT.is_dir()):
        raise ScriptError(
            "skills/ must be a directory, not a file or symlink; "
            "move it aside, then rerun just compile-skills"
        )
    expected = build_expected()
    lines = changes(expected)
    if lines and not dry_run:
        with tempfile.TemporaryDirectory(
            prefix=".skills-compile-", dir=ROOT
        ) as temporary:
            staging = Path(temporary) / "skills"
            staging.mkdir()
            for relative, source in expected.items():
                destination = staging / relative.relative_to("skills")
                destination.parent.mkdir(parents=True, exist_ok=True)
                publish(source, Path(*relative.parts[2:]), destination)
            swap(staging, OUTPUT, Path(temporary) / "previous")

    # A run with changes swaps in exactly the expected skills; otherwise
    # skills/ stays as it is, strays included, so a dry run counts the same
    compiled = (
        len({relative.parts[1] for relative in expected})
        if lines
        else len(list(OUTPUT.glob("*/SKILL.md")))
    )
    page = count_page(expected, compiled)
    target = ROOT / COUNT
    current = target.read_text(encoding="utf-8") if target.is_file() else None
    if page != current:
        lines.append(["add" if current is None else "update", COUNT.as_posix()])
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page, encoding="utf-8")
    return lines


def work(args: argparse.Namespace) -> dict[str, Any]:
    lines = compile_tree(dry_run=args.dry_run or args.check)
    if args.check and lines:
        raise ScriptError(
            "skills/ or the skill count differs from authoring/; "
            "run: just compile-skills",
            report={"changes": lines},
        )
    return {"changes": lines} if lines else {}


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just compile-skills",
        description=(
            "Compile authoring/<skill>/ and authoring/<category>/<skill>/ "
            "packages into skills/<skill>/"
        ),
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
        help="dry run that exits 1 when skills/ or the skill count differs, "
        "listing the changes beside the error",
    )
    return run_script(
        parser, work, argv, debug="COMPILE_SKILLS_DEBUG", json_answer=True
    )


if __name__ == "__main__":
    raise SystemExit(main())

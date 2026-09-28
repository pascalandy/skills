#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Flatten categorized authoring packages into the published skills directory."""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes
from _common import run_script, swap

ROOT = Path(__file__).resolve().parent.parent
AUTHORING = ROOT / "authoring"
OUTPUT = ROOT / "skills"

EPILOG = """\
Each run prints one line per skill it changes: add, update, or remove, then a
tab and skills/<name>. A dry run prints the same lines and changes nothing;
a run with nothing to change prints nothing.

examples:
  just flatten-skills
  just flatten-skills --dry-run
  just flatten-skills --check
  just flatten-skills --verbose"""

EXIT_CODES = exit_codes(
    {
        0: "skills/ matches authoring/, or now does",
        1: "flatten failed, or --check found changes",
    }
)

log = logging.getLogger("flatten-skills")


def git(*args: str) -> bytes:
    """Run git in the repository and return its stdout."""
    executable = shutil.which("git")
    if executable is None:
        raise ScriptError("git not found on PATH; install git and rerun")
    result = subprocess.run(
        [executable, *args], cwd=ROOT, capture_output=True, check=False
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
    """Map each skill to the tracked source files that flattening would copy."""
    packages: dict[str, Path] = {}
    for entry in sorted(AUTHORING.glob("*/*/SKILL.md")):
        package = entry.parent
        if package.parent.name == "commands":
            log.debug("skip %s (commands are not skills)", package.relative_to(ROOT))
            continue
        if package.name in packages:
            raise ScriptError(
                f"duplicate skill name {package.name!r}: "
                f"{packages[package.name].relative_to(ROOT)} and {package.relative_to(ROOT)}; "
                "rename one package"
            )
        packages[package.name] = package

    if not packages:
        raise ScriptError(
            "no skill packages found at authoring/<category>/<skill>/SKILL.md"
        )
    files: dict[str, list[tuple[Path, Path]]] = {name: [] for name in packages}
    unpackaged: set[str] = set()
    for relative in git_files("authoring"):
        if len(relative.parts) < 3 or relative.parts[1] == "commands":
            continue
        source = ROOT / relative
        if not (source.is_file() or source.is_symlink()):
            log.debug("skip %s (not a file)", relative)
            continue
        if len(relative.parts) == 3:
            unpackaged.add(relative.as_posix())
            continue
        _, category, name, *inside = relative.parts
        if packages.get(name) != AUTHORING / category / name:
            unpackaged.add(f"authoring/{category}/{name}/")
            continue

        if source.is_symlink():
            raise ScriptError(
                f"skill source symlink is unsupported: {relative}; replace it with a file"
            )
        files[name].append((source, Path(*inside)))

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


def build_expected() -> dict[Path, Path]:
    """Map each generated path to the source file that supplies its bytes and mode."""
    return {
        Path("skills") / name / relative: source
        for name, entries in collect().items()
        for source, relative in entries
    }


def changes(expected: dict[Path, Path]) -> list[str]:
    """One `<action>\tskills/<name>` line per skill whose generated copy differs."""
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
        elif source.read_bytes() != destination.read_bytes():
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
        f"{'add' if name not in present else 'remove' if name not in wanted else 'update'}"
        f"\tskills/{name}"
        for name in sorted(stale)
    ]


def flatten(*, dry_run: bool = False) -> list[str]:
    """Rebuild skills/ from authoring/ when they differ; return one change line
    per skill, and change nothing on a dry run."""
    if OUTPUT.is_symlink() or (OUTPUT.exists() and not OUTPUT.is_dir()):
        raise ScriptError(
            "skills/ must be a directory, not a file or symlink; "
            "move it aside, then rerun just flatten-skills"
        )
    expected = build_expected()
    lines = changes(expected)
    if dry_run or not lines:
        return lines

    with tempfile.TemporaryDirectory(prefix=".skills-flatten-", dir=ROOT) as temporary:
        staging = Path(temporary) / "skills"
        staging.mkdir()
        for relative, source in expected.items():
            destination = staging / relative.relative_to("skills")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        swap(staging, OUTPUT, Path(temporary) / "previous")
    return lines


def run(args: argparse.Namespace) -> str:
    lines = flatten(dry_run=args.dry_run or args.check)
    if args.check and lines:
        raise ScriptError(
            "skills/ differs from authoring/; run: just flatten-skills",
            detail="\n".join(lines),
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just flatten-skills",
        description="Flatten authoring/<category>/<skill>/ packages into skills/<skill>/",
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
        help="dry run that exits 1 when skills/ differs, listing the changes on stderr",
    )
    return run_script(parser, run, argv, debug="FLATTEN_SKILLS_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

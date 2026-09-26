#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Flatten categorized authoring packages into the published skills directory."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from contextlib import nullcontext
from pathlib import Path

from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
AUTHORING = ROOT / "authoring"
OUTPUT = ROOT / "skills"

EPILOG = """\
examples:
  just flatten-skills
  just flatten-skills --dry-run
  just flatten-skills --verbose

exit codes: 0 ok, 1 flatten failed, 2 bad usage, 130 interrupted"""

log = logging.getLogger("flatten-skills")


def flatten(*, dry_run: bool) -> str:
    """Rebuild skills/ from authoring/ and return the summary line."""
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
    if OUTPUT.is_symlink() or (OUTPUT.exists() and not OUTPUT.is_dir()):
        raise ScriptError("skills/ must be a directory, not a file or symlink")

    git = shutil.which("git")
    if git is None:
        raise ScriptError("git not found on PATH; install git and rerun")
    listed = subprocess.run(
        [
            git,
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "authoring",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if listed.returncode != 0:
        raise ScriptError(f"git ls-files failed: {listed.stderr.decode().strip()}")

    file_counts: Counter[str] = Counter()
    entry_points: set[str] = set()
    unpackaged: set[str] = set()
    temporary_context = (
        nullcontext(None)
        if dry_run
        else tempfile.TemporaryDirectory(prefix=".skills-flatten-", dir=ROOT)
    )
    with temporary_context as temporary:
        staging = Path(temporary) / "skills" if temporary is not None else None
        if staging is not None:
            staging.mkdir()
        for raw_path in listed.stdout.split(b"\0"):
            if not raw_path:
                continue
            relative = Path(os.fsdecode(raw_path))
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
            if inside == ["SKILL.md"]:
                entry_points.add(name)
            if staging is not None:
                destination = staging / name / Path(*inside)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            file_counts[name] += 1

        if unpackaged:
            raise ScriptError(
                f"files outside a skill package: {', '.join(sorted(unpackaged))}; "
                "add a SKILL.md or move them into a package"
            )
        for name, package in packages.items():
            if name not in entry_points:
                raise ScriptError(
                    f"skill entry point is missing or git-ignored: {package.relative_to(ROOT)}/SKILL.md"
                )
            log.debug(
                "%s (%d files)", package.relative_to(AUTHORING), file_counts[name]
            )

        counts = f"{len(packages)} skills, {file_counts.total()} files"
        if staging is None:
            return f"dry run: {counts}; skills/ unchanged"

        previous = staging.parent / "previous"
        try:
            if OUTPUT.exists():
                OUTPUT.rename(previous)
            staging.rename(OUTPUT)
        except BaseException:
            if previous.exists() and not OUTPUT.exists():
                previous.rename(OUTPUT)
            raise

    return f"ok: {counts} -> skills/"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just flatten-skills",
        description="Flatten authoring/<category>/<skill>/ packages into skills/<skill>/",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and count without replacing skills/",
    )
    return run_script(parser, lambda args: flatten(dry_run=args.dry_run), argv)


if __name__ == "__main__":
    raise SystemExit(main())

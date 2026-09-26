"""Flatten categorized authoring packages into the published skills directory."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTHORING = ROOT / "authoring"
OUTPUT = ROOT / "skills"

EPILOG = """\
examples:
  just flatten-skills
  just flatten-skills --verbose

exit codes: 0 ok, 1 flatten failed, 2 bad usage, 130 interrupted"""

log = logging.getLogger("flatten-skills")


class FlattenError(Exception):
    """Expected failure whose message says what to fix."""


def flatten() -> tuple[int, int]:
    """Rebuild skills/ from authoring/ and return the skill and file counts."""
    packages: dict[str, Path] = {}
    for entry in sorted(AUTHORING.glob("*/*/SKILL.md")):
        package = entry.parent
        if package.parent.name == "commands":
            log.debug("skip %s (commands are not skills)", package.relative_to(ROOT))
            continue
        if package.name in packages:
            raise FlattenError(
                f"duplicate skill name {package.name!r}: "
                f"{packages[package.name].relative_to(ROOT)} and {package.relative_to(ROOT)}; "
                "rename one package"
            )
        packages[package.name] = package

    if not packages:
        raise FlattenError(
            "no skill packages found at authoring/<category>/<skill>/SKILL.md"
        )
    if OUTPUT.is_symlink() or (OUTPUT.exists() and not OUTPUT.is_dir()):
        raise FlattenError("skills/ must be a directory, not a file or symlink")

    listed = subprocess.run(
        [
            "git",
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
        raise FlattenError(f"git ls-files failed: {listed.stderr.decode().strip()}")

    file_counts: Counter[str] = Counter()
    unpackaged: set[str] = set()
    with tempfile.TemporaryDirectory(prefix=".skills-flatten-", dir=ROOT) as temporary:
        staging = Path(temporary) / "skills"
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
                raise FlattenError(
                    f"skill source symlink is unsupported: {relative}; replace it with a file"
                )
            destination = staging / name / Path(*inside)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            file_counts[name] += 1

        if unpackaged:
            raise FlattenError(
                f"files outside a skill package: {', '.join(sorted(unpackaged))}; "
                "add a SKILL.md or move them into a package"
            )
        for name, package in packages.items():
            if not (staging / name / "SKILL.md").is_file():
                raise FlattenError(
                    f"skill entry point is missing or git-ignored: {package.relative_to(ROOT)}/SKILL.md"
                )
            log.debug(
                "%s (%d files)", package.relative_to(AUTHORING), file_counts[name]
            )

        previous = Path(temporary) / "previous"
        try:
            if OUTPUT.exists():
                OUTPUT.rename(previous)
            staging.rename(OUTPUT)
        except BaseException:
            if previous.exists() and not OUTPUT.exists():
                previous.rename(OUTPUT)
            raise

    return len(packages), file_counts.total()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just flatten-skills",
        description="Flatten authoring/<category>/<skill>/ packages into skills/<skill>/",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="report each skill and skipped entry on stderr",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        format="%(message)s", level=logging.DEBUG if args.verbose else logging.WARNING
    )

    try:
        skill_count, file_count = flatten()
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except FlattenError as error:
        print(f"error: {error}", file=sys.stderr)
    except Exception as error:
        log.debug("unexpected failure", exc_info=True)
        print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
    else:
        print(f"ok: {skill_count} skills, {file_count} files -> skills/")
        return 0

    if not args.verbose:
        print("rerun with --verbose for details", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

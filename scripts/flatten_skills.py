"""Flatten categorized authoring packages into the published skills directory."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUTHORING = ROOT / "authoring"
OUTPUT = ROOT / "skills"


def main() -> None:
    packages: dict[str, Path] = {}
    for entry in sorted(AUTHORING.glob("*/*/SKILL.md")):
        package = entry.parent
        if package.parent.name == "commands":
            continue
        if package.name in packages:
            raise SystemExit(
                f"Duplicate skill name {package.name!r}: "
                f"{packages[package.name]} and {package}"
            )
        packages[package.name] = package

    if not packages:
        raise SystemExit("No skill packages found in authoring/")
    if OUTPUT.is_symlink() or (OUTPUT.exists() and not OUTPUT.is_dir()):
        raise SystemExit("skills/ must be a directory, not a file or symlink")

    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "authoring"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout

    file_count = 0
    with tempfile.TemporaryDirectory(prefix=".skills-flatten-", dir=ROOT) as temporary:
        staging = Path(temporary) / "skills"
        staging.mkdir()
        for raw_path in listed.split(b"\0"):
            if not raw_path:
                continue
            relative = Path(os.fsdecode(raw_path))
            if len(relative.parts) < 4:
                continue
            _, category, name, *inside = relative.parts
            if packages.get(name) != AUTHORING / category / name:
                continue

            source = ROOT / relative
            if source.is_symlink():
                raise SystemExit(f"Skill source symlink is unsupported: {relative}")
            if not source.is_file():
                continue
            destination = staging / name / Path(*inside)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            file_count += 1

        for name in packages:
            if not (staging / name / "SKILL.md").is_file():
                raise SystemExit(f"Skill entry point is ignored or missing: {name}")

        previous = Path(temporary) / "previous"
        if OUTPUT.exists():
            OUTPUT.rename(previous)
        try:
            staging.rename(OUTPUT)
        except OSError:
            if previous.exists():
                previous.rename(OUTPUT)
            raise

    print(f"Flattened {len(packages)} skills ({file_count} files) into skills/")


if __name__ == "__main__":
    main()

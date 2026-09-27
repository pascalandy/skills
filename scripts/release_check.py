#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate a tagged release candidate and extract its changelog notes."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
SECTION = re.compile(r"## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}")

EPILOG = """\
examples:
  just release-check v0.1.0 --verbose
  just release-check v0.1.0 --notes /tmp/notes.md

exit codes: 0 ok, 1 release check failed, 2 bad usage, 130 interrupted"""


@dataclass(frozen=True)
class SkillChanges:
    added: tuple[str, ...]
    changed: tuple[str, ...]
    removed: tuple[str, ...]
    first_release: bool

    def summary(self, version: str) -> str:
        if self.first_release:
            count = len(self.added)
            return f"ok: {version}: {count} skill{'s' if count != 1 else ''} total"
        return (
            f"ok: {version}: {len(self.added)} added, "
            f"{len(self.changed)} changed, {len(self.removed)} removed"
        )

    def print_names(self) -> None:
        if self.first_release:
            print(
                f"skills ({len(self.added)}): {', '.join(self.added)}", file=sys.stderr
            )
            return
        for label, names in (
            ("added", self.added),
            ("changed", self.changed),
            ("removed", self.removed),
        ):
            print(f"{label} ({len(names)}): {', '.join(names) or '-'}", file=sys.stderr)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("git")
    if executable is None:
        raise ScriptError("git not found on PATH; install git and rerun")
    return subprocess.run(
        [executable, *args], cwd=ROOT, text=True, capture_output=True, check=False
    )


def git_output(*args: str) -> str:
    result = git(*args)
    if result.returncode:
        raise ScriptError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def parse_version(value: str) -> tuple[int, int, int] | None:
    match = VERSION.fullmatch(value)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def skill_names(revision: str) -> set[str]:
    paths = git_output("ls-tree", "-r", "--name-only", revision, "--", "skills/")
    return {
        parts[1] for path in paths.splitlines() if len(parts := Path(path).parts) > 2
    }


def skill_changes(previous: str | None) -> SkillChanges:
    current = skill_names("HEAD")
    if previous is None:
        return SkillChanges(tuple(sorted(current)), (), (), True)

    earlier = skill_names(previous)
    changed_paths = git_output(
        "diff", "--no-renames", "--name-only", previous, "HEAD", "--", "skills/"
    )
    changed_names = {
        parts[1]
        for path in changed_paths.splitlines()
        if len(parts := Path(path).parts) > 2
    }
    return SkillChanges(
        tuple(sorted(current - earlier)),
        tuple(sorted((current & earlier) & changed_names)),
        tuple(sorted(earlier - current)),
        False,
    )


def changelog_body(version: str) -> tuple[str | None, str | None]:
    path = ROOT / "CHANGELOG.md"
    if not path.is_file():
        return (
            None,
            f"CHANGELOG.md has no [{version.removeprefix('v')}] section; add it",
        )

    lines = path.read_text(encoding="utf-8").splitlines()
    wanted = version.removeprefix("v")
    matches = [
        index
        for index, line in enumerate(lines)
        if (match := SECTION.fullmatch(line)) and match.group(1) == wanted
    ]
    if not matches:
        return None, f"CHANGELOG.md has no [{wanted}] section; add it"
    if len(matches) > 1:
        return None, f"CHANGELOG.md has duplicate [{wanted}] sections; keep one"

    start = matches[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    body = "\n".join(lines[start:end]).strip("\n")
    if not body.strip():
        return None, f"CHANGELOG.md [{wanted}] section is empty; add release notes"
    return body + "\n", None


def check_release(version: str, notes: Path | None, verbose: bool) -> str:
    errors: list[str] = []
    requested = parse_version(version)
    if requested is None:
        errors.append("version must be vMAJOR.MINOR.PATCH without leading zeros")

    releases: dict[str, tuple[int, int, int]] = {}
    ignored: list[str] = []
    for tag in git_output("tag", "--list", "--sort=refname", "v*").splitlines():
        if tag == version:
            continue
        parsed = parse_version(tag)
        if parsed is None:
            ignored.append(tag)
        else:
            releases[tag] = parsed

    previous = max(releases, key=lambda tag: releases[tag], default=None)
    if (
        requested is not None
        and previous is not None
        and releases[previous] >= requested
    ):
        errors.append(f"version must be greater than the latest release tag {previous}")

    changes = skill_changes(previous)
    if verbose:
        if ignored:
            print(f"ignored non-release tags: {', '.join(ignored)}", file=sys.stderr)
        changes.print_names()

    body, changelog_error = changelog_body(version)
    if changelog_error:
        errors.append(changelog_error)

    head = git_output("rev-parse", "HEAD")
    if git(
        "merge-base", "--is-ancestor", "HEAD", "refs/remotes/origin/main"
    ).returncode:
        errors.append(
            "HEAD is not an ancestor of origin/main; run git fetch --tags origin main"
        )

    if (
        requested is not None
        and git("show-ref", "--verify", "--quiet", f"refs/tags/{version}").returncode
        == 0
    ):
        tagged = git_output("rev-parse", f"refs/tags/{version}^{{commit}}")
        if tagged != head:
            errors.append(
                f"tag {version} points to a different commit; choose a new version"
            )

    if git_output("status", "--porcelain", "--untracked-files=all"):
        errors.append("working tree is dirty; commit or remove changes before release")

    if errors:
        raise ScriptError(*errors)
    if notes is not None and body is not None:
        notes.write_text(body, encoding="utf-8")
    return changes.summary(version)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just release-check",
        description="Validate HEAD for a versioned release and extract its notes",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("version", help="release tag, for example v0.1.0")
    parser.add_argument(
        "--notes", type=Path, metavar="FILE", help="write release notes to FILE"
    )
    return run_script(
        parser, lambda args: check_release(args.version, args.notes, args.verbose), argv
    )


if __name__ == "__main__":
    raise SystemExit(main())

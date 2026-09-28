#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install public skills, private skills, and shared commands into local agent directories.

The installer owns every name this repository ever published under skills/ or
authoring/commands/, as recorded in git history. It removes an owned name once
no source provides it and never touches entries it did not publish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

import flatten_skills
from _cli import Parser, ScriptError, duration, exit_codes
from _common import exclusive, run, run_script, swap

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / "_skills_private"
PROFILES = {
    "mac": (
        ".pi/agent/skills",
        ".agents/skills",
        ".claude/skills",
        ".config/opencode/skills",
        ".config/agents/skills",
    ),
    "om1": (
        ".pi/agent/skills",
        ".codex/skills",
        ".claude/skills",
        ".config/opencode/skills",
    ),
}
EXCLUSIONS = {"mac": frozenset(), "om1": frozenset({"apple-mail"})}
HOST_PROFILE = "mac" if sys.platform == "darwin" else "om1"
COMMAND_TARGETS = {
    "mac": (
        ".claude/commands",
        ".pi/agent/prompts",
        ".codex/prompts",
        ".config/opencode/commands",
        ".config/agents/commands",
    ),
    "om1": (
        ".claude/commands",
        ".pi/agent/prompts",
        ".codex/prompts",
        ".config/opencode/commands",
    ),
}
RUNTIME_NAMES = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".cache",
        ".turbo",
        "coverage",
        "dist",
        "build",
        ".coverage",
        ".DS_Store",
    }
)
RUNTIME_PREFIXES = (".coverage.", "._")
RUNTIME_SUFFIXES = (".pyc", ".pyo", ".tsbuildinfo", ".swp", ".swo", "~")
CHANGES = ("add", "update", "remove")
EXIT_CODES = exit_codes(
    {
        0: "installed, or nothing to change",
        1: "a conflict blocks the install, or --check found pending changes",
        75: "another install still held the lock after --timeout",
    }
)
EPILOG = """\
Each run prints one line per change: add, update, or remove, then a tab and
the installed path. A dry run prints the same lines and writes nothing; a run
with nothing to change prints nothing. A conflict, a symlink or wrong type at
a target path, blocks the install and is reported on stderr.

profiles:
  mac: ~/.pi/agent/skills, ~/.agents/skills, ~/.claude/skills,
       ~/.config/opencode/skills, ~/.config/agents/skills
  om1: ~/.pi/agent/skills, ~/.codex/skills, ~/.claude/skills,
       ~/.config/opencode/skills (excludes apple-mail)
  commands on both: ~/.claude/commands, ~/.pi/agent/prompts,
        ~/.codex/prompts, ~/.config/opencode/commands
  commands on mac: ~/.config/agents/commands

examples:
  just install-skills --dry-run
  just install-skills
  just install-skills --private-root ~/private-skills
  just install-skills --check --json"""
log = logging.getLogger("install-skills")


@dataclass(frozen=True)
class Source:
    path: Path
    kind: str
    digest: str


@dataclass(frozen=True)
class Action:
    target: str
    name: str
    kind: str
    source: str | None = None
    detail: str | None = None


def is_runtime(name: str) -> bool:
    return (
        name in RUNTIME_NAMES
        or name.startswith(RUNTIME_PREFIXES)
        or name.endswith(RUNTIME_SUFFIXES)
    )


def digest_files(entries: Iterable[tuple[Path, Path]]) -> str:
    hasher = hashlib.sha256()
    for relative, path in sorted(entries, key=lambda entry: entry[0].as_posix()):
        if any(is_runtime(part) for part in relative.parts):
            continue
        label = relative.as_posix()
        if path.is_symlink():
            header, content = f"link:{label}", os.readlink(path).encode()
        else:
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            header, content = f"file:{label}:{executable:d}", path.read_bytes()
        hasher.update(f"{header}:{len(content)}\0".encode())
        hasher.update(content)
    return hasher.hexdigest()


def digest(skill: Path) -> str:
    entries: list[tuple[Path, Path]] = []
    for directory, subdirs, files in os.walk(skill):
        base = Path(directory)
        links = [name for name in subdirs if (base / name).is_symlink()]
        subdirs[:] = [
            name for name in subdirs if name not in links and not is_runtime(name)
        ]
        for name in [*files, *links]:
            if not is_runtime(name):
                path = base / name
                entries.append((path.relative_to(skill), path))
    return digest_files(entries)


def digest_command(path: Path) -> str:
    return digest_files(((Path(path.name), path),))


def replace(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".install-skills-", dir=destination.parent
    ) as temporary:
        fresh = Path(temporary) / "fresh"
        shutil.copytree(
            source,
            fresh,
            ignore=lambda _, names: {name for name in names if is_runtime(name)},
        )
        swap(fresh, destination, Path(temporary) / "previous")


def replace_command(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=".install-command-", dir=destination.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
    try:
        shutil.copy2(source, temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def private_packages(root: Path | None) -> dict[str, Path]:
    """Map every package in the private tree; the default tree is optional."""
    if root is None:
        if not PRIVATE.exists():
            return {}
        root = PRIVATE
    if not root.is_dir() or root.is_symlink():
        raise ScriptError(
            f"private source {root} is missing or invalid; fix --private-root"
        )
    packages: dict[str, Path] = {}
    for entry in sorted(root.rglob("SKILL.md")):
        package = entry.parent
        # A nested reference with its own SKILL.md belongs to the outer package.
        if any(
            (parent / "SKILL.md").is_file()
            for parent in package.parents
            if parent != root and root in parent.parents
        ):
            continue
        name = package.name
        if name in packages:
            raise ScriptError(
                f"duplicate private skill {name!r}: {packages[name]} and {package}"
            )
        if package.is_symlink() or any(
            path.is_symlink() for path in package.rglob("*")
        ):
            raise ScriptError(
                f"private skill {name!r} contains a symlink; replace it with files"
            )
        packages[name] = package
    return packages


def skill_sources(
    stage: Path, private_root: Path | None, profile: str
) -> dict[str, Source]:
    """Stage public packages under `stage`, add every private package, and drop
    the profile's exclusions."""
    sources: dict[str, Source] = {}
    for name, entries in flatten_skills.collect().items():
        package = stage / name
        for source, relative in entries:
            destination = package / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        sources[name] = Source(package, "public", digest(package))
    duplicates: list[str] = []
    for name, package in private_packages(private_root).items():
        if name in sources:
            duplicates.append(
                f"skill {name!r} is public and private; delete the stale copy at {package}"
            )
            continue
        sources[name] = Source(package, "private", digest(package))
    if duplicates:
        raise ScriptError(*duplicates)
    if not sources:
        raise ScriptError("no public skills found; run just flatten-skills")
    return {
        name: source
        for name, source in sources.items()
        if name not in EXCLUSIONS[profile]
    }


def command_sources() -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for relative in flatten_skills.git_files("authoring/commands"):
        if len(relative.parts) != 3 or relative.suffix != ".md":
            continue
        path = ROOT / relative
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise ScriptError(f"command source {relative} must be a regular file")
        sources[path.name] = Source(path, "command", digest_command(path))
    return sources


def published(directory: str) -> list[Path]:
    """List every path git history ever added under `directory`, relative to it."""
    if flatten_skills.git("rev-parse", "--is-shallow-repository").strip() == b"true":
        raise ScriptError(
            "shallow clone hides retired skills; run git fetch --unshallow and rerun"
        )
    listed = flatten_skills.git(
        "log",
        "--no-renames",
        "--diff-filter=A",
        "--name-only",
        "--format=",
        "-z",
        "--",
        directory,
    )
    paths = (os.fsdecode(path).strip() for path in listed.split(b"\0"))
    return [Path(path).relative_to(directory) for path in paths if path]


def owned_skills() -> set[str]:
    """Names ever committed under skills/, plus uncommitted ones flattened there."""
    return {path.parts[0] for path in published("skills") if len(path.parts) > 1} | {
        path.parts[1]
        for path in flatten_skills.git_files("skills")
        if len(path.parts) > 2
    }


def owned_private(root: Path | None) -> set[str]:
    """Package names the private clone's history ever added, so deleting one there
    removes its installed copies. A private tree that is not a clone owns nothing."""
    root = root or PRIVATE
    if root.is_symlink() or not (root / ".git").is_dir():
        return set()

    def git(*args: str) -> bytes:
        result = run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise ScriptError(
                f"git failed in {root}: {os.fsdecode(result.stderr).strip()}"
            )
        return result.stdout

    if git("rev-parse", "--is-shallow-repository").strip() == b"true":
        raise ScriptError(
            f"shallow clone at {root} hides retired skills; run git fetch --unshallow there and rerun"
        )
    listed = git(
        "log", "--no-renames", "--diff-filter=A", "--name-only", "--format=", "-z"
    )
    added = {
        Path(os.fsdecode(path).strip()) for path in listed.split(b"\0") if path.strip()
    }
    entries = {path for path in added if path.name == "SKILL.md"}
    # A nested reference with its own SKILL.md belongs to the outer package.
    return {
        entry.parent.name
        for entry in entries
        if entry.parent != Path(".")
        and not any(
            parent / "SKILL.md" in entries
            for parent in entry.parent.parents
            if parent != Path(".")
        )
    }


def target_groups(home: Path, targets: Iterable[str]) -> dict[Path, list[str]]:
    groups: dict[Path, list[str]] = {}
    for target in targets:
        directory = home / target
        for ancestor in (directory, *directory.parents):
            if ancestor == home.parent:
                break
            if ancestor.is_symlink() and not ancestor.exists():
                raise ScriptError(
                    f"~/{target} has a broken symlink ancestor: {ancestor}"
                )
            if ancestor.exists() and not ancestor.is_dir():
                raise ScriptError(f"~/{target} has a file ancestor: {ancestor}")
        if not directory.resolve().is_relative_to(home.resolve()):
            raise ScriptError(
                f"~/{target} resolves outside the selected home; fix it and rerun"
            )
        groups.setdefault(directory.resolve(), []).append(target)
    return groups


def plan(
    home: Path,
    targets: Iterable[str],
    sources: dict[str, Source],
    owned: set[str],
    files: bool = False,
) -> list[Action]:
    """Install every source and remove owned names without one; skill targets hold
    directories and command targets hold files."""
    measure = digest_command if files else digest
    retired = "command" if files else "public"
    actions: list[Action] = []
    for aliases in target_groups(home, targets).values():
        target = aliases[0]
        for name in sorted(sources.keys() | owned):
            source = sources.get(name)
            path = home / target / name
            if path.is_symlink() or (path.exists() and path.is_dir() == files):
                actions.append(
                    Action(
                        target,
                        name,
                        "conflict",
                        source.kind if source else retired,
                        f"~/{target}/{name} is a symlink or "
                        + ("directory" if files else "file"),
                    )
                )
                continue
            current = measure(path) if path.exists() else None
            if source is None:
                if current is not None:
                    actions.append(Action(target, name, "remove", retired))
                continue
            kind = (
                "add"
                if current is None
                else "current"
                if current == source.digest
                else "update"
            )
            actions.append(Action(target, name, kind, source.kind))
    return actions


def execute(
    home: Path,
    sources: dict[str, Source],
    commands: dict[str, Source],
    actions: list[Action],
) -> None:
    for action in actions:
        destination = home / action.target / action.name
        if action.kind in ("add", "update"):
            if action.source == "command":
                replace_command(commands[action.name].path, destination)
            else:
                replace(sources[action.name].path, destination)
        elif action.kind == "remove":
            if action.source == "command":
                destination.unlink()
            else:
                shutil.rmtree(destination)


def summarize(actions: list[Action], expected: dict[str, int]) -> list[dict]:
    """Count each target's actions against the number of names it should hold."""
    summary: list[dict] = []
    for target in dict.fromkeys(action.target for action in actions):
        counts = Counter(action.kind for action in actions if action.target == target)
        summary.append(
            {
                "target": target,
                "expected": expected[target],
                "current": counts["current"],
                "counts": dict(counts),
            }
        )
    return summary


def install_lock() -> Path:
    """One lock per repository, shared by its worktrees and outside the home,
    so a run that fails validation still writes nothing there."""
    common = os.fsdecode(flatten_skills.git("rev-parse", "--git-common-dir"))
    return ROOT / common.strip() / "install-skills.lock"


def report(
    actions: list[Action], profile: str, synced: tuple[int, int], preview: bool
) -> dict:
    """The --json object: counts per target and every action."""
    skills, commands = synced
    expected = {
        **dict.fromkeys(PROFILES[profile], skills),
        **dict.fromkeys(COMMAND_TARGETS[profile], commands),
    }
    return {
        "profile": profile,
        "mode": "preview" if preview else "apply",
        "skills": skills,
        "commands": commands,
        "counts": dict(Counter(action.kind for action in actions)),
        "targets": summarize(actions, expected),
        "actions": [action.__dict__ for action in actions],
    }


def install(args: argparse.Namespace) -> str:
    home = Path.home()
    preview = args.dry_run or args.check
    # An apply waits for any other one before it reads the working tree, so
    # the last to finish installs the newest version. Previews and checks
    # write nothing and do not wait.
    with (
        nullcontext() if preview else exclusive(install_lock(), args.timeout),
        tempfile.TemporaryDirectory(prefix=".install-skills-source-") as temporary,
    ):
        sources = skill_sources(Path(temporary), args.private_root, args.profile)
        commands = command_sources()
        actions = [
            *plan(
                home,
                PROFILES[args.profile],
                sources,
                owned_skills() | owned_private(args.private_root),
            ),
            *plan(
                home,
                COMMAND_TARGETS[args.profile],
                commands,
                {
                    path.name
                    for path in published("authoring/commands")
                    if len(path.parts) == 1 and path.suffix == ".md"
                },
                files=True,
            ),
        ]
        summary = report(actions, args.profile, (len(sources), len(commands)), preview)
        for target in summary["targets"]:
            log.info(
                "~/%s: %d of %d current",
                target["target"],
                target["current"],
                target["expected"],
            )
        changes = "\n".join(
            f"{action.kind}\t~/{action.target}/{action.name}"
            for action in actions
            if action.kind in CHANGES
        )
        conflicts = [
            f"{action.detail}; move it aside, then rerun: just install-skills"
            for action in actions
            if action.kind == "conflict"
        ]
        output = json.dumps(summary, indent=2) if args.json else changes
        pending = [action for action in actions if action.kind != "current"]
        if args.check and pending:
            raise ScriptError(
                *conflicts,
                f"{len(pending)} installed entries differ from the checkout; "
                "run: just install-skills",
                detail=changes,
                report=summary,
            )
        if preview:
            for conflict in conflicts:
                log.warning("warning: %s", conflict)
            return output
        if conflicts:
            raise ScriptError(*conflicts, report=summary)
        flatten_skills.flatten()
        execute(home, sources, commands, actions)
        return output


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just install-skills",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default=HOST_PROFILE,
        help="local target set; defaults to mac on macOS and om1 elsewhere",
    )
    parser.add_argument(
        "--private-root",
        type=Path,
        help="private package tree whose packages all install (default: _skills_private/ when present)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print the changes an install would make, and warn about conflicts, without writing",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="dry run that exits 1 when an installed entry differs, listing the changes on stderr",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the per-target report as one JSON object",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="5m",
        help="how long an install waits for another one to finish (default: 5m)",
    )
    # Syncs started before this version pass -q to the installer they pulled;
    # accept it silently until every machine runs this one
    parser.add_argument("-q", "--quiet", action="store_true", help=argparse.SUPPRESS)
    return run_script(parser, install, argv, debug="INSTALL_SKILLS_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

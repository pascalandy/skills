#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install the flattened skills/ directory into each agent skill directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import stat
import tempfile
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import flatten_skills
from _common import ScriptError, run_script, swap

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "skills"

# Home-relative skill directories the agents on this Mac read
TARGETS = (
    ".agents/skills",
    ".claude/skills",
    ".config/agents/skills",
    ".config/opencode/skills",
    ".pi/agent/skills",
)

# Disposable files created while using a skill; keep edits such as .env visible
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

EPILOG = f"""\
targets:
  {", ".join(f"~/{target}" for target in TARGETS)}

ownership:
  A manifest in $XDG_STATE_HOME/install-skills/ (default ~/.local/state)
  records the skills this script installed. Skills it did not install are
  never touched. An installed copy identical to skills/ is adopted; one that
  differs, or that was edited after the last install, stops the run until you
  rerun with --force.

examples:
  just install-skills --dry-run --verbose
  just install-skills
  just install-skills --force

exit codes: 0 ok, 1 install failed, 2 bad usage, 130 interrupted"""

log = logging.getLogger("install-skills")

# Skill name to digest, per home-relative target directory
Owned = dict[str, dict[str, str]]


def is_runtime(name: str) -> bool:
    return (
        name in RUNTIME_NAMES
        or name.startswith(RUNTIME_PREFIXES)
        or name.endswith(RUNTIME_SUFFIXES)
    )


def digest_files(entries: Iterable[tuple[Path, Path]]) -> str:
    """Hash relative file paths, contents, and exec bits in a stable order."""
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
    """Hash a skill's files, ignoring disposable runtime artifacts."""
    entries: list[tuple[Path, Path]] = []
    for directory, subdirs, files in os.walk(skill):
        base = Path(directory)
        links = [name for name in subdirs if (base / name).is_symlink()]
        subdirs[:] = [
            name for name in subdirs if name not in links and not is_runtime(name)
        ]
        for name in [*files, *links]:
            if is_runtime(name):
                continue
            path = base / name
            entries.append((path.relative_to(skill), path))
    return digest_files(entries)


def load_manifest(path: Path) -> Owned:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ScriptError(
            f"cannot read manifest {path}: {error}; "
            "fix it, or delete it so identical copies are adopted again"
        ) from error
    if (
        not isinstance(data, dict)
        or data.get("version") != 1
        or not isinstance(data.get("targets"), dict)
    ):
        raise ScriptError(
            f"unexpected manifest format in {path}; "
            "delete it so identical copies are adopted again"
        )
    return data["targets"]


def save_manifest(path: Path, owned: Owned) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    document = {"version": 1, "targets": owned}
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def replace(source: Path, destination: Path) -> None:
    """Swap a fresh copy of `source` into `destination` so agents never read half a skill."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".install-skills-", dir=destination.parent
    ) as temporary:
        fresh = Path(temporary) / "fresh"
        previous = Path(temporary) / "previous"
        shutil.copytree(
            source,
            fresh,
            ignore=lambda _, names: {name for name in names if is_runtime(name)},
        )
        swap(fresh, destination, previous)


def install(
    source: Path,
    home: Path,
    manifest: Path,
    *,
    dry_run: bool,
    force: bool,
    planned: dict[str, str] | None = None,
) -> str:
    """Install every skill in `source` into each target under `home` and return the summary line.

    Collect installation conflicts before changing agent dirs or the manifest.
    An interrupted run heals on the next one: copies that already match skills/
    count as current.
    """
    wanted = planned
    if wanted is None:
        skills = {
            entry.parent.name: entry.parent for entry in source.glob("*/SKILL.md")
        }
        wanted = {name: digest(path) for name, path in skills.items()}
    else:
        skills = {name: source / name for name in wanted}
    if not wanted:
        raise ScriptError(f"no skills found in {source}; run just flatten-skills")
    previous = load_manifest(manifest)

    target_groups: dict[Path, list[str]] = {}
    invalid_targets: list[str] = []
    for target in TARGETS:
        directory = home / target
        if directory.is_symlink() and not directory.exists():
            invalid_targets.append(f"~/{target} is a broken symlink; fix it and rerun")
        elif directory.exists() and not directory.is_dir():
            invalid_targets.append(f"~/{target} is a file; remove it and rerun")
        else:
            target_groups.setdefault(directory.resolve(), []).append(target)
    if invalid_targets:
        raise ScriptError(*invalid_targets)

    owned: Owned = {}
    actions: list[tuple[str, str, str]] = []
    adoptions = 0
    problems: list[str] = []
    for aliases in target_groups.values():
        target = aliases[0]
        recorded: dict[str, str] = {}
        for alias in aliases:
            for name, checksum in previous.get(alias, {}).items():
                if name in recorded and recorded[name] != checksum:
                    raise ScriptError(
                        f"manifest has conflicting ownership for ~/{target} "
                        f"and ~/{alias}; fix the manifest and rerun"
                    )
                recorded[name] = checksum
        group_owned: dict[str, str] = {}
        for alias in aliases:
            owned[alias] = group_owned
        for name in sorted(wanted.keys() | recorded.keys()):
            path = home / target / name
            label = f"~/{target}/{name}"
            want, had = wanted.get(name), recorded.get(name)
            if path.is_symlink() or (path.exists() and not path.is_dir()):
                problems.append(f"{label} is a symlink or a file; remove it and rerun")
                continue
            current = digest(path) if path.exists() else None
            if current is not None and current not in (had, want) and not force:
                problems.append(
                    f"{label} was edited after the last install; "
                    "move the edit into authoring/ or rerun with --force"
                    if had
                    else f"{label} differs from skills/{name} and was not installed "
                    "by this script; rerun with --force to replace it"
                )
                continue

            if want is not None:
                group_owned[name] = want
            if current == want:
                if had is None:
                    adoptions += 1
                    log.debug("adopt %s", label)
            elif want is None:
                actions.append(("remove", target, name))
            else:
                actions.append(("add" if current is None else "update", target, name))

    if problems:
        raise ScriptError(*problems)

    for kind, target, name in actions:
        log.debug("%s ~/%s/%s", kind, target, name)
    counts = Counter(kind for kind, _, _ in actions)
    scope = f"{len(skills)} skills, {len(target_groups)} agent dirs"
    if dry_run:
        return (
            f"dry run: {scope}; {counts['add']} to add, "
            f"{counts['update']} to update, {counts['remove']} to remove, "
            f"{adoptions} to adopt"
        )

    for kind, target, name in actions:
        destination = home / target / name
        if kind == "remove":
            shutil.rmtree(destination)
        else:
            replace(skills[name], destination)
    if owned != previous:
        save_manifest(manifest, owned)
    return (
        f"ok: {scope}; {counts['add']} added, "
        f"{counts['update']} updated, {counts['remove']} removed, {adoptions} adopted"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="just install-skills",
        description="Install skills/ into each agent skill directory under your home",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would change without writing anything",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace installed copies that differ or were edited in place",
    )
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    manifest = state / "install-skills" / "manifest.json"

    def work(args: argparse.Namespace) -> str:
        if args.dry_run:
            files = flatten_skills.collect()
            planned = {
                name: digest_files((relative, path) for path, relative in entries)
                for name, entries in files.items()
            }
            return install(
                SOURCE,
                Path.home(),
                manifest,
                dry_run=True,
                force=args.force,
                planned=planned,
            )

        flatten_skills.flatten(dry_run=False)
        return install(SOURCE, Path.home(), manifest, dry_run=False, force=args.force)

    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

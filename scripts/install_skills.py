#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
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
from pathlib import Path

from _common import ScriptError, run_script

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

# Created by running a skill: never copied, never counted as an edit
RUNTIME_NAMES = frozenset(
    {
        "node_modules",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".DS_Store",
    }
)
RUNTIME_SUFFIXES = (".pyc", ".pyo")

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
type Owned = dict[str, dict[str, str]]


def is_runtime(name: str) -> bool:
    return name in RUNTIME_NAMES or name.endswith(RUNTIME_SUFFIXES)


def digest(skill: Path) -> str:
    """Hash a skill's file paths, contents, and exec bits, ignoring runtime artifacts."""
    hasher = hashlib.sha256()
    for directory, subdirs, files in os.walk(skill):
        base = Path(directory)
        links = [name for name in subdirs if (base / name).is_symlink()]
        subdirs[:] = sorted(
            name for name in subdirs if name not in links and not is_runtime(name)
        )
        for name in sorted([*files, *links]):
            if is_runtime(name):
                continue
            path = base / name
            relative = path.relative_to(skill).as_posix()
            if path.is_symlink():
                header, content = f"link:{relative}", os.readlink(path).encode()
            else:
                executable = bool(path.stat().st_mode & stat.S_IXUSR)
                header, content = f"file:{relative}:{executable:d}", path.read_bytes()
            hasher.update(f"{header}:{len(content)}\0".encode())
            hasher.update(content)
    return hasher.hexdigest()


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
        try:
            if destination.exists():
                destination.rename(previous)
            fresh.rename(destination)
        except BaseException:
            if previous.exists() and not destination.exists():
                previous.rename(destination)
            raise


def install(
    source: Path, home: Path, manifest: Path, *, dry_run: bool, force: bool
) -> str:
    """Install every skill in `source` into each target under `home` and return the summary line.

    Every problem is collected before anything is written, so a failed run changes
    nothing. An interrupted run heals on the next one: copies that already match
    skills/ count as current.
    """
    skills = {entry.parent.name: entry.parent for entry in source.glob("*/SKILL.md")}
    if not skills:
        raise ScriptError(f"no skills found in {source}; run just flatten-skills")
    wanted = {name: digest(path) for name, path in skills.items()}
    previous = load_manifest(manifest)

    owned: Owned = {}
    actions: list[tuple[str, str, str]] = []
    adoptions = 0
    problems: list[str] = []
    for target in TARGETS:
        recorded = previous.get(target, {})
        owned[target] = {}
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
                owned[target][name] = want
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
    scope = f"{len(skills)} skills, {len(TARGETS)} agent dirs"
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
    return run_script(
        parser,
        lambda args: install(
            SOURCE, Path.home(), manifest, dry_run=args.dry_run, force=args.force
        ),
        argv,
    )


if __name__ == "__main__":
    raise SystemExit(main())

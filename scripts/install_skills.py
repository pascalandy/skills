#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install public and explicitly selected private skills into local agent directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import stat
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import flatten_skills
from _common import ScriptError, swap

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
COMMAND_TARGETS = (
    ".claude/commands",
    ".pi/agent/prompts",
    ".codex/prompts",
    ".config/opencode/commands",
    ".config/agents/commands",
)
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
DIGEST = re.compile(r"^[0-9a-f]{64}$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
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


# Per target, a skill records both provenance and the last installed digest.
Owned = dict[str, dict[str, dict[str, str]]]


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


def load_manifest(path: Path) -> Owned:
    if path.is_symlink():
        raise ScriptError(
            f"manifest {path} is a symlink; replace it with a regular file"
        )
    for ancestor in (path.parent, *path.parent.parents):
        if ancestor.is_symlink() and not ancestor.exists():
            raise ScriptError(f"manifest parent {ancestor} is a broken symlink")
        if ancestor.exists() and not ancestor.is_dir():
            raise ScriptError(f"manifest parent {ancestor} is a file")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ScriptError(
            f"cannot read manifest {path}: {error}; repair it before installing"
        ) from error
    if (
        not isinstance(data, dict)
        or data.get("version") not in (1, 2)
        or not isinstance(data.get("targets"), dict)
    ):
        raise ScriptError(
            f"unexpected manifest format in {path}; repair it before installing"
        )
    version = data["version"]
    owned: Owned = {}
    for target, records in data["targets"].items():
        if target not in set().union(
            *[set(paths) for paths in PROFILES.values()]
        ) or not isinstance(records, dict):
            raise ScriptError(f"invalid manifest target {target!r} in {path}")
        owned[target] = {}
        for name, record in records.items():
            if not isinstance(name, str) or not NAME.fullmatch(name):
                raise ScriptError(f"invalid manifest skill name {name!r} in {path}")
            if version == 1:
                record = {"source": "public", "digest": record}
            if (
                not isinstance(record, dict)
                or record.get("source") not in ("public", "private")
                or not isinstance(record.get("digest"), str)
                or not DIGEST.fullmatch(record["digest"])
            ):
                raise ScriptError(
                    f"invalid manifest ownership for {target}/{name} in {path}"
                )
            owned[target][name] = {
                "source": record["source"],
                "digest": record["digest"],
            }
    commands = data.get("commands", {}) if version == 2 else {}
    if not isinstance(commands, dict):
        raise ScriptError(f"invalid command ownership in {path}")
    for target, records in commands.items():
        if target not in COMMAND_TARGETS or not isinstance(records, dict):
            raise ScriptError(f"invalid command target {target!r} in {path}")
        for name, checksum in records.items():
            if (
                not isinstance(name, str)
                or not name.endswith(".md")
                or not NAME.fullmatch(name)
                or not isinstance(checksum, str)
                or not DIGEST.fullmatch(checksum)
            ):
                raise ScriptError(
                    f"invalid command ownership for {target}/{name} in {path}"
                )
    return owned


def load_commands(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("commands", {}) if data["version"] == 2 else {}


def save_manifest(
    path: Path, owned: Owned, commands: dict[str, dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix=".manifest-", dir=path.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        json.dump(
            {"version": 2, "targets": owned, "commands": commands},
            stream,
            indent=2,
            sort_keys=True,
        )
        stream.write("\n")
    temporary.replace(path)


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


def private_packages(root: Path, selected: list[str]) -> dict[str, Path]:
    if not selected:
        return {}
    if not root.is_dir() or root.is_symlink():
        raise ScriptError(
            f"private source {root} is missing or invalid; provide --private-root"
        )
    requested = set(selected)
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
        if name not in requested:
            continue
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
    missing = requested - packages.keys()
    if missing:
        raise ScriptError(
            f"requested private skill missing: {', '.join(sorted(missing))}; check --private-root"
        )
    return packages


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
    manifest: Path,
    sources: dict[str, Source],
    profile: str,
    retire: dict[str, str],
) -> tuple[list[Action], Owned]:
    previous = load_manifest(manifest)
    targets = PROFILES[profile]
    for name, checksum in retire.items():
        records = [previous.get(target, {}).get(name) for target in targets]
        present = [record for record in records if record is not None]
        if not present or any(
            record["source"] != "private" or record["digest"] != checksum
            for record in present
        ):
            raise ScriptError(
                f"private retirement {name!r} lacks matching ownership evidence in selected targets"
            )
    groups = target_groups(home, targets)
    owned: Owned = {target: records.copy() for target, records in previous.items()}
    actions: list[Action] = []
    for aliases in groups.values():
        target = aliases[0]
        recorded: dict[str, dict[str, str]] = {}
        for alias in aliases:
            for name, record in previous.get(alias, {}).items():
                if name in recorded and recorded[name] != record:
                    raise ScriptError(
                        f"manifest has conflicting ownership for ~/{target} and ~/{alias}"
                    )
                recorded[name] = record
        next_records = recorded.copy()
        for alias in aliases:
            owned[alias] = next_records
        for name in sorted(sources.keys() | recorded.keys() | retire.keys()):
            selected = sources.get(name)
            old = recorded.get(name)
            if name in EXCLUSIONS[profile] and name not in retire:
                continue
            if selected is None:
                if name in retire:
                    if old is None:
                        continue
                elif old is None or old["source"] == "private":
                    continue
            elif old is not None and old["source"] != selected.kind:
                raise ScriptError(
                    f"source ownership differs for ~/{target}/{name}; resolve the manifest before installing"
                )
            path = home / target / name
            label = f"~/{target}/{name}"
            if path.is_symlink() or (path.exists() and not path.is_dir()):
                actions.append(
                    Action(
                        target, name, "conflict", detail=f"{label} is a symlink or file"
                    )
                )
                continue
            current = digest(path) if path.exists() else None
            wanted = selected.digest if selected else None
            had = old["digest"] if old else None
            if current is not None and current not in (had, wanted):
                actions.append(
                    Action(
                        target,
                        name,
                        "conflict",
                        selected.kind if selected else old["source"] if old else None,
                        f"{label} was edited or is unowned; resolve it or use --force",
                    )
                )
                continue
            if selected:
                next_records[name] = {
                    "source": selected.kind,
                    "digest": selected.digest,
                }
                kind = (
                    "adopt"
                    if current == wanted and old is None
                    else "current"
                    if current == wanted
                    else "add"
                    if current is None
                    else "update"
                )
            else:
                next_records.pop(name, None)
                kind = "remove"
            actions.append(
                Action(
                    target,
                    name,
                    kind,
                    selected.kind if selected else old["source"] if old else None,
                )
            )
    return actions, owned


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


def plan_commands(
    home: Path, previous: dict[str, dict[str, str]], sources: dict[str, Source]
) -> tuple[list[Action], dict[str, dict[str, str]]]:
    owned = {target: records.copy() for target, records in previous.items()}
    actions: list[Action] = []
    for aliases in target_groups(home, COMMAND_TARGETS).values():
        target = aliases[0]
        recorded: dict[str, str] = {}
        for alias in aliases:
            for name, checksum in previous.get(alias, {}).items():
                if name in recorded and recorded[name] != checksum:
                    raise ScriptError(
                        f"manifest has conflicting command ownership for ~/{target} and ~/{alias}"
                    )
                recorded[name] = checksum
        next_records = recorded.copy()
        for alias in aliases:
            owned[alias] = next_records
        for name in sorted(sources.keys() | recorded.keys()):
            path = home / target / name
            source = sources.get(name)
            wanted = source.digest if source else None
            had = recorded.get(name)
            if path.is_symlink() or (path.exists() and not path.is_file()):
                actions.append(
                    Action(
                        target,
                        name,
                        "conflict",
                        "command",
                        f"~/{target}/{name} is a symlink or directory",
                    )
                )
                continue
            current = digest_command(path) if path.exists() else None
            if current is not None and current not in (had, wanted):
                actions.append(
                    Action(
                        target,
                        name,
                        "conflict",
                        "command",
                        f"~/{target}/{name} was edited or is unowned; resolve it or use --force",
                    )
                )
                continue
            if source:
                next_records[name] = wanted
                kind = (
                    "adopt"
                    if current == wanted and had is None
                    else "current"
                    if current == wanted
                    else "add"
                    if current is None
                    else "update"
                )
            else:
                next_records.pop(name, None)
                kind = "remove"
            actions.append(Action(target, name, kind, "command"))
    return actions, owned


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


def execute(
    home: Path,
    manifest: Path,
    sources: dict[str, Source],
    commands: dict[str, Source],
    actions: list[Action],
    owned: Owned,
    command_owned: dict[str, dict[str, str]],
    previous: Owned,
    previous_commands: dict[str, dict[str, str]],
) -> None:
    for action in actions:
        destination = home / action.target / action.name
        if action.kind in ("add", "update"):
            if action.source == "command":
                replace_command(commands[action.name].path, destination)
            else:
                replace(sources[action.name].path, destination)
        elif action.kind == "remove" and destination.exists():
            if action.source == "command":
                destination.unlink()
            else:
                shutil.rmtree(destination)
    if (
        owned != previous
        or command_owned != previous_commands
        or (
            manifest.exists()
            and json.loads(manifest.read_text(encoding="utf-8")).get("version") == 1
        )
    ):
        save_manifest(manifest, owned, command_owned)


def render(
    actions: list[Action], profile: str, dry_run: bool, json_output: bool, verbose: bool
) -> str:
    counts = Counter(action.kind for action in actions)
    if json_output:
        return json.dumps(
            {
                "profile": profile,
                "mode": "preview" if dry_run else "apply",
                "counts": dict(counts),
                "actions": [action.__dict__ for action in actions],
            },
            indent=2,
        )
    lines = [
        f"{'preview' if dry_run else 'applied'}: {profile}; "
        + ", ".join(
            f"{kind}={counts[kind]}"
            for kind in ("add", "update", "adopt", "remove", "current", "conflict")
        )
    ]
    if verbose:
        lines.extend(
            f"{action.kind}: ~/{action.target}/{action.name}"
            + (f" ({action.detail})" if action.detail else "")
            for action in actions
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""profiles:
  mac: ~/.pi/agent/skills, ~/.agents/skills, ~/.claude/skills,
       ~/.config/opencode/skills, ~/.config/agents/skills
  om1: ~/.pi/agent/skills, ~/.codex/skills, ~/.claude/skills,
       ~/.config/opencode/skills (excludes apple-mail)
  both: ~/.claude/commands, ~/.pi/agent/prompts, ~/.codex/prompts,
        ~/.config/opencode/commands, ~/.config/agents/commands

examples:
  just install-skills --dry-run --profile mac
  just install-skills --profile om1 --private transcript-sk
  just install-skills --check --json""",
    )
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="mac",
        help="local target set; mac is the default",
    )
    parser.add_argument(
        "--private",
        action="append",
        default=[],
        metavar="NAME",
        help="include a local ignored private package; repeatable",
    )
    parser.add_argument(
        "--private-root",
        type=Path,
        default=PRIVATE,
        help="private package tree (default: _skills_private/)",
    )
    parser.add_argument(
        "--retire-private",
        action="append",
        default=[],
        metavar="NAME:DIGEST",
        help="retire owned private skill only with its manifest digest",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="preview all actions, including conflicts, without writes; exit 0",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="preview and exit 1 if any selected target needs work or conflicts",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace edited or unowned copies after reviewing conflicts",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the per-target report as JSON"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show per-item detail and error tracebacks",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    state = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    manifest = state / "install-skills" / "manifest.json"
    try:
        retire: dict[str, str] = {}
        for item in args.retire_private:
            name, separator, checksum = item.partition(":")
            if (
                not separator
                or not NAME.fullmatch(name)
                or not DIGEST.fullmatch(checksum)
            ):
                raise ScriptError(
                    f"invalid --retire-private {item!r}; use NAME:DIGEST from the manifest"
                )
            retire[name] = checksum
        if set(retire) & set(args.private):
            raise ScriptError(
                "a private skill cannot be included and retired in the same run"
            )
        with tempfile.TemporaryDirectory(prefix=".install-skills-source-") as temporary:
            stage = Path(temporary) / "skills"
            files = flatten_skills.collect()
            stage.mkdir()
            sources: dict[str, Source] = {}
            for name, entries in files.items():
                package = stage / name
                for source, relative in entries:
                    destination = package / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                sources[name] = Source(package, "public", digest(package))
            for name, package in private_packages(
                args.private_root, args.private
            ).items():
                if name in sources:
                    raise ScriptError(
                        f"duplicate selected skill {name!r}: public and private"
                    )
                sources[name] = Source(package, "private", digest(package))
            if not sources:
                raise ScriptError("no public skills found; run just flatten-skills")
            commands = command_sources()
            actions, owned = plan(Path.home(), manifest, sources, args.profile, retire)
            previous_commands = load_commands(manifest)
            command_actions, command_owned = plan_commands(
                Path.home(), previous_commands, commands
            )
            actions.extend(command_actions)
            if args.force:
                actions = force_conflicts(
                    actions, owned, command_owned, sources, commands
                )
            report = render(
                actions,
                args.profile,
                args.dry_run or args.check,
                args.json,
                args.verbose,
            )
            if args.check:
                print(report)
                return int(any(action.kind not in ("current",) for action in actions))
            if args.dry_run:
                print(report)
                return 0
            if any(action.kind == "conflict" for action in actions):
                print(report)
                return 1
            previous = load_manifest(manifest)
            flatten_skills.flatten(dry_run=False)
            execute(
                Path.home(),
                manifest,
                sources,
                commands,
                actions,
                owned,
                command_owned,
                previous,
                previous_commands,
            )
            print(report)
            return 0
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except ScriptError as error:
        for message in error.args:
            print(f"error: {message}", file=sys.stderr)
    except Exception as error:
        log.debug("unexpected failure", exc_info=True)
        print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
    if not args.verbose:
        print("rerun with --verbose for details", file=sys.stderr)
    return 1


def force_conflicts(
    actions: list[Action],
    owned: Owned,
    command_owned: dict[str, dict[str, str]],
    sources: dict[str, Source],
    commands: dict[str, Source],
) -> list[Action]:
    forced: list[Action] = []
    for action in actions:
        if action.kind != "conflict" or "symlink or" in (action.detail or ""):
            forced.append(action)
            continue
        if action.source == "command":
            source = commands.get(action.name)
            forced.append(
                Action(
                    action.target,
                    action.name,
                    "update" if source else "remove",
                    "command",
                )
            )
            if source:
                command_owned[action.target][action.name] = source.digest
            else:
                command_owned[action.target].pop(action.name, None)
            continue
        source = sources.get(action.name)
        kind = "update" if source else "remove"
        forced.append(Action(action.target, action.name, kind, action.source))
        if source:
            owned[action.target][action.name] = {
                "source": source.kind,
                "digest": source.digest,
            }
        else:
            owned[action.target].pop(action.name, None)
    return forced


if __name__ == "__main__":
    raise SystemExit(main())

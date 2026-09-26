"""Update or verify Matt mode's vendored upstream source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

TOOLS = Path(__file__).resolve().parent
DEFAULT_ROOT = TOOLS.parent.parent
LOCK_PATH = PurePosixPath("matt-mode/upstream-lock.json")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
SKILL_CALL = re.compile(
    r"\b(?:call|calls|calling)\s+the Skill tool(?:\s+twice)?\s*,?\s*"
    r'(?:with|for)\s+(?P<names>"[a-z0-9-]+"'
    r'(?:\s*(?:,\s*(?:and\s+)?|and\s+)"[a-z0-9-]+")*)',
    re.IGNORECASE,
)
QUOTED_NAME = re.compile(r'"([a-z0-9-]+)"')
MARKDOWN_TARGET = re.compile(
    r"(?P<prefix>\]\()(?P<open><)?(?P<target>[^)\s>]+)(?P<close>>)?"
    r"(?P<tail>(?:\s+[^)]*)?\))"
)


class ImportError(RuntimeError):
    """A user-correctable import or integrity error."""


@dataclass(frozen=True)
class Mapping:
    name: str
    kind: str
    source: PurePosixPath
    destination: PurePosixPath
    entry: str
    exclude: tuple[PurePosixPath, ...]


@dataclass(frozen=True)
class FileRecord:
    source: PurePosixPath
    destination: PurePosixPath
    source_sha256: str
    rendered_sha256: str
    content: bytes


@dataclass(frozen=True)
class Registry:
    repository: str
    revision: str
    mappings: tuple[Mapping, ...]
    handoffs: dict[str, str]
    files: tuple[FileRecord, ...]


def fail(message: str) -> NoReturn:
    raise ImportError(message)


def safe_relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        fail(f"{label} is not a safe relative path: {value!r}")
    return path


def expect_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        fail(f"{label} must be a non-empty string")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"lock file is missing: {path}")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail(f"cannot read lock file {path}: {error}")
    if not isinstance(value, dict):
        fail(f"lock file must contain a JSON object: {path}")
    return value


def parse_registry(root: Path) -> Registry:
    lock_path = root / LOCK_PATH
    current = root
    for part in LOCK_PATH.parts:
        current /= part
        if current.is_symlink():
            fail(f"lock path contains a symlink: {current}")
    raw = load_json(lock_path)
    if raw.get("schema_version") != 1:
        fail("lock schema_version must be 1")
    repository = expect_string(raw.get("repository"), "repository")
    revision = expect_string(raw.get("revision"), "revision")
    if FULL_SHA.fullmatch(revision) is None:
        fail("lock revision must be a full lowercase Git SHA")

    raw_mappings = raw.get("mappings")
    if not isinstance(raw_mappings, list) or not raw_mappings:
        fail("lock mappings must be a non-empty list")
    mappings: list[Mapping] = []
    names: set[str] = set()
    sources: set[PurePosixPath] = set()
    destinations: set[PurePosixPath] = set()
    for index, item in enumerate(raw_mappings):
        label = f"mappings[{index}]"
        if not isinstance(item, dict):
            fail(f"{label} must be an object")
        name = expect_string(item.get("name"), f"{label}.name")
        kind = expect_string(item.get("kind"), f"{label}.kind")
        if kind not in {"internal", "shared"}:
            fail(f"{label}.kind must be internal or shared")
        source = safe_relative(item.get("source"), f"{label}.source")
        destination = safe_relative(item.get("destination"), f"{label}.destination")
        entry = expect_string(item.get("entry"), f"{label}.entry")
        if PurePosixPath(entry).name != entry or not entry.endswith(".md"):
            fail(f"{label}.entry must be one Markdown filename")
        raw_exclude = item.get("exclude")
        if not isinstance(raw_exclude, list):
            fail(f"{label}.exclude must be a list")
        exclude = tuple(
            safe_relative(value, f"{label}.exclude") for value in raw_exclude
        )
        if "SKILL.md" in {str(path) for path in exclude}:
            fail(f"{label}.exclude cannot omit SKILL.md")
        if name in names:
            fail(f"duplicate mapping name: {name}")
        if source in sources:
            fail(f"duplicate mapping source: {source}")
        if destination in destinations:
            fail(f"duplicate mapping destination: {destination}")
        names.add(name)
        sources.add(source)
        destinations.add(destination)
        mappings.append(Mapping(name, kind, source, destination, entry, exclude))

    raw_handoffs = raw.get("handoffs", {})
    if not isinstance(raw_handoffs, dict):
        fail("lock handoffs must be an object")
    handoffs: dict[str, str] = {}
    for raw_name, raw_target in raw_handoffs.items():
        name = expect_string(raw_name, "handoff name")
        target = expect_string(raw_target, f"handoffs[{name!r}]")
        if name in names:
            fail(f"handoff name conflicts with mapping name: {name}")
        handoffs[name] = target

    raw_files = raw.get("files")
    if not isinstance(raw_files, list):
        fail("lock files must be a list")
    files: list[FileRecord] = []
    file_destinations: set[PurePosixPath] = set()
    for index, item in enumerate(raw_files):
        label = f"files[{index}]"
        if not isinstance(item, dict):
            fail(f"{label} must be an object")
        source = safe_relative(item.get("source"), f"{label}.source")
        destination = safe_relative(item.get("destination"), f"{label}.destination")
        source_sha = expect_string(item.get("source_sha256"), f"{label}.source_sha256")
        rendered_sha = expect_string(
            item.get("rendered_sha256"), f"{label}.rendered_sha256"
        )
        for field_name, digest in (
            ("source_sha256", source_sha),
            ("rendered_sha256", rendered_sha),
        ):
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                fail(f"{label}.{field_name} must be a lowercase SHA256")
        if destination in file_destinations:
            fail(f"duplicate file destination: {destination}")
        file_destinations.add(destination)
        files.append(FileRecord(source, destination, source_sha, rendered_sha, b""))

    return Registry(repository, revision, tuple(mappings), handoffs, tuple(files))


def run_git(checkout: Path, *args: str, binary: bool = False) -> bytes | str:
    command = ["git", "-C", str(checkout), *args]
    try:
        result = subprocess.run(command, capture_output=True, check=False)
    except OSError as error:
        fail(f"cannot run git: {error}")
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"git {' '.join(args)} failed: {detail or 'unknown error'}")
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict").strip()


def verify_revision(checkout: Path, revision: str) -> None:
    if FULL_SHA.fullmatch(revision) is None:
        fail("--revision must be a full lowercase Git SHA")
    if not checkout.is_dir():
        fail(f"upstream checkout is not a directory: {checkout}")
    resolved = run_git(checkout, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if resolved != revision:
        fail(f"revision does not resolve to the requested commit: {revision}")


def git_tree(checkout: Path, revision: str, source: PurePosixPath) -> list[str]:
    raw = run_git(
        checkout,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        revision,
        "--",
        str(source),
        binary=True,
    )
    assert isinstance(raw, bytes)
    paths: list[str] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, encoded_path = record.split(b"\t", 1)
            mode, object_type, _object_id = metadata.decode("ascii").split(" ")
            path = encoded_path.decode("utf-8")
        except (ValueError, UnicodeError):
            fail(f"cannot parse Git tree entry below {source}")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            fail(f"unsupported Git tree entry {path}: {mode} {object_type}")
        paths.append(path)
    return sorted(paths)


def git_blob(checkout: Path, revision: str, source: PurePosixPath) -> bytes:
    raw = run_git(checkout, "show", f"{revision}:{source}", binary=True)
    assert isinstance(raw, bytes)
    return raw


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def strip_frontmatter(content: bytes, source: PurePosixPath) -> bytes:
    if not content.startswith(b"---\n"):
        fail(f"source entry has no opening frontmatter: {source}")
    end = content.find(b"\n---\n", 4)
    if end < 0:
        fail(f"source entry has unterminated frontmatter: {source}")
    return content[end + len(b"\n---\n") :]


def render_markdown(
    content: bytes,
    source: PurePosixPath,
    destination: PurePosixPath,
    entry_destinations: dict[PurePosixPath, PurePosixPath],
) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        fail(f"source Markdown is not UTF-8: {source}: {error}")

    def rewrite(match: re.Match[str]) -> str:
        if bool(match.group("open")) != bool(match.group("close")):
            return match.group(0)
        target = match.group("target")
        path_text, separator, fragment = target.partition("#")
        if (
            not path_text
            or path_text.startswith("/")
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path_text)
        ):
            return match.group(0)
        source_target = PurePosixPath(
            posixpath.normpath(str(source.parent / PurePosixPath(path_text)))
        )
        destination_target = entry_destinations.get(source_target)
        if destination_target is None:
            return match.group(0)
        if destination.parts[0] != destination_target.parts[0]:
            fail(
                "cross-package renamed-entry link requires maintainer classification: "
                f"{source} -> {source_target}"
            )
        rendered_target = posixpath.relpath(
            str(destination_target), start=str(destination.parent)
        )
        if path_text.startswith("./") and not rendered_target.startswith("."):
            rendered_target = f"./{rendered_target}"
        if separator:
            rendered_target = f"{rendered_target}#{fragment}"
        return (
            match.group("prefix")
            + (match.group("open") or "")
            + rendered_target
            + (match.group("close") or "")
            + match.group("tail")
        )

    return MARKDOWN_TARGET.sub(rewrite, text).encode("utf-8")


def skill_dependencies(content: bytes) -> set[str]:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        fail(f"source SKILL.md is not UTF-8: {error}")
    dependencies: set[str] = set()
    for match in SKILL_CALL.finditer(text):
        dependencies.update(QUOTED_NAME.findall(match.group("names")))
    return dependencies


def build_plan(
    checkout: Path, revision: str, registry: Registry
) -> tuple[FileRecord, ...]:
    verify_revision(checkout, revision)
    records: list[FileRecord] = []
    known_names = {mapping.name for mapping in registry.mappings} | set(
        registry.handoffs
    )
    entry_destinations = {
        mapping.source / "SKILL.md": mapping.destination / mapping.entry
        for mapping in registry.mappings
    }
    destinations: set[PurePosixPath] = set()
    found_dependencies: set[str] = set()

    license_source = PurePosixPath("LICENSE")
    if git_tree(checkout, revision, license_source) != ["LICENSE"]:
        fail("upstream LICENSE is missing or is not a regular file")
    license_content = git_blob(checkout, revision, license_source)
    license_destination = PurePosixPath("matt-mode/references/LICENSE")
    records.append(
        FileRecord(
            license_source,
            license_destination,
            sha256(license_content),
            sha256(license_content),
            license_content,
        )
    )
    destinations.add(license_destination)

    for mapping in registry.mappings:
        paths = git_tree(checkout, revision, mapping.source)
        if not paths:
            fail(f"mapped source directory is missing or empty: {mapping.source}")
        expected_entry = mapping.source / "SKILL.md"
        if str(expected_entry) not in paths:
            fail(f"mapped source entry is missing: {expected_entry}")
        prefix = f"{mapping.source}/"
        relative_paths = [
            safe_relative(
                path.removeprefix(prefix), f"source file below {mapping.source}"
            )
            for path in paths
        ]
        nested_skills = [
            path
            for path in relative_paths
            if path.name == "SKILL.md" and path.parts != ("SKILL.md",)
        ]
        if nested_skills:
            names = ", ".join(str(path) for path in nested_skills)
            fail(
                f"new nested Skill source requires maintainer classification: {mapping.name}: {names}"
            )
        excluded = set(mapping.exclude)
        missing_exclusions = excluded - set(relative_paths)
        if missing_exclusions:
            names = ", ".join(str(path) for path in sorted(missing_exclusions))
            fail(f"declared metadata exclusion is missing: {mapping.name}: {names}")

        for source_path, relative in zip(paths, relative_paths, strict=True):
            if relative in excluded:
                continue
            source = PurePosixPath(source_path)
            raw = git_blob(checkout, revision, source)
            if relative.suffix.lower() == ".md":
                found_dependencies.update(skill_dependencies(raw))
            if relative.parts == ("SKILL.md",):
                destination = mapping.destination / mapping.entry
                rendered = render_markdown(
                    strip_frontmatter(raw, source),
                    source,
                    destination,
                    entry_destinations,
                )
            else:
                destination = mapping.destination / relative
                rendered = (
                    render_markdown(raw, source, destination, entry_destinations)
                    if relative.suffix.lower() == ".md"
                    else raw
                )
            if destination in destinations:
                fail(f"colliding generated destination: {destination}")
            destinations.add(destination)
            records.append(
                FileRecord(
                    source,
                    destination,
                    sha256(raw),
                    sha256(rendered),
                    rendered,
                )
            )

    unknown = found_dependencies - known_names
    if unknown:
        fail(
            "unclassified Skill dependencies: "
            + ", ".join(sorted(unknown))
            + "; add mappings or classify them before updating"
        )
    return tuple(sorted(records, key=lambda record: str(record.destination)))


def lock_document(
    registry: Registry, revision: str, files: Sequence[FileRecord]
) -> bytes:
    value = {
        "schema_version": 1,
        "repository": registry.repository,
        "revision": revision,
        "mappings": [
            {
                "name": mapping.name,
                "kind": mapping.kind,
                "source": str(mapping.source),
                "destination": str(mapping.destination),
                "entry": mapping.entry,
                "exclude": [str(path) for path in mapping.exclude],
            }
            for mapping in registry.mappings
        ],
        "handoffs": registry.handoffs,
        "files": [
            {
                "source": str(record.source),
                "destination": str(record.destination),
                "source_sha256": record.source_sha256,
                "rendered_sha256": record.rendered_sha256,
            }
            for record in files
        ],
    }
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def local_path(root: Path, relative: PurePosixPath) -> Path:
    return root.joinpath(*relative.parts)


def reject_symlink_path(root: Path, relative: PurePosixPath) -> None:
    current = root
    if current.is_symlink():
        fail(f"bucket root cannot be a symlink: {root}")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            fail(f"generated path contains a symlink: {current}")


def current_digest(path: Path) -> str | None:
    try:
        if not path.exists():
            return None
        if not path.is_file():
            fail(f"generated path is not a regular file: {path}")
        return sha256(path.read_bytes())
    except OSError as error:
        fail(f"cannot inspect generated file {path}: {error}")


def preflight_update(
    root: Path, registry: Registry, planned: Sequence[FileRecord]
) -> tuple[list[FileRecord], list[PurePosixPath]]:
    old_by_destination = {record.destination: record for record in registry.files}
    new_by_destination = {record.destination: record for record in planned}
    writes: list[FileRecord] = []

    for destination, record in new_by_destination.items():
        reject_symlink_path(root, destination)
        path = local_path(root, destination)
        digest = current_digest(path)
        accepted = {record.rendered_sha256}
        old = old_by_destination.get(destination)
        if old is not None:
            accepted.add(old.rendered_sha256)
        if digest is not None and digest not in accepted:
            fail(
                f"refusing to overwrite locally modified generated file: {destination}"
            )
        if digest != record.rendered_sha256:
            writes.append(record)

    removals: list[PurePosixPath] = []
    for destination, old in old_by_destination.items():
        if destination in new_by_destination:
            continue
        reject_symlink_path(root, destination)
        path = local_path(root, destination)
        digest = current_digest(path)
        if digest is None:
            continue
        if digest != old.rendered_sha256:
            fail(f"refusing to delete locally modified generated file: {destination}")
        removals.append(destination)
    return sorted(writes, key=lambda item: str(item.destination)), sorted(removals)


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except OSError as error:
        try:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        except OSError:
            pass
        fail(f"cannot write {path}: {error}")


def prune_empty_parents(path: Path, stop: Path) -> None:
    parent = path.parent
    while parent != stop:
        try:
            parent.rmdir()
        except OSError:
            return
        parent = parent.parent


def generated_inventory(root: Path, registry: Registry) -> set[PurePosixPath]:
    inventory: set[PurePosixPath] = set()
    generated_roots = {
        PurePosixPath("matt-mode/playbooks")
        if mapping.kind == "internal"
        else mapping.destination
        for mapping in registry.mappings
    }
    for generated_root in sorted(generated_roots):
        directory = local_path(root, generated_root)
        reject_symlink_path(root, generated_root)
        if not directory.exists():
            continue
        if not directory.is_dir():
            fail(f"generated directory is not a directory: {generated_root}")
        for path in directory.rglob("*"):
            relative = PurePosixPath(path.relative_to(root).as_posix())
            reject_symlink_path(root, relative)
            if path.is_file():
                inventory.add(relative)
            elif not path.is_dir():
                fail(f"unsupported generated filesystem entry: {relative}")
    license_path = local_path(root, PurePosixPath("matt-mode/references/LICENSE"))
    if license_path.exists():
        inventory.add(PurePosixPath("matt-mode/references/LICENSE"))
    return inventory


def verify_imports(root: Path, upstream: Path | None = None) -> list[str]:
    try:
        registry = parse_registry(root)
    except ImportError as error:
        return [str(error)]
    errors: list[str] = []
    expected = {record.destination: record for record in registry.files}
    for destination, record in expected.items():
        try:
            reject_symlink_path(root, destination)
            digest = current_digest(local_path(root, destination))
        except ImportError as error:
            errors.append(str(error))
            continue
        if digest is None:
            errors.append(f"missing generated file: {destination}")
        elif digest != record.rendered_sha256:
            errors.append(f"changed generated file: {destination}")
    try:
        actual = generated_inventory(root, registry)
    except ImportError as error:
        errors.append(str(error))
        actual = set()
    for destination in sorted(actual - set(expected)):
        errors.append(f"untracked generated file: {destination}")

    if upstream is not None:
        try:
            planned = build_plan(upstream, registry.revision, registry)
            planned_by_destination = {record.destination: record for record in planned}
            if set(planned_by_destination) != set(expected):
                missing = sorted(set(planned_by_destination) - set(expected))
                stale = sorted(set(expected) - set(planned_by_destination))
                for destination in missing:
                    errors.append(f"lock omits upstream file: {destination}")
                for destination in stale:
                    errors.append(f"lock contains stale upstream file: {destination}")
            for destination in sorted(set(expected) & set(planned_by_destination)):
                locked = expected[destination]
                source = planned_by_destination[destination]
                if locked.source != source.source:
                    errors.append(f"source path mismatch for {destination}")
                if locked.source_sha256 != source.source_sha256:
                    errors.append(f"source hash mismatch for {destination}")
                if locked.rendered_sha256 != source.rendered_sha256:
                    errors.append(f"rendered hash mismatch for {destination}")
        except ImportError as error:
            errors.append(str(error))
    return sorted(set(errors))


def command_check(args: argparse.Namespace) -> int:
    root = args.root.absolute()
    errors = verify_imports(root, args.upstream.resolve() if args.upstream else None)
    if errors:
        print("Matt mode import check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    registry = parse_registry(root)
    print(
        f"OK: Matt mode imports match {registry.revision} ({len(registry.files)} files)"
    )
    return 0


def command_update(args: argparse.Namespace) -> int:
    root = args.root.absolute()
    registry = parse_registry(root)
    planned = build_plan(args.upstream.resolve(), args.revision, registry)
    writes, removals = preflight_update(root, registry, planned)
    lock_content = lock_document(registry, args.revision, planned)
    lock_file = local_path(root, LOCK_PATH)
    try:
        existing_lock = lock_file.read_bytes()
    except OSError as error:
        fail(f"cannot read lock file {lock_file}: {error}")
    lock_changed = existing_lock != lock_content

    if not writes and not removals and not lock_changed:
        print(f"Matt mode is already at {args.revision}; no changes")
        return 0

    if args.dry_run:
        print(f"Would update Matt mode from {registry.revision} to {args.revision}")
        for record in writes:
            print(f"  write {record.destination}")
        for destination in removals:
            print(f"  remove {destination}")
        if lock_changed:
            print(f"  write {LOCK_PATH}")
        return 0

    for record in writes:
        atomic_write(local_path(root, record.destination), record.content)
    for destination in removals:
        path = local_path(root, destination)
        try:
            path.unlink()
        except OSError as error:
            fail(f"cannot remove stale generated file {destination}: {error}")
        prune_empty_parents(path, root)
    atomic_write(lock_file, lock_content)
    print(f"Updated Matt mode from {registry.revision} to {args.revision}")
    print(f"  wrote {len(writes)} generated file(s)")
    print(f"  removed {len(removals)} stale generated file(s)")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Verify or update Matt mode's pinned upstream imports."
    )
    subparsers = result.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser(
        "check", help="verify the lock and generated files without network access"
    )
    check.add_argument(
        "--upstream",
        type=Path,
        help="local Git checkout used to reconstruct the pinned revision",
    )
    check.add_argument(
        "--root", type=Path, default=DEFAULT_ROOT, help="Matt skill bucket root"
    )
    check.set_defaults(handler=command_check)

    update = subparsers.add_parser(
        "update", help="render one immutable upstream Git revision"
    )
    update.add_argument(
        "--upstream", type=Path, required=True, help="local Git checkout"
    )
    update.add_argument(
        "--revision", required=True, help="full immutable upstream commit SHA"
    )
    update.add_argument(
        "--dry-run", action="store_true", help="print the complete plan without writing"
    )
    update.add_argument(
        "--root", type=Path, default=DEFAULT_ROOT, help="Matt skill bucket root"
    )
    update.set_defaults(handler=command_update)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except ImportError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

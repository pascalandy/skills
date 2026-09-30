# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Import Corey Haines' marketing skills as corey-mode playbooks, or verify them."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import NoReturn

PACKAGE = Path(__file__).resolve().parent.parent
REPOSITORY = "https://github.com/coreyhaines31/marketingskills"
LOCK = PurePosixPath("upstream-lock.json")
PLAYBOOKS = PurePosixPath("playbooks")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
FULL_HASH = re.compile(r"[0-9a-f]{64}")
LINK = re.compile(r"(?P<head>\]\()(?P<target>[^)\s]+)(?P<tail>(?:\s+[^)]*)?\))")
ROUTE = re.compile(r"^\|\s*\[`(?P<name>[^`]+)`\]\((?P<target>[^)]+)\)\s*\|")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

EPILOG = """\
examples:
  update_corey_mode.py check
  update_corey_mode.py check --upstream DIR
  update_corey_mode.py update --upstream DIR --revision SHA --dry-run
  update_corey_mode.py update --upstream DIR --revision SHA

exit codes:
  0  success, including a no-op
  1  the package drifted from the lock or the upstream, or the update failed
  2  bad usage
  130  interrupted
"""


class Failure(Exception):
    """An expected failure; each argument is one message."""


@dataclass(frozen=True)
class Rendered:
    source: PurePosixPath
    content: bytes


Plan = dict[PurePosixPath, Rendered]


@dataclass(frozen=True)
class Locked:
    revision: str
    hashes: dict[PurePosixPath, str]


def destination(source: PurePosixPath) -> PurePosixPath | None:
    """Where an upstream file lives in the package, or None when it stays out."""
    if source == PurePosixPath("LICENSE"):
        return PurePosixPath("references/LICENSE")
    parts = source.parts
    if len(parts) < 3 or parts[0] != "skills" or "evals" in parts[2:-1]:
        return None
    name = parts[1]
    if parts[2:] == ("SKILL.md",):
        return PLAYBOOKS / name / f"{name}.md"
    return PLAYBOOKS.joinpath(name, *parts[2:])


def upstream_files(upstream: Path) -> set[PurePosixPath]:
    if not (upstream / "skills").is_dir() or not (upstream / "LICENSE").is_file():
        raise Failure(
            f"{upstream} is not a marketingskills checkout: it needs skills/ and LICENSE",
            "pass --upstream the snapshot folder, such as "
            "$OPENSRC_HOME/repos/github.com/coreyhaines31/marketingskills/main",
        )
    return {
        PurePosixPath(path.relative_to(upstream).as_posix())
        for path in upstream.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(upstream).parts)
    }


def rewrite_links(
    text: str,
    source: PurePosixPath,
    target_of: dict[PurePosixPath, PurePosixPath],
    files: set[PurePosixPath],
    revision: str,
) -> str:
    """Point each link at the package copy, or at GitHub when the file stays out.

    A link that is already broken upstream keeps its text.
    """
    folders = {parent for path in files for parent in path.parents}
    here = target_of[source].parent

    def replace(match: re.Match[str]) -> str:
        path, hash_, anchor = match["target"].partition("#")
        if not path or SCHEME.match(path) or path.startswith("/"):
            return match[0]
        resolved = PurePosixPath(posixpath.normpath(str(source.parent / path)))
        if resolved.parts[:1] == ("..",):
            return match[0]
        local = target_of.get(resolved)
        if local is not None:
            if posixpath.normpath(str(here / path)) == str(local):
                return match[0]
            new = posixpath.relpath(str(local), str(here))
        elif resolved in files:
            new = f"{REPOSITORY}/blob/{revision}/{resolved}"
        elif resolved in folders:
            new = f"{REPOSITORY}/tree/{revision}/{resolved}"
        else:
            return match[0]
        return f"{match['head']}{new}{hash_}{anchor}{match['tail']}"

    return LINK.sub(replace, text)


def render(upstream: Path, revision: str) -> Plan:
    files = upstream_files(upstream)
    target_of = {
        source: dest for source in files if (dest := destination(source)) is not None
    }
    clashes = len(target_of) - len(set(target_of.values()))
    if clashes:
        raise Failure(f"{clashes} upstream files map to the same package path")
    plan: Plan = {}
    for source, dest in target_of.items():
        content = (upstream / source).read_bytes()
        if source.suffix == ".md":
            text = rewrite_links(
                content.decode("utf-8"), source, target_of, files, revision
            )
            content = text.encode("utf-8")
        plan[dest] = Rendered(source, content)
    return plan


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def lock_document(plan: Plan, revision: str) -> bytes:
    document = {
        "schema_version": 1,
        "repository": REPOSITORY,
        "revision": revision,
        "files": {
            str(dest): {"source": str(item.source), "sha256": sha256(item.content)}
            for dest, item in sorted(plan.items())
        },
    }
    return (json.dumps(document, indent=2) + "\n").encode("utf-8")


def read_lock(package: Path) -> Locked | None:
    """Parse the lock, refusing any path the importer would not write itself."""
    path = package / LOCK

    def invalid(reason: str) -> NoReturn:
        raise Failure(
            f"{path}: invalid lock: {reason}",
            f"restore a valid {LOCK}, then run "
            f"'update_corey_mode.py check --package {package}'",
        )

    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as error:
        invalid(str(error))
    if not isinstance(raw, dict):
        invalid("expected a JSON object")
    if raw.get("schema_version") != 1:
        invalid("schema_version must be 1")
    if raw.get("repository") != REPOSITORY:
        invalid(f"repository must be {REPOSITORY}")
    revision = raw.get("revision")
    if not isinstance(revision, str) or not FULL_SHA.fullmatch(revision):
        invalid("revision must be a full 40-character SHA")
    files = raw.get("files")
    if not isinstance(files, dict) or not files:
        invalid("files must be a non-empty object")
    hashes: dict[PurePosixPath, str] = {}
    for dest, entry in files.items():
        if not isinstance(entry, dict):
            invalid(f"invalid file record: {dest!r}")
        source, digest = entry.get("source"), entry.get("sha256")
        target = PurePosixPath(dest)
        if (
            not isinstance(source, str)
            or ".." in target.parts
            or str(target) != dest
            or destination(PurePosixPath(source)) != target
        ):
            invalid(f"{dest!r} is not where the importer writes {source!r}")
        if not isinstance(digest, str) or not FULL_HASH.fullmatch(digest):
            invalid(f"{dest}: sha256 must be a 64-character hash")
        hashes[target] = digest
    return Locked(revision, hashes)


def owned(package: Path, lock: Locked | None) -> set[PurePosixPath]:
    """Files the importer writes: everything in the lock and under playbooks/."""
    paths = set(lock.hashes) if lock else set()
    if (package / PLAYBOOKS).is_dir():
        paths |= {
            PurePosixPath(path.relative_to(package).as_posix())
            for path in (package / PLAYBOOKS).rglob("*")
            if path.is_file()
        }
    return paths


def update(package: Path, upstream: Path, revision: str, dry_run: bool) -> str:
    plan = render(upstream, revision)
    lock = read_lock(package)
    files = {dest: item.content for dest, item in plan.items()}
    files[LOCK] = lock_document(plan, revision)
    changes: list[str] = []
    for dest in sorted(owned(package, lock) - set(plan)):
        changes.append(f"delete\t{dest}")
        if not dry_run:
            (package / dest).unlink(missing_ok=True)
    for dest, content in sorted(files.items()):
        path = package / dest
        if path.is_file() and path.read_bytes() == content:
            continue
        changes.append(f"{'update' if path.exists() else 'add'}\t{dest}")
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if not dry_run and (package / PLAYBOOKS).is_dir():
        for folder in sorted((package / PLAYBOOKS).rglob("*"), reverse=True):
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
    return "\n".join(changes)


def markdown_links(text: str) -> list[str]:
    links: list[str] = []
    in_code = False
    for line in text.splitlines():
        if FENCE.match(line):
            in_code = not in_code
        elif not in_code:
            links += [match["target"] for match in LINK.finditer(line)]
    return links


def check_routes(package: Path) -> list[str]:
    problems: list[str] = []
    rows = [
        match
        for line in (package / "SKILL.md").read_text(encoding="utf-8").splitlines()
        if (match := ROUTE.match(line))
    ]
    names = [row["name"] for row in rows]
    for name in sorted({name for name in names if names.count(name) > 1}):
        problems.append(f"duplicate route: {name}")
    for row in rows:
        expected = f"{PLAYBOOKS}/{row['name']}/{row['name']}.md"
        if row["target"] != expected:
            problems.append(
                f"route {row['name']} links to {row['target']}, not {expected}"
            )
    folders = (
        {path.name for path in (package / PLAYBOOKS).iterdir() if path.is_dir()}
        if (package / PLAYBOOKS).is_dir()
        else set()
    )
    for name in sorted(set(names) - folders):
        problems.append(f"route without a playbook: {name}")
    for name in sorted(folders - set(names)):
        problems.append(f"playbook without a route: {name}")
    return problems


def check(package: Path, upstream: Path | None) -> None:
    lock = read_lock(package)
    if lock is None:
        raise Failure(
            f"{package / LOCK} is missing",
            "import upstream with: update_corey_mode.py update --upstream DIR --revision SHA",
        )
    problems: list[str] = []
    entries = lock.hashes
    for dest, digest in sorted(entries.items()):
        path = package / dest
        if not path.is_file():
            problems.append(f"missing: {dest}")
        elif sha256(path.read_bytes()) != digest:
            problems.append(f"changed: {dest}")
    for dest in sorted(owned(package, lock) - entries.keys()):
        problems.append(f"not in the lock: {dest}")
    for path in sorted(package.rglob("SKILL.md")):
        if path != package / "SKILL.md":
            problems.append(f"nested SKILL.md: {path.relative_to(package)}")
    stale = bool(problems)
    routes = check_routes(package)
    problems += routes
    for path in sorted(package.rglob("*.md")):
        relative = PurePosixPath(path.relative_to(package).as_posix())
        if relative in entries:
            continue
        for target in markdown_links(path.read_text(encoding="utf-8")):
            link = target.partition("#")[0]
            if link and not SCHEME.match(link) and not (path.parent / link).exists():
                problems.append(f"broken link in {relative}: {target}")
    if upstream is not None:
        revision = lock.revision
        plan = render(upstream, revision)
        if lock_document(plan, revision) != (package / LOCK).read_bytes():
            problems.append(f"{LOCK} differs from a fresh render of {upstream}")
            stale = True
        for dest, item in sorted(plan.items()):
            path = package / dest
            if not path.is_file() or path.read_bytes() != item.content:
                problems.append(f"differs from upstream: {dest}")
                stale = True
    if stale:
        problems.append(
            "regenerate with: update_corey_mode.py update --upstream DIR --revision SHA"
        )
    if routes:
        problems.append("give each folder in playbooks/ exactly one row in SKILL.md")
    if problems:
        raise Failure(*problems)


def full_sha(value: str) -> str:
    if not FULL_SHA.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"must be a full 40-character SHA, got {value!r}"
        )
    return value


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        print(f"run '{self.prog} --help'", file=sys.stderr)
        raise SystemExit(2)


def parser() -> Parser:
    result = Parser(
        prog="update_corey_mode.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
        allow_abbrev=False,
    )
    commands = result.add_subparsers(dest="command", required=True, parser_class=Parser)

    def subcommand(
        name: str, summary: str, description: str
    ) -> argparse.ArgumentParser:
        return commands.add_parser(
            name,
            help=summary,
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=EPILOG,
            allow_abbrev=False,
        )

    check_command = subcommand(
        "check",
        "verify the playbooks against the lock, offline by default",
        "Verify the playbooks, the lock, and the route table.",
    )
    check_command.add_argument(
        "--upstream", type=Path, help="upstream folder to rebuild the files from"
    )
    update_command = subcommand(
        "update",
        "import one upstream revision",
        "Rewrite playbooks/, references/LICENSE, and the lock.",
    )
    update_command.add_argument(
        "--upstream", type=Path, required=True, help="upstream folder to import"
    )
    update_command.add_argument(
        "--revision",
        type=full_sha,
        required=True,
        help="full commit SHA of that folder",
    )
    update_command.add_argument(
        "-n", "--dry-run", action="store_true", help="print the changes, write nothing"
    )
    for command in (check_command, update_command):
        command.add_argument(
            "--package", type=Path, default=PACKAGE, help="corey-mode package folder"
        )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "update":
            output = update(args.package, args.upstream, args.revision, args.dry_run)
            if output:
                print(output)
        else:
            check(args.package, args.upstream)
    except Failure as failure:
        for message in failure.args:
            print(message, file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

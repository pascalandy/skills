"""Every scripts/ entry point is registered, and its --help shows that it uses the shared parser.

test_cli.py tests the parser and the contract behavior once; this suite checks
each script is wired to it, and that doc lines running a script use only flags
its help lists. The contract is in docs/references/script-conventions.md.
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from collections.abc import Iterator, Sequence
from itertools import takewhile
from pathlib import Path

import pytest
from conftest import SCRIPTS

ROOT = SCRIPTS.parent

# Each scripts/ entry point and the name its usage line prints
ENTRIES = {
    "scripts/check.py": "just check",
    "scripts/check_cli_block.py": "scripts/check_cli_block.py",
    "scripts/check_frontmatter.py": "just check-frontmatter",
    "scripts/discover_skills.py": "just skills-discover",
    "scripts/flatten_skills.py": "just flatten-skills",
    "scripts/install_skills.py": "just install-skills",
    "scripts/release_check.py": "just release-check",
    "scripts/remote_skills.py": "just remote-skills",
    "scripts/signoff.py": "just signoff",
    "scripts/sync.py": "just sync",
    "scripts/sync_fleet.py": "just sync-fleet",
    "scripts/sync_private.py": "scripts/sync_private.py",
}


def section(text: str, title: str) -> list[str]:
    """The lines under `title:` in a help page, up to the next blank line."""
    lines = text.splitlines()
    return list(takewhile(str.strip, lines[lines.index(f"{title}:") + 1 :]))


FLAG = re.compile(r"(?<![\w/.-])(--?[A-Za-z][\w-]*)")


def accepted(flag: str, allowed: set[str]) -> bool:
    """Whether the script takes `flag`, reading `-vn` as `-v -n`."""
    if flag in allowed:
        return True
    return not flag.startswith("--") and all(f"-{c}" in allowed for c in flag[1:])


def recipes() -> dict[str, str]:
    """Each justfile recipe that runs a scripts/ file, mapped to that file."""
    found: dict[str, str] = {}
    name = ""
    for line in (ROOT / "justfile").read_text(encoding="utf-8").splitlines():
        if header := re.match(r"([a-z][\w-]*)[^:=]*:(?!=)", line):
            name = header[1]
        elif name and (target := re.search(r"\bscripts/\w+\.py", line)):
            found[name] = target[0]
    return found


def doc_sources() -> Iterator[Path]:
    """Files whose lines may run a script: docs, hooks, CI, and scripts/."""
    for name in ("README.md", "AGENTS.md", "CHANGELOG.md", "justfile", "lefthook.yml"):
        yield ROOT / name
    yield from (ROOT / "docs").rglob("*.md")
    yield from (ROOT / "authoring").rglob("*.md")
    yield from (ROOT / ".github").rglob("*.yml")
    yield from (path for path in (ROOT / ".lefthook").rglob("*") if path.is_file())
    yield from SCRIPTS.glob("*.py")


# What ends a command inside a line: shell operators everywhere, closing quotes
# in Python strings, and code spans or table cells in Markdown
ENDINGS = {".py": "`\"'", ".md": "`|"}


def doc_flags(path: str) -> Iterator[tuple[str, str]]:
    """Each flag a doc line passes to the script, with where the line is."""
    names = [name for name, target in recipes().items() if target == path]
    runs = re.compile(
        "|".join(
            [rf"\bjust {re.escape(name)}(?![\w-])" for name in names]
            + [rf"(?<![\w/]){re.escape(path)}(?![\w.])"]
        )
    )
    for source in doc_sources():
        stop = re.compile(
            r"&&|\|\||[;#<>()]"
            + (
                f"|[{re.escape(ENDINGS[source.suffix])}]"
                if source.suffix in ENDINGS
                else ""
            )
        )
        lines = source.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            for match in runs.finditer(line):
                rest = line[match.end() :]
                end = stop.search(rest)
                for flag in FLAG.findall(rest[: end.start() if end else None]):
                    yield flag, f"{source.relative_to(ROOT)}:{number}"


CONTRACT_DOC = ROOT / "docs/references/script-conventions.md"

CONTRACT_COMMAND = ROOT / "authoring/commands/cli-contract.md"


def headings(lines: Sequence[str]) -> Iterator[tuple[int, str]]:
    """Every `## ` line outside a fence, so an example heading ends no section."""
    fence = ""
    for offset, line in enumerate(lines):
        marker = line[:3]
        if marker in ("```", "~~~"):
            fence = "" if fence == marker else fence or marker
        if not fence and line.startswith("## "):
            yield offset, line


def contract_sections(path: Path) -> str:
    """The Baseline and Opt-in sections, from their file's own headings.

    The span ends at the first heading after Baseline that is not Opt-in, so
    each file keeps its own sections around the shared ones.
    """
    lines = path.read_text().splitlines()
    found = dict(headings(lines))
    assert "## Baseline" in found.values(), f"{path.name} has no Baseline section"
    start = next(offset for offset, line in found.items() if line == "## Baseline")
    end = next(
        (
            offset
            for offset, line in found.items()
            if offset > start and line != "## Opt-in"
        ),
        len(lines),
    )
    return "\n".join(lines[start:end]).strip("\n")


def test_the_portable_command_copies_the_contract_word_for_word() -> None:
    """authoring/commands/cli-contract.md carries the contract outside this repo."""
    doc = contract_sections(CONTRACT_DOC)
    command = contract_sections(CONTRACT_COMMAND)

    assert command == doc, (
        f"{CONTRACT_COMMAND.name} and {CONTRACT_DOC.name} disagree; "
        "edit the doc, then copy its Baseline and Opt-in sections across"
    )


def test_every_entry_point_is_registered() -> None:
    found = {
        f"scripts/{path.name}"
        for path in SCRIPTS.glob("*.py")
        if not path.name.startswith("_")
    }

    assert sorted(found) == sorted(ENTRIES)


@pytest.mark.parametrize(("path", "name"), sorted(ENTRIES.items()))
def test_help_comes_from_the_shared_parser_and_docs_use_only_its_flags(
    path: str, name: str
) -> None:
    shown = subprocess.run(
        [sys.executable, str(ROOT / path), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    codes = [int(line.split()[0]) for line in section(shown.stdout, "exit codes")]
    allowed = set(FLAG.findall("\n".join(section(shown.stdout, "options"))))
    unknown = [
        f"{where}: {flag}"
        for flag, where in doc_flags(path)
        if not accepted(flag, allowed)
    ]

    assert (shown.returncode, shown.stderr) == (0, "")
    assert shown.stdout.startswith(f"usage: {name} ")
    assert section(shown.stdout, "examples")
    assert codes == list(importlib.import_module(Path(path).stem).EXIT_CODES)
    assert unknown == []

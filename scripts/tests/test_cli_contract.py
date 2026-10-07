"""Every scripts/ entry point is registered, uses the shared parser, and answers
in one JSON line.

test_cli.py tests the parser and the contract behavior once; this suite checks
each script is wired to it, that doc lines running a script use only flags its
help lists, and that nothing but answer() writes to stdout. The contract is
in docs/references/script-conventions.md, the output in script-output.md.
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from itertools import takewhile
from pathlib import Path

import pytest
from conftest import SCRIPTS

ROOT = SCRIPTS.parent

# Each scripts/ entry point and the name its usage line prints
ENTRIES = {
    "scripts/api_keys_validation.py": "just api-keys-validation",
    "scripts/check.py": "just check",
    "scripts/check_cli_block.py": "scripts/check_cli_block.py",
    "scripts/check_frontmatter.py": "just check-frontmatter",
    "scripts/discover_skills.py": "just skills-discover",
    "scripts/compile_skills.py": "just compile-skills",
    "scripts/install_skills.py": "just install-skills",
    "scripts/merge.py": "just merge",
    "scripts/release_check.py": "just release-check",
    "scripts/remote_skills.py": "just remote-skills",
    "scripts/replay_routing.py": "just replay-routing",
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
    yield from (ROOT / "commands").rglob("*.md")
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
        env={**os.environ, "PATH": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert (shown.returncode, shown.stderr) == (0, "")
    assert shown.stdout.startswith(f"usage: {name} ")
    codes = [int(line.split()[0]) for line in section(shown.stdout, "exit codes")]
    allowed = set(FLAG.findall("\n".join(section(shown.stdout, "options"))))
    unknown = [
        f"{where}: {flag}"
        for flag, where in doc_flags(path)
        if not accepted(flag, allowed)
    ]

    assert section(shown.stdout, "examples")
    assert codes == list(importlib.import_module(Path(path).stem).EXIT_CODES)
    assert unknown == []


@pytest.mark.parametrize("path", sorted(ENTRIES))
def test_a_usage_error_answers_in_one_json_line_and_exits_2(path: str) -> None:
    refused = subprocess.run(
        [sys.executable, str(ROOT / path), "--no-such-flag"],
        cwd=ROOT,
        env={**os.environ, "PATH": ""},
        capture_output=True,
        text=True,
        check=False,
    )

    assert (refused.returncode, refused.stdout) == (2, "")
    answer = json.loads(refused.stderr.splitlines()[-1])
    assert answer["ok"] is False
    assert answer["errors"]


def stdout_writes(source: str, allowed: str = "") -> list[int]:
    """The lines of `source` that write to stdout, a print() without file= or any
    sys.stdout, outside the function named `allowed`."""
    tree = ast.parse(source)
    skipped = {
        id(node)
        for function in ast.walk(tree)
        if isinstance(function, ast.FunctionDef) and function.name == allowed
        for node in ast.walk(function)
    }
    found: set[int] = set()
    for node in ast.walk(tree):
        if id(node) in skipped:
            continue
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "print":
            if not any(keyword.arg == "file" for keyword in node.keywords):
                found.add(node.lineno)
        elif isinstance(node, ast.Attribute) and ast.unparse(node) == "sys.stdout":
            found.add(node.lineno)
    return sorted(found)


def warnings_in(source: str) -> list[int]:
    """The lines of `source` that log a warning, which a success would hide."""
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("warning", "warn")
        and ast.unparse(node.func.value) in ("log", "logging")
    ]


@pytest.mark.parametrize(
    ("source", "writes", "warns"),
    [
        ('print("done")', [1], []),
        ('import sys\nsys.stdout.write("done")', [2], []),
        ('import sys\nprint("note", file=sys.stderr)', [], []),
        ('log.warning("stale cache")', [], [1]),
        ('logging.warning("stale cache")', [], [1]),
        ('log.info("stale cache")', [], []),
    ],
    ids=["print", "sys-stdout", "stderr", "log-warning", "logging-warning", "info"],
)
def test_the_lock_flags_a_write_beside_the_answer_and_a_warning(
    source: str, writes: list[int], warns: list[int]
) -> None:
    assert (stdout_writes(source), warnings_in(source)) == (writes, warns)


def test_only_the_answer_writes_to_stdout_and_no_script_warns() -> None:
    found = []
    for path in sorted(SCRIPTS.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        allowed = "answer" if path.name == "_cli.py" else ""
        found += [
            f"{path.name}:{line} writes to stdout"
            for line in stdout_writes(source, allowed)
        ]
        found += [f"{path.name}:{line} logs a warning" for line in warnings_in(source)]

    assert found == []

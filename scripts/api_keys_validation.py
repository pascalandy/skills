#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Check that this machine's keyring holds every key the skills name in `api-key`."""

from __future__ import annotations

import logging
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from _cli import Parser, ScriptError, TemporaryError, exit_codes
from _common import frontmatter_value, main_checkout, run, run_script

ROOT = Path(__file__).resolve().parent.parent
TREES = (ROOT / "authoring", main_checkout(ROOT) / "_skills_private")
USER = "api_key"
TIMEOUT = 15.0

EPILOG = """\
rule:
  A SKILL.md or playbook under authoring/, or under _skills_private/ when it
  exists, names in its api-key field the keyring entries that hold the keys it
  reads. Each entry is looked up with chezmoi, user api_key; no value is ever
  printed. Only presence is checked: a revoked or expired key still passes.

examples:
  just api-keys-validation
  just api-keys-validation --verbose"""

EXIT_CODES = exit_codes(
    {
        0: "the keyring holds every entry",
        1: "an entry is missing or unreadable",
        75: "the keyring timed out; safe to retry",
    }
)

log = logging.getLogger("api-keys-validation")


def label(path: Path) -> str:
    """The skill a file belongs to, and the route for a playbook: `andy-mode/trello`."""
    package = next(
        (folder for folder in path.parents if (folder / "SKILL.md").is_file()),
        path.parent,
    )
    return package.name if path.name == "SKILL.md" else f"{package.name}/{path.stem}"


def needed() -> dict[str, list[str]]:
    """Each keyring entry a skill names, with the skills that read it."""
    readers: defaultdict[str, list[str]] = defaultdict(list)
    for tree in TREES:
        for path in sorted(tree.glob("**/*.md")):
            value = frontmatter_value(path.read_text(encoding="utf-8"), "api-key")
            for entry in (part.strip() for part in (value or "").split(",")):
                if entry:
                    readers[entry].append(label(path))
    return dict(sorted(readers.items()))


def problem(entry: str, readers: list[str]) -> str | None:
    """Why the keyring cannot give `entry`, or None when it holds a value."""
    command = [
        "chezmoi",
        "secret",
        "keyring",
        "get",
        f"--service={entry}",
        f"--user={USER}",
    ]
    try:
        result = run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise TemporaryError(
            f"the keyring did not answer within {TIMEOUT:g}s for {entry}; "
            "unlock it, then rerun: just api-keys-validation"
        ) from None
    if result.returncode == 0 and result.stdout.strip():
        return None
    where = f"{entry} ({', '.join(readers)})"
    add = f"add it: chezmoi secret keyring set --service={entry} --user={USER}"
    # chezmoi's own text never reaches the output, in case a backend echoes a value
    if result.returncode == 0:
        return f"{where}: the entry is empty; {add}"
    if "not found" in result.stderr:
        return f"{where}: not in the keyring; {add}"
    return (
        f"{where}: the keyring refused the lookup (chezmoi exit {result.returncode}); "
        "unlock it, or run this in the machine's own terminal"
    )


def validate() -> dict[str, Any]:
    """Look up every entry the skills name in this machine's keyring."""
    readers = needed()
    if not readers:
        raise ScriptError(f"no api-key field found under {TREES[0]}")
    if shutil.which("chezmoi") is None:
        raise ScriptError(
            "chezmoi is not on PATH; install it: https://www.chezmoi.io/install/"
        )
    errors: list[str] = []
    for entry, skills in readers.items():
        log.info("look up %s for %s", entry, ", ".join(skills))
        if reason := problem(entry, skills):
            errors.append(reason)
    if errors:
        raise ScriptError(*errors)
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just api-keys-validation",
        description="Check that this machine's keyring holds every API key the skills name",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    return run_script(parser, lambda args: validate(), argv, json_answer=True)


if __name__ == "__main__":
    raise SystemExit(main())

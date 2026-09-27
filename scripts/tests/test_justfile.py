"""The justfile is a menu: most-run commands first, checks last, and no logic."""

from __future__ import annotations

import json
import subprocess

from conftest import SCRIPTS

ROOT = SCRIPTS.parent
# A shell operator means the recipe decides or chains; that belongs in scripts/
OPERATORS = ("&&", "||", ";", "|")


def just(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["just", *args], cwd=ROOT, check=True, capture_output=True, text=True
    )


def test_every_recipe_is_one_line_without_shell_logic() -> None:
    problems: list[str] = []
    recipes = json.loads(just("--dump", "--dump-format", "json").stdout)["recipes"]
    for name, recipe in recipes.items():
        # Each body line is a list of text fragments and {{ }} expressions
        lines = [
            "".join(part for part in line if isinstance(part, str))
            for line in recipe["body"]
        ]
        if recipe["shebang"] or len(lines) != 1:
            problems.append(f"{name}: {len(lines)} lines; move them into a script")
        elif operator := next((op for op in OPERATORS if op in lines[0]), None):
            problems.append(f"{name}: uses {operator!r}; move the logic into a script")

    assert problems == []


def test_bare_just_lists_commands_then_checks_without_hook_plumbing() -> None:
    # --dry-run names what bare `just` would run instead of running it
    assert just("--dry-run").stderr.rstrip().endswith(" --list --unsorted")

    menu = [line.strip() for line in just("--list", "--unsorted").stdout.splitlines()]

    assert menu[:2] == ["Available recipes:", "[commands]"]
    assert [line for line in menu if line.startswith("[")] == [
        "[commands]",
        "[checks]",
    ]
    assert not [line for line in menu if line.startswith("sync-hook")]

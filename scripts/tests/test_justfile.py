"""The justfile is a menu: most-run commands first, checks last, and no logic."""

from __future__ import annotations

import json
import os
import re
import subprocess

from conftest import SCRIPTS

ROOT = SCRIPTS.parent
# A shell operator means the recipe decides or chains; that belongs in scripts/
OPERATORS = ("&&", "||", ";", "|")
# A recipe that runs one of the repository's scripts, not a skill's
SCRIPT = re.compile(r"(?<![\w/])scripts/\w+\.py")


def just(*args: str) -> subprocess.CompletedProcess[str]:
    # The caller's JUST_* settings, such as JUST_COLOR, would change the listing
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("JUST_")
    }
    return subprocess.run(
        ["just", "--justfile", str(ROOT / "justfile"), *args],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_every_recipe_is_one_quiet_line_without_shell_logic() -> None:
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
        elif "uv run " in lines[0] and "uv run --quiet " not in lines[0]:
            # uv's own progress lines would break a script's quiet stderr
            problems.append(f"{name}: runs uv without --quiet")

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


def test_every_recipe_that_runs_a_script_ends_with_its_answer() -> None:
    # Without the attribute, just adds "error: Recipe failed" after the answer
    recipes = json.loads(just("--dump", "--dump-format", "json").stdout)["recipes"]
    bare = [
        name
        for name, recipe in recipes.items()
        if any(
            SCRIPT.search(part)
            for line in recipe["body"]
            for part in line
            if isinstance(part, str)
        )
        and "no-exit-message" not in recipe["attributes"]
    ]

    assert bare == []

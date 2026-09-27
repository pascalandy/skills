"""The justfile holds no logic: each recipe is one line calling one script or tool."""

from __future__ import annotations

import json
import subprocess

from conftest import SCRIPTS

ROOT = SCRIPTS.parent
# A shell operator means the recipe decides or chains; that belongs in scripts/
OPERATORS = ("&&", "||", ";", "|")


def recipes() -> dict[str, dict]:
    dumped = subprocess.run(
        ["just", "--dump", "--dump-format", "json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(dumped.stdout)["recipes"]


def test_every_recipe_is_one_line_without_shell_logic() -> None:
    problems: list[str] = []
    for name, recipe in recipes().items():
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

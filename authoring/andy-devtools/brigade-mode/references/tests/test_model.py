"""The command-line contract of model.py, run as `just check` runs it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent / "model.py"
OK = '{"ok":true}\n'


def run(*args: str, model: Path = MODEL) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(model), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def mutant(tmp_path: Path, rule: str, change: str) -> Path:
    """A throwaway copy of model.py with one rule changed."""
    source = MODEL.read_text(encoding="utf-8")
    assert source.count(rule) == 1, f"the rule to mutate moved: {rule}"
    copy = tmp_path / "model.py"
    copy.write_text(source.replace(rule, change), encoding="utf-8")
    return copy


def answer(stderr: str) -> dict[str, object]:
    return json.loads(stderr.splitlines()[-1])


def test_the_model_answers_ok_and_prints_nothing_else() -> None:
    result = run()

    assert (result.returncode, result.stdout, result.stderr) == (0, OK, "")


def test_verbose_prints_the_counts_and_grids_on_stderr_only() -> None:
    result = run("--verbose")

    assert (result.returncode, result.stdout) == (0, OK)
    assert result.stderr.startswith("Chef cases: ")
    assert "\nChef x Cook\n| | 🍳 |" in result.stderr
    assert "\nHead Chef x Chef\n| | ⏳ |" in result.stderr


def test_a_broken_rule_fails_and_names_each_broken_property(tmp_path: Path) -> None:
    copy = mutant(tmp_path, 'return "🔀"  # merges, then releases', 'return "⛳"')

    result = run(model=copy)

    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr.count("\n") == 1, "without --verbose, only the answer"
    errors = answer(result.stderr)["errors"]
    assert isinstance(errors, list)
    assert [error.split(":")[0] for error in errors] == [
        "Chef C1 final over a live Cook",
        "Chef C5 delivered without delivery",
        "no Chef case reaches 🔀",
    ]


def test_help_wins_over_other_arguments_and_lists_the_exit_codes() -> None:
    result = run("--typo", "--help")

    assert (result.returncode, result.stderr) == (0, "")
    assert result.stdout.startswith("usage: model.py")
    assert "examples:" in result.stdout
    assert "exit codes:" in result.stdout


def test_an_unknown_flag_is_a_usage_error_that_exits_two() -> None:
    result = run("--typo")

    assert (result.returncode, result.stdout) == (2, "")
    assert answer(result.stderr) == {
        "ok": False,
        "errors": ["unrecognized arguments: --typo"],
        "help": "model.py --help",
    }

"""run_script's failure paths that no script triggers on purpose."""

from __future__ import annotations

import argparse
import io
import json
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout

from _cli import Parser, TemporaryError, exit_codes
from _common import run_script


def broken(_: argparse.Namespace) -> str:
    raise RuntimeError("boom")


def busy(_: argparse.Namespace) -> str:
    raise TemporaryError("the lock is held", report={"mode": "apply"})


def call(work: Callable[[argparse.Namespace], str], *argv: str) -> tuple[int, str, str]:
    parser = Parser(prog="just tool", exit_codes=exit_codes({75: "retry"}))
    parser.add_argument("--json", action="store_true")
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run_script(parser, work, list(argv), debug="TOOL_DEBUG")
    return code, stdout.getvalue(), stderr.getvalue()


def test_a_bug_names_the_rerun_and_only_debug_shows_the_traceback() -> None:
    code, stdout, stderr = call(broken)
    traced = call(broken, "--debug")

    assert (code, stdout, stderr) == (
        1,
        "",
        "error: RuntimeError: boom\nrerun: just tool --debug\n",
    )
    assert traced[2].startswith("error: RuntimeError: boom\nunexpected failure\n")
    assert "Traceback" in traced[2]


def test_under_json_a_bug_and_a_temporary_failure_are_one_object_each() -> None:
    bug = call(broken, "--json")
    retry = call(busy, "--json")

    assert bug[:2] == (1, "")
    assert json.loads(bug[2]) == {
        "errors": ["RuntimeError: boom"],
        "rerun": "just tool --json --debug",
    }
    assert retry[:2] == (75, "")
    assert json.loads(retry[2]) == {
        "mode": "apply",
        "errors": ["the lock is held"],
        "retry": "just tool --json",
    }

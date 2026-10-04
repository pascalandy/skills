"""run_script's failure paths that no script triggers on purpose."""

from __future__ import annotations

import argparse
import io
import json
import os
import signal
import subprocess
import time
from collections.abc import Callable, Mapping
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

import _common
import pytest
from _cli import (
    INTERRUPTED,
    Interrupted,
    Parser,
    ScriptError,
    TemporaryError,
    exit_codes,
)
from _common import run_script, stop


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
    assert traced[2].startswith("unexpected failure\nTraceback")
    assert traced[2].endswith("\nerror: RuntimeError: boom\n")


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


def test_under_json_a_usage_error_is_one_object_and_exits_2() -> None:
    code, stdout, stderr = call(broken, "--json", "--bogus")

    assert (code, stdout) == (2, "")
    assert json.loads(stderr) == {
        "errors": ["unrecognized arguments: --bogus"],
        "help": "just tool --help",
    }


def test_under_json_and_debug_the_error_object_still_ends_stderr() -> None:
    code, stdout, stderr = call(broken, "--json", "--debug")
    lines = stderr.splitlines()
    start = len(lines) - 1 - lines[::-1].index("{")

    assert (code, stdout) == (1, "")
    assert "Traceback" in stderr
    assert json.loads("\n".join(lines[start:])) == {"errors": ["RuntimeError: boom"]}


def answered(
    work: Callable[[argparse.Namespace], str | Mapping[str, Any]], *argv: str
) -> tuple[int, str, str]:
    parser = Parser(prog="just tool", exit_codes=exit_codes({75: "retry"}))
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run_script(
            parser, work, list(argv), debug="TOOL_DEBUG", json_answer=True
        )
    return code, stdout.getvalue(), stderr.getvalue()


def interrupted(_: argparse.Namespace) -> str:
    raise Interrupted(INTERRUPTED)


def test_a_json_answer_is_one_line_whose_ok_matches_the_exit_code() -> None:
    assert answered(lambda _: {"checks": ["lint"]}) == (
        0,
        '{"ok":true,"checks":["lint"]}\n',
        "",
    )
    assert answered(busy) == (
        75,
        "",
        '{"ok":false,"mode":"apply","errors":["the lock is held"],"retry":"just tool"}\n',
    )
    assert answered(broken) == (
        1,
        "",
        '{"ok":false,"errors":["RuntimeError: boom"],"rerun":"just tool --debug"}\n',
    )
    assert answered(interrupted) == (130, "", '{"ok":false,"errors":["interrupted"]}\n')


def lying(_: argparse.Namespace) -> str:
    raise ScriptError("the deploy missed mbp", report={"ok": True})


def test_ok_follows_the_exit_code_whatever_work_returns() -> None:
    assert answered(lambda _: {"ok": False}) == (0, '{"ok":true}\n', "")
    assert answered(lying) == (
        1,
        "",
        '{"ok":false,"errors":["the deploy missed mbp"]}\n',
    )
    assert answered(lambda _: "") == (
        1,
        "",
        (
            '{"ok":false,"errors":["TypeError: work must return a mapping under json_answer"],'
            '"rerun":"just tool --debug"}\n'
        ),
    )


def test_a_json_answer_covers_usage_errors_and_ends_stderr_after_a_traceback() -> None:
    code, stdout, stderr = answered(broken, "--debug")

    assert answered(broken, "--bogus") == (
        2,
        "",
        '{"ok":false,"errors":["unrecognized arguments: --bogus"],"help":"just tool --help"}\n',
    )
    assert (code, stdout) == (1, "")
    assert "Traceback" in stderr
    assert stderr.endswith('\n{"ok":false,"errors":["RuntimeError: boom"]}\n')


def started(script: str, tmp_path: Path) -> subprocess.Popen[str]:
    """A shell running `script` once it has set its traps and written ready."""
    ready = tmp_path / "ready"
    process = subprocess.Popen(
        ["sh", "-c", f'{script}\n: > "{ready}"\nwait'],
        stdout=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 10
    while not ready.exists():
        assert time.monotonic() < deadline, "the shell never got ready"
        time.sleep(0.02)
    return process


def test_stop_kills_a_child_that_ignores_sigterm_after_the_grace_period(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_common, "GRACE", 0.3)
    sleeper = tmp_path / "sleeper"
    process = started(
        f'trap "" TERM\nsleep 30 <&- >&- & echo $! > "{sleeper}"', tmp_path
    )
    try:
        began = time.monotonic()
        stop(process)

        assert process.returncode == -signal.SIGKILL
        assert time.monotonic() - began < 2
    finally:
        os.kill(int(sleeper.read_text()), signal.SIGKILL)


def test_stop_stops_reading_pipes_a_descendant_keeps_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_common, "GRACE", 0.3)
    holder = tmp_path / "holder"
    # The shell exits on SIGTERM, but its child ignores it and keeps stdout
    process = started(
        f'(trap "" TERM; exec sleep 30) & echo $! > "{holder}"\ntrap "exit 0" TERM',
        tmp_path,
    )
    try:
        began = time.monotonic()
        stop(process)

        assert process.returncode == 0
        assert time.monotonic() - began < 2
    finally:
        os.kill(int(holder.read_text()), signal.SIGKILL)

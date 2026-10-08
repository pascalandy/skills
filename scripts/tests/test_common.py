"""run_script's failure paths that no script triggers on purpose."""

from __future__ import annotations

import argparse
import io
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


def broken(_: argparse.Namespace) -> dict[str, Any]:
    raise RuntimeError("boom")


def busy(_: argparse.Namespace) -> dict[str, Any]:
    raise TemporaryError("the lock is held", report={"mode": "apply"})


def interrupted(_: argparse.Namespace) -> dict[str, Any]:
    raise Interrupted(INTERRUPTED)


def lying(_: argparse.Namespace) -> dict[str, Any]:
    raise ScriptError("the deploy missed mbp", report={"ok": True})


def answered(
    work: Callable[[argparse.Namespace], Mapping[str, Any]], *argv: str
) -> tuple[int, str, str]:
    parser = Parser(prog="just tool", exit_codes=exit_codes({75: "retry"}))
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = run_script(parser, work, list(argv), debug="TOOL_DEBUG")
    return code, stdout.getvalue(), stderr.getvalue()


def test_a_json_answer_is_one_line_whose_ok_matches_the_exit_code() -> None:
    assert answered(lambda _: {"checks": ["lint"]}) == (
        0,
        '{"ok":true,"checks":["lint"]}\n',
        "",
    )
    assert answered(busy) == (
        75,
        "",
        '{"ok":false,"errors":["the lock is held"],"mode":"apply","retry":"just tool"}\n',
    )
    assert answered(broken) == (
        1,
        "",
        '{"ok":false,"errors":["RuntimeError: boom"],"rerun":"just tool --debug"}\n',
    )
    assert answered(interrupted) == (130, "", '{"ok":false,"errors":["interrupted"]}\n')


def test_ok_follows_the_exit_code_whatever_work_returns() -> None:
    assert answered(lambda _: {"ok": False}) == (0, '{"ok":true}\n', "")
    assert answered(lying) == (
        1,
        "",
        '{"ok":false,"errors":["the deploy missed mbp"]}\n',
    )


def test_a_json_answer_covers_usage_errors_and_ends_stderr_after_a_traceback() -> None:
    code, stdout, stderr = answered(broken, "--debug")

    assert answered(broken, "--bogus") == (
        2,
        "",
        '{"ok":false,"errors":["unrecognized arguments: --bogus"],"help":"just tool --help"}\n',
    )
    assert (code, stdout) == (1, "")
    assert stderr.startswith("unexpected failure\nTraceback")
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


def test_a_group_signal_to_a_child_that_already_exited_is_a_no_op() -> None:
    process = subprocess.Popen(["/bin/sh", "-c", "exit 0"], start_new_session=True)
    # Nothing reaps it yet, so the exited leader stays a zombie
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(process.pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        if state.startswith("Z"):
            break
        time.sleep(0.05)

    _common.send(process, signal.SIGTERM, group=True)

    assert process.wait(timeout=5) == 0


@pytest.mark.parametrize(
    "lines",
    [
        [
            "a login profile line",
            '{"ok":true,"changes":[["pull","_skills_private","a..b"]]}',
            '{"ok":true,"changes":[["add","~/.claude/skills/alpha"]]}',
        ],
        [
            "a login profile line",
            "pull\t_skills_private\ta..b",
            "add\t~/.claude/skills/alpha",
        ],
    ],
    ids=["json-answers", "change-lines-from-before-490"],
)
def test_changes_in_reads_json_answers_and_older_change_lines(
    lines: list[str],
) -> None:
    assert _common.changes_in(lines) == [
        ["pull", "_skills_private", "a..b"],
        ["add", "~/.claude/skills/alpha"],
    ]


def test_answer_in_finds_the_last_json_answer_among_other_lines() -> None:
    lines = ['{"ok":true}', "warning: noise", '{"ok":false,"errors":["boom"]}', "x"]

    assert _common.answer_in(lines) == {"ok": False, "errors": ["boom"]}
    assert _common.answer_in(["error: old text"]) is None


def test_readers_take_an_answer_whatever_its_key_order() -> None:
    lines = ['{"changes":[["update","~/.claude/skills/alpha"]],"ok":true}']

    assert _common.answer_in(lines) == {
        "changes": [["update", "~/.claude/skills/alpha"]],
        "ok": True,
    }
    assert _common.changes_in(lines) == [["update", "~/.claude/skills/alpha"]]
    assert _common.answer_in(['{"changes":[]}', "[1]"]) is None

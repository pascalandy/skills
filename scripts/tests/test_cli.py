"""The contract pieces in _cli.py that no single script exercises."""

from __future__ import annotations

import argparse
import io
import os
import signal
import time

import pytest
from _cli import (
    Interrupted,
    color_enabled,
    duration,
    exit_codes,
    given,
    signals_interrupt,
)


class Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize(
    ("text", "seconds"),
    [("30s", 30), ("5m", 300), ("2h", 7200), ("40", 40), ("1.5s", 1.5)],
)
def test_duration_reads_units_and_bare_seconds(text: str, seconds: float) -> None:
    assert duration(text) == seconds


@pytest.mark.parametrize("text", ["0", "0s", "-5m", "5 minutes", "5d", ""])
def test_duration_rejects_what_is_not_a_positive_duration(text: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="30s, 5m, 2h"):
        duration(text)


def test_exit_codes_always_list_the_base_codes_in_order() -> None:
    assert exit_codes({75: "retry later", 1: "a check failed"}) == {
        0: "success",
        1: "a check failed",
        2: "bad usage",
        75: "retry later",
        130: "interrupted (SIGINT)",
        143: "terminated (SIGTERM)",
    }


@pytest.mark.parametrize("code", [124, 127, 128, 255])
def test_exit_codes_refuse_codes_the_shell_reserves(code: int) -> None:
    with pytest.raises(ValueError, match="reserved"):
        exit_codes({code: "clashes"})


def test_a_flag_counts_only_before_the_end_of_options() -> None:
    assert given(["--bogus", "-h"], "-h", "--help")
    assert given(["mbp", "--help"], "-h", "--help")
    assert not given(["--", "--help"], "-h", "--help")
    assert not given(["--notes", "help.md"], "-h", "--help")


@pytest.mark.parametrize(
    ("environment", "disabled", "expected"),
    [
        ({"TERM": "xterm"}, False, True),
        ({"TERM": "xterm"}, True, False),
        ({"TERM": "xterm", "NO_COLOR": "1"}, False, False),
        ({"TERM": "dumb"}, False, False),
    ],
)
def test_color_needs_a_terminal_and_no_opt_out(
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    disabled: bool,
    expected: bool,
) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    assert color_enabled(Terminal(), disabled) is expected
    assert color_enabled(io.StringIO(), disabled) is False


@pytest.fixture
def handlers():
    """Put back pytest's own signal handlers after a test replaces them."""
    saved = {
        number: signal.getsignal(number) for number in (signal.SIGINT, signal.SIGTERM)
    }
    yield
    for number, handler in saved.items():
        signal.signal(number, handler)


def test_the_first_signal_interrupts_and_a_repeat_is_ignored(handlers: None) -> None:
    with pytest.raises(Interrupted) as raised, signals_interrupt():
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(5)
    os.kill(os.getpid(), signal.SIGINT)
    time.sleep(0.1)

    assert raised.value.code == 143
    assert signal.getsignal(signal.SIGINT) == signal.SIG_IGN


def test_handlers_come_back_when_no_signal_arrived(handlers: None) -> None:
    before = signal.getsignal(signal.SIGTERM)

    with signals_interrupt():
        assert signal.getsignal(signal.SIGTERM) != before

    assert signal.getsignal(signal.SIGTERM) == before

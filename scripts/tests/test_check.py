"""Behavior checks for the CI verdict runner."""

from __future__ import annotations

import sys
from pathlib import Path

import check
import pytest
from check import Check
from conftest import exits, observe

FAIL = (sys.executable, "-c", "print('boom'); raise SystemExit(3)")
MARK = (sys.executable, "-c", "open('ran', 'w').close()")
TALK = (sys.executable, "-c", "print('child says hi')")


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(check, "ROOT", tmp_path)
    return tmp_path


def verdict(
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    checks: list[Check],
    *argv: str,
) -> tuple[int, str, str]:
    """Run main() over `checks`; children write straight to the captured descriptors."""
    monkeypatch.setattr(check, "CHECKS", checks)
    code = observe("check", check.main(list(argv)))
    stdout, stderr = capfd.readouterr()
    return code, stdout, stderr


@exits("check", 1)
def test_a_failure_reports_its_output_and_rerun_without_stopping_later_checks(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    code, stdout, stderr = verdict(
        monkeypatch, capfd, [Check("broken", FAIL, MARK), Check("later", MARK)]
    )

    assert (code, stdout) == (1, "")
    assert "boom" in stderr
    assert stderr.endswith("error: broken failed; rerun: just check --only broken\n")
    assert (root / "ran").exists(), "the later check must still run"


@exits("check", 0)
def test_only_runs_the_named_checks_and_success_prints_nothing(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    checks = [Check("broken", FAIL), Check("fine", MARK)]

    assert verdict(monkeypatch, capfd, checks, "--only", "fine") == (0, "", "")


@exits("check", 0)
def test_verbose_streams_each_command_on_stderr_and_keeps_stdout_empty(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    code, stdout, stderr = verdict(monkeypatch, capfd, [Check("talk", TALK)], "-v")

    assert (code, stdout) == (0, "")
    assert stderr.startswith("==> talk: ")
    assert stderr.endswith("child says hi\n")


@exits("check", 0)
def test_list_prints_names_and_verbose_adds_commands_on_stderr(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    checks = [Check("fine", MARK), Check("talk", TALK)]

    code, stdout, stderr = verdict(monkeypatch, capfd, checks, "--list", "-v")

    assert (code, stdout) == (0, "fine\ntalk\n")
    assert stderr.splitlines()[0].startswith(f"fine: {sys.executable} -c ")

"""Behavior checks for the CI verdict runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import check
import pytest
from check import Check
from conftest import commit, exits, observe, skill

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


def touch(marker: str, *paths: str) -> tuple[str, ...]:
    """A command that leaves `marker` behind and names `paths` the way a check names its skill."""
    return (sys.executable, "-c", f"open({marker!r}, 'w').close()", *paths)


@exits("check", 0)
def test_a_skill_check_runs_only_when_the_change_touches_its_skill(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    for name in ("alpha", "beta", "gamma"):
        skill(root / "authoring/content", name)
    commit(root)
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"], cwd=root, check=True
    )
    (root / "authoring/content/alpha/SKILL.md").write_text("# alpha\n\nnew\n")
    (root / "authoring/content/gamma/résumé.md").write_text("new\n")
    checks = [
        Check("repo", touch("repo-ran")),
        Check("alpha", touch("alpha-ran", "authoring/content/alpha/scripts/tests")),
        Check("beta", touch("beta-ran", "authoring/content/beta")),
        Check("gamma", touch("gamma-ran", "authoring/content/gamma")),
    ]

    assert verdict(monkeypatch, capfd, checks) == (0, "", "")
    assert sorted(p.name for p in root.glob("*-ran")) == [
        "alpha-ran",
        "gamma-ran",
        "repo-ran",
    ]

    assert verdict(monkeypatch, capfd, checks, "--all") == (0, "", "")
    assert (root / "beta-ran").exists()

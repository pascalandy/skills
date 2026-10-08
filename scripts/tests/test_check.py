"""Behavior checks for the CI verdict runner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import check
import pytest
from check import Check
from conftest import commit, skill

FAIL = (sys.executable, "-c", "print('boom'); raise SystemExit(3)")
MARK = (sys.executable, "-c", "open('ran', 'w').close()")
TALK = (sys.executable, "-c", "print('child says hi')")
OK = '{"ok":true}\n'


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
    code = check.main(list(argv))
    stdout, stderr = capfd.readouterr()
    return code, stdout, stderr


def test_a_failure_reports_its_output_and_rerun_without_stopping_later_checks(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    code, stdout, stderr = verdict(
        monkeypatch, capfd, [Check("broken", FAIL, MARK), Check("later", MARK)]
    )

    assert (code, stdout) == (1, "")
    assert "boom" in stderr
    assert stderr.endswith(
        '{"ok":false,"errors":["broken failed; rerun: just check --only broken"]}\n'
    )
    assert (root / "ran").exists(), "the later check must still run"


def test_only_runs_the_named_checks_and_success_answers_ok(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    checks = [Check("broken", FAIL), Check("fine", MARK)]

    assert verdict(monkeypatch, capfd, checks, "--only", "fine") == (0, OK, "")


def test_verbose_streams_each_command_on_stderr_and_keeps_stdout_for_the_answer(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    code, stdout, stderr = verdict(monkeypatch, capfd, [Check("talk", TALK)], "-v")

    assert (code, stdout) == (0, OK)
    assert stderr.startswith("==> talk: ")
    assert stderr.endswith("child says hi\n")


def test_list_answers_the_names_and_verbose_adds_commands_on_stderr(
    root: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    checks = [Check("fine", MARK), Check("talk", TALK)]

    code, stdout, stderr = verdict(monkeypatch, capfd, checks, "--list", "-v")

    assert (code, stdout) == (0, '{"ok":true,"checks":["fine","talk"]}\n')
    assert stderr.splitlines()[0].startswith(f"fine: {sys.executable} -c ")


def touch(marker: str, *paths: str) -> tuple[str, ...]:
    """A command that leaves `marker` behind and names `paths` the way a check names its skill."""
    return (sys.executable, "-c", f"open({marker!r}, 'w').close()", *paths)


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
        Check(
            "reader",
            touch("reader-ran", "authoring/content/beta"),
            reads=("authoring/content/alpha",),
        ),
    ]

    assert verdict(monkeypatch, capfd, checks) == (0, OK, "")
    assert sorted(p.name for p in root.glob("*-ran")) == [
        "alpha-ran",
        "gamma-ran",
        "reader-ran",
        "repo-ran",
    ]

    assert verdict(monkeypatch, capfd, checks, "--sweep") == (0, OK, "")
    assert (root / "beta-ran").exists()


@pytest.fixture
def routing_repo(root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    tests = root / "scripts/tests"
    tests.mkdir(parents=True)
    bin_dir = root / "bin"
    bin_dir.mkdir()
    fake_uvx = bin_dir / "uvx"
    fake_uvx.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "with Path('pytest-calls').open('a', encoding='utf-8') as log:\n"
        "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if os.environ.get('FAKE_PYTEST_EXIT'):\n"
        "    print('batch boom')\n"
        "    raise SystemExit(1)\n",
        encoding="utf-8",
    )
    fake_uvx.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    return root


def repository_checks(root: Path, *names: str) -> list[Check]:
    checks = []
    for name in names:
        path = f"scripts/tests/test_{name.replace('-', '_')}.py"
        (root / path).write_text("", encoding="utf-8")
        checks.append(Check(f"test-{name}", test_path=path))
    return checks


def registered_checks(root: Path, *names: str) -> list[Check]:
    checks = [
        row
        for row in check.CHECKS
        if row.test_path and (not names or row.name in names)
    ]
    for row in checks:
        assert row.test_path is not None
        target = root / row.test_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
    return checks


def pytest_calls(root: Path) -> list[list[str]]:
    return [
        json.loads(line)
        for line in (root / "pytest-calls").read_text(encoding="utf-8").splitlines()
    ]


def publish_base(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("old\n", encoding="utf-8")
    commit(root)
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=root,
        check=True,
    )
    target.write_text("new\n", encoding="utf-8")


def test_selected_repository_modules_run_in_one_pytest_batch(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = repository_checks(routing_repo, "alpha", "beta")
    code, stdout, stderr = verdict(
        monkeypatch, capfd, checks, "--only", "test-alpha", "--only", "test-beta"
    )

    assert (code, stdout, stderr) == (0, OK, "")
    assert pytest_calls(routing_repo) == [
        [
            "--from",
            "pytest@9.1.1",
            "--with",
            "pytest-xdist==3.8.0",
            "pytest",
            "-W",
            "error",
            "-n",
            "auto",
            "scripts/tests/test_alpha.py",
            "scripts/tests/test_beta.py",
        ]
    ]


def test_cheap_project_rules_run_on_every_default_check_without_xdist(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = registered_checks(routing_repo)
    publish_base(routing_repo, "notes.txt")

    assert verdict(monkeypatch, capfd, checks) == (0, OK, "")
    assert pytest_calls(routing_repo) == [
        [
            "--from",
            "pytest@9.1.1",
            "pytest",
            "-W",
            "error",
            "scripts/tests/test_commands.py",
            "scripts/tests/test_skill_invocation.py",
        ]
    ]


@pytest.mark.parametrize(
    ("changed_path", "expected"),
    [
        (
            "scripts/compile_skills.py",
            [
                "scripts/tests/test_cli_contract.py",
                "scripts/tests/test_commands.py",
                "scripts/tests/test_discover_skills.py",
                "scripts/tests/test_compile_skills.py",
                "scripts/tests/test_install_skills.py",
                "scripts/tests/test_skill_invocation.py",
                "scripts/tests/test_sync.py",
                "scripts/tests/test_sync_fleet.py",
            ],
        ),
        (
            "scripts/install_skills.py",
            [
                "scripts/tests/test_cli_contract.py",
                "scripts/tests/test_commands.py",
                "scripts/tests/test_discover_skills.py",
                "scripts/tests/test_install_skills.py",
                "scripts/tests/test_skill_invocation.py",
                "scripts/tests/test_sync.py",
                "scripts/tests/test_sync_fleet.py",
            ],
        ),
        (
            "scripts/sync_private.py",
            [
                "scripts/tests/test_cli_contract.py",
                "scripts/tests/test_commands.py",
                "scripts/tests/test_discover_skills.py",
                "scripts/tests/test_install_skills.py",
                "scripts/tests/test_skill_invocation.py",
                "scripts/tests/test_sync.py",
                "scripts/tests/test_sync_fleet.py",
                "scripts/tests/test_sync_private.py",
            ],
        ),
        (
            "scripts/tests/test_sync.py",
            [
                "scripts/tests/test_cli_contract.py",
                "scripts/tests/test_commands.py",
                "scripts/tests/test_skill_invocation.py",
                "scripts/tests/test_sync.py",
            ],
        ),
    ],
)
def test_repository_dependency_changes_select_their_test_modules(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    changed_path: str,
    expected: list[str],
) -> None:
    checks = registered_checks(routing_repo)
    publish_base(routing_repo, changed_path)

    assert verdict(monkeypatch, capfd, checks) == (0, OK, "")
    assert [
        arg for arg in pytest_calls(routing_repo)[0] if arg.startswith("scripts/tests/")
    ] == expected


@pytest.mark.parametrize("args", [("--list",), ("--only", "test-known"), ()])
def test_unregistered_repository_test_fails_before_running_or_listing(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    args: tuple[str, ...],
) -> None:
    checks = repository_checks(routing_repo, "known")
    (routing_repo / "scripts/tests/test_new.py").write_text("", encoding="utf-8")

    assert verdict(monkeypatch, capfd, checks, *args) == (
        1,
        "",
        '{"ok":false,"errors":["test check registry is incomplete; unregistered repository tests: scripts/tests/test_new.py"]}\n',
    )


def test_duplicate_and_stale_registry_entries_fail_before_listing(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = repository_checks(routing_repo, "known")
    checks.append(Check("test-copy", test_path="scripts/tests/test_known.py"))
    assert verdict(monkeypatch, capfd, checks, "--list") == (
        1,
        "",
        '{"ok":false,"errors":["test check registry is incomplete; duplicate repository tests: scripts/tests/test_known.py"]}\n',
    )

    checks.pop()
    (routing_repo / "scripts/tests/test_known.py").unlink()
    assert verdict(monkeypatch, capfd, checks, "--list") == (
        1,
        "",
        '{"ok":false,"errors":["test check registry is incomplete; missing repository tests: scripts/tests/test_known.py"]}\n',
    )


@pytest.mark.parametrize(
    "changed_path",
    [
        "scripts/_cli.py",
        "scripts/_common.py",
        "pytest.ini",
        "scripts/tests/conftest.py",
        "scripts/tests/helper.py",
    ],
)
def test_shared_test_dependencies_run_every_repository_module(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    changed_path: str,
) -> None:
    checks = registered_checks(routing_repo)
    publish_base(routing_repo, changed_path)

    assert verdict(monkeypatch, capfd, checks) == (0, OK, "")
    assert [
        arg for arg in pytest_calls(routing_repo)[0] if arg.startswith("scripts/tests/")
    ] == [row.test_path for row in checks]


def test_missing_origin_main_runs_every_repository_module(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = registered_checks(routing_repo)

    assert verdict(monkeypatch, capfd, checks) == (0, OK, "")
    assert [
        arg for arg in pytest_calls(routing_repo)[0] if arg.startswith("scripts/tests/")
    ] == [row.test_path for row in checks]


def test_verbose_list_shows_the_actual_cheap_test_command(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = registered_checks(routing_repo, "test-commands")

    assert verdict(
        monkeypatch, capfd, checks, "--only", "test-commands", "--list", "-v"
    ) == (
        0,
        '{"ok":true,"checks":["test-commands"]}\n',
        "repository-tests: uvx --from pytest@9.1.1 pytest -W error scripts/tests/test_commands.py\n",
    )
    assert not (routing_repo / "pytest-calls").exists()


def test_failed_batch_names_an_executable_rerun_and_continues(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = repository_checks(routing_repo, "alpha", "beta")
    checks.append(Check("later", MARK))
    monkeypatch.setenv("FAKE_PYTEST_EXIT", "1")

    code, stdout, stderr = verdict(monkeypatch, capfd, checks, "--sweep")

    assert (code, stdout) == (1, "")
    assert "batch boom" in stderr
    assert stderr.endswith(
        '{"ok":false,"errors":["repository-tests failed; rerun: just check --only test-alpha --only test-beta"]}\n'
    )
    assert (routing_repo / "ran").exists()


def test_ambiguous_test_alias_is_rejected(
    routing_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    checks = repository_checks(routing_repo, "known")

    code, stdout, stderr = verdict(monkeypatch, capfd, checks, "--only", "test")

    assert (code, stdout) == (2, "")
    assert "invalid choice: 'test'" in stderr
    assert not (routing_repo / "pytest-calls").exists()


def test_a_test_that_warns_fails_its_check(tmp_path: Path) -> None:
    (tmp_path / "test_warns.py").write_text(
        "import warnings\n\ndef test_warns():\n    warnings.warn('stale call')\n",
        encoding="utf-8",
    )
    command = check.pytest("test_warns.py", parallel=False)
    flags = command[command.index("pytest") + 1 :]

    ran = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *flags],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert ran.returncode == 1
    assert "UserWarning: stale call" in ran.stdout

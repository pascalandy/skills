"""Pasted cli blocks through the checker's CLI, in a scratch repository."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import check_cli_block
import pytest
from conftest import SCRIPTS

CANONICAL = (SCRIPTS / "_cli.py").read_text(encoding="utf-8")
BLOCK = CANONICAL[CANONICAL.index(check_cli_block.BEGIN) :]


def script(block: str) -> str:
    return f'"""A skill script."""\n\nimport json\n\n{block}\n\nprint(json.dumps(1))\n'


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/_cli.py").write_text(CANONICAL, encoding="utf-8")
    monkeypatch.setattr(check_cli_block, "ROOT", tmp_path)
    monkeypatch.setattr(check_cli_block, "CANONICAL", tmp_path / "scripts/_cli.py")
    return tmp_path


def paste(repo: Path, name: str, block: str) -> Path:
    path = repo / "authoring/content" / name / "scripts/tool.py"
    path.parent.mkdir(parents=True)
    path.write_text(script(block), encoding="utf-8")
    return path


def run(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = check_cli_block.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def test_a_stale_copy_fails_until_fix_rewrites_only_its_block(repo: Path) -> None:
    current = paste(repo, "current", BLOCK)
    stale = paste(repo, "stale", BLOCK.replace("USAGE = 2", "USAGE = 64"))

    assert run() == (
        1,
        "",
        (
            "update\tauthoring/content/stale/scripts/tool.py\n"
            "error: 1 pasted cli block differs from scripts/_cli.py; "
            "run: uv run scripts/check_cli_block.py --fix\n"
        ),
    )
    assert run("--fix") == (0, "update\tauthoring/content/stale/scripts/tool.py\n", "")
    assert stale.read_text(encoding="utf-8") == script(BLOCK)
    assert current.read_text(encoding="utf-8") == script(BLOCK)
    assert run() == (0, "", "")


def test_a_copy_without_its_end_marker_is_named(repo: Path) -> None:
    paste(repo, "cut", BLOCK.replace(check_cli_block.END, ""))

    code, stdout, stderr = run("--fix")

    assert (code, stdout) == (1, "")
    assert stderr.startswith(
        "error: authoring/content/cut/scripts/tool.py has no whole cli block"
    )

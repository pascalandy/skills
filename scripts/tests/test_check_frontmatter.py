"""Behavior checks for the skill frontmatter checker, through its CLI."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import check_frontmatter
import pytest


@pytest.fixture
def authoring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(check_frontmatter, "ROOT", tmp_path)
    monkeypatch.setattr(check_frontmatter, "AUTHORING", tmp_path / "authoring")
    return tmp_path / "authoring"


def write(authoring: Path, name: str, frontmatter: str) -> None:
    path = authoring / "devtools" / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\n{frontmatter}---\n", encoding="utf-8")


def run(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = check_frontmatter.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def test_quoted_frontmatter_answers_ok(authoring: Path) -> None:
    write(authoring, "example", 'name: "example"\nkeywords: ["foo, bar", 3]\n')

    assert run() == (0, '{"ok":true}\n', "")
    assert run("--verbose") == (
        0,
        '{"ok":true}\n',
        "check authoring/devtools/example/SKILL.md\n",
    )


def test_commas_inside_quoted_inline_items_keep_their_quotes(authoring: Path) -> None:
    write(
        authoring,
        "example",
        'keywords: ["foo, bar", "baz"]\ninvalid: ["foo, bar", plain]\n',
    )

    assert run() == (
        1,
        "",
        (
            '{"ok":false,"errors":["authoring/devtools/example/SKILL.md:3: invalid '
            'inline list string items must be double-quoted"]}\n'
        ),
    )

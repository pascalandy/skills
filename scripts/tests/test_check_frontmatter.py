"""Behavior checks for the skill frontmatter checker, through its CLI."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import check_frontmatter
import pytest
from conftest import exits, observe


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
    return observe("check_frontmatter", code), stdout.getvalue(), stderr.getvalue()


@exits("check_frontmatter", 0)
def test_quoted_frontmatter_passes_silently(authoring: Path) -> None:
    write(authoring, "example", 'name: "example"\nkeywords: ["foo, bar", 3]\n')

    assert run() == (0, "", "")
    assert run("--verbose") == (0, "", "check authoring/devtools/example/SKILL.md\n")


@exits("check_frontmatter", 1)
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
            "error: authoring/devtools/example/SKILL.md:3: invalid "
            "inline list string items must be double-quoted\n"
        ),
    )

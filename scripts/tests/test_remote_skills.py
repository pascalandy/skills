"""Behavior checks for the remote skill table, through its CLI."""

from __future__ import annotations

import io
import re
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import remote_skills

PATH = "docs/maintainer/references/remote-skills.md"
RAW = "https://raw.githubusercontent.com/pascalandy/skills/main/skills"


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(remote_skills, "ROOT", tmp_path)
    monkeypatch.setattr(remote_skills, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(remote_skills, "TABLE", tmp_path / PATH)
    (tmp_path / PATH).parent.mkdir(parents=True)
    return tmp_path


def skill(root: Path, name: str, text: str) -> None:
    path = root / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")


def run(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = remote_skills.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def test_run_writes_one_linked_row_per_skill_and_only_the_date_may_differ(
    root: Path,
) -> None:
    skill(root, "zeta", '---\nname: "zeta"\ndescription: "Use for z."\n---\n# Z\n')
    skill(root, "alpha", '---\nname: "alpha"\ndescription: "Use for a | b."\n---\n')

    assert run("--dry-run") == (0, f"add\t{PATH}\n", "")
    assert not (root / PATH).exists()
    assert run() == (0, f"add\t{PATH}\n", "")
    rows = [
        line
        for line in (root / PATH).read_text(encoding="utf-8").splitlines()
        if line.startswith("| [")
    ]
    assert rows == [
        f"| [alpha]({RAW}/alpha/SKILL.md) | Use for a \\| b. |",
        f"| [zeta]({RAW}/zeta/SKILL.md) | Use for z. |",
    ]
    assert run() == (0, "", "")
    table = (root / PATH).read_text(encoding="utf-8")
    dated = re.compile(r"^date_updated: \d{4}-\d{2}-\d{2}$", re.MULTILINE)
    assert len(dated.findall(table)) == 1
    (root / PATH).write_text(
        dated.sub("date_updated: 2000-01-01", table), encoding="utf-8"
    )
    assert run("--check") == (0, "", "")


def test_check_reports_a_stale_table_and_leaves_it_alone(root: Path) -> None:
    skill(root, "alpha", '---\nname: "alpha"\ndescription: "Use for a."\n---\n')
    (root / PATH).write_text("stale\n", encoding="utf-8")

    assert run("--check") == (
        1,
        "",
        (
            f"update\t{PATH}\n"
            f"error: {PATH} differs from skills/; run: just remote-skills\n"
        ),
    )
    assert (root / PATH).read_text(encoding="utf-8") == "stale\n"


def test_a_skill_without_a_description_fails_before_writing(root: Path) -> None:
    skill(root, "alpha", '---\nname: "alpha"\ndescription: "Use for a."\n---\n')
    skill(root, "bare", "# Bare\n")

    assert run() == (
        1,
        "",
        (
            "error: skills/bare/SKILL.md has no description; "
            "add one to its source in authoring/, then run: just flatten-skills\n"
        ),
    )
    assert not (root / PATH).exists()

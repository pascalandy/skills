"""Behavior checks for the remote skill tables, through their CLI."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import remote_skills

MAIN = "docs/references/remote-skills.md"
GENERAL = "docs/references/remote-skills-general.md"
DEV = "docs/references/remote-skills-dev.md"
URL = "URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md\n\n"
HEAD = "| Skill | Description |\n|---|---|\n"


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(remote_skills, "ROOT", tmp_path)
    monkeypatch.setattr(remote_skills, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(remote_skills, "DOCS", tmp_path / "docs/references")
    (tmp_path / MAIN).parent.mkdir(parents=True)
    return tmp_path


def skill(root: Path, name: str, text: str) -> None:
    path = root / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tagged(name: str, description: str, kind: str) -> str:
    return f'---\nname: "{name}"\ndescription: "{description}"\nkind: "{kind}"\n---\n'


def run(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = remote_skills.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def table(root: Path, path: str) -> str:
    """A page from its URL line on, below the generated header."""
    page = (root / path).read_text(encoding="utf-8")
    return page[page.index("URL: ") :]


def test_run_writes_each_kind_to_its_section_and_its_own_page(root: Path) -> None:
    skill(root, "zeta", tagged("zeta", "Use for z.", "general") + "# Z\n")
    skill(root, "alpha", tagged("alpha", "Use for a | b.", "general"))
    skill(root, "code", tagged("code", "Use for code.", "dev"))
    skill(root, "fresh", '---\nname: "fresh"\ndescription: "Use for new."\n---\n')
    skill(root, "typo", tagged("typo", "Use for typos.", "Dev"))
    written = f"add\t{MAIN}\nadd\t{GENERAL}\nadd\t{DEV}\n"

    assert run("--dry-run") == (0, written, "")
    assert not any((root / path).exists() for path in (MAIN, GENERAL, DEV))
    assert run() == (0, written, "")
    assert table(root, MAIN) == (
        f"{URL}## General\n\n{HEAD}"
        "| alpha | Use for a \\| b. |\n"
        "| zeta | Use for z. |\n"
        f"\n## Dev\n\n{HEAD}"
        "| code | Use for code. |\n"
        f"\n## Unknown\n\n{HEAD}"
        "| fresh | Use for new. |\n"
        "| typo | Use for typos. |\n"
    )
    assert (
        (root / GENERAL)
        .read_text(encoding="utf-8")
        .startswith(
            "---\nname: remote-skills-general\n"
            "description: Use andy's general skills remotely\n---\n"
        )
    )
    assert table(root, GENERAL) == (
        f"{URL}{HEAD}| alpha | Use for a \\| b. |\n| zeta | Use for z. |\n"
    )
    assert table(root, DEV) == f"{URL}{HEAD}| code | Use for code. |\n"
    assert run() == (0, "", "")


def test_classifying_the_last_unknown_skill_drops_the_unknown_section(
    root: Path,
) -> None:
    skill(root, "code", tagged("code", "Use for code.", "dev"))
    skill(root, "fresh", '---\nname: "fresh"\ndescription: "Use for new."\n---\n')
    assert run()[0] == 0
    assert "## Unknown" in (root / MAIN).read_text(encoding="utf-8")

    skill(root, "fresh", tagged("fresh", "Use for new.", "general"))

    assert run() == (0, f"update\t{MAIN}\nupdate\t{GENERAL}\n", "")
    assert table(root, MAIN) == (
        f"{URL}## General\n\n{HEAD}| fresh | Use for new. |\n"
        f"\n## Dev\n\n{HEAD}| code | Use for code. |\n"
    )


def test_check_reports_each_stale_table_and_leaves_them_alone(root: Path) -> None:
    skill(root, "alpha", tagged("alpha", "Use for a.", "dev"))
    (root / MAIN).write_text("stale\n", encoding="utf-8")

    assert run("--check") == (
        1,
        "",
        (
            f"update\t{MAIN}\nadd\t{GENERAL}\nadd\t{DEV}\n"
            "error: the skill tables differ from skills/; run: just remote-skills\n"
        ),
    )
    assert (root / MAIN).read_text(encoding="utf-8") == "stale\n"
    assert not any((root / path).exists() for path in (GENERAL, DEV))


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("# Bare\n", "has no description"),
        (
            '---\nname: "bare"\ndescription: "Use for a\\nthen b."\n---\n',
            "has a line break in its description",
        ),
    ],
)
def test_a_skill_without_a_one_line_description_fails_before_writing(
    root: Path, text: str, problem: str
) -> None:
    skill(root, "alpha", tagged("alpha", "Use for a.", "dev"))
    skill(root, "bare", text)

    assert run() == (
        1,
        "",
        (
            f"error: skills/bare/SKILL.md {problem}; "
            "fix its source in authoring/, then run: just flatten-skills\n"
        ),
    )
    assert not any((root / path).exists() for path in (MAIN, GENERAL, DEV))

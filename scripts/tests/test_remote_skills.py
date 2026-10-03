"""Behavior checks for the remote skill lists, through their CLI."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest
import remote_skills

MAIN = "docs/references/remote-skills.md"
GENERAL = "docs/references/remote-skills-general.md"
DEV = "docs/references/remote-skills-dev.md"
URL = (
    "URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md\n\n"
    "A mode's routes run through that mode's SKILL.md.\n\n"
)


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(remote_skills, "ROOT", tmp_path)
    monkeypatch.setattr(remote_skills, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(remote_skills, "DOCS", tmp_path / "docs/references")
    (tmp_path / MAIN).parent.mkdir(parents=True)
    return tmp_path


def skill(root: Path, name: str, text: str, *playbooks: str) -> None:
    """A compiled skill; each playbook ending in / is a folder, else a file. Each
    route's entry file describes it as: Run <route>."""
    path = root / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    for playbook in playbooks:
        route = playbook.removesuffix("/").removesuffix(".md")
        entry = path.parent / "playbooks" / playbook
        if playbook.endswith("/"):
            entry /= f"{route}.md"
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(
            f'---\ndescription: "Run {route}."\n---\n\n# Route\n', encoding="utf-8"
        )


def tagged(name: str, description: str, kind: str, role: str | None = None) -> str:
    extra = f'role: "{role}"\n' if role is not None else ""
    return (
        f'---\nname: "{name}"\ndescription: "{description}"\nkind: "{kind}"\n'
        f"{extra}---\n"
    )


def run(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = remote_skills.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def listing(root: Path, path: str) -> str:
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
    assert listing(root, MAIN) == (
        f"{URL}## General\n\n### Skills\n\n"
        "- `alpha`: Use for a | b.\n"
        "- `zeta`: Use for z.\n"
        "\n## Dev\n\n### Skills\n\n"
        "- `code`: Use for code.\n"
        "\n## Unknown\n\n### Skills\n\n"
        "- `fresh`: Use for new.\n"
        "- `typo`: Use for typos.\n"
    )
    assert (
        (root / GENERAL)
        .read_text(encoding="utf-8")
        .startswith(
            "---\nname: remote-skills-general\n"
            "description: Use andy's general skills remotely\n---\n"
        )
    )
    assert listing(root, GENERAL) == (
        f"{URL}## Skills\n\n- `alpha`: Use for a | b.\n- `zeta`: Use for z.\n"
    )
    assert listing(root, DEV) == f"{URL}## Skills\n\n- `code`: Use for code.\n"
    assert run() == (0, "", "")


def test_each_kind_lists_modes_with_their_routes_then_skills_then_helpers(
    root: Path,
) -> None:
    skill(root, "alpha", tagged("alpha", "Use for a.", "dev", "helper"))
    skill(root, "beta", tagged("beta", "Use for b.", "dev"))
    skill(
        root,
        "zeta-mode",
        tagged("zeta-mode", "Use for z.", "dev"),
        "plan.md",
        "cro/",
        "ask.md",
        ".DS_Store",
    )
    skill(root, "draw-mode", tagged("draw-mode", "Use to draw.", "general"), "ink.md")

    assert run()[0] == 0
    routes = "  - `ask`: Run ask.\n  - `cro`: Run cro.\n  - `plan`: Run plan.\n"
    assert listing(root, MAIN) == (
        f"{URL}## General\n\n### Modes\n\n"
        "- `draw-mode`: Use to draw.\n"
        "  - `ink`: Run ink.\n"
        "\n## Dev\n\n### Modes\n\n"
        f"- `zeta-mode`: Use for z.\n{routes}"
        "\n### Skills\n\n"
        "- `beta`: Use for b.\n"
        "\n### Helpers\n\n"
        "- `alpha`: Use for a.\n"
    )
    assert listing(root, DEV) == (
        f"{URL}## Modes\n\n- `zeta-mode`: Use for z.\n{routes}"
        "\n## Skills\n\n- `beta`: Use for b.\n"
        "\n## Helpers\n\n- `alpha`: Use for a.\n"
    )


def test_a_route_lists_the_first_sentence_of_its_description(root: Path) -> None:
    skill(root, "draw-mode", tagged("draw-mode", "Use to draw.", "general"), "ink.md")
    (root / "skills/draw-mode/playbooks/ink.md").write_text(
        "---\nname: ink\n"
        'description: "Ink logos, e.g. Marks vs. Icons for U.S. Clients in v2.0. Also use when inking."\n'
        "---\n",
        encoding="utf-8",
    )

    assert run()[0] == 0
    assert listing(root, GENERAL) == (
        f"{URL}## Modes\n\n- `draw-mode`: Use to draw.\n"
        "  - `ink`: Ink logos, e.g. Marks vs. Icons for U.S. Clients in v2.0.\n"
    )


@pytest.mark.parametrize(
    ("playbook", "entry", "content", "problem"),
    [
        ("ink.md", "ink.md", "# Ink\n", "has no description"),
        ("ink/", "ink/ink.md", None, "is missing"),
    ],
)
def test_a_route_without_a_description_fails_before_writing(
    root: Path, playbook: str, entry: str, content: str | None, problem: str
) -> None:
    skill(root, "draw-mode", tagged("draw-mode", "Use to draw.", "general"), playbook)
    path = root / "skills/draw-mode/playbooks" / entry
    path.unlink()
    if content is not None:
        path.write_text(content, encoding="utf-8")

    assert run() == (
        1,
        "",
        (
            f"error: skills/draw-mode/playbooks/{entry} {problem}; "
            "fix its source in authoring/, then run: just compile-skills\n"
        ),
    )
    assert not any((root / path).exists() for path in (MAIN, GENERAL, DEV))


def test_classifying_the_last_unknown_skill_drops_the_unknown_section(
    root: Path,
) -> None:
    skill(root, "code", tagged("code", "Use for code.", "dev"))
    skill(root, "fresh", '---\nname: "fresh"\ndescription: "Use for new."\n---\n')
    assert run()[0] == 0
    assert "## Unknown" in (root / MAIN).read_text(encoding="utf-8")

    skill(root, "fresh", tagged("fresh", "Use for new.", "general"))

    assert run() == (0, f"update\t{MAIN}\nupdate\t{GENERAL}\n", "")
    assert listing(root, MAIN) == (
        f"{URL}## General\n\n### Skills\n\n- `fresh`: Use for new.\n"
        "\n## Dev\n\n### Skills\n\n- `code`: Use for code.\n"
    )


def test_check_reports_each_stale_list_and_leaves_them_alone(root: Path) -> None:
    skill(root, "alpha", tagged("alpha", "Use for a.", "dev"))
    (root / MAIN).write_text("stale\n", encoding="utf-8")

    assert run("--check") == (
        1,
        "",
        (
            f"update\t{MAIN}\nadd\t{GENERAL}\nadd\t{DEV}\n"
            "error: the skill lists differ from skills/; run: just remote-skills\n"
        ),
    )
    assert (root / MAIN).read_text(encoding="utf-8") == "stale\n"
    assert not any((root / path).exists() for path in (GENERAL, DEV))


@pytest.mark.parametrize(
    ("name", "text", "playbooks", "problem"),
    [
        ("bare", "# Bare\n", (), "has no description"),
        (
            "bare",
            '---\nname: "bare"\ndescription: "Use for a\\nthen b."\n---\n',
            (),
            "has a line break in its description",
        ),
        (
            "bare-mode",
            tagged("bare-mode", "Use for b.", "dev"),
            (),
            "is named like a mode but has no playbooks/ folder beside it",
        ),
        (
            "bare",
            tagged("bare", "Use for b.", "dev"),
            ("plan.md",),
            "has a playbooks/ folder beside it but no -mode name",
        ),
        (
            "bare",
            tagged("bare", "Use for b.", "dev", "helpr"),
            (),
            'has role "helpr", but the only role is "helper"',
        ),
        (
            "bare-mode",
            tagged("bare-mode", "Use for b.", "dev", "helper"),
            ("plan.md",),
            "is a mode, which always lists first, but sets a role",
        ),
    ],
)
def test_a_skill_that_breaks_a_listing_rule_fails_before_writing(
    root: Path, name: str, text: str, playbooks: tuple[str, ...], problem: str
) -> None:
    skill(root, "alpha", tagged("alpha", "Use for a.", "dev"))
    skill(root, name, text, *playbooks)

    assert run() == (
        1,
        "",
        (
            f"error: skills/{name}/SKILL.md {problem}; "
            "fix its source in authoring/, then run: just compile-skills\n"
        ),
    )
    assert not any((root / path).exists() for path in (MAIN, GENERAL, DEV))

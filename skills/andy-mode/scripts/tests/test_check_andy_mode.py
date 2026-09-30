from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import check_andy_mode as checker

SKILL = """\
# Andy mode

### Retro

| Route | Aliases | Use when |
|---|---|---|
| [`retro-skill`](playbooks/retro-skill.md) | `retro` | A skill cost a detour |
| [`2nd-pass`](../2nd-pass/SKILL.md) | `2pass` | A fresh-eyes review |
"""


def package(tmp_path: Path, skill: str = SKILL) -> Path:
    root = tmp_path / "andy-mode"
    (root / "playbooks").mkdir(parents=True)
    (root / "references/retro-skill").mkdir(parents=True)
    (root / "SKILL.md").write_text(skill, encoding="utf-8")
    (root / "playbooks/retro-skill.md").write_text(
        "Read [the template](../references/retro-skill/template.md#body) "
        "and `references/retro-skill/template.md`.\n",
        encoding="utf-8",
    )
    (root / "references/retro-skill/template.md").write_text(
        "# Template\n\n## Body\n", encoding="utf-8"
    )
    (tmp_path / "2nd-pass").mkdir()
    (tmp_path / "2nd-pass/SKILL.md").write_text("# 2nd pass\n", encoding="utf-8")
    return root


def test_valid_package_passes(tmp_path: Path) -> None:
    assert checker.validate(package(tmp_path)) == []


def test_main_prints_each_problem_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = package(tmp_path)
    (root / "playbooks/retro-skill.md").write_text(
        "See [gone](../references/retro-skill/gone.md).\n", encoding="utf-8"
    )
    assert checker.main([str(root)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "playbooks/retro-skill.md: unresolved link: ../references/retro-skill/gone.md\n"
    )


def test_names_collide_after_normalization(tmp_path: Path) -> None:
    root = package(
        tmp_path,
        SKILL + "| [`retroskill`](playbooks/retroskill.md) | | Clash |\n",
    )
    (root / "playbooks/retroskill.md").write_text("Body.\n", encoding="utf-8")
    assert checker.validate(root) == [
        "SKILL.md: 'retroskill' matches both retro-skill and retroskill"
    ]


def test_unrouted_playbook_and_nested_skill_fail(tmp_path: Path) -> None:
    root = package(tmp_path)
    (root / "playbooks/orphan.md").write_text("Body.\n", encoding="utf-8")
    (root / "references/retro-skill/SKILL.md").write_text("x\n", encoding="utf-8")
    assert checker.validate(root) == [
        "references/retro-skill/SKILL.md: only the root may be named SKILL.md",
        "playbooks/orphan.md: no route in SKILL.md reaches it",
    ]


def test_broken_anchor_and_bundled_path_fail(tmp_path: Path) -> None:
    root = package(tmp_path)
    (root / "playbooks/retro-skill.md").write_text(
        "Read [it](../references/retro-skill/template.md#missing) "
        "and `references/retro-skill/old.md`.\n\n"
        "```\n`references/retro-skill/in-fence.md` stays unchecked\n```\n",
        encoding="utf-8",
    )
    assert checker.validate(root) == [
        (
            "playbooks/retro-skill.md: unresolved anchor: "
            "../references/retro-skill/template.md#missing"
        ),
        (
            "playbooks/retro-skill.md: unresolved bundled path: "
            "references/retro-skill/old.md"
        ),
    ]


def test_link_outside_a_sibling_skill_fails(tmp_path: Path) -> None:
    root = package(tmp_path)
    (tmp_path / "notes.md").write_text("x\n", encoding="utf-8")
    (root / "playbooks/retro-skill.md").write_text(
        "See [notes](../../notes.md).\n", encoding="utf-8"
    )
    assert checker.validate(root) == [
        "playbooks/retro-skill.md: link leaves andy-mode: ../../notes.md"
    ]

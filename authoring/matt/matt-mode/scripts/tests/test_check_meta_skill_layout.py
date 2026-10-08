from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import check_meta_skill_layout as layout


@pytest.fixture
def meta_skill(tmp_path: Path) -> Path:
    """A valid meta-skill: a root SKILL.md, its router, and one routed mode."""
    root = tmp_path / "demo"
    (root / "references/Mode").mkdir(parents=True)
    (root / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Use when testing.\n---\n\n"
        "Read references/ROUTER.md.\n"
    )
    (root / "references/ROUTER.md").write_text(
        "---\nname: router\ndescription: Routes requests.\n---\n\n# Router\n\n"
        "## Routing\n\n| Request Pattern | Route To |\n| --- | --- |\n"
        "| anything | `Mode/MetaSkill.md` |\n"
    )
    (root / "references/Mode/MetaSkill.md").write_text(
        "---\nname: mode\ndescription: One mode.\n---\n\nDo the work.\n"
    )
    return root


def answered(capsys: pytest.CaptureFixture[str]) -> tuple[str, dict[str, object]]:
    """stdout, and the one JSON line that ends the output."""
    out, err = capsys.readouterr()
    return out, json.loads((out or err).splitlines()[-1])


def test_a_valid_layout_answers_ok_on_stdout(
    meta_skill: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert layout.main([str(meta_skill), "--expected-mode-count", "1"]) == 0
    assert capsys.readouterr() == ('{"ok":true}\n', "")


def test_an_invalid_layout_answers_each_problem_on_stderr(
    meta_skill: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (meta_skill / "references/ROUTER.md").unlink()

    assert layout.main([str(meta_skill)]) == 1
    assert answered(capsys) == (
        "",
        {
            "ok": False,
            "errors": [
                "references/ROUTER.md: mode is not routed: Mode/MetaSkill.md",
                "references/ROUTER.md: required router is missing",
            ],
        },
    )


def test_a_usage_error_answers_with_the_help_command(
    meta_skill: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert layout.main([str(meta_skill), "--expected-mode-count", "0"]) == 2
    assert answered(capsys) == (
        "",
        {
            "ok": False,
            "errors": ["--expected-mode-count must be at least 1"],
            "help": "check_meta_skill_layout.py --help",
        },
    )

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import validate_skill as validator

THIS_SKILL = SCRIPTS.parent
BP_LINE_RE = re.compile(
    r"^- (?P<box>\[ \] )?\*\*(?P<id>BP_\d{2}) (?P<title>[^*]+)\*\*", re.MULTILINE
)


def skill(
    tmp_path: Path,
    body: str = "Steps.\n",
    name: str = "processing-pdfs",
    folder: str = "processing-pdfs",
    description: str = '"Use when filling PDF forms."',
    files: dict[str, str] | None = None,
) -> Path:
    root = tmp_path / folder
    root.mkdir()
    (root / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}",
        encoding="utf-8",
    )
    for relative, text in (files or {}).items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text(text, encoding="utf-8")
    return root


def errors(code: int, out: str, err: str) -> list[str]:
    """The errors of the one-line answer, after checking it agrees with `code`."""
    if code == 0:
        assert out == '{"ok":true}\n'
        return []
    assert out == ""
    answer = json.loads(err.splitlines()[-1])
    assert answer["ok"] is False
    return answer["errors"]


def run(capsys: pytest.CaptureFixture[str], *args: str | Path) -> tuple[int, list[str]]:
    code = validator.main([str(arg) for arg in args])
    captured = capsys.readouterr()
    return code, errors(code, captured.out, captured.err)


def test_this_skill_is_clean(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, THIS_SKILL) == (0, [])


def test_exclude_skips_findings_in_copied_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = skill(
        tmp_path,
        "See [ads](vendor/ads.md) and [mine](mine.md).\n",
        files={"vendor/ads.md": "[gone](../gone.md)\n", "mine.md": "[gone](gone.md)\n"},
    )

    code, lines = run(capsys, root)

    assert (code, len(lines)) == (1, 2)
    assert run(capsys, "--exclude", root / "vendor", root) == (
        1,
        [
            f"{root}/mine.md:1: error: BP_12 Links resolve: link to missing file 'gone.md'"
        ],
    )


def test_clean_skill_answers_ok(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = skill(
        tmp_path,
        "See [forms](references/forms.md) and [the docs](https://example.com).\n",
        files={"references/forms.md": "Back to [the skill](../SKILL.md).\n"},
    )
    assert run(capsys, root) == (0, [])


def test_eval_fixture_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "pdf-helper"
    root.mkdir()
    shutil.copy(THIS_SKILL / "evals/fixtures/messy-skill.md", root / "SKILL.md")
    s = f"{root}/SKILL.md"
    assert run(capsys, root) == (
        1,
        [
            f"{s}:2: error: BP_13 Name: name 'PDF_Helper' does not match the folder name 'pdf-helper'",
            f"{s}:2: error: BP_13 Name: name 'PDF_Helper' may only use lowercase letters, digits, and hyphens",
            f"{s}:10: warning: BP_07 No dated text: dated text 'After August 2025'; keep the current method and move the old one to 'Old patterns'",
            f"{s}:10: warning: BP_07 No dated text: dated text 'before August 2025'; keep the current method and move the old one to 'Old patterns'",
            f"{s}:18: error: BP_12 Links resolve: path 'scripts\\extract.py' uses backslashes",
            f"{s}:20: error: BP_12 Links resolve: link to missing file 'advanced.md'",
        ],
    )


def test_name_format_and_reserved_words(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = skill(tmp_path, name="claude--tools-", folder="claude--tools-")
    s = f"{root}/SKILL.md"
    assert run(capsys, root) == (
        1,
        [
            f"{s}:2: error: BP_13 Name: name 'claude--tools-' contains the reserved word 'claude'",
            f"{s}:2: error: BP_13 Name: name 'claude--tools-' starts or ends with a hyphen or contains '--'",
        ],
    )


def test_name_longer_than_64_characters(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    name = "a" * 65
    root = skill(tmp_path, name=name, folder=name)
    assert run(capsys, root) == (
        1,
        [
            f"{root}/SKILL.md:2: error: BP_13 Name: name '{name}' is longer than 64 characters",
        ],
    )


def test_description_limits(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    long = skill(tmp_path, folder="long", name="long", description="x" * 1025)
    tag = skill(
        tmp_path, folder="tag", name="tag", description='"Use as `tag ; <route>`."'
    )
    missing = skill(tmp_path, folder="missing", name="missing", description='""')
    comment = skill(
        tmp_path, folder="comment", name="comment", description="# Add a trigger"
    )
    assert run(capsys, long, tag, missing, comment) == (
        1,
        [
            f"{long}/SKILL.md:3: error: BP_14 Description is a trigger: description has 1025 characters; the limit is 1024",
            f"{tag}/SKILL.md:3: error: BP_14 Description is a trigger: description contains the XML tag '<route>'",
            f"{missing}/SKILL.md:3: error: BP_14 Description is a trigger: description is missing",
            f"{comment}/SKILL.md:3: error: BP_14 Description is a trigger: description is missing",
        ],
    )


def test_block_scalar_description_is_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = skill(tmp_path, description=">\n  Use when filling\n  PDF forms.")
    assert run(capsys, root) == (0, [])


def test_missing_frontmatter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "bare"
    root.mkdir()
    (root / "SKILL.md").write_text("# Bare\n", encoding="utf-8")
    assert run(capsys, root) == (
        1,
        [
            f"{root}/SKILL.md:1: error: BP_13 Name: name is missing",
            f"{root}/SKILL.md:1: error: BP_14 Description is a trigger: description is missing",
        ],
    )


@pytest.mark.parametrize("lines", [500, 501])
def test_skill_md_line_limit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], lines: int
) -> None:
    root = skill(tmp_path, "line\n" * (lines - 5))
    expected = (
        (0, [])
        if lines == 500
        else (
            1,
            [
                f"{root}/SKILL.md:501: error: BP_15 SKILL.md under 500 lines: file has 501 lines; the limit is 500",
            ],
        )
    )
    assert run(capsys, root) == expected


def test_code_and_outside_links_are_skipped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = (
        "Write `[x](missing.md)` and `before 2025`.\n"
        "See [shared](../other-skill/SKILL.md) and [top](#steps).\n"
        "```\n[x](missing.md) before 2025 C:\\Users\\me\\notes.txt\n```\n"
    )
    assert run(capsys, skill(tmp_path, body)) == (0, [])


def test_backslash_link(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = skill(tmp_path, "See [forms](references\\forms.md).\n")
    assert run(capsys, root) == (
        1,
        [
            f"{root}/SKILL.md:6: error: BP_12 Links resolve: link 'references\\forms.md' uses backslashes",
        ],
    )


def test_warnings_fail(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    long_reference = "# Long\n" + "text\n" * 100
    root = skill(
        tmp_path,
        "Read [a](references/a.md) and [long](references/long.md).\n",
        files={
            "references/a.md": "# A\n\nSee [b](b.md).\n\n## Old patterns\n\n### v1\n\nBefore 2025-08, use v1.\n",
            "references/b.md": "# B\n",
            "references/long.md": long_reference,
        },
    )
    assert run(capsys, root) == (
        1,
        [
            f"{root}/references/a.md:3: warning: BP_01 Progressive disclosure: links to reference file 'b.md'; link it from SKILL.md instead",
            f"{root}/references/long.md:1: warning: BP_16 Contents list: 101 lines and no Contents list; ask the user before adding one",
        ],
    )


def test_errors_only_leaves_warnings_to_verbose(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = skill(
        tmp_path,
        "See [a](references/a.md) and [gone](gone.md).\n",
        files={"references/a.md": "See [b](b.md).\n", "references/b.md": "# B\n"},
    )
    warning = f"{root}/references/a.md:1: warning: BP_01 Progressive disclosure: links to reference file 'b.md'; link it from SKILL.md instead"
    error = (
        f"{root}/SKILL.md:6: error: BP_12 Links resolve: link to missing file 'gone.md'"
    )

    assert run(capsys, root) == (1, [error, warning])
    assert run(capsys, "--errors-only", root) == (1, [error])
    (root / "SKILL.md").write_text(
        "---\nname: processing-pdfs\ndescription: Use when filling PDF forms.\n---\n\n"
        "See [a](references/a.md).\n",
        encoding="utf-8",
    )
    assert run(capsys, "--errors-only", root) == (0, [])
    assert validator.main(["--errors-only", "-v", str(root)]) == 0
    assert capsys.readouterr().err == f"{warning}\n"


def test_contents_list_satisfies_bp_16(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    reference = "# Long\n\n## Contents\n\n- [Part](#part)\n" + "text\n" * 100
    root = skill(tmp_path, "Read [long](long.md).\n", files={"long.md": reference})
    assert run(capsys, root) == (0, [])


def test_folder_without_skill_md_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert validator.main([str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "ok": False,
        "errors": [f"{tmp_path} has no SKILL.md; pass a skill folder"],
        "help": "validate_skill.py --help",
    }


def test_validator_ids_match_the_skill_list() -> None:
    text = (THIS_SKILL / "SKILL.md").read_text(encoding="utf-8")
    active_text, _, voided_text = text.partition("\n### Voided\n")
    active = {m["id"]: m["title"] for m in BP_LINE_RE.finditer(active_text)}
    voided = [m["id"] for m in BP_LINE_RE.finditer(voided_text)]
    all_ids = [m["id"] for m in BP_LINE_RE.finditer(text)]
    assert sorted(all_ids) == [f"BP_{n:02d}" for n in range(1, len(all_ids) + 1)]
    assert all(m["box"] for m in BP_LINE_RE.finditer(active_text)), (
        "an active BP is not a checkbox"
    )
    assert not set(validator.BP_TITLES) & set(voided), "the validator cites a voided BP"
    assert {bp: active.get(bp) for bp in validator.BP_TITLES} == validator.BP_TITLES


def test_link_forms(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = (
        "See [v2](references/guide(v2).md) and [spaced](<references/my guide.md>).\n"
        "See [gone](<references/gone file.md>) and [the ref][ref].\n"
        "\n"
        "[ref]: references/missing.md\n"
    )
    root = skill(
        tmp_path,
        body,
        files={
            "references/guide(v2).md": "# V2\n",
            "references/my guide.md": "# Mine\n",
        },
    )
    s = f"{root}/SKILL.md"
    assert run(capsys, root) == (
        1,
        [
            f"{s}:7: error: BP_12 Links resolve: link to missing file 'references/gone file.md'",
            f"{s}:9: error: BP_12 Links resolve: link to missing file 'references/missing.md'",
        ],
    )


def test_yaml_comments_are_ignored(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "commented"
    root.mkdir()
    (root / "SKILL.md").write_text(
        '---\n# owned by the docs team\nname: "commented" # stable name\n'
        "description: Use when filling PDF forms # trigger\n---\n\nSteps.\n",
        encoding="utf-8",
    )
    assert run(capsys, root) == (0, [])


def test_command_exits_with_the_error_status(tmp_path: Path) -> None:
    root = skill(tmp_path, name="Bad_Name", folder="bad-name")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_skill.py"), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    answer = {
        "ok": False,
        "errors": [
            f"{root}/SKILL.md:2: error: BP_13 Name: name 'Bad_Name' does not match the folder name 'bad-name'",
            f"{root}/SKILL.md:2: error: BP_13 Name: name 'Bad_Name' may only use lowercase letters, digits, and hyphens",
        ],
    }
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "",
        json.dumps(answer, separators=(",", ":")) + "\n",
    )


def test_invoke_by_a_word(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = skill(
        tmp_path,
        folder="good",
        name="good",
        description='"Use only when explicitly invoked as `good`. Help the user learn Python."',
    )
    bare = skill(
        tmp_path,
        folder="bare",
        name="bare",
        description='"Use only when explicitly invoked as bare."',
    )
    actor = skill(
        tmp_path,
        folder="actor",
        name="actor",
        description='"Use only when the user invokes `actor`."',
    )
    mention = skill(
        tmp_path,
        folder="mention",
        name="mention",
        description='"Use only when the user mentions `mention`."',
    )
    by_user = skill(
        tmp_path,
        folder="by-user",
        name="by-user",
        description='"Use only when explicitly invoked as `by-user` by the user."',
    )
    model = skill(
        tmp_path,
        folder="model",
        name="model",
        description='"Use when the user asks to fill a PDF form."',
    )
    restricted = skill(
        tmp_path,
        folder="restricted",
        name="restricted",
        description='"Use only when debugging tests. Help the user invoke a failing test."',
    )
    actor_message = "names an actor, 'the user'; a delegated prompt would be refused"
    form = (
        "start with 'Use only when explicitly invoked as `word`', the word in backticks"
    )
    assert run(capsys, good, bare, actor, mention, by_user, model, restricted) == (
        1,
        [
            f"{bare}/SKILL.md:3: warning: BP_21 Invoke by a word: {form}",
            f"{actor}/SKILL.md:3: warning: BP_21 Invoke by a word: names an actor, 'the user'; a delegated prompt would be refused",
            f"{actor}/SKILL.md:3: warning: BP_21 Invoke by a word: {form}",
            f"{mention}/SKILL.md:3: warning: BP_21 Invoke by a word: {actor_message}",
            f"{mention}/SKILL.md:3: warning: BP_21 Invoke by a word: {form}",
            f"{by_user}/SKILL.md:3: warning: BP_21 Invoke by a word: {actor_message}",
        ],
    )

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import update_matt_mode as updater

SOURCE = PurePosixPath("skills/engineering/to-spec/SKILL.md")
UPSTREAM = (
    b"---\nname: to-spec\n"
    b'description: "Turn talk into a spec: no interview."\n'
    b"disable-model-invocation: true\n---\n\n# To Spec\n"
)
PLAYBOOK = "matt-mode/playbooks/to-spec/to-spec.md"


def test_a_route_keeps_only_its_description_and_a_shared_skill_keeps_none() -> None:
    assert updater.strip_frontmatter(UPSTREAM, SOURCE, keep_description=True) == (
        b'---\ndescription: "Turn talk into a spec: no interview."\n---\n\n# To Spec\n'
    )
    assert updater.strip_frontmatter(UPSTREAM, SOURCE, keep_description=False) == (
        b"\n# To Spec\n"
    )


@pytest.mark.parametrize(
    "frontmatter",
    [
        b"name: to-spec\n",
        b"description:\n",
        b"description: >\n  Turn talk into a spec.\n",
        b"description: Turn talk\n  into a spec.\n",
        b"description: Turn talk\n\n  into a spec.\n",
    ],
)
def test_a_route_without_a_one_line_description_fails(frontmatter: bytes) -> None:
    content = b"---\n" + frontmatter + b"---\n# To Spec\n"
    with pytest.raises(updater.ImportError, match="needs a one-line description"):
        updater.strip_frontmatter(content, SOURCE, keep_description=True)


@pytest.fixture
def upstream(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    """A local upstream checkout with a license and one procedure, and its commit."""
    # A leftover GIT_DIR, as in a git hook, would point every git call, the
    # updater's included, at the real repository
    for key in [key for key in os.environ if key.startswith("GIT_")]:
        monkeypatch.delenv(key)
    for key, value in {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }.items():
        monkeypatch.setenv(key, value)
    checkout = tmp_path / "upstream"
    (checkout / "skills/to-spec").mkdir(parents=True)
    (checkout / "LICENSE").write_text("MIT\n")
    (checkout / "skills/to-spec/SKILL.md").write_text(
        "---\nname: to-spec\ndescription: Turn talk into a spec\n---\n# To Spec\n"
    )
    for command in (["init", "-q"], ["add", "."], ["commit", "-qm", "one"]):
        subprocess.run(["git", *command], cwd=checkout, check=True)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return checkout, revision


@pytest.fixture
def bucket(tmp_path: Path) -> Path:
    """A Matt skill bucket whose lock maps the procedure and holds no files yet."""
    root = tmp_path / "bucket"
    lock = {
        "schema_version": 1,
        "repository": "https://example.invalid/skills",
        "revision": "0" * 40,
        "mappings": [
            {
                "name": "to-spec",
                "kind": "internal",
                "source": "skills/to-spec",
                "destination": "matt-mode/playbooks/to-spec",
                "entry": "to-spec.md",
                "exclude": [],
            }
        ],
        "handoffs": {},
        "files": [],
    }
    (root / "matt-mode").mkdir(parents=True)
    (root / "matt-mode/upstream-lock.json").write_text(json.dumps(lock))
    return root


def answered(capsys: pytest.CaptureFixture[str]) -> tuple[str, dict[str, object]]:
    """stdout, and the one JSON line that ends the output."""
    out, err = capsys.readouterr()
    return out, json.loads((out or err).splitlines()[-1])


def test_check_answers_ok_for_the_repository(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert updater.main(["check"]) == 0
    assert capsys.readouterr() == ('{"ok":true}\n', "")


def test_a_dry_run_answers_the_changes_a_real_run_makes(
    upstream: tuple[Path, str], bucket: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    checkout, revision = upstream
    update = ["update", "--upstream", str(checkout), "--revision", revision]
    update += ["--root", str(bucket)]
    changes = {
        "ok": True,
        "changes": [
            ["add", PLAYBOOK],
            ["add", "matt-mode/references/LICENSE"],
            ["update", "matt-mode/upstream-lock.json"],
        ],
    }

    assert updater.main([*update, "--dry-run"]) == 0
    assert answered(capsys)[1] == changes
    assert not (bucket / PLAYBOOK).exists()
    assert updater.main(update) == 0
    assert answered(capsys)[1] == changes
    assert (bucket / PLAYBOOK).is_file()
    assert updater.main(update) == 0
    assert capsys.readouterr() == ('{"ok":true}\n', "")
    check = ["check", "--upstream", str(checkout), "--root", str(bucket)]
    assert updater.main(check) == 0
    assert capsys.readouterr() == ('{"ok":true}\n', "")


def test_a_changed_generated_file_fails_the_check_on_stderr(
    upstream: tuple[Path, str], bucket: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    checkout, revision = upstream
    update = ["update", "--upstream", str(checkout), "--revision", revision]
    assert updater.main([*update, "--root", str(bucket)]) == 0
    capsys.readouterr()
    with (bucket / PLAYBOOK).open("a") as playbook:
        playbook.write("a local edit\n")

    assert updater.main(["check", "--root", str(bucket)]) == 1
    assert answered(capsys) == (
        "",
        {
            "ok": False,
            "errors": [
                f"changed generated file: {PLAYBOOK}; restore it from git, or move your "
                + "edit out of it, then rerun check"
            ],
        },
    )


def test_a_failed_write_answers_the_changes_already_made(
    upstream: tuple[Path, str],
    bucket: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkout, revision = upstream
    write = updater.atomic_write

    def full_disk(path: Path, content: bytes) -> None:
        if path.name == "LICENSE":
            raise OSError(28, "No space left on device")
        write(path, content)

    monkeypatch.setattr(updater, "atomic_write", full_disk)
    update = ["update", "--upstream", str(checkout), "--revision", revision]

    assert updater.main([*update, "--root", str(bucket)]) == 1
    answer = answered(capsys)[1]
    assert answer["changes"] == [["add", PLAYBOOK]]
    assert str(answer["errors"]).startswith("['cannot write Matt mode: ")


def test_a_usage_error_in_a_command_answers_with_the_help_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert updater.main(["update"]) == 2
    assert answered(capsys) == (
        "",
        {
            "ok": False,
            "errors": ["the following arguments are required: --upstream, --revision"],
            "help": "update_matt_mode.py update --help",
        },
    )


def test_help_is_text_for_the_command_it_names(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert updater.main(["update", "--typo", "-h"]) == 0
    assert capsys.readouterr().out.startswith("usage: update_matt_mode.py update ")


@pytest.mark.parametrize(
    ("raised", "code", "message"),
    [
        (KeyboardInterrupt(), 130, "interrupted"),
        (RuntimeError("boom"), 1, "RuntimeError: boom"),
    ],
)
def test_an_interrupt_or_a_bug_still_answers(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    raised: BaseException,
    code: int,
    message: str,
) -> None:
    def command_check(_args: object) -> dict[str, object]:
        raise raised

    monkeypatch.setattr(updater, "command_check", command_check)
    assert updater.main(["check"]) == code
    assert answered(capsys) == ("", {"ok": False, "errors": [message]})

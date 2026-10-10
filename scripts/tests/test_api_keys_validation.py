"""Behavior checks for just api-keys-validation, with a fake chezmoi on PATH."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import api_keys_validation
import pytest

# Answers only the exact lookup, so a wrong keyring user fails the tests. A
# locked keychain can wait indefinitely for an unlock prompt
FAKE_CHEZMOI = """\
#!/bin/sh
if [ $# -ne 5 ] || [ "$1 $2 $3 $5" != "secret keyring get --user=api_key" ]; then
  echo "unexpected call: $*" >&2
  exit 64
fi
service=${4#--service=}
if [ "$service" = "$FAKE_REFUSE" ]; then
  echo "keychain refused near s3cret-$service" >&2
  exit 1
fi
case ",$FAKE_KEYRING," in *",$service,"* | *",*,"*) echo "s3cret-$service"; exit 0 ;; esac
if [ "$service" = "$FAKE_HANG" ]; then exec sleep 30; fi
if [ "$service" = "$FAKE_EMPTY" ]; then exit 0; fi
echo "chezmoi: secret not found in keyring" >&2
exit 1
"""


def write(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n\n# Body\n", encoding="utf-8")


@pytest.fixture
def machine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    authoring = tmp_path / "authoring"
    private = tmp_path / "_skills_private/authoring"
    write(
        authoring / "andy/transcript/SKILL.md",
        'name: "transcript"\napi-key: "deepgram"\n',
    )
    write(
        authoring / "verify-loops/verify-transcript/SKILL.md",
        'name: "verify-transcript"\napi-key: "deepgram"\n',
    )
    write(authoring / "andy/andy-mode/SKILL.md", 'name: "andy-mode"\n')
    write(
        authoring / "andy/andy-mode/playbooks/trello.md",
        'description: "Trello"\napi-key: "TRELLO_API_KEY, TRELLO_TOKEN"\n',
    )
    write(
        private / "devtools/typesafe-ai/SKILL.md",
        'name: "typesafe-ai"\napi-key: "typesafe_ai"\n',
    )
    monkeypatch.setattr(api_keys_validation, "TREES", (authoring, private))

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    chezmoi = bin_dir / "chezmoi"
    chezmoi.write_text(FAKE_CHEZMOI, encoding="utf-8")
    chezmoi.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin")
    for variable in ("FAKE_KEYRING", "FAKE_EMPTY", "FAKE_REFUSE", "FAKE_HANG"):
        monkeypatch.delenv(variable, raising=False)
    return tmp_path


def run(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = api_keys_validation.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def test_a_full_keyring_answers_ok_and_prints_no_value(
    machine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "FAKE_KEYRING", "deepgram,TRELLO_API_KEY,TRELLO_TOKEN,typesafe_ai"
    )

    assert run() == (0, '{"ok":true}\n', "")
    assert run("--verbose") == (
        0,
        '{"ok":true}\n',
        (
            "look up TRELLO_API_KEY for andy-mode/trello\n"
            "look up TRELLO_TOKEN for andy-mode/trello\n"
            "look up deepgram for transcript, verify-transcript\n"
            "look up typesafe_ai for typesafe-ai\n"
        ),
    )


def test_each_failed_entry_names_its_skills_and_the_fix_without_chezmoi_text(
    machine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_KEYRING", "TRELLO_API_KEY")
    monkeypatch.setenv("FAKE_EMPTY", "TRELLO_TOKEN")
    monkeypatch.setenv("FAKE_REFUSE", "typesafe_ai")

    assert run() == (
        1,
        "",
        (
            '{"ok":false,"errors":['
            '"TRELLO_TOKEN (andy-mode/trello): the entry is empty; '
            'add it: chezmoi secret keyring set --service=TRELLO_TOKEN --user=api_key",'
            '"deepgram (transcript, verify-transcript): not in the keyring; '
            'add it: chezmoi secret keyring set --service=deepgram --user=api_key",'
            '"typesafe_ai (typesafe-ai): the keyring refused the lookup (chezmoi exit 1); '
            "unlock it, or run this in the machine's own terminal\"]}\n"
        ),
    )


def test_a_machine_without_chezmoi_says_how_to_install_it(
    machine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = machine / "empty"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))

    assert run() == (
        1,
        "",
        (
            '{"ok":false,"errors":["chezmoi is not on PATH; '
            'install it: https://www.chezmoi.io/install/"]}\n'
        ),
    )


def test_a_keyring_that_does_not_answer_stops_the_run(
    machine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_HANG", "TRELLO_API_KEY")
    monkeypatch.setattr(api_keys_validation, "TIMEOUT", 0.5)

    assert run() == (
        75,
        "",
        (
            '{"ok":false,"errors":["the keyring did not answer within 0.5s for '
            'TRELLO_API_KEY; unlock it, then rerun: just api-keys-validation"],'
            '"retry":"just api-keys-validation"}\n'
        ),
    )


def test_no_value_reaches_the_process_streams(
    machine: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the script as a process over this repository's own skills, so a raw
    write to a file descriptor, or a chezmoi child that inherits one, shows."""
    monkeypatch.setenv("FAKE_KEYRING", "*")
    monkeypatch.setenv("FAKE_REFUSE", "deepgram")

    result = subprocess.run(
        [sys.executable, api_keys_validation.__file__, "--verbose"],
        capture_output=True,
        check=False,
    )

    assert b"s3cret" not in result.stdout + result.stderr
    assert (result.returncode, result.stdout) == (1, b"")
    errors = json.loads(result.stderr.splitlines()[-1])["errors"]
    assert [error.split(" (")[0] for error in errors] == ["deepgram"]

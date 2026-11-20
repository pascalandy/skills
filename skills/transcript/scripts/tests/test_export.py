"""The copy of each result folder to mbp, the machine Pascal reads transcripts on."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

import pytest
from test_transcript import deepgram_response

MBP = "andy16@mbp16.example.ts.net"


@pytest.fixture
def fleet(tmp_path, monkeypatch):
    """A fleet.toml naming mbp, the default output parent in tmp_path, and a
    machine named om1; answers the rsync commands the run starts."""
    import httpx
    import transcript

    machines = tmp_path / "fleet.toml"
    machines.write_text(
        f'[machines.om1]\nssh = "pascal@om1.example.ts.net"\n'
        f'[machines.mbp]\nssh = "{MBP}"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(transcript, "FLEET_MACHINES", machines)
    monkeypatch.setattr(transcript, "OUTPUT_DIR", tmp_path / "exports")
    monkeypatch.setattr(transcript.platform, "node", lambda: "om1")
    monkeypatch.setattr(transcript, "get_api_key_from_fnox", lambda *_args: "dummy-key")
    monkeypatch.setattr(
        transcript.httpx,
        "post",
        # Deepgram reads the whole upload before it answers
        lambda url, *, content, **_kwargs: (
            list(content)
            and httpx.Response(
                200, json=deepgram_response(), request=httpx.Request("POST", url)
            )
        ),
    )
    commands: list[list[str]] = []
    outcome = {"returncode": 0, "stderr": ""}

    def rsync(command, **_kwargs):
        commands.append(list(command))
        return subprocess.CompletedProcess(
            command, outcome["returncode"], "", outcome["stderr"]
        )

    monkeypatch.setattr(transcript, "run_child", rsync)
    audio = tmp_path / "Entrevue à Montréal.m4a"
    audio.write_bytes(b"audio" * 100)
    return {"commands": commands, "outcome": outcome, "audio": audio}


def run_file(capsys, audio: Path, *extra: str) -> tuple[int, dict]:
    import transcript

    code = transcript.main(
        ["run", "file", "--path", str(audio), "--no-summary", *extra]
    )
    out, err = capsys.readouterr()
    return code, json.loads(out if code == 0 else err.splitlines()[-1])


def test_a_result_under_the_default_parent_is_copied_to_mbp(fleet, capsys) -> None:
    code, answer = run_file(capsys, fleet["audio"])

    folder = Path(answer["files"][0]).parent
    destination = f"{MBP}:Documents/_my_docs/61_transcription_exports_yt/"
    assert code == 0
    assert fleet["commands"] == [
        [
            "rsync",
            "-rt",
            "-e",
            "ssh -o BatchMode=yes -o ConnectTimeout=10",
            str(folder),
            destination,
        ]
    ]
    assert answer["changes"] == [["copy", f"{destination}{folder.name}"]]
    # The local copy stays
    assert (folder / "raw_transcript.txt").is_file()


def test_a_failed_copy_keeps_the_local_result_and_names_the_rsync_retry(
    fleet, capsys
) -> None:
    fleet["outcome"].update(
        returncode=255, stderr="ssh: connect to host mbp16: Operation timed out"
    )

    code, answer = run_file(capsys, fleet["audio"])

    folder = Path(answer["files"][0]).parent
    (error,) = answer["errors"]
    assert code == 1
    assert "changes" not in answer
    assert (folder / "raw_transcript.txt").is_file()
    assert "Operation timed out" in error
    assert f"The local copy stays in {folder}" in error
    retry = shlex.split(error.split("; retry: ", 1)[1])
    assert retry == [
        "rsync",
        "-rt",
        str(folder),
        f"{MBP}:Documents/_my_docs/61_transcription_exports_yt/",
    ]


def test_a_custom_output_dir_stays_local(fleet, tmp_path, capsys) -> None:
    code, answer = run_file(
        capsys, fleet["audio"], "--output-dir", str(tmp_path / "elsewhere")
    )

    assert code == 0
    assert fleet["commands"] == []
    assert "changes" not in answer


@pytest.mark.parametrize("node", ["mbp16.example.ts.net", "MBP16", "mbp"])
def test_results_stay_on_mbp_itself(fleet, monkeypatch, capsys, node) -> None:
    import transcript

    monkeypatch.setattr(transcript.platform, "node", lambda: node)

    code, answer = run_file(capsys, fleet["audio"])

    assert code == 0
    assert fleet["commands"] == []
    assert "changes" not in answer


def test_without_the_fleet_skill_results_stay_local(
    fleet, tmp_path, monkeypatch, capsys
) -> None:
    import transcript

    monkeypatch.setattr(transcript, "FLEET_MACHINES", tmp_path / "missing.toml")

    code, answer = run_file(capsys, fleet["audio"])

    assert code == 0
    assert fleet["commands"] == []


def test_a_fleet_toml_without_mbp_fails_the_dry_run_and_doctor(fleet, capsys) -> None:
    import transcript

    transcript.FLEET_MACHINES.write_text(
        '[machines.om1]\nssh = "pascal@om1"\n', encoding="utf-8"
    )

    assert run_file(capsys, fleet["audio"], "--dry-run")[0] == 1
    assert transcript.main(["doctor", "--source", "file", "--no-summary"]) == 1
    assert "has no ssh address for [machines.mbp]" in capsys.readouterr().err


def test_the_dry_run_and_doctor_name_the_destination(
    fleet, monkeypatch, capsys
) -> None:
    import transcript

    code, plan = run_file(capsys, fleet["audio"], "--dry-run")
    assert code == 0
    assert plan["export"] == f"{MBP}:Documents/_my_docs/61_transcription_exports_yt/"
    assert fleet["commands"] == []

    monkeypatch.setattr(
        transcript.shutil,
        "which",
        lambda name: None if name == "rsync" else f"/bin/{name}",
    )
    assert transcript.main(["doctor", "--source", "file", "--no-summary"]) == 1
    assert "rsync was not found on PATH" in capsys.readouterr().err


def test_a_failed_run_still_copies_the_folder_it_saved(
    fleet, monkeypatch, capsys
) -> None:
    import httpx
    import transcript

    monkeypatch.setattr(
        transcript.httpx,
        "post",
        lambda url, *, content, **_kwargs: (
            list(content) and httpx.Response(500, request=httpx.Request("POST", url))
        ),
    )

    code, answer = run_file(capsys, fleet["audio"])

    folder = Path(answer["files"][0]).parent
    assert code == 1
    assert len(fleet["commands"]) == 1
    assert answer["changes"] == [
        ["copy", f"{MBP}:Documents/_my_docs/61_transcription_exports_yt/{folder.name}"]
    ]

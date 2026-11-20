"""Copy result folders to the configured export machine."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

import pytest
from test_transcript import deepgram_response

READER_SSH = "reader@receiving-host.example.test"


@pytest.fixture
def fleet(tmp_path, monkeypatch):
    """Set up an export role and a local output folder, then stub rsync."""
    import httpx
    import transcript

    machines = tmp_path / "fleet.toml"
    machines.write_text(
        '[roles]\ntranscript_export = "reader"\n'
        f'[machines.reader]\nssh = "{READER_SSH}"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(transcript, "FLEET_MACHINES", machines)
    monkeypatch.setattr(transcript, "OUTPUT_DIR", tmp_path / "exports")
    monkeypatch.setattr(transcript.platform, "node", lambda: "worker")
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


def test_a_result_under_the_default_parent_is_copied_to_the_configured_host(fleet, capsys) -> None:
    code, answer = run_file(capsys, fleet["audio"])

    folder = Path(answer["files"][0]).parent
    destination = f"{READER_SSH}:Documents/_my_docs/61_transcription_exports_yt/"
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
        returncode=255, stderr="ssh: connect to host receiving-host: Operation timed out"
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
        f"{READER_SSH}:Documents/_my_docs/61_transcription_exports_yt/",
    ]


def test_a_custom_output_dir_stays_local(fleet, tmp_path, capsys) -> None:
    code, answer = run_file(
        capsys, fleet["audio"], "--output-dir", str(tmp_path / "elsewhere")
    )

    assert code == 0
    assert fleet["commands"] == []
    assert "changes" not in answer


@pytest.mark.parametrize(
    "node", ["receiving-host.example.test", "RECEIVING-HOST", "reader"]
)
def test_results_stay_on_the_export_machine(fleet, monkeypatch, capsys, node) -> None:
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


@pytest.mark.parametrize(
    ("inventory", "error"),
    [
        ("[roles]\n", "must name a machine in [roles].transcript_export"),
        (
            '[roles]\ntranscript_export = "reader"\n',
            "has no ssh address for [machines.reader]",
        ),
    ],
)
def test_incomplete_export_config_fails_the_dry_run_and_doctor(
    fleet, capsys, inventory: str, error: str
) -> None:
    import transcript

    transcript.FLEET_MACHINES.write_text(inventory, encoding="utf-8")

    code, plan = run_file(capsys, fleet["audio"], "--dry-run")
    assert code == 1
    assert error in plan["errors"][0]
    assert transcript.main(["doctor", "--source", "file", "--no-summary"]) == 1
    assert error in capsys.readouterr().err


def test_the_dry_run_and_doctor_name_the_destination(
    fleet, monkeypatch, capsys
) -> None:
    import transcript

    code, plan = run_file(capsys, fleet["audio"], "--dry-run")
    assert code == 0
    assert plan["export"] == f"{READER_SSH}:Documents/_my_docs/61_transcription_exports_yt/"
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
        ["copy", f"{READER_SSH}:Documents/_my_docs/61_transcription_exports_yt/{folder.name}"]
    ]


def test_an_interrupted_copy_answers_the_saved_files_and_the_rsync(
    fleet, monkeypatch, capsys
) -> None:
    import transcript

    def interrupt(command, **_kwargs):
        raise transcript.Interrupted(transcript.INTERRUPTED)

    monkeypatch.setattr(transcript, "run_child", interrupt)

    code, answer = run_file(capsys, fleet["audio"])

    folder = Path(answer["files"][0]).parent
    assert code == transcript.INTERRUPTED
    assert (folder / "raw_transcript.txt").is_file()
    assert answer["errors"] == [
        "interrupted; rerun: "
        + shlex.join(
            [
                "rsync",
                "-rt",
                str(folder),
                f"{READER_SSH}:Documents/_my_docs/61_transcription_exports_yt/",
            ]
        )
    ]


def test_zoom_stays_local_even_in_the_default_parent(fleet, tmp_path, capsys) -> None:
    import transcript

    meeting = tmp_path / "2026-05-03 14.46.55 Réunion Zoom de Camille Exemple"
    meeting.mkdir()
    (meeting / "audio1.m4a").write_bytes(b"audio" * 100)
    zoom = ["run", "zoom", "--path", str(meeting), "--no-summary"]
    zoom += ["--output-dir", str(transcript.OUTPUT_DIR)]

    assert transcript.main([*zoom, "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["export"] is None
    assert transcript.main(zoom) == 0
    assert "changes" not in json.loads(capsys.readouterr().out)
    assert fleet["commands"] == []

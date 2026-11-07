"""Portable cookies retain an immutable source and a strict transport choice."""

from __future__ import annotations

import builtins
import io
import json
import stat
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import transcript
from test_transcript import deepgram_response

URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
SENTINEL = "synthetic-cookie-value-for-tests"


@pytest.fixture
def cookies_file(tmp_path: Path) -> Path:
    path = tmp_path / "youtube.cookies.txt"
    path.write_text(
        "# Netscape HTTP Cookie File\n"
        f".youtube.com\tTRUE\t/\tTRUE\t0\tsession\t{SENTINEL}\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("outcome", ["success", "refusal", "timeout", "interrupt"])
def test_transport_owns_a_private_copy_on_every_exit(
    cookies_file: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    original = cookies_file.read_bytes()
    observed: list[Path] = []
    arc_profile = cookies_file.parent / "Arc" / "Default"
    arc_profile.mkdir(parents=True)
    monkeypatch.setattr(transcript, "ARC_BROWSER_PROFILE", arc_profile)

    def child(command, **kwargs):
        path = Path(command[command.index("--cookies") + 1])
        observed.append(path)
        assert path != cookies_file
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
        assert path.read_bytes() == original
        assert "--no-cookies-from-browser" in command
        assert "--cookies-from-browser" not in command
        path.write_text("changed by yt-dlp", encoding="utf-8")
        if outcome == "timeout":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if outcome == "interrupt":
            raise KeyboardInterrupt
        return subprocess.CompletedProcess(
            command,
            1 if outcome == "refusal" else 0,
            "",
            f"WARNING: skipping cookie file entry {SENTINEL}\nERROR: Video unavailable",
        )

    monkeypatch.setattr(transcript, "run_child", child)
    errors = {
        "refusal": transcript.YtDlpError,
        "timeout": subprocess.TimeoutExpired,
        "interrupt": KeyboardInterrupt,
    }
    if outcome == "success":
        result = transcript.run_ytdlp(
            [],
            URL,
            transcript.RunBudget.start(),
            auth_mode=transcript.CookieFile(cookies_file),
        )
        assert result.method == "cookies"
    else:
        with pytest.raises(errors[outcome]) as caught:
            transcript.run_ytdlp(
                [],
                URL,
                transcript.RunBudget.start(),
                auth_mode=transcript.CookieFile(cookies_file),
            )
        assert SENTINEL not in str(caught.value)
        if outcome == "refusal":
            assert "video may be unavailable" in str(caught.value)
            assert "session expired or refused" in str(caught.value)
            assert "JavaScript/PO-token" in str(caught.value)
            assert "youtube_smoke.py --cookies" in str(caught.value)
            assert "WARNING:" not in str(caught.value)
    assert len(observed) == 1
    assert not observed[0].parent.exists()
    assert cookies_file.read_bytes() == original


def test_overlapping_downloads_have_distinct_writable_jars(
    cookies_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rendezvous = threading.Barrier(2)
    observed: list[Path] = []
    original = cookies_file.read_bytes()

    def child(command, **_kwargs):
        path = Path(command[command.index("--cookies") + 1])
        observed.append(path)
        path.write_text("private mutation", encoding="utf-8")
        rendezvous.wait(timeout=5)
        assert len(set(observed)) == 2
        assert all(item.exists() for item in observed)
        rendezvous.wait(timeout=5)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(transcript, "run_child", child)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(
                transcript.run_ytdlp,
                [],
                URL,
                transcript.RunBudget.start(),
                auth_mode=transcript.CookieFile(cookies_file),
            )
            for _ in range(2)
        ]
        assert [future.result().method for future in futures] == ["cookies", "cookies"]
    assert cookies_file.read_bytes() == original
    assert all(not path.parent.exists() for path in observed)


@pytest.mark.parametrize("queued", [False, True])
def test_dry_run_describes_file_without_opening_secrets_or_writing(
    cookies_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    queued: bool,
) -> None:
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if Path(file) == cookies_file:
            pytest.fail("dry-run opened cookies")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(io, "open", guarded_open)
    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: pytest.fail("dry-run read credentials")
    )
    monkeypatch.setattr(
        transcript.tempfile,
        "TemporaryDirectory",
        lambda **_k: pytest.fail("dry-run created temporary state"),
    )
    urls = [URL, "https://www.youtube.com/watch?v=QwpTAk_IiyU"] if queued else [URL]
    output = tmp_path / "not-created"
    code = transcript.main(
        [
            "run",
            "youtube",
            "--url",
            *urls,
            "--cookies",
            str(cookies_file),
            "--no-summary",
            "--dry-run",
            "--output-dir",
            str(output),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    assert json.loads(captured.out)["source"]["cookies_file"] == str(cookies_file)
    assert SENTINEL not in captured.out
    assert not output.exists()


@pytest.mark.parametrize("debug", [False, True])
@pytest.mark.parametrize("queued", [False, True])
@pytest.mark.parametrize("contents", ["empty", "malformed"])
def test_invalid_contents_fail_before_credentials_without_secret_diagnostics(
    cookies_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    debug: bool,
    queued: bool,
    contents: str,
) -> None:
    cookies_file.write_text(
        "# Netscape HTTP Cookie File\n"
        + (
            f".youtube.com\tFALSE\t/\tFALSE\tnot-an-expiry\tname\t{SENTINEL}\n"
            if contents == "malformed"
            else ""
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        transcript,
        "validate_env",
        lambda *_a: pytest.fail("invalid cookies read credentials"),
    )
    urls = [URL, "https://www.youtube.com/watch?v=QwpTAk_IiyU"] if queued else [URL]
    code = transcript.main(
        [
            "run",
            "youtube",
            "--url",
            *urls,
            "--cookies",
            str(cookies_file),
            "--no-summary",
        ]
        + (["--debug"] if debug else [])
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "Netscape" in captured.err
    assert SENTINEL not in captured.err
    assert "http.cookiejar bug" not in captured.err
    assert json.loads(captured.err.splitlines()[-1])["ok"] is False


def test_missing_file_fails_dry_run_before_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        transcript,
        "validate_env",
        lambda *_a: pytest.fail("missing file read credentials"),
    )
    assert (
        transcript.main(
            [
                "run",
                "youtube",
                "--url",
                URL,
                "--cookies",
                str(tmp_path / "missing"),
                "--dry-run",
            ]
        )
        == 2
    )
    assert "existing regular file" in capsys.readouterr().err


@pytest.mark.parametrize("malformed", [False, True])
def test_doctor_checks_the_file_instead_of_browser_presence(
    cookies_file: Path, monkeypatch: pytest.MonkeyPatch, malformed: bool
) -> None:
    if malformed:
        cookies_file.write_text(
            "# Netscape HTTP Cookie File\n"
            f".youtube.com\tFALSE\t/\tFALSE\tnot-an-expiry\tsession\t{SENTINEL}\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: "unused-test-credential"
    )
    monkeypatch.setattr(transcript.shutil, "which", lambda _name: "/bin/test-tool")
    monkeypatch.setattr(transcript, "_installed_ytdlp_version", lambda: "2026.7.4")
    checks = transcript._doctor_checks(
        source="youtube",
        summarize=False,
        youtube_auth=transcript.CookieFile(cookies_file),
    )
    assert "youtube_browser" not in {check["name"] for check in checks}
    check = next(check for check in checks if check["name"] == "youtube_cookies")
    if malformed:
        assert [item["name"] for item in checks if item["status"] == "fail"] == [
            "youtube_cookies"
        ]
        assert "--cookies" in check["hint"]
        assert "Replace" in check["hint"]
    else:
        assert all(item["status"] == "pass" for item in checks)
        assert "server authentication is untested" in check["message"]
    assert SENTINEL not in json.dumps(checks)


def test_doctor_rejects_cookies_for_an_unrelated_source_before_credentials(
    cookies_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        transcript,
        "validate_env",
        lambda *_a: pytest.fail("invalid doctor read credentials"),
    )
    assert (
        transcript.main(["doctor", "--source", "file", "--cookies", str(cookies_file)])
        == 2
    )
    assert "--source youtube" in capsys.readouterr().err


def test_cli_propagates_the_file_and_records_transport_provenance(
    cookies_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def child(command, **_kwargs):
        cookie_path = Path(command[command.index("--cookies") + 1])
        assert cookie_path.read_bytes() == cookies_file.read_bytes()
        audio_path = Path(command[command.index("-o") + 1].replace("%(ext)s", "webm"))
        audio_path.write_bytes(b"test media")
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                {"id": "EIEc43CxIvY", "title": "Fixture", "filepath": str(audio_path)}
            ),
            "",
        )

    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: "unused-test-credential"
    )
    monkeypatch.setattr(transcript, "run_child", child)
    monkeypatch.setattr(transcript, "transcribe_audio", lambda *_a: deepgram_response())
    output = tmp_path / "results"
    assert (
        transcript.main(
            [
                "run",
                "youtube",
                "--url",
                URL,
                "--cookies",
                str(cookies_file),
                "--no-summary",
                "--output-dir",
                str(output),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    files = json.loads(captured.out)["files"]
    metadata = Path(files[0]).read_text(encoding="utf-8")
    assert "YouTube audio method: cookies" in metadata
    assert SENTINEL not in metadata + captured.out + captured.err

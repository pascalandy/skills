"""Offline contract tests for the explicit YouTube download smoke command."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

CANONICAL_TRANSPORT_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
SKILL_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[5]


def test_smoke_uses_the_canonical_transport_fixture() -> None:
    import youtube_smoke

    assert youtube_smoke.CANONICAL_TRANSPORT_URL == CANONICAL_TRANSPORT_URL


def test_canonical_fixture_is_documented_for_the_transport_check() -> None:
    for documentation in (SKILL_DIR / "SKILL.md", SKILL_DIR / "README.md"):
        content = documentation.read_text(encoding="utf-8")
        assert CANONICAL_TRANSPORT_URL in content
        assert "transport check" in content


def test_ytdlp_pin_matches_source_adapter_smoke_check_and_docs() -> None:
    import ytdlp_arc

    source_text = (SKILL_DIR / "scripts" / "transcript.py").read_text(encoding="utf-8")
    smoke_text = (SKILL_DIR / "scripts" / "youtube_smoke.py").read_text(
        encoding="utf-8"
    )
    source_pin = re.search(r'"yt-dlp==([^"\s]+)"', source_text)
    smoke_pin = re.search(r'"yt-dlp==([^"\s]+)"', smoke_text)

    assert source_pin is not None
    assert smoke_pin is not None
    assert source_pin.group(1) == smoke_pin.group(1) == "2026.7.4"
    normalized_adapter_pin = ".".join(
        str(int(part)) for part in ytdlp_arc.SUPPORTED_YTDLP_VERSION.split(".")
    )
    assert normalized_adapter_pin == source_pin.group(1)

    check_runner = (REPO_ROOT / "scripts" / "check.py").read_text(encoding="utf-8")
    assert f"yt-dlp=={source_pin.group(1)}" in check_runner
    for documentation in (SKILL_DIR / "SKILL.md", SKILL_DIR / "README.md"):
        assert source_pin.group(1) in documentation.read_text(encoding="utf-8")


def test_docs_explain_arc_transport_and_user_auth_responsibilities() -> None:
    required_phrases = (
        "Default",
        "valid YouTube session",
        "sign in again",
        "Arc can remain open",
        "YouTube Premium does not replace browser authentication",
        "If browser authentication fails",
        "transport check requires Arc",
    )
    for documentation in (SKILL_DIR / "SKILL.md", SKILL_DIR / "README.md"):
        content = documentation.read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in content


def test_docs_define_validation_boundaries_and_mandatory_e2e() -> None:
    required_phrases = (
        "Checks",
        "Automated tests",
        "CI",
        "Agent QA",
        "E2E",
        "Always finish",
    )
    for documentation in (SKILL_DIR / "SKILL.md", SKILL_DIR / "README.md"):
        content = documentation.read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in content
        qa_lines = [line for line in content.splitlines() if "QA" in line]
        assert qa_lines
        assert all("Agent QA" in line for line in qa_lines)


def test_smoke_downloads_validates_and_cleans_without_paid_services(
    monkeypatch, capsys
) -> None:
    import transcript
    import youtube_smoke

    observed_audio_paths: list[Path] = []

    def fake_download(_url, output_dir, _budget, *, auth_mode):
        assert auth_mode == "arc-required"
        audio_path = output_dir / "audio.webm"
        audio_path.write_bytes(b"audio")
        observed_audio_paths.append(audio_path)
        return transcript.DownloadedAudio(audio_path, "arc", "A video", "abc")

    def fake_run(command, **kwargs):
        assert command[0] == "ffprobe"
        assert kwargs["timeout"] > 0
        return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")

    monkeypatch.setattr(youtube_smoke, "download_audio", fake_download)
    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _command: "ffprobe")
    monkeypatch.setattr(youtube_smoke, "run_child", fake_run)
    monkeypatch.setattr(
        transcript,
        "transcribe_audio",
        lambda *_args: pytest.fail("smoke called Deepgram"),
    )
    monkeypatch.setattr(
        transcript,
        "run_summary_prompt",
        lambda *_args: pytest.fail("smoke called Pi or GPT"),
    )

    code = youtube_smoke.main([CANONICAL_TRANSPORT_URL])

    assert code == 0
    # A pass says nothing; -v reports the steps on stderr
    assert capsys.readouterr() == ("", "")
    assert len(observed_audio_paths) == 1
    assert not observed_audio_paths[0].parent.exists()


def test_smoke_cleans_temporary_audio_when_ffprobe_fails(monkeypatch) -> None:
    import transcript
    import youtube_smoke

    observed_audio_paths: list[Path] = []

    def fake_download(_url, output_dir, _budget, *, auth_mode):
        assert auth_mode == "arc-required"
        audio_path = output_dir / "audio.webm"
        audio_path.write_bytes(b"audio")
        observed_audio_paths.append(audio_path)
        return transcript.DownloadedAudio(audio_path, "arc", "A video", "abc")

    monkeypatch.setattr(youtube_smoke, "download_audio", fake_download)
    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _command: "ffprobe")
    monkeypatch.setattr(
        youtube_smoke,
        "run_child",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1, stdout="", stderr="invalid media"
        ),
    )

    code = youtube_smoke.main([CANONICAL_TRANSPORT_URL])

    assert code == 1
    assert not observed_audio_paths[0].parent.exists()


def test_smoke_bounds_ffprobe_with_the_global_budget(monkeypatch) -> None:
    import transcript
    import youtube_smoke

    observed_timeouts: list[float] = []

    def fake_download(_url, output_dir, _budget, *, auth_mode):
        assert auth_mode == "arc-required"
        audio_path = output_dir / "audio.webm"
        audio_path.write_bytes(b"audio")
        return transcript.DownloadedAudio(audio_path, "arc", "A video", "abc")

    def timeout(_command, **kwargs):
        observed_timeouts.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired("ffprobe", kwargs["timeout"])

    monkeypatch.setattr(youtube_smoke, "download_audio", fake_download)
    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _command: "ffprobe")
    monkeypatch.setattr(youtube_smoke, "run_child", timeout)

    code = youtube_smoke.main([CANONICAL_TRANSPORT_URL])

    assert code == youtube_smoke.TEMPORARY
    assert 0 < observed_timeouts[0] <= youtube_smoke.FFPROBE_TIMEOUT


def test_smoke_rejects_an_invalid_url_before_download(monkeypatch) -> None:
    import youtube_smoke

    monkeypatch.setattr(
        youtube_smoke,
        "download_audio",
        lambda *_args: pytest.fail("download started for an invalid URL"),
    )

    assert youtube_smoke.main(["https://example.com/video"]) == 2


def test_smoke_requires_ffprobe_before_download(monkeypatch, capsys) -> None:
    import youtube_smoke

    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _command: None)
    monkeypatch.setattr(
        youtube_smoke,
        "download_audio",
        lambda *_args, **_kwargs: pytest.fail("download started without ffprobe"),
    )

    assert youtube_smoke.main([CANONICAL_TRANSPORT_URL]) == 1
    assert "ffprobe was not found on PATH" in capsys.readouterr().err

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "yt-dlp==2026.7.4",
#     "rich",
# ]
# ///
"""Verify the YouTube audio transport without calling paid services."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from transcript import (
    RunBudget,
    WorkflowTimeoutError,
    YtDlpError,
    _clean_subprocess_diagnostic,
    download_audio,
    validate_youtube_url,
)

CANONICAL_TRANSPORT_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
FFPROBE_TIMEOUT = 30


def validate_audio_stream(audio_path: Path, budget: RunBudget) -> None:
    """Require ffprobe to find an audio stream in the downloaded media."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=budget.remaining("ffprobe", FFPROBE_TIMEOUT),
    )
    if result.returncode != 0 or "audio" not in result.stdout.split():
        details = _clean_subprocess_diagnostic(result.stderr or result.stdout)
        raise RuntimeError(
            f"ffprobe did not find a valid audio stream: {details or 'no diagnostic'}"
        )


def build_parser() -> argparse.ArgumentParser:
    """Build the standalone, free smoke-test CLI."""
    parser = argparse.ArgumentParser(
        description="Download and validate YouTube audio without Deepgram or AI",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=CANONICAL_TRANSPORT_URL,
        help=f"YouTube fixture URL (default: {CANONICAL_TRANSPORT_URL})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Download into a temporary directory, validate, and always clean it."""
    args = build_parser().parse_args(argv)
    if not validate_youtube_url(args.url):
        print(f"Invalid YouTube URL: {args.url}", file=sys.stderr)
        return 2
    if not shutil.which("ffprobe"):
        print(
            "ffprobe was not found on PATH; install ffmpeg and retry", file=sys.stderr
        )
        return 1

    budget = RunBudget.start()
    try:
        with tempfile.TemporaryDirectory(prefix="transcript-youtube-smoke-") as temp:
            downloaded = download_audio(
                args.url, Path(temp), budget, auth_mode="arc-required"
            )
            validate_audio_stream(downloaded.path, budget)
    except (
        OSError,
        RuntimeError,
        subprocess.SubprocessError,
        WorkflowTimeoutError,
        YtDlpError,
    ) as error:
        print(f"YouTube smoke failed: {error}", file=sys.stderr)
        return 1

    print("YouTube smoke passed: Arc adapter exercised; audio stream verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "yt-dlp[default]==2026.7.4",
#     "pycryptodomex",
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
from collections.abc import Sequence
from pathlib import Path

from transcript import (
    TEMPORARY,
    WORKFLOW_TOTAL_TIMEOUT,
    ConfigurationError,
    CookieFile,
    Failure,
    Parser,
    RunBudget,
    UsageError,
    WorkflowTimeoutError,
    YtDlpError,
    _clean_subprocess_diagnostic,
    _rerun,
    add_cookies_option,
    download_audio,
    duration,
    exit_codes,
    log,
    run_child,
    run_script,
    select_youtube_auth,
    validate_youtube_url,
    youtube_session,
)

PROG = "youtube_smoke.py"
DEBUG_ENV = "YOUTUBE_SMOKE_DEBUG"
CANONICAL_TRANSPORT_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
FFPROBE_TIMEOUT = 30
EXIT_CODES = exit_codes(
    {
        0: "the selected transport downloaded audio with a valid stream",
        1: "the transport check failed",
        TEMPORARY: "a network failure a later retry may fix",
    }
)


def validate_audio_stream(audio_path: Path, budget: RunBudget) -> None:
    """Require ffprobe to find an audio stream in the downloaded media."""
    result = run_child(
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
        timeout=budget.remaining("ffprobe", FFPROBE_TIMEOUT),
    )
    if result.returncode != 0 or "audio" not in result.stdout.split():
        details = _clean_subprocess_diagnostic(result.stderr or result.stdout)
        raise RuntimeError(
            f"ffprobe did not find a valid audio stream: {details or 'no diagnostic'}"
        )


def build_parser() -> Parser:
    """Build the standalone, free smoke-test CLI."""
    parser = Parser(
        prog=PROG,
        exit_codes=EXIT_CODES,
        description=(
            "Download YouTube audio through the stored session, Arc, or an explicit cookies file, and validate it with "
            'ffprobe, without Deepgram or AI. A pass answers {"ok":true}.'
        ),
        epilog=f"""examples:
  {PROG}
  {PROG} -v
  {PROG} {CANONICAL_TRANSPORT_URL} --timeout 2m""",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=CANONICAL_TRANSPORT_URL,
        help=f"YouTube fixture URL (default: {CANONICAL_TRANSPORT_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=float(WORKFLOW_TOTAL_TIMEOUT),
        metavar="DURATION",
        help=(
            "Deadline for the download and the check: 30s, 5m, 2h, or seconds "
            f"(default: {WORKFLOW_TOTAL_TIMEOUT}s)"
        ),
    )
    add_cookies_option(parser)
    return parser


def check(args: argparse.Namespace, argv: Sequence[str]) -> dict:
    """Download into a temporary directory, validate, and always clean it."""
    if not validate_youtube_url(args.url):
        raise UsageError(f"invalid YouTube URL: {args.url!r}")
    try:
        auth_mode = select_youtube_auth(args.cookies, fallback="arc-required")
    except ConfigurationError as error:
        raise UsageError(str(error)) from None
    rerun = _rerun(argv, prog=PROG)
    if not shutil.which("ffprobe"):
        raise Failure(
            "missing_ffprobe", "ffprobe was not found on PATH", "brew install ffmpeg"
        )

    budget = RunBudget.start(args.timeout)
    try:
        if isinstance(auth_mode, CookieFile) and auth_mode.verify_session:
            youtube_session.check_session(
                auth_mode.path, timeout=budget.remaining("YouTube session check", 25)
            )
        with tempfile.TemporaryDirectory(prefix="transcript-youtube-smoke-") as temp:
            transport = (
                "the cookies file"
                if isinstance(auth_mode, CookieFile)
                else "the Arc adapter"
            )
            log.info(f"Downloading {args.url} through {transport}")
            downloaded = download_audio(
                args.url, Path(temp), budget, auth_mode=auth_mode
            )
            log.info("Checking the audio stream with ffprobe")
            validate_audio_stream(downloaded.path, budget)
    except youtube_session.SessionError as error:
        raise Failure(
            "session_failed",
            str(error),
            "transcript auth refresh",
            code=TEMPORARY
            if isinstance(error, youtube_session.SessionNetworkError)
            else 1,
        ) from None
    except YtDlpError as error:
        if error.temporary:
            raise Failure(
                "temporary_failure",
                f"YouTube smoke failed: {error}",
                rerun,
                code=TEMPORARY,
                label="retry",
            ) from error
        repair = (
            "replace the YouTube cookies export"
            if isinstance(auth_mode, CookieFile)
            else "sign in to YouTube in Arc"
        )
        raise Failure(
            "transport_failed",
            f"YouTube smoke failed: {error}",
            f"{repair}, then run: {rerun}",
        ) from error
    except (WorkflowTimeoutError, subprocess.TimeoutExpired) as error:
        raise Failure(
            "temporary_failure",
            f"YouTube smoke timed out: {error}",
            _rerun(argv, drop={"--timeout"}, add=("--timeout", "20m"), prog=PROG),
            code=TEMPORARY,
            label="retry",
        ) from error
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        raise Failure(
            "transport_failed",
            f"YouTube smoke failed: {error}",
            _rerun(argv, drop={"--debug"}, add=("--debug",), prog=PROG),
            label="rerun",
        ) from error

    log.info(
        "Cookies-file transport exercised; audio stream verified"
        if isinstance(auth_mode, CookieFile)
        else "Arc adapter exercised; audio stream verified"
    )
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    """Run the transport check and answer it in one JSON line; return its exit
    code, as listed in --help."""
    argv = list(sys.argv[1:] if argv is None else argv)
    return run_script(
        build_parser(), lambda args: check(args, argv), argv, debug=DEBUG_ENV
    )


if __name__ == "__main__":
    raise SystemExit(main())

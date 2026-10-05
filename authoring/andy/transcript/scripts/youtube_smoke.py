# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "yt-dlp==2026.7.4",
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
    Failure,
    Parser,
    RunBudget,
    WorkflowTimeoutError,
    YtDlpError,
    _clean_subprocess_diagnostic,
    _rerun,
    download_audio,
    duration,
    exit_codes,
    given,
    log,
    run_child,
    run_guarded,
    validate_youtube_url,
)

PROG = "youtube_smoke.py"
DEBUG_ENV = "YOUTUBE_SMOKE_DEBUG"
CANONICAL_TRANSPORT_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
FFPROBE_TIMEOUT = 30
EXIT_CODES = exit_codes(
    {
        0: "the Arc adapter downloaded audio with a valid stream",
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
            "Download YouTube audio through the Arc adapter and validate it with "
            "ffprobe, without Deepgram or AI. A pass prints nothing."
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
        "-v",
        "--verbose",
        action="store_true",
        help="Print progress and step details on stderr",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=f"Print internals, timings, and tracebacks on stderr; also {DEBUG_ENV}=1",
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
    return parser


def check(args: argparse.Namespace, argv: Sequence[str]) -> int:
    """Download into a temporary directory, validate, and always clean it."""
    rerun = _rerun(argv, prog=PROG)
    if not shutil.which("ffprobe"):
        raise Failure(
            "missing_ffprobe", "ffprobe was not found on PATH", "brew install ffmpeg"
        )

    budget = RunBudget.start(args.timeout)
    try:
        with tempfile.TemporaryDirectory(prefix="transcript-youtube-smoke-") as temp:
            log.info(f"Downloading {args.url} through the Arc adapter")
            downloaded = download_audio(
                args.url, Path(temp), budget, auth_mode="arc-required"
            )
            log.info("Checking the audio stream with ffprobe")
            validate_audio_stream(downloaded.path, budget)
    except YtDlpError as error:
        if error.temporary:
            raise Failure(
                "temporary_failure",
                f"YouTube smoke failed: {error}",
                rerun,
                code=TEMPORARY,
                label="retry",
            ) from error
        raise Failure(
            "transport_failed",
            f"YouTube smoke failed: {error}",
            f"sign in to YouTube in Arc, then run: {rerun}",
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

    log.info("Arc adapter exercised; audio stream verified")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the transport check and return its exit code, as listed in --help."""
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if given(argv, "-h", "--help", parser=parser):
        parser.print_help()
        return 0

    def parse() -> argparse.Namespace:
        args = parser.parse_args(argv)
        if not validate_youtube_url(args.url):
            parser.error(f"invalid YouTube URL: {args.url!r}")
        return args

    return run_guarded(
        argv,
        parse,
        lambda args, _warnings: check(args, argv),
        prog=PROG,
        debug_env=DEBUG_ENV,
        as_json=False,
    )


if __name__ == "__main__":
    raise SystemExit(main())

"""The CLI contract in docs/maintainer/references/script-conventions.md, for
transcript.py and youtube_smoke.py.

scripts/tests/test_cli_contract.py probes the flat scripts in scripts/; these two
have subcommands and PEP 723 dependencies, so this suite runs the same probes
here, where the transcript check provides those dependencies. In-process
probes call main() the way the command line does. Signal and terminal probes run
the real script with this test's Python, in an isolated home with stub commands
first on PATH. Nothing here reaches the network.
"""

from __future__ import annotations

import json
import os
import pty
import re
import select
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from itertools import takewhile
from pathlib import Path

import httpx
import pytest
import transcript
import youtube_smoke
from conftest import DECLARED, covers, exits, observe
from test_transcript import deepgram_response

SCRIPTS = Path(__file__).parent.parent
SKILL_DIR = SCRIPTS.parent
REPO_ROOT = SKILL_DIR.parents[2]
URL = "https://youtu.be/abc"

# Every help page, with the exit codes it must list
COMMANDS: dict[tuple[str, ...], dict[int, str]] = {
    (): transcript.EXIT_CODES,
    ("run",): transcript.EXIT_CODES,
    ("run", "youtube"): transcript.EXIT_CODES,
    ("run", "zoom"): transcript.EXIT_CODES,
    ("list",): transcript.LIST_EXIT_CODES,
    ("list", "prompts"): transcript.LIST_EXIT_CODES,
    ("list", "profiles"): transcript.LIST_EXIT_CODES,
    ("list", "models"): transcript.LIST_EXIT_CODES,
    ("doctor",): transcript.DOCTOR_EXIT_CODES,
    ("help",): transcript.LIST_EXIT_CODES,
}


def section(text: str, title: str) -> list[str]:
    """The lines under `title:` in a help page, up to the next blank line."""
    lines = text.splitlines()
    return list(takewhile(str.strip, lines[lines.index(f"{title}:") + 1 :]))


def cli(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    """Run transcript's main() the way the command line does."""
    code = observe("transcript", transcript.main(list(argv)))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def smoke(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = observe("youtube_smoke", youtube_smoke.main(list(argv)))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


FALLBACK = "Arc YouTube access failed; retrying anonymously"


def fall_back_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Warn from both yt-dlp steps, as a run without a browser session does."""

    def warn_then_download(_url, output_dir, *_args, **_kwargs):
        transcript.log.warning(FALLBACK)
        audio = output_dir / "audio.mp3"
        audio.write_bytes(b"audio")
        return transcript.DownloadedAudio(audio, "anonymous")

    def warn_then_describe(*_args):
        transcript.log.warning(FALLBACK)
        return {"title": "A video", "video_id": "abc"}

    fake_youtube(monkeypatch, download=warn_then_download)
    monkeypatch.setattr(transcript, "get_video_info", warn_then_describe)


def fake_youtube(
    monkeypatch: pytest.MonkeyPatch,
    *,
    download: Callable[..., object] | None = None,
    transcribe: Callable[..., object] | None = None,
) -> None:
    """Stand in for every paid or networked step of a YouTube run."""

    def fake_download(_url, output_dir, *_args, **_kwargs):
        audio = output_dir / "audio.mp3"
        audio.write_bytes(b"audio")
        return transcript.DownloadedAudio(audio, "anonymous")

    monkeypatch.setattr(transcript, "validate_env", lambda *_args: "secret")
    monkeypatch.setattr(transcript, "ensure_cli_available", lambda *_args: None)
    monkeypatch.setattr(
        transcript,
        "get_video_info",
        lambda *_args: {"title": "A video", "video_id": "abc"},
    )
    monkeypatch.setattr(transcript, "download_audio", download or fake_download)
    monkeypatch.setattr(
        transcript,
        "transcribe_audio",
        transcribe or (lambda *_args: deepgram_response()),
    )


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("command", list(COMMANDS), ids=lambda c: " ".join(c) or "root")
def test_every_help_page_lists_examples_and_exit_codes_and_wins(
    command: tuple[str, ...], capsys
) -> None:
    code, shown, err = cli(capsys, *command, "--help")
    name = " ".join(("transcript", *command))
    examples = section(shown, "examples")
    codes = [int(line.split()[0]) for line in section(shown, "exit codes")]

    assert (code, err) == (0, "")
    assert shown.startswith(f"usage: {name} ")
    assert 2 <= len(examples) <= 5
    assert all(example.lstrip().startswith("transcript ") for example in examples)
    assert codes == list(COMMANDS[command])
    for argv in (
        [*command, "-h"],
        [*command, "--bogus-flag", "--help"],
        [*command, "--help", "--bogus-flag"],
        ["help", *command],
    ):
        assert cli(capsys, *argv) == (0, shown, ""), argv


@pytest.mark.parametrize(
    ("argv", "command"),
    [
        (["run", "youtube", "--timeout", "nope", "-vh"], ["run", "youtube"]),
        (["ru", "-vh"], []),
    ],
    ids=["bad-value-first", "unknown-command-first"],
)
def test_a_bundled_help_flag_wins_too(
    argv: list[str], command: list[str], capsys
) -> None:
    shown = cli(capsys, *command, "--help")

    assert cli(capsys, *argv) == shown


def test_version_is_one_line_on_stdout(capsys) -> None:
    assert cli(capsys, "--version") == (0, f"transcript {transcript.__version__}\n", "")


def test_smoke_help_lists_examples_and_exit_codes_and_wins(capsys) -> None:
    code, shown, err = smoke(capsys, "--help")
    examples = section(shown, "examples")
    codes = [int(line.split()[0]) for line in section(shown, "exit codes")]

    assert (code, err) == (0, "")
    assert 2 <= len(examples) <= 5
    assert codes == list(youtube_smoke.EXIT_CODES)
    for argv in (["-h"], ["--bogus-flag", "--help"], ["--help", "--bogus-flag"]):
        assert smoke(capsys, *argv) == (0, shown, "")


def test_a_bundled_help_flag_wins_in_the_smoke_check_too(capsys) -> None:
    shown = smoke(capsys, "--help")

    assert smoke(capsys, "--timeout", "nope", "-vh") == shown


def test_a_smoke_retry_hint_keeps_the_url_after_double_dash(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _name: "/bin/ffprobe")
    monkeypatch.setattr(
        youtube_smoke,
        "download_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            transcript.WorkflowTimeoutError("budget exhausted before the download")
        ),
    )

    code, out, err = smoke(capsys, "--", URL)

    assert (code, out) == (75, "")
    assert err.splitlines()[-1] == f"retry: youtube_smoke.py --timeout 20m -- {URL}"


# ---------------------------------------------------------------------------
# Usage errors and parsing
# ---------------------------------------------------------------------------


@exits("transcript", 2)
@pytest.mark.parametrize(
    ("argv", "command", "error"),
    [
        ([], "transcript", "the following arguments are required: COMMAND"),
        (
            ["run", "youtube"],
            "transcript run youtube",
            "the following arguments are required: --url",
        ),
        (
            ["list", "prompts", "--bogus-flag"],
            "transcript list prompts",
            "unrecognized arguments: --bogus-flag",
        ),
        (
            ["list", "prompts", "--jso"],
            "transcript list prompts",
            "unrecognized arguments: --jso",
        ),
        (
            ["ru"],
            "transcript",
            "argument COMMAND: unknown command 'ru'; did you mean 'run'?",
        ),
        (
            ["list", "prompt"],
            "transcript list",
            "argument RESOURCE: unknown command 'prompt'; did you mean 'prompts'?",
        ),
        (
            ["help", "lst"],
            "transcript help",
            "unknown command 'lst'; did you mean 'list'?",
        ),
        (
            ["run", "youtube", "--url", URL, "--timeout", "0"],
            "transcript run youtube",
            (
                "argument --timeout: invalid duration '0'; use a positive number of "
                "seconds, or 30s, 5m, 2h"
            ),
        ),
        (
            ["run", "youtube", "--url", "https://example.com/video", "-n"],
            "transcript run youtube",
            "Invalid YouTube URL: https://example.com/video",
        ),
        (
            ["run", "youtube", "--url", URL, "--prompt", "nope", "-n"],
            "transcript run youtube",
            (
                "Unknown prompt 'nope'. Available prompts: follow_along_note, "
                "short_summary, summary_with_quotes"
            ),
        ),
    ],
    ids=[
        "no-command",
        "missing-url",
        "unknown-flag",
        "abbreviated-flag",
        "unknown-command",
        "unknown-resource",
        "unknown-help-topic",
        "bad-duration",
        "invalid-url",
        "unknown-prompt",
    ],
)
def test_a_usage_error_exits_2_with_short_usage_and_the_help_hint(
    argv: list[str], command: str, error: str, capsys
) -> None:
    code, out, err = cli(capsys, *argv)
    lines = err.splitlines()

    assert (code, out) == (2, "")
    assert lines[0].startswith(f"usage: {command} ")
    assert f"error: {error}" in lines
    assert lines[-1] == f"run '{command} --help'"


@exits("youtube_smoke", 2)
@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (["--bogus-flag"], "unrecognized arguments: --bogus-flag"),
        (
            ["https://example.com/video"],
            "invalid YouTube URL: 'https://example.com/video'",
        ),
    ],
    ids=["unknown-flag", "invalid-url"],
)
def test_a_smoke_usage_error_exits_2_with_the_help_hint(
    argv: list[str], error: str, capsys
) -> None:
    code, out, err = smoke(capsys, *argv)

    assert (code, out) == (2, "")
    assert f"error: {error}" in err.splitlines()
    assert err.splitlines()[-1] == "run 'youtube_smoke.py --help'"


def test_a_json_usage_error_is_one_object_on_stderr(capsys) -> None:
    code, out, err = cli(capsys, "list", "prompts", "--json", "--bogus-flag")

    assert (code, out) == (2, "")
    assert json.loads(err) == {
        "ok": False,
        "error": {
            "code": "invalid_usage",
            "message": "unrecognized arguments: --bogus-flag",
            "hint": "transcript list prompts --help",
        },
    }


def test_a_pasted_url_names_the_command_it_was_meant_for(capsys) -> None:
    code, _out, err = cli(capsys, URL)

    assert code == 2
    assert f"to transcribe it, run: transcript run youtube --url {URL}" in err


def test_double_dash_ends_options_so_help_after_it_is_an_argument(capsys) -> None:
    code, out, _err = cli(capsys, "list", "prompts", "--", "--help")

    assert (code, out) == (2, "")


@pytest.mark.parametrize(
    ("spaced", "joined"),
    [
        (
            ["run", "youtube", "--url", URL, "--timeout", "5m", "-v", "-n"],
            ["run", "youtube", f"--url={URL}", "--timeout=5m", "-vn"],
        ),
        (["list", "prompts", "--json"], ["--json", "list", "prompts"]),
        (
            ["run", "youtube", "--url", URL, "-n", "-v"],
            ["-v", "run", "youtube", "--url", URL, "-n"],
        ),
    ],
    ids=["equals-and-bundled-shorts", "global-json-first", "global-verbose-first"],
)
def test_equivalent_spellings_give_identical_results(
    spaced: list[str], joined: list[str], capsys
) -> None:
    assert cli(capsys, *spaced) == cli(capsys, *joined)


def test_a_duration_reaches_the_plan_in_seconds(capsys) -> None:
    code, out, _err = cli(
        capsys, "run", "youtube", "--url", URL, "--timeout", "5m", "-n", "--json"
    )

    assert code == 0
    assert json.loads(out)["timeout_seconds"] == 300.0


# ---------------------------------------------------------------------------
# Output: silence, verbosity, and JSON
# ---------------------------------------------------------------------------


@exits("transcript", 0)
def test_a_successful_run_prints_only_its_result_folder(
    tmp_path, monkeypatch, capsys
) -> None:
    fake_youtube(monkeypatch)

    code, out, err = cli(
        capsys,
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
    )

    result = next(tmp_path.iterdir())
    assert (code, out, err) == (0, f"{result}\n", "")
    assert (result / "raw_transcript.txt").read_text() == "Hello world"


@pytest.mark.parametrize(
    "argv",
    [
        ["list", "prompts"],
        ["run", "youtube", "--url", URL, "--dry-run"],
        ["run", "youtube", "--url", URL, "--no-summary", "--output-dir", "{out}"],
    ],
    ids=["list", "dry-run", "run"],
)
def test_verbosity_changes_only_stderr(
    argv: list[str], tmp_path, monkeypatch, capsys
) -> None:
    fake_youtube(monkeypatch)
    levels = {"default": [], "verbose": ["-v"], "debug": ["--debug"]}
    runs = {}
    for level, flags in levels.items():
        out_dir = tmp_path / level
        code, out, err = cli(
            capsys, *(a.replace("{out}", str(out_dir)) for a in argv), *flags
        )
        runs[level] = (code, out.replace(str(out_dir), "<out>"), err)
    monkeypatch.setenv(transcript.DEBUG_ENV, "1")
    code, out, via_env = cli(
        capsys, *(a.replace("{out}", str(tmp_path / "env")) for a in argv)
    )

    assert runs["default"][2] == ""
    assert {(c, o) for c, o, _ in runs.values()} == {runs["default"][:2]}
    assert (code, out.replace(str(tmp_path / "env"), "<out>")) == runs["default"][:2]
    assert not any(
        line.startswith("debug: ") for line in runs["verbose"][2].splitlines()
    )
    assert "Traceback" not in runs["verbose"][2]
    assert len(via_env.splitlines()) == len(runs["debug"][2].splitlines())
    if argv[0] == "run" and "--dry-run" not in argv:
        assert "Completed Publication" in runs["verbose"][2]
        assert "debug: workflow deadline: 570s" in runs["debug"][2]


@pytest.mark.parametrize(
    "argv",
    [
        ["list", "prompts", "--json"],
        ["list", "profiles", "--json"],
        ["list", "models", "--json"],
        ["run", "youtube", "--url", URL, "--dry-run", "--json"],
        [
            "run",
            "youtube",
            "--url",
            URL,
            "--no-summary",
            "--output-dir",
            "{out}",
            "--json",
        ],
    ],
    ids=["prompts", "profiles", "models", "dry-run", "run"],
)
def test_json_stdout_is_exactly_one_object(
    argv: list[str], tmp_path, monkeypatch, capsys
) -> None:
    fake_youtube(monkeypatch)

    code, out, err = cli(capsys, *(a.replace("{out}", str(tmp_path)) for a in argv))

    assert (code, err) == (0, "")
    assert isinstance(json.loads(out), dict)
    assert out.count("\n") == 1


def test_json_warnings_join_the_object_once_and_leave_stderr_empty(
    tmp_path, monkeypatch, capsys
) -> None:
    fall_back_twice(monkeypatch)

    code, out, err = cli(
        capsys,
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
        "--json",
    )

    assert (code, err) == (0, "")
    assert json.loads(out)["warnings"] == [FALLBACK]


def test_a_human_warning_goes_to_stderr_once_and_keeps_success(
    tmp_path, monkeypatch, capsys
) -> None:
    fall_back_twice(monkeypatch)

    code, out, err = cli(
        capsys,
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
    )

    assert code == 0
    assert out == f"{next(tmp_path.iterdir())}\n"
    assert err == f"warning: {FALLBACK}\n"


def test_a_failed_finder_launch_warns_and_keeps_success(
    tmp_path, monkeypatch, capsys
) -> None:
    def no_open(command, **_kwargs):
        raise FileNotFoundError(2, "No such file or directory", command[0])

    fake_youtube(monkeypatch)
    monkeypatch.setattr(transcript.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(transcript, "run_child", no_open)

    code, out, err = cli(
        capsys,
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
        "--open",
    )

    assert code == 0
    assert out == f"{next(tmp_path.iterdir())}\n"
    assert err.startswith("warning: Could not open the output folder in Finder: ")


def test_a_dry_run_prints_where_the_result_would_go_and_writes_nothing(
    tmp_path, capsys
) -> None:
    out_dir = tmp_path / "parent"

    code, out, err = cli(
        capsys, "run", "youtube", "--url", URL, "--output-dir", str(out_dir), "-n"
    )

    assert (code, out, err) == (0, f"{out_dir}\n", "")
    assert not out_dir.exists()


# ---------------------------------------------------------------------------
# Exit codes: 1 and 75
# ---------------------------------------------------------------------------


@exits("transcript", 1)
def test_a_failed_summary_leaves_stdout_empty_and_names_the_saved_transcript(
    tmp_path, monkeypatch, capsys
) -> None:
    fake_youtube(monkeypatch)
    monkeypatch.setattr(
        transcript,
        "run_summary_prompt",
        lambda *_args: (_ for _ in ()).throw(transcript.SummaryCLIError("quota")),
    )
    argv = ["run", "youtube", "--url", URL, "--output-dir", str(tmp_path), "--json"]

    code, out, err = cli(capsys, *argv)

    result = next(tmp_path.iterdir())
    failure = json.loads(err)
    assert (code, out) == (1, "")
    assert failure["output_dir"] == str(result)
    assert failure["summary"]["status"] == "failed"
    assert failure["artifacts"]["transcript"] == str(result / "raw_transcript.txt")
    assert failure["error"] == {
        "code": "summary_failed",
        "message": f"Summary generation failed: quota. The transcript is saved in {result}",
        "hint": shlex.join(["transcript", *argv, "--profile", "sol"]),
    }


@exits("transcript", 1)
def test_a_failed_doctor_check_exits_1_with_the_report_on_stderr(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(transcript, "ZOOM_ROOT", tmp_path / "missing")
    monkeypatch.setattr(transcript, "validate_env", lambda *_args: "secret")
    monkeypatch.setattr(transcript.shutil, "which", lambda name: f"/bin/{name}")

    code, out, err = cli(capsys, "doctor", "--source", "zoom")

    assert (code, out) == (1, "")
    assert err.splitlines()[-2:] == [
        "error: 1 required check failed: zoom_recordings",
        (
            "fix: Record a Zoom meeting locally, or check YouTube only: "
            "transcript doctor --source youtube"
        ),
    ]


@exits("transcript", 75)
@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("connection refused"),
        httpx.HTTPStatusError(
            "busy",
            request=httpx.Request("POST", "https://api.deepgram.com"),
            response=httpx.Response(429),
        ),
    ],
    ids=["connect", "429"],
)
def test_deepgram_refusing_the_audio_is_safe_to_retry(
    error: Exception, tmp_path, monkeypatch, capsys
) -> None:
    fake_youtube(monkeypatch, transcribe=lambda *_args: (_ for _ in ()).throw(error))
    argv = [
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
    ]

    code, out, err = cli(capsys, *argv)

    assert (code, out) == (75, "")
    assert err.splitlines()[-1] == f"retry: {shlex.join(['transcript', *argv])}"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "error",
    [
        httpx.ReadTimeout("no response after upload"),
        httpx.HTTPStatusError(
            "boom",
            request=httpx.Request("POST", "https://api.deepgram.com"),
            response=httpx.Response(500),
        ),
    ],
    ids=["read-timeout", "500"],
)
def test_a_deepgram_failure_that_may_have_been_paid_is_never_75(
    error: Exception, tmp_path, monkeypatch, capsys
) -> None:
    fake_youtube(monkeypatch, transcribe=lambda *_args: (_ for _ in ()).throw(error))

    code, out, _err = cli(
        capsys,
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
    )

    assert (code, out) == (1, "")


@exits("transcript", 75)
def test_a_deadline_passing_before_deepgram_is_safe_to_retry(
    tmp_path, monkeypatch, capsys
) -> None:
    now = [0.0]

    def slow_download(_url, output_dir, *_args, **_kwargs):
        now[0] = 10_000.0
        audio = output_dir / "audio.mp3"
        audio.write_bytes(b"audio")
        return transcript.DownloadedAudio(audio, "anonymous")

    monkeypatch.setattr(transcript.time, "monotonic", lambda: now[0])
    fake_youtube(
        monkeypatch,
        download=slow_download,
        transcribe=lambda *_args: pytest.fail("Deepgram was called after the deadline"),
    )

    code, out, err = cli(
        capsys,
        "run",
        "youtube",
        "--url",
        URL,
        "--no-summary",
        "--output-dir",
        str(tmp_path),
    )

    assert (code, out) == (75, "")
    assert err.splitlines()[-1].startswith("retry: transcript run youtube ")


def test_a_network_failure_reaching_youtube_is_safe_to_retry(
    monkeypatch, capsys
) -> None:
    responses = [
        subprocess.CompletedProcess([], 1, "", "ERROR: Sign in failed"),
        subprocess.CompletedProcess(
            [], 1, "", "ERROR: HTTP Error 429: Too Many Requests"
        ),
    ]
    monkeypatch.setattr(
        transcript, "run_child", lambda *_args, **_kwargs: responses.pop(0)
    )
    monkeypatch.setattr(transcript, "validate_env", lambda *_args: "secret")

    code, out, err = cli(capsys, "run", "youtube", "--url", URL, "--no-summary")

    assert (code, out) == (75, "")
    assert "retry: transcript run youtube" in err


@exits("youtube_smoke", 0, 1, 75)
def test_smoke_exit_codes_follow_the_transport_outcome(monkeypatch, capsys) -> None:
    def downloaded(_url, output_dir, *_args, **_kwargs):
        audio = output_dir / "audio.mp3"
        audio.write_bytes(b"audio")
        return transcript.DownloadedAudio(audio, "arc")

    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _name: "/bin/ffprobe")
    monkeypatch.setattr(youtube_smoke, "download_audio", downloaded)
    monkeypatch.setattr(
        youtube_smoke,
        "run_child",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "audio\n", ""),
    )
    assert smoke(capsys) == (0, "", "")
    verbose = smoke(capsys, "-v")
    assert verbose[:2] == (0, "")
    assert "Arc adapter exercised; audio stream verified" in verbose[2]

    monkeypatch.setattr(
        youtube_smoke,
        "download_audio",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            transcript.YtDlpError("HTTP Error 503", temporary=True)
        ),
    )
    code, out, err = smoke(capsys)
    assert (code, out) == (75, "")
    assert err.splitlines()[-1] == "retry: youtube_smoke.py"

    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _name: None)
    code, out, err = smoke(capsys)
    assert (code, out) == (1, "")
    assert err.splitlines()[-1] == "fix: brew install ffmpeg"


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

# Blocks until SIGTERM, then stops its own child, says it is cleaning up, and
# waits for the test to release it; it marks itself ready once the trap is set
STUB = """\
#!/bin/sh
trap 'kill "$child"; : > "{ready}.cleanup"; while [ ! -e "{ready}.release" ]; do sleep 0.05; done; exit 0' TERM
sleep 60 &
child=$!
echo "$$ $child" > "{ready}.tmp" && mv "{ready}.tmp" "{ready}"
wait
"""


@dataclass(frozen=True)
class Sandbox:
    """An isolated home and a bin/ of stub commands first on PATH."""

    home: Path
    bin: Path

    def env(self, **extra: str) -> dict[str, str]:
        env = {
            name: value
            for name, value in os.environ.items()
            if not name.endswith("_DEBUG")
            and name not in {"DEEPGRAM_API_KEY", "NO_COLOR", "FORCE_COLOR"}
        }
        return {
            **env,
            "HOME": str(self.home),
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            **extra,
        }

    def stub(self, name: str, body: str) -> None:
        path = self.bin / name
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def command(self, *args: str) -> list[str]:
        return [sys.executable, str(SCRIPTS / "transcript.py"), *args]


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    box = Sandbox(tmp_path / "home", tmp_path / "bin")
    box.home.mkdir()
    box.bin.mkdir()
    # The real keyring must never answer
    box.stub("chezmoi", "#!/bin/sh\nexit 1\n")
    return box


def alive(pid: int) -> bool:
    """Whether `pid` runs; a zombie waiting for init counts as gone."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    try:
        state = Path(f"/proc/{pid}/stat").read_text().split(") ")[-1]
    except FileNotFoundError:
        return not Path("/proc/self/stat").exists()
    return not state.startswith("Z")


def wait_for(condition: Callable[[], object], what: str, seconds: float = 30) -> None:
    deadline = time.monotonic() + seconds
    while not condition():
        assert time.monotonic() < deadline, f"timed out waiting for {what}"
        time.sleep(0.05)


@covers("transcript", 130, 143)
@pytest.mark.parametrize(
    ("first", "repeat", "code", "last"),
    [
        (signal.SIGINT, None, 130, "interrupted"),
        (signal.SIGTERM, None, 143, "terminated"),
        (signal.SIGTERM, signal.SIGINT, 143, "terminated"),
    ],
    ids=["sigint", "sigterm", "repeat"],
)
def test_a_signal_exits_without_a_traceback_and_stops_children_gently(
    sandbox: Sandbox,
    first: signal.Signals,
    repeat: signal.Signals | None,
    code: int,
    last: str,
    tmp_path: Path,
) -> None:
    # The keyring lookup blocks, so the signal lands while a child runs
    ready = tmp_path / "ready"
    sandbox.stub("chezmoi", STUB.format(ready=ready))
    process = subprocess.Popen(
        sandbox.command("run", "youtube", "--url", URL, "--no-summary"),
        cwd=sandbox.home,
        env=sandbox.env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    children: list[int] = []
    try:
        wait_for(ready.exists, "the stub to block")
        children = [int(pid) for pid in ready.read_text().split()]
        process.send_signal(first)
        wait_for(Path(f"{ready}.cleanup").exists, "the stub to get SIGTERM")
        if repeat is not None:
            process.send_signal(repeat)
            time.sleep(0.3)
            assert process.poll() is None, "a repeated signal cut cleanup short"
        Path(f"{ready}.release").touch()
        stdout, stderr = process.communicate(timeout=30)
        observe("transcript", process.returncode)

        assert process.returncode == code, stderr
        assert (stdout, stderr.splitlines()[-1]) == ("", last)
        assert "Traceback" not in stderr
        for pid in children:
            wait_for(lambda pid=pid: not alive(pid), f"process {pid} to end", 10)
    finally:
        process.kill()
        process.wait()
        Path(f"{ready}.release").touch()
        for pid in children:
            if alive(pid):
                os.kill(pid, signal.SIGKILL)


# A child that starts its own child and has no TERM trap, as yt-dlp starts ffmpeg
UNCOOPERATIVE = """\
#!/bin/sh
sleep 60 &
echo "$!" > "{ready}.tmp" && mv "{ready}.tmp" "{ready}"
wait
"""


def test_a_signal_also_stops_what_a_child_started(
    sandbox: Sandbox, tmp_path: Path
) -> None:
    ready = tmp_path / "ready"
    sandbox.stub("chezmoi", UNCOOPERATIVE.format(ready=ready))
    process = subprocess.Popen(
        sandbox.command("run", "youtube", "--url", URL, "--no-summary"),
        cwd=sandbox.home,
        env=sandbox.env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    grandchild = 0
    try:
        wait_for(ready.exists, "the stub to start its own child")
        grandchild = int(ready.read_text())
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=60)

        assert observe("transcript", process.returncode) == 143
        wait_for(lambda: not alive(grandchild), "the grandchild to end", 5)
    finally:
        process.kill()
        process.wait()
        if grandchild and alive(grandchild):
            os.kill(grandchild, signal.SIGKILL)


def test_a_child_on_the_terminal_stays_in_our_process_group(monkeypatch) -> None:
    """glow and Finder share the terminal; in another process group, glow would
    stop the moment it read the terminal to learn its colors."""
    monkeypatch.undo()  # run one real, harmless child
    same_group = f"import os, sys; sys.exit(os.getpgid(0) != {os.getpgid(0)})"

    result = transcript.run_child([sys.executable, "-c", same_group], capture=False)

    assert result.returncode == 0


@covers("youtube_smoke", 130, 143)
@pytest.mark.parametrize(
    ("number", "code", "word"),
    [(signal.SIGINT, 130, "interrupted"), (signal.SIGTERM, 143, "terminated")],
    ids=["sigint", "sigterm"],
)
def test_a_signal_stops_the_smoke_check_and_removes_its_download(
    number: signal.Signals, code: int, word: str, monkeypatch, capsys
) -> None:
    downloads: list[Path] = []

    def signalled_download(_url, output_dir, *_args, **_kwargs):
        downloads.append(output_dir)
        (output_dir / "audio.mp3").write_bytes(b"partial")
        os.kill(os.getpid(), number)
        time.sleep(5)
        pytest.fail("the signal did not interrupt the download")

    monkeypatch.setattr(youtube_smoke.shutil, "which", lambda _name: "/bin/ffprobe")
    monkeypatch.setattr(youtube_smoke, "download_audio", signalled_download)

    assert smoke(capsys) == (code, "", f"{word}\n")
    assert not downloads[0].exists()


# ---------------------------------------------------------------------------
# Terminal: color and the spinner
# ---------------------------------------------------------------------------


def on_terminal(sandbox: Sandbox, *args: str, **env: str) -> bytes:
    """Run transcript with stderr on a pseudo-terminal; return what it drew."""
    leader, follower = pty.openpty()
    process = subprocess.Popen(
        sandbox.command(*args),
        cwd=sandbox.home,
        env=sandbox.env(**{"TERM": "xterm-256color", **env}),
        stdout=subprocess.DEVNULL,
        stderr=follower,
    )
    os.close(follower)
    drawn = []
    deadline = time.monotonic() + 60
    try:
        while True:
            assert time.monotonic() < deadline, "the run kept its terminal too long"
            ready, _, _ = select.select([leader], [], [], 0.5)
            if not ready:
                if process.poll() is not None:
                    break
                continue
            try:
                chunk = os.read(leader, 4096)
            except OSError:  # the terminal closed with the process
                break
            if not chunk:
                break
            drawn.append(chunk)
    finally:
        process.kill()
        process.wait()
        os.close(leader)
    return b"".join(drawn)


@pytest.mark.parametrize(
    ("flags", "env", "animated"),
    [
        ([], {}, True),
        (["--no-progress"], {}, False),
        (["--no-color"], {}, False),
        ([], {"NO_COLOR": "1"}, False),
        ([], {"TERM": "dumb"}, False),
    ],
    ids=["terminal", "no-progress", "no-color", "NO_COLOR", "TERM=dumb"],
)
def test_the_spinner_animates_only_on_a_terminal_that_allows_it(
    sandbox: Sandbox, flags: list[str], env: dict[str, str], animated: bool
) -> None:
    # A slow keyring keeps the Preflight step on screen long enough to draw
    sandbox.stub("chezmoi", "#!/bin/sh\nsleep 1\nexit 1\n")

    drawn = on_terminal(
        sandbox, "run", "youtube", "--url", URL, "--no-summary", *flags, **env
    )

    assert b"Missing Deepgram API key" in drawn
    assert (b"\x1b[" in drawn) is animated


# ---------------------------------------------------------------------------
# Documentation and the exit-code table
# ---------------------------------------------------------------------------

DOCS = [
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "README.md",
    REPO_ROOT / "justfile",
    REPO_ROOT / "authoring/verify/verify-transcript/SKILL.md",
]
# A doc line runs transcript through its path or a just recipe
RUNS = re.compile(
    r"scripts/(transcript|youtube_smoke)\.py|just (ttr|transcript)(?:-cli)?\b"
)
FLAG = re.compile(r"(?<![\w/.-])(--?[A-Za-z][\w-]*)")


def doc_commands() -> list[tuple[str, str, list[str]]]:
    """Each script run in the docs: where, which script, and its arguments."""
    found = []
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8").replace("\\\n", " ")
        for number, line in enumerate(text.splitlines(), start=1):
            for match in RUNS.finditer(line):
                rest = re.split(r"[`|;&#)]|\$@", line[match.end() :])[0]
                try:
                    args = shlex.split(rest)
                except ValueError:
                    args = rest.split()
                if match.group(2) == "ttr" or (
                    match.group(2) == "transcript" and "-cli" not in match.group(0)
                ):
                    args = ["run", "youtube", "--url", *args]
                script = match.group(1) or "transcript"
                found.append((f"{doc.name}:{number}", script, args))
    return found


def help_flags(
    capsys: pytest.CaptureFixture[str], script: str, args: list[str]
) -> set[str]:
    """The flags the help page of the command `args` names accepts."""
    if script == "youtube_smoke":
        return set(FLAG.findall(smoke(capsys, "--help")[1]))
    target = transcript.build_parser()
    command: list[str] = []
    for token in args:
        if token in (children := transcript._subcommands(target)):
            target = children[token]
            command.append(token)
    return set(FLAG.findall(cli(capsys, *command, "--help")[1]))


def test_doc_lines_that_run_a_script_use_only_its_flags(capsys) -> None:
    commands = doc_commands()
    unknown = [
        f"{where}: {flag}"
        for where, script, args in commands
        for flag in (arg.split("=", 1)[0] for arg in args if arg.startswith("-"))
        if flag not in help_flags(capsys, script, args)
    ]

    assert len(commands) > 10, "the doc scan found too few commands"
    assert unknown == []


def test_every_exit_code_has_a_test_that_triggers_it() -> None:
    # Help and usage probes above trigger 2; the signal probes 130 and 143
    for name, module in (("transcript", transcript), ("youtube_smoke", youtube_smoke)):
        assert DECLARED.get(name, set()) == set(module.EXIT_CODES), name

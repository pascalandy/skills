#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Verify transcript through its public CLI and retain structured evidence."""

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

__version__ = "2.0.0"
CANONICAL_YOUTUBE_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
# Selected by the transcript README's Test videos rule
TEST_PROFILE = "sonnet"
EVIDENCE_NAMESPACE = "eval-transcript"
RUN_MARKER = ".verify-transcript-run"
FEATURE_AREAS = (
    "interface",
    "youtube",
    "zoom",
    "summaries",
    "configuration",
    "diagnostics",
    "dry-runs",
)

Layout = Literal["source", "applied"]
Verdict = Literal["PASS", "FAIL"]
# "json-by-exit" reads stdout on exit 0 and stderr otherwise, as a doctor
# report moves to stderr when a check fails
OutputKind = Literal["stdout-json", "stderr-json", "json-by-exit", "stdout-text"]
SurfaceKind = Literal["command", "option", "behavior"]
ProbeKind = Literal[
    "help-version",
    "structured-recovery",
    "transcript-only-dry-run",
    "prompts",
    "profiles",
    "models",
    "doctor-youtube",
    "doctor-zoom",
    "youtube-dry-run-summary",
    "zoom-dry-run",
    "youtube-real-summary",
]


class CLIArgumentParser(argparse.ArgumentParser):
    """Return structured usage errors when JSON mode is active."""

    json_errors = False

    def error(self, message: str) -> None:
        hint = f"Run '{self.prog} --help' for valid arguments and examples."
        if self.json_errors:
            payload = {
                "ok": False,
                "error": {
                    "code": "invalid_usage",
                    "message": message,
                    "hint": hint,
                },
            }
            self.exit(2, json.dumps(payload, ensure_ascii=False) + "\n")
        self.exit(2, f"Error: {message}\nHint: {hint}\n")


class VerificationError(RuntimeError):
    """Describe an actionable verifier failure before feature execution."""

    def __init__(self, code: str, message: str, hint: str, exit_code: int = 1):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.exit_code = exit_code


@dataclass(frozen=True)
class LocatedSkill:
    directory: Path
    transcript_script: Path
    layout: Layout


@dataclass(frozen=True)
class FeatureSpec:
    id: str
    title: str
    areas: tuple[str, ...]
    default: bool
    probe: ProbeKind
    timeout_seconds: int = 30

    @property
    def paid(self) -> bool:
        return self.probe == "youtube-real-summary"


@dataclass(frozen=True)
class OutputExpectation:
    kind: OutputKind
    exit_codes: tuple[int, ...]


@dataclass(frozen=True)
class CommandPlan:
    id: str
    args: tuple[str, ...]
    output_dir: Path | None = None
    expectation: OutputExpectation = OutputExpectation("stdout-json", (0,))


@dataclass(frozen=True)
class PublicSurface:
    id: str
    kind: SurfaceKind
    token: str | None = None
    owners: tuple[str, ...] = ()
    exclusion_reason: str | None = None


@dataclass(frozen=True)
class HelpContract:
    id: str
    args: tuple[str, ...]
    choices: frozenset[str]
    options: frozenset[str]


@dataclass(frozen=True)
class CapturedProcess:
    argv: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


@dataclass(frozen=True)
class RunContext:
    run_id: str
    located: LocatedSkill
    scratch_dir: Path
    evidence_dir: Path
    allow_paid: bool
    youtube_url: str


# Options every transcript command accepts, before or after its name
GLOBAL_OPTIONS = frozenset(
    {"--help", "--verbose", "--debug", "--json", "--no-color", "--no-progress"}
)

RUN_OPTIONS = GLOBAL_OPTIONS | {
    "--dry-run",
    "--effort",
    "--model",
    "--no-summary",
    "--open",
    "--output-dir",
    "--preview",
    "--profile",
    "--prompt",
    "--provider",
    "--timeout",
}

HELP_CONTRACTS = (
    HelpContract(
        "root-help",
        ("--help",),
        frozenset({"run", "list", "doctor", "help"}),
        GLOBAL_OPTIONS | {"--version"},
    ),
    HelpContract(
        "run-help",
        ("run", "--help"),
        frozenset({"youtube", "zoom"}),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "youtube-help",
        ("run", "youtube", "--help"),
        frozenset(),
        RUN_OPTIONS | {"--url"},
    ),
    HelpContract(
        "zoom-help",
        ("run", "zoom", "--help"),
        frozenset(),
        RUN_OPTIONS | {"--latest", "--path"},
    ),
    HelpContract(
        "list-help",
        ("list", "--help"),
        frozenset({"profiles", "prompts", "models"}),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "prompts-help",
        ("list", "prompts", "--help"),
        frozenset(),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "profiles-help",
        ("list", "profiles", "--help"),
        frozenset(),
        GLOBAL_OPTIONS,
    ),
    HelpContract(
        "models-help",
        ("list", "models", "--help"),
        frozenset(),
        GLOBAL_OPTIONS | {"--provider"},
    ),
    HelpContract(
        "doctor-help",
        ("doctor", "--help"),
        frozenset(),
        GLOBAL_OPTIONS | {"--no-summary", "--source"},
    ),
    HelpContract(
        "help-help",
        ("help", "--help"),
        frozenset(),
        GLOBAL_OPTIONS,
    ),
)

PUBLIC_SURFACES = (
    PublicSurface(
        "command.run",
        "command",
        "run",
        ("youtube.dry-run-summary", "zoom.dry-run"),
    ),
    PublicSurface(
        "command.list",
        "command",
        "list",
        (
            "configuration.profiles",
            "configuration.prompts",
            "configuration.models",
        ),
    ),
    PublicSurface(
        "command.doctor",
        "command",
        "doctor",
        ("diagnostics.youtube", "diagnostics.zoom"),
    ),
    PublicSurface(
        "command.youtube",
        "command",
        "youtube",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface("command.zoom", "command", "zoom", ("zoom.dry-run",)),
    PublicSurface(
        "command.prompts",
        "command",
        "prompts",
        ("configuration.prompts",),
    ),
    PublicSurface(
        "command.profiles",
        "command",
        "profiles",
        ("configuration.profiles",),
    ),
    PublicSurface(
        "command.models",
        "command",
        "models",
        ("configuration.models",),
    ),
    PublicSurface("command.help", "command", "help", ("interface.help-version",)),
    PublicSurface("option.help", "option", "--help", ("interface.help-version",)),
    PublicSurface("option.version", "option", "--version", ("interface.help-version",)),
    PublicSurface("option.url", "option", "--url", ("youtube.dry-run-summary",)),
    PublicSurface(
        "option.latest",
        "option",
        "--latest",
        exclusion_reason="Requires reading the user's private Zoom directory",
    ),
    PublicSurface("option.path", "option", "--path", ("zoom.dry-run",)),
    PublicSurface(
        "option.source",
        "option",
        "--source",
        ("diagnostics.youtube", "diagnostics.zoom"),
    ),
    PublicSurface(
        "option.no-summary",
        "option",
        "--no-summary",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.profile",
        "option",
        "--profile",
        ("youtube.dry-run-summary", "zoom.dry-run", "youtube.real-summary"),
    ),
    PublicSurface(
        "option.provider",
        "option",
        "--provider",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.prompt",
        "option",
        "--prompt",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.model",
        "option",
        "--model",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.effort",
        "option",
        "--effort",
        ("youtube.dry-run-summary",),
    ),
    PublicSurface(
        "option.output-dir",
        "option",
        "--output-dir",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.dry-run",
        "option",
        "--dry-run",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface("option.json", "option", "--json", ("dry-runs.transcript-only",)),
    PublicSurface(
        "option.timeout",
        "option",
        "--timeout",
        ("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "option.open", "option", "--open", exclusion_reason="Would open Finder"
    ),
    PublicSurface(
        "option.preview",
        "option",
        "--preview",
        exclusion_reason="Would render an interactive preview",
    ),
    PublicSurface(
        "option.debug",
        "option",
        "--debug",
        exclusion_reason=(
            "Only adds internals, timings, and tracebacks on stderr; "
            "transcript contract tests compare every verbosity level"
        ),
    ),
    PublicSurface(
        "option.verbose",
        "option",
        "--verbose",
        exclusion_reason=(
            "Only adds progress lines on stderr; "
            "transcript contract tests compare every verbosity level"
        ),
    ),
    PublicSurface(
        "option.no-color",
        "option",
        "--no-color",
        exclusion_reason=(
            "Only changes terminal rendering; "
            "transcript contract tests drive it on a pseudo-terminal"
        ),
    ),
    PublicSurface(
        "option.no-progress",
        "option",
        "--no-progress",
        exclusion_reason=(
            "Only hides the terminal spinner; "
            "transcript contract tests drive it on a pseudo-terminal"
        ),
    ),
    PublicSurface(
        "stream.text-stdout",
        "behavior",
        owners=("interface.help-version",),
    ),
    PublicSurface(
        "stream.success-json-stdout",
        "behavior",
        owners=("dry-runs.transcript-only",),
    ),
    PublicSurface(
        "stream.invalid-json-stderr",
        "behavior",
        owners=("interface.structured-recovery",),
    ),
    PublicSurface(
        "stream.runtime-json-stderr",
        "behavior",
        exclusion_reason=(
            "Runtime JSON failures require injected external failures and are covered by unit tests"
        ),
    ),
    PublicSurface("exit.success", "behavior", owners=("interface.help-version",)),
    PublicSurface(
        "exit.runtime-failure",
        "behavior",
        exclusion_reason=(
            "Runtime exit paths require injected external failures and are covered by unit tests"
        ),
    ),
    PublicSurface(
        "exit.invalid-input",
        "behavior",
        owners=("interface.structured-recovery",),
    ),
    PublicSurface(
        "exit.interrupted",
        "behavior",
        exclusion_reason="Requires sending a process signal and is covered by unit tests",
    ),
    PublicSurface(
        "exit.temporary",
        "behavior",
        exclusion_reason=(
            "Requires an injected network failure and is covered by unit tests"
        ),
    ),
    PublicSurface(
        "publication.summary-success",
        "behavior",
        owners=("youtube.real-summary",),
    ),
    PublicSurface(
        "transcription.upload-completion",
        "behavior",
        owners=("youtube.real-summary",),
    ),
    PublicSurface(
        "transcription.upload-timeouts",
        "behavior",
        exclusion_reason=(
            "Slow and interrupted uploads are covered by transcript "
            "TestDeepgramContract tests without paid calls"
        ),
    ),
    PublicSurface(
        "publication.transcript-only",
        "behavior",
        exclusion_reason="Requires a paid Deepgram call and is covered by unit tests",
    ),
    PublicSurface(
        "publication.summary-failure",
        "behavior",
        exclusion_reason="Requires a forced provider failure and is covered by unit tests",
    ),
    PublicSurface(
        "publication.transaction-and-collisions",
        "behavior",
        exclusion_reason="Covered by deterministic unit tests without paid work",
    ),
)


FEATURES = (
    FeatureSpec(
        id="interface.help-version",
        title="CLI help and version",
        areas=("interface",),
        default=True,
        probe="help-version",
    ),
    FeatureSpec(
        id="interface.structured-recovery",
        title="Structured CLI recovery",
        areas=("interface", "configuration", "youtube"),
        default=True,
        probe="structured-recovery",
    ),
    FeatureSpec(
        id="dry-runs.transcript-only",
        title="Transcript-only plans",
        areas=("dry-runs", "configuration", "summaries", "youtube", "zoom"),
        default=True,
        probe="transcript-only-dry-run",
    ),
    FeatureSpec(
        id="configuration.prompts",
        title="Bundled prompt discovery",
        areas=("configuration", "summaries"),
        default=True,
        probe="prompts",
    ),
    FeatureSpec(
        id="configuration.profiles",
        title="Inference profile discovery",
        areas=("configuration", "summaries"),
        default=True,
        probe="profiles",
    ),
    FeatureSpec(
        id="configuration.models",
        title="Summary model discovery",
        areas=("configuration", "summaries"),
        default=True,
        probe="models",
    ),
    FeatureSpec(
        id="diagnostics.youtube",
        title="YouTube diagnostics",
        areas=("diagnostics", "youtube"),
        default=True,
        probe="doctor-youtube",
    ),
    FeatureSpec(
        id="diagnostics.zoom",
        title="Zoom diagnostics",
        areas=("diagnostics", "zoom"),
        default=True,
        probe="doctor-zoom",
    ),
    FeatureSpec(
        id="youtube.dry-run-summary",
        title="YouTube summary plan",
        areas=("youtube", "summaries", "configuration", "dry-runs"),
        default=True,
        probe="youtube-dry-run-summary",
    ),
    FeatureSpec(
        id="zoom.dry-run",
        title="Zoom source plan",
        areas=("zoom", "summaries", "configuration", "dry-runs"),
        default=True,
        probe="zoom-dry-run",
    ),
    FeatureSpec(
        id="youtube.real-summary",
        title="Real YouTube transcription and summary",
        areas=("youtube", "summaries"),
        default=False,
        probe="youtube-real-summary",
        timeout_seconds=620,
    ),
)


def verify_skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def locate_transcript_skill(skill_dir: Path) -> LocatedSkill:
    """Locate the transcript skill in categorized source or flat applied layouts."""
    candidates: tuple[tuple[Layout, Path], ...] = (
        ("source", skill_dir.parent.parent / "andy" / "transcript"),
        ("applied", skill_dir.parent / "transcript"),
    )
    attempted = []
    for layout, candidate in candidates:
        resolved = candidate.resolve()
        attempted.append(str(resolved))
        script = resolved / "scripts" / "transcript.py"
        if (resolved / "SKILL.md").is_file() and script.is_file():
            return LocatedSkill(resolved, script, layout)
    raise VerificationError(
        "transcript_skill_not_found",
        "Could not locate the transcript skill beside verify-transcript.",
        "Expected a categorized source or flat applied layout. Checked: "
        + ", ".join(attempted),
    )


def select_features(
    requested: tuple[str, ...], select_all: bool, allow_paid: bool
) -> tuple[FeatureSpec, ...]:
    """Resolve feature selection and reject paid work without dual intent."""
    by_id = {feature.id: feature for feature in FEATURES}
    if select_all and requested:
        raise VerificationError(
            "invalid_selection",
            "--all cannot be combined with --feature.",
            "Use --all or repeat --feature with exact feature IDs.",
            exit_code=2,
        )
    unknown = sorted(set(requested) - by_id.keys())
    if unknown:
        raise VerificationError(
            "unknown_feature",
            "Unknown feature ID: " + ", ".join(unknown),
            "Run 'verify-transcript features --json' and use one of features[].id.",
            exit_code=2,
        )
    if select_all:
        selected = FEATURES
    elif requested:
        selected = tuple(by_id[feature_id] for feature_id in dict.fromkeys(requested))
    else:
        selected = tuple(feature for feature in FEATURES if feature.default)
    paid = [feature.id for feature in selected if feature.paid]
    if paid and not allow_paid:
        raise VerificationError(
            "paid_intent_required",
            "Paid feature selection requires --allow-paid: " + ", ".join(paid),
            "Follow the transcript README's Test videos rule, then repeat with --allow-paid.",
            exit_code=2,
        )
    return selected


def _slug(feature_id: str) -> str:
    return feature_id.replace(".", "-")


def _zoom_fixture(context: RunContext) -> Path:
    meeting = context.scratch_dir / "input" / "zoom-meeting"
    meeting.mkdir(parents=True, exist_ok=True)
    (meeting / "audio_only.m4a").touch()
    return meeting


def build_commands(
    feature: FeatureSpec, context: RunContext
) -> tuple[CommandPlan, ...]:
    """Build fixed public commands from the typed feature registry."""
    output_dir = context.scratch_dir / "output" / _slug(feature.id)
    if feature.probe == "help-version":
        text_output = OutputExpectation("stdout-text", (0,))
        return tuple(
            CommandPlan(contract.id, contract.args, expectation=text_output)
            for contract in HELP_CONTRACTS
        ) + (CommandPlan("version", ("--version",), expectation=text_output),)
    if feature.probe == "structured-recovery":
        error_output = OutputExpectation("stderr-json", (2,))
        plans = (
            (
                "invalid-usage",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--unknown-option",
                ),
            ),
            (
                "invalid-source",
                ("run", "youtube", "--url", "https://example.com/video"),
            ),
            (
                "invalid-configuration",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--provider",
                    "codex",
                    "--model",
                    "",
                    "--effort",
                    "low",
                ),
            ),
        )
        return tuple(
            CommandPlan(
                plan_id,
                (
                    *args,
                    "--output-dir",
                    str(output_dir / plan_id),
                    "--dry-run",
                    "--json",
                ),
                output_dir / plan_id,
                error_output,
            )
            for plan_id, args in plans
        )
    if feature.probe == "transcript-only-dry-run":
        youtube_output = output_dir / "youtube"
        zoom_output = output_dir / "zoom"
        return (
            CommandPlan(
                "youtube-transcript-only",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--no-summary",
                    "--output-dir",
                    str(youtube_output),
                    "--timeout",
                    "42",
                    "--dry-run",
                    "--json",
                ),
                youtube_output,
            ),
            CommandPlan(
                "zoom-transcript-only",
                (
                    "run",
                    "zoom",
                    "--path",
                    str(_zoom_fixture(context)),
                    "--no-summary",
                    "--output-dir",
                    str(zoom_output),
                    "--timeout",
                    "43",
                    "--dry-run",
                    "--json",
                ),
                zoom_output,
            ),
        )
    if feature.probe == "prompts":
        return (CommandPlan("prompts", ("list", "prompts", "--json")),)
    if feature.probe == "profiles":
        return (CommandPlan("profiles", ("list", "profiles", "--json")),)
    if feature.probe == "models":
        return (
            CommandPlan(
                "models-claude",
                ("list", "models", "--provider", "claude", "--json"),
            ),
            CommandPlan(
                "models-codex",
                ("list", "models", "--provider", "codex", "--json"),
            ),
            CommandPlan(
                "models-openrouter",
                ("list", "models", "--provider", "openrouter", "--json"),
            ),
        )
    if feature.probe == "doctor-youtube":
        return (
            CommandPlan(
                "doctor-youtube",
                ("doctor", "--source", "youtube", "--json"),
                expectation=OutputExpectation("json-by-exit", (0, 1)),
            ),
        )
    if feature.probe == "doctor-zoom":
        return (
            CommandPlan(
                "doctor-zoom",
                ("doctor", "--source", "zoom", "--json"),
                expectation=OutputExpectation("json-by-exit", (0, 1)),
            ),
        )
    if feature.probe == "youtube-dry-run-summary":
        return (
            CommandPlan(
                "youtube-dry-run-summary",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--profile",
                    "glm",
                    "--prompt",
                    "summary_with_quotes",
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                    "--json",
                ),
                output_dir,
            ),
        )
    if feature.probe == "zoom-dry-run":
        return (
            CommandPlan(
                "zoom-dry-run",
                (
                    "run",
                    "zoom",
                    "--path",
                    str(_zoom_fixture(context)),
                    "--output-dir",
                    str(output_dir),
                    "--dry-run",
                    "--json",
                ),
                output_dir,
            ),
        )
    if feature.probe == "youtube-real-summary":
        return (
            CommandPlan(
                "youtube-real-summary",
                (
                    "run",
                    "youtube",
                    "--url",
                    context.youtube_url,
                    "--profile",
                    TEST_PROFILE,
                    "--prompt",
                    "short_summary",
                    "--output-dir",
                    str(output_dir),
                    "--json",
                ),
                output_dir,
            ),
        )
    raise AssertionError(f"Unhandled probe: {feature.probe}")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def assert_safe_command(
    feature: FeatureSpec, plan: CommandPlan, context: RunContext
) -> None:
    """Recheck payment and output confinement immediately before execution."""
    args = plan.args
    if not args:
        raise VerificationError(
            "unsafe_command",
            f"{feature.id} has an empty transcript command.",
            "Fix the registry before running this feature.",
        )
    forbidden = sorted({"--open", "--preview"}.intersection(args))
    if forbidden:
        raise VerificationError(
            "unsafe_side_effect",
            f"{feature.id} requests a GUI side effect: {', '.join(forbidden)}",
            "Remove GUI flags from verification commands.",
        )
    if plan.expectation.kind == "stdout-text":
        if args != ("--version",) and args[-1] != "--help":
            raise VerificationError(
                "unsafe_command",
                f"{feature.id} requests unrecognized text output.",
                "Text verification is limited to transcript help and version output.",
            )
        return
    if "--json" not in args:
        raise VerificationError(
            "unsafe_command",
            f"{feature.id} does not use transcript's JSON interface.",
            "Fix the registry before running this feature.",
        )
    if args[0] != "run":
        return
    if "--output-dir" not in args or plan.output_dir is None:
        raise VerificationError(
            "unsafe_output",
            f"{feature.id} has no eval-owned output directory.",
            "Every transcript run must set --output-dir under the current scratch root.",
        )
    output_arg = Path(args[args.index("--output-dir") + 1])
    if output_arg.resolve() != plan.output_dir.resolve() or not _is_within(
        output_arg, context.scratch_dir
    ):
        raise VerificationError(
            "unsafe_output",
            f"{feature.id} output escapes the eval scratch root: {output_arg}",
            "Use the output path created by verify-transcript for this run.",
        )
    is_paid_command = "--dry-run" not in args
    if is_paid_command != feature.paid:
        raise VerificationError(
            "invalid_cost_classification",
            f"{feature.id} paid classification does not match its command.",
            "Fix the typed feature registry before running this feature.",
        )
    if is_paid_command and not context.allow_paid:
        raise VerificationError(
            "paid_intent_required",
            f"{feature.id} reached the paid boundary without --allow-paid.",
            "Follow the transcript README's Test videos rule, then repeat with --allow-paid.",
            exit_code=2,
        )


def run_process(
    argv: tuple[str, ...], cwd: Path, timeout_seconds: int
) -> CapturedProcess:
    """Run one process group so timeout and interruption teardown are bounded."""
    started = time.monotonic()
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
    except KeyboardInterrupt:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise
    return CapturedProcess(
        argv=argv,
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=round(time.monotonic() - started, 3),
        timed_out=timed_out,
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def _parse_json_document(content: str, stream: str) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as error:
        raise AssertionError(f"transcript returned invalid JSON on {stream}") from error
    if not isinstance(payload, dict):
        raise TypeError(f"transcript returned non-object JSON on {stream}")
    return payload


def _reported_error(stderr: str) -> str:
    """`: <code>: <message>` from transcript's JSON error on stderr, or nothing."""
    try:
        payload = json.loads(stderr)
    except json.JSONDecodeError:
        return ""
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return ""
    code, message = error.get("code"), error.get("message")
    if not isinstance(code, str) or not isinstance(message, str):
        return ""
    return f": {code}: {message}"


def parse_expected_output(
    process: CapturedProcess, expectation: OutputExpectation
) -> dict[str, object]:
    """Parse only the declared public stream and enforce its exit contract."""
    if process.exit_code not in expectation.exit_codes:
        raise AssertionError(
            f"transcript exited {process.exit_code}; expected {expectation.exit_codes}"
            + _reported_error(process.stderr)
        )
    kind = expectation.kind
    if kind == "json-by-exit":
        kind = "stdout-json" if process.exit_code == 0 else "stderr-json"
    if kind == "stdout-json":
        _require(not process.stderr, "stdout JSON command wrote to stderr")
        _require(bool(process.stdout.strip()), "stdout JSON output is empty")
        return _parse_json_document(process.stdout, "stdout")
    if kind == "stderr-json":
        _require(not process.stdout, "stderr JSON command wrote to stdout")
        _require(bool(process.stderr.strip()), "stderr JSON output is empty")
        return _parse_json_document(process.stderr, "stderr")
    _require(not process.stderr, "text command wrote to stderr")
    _require(bool(process.stdout.strip()), "text output is empty")
    return {"text": process.stdout}


def capture_command(
    feature: FeatureSpec,
    plan: CommandPlan,
    context: RunContext,
) -> tuple[CapturedProcess, dict[str, object]]:
    assert_safe_command(feature, plan, context)
    # --quiet keeps uv's own setup lines, such as "Installed 12 packages", off
    # stderr; a fresh checkout triggers them, and they are not transcript's output
    argv = (
        "uv",
        "run",
        "--quiet",
        str(context.located.transcript_script),
        *plan.args,
    )
    command_dir = context.evidence_dir / "cases" / _slug(feature.id) / plan.id
    _write_json(
        command_dir / "command.json",
        {
            "argv": argv,
            "cwd": str(context.scratch_dir),
            "timeout_seconds": feature.timeout_seconds,
        },
    )
    process = run_process(argv, context.scratch_dir, feature.timeout_seconds)
    command_dir.mkdir(parents=True, exist_ok=True)
    (command_dir / "stdout.txt").write_text(process.stdout, encoding="utf-8")
    (command_dir / "stderr.txt").write_text(process.stderr, encoding="utf-8")
    _write_json(
        command_dir / "process.json",
        {
            "exit_code": process.exit_code,
            "duration_seconds": process.duration_seconds,
            "timed_out": process.timed_out,
        },
    )
    payload = parse_expected_output(process, plan.expectation)
    _write_json(command_dir / "parsed.json", payload)
    return process, payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _validate_doctor(
    feature: FeatureSpec,
    process: CapturedProcess,
    payload: dict[str, object],
) -> dict[str, object]:
    checks = payload.get("checks")
    counts = payload.get("counts")
    _require(payload.get("command") == "doctor", "doctor command field is invalid")
    _require(isinstance(checks, list) and bool(checks), "doctor checks are missing")
    _require(isinstance(counts, dict), "doctor counts are missing")
    check_names = {check.get("name") for check in checks if isinstance(check, dict)}
    if feature.probe == "doctor-youtube":
        expected_source = "youtube"
        expected_summary = True
        expected_checks = {
            "deepgram_credential",
            "claude",
            "pi",
            "ffmpeg",
            "ffprobe",
            "yt_dlp",
            "youtube_browser",
        }
    else:
        expected_source = "zoom"
        expected_summary = True
        expected_checks = {"deepgram_credential", "claude", "pi", "zoom_recordings"}
    _require(payload.get("source") == expected_source, "doctor source is invalid")
    _require(
        payload.get("summary") is expected_summary, "doctor summary mode is invalid"
    )
    _require(expected_checks <= check_names, "doctor source checks are incomplete")
    expected = {
        status: sum(
            isinstance(check, dict) and check.get("status") == status
            for check in checks
        )
        for status in ("pass", "warn", "fail")
    }
    _require(counts == expected, "doctor counts do not match its checks")
    readiness_ok = expected["fail"] == 0
    _require(payload.get("ok") is readiness_ok, "doctor ok disagrees with checks")
    _require(
        process.exit_code == (0 if readiness_ok else 1),
        "doctor exit code disagrees with readiness",
    )
    return {"readiness_ok": readiness_ok, "counts": expected}


def _validate_dry_run(
    feature: FeatureSpec,
    plan: CommandPlan,
    process: CapturedProcess,
    payload: dict[str, object],
) -> dict[str, object]:
    _require(process.exit_code == 0, f"{feature.id} exited {process.exit_code}")
    _require(payload.get("ok") is True, f"{feature.id} did not report ok")
    _require(payload.get("dry_run") is True, f"{feature.id} is not a dry run")
    _require(payload.get("side_effects") == [], f"{feature.id} reports side effects")
    _require(
        payload.get("timeout_seconds") == 570.0,
        f"{feature.id} did not resolve the default timeout",
    )
    _require(plan.output_dir is not None, f"{feature.id} has no planned output")
    _require(
        Path(str(payload.get("output_dir"))).resolve() == plan.output_dir.resolve(),
        f"{feature.id} reported the wrong output directory",
    )
    _require(not plan.output_dir.exists(), f"{feature.id} created its output directory")
    source = payload.get("source")
    summary = payload.get("summary")
    _require(isinstance(source, dict), f"{feature.id} source is missing")
    _require(isinstance(summary, dict), f"{feature.id} summary is missing")
    if feature.probe == "youtube-dry-run-summary":
        _require(source.get("kind") == "youtube", "YouTube dry-run source is invalid")
        expected_url = plan.args[plan.args.index("--url") + 1]
        _require(source.get("url") == expected_url, "YouTube dry-run URL is invalid")
        _require(summary.get("enabled") is True, "summary plan is disabled")
        _require(summary.get("profile") == "glm", "summary profile is invalid")
        _require(summary.get("provider") == "openrouter", "summary provider is invalid")
        _require(
            summary.get("model") == "z-ai/glm-5.3-flash",
            "summary model is invalid",
        )
        _require(summary.get("effort") == "medium", "summary effort is invalid")
        _require(
            summary.get("prompt") == "summary_with_quotes",
            "summary prompt is invalid",
        )
    else:
        _require(source.get("kind") == "zoom", "Zoom dry-run source is invalid")
        expected_meeting = Path(plan.args[plan.args.index("--path") + 1]).resolve()
        _require(
            Path(str(source.get("path"))).resolve() == expected_meeting,
            "Zoom dry-run folder is invalid",
        )
        _require(
            Path(str(source.get("audio"))).resolve()
            == expected_meeting / "audio_only.m4a",
            "Zoom dry-run audio is invalid",
        )
        _require(summary.get("enabled") is True, "Zoom summary plan is disabled")
        _require(summary.get("profile") == "opus", "Zoom summary profile is invalid")
        _require(
            summary.get("provider") == "claude", "Zoom summary provider is invalid"
        )
        _require(
            summary.get("model") == "claude-opus-5-5", "Zoom summary model is invalid"
        )
        _require(summary.get("effort") == "high", "Zoom summary effort is invalid")
        _require(
            summary.get("prompt") == "synthese-rencontre",
            "Zoom summary prompt is invalid",
        )
    return {"source": source, "summary": summary, "side_effects": []}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_e2e(
    feature: FeatureSpec,
    plan: CommandPlan,
    process: CapturedProcess,
    payload: dict[str, object],
    context: RunContext,
) -> dict[str, object]:
    _require(process.exit_code == 0, f"{feature.id} exited {process.exit_code}")
    _require(payload.get("ok") is True, "real run did not report success")
    _require(payload.get("source") == "youtube", "real run source is not YouTube")
    summary = payload.get("summary")
    artifacts = payload.get("artifacts")
    _require(isinstance(summary, dict), "real run summary state is missing")
    _require(summary.get("status") == "succeeded", "real summary did not succeed")
    _require(
        summary.get("profile") == TEST_PROFILE,
        f"real summary did not use the {TEST_PROFILE} test profile",
    )
    _require(isinstance(artifacts, dict), "real run artifacts are missing")
    required = {"transcript", "sentences", "json", "metadata", "summary"}
    _require(required <= artifacts.keys(), "real run artifact set is incomplete")
    _require(plan.output_dir is not None, "real run has no isolated output root")
    published_dir = Path(str(payload.get("output_dir"))).resolve()
    _require(
        _is_within(published_dir, plan.output_dir), "published output escaped isolation"
    )
    manifest: dict[str, object] = {}
    for kind in sorted(required):
        artifact = Path(str(artifacts[kind])).resolve()
        _require(
            _is_within(artifact, published_dir), f"{kind} escaped published output"
        )
        _require(artifact.is_file(), f"{kind} artifact does not exist")
        size = artifact.stat().st_size
        _require(size > 0, f"{kind} artifact is empty")
        manifest[kind] = {
            "name": artifact.name,
            "bytes": size,
            "sha256": _sha256(artifact),
        }
    transcript_json = json.loads(
        Path(str(artifacts["json"])).read_text(encoding="utf-8")
    )
    _require(
        isinstance(transcript_json, list) and bool(transcript_json),
        "raw transcript JSON is not a non-empty paragraph list",
    )
    metadata = Path(str(artifacts["metadata"])).read_text(encoding="utf-8")
    _require(
        "Summary status: succeeded" in metadata, "metadata summary status is invalid"
    )
    upload = re.search(
        r"^Audio upload: complete \(([1-9]\d*) bytes\)$", metadata, re.MULTILINE
    )
    _require(upload is not None, "metadata does not confirm a complete audio upload")
    audio_upload = {"status": "complete", "bytes": int(upload.group(1))}
    manifest_path = (
        context.evidence_dir / "cases" / _slug(feature.id) / "artifacts.json"
    )
    _write_json(
        manifest_path,
        {
            "published_dir_name": published_dir.name,
            "artifacts": manifest,
            "raw_transcript_items": len(transcript_json),
            "summary_status": "succeeded",
            "audio_upload": audio_upload,
        },
    )
    return {
        "artifact_manifest": str(manifest_path),
        "artifact_count": len(manifest),
        "raw_transcript_items": len(transcript_json),
        "summary_status": "succeeded",
        "audio_upload": audio_upload,
    }


def _help_section(text: str, heading: str) -> str:
    marker = f"{heading}:\n"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("\n\n", 1)[0]


def _help_options(text: str) -> frozenset[str]:
    declarations = re.split(r"\n[Ee]xamples:\n", text, maxsplit=1)[0]
    return frozenset(
        re.findall(
            r"^  (?:-[A-Za-z], )?(--[a-z][a-z-]*)",
            declarations,
            flags=re.MULTILINE,
        )
    )


def _help_choices(text: str) -> frozenset[str]:
    positional = _help_section(text, "positional arguments")
    return frozenset(
        re.findall(r"^    ([a-z][a-z-]*)\s{2,}\S", positional, flags=re.MULTILINE)
    )


def _validate_help_version(
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
) -> dict[str, object]:
    contracts = {contract.id: contract for contract in HELP_CONTRACTS}
    observed = {}
    version = None
    for plan, (process, payload) in zip(commands, captures, strict=True):
        text = payload.get("text")
        _require(isinstance(text, str), f"{plan.id} returned no text")
        if plan.id == "version":
            _require(
                re.fullmatch(r"transcript \d+\.\d+\.\d+\n", text) is not None,
                "transcript version output is invalid",
            )
            version = text.strip().split()[-1]
            continue
        contract = contracts[plan.id]
        options = _help_options(text)
        choices = _help_choices(text)
        _require(
            options == contract.options,
            f"{plan.id} options changed: {sorted(options)}",
        )
        _require(
            choices == contract.choices,
            f"{plan.id} choices changed: {sorted(choices)}",
        )
        _require(process.exit_code == 0, f"{plan.id} did not exit successfully")
        observed[plan.id] = {
            "options": sorted(options),
            "choices": sorted(choices),
        }
    _require(version is not None, "transcript version was not observed")
    return {"version": version, "help": observed}


def _validate_structured_recovery(
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
) -> dict[str, object]:
    expected_codes = {
        "invalid-usage": "invalid_usage",
        "invalid-source": "invalid_source",
        "invalid-configuration": "invalid_configuration",
    }
    observations = {}
    for plan, (_process, payload) in zip(commands, captures, strict=True):
        _require(payload.get("ok") is False, f"{plan.id} did not report failure")
        error = payload.get("error")
        _require(isinstance(error, dict), f"{plan.id} returned no error object")
        _require(
            error.get("code") == expected_codes[plan.id],
            f"{plan.id} returned the wrong error code",
        )
        _require(bool(error.get("message")), f"{plan.id} returned no message")
        _require(bool(error.get("hint")), f"{plan.id} returned no hint")
        if plan.id == "invalid-configuration":
            message = str(error["message"])
            _require(
                "transcript list models --provider codex" in message,
                "model recovery does not name the current discovery command",
            )
            _require(
                "--list-models" not in message, "model recovery uses legacy syntax"
            )
        _require(
            plan.output_dir is not None and not plan.output_dir.exists(),
            f"{plan.id} created its output directory",
        )
        observations[plan.id] = {"code": error["code"], "hint": error["hint"]}
    return {"errors": observations}


def _validate_transcript_only(
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
) -> dict[str, object]:
    plans = {}
    for plan, (_process, payload) in zip(commands, captures, strict=True):
        _require(payload.get("ok") is True, f"{plan.id} did not report success")
        _require(payload.get("dry_run") is True, f"{plan.id} is not a dry run")
        _require(payload.get("side_effects") == [], f"{plan.id} reports side effects")
        _require(plan.output_dir is not None, f"{plan.id} has no isolated output")
        _require(
            Path(str(payload.get("output_dir"))).resolve() == plan.output_dir.resolve(),
            f"{plan.id} reported the wrong output directory",
        )
        _require(
            not plan.output_dir.exists(), f"{plan.id} created its output directory"
        )
        summary = payload.get("summary")
        _require(
            summary
            == {
                "enabled": False,
                "profile": None,
                "provider": None,
                "model": None,
                "effort": None,
                "prompt": None,
            },
            f"{plan.id} did not disable summary settings",
        )
        source = payload.get("source")
        _require(isinstance(source, dict), f"{plan.id} returned no source")
        if plan.id == "youtube-transcript-only":
            _require(source.get("kind") == "youtube", "YouTube source is invalid")
            expected_timeout = 42.0
        else:
            _require(source.get("kind") == "zoom", "Zoom source is invalid")
            meeting = Path(plan.args[plan.args.index("--path") + 1]).resolve()
            _require(
                Path(str(source.get("path"))).resolve() == meeting,
                "Zoom folder is invalid",
            )
            _require(
                Path(str(source.get("audio"))).resolve() == meeting / "audio_only.m4a",
                "Zoom audio is invalid",
            )
            expected_timeout = 43.0
        _require(
            payload.get("timeout_seconds") == expected_timeout,
            f"{plan.id} did not resolve its timeout override",
        )
        plans[plan.id] = {
            "source": source,
            "summary": summary,
            "timeout_seconds": expected_timeout,
        }
    return {"plans": plans, "side_effects": []}


def validate_feature(
    feature: FeatureSpec,
    commands: tuple[CommandPlan, ...],
    captures: tuple[tuple[CapturedProcess, dict[str, object]], ...],
    context: RunContext,
) -> dict[str, object]:
    """Validate one public behavior after all of its commands are captured."""
    if feature.probe == "help-version":
        return _validate_help_version(commands, captures)
    if feature.probe == "structured-recovery":
        return _validate_structured_recovery(commands, captures)
    if feature.probe == "transcript-only-dry-run":
        return _validate_transcript_only(commands, captures)
    if feature.probe == "prompts":
        process, payload = captures[0]
        prompts = payload.get("prompts")
        _require(process.exit_code == 0, "prompt discovery failed")
        _require(isinstance(prompts, list), "prompt discovery returned no list")
        discovered = {
            prompt.get("name"): prompt.get("input_kind")
            for prompt in prompts
            if isinstance(prompt, dict)
        }
        expected = {
            "follow_along_note": "plain",
            "short_summary": "plain",
            "summary_with_quotes": "timestamped",
        }
        _require(
            all(
                discovered.get(name) == input_kind
                for name, input_kind in expected.items()
            ),
            "prompt discovery is missing a bundled prompt or input kind",
        )
        return {"prompts": expected}
    if feature.probe == "models":
        providers = []
        for process, payload in captures:
            _require(process.exit_code == 0, "model discovery failed")
            provider = payload.get("provider")
            models = payload.get("models")
            _require(
                provider in {"claude", "codex", "openrouter"},
                "model provider is invalid",
            )
            _require(isinstance(models, list) and bool(models), "model list is empty")
            _require(payload.get("default") in models, "default model is not suggested")
            providers.append(provider)
        _require(
            set(providers) == {"claude", "codex", "openrouter"},
            "provider coverage is incomplete",
        )
        return {"providers": sorted(providers)}
    if feature.probe == "profiles":
        process, payload = captures[0]
        _require(process.exit_code == 0, "profile discovery failed")
        _require(payload.get("default") == "opus", "default profile is invalid")
        profiles = payload.get("profiles")
        _require(isinstance(profiles, list) and bool(profiles), "profile list is empty")
        for profile in profiles:
            _require(
                isinstance(profile, dict)
                and all(
                    isinstance(profile.get(key), str) and bool(profile[key].strip())
                    for key in ("name", "provider", "model", "effort")
                ),
                f"profile has missing or empty fields: {profile!r}",
            )
        names = [profile["name"] for profile in profiles]
        _require(len(set(names)) == len(names), f"duplicate profile names: {names!r}")
        _require(payload["default"] in names, "default profile is not listed")
        _require(TEST_PROFILE in names, f"test profile is not listed: {TEST_PROFILE}")
        return {"default": payload["default"], "profiles": names}
    if feature.probe in {"doctor-youtube", "doctor-zoom"}:
        return _validate_doctor(feature, *captures[0])
    if feature.probe in {"youtube-dry-run-summary", "zoom-dry-run"}:
        return _validate_dry_run(feature, commands[0], *captures[0])
    if feature.probe == "youtube-real-summary":
        return _validate_e2e(feature, commands[0], *captures[0], context)
    raise AssertionError(f"Unhandled probe: {feature.probe}")


def run_feature(feature: FeatureSpec, context: RunContext) -> dict[str, object]:
    evidence = context.evidence_dir / "cases" / _slug(feature.id)
    try:
        commands = build_commands(feature, context)
        captures = tuple(capture_command(feature, plan, context) for plan in commands)
        observations = validate_feature(feature, commands, captures, context)
    except (
        AssertionError,
        OSError,
        TypeError,
        VerificationError,
        json.JSONDecodeError,
    ) as error:
        result: dict[str, object] = {
            "id": feature.id,
            "title": feature.title,
            "verdict": "FAIL",
            "paid": feature.paid,
            "evidence": str(evidence),
            "error": {
                "code": (
                    error.code
                    if isinstance(error, VerificationError)
                    else "verification_failed"
                ),
                "message": str(error),
            },
        }
    else:
        result = {
            "id": feature.id,
            "title": feature.title,
            "verdict": "PASS",
            "paid": feature.paid,
            "evidence": str(evidence),
            "observations": observations,
        }
    _write_json(evidence / "result.json", result)
    return result


def create_scratch(run_id: str) -> Path:
    scratch = Path(tempfile.mkdtemp(prefix=f"verify-transcript-{run_id}-")).resolve()
    (scratch / RUN_MARKER).write_text(run_id + "\n", encoding="utf-8")
    return scratch


def safe_cleanup(scratch: Path, run_id: str) -> None:
    """Remove only the marked temporary directory created by this run."""
    resolved = scratch.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    marker = resolved / RUN_MARKER
    if not _is_within(resolved, temp_root):
        raise VerificationError(
            "unsafe_cleanup",
            f"Refusing cleanup outside the system temporary directory: {resolved}",
            "Remove the scratch directory manually after checking its contents.",
        )
    if not resolved.name.startswith(f"verify-transcript-{run_id}-"):
        raise VerificationError(
            "unsafe_cleanup",
            f"Refusing cleanup of an unexpected directory name: {resolved.name}",
            "Remove the scratch directory manually after checking its contents.",
        )
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != run_id:
        raise VerificationError(
            "unsafe_cleanup",
            f"Refusing cleanup without the current run marker: {resolved}",
            "Remove the scratch directory manually after checking its contents.",
        )
    shutil.rmtree(resolved)


def default_evidence_root() -> Path:
    state_home = Path(os.getenv("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_home / EVIDENCE_NAMESPACE / "runs"


def new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def run_verification(
    selected: tuple[FeatureSpec, ...],
    located: LocatedSkill,
    evidence_root: Path,
    allow_paid: bool,
    youtube_url: str,
) -> dict[str, object]:
    """Run selected features, clean scratch, and retain the final report."""
    run_id = new_run_id()
    evidence_dir = evidence_root.expanduser().resolve() / run_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    scratch = create_scratch(run_id)
    context = RunContext(
        run_id=run_id,
        located=located,
        scratch_dir=scratch,
        evidence_dir=evidence_dir,
        allow_paid=allow_paid,
        youtube_url=youtube_url,
    )
    results: list[dict[str, object]] = []
    cleanup_error: VerificationError | None = None
    try:
        for feature in selected:
            results.append(run_feature(feature, context))
    finally:
        try:
            safe_cleanup(scratch, run_id)
        except VerificationError as error:
            cleanup_error = error
    passed = sum(result["verdict"] == "PASS" for result in results)
    failed = len(results) - passed
    if cleanup_error is not None:
        failed += 1
    ok = failed == 0
    report: dict[str, object] = {
        "schema_version": 1,
        "ok": ok,
        "verdict": "PASS" if ok else "FAIL",
        "run_id": run_id,
        "layout": located.layout,
        "transcript_skill_dir": str(located.directory),
        "paid_authorized": allow_paid,
        "evidence_dir": str(evidence_dir),
        "counts": {"passed": passed, "failed": failed},
        "scratch_removed": not scratch.exists(),
        "features": results,
    }
    if cleanup_error is not None:
        report["cleanup_error"] = {
            "code": cleanup_error.code,
            "message": cleanup_error.message,
            "hint": cleanup_error.hint,
        }
    _write_json(evidence_dir / "result.json", report)
    return report


def feature_documents(skill_dir: Path, query: str | None) -> list[dict[str, str]]:
    """Search the checked-in Feature Map by filename, title, or body text."""
    normalized = query.casefold() if query else None
    documents = []
    for path in sorted((skill_dir / "features").glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        haystack = f"{path.stem}\n{text}".casefold()
        if normalized and normalized not in haystack:
            continue
        lines = text.splitlines()
        title = next((line[2:] for line in lines if line.startswith("# ")), path.stem)
        summary = next(
            (
                line
                for line in lines[1:]
                if line and not line.startswith("#") and not line.startswith("<!--")
            ),
            "",
        )
        documents.append(
            {
                "id": path.stem,
                "title": title,
                "summary": summary,
                "path": str(Path("features") / path.name),
            }
        )
    return documents


def feature_entries(skill_dir: Path, query: str | None) -> list[dict[str, object]]:
    """Return exact selectable feature IDs with their Feature Map pages."""
    normalized = query.casefold() if query else None
    entries = []
    for feature in FEATURES:
        page_paths = [Path("features") / f"{area}.md" for area in feature.areas]
        missing = [
            page_path
            for page_path in page_paths
            if not (skill_dir / page_path).is_file()
        ]
        if missing:
            raise OSError("Missing Feature Map pages: " + ", ".join(map(str, missing)))
        haystack = "\n".join((feature.id, feature.title, *feature.areas)).casefold()
        if normalized and normalized not in haystack:
            continue
        paid_flag = " --allow-paid" if feature.paid else ""
        entries.append(
            {
                "id": feature.id,
                "title": feature.title,
                "default": feature.default,
                "paid": feature.paid,
                "areas": list(feature.areas),
                "pages": [str(page_path) for page_path in page_paths],
                "verify_command": (
                    f"verify-transcript verify --feature {feature.id}{paid_flag} --json"
                ),
            }
        )
    if normalized and not entries:
        documents = feature_documents(skill_dir, None)
        matching_areas = {
            document["id"]
            for document in documents
            if normalized
            in "\n".join(
                (document["id"], document["title"], document["summary"])
            ).casefold()
        }
        if not matching_areas:
            matching_areas = {
                document["id"] for document in feature_documents(skill_dir, query)
            }
        matching_ids = {
            feature.id
            for feature in FEATURES
            if matching_areas.intersection(feature.areas)
        }
        return [
            entry
            for entry in feature_entries(skill_dir, None)
            if entry["id"] in matching_ids
        ]
    return entries


def doctor_report(skill_dir: Path) -> dict[str, object]:
    checks = []
    try:
        located = locate_transcript_skill(skill_dir)
    except VerificationError as error:
        checks.append(
            {"name": "transcript_skill", "status": "fail", "message": error.message}
        )
        located = None
    else:
        checks.append(
            {
                "name": "transcript_skill",
                "status": "pass",
                "message": f"Found {located.layout} layout at {located.directory}",
            }
        )
    uv_path = shutil.which("uv")
    checks.append(
        {
            "name": "uv",
            "status": "pass" if uv_path else "fail",
            "message": f"uv is available at {uv_path}"
            if uv_path
            else "uv is not on PATH",
        }
    )
    feature_dir = skill_dir / "features"
    missing = [
        area for area in FEATURE_AREAS if not (feature_dir / f"{area}.md").is_file()
    ]
    checks.append(
        {
            "name": "feature_map",
            "status": "pass" if not missing else "fail",
            "message": (
                f"All {len(FEATURE_AREAS)} feature pages are available"
                if not missing
                else "Missing feature pages: " + ", ".join(missing)
            ),
        }
    )
    failures = sum(check["status"] == "fail" for check in checks)
    return {
        "ok": failures == 0,
        "command": "doctor",
        "checks": checks,
        "counts": {"pass": len(checks) - failures, "fail": failures},
    }


def build_parser(*, json_errors: bool = False) -> CLIArgumentParser:
    CLIArgumentParser.json_errors = json_errors
    parser = CLIArgumentParser(
        prog="verify-transcript",
        description="Verify transcript through its public CLI and retain evidence.",
        epilog="""Examples:
  verify-transcript verify --json
  verify-transcript features zoom --json
  verify-transcript verify --feature youtube.real-summary --allow-paid --json
""",
    )
    parser.add_argument(
        "--version", action="version", version=f"verify-transcript {__version__}"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Check that this verifier can run")
    doctor.add_argument("--json", action="store_true", help="Write one JSON document")

    features = commands.add_parser("features", help="Search the transcript Feature Map")
    features.add_argument("query", nargs="?", help="Case-insensitive search text")
    features.add_argument("--json", action="store_true", help="Write one JSON document")

    verify = commands.add_parser("verify", help="Run public-interface verification")
    verify.add_argument("--feature", action="append", default=[], metavar="ID")
    verify.add_argument(
        "--all", action="store_true", help="Select free and paid features"
    )
    verify.add_argument(
        "--allow-paid",
        action="store_true",
        help="Authorize paid calls already selected with --feature or --all",
    )
    verify.add_argument(
        "--youtube-url",
        default=CANONICAL_YOUTUBE_URL,
        metavar="URL",
        help="Override the canonical URL for the selected real YouTube feature",
    )
    verify.add_argument(
        "--evidence-root",
        type=Path,
        default=default_evidence_root(),
        metavar="DIR",
        help="Parent for retained per-run evidence",
    )
    verify.add_argument("--json", action="store_true", help="Write one JSON document")
    return parser


def _print_json(payload: object, *, stream: object = sys.stdout) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), file=stream)


def _emit_error(error: VerificationError, json_mode: bool) -> None:
    if json_mode:
        _print_json(
            {
                "ok": False,
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "hint": error.hint,
                },
            },
            stream=sys.stderr,
        )
    else:
        print(
            f"Error {error.code}: {error.message}\nHint: {error.hint}", file=sys.stderr
        )


def main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv
    if not raw_argv:
        raw_argv = ["--help"]
    json_mode = "--json" in raw_argv
    args = build_parser(json_errors=json_mode).parse_args(raw_argv)
    skill_dir = verify_skill_dir()
    try:
        if args.command == "doctor":
            report = doctor_report(skill_dir)
            if args.json:
                _print_json(report)
            else:
                print("PASS" if report["ok"] else "FAIL")
                for check in report["checks"]:
                    print(
                        f"{check['status'].upper()} {check['name']}: {check['message']}"
                    )
            return 0 if report["ok"] else 1
        if args.command == "features":
            entries = feature_entries(skill_dir, args.query)
            documents = feature_documents(skill_dir, args.query)
            report = {
                "ok": bool(entries or documents) or args.query is None,
                "command": "features",
                "query": args.query,
                "features": entries,
                "documents": documents,
            }
            if args.json:
                _print_json(report)
            else:
                for entry in entries:
                    print(
                        f"{entry['id']}\t{entry['title']}\t"
                        f"paid={str(entry['paid']).lower()}"
                    )
            return 0 if report["ok"] else 1
        requested = tuple(args.feature)
        selected = select_features(requested, args.all, args.allow_paid)
        paid_selected = any(feature.paid for feature in selected)
        if args.youtube_url != CANONICAL_YOUTUBE_URL and not paid_selected:
            raise VerificationError(
                "unused_option",
                "--youtube-url only applies to a selected paid YouTube feature.",
                "Select youtube.real-summary and add --allow-paid, or omit --youtube-url.",
                exit_code=2,
            )
        located = locate_transcript_skill(skill_dir)
        report = run_verification(
            selected=selected,
            located=located,
            evidence_root=args.evidence_root,
            allow_paid=args.allow_paid,
            youtube_url=args.youtube_url,
        )
        if args.json:
            _print_json(report)
        else:
            print(f"{report['verdict']} {report['evidence_dir']}")
        return 0 if report["ok"] else 1
    except VerificationError as error:
        _emit_error(error, json_mode)
        return error.exit_code
    except KeyboardInterrupt:
        error = VerificationError(
            "interrupted",
            "Verification was interrupted.",
            "Inspect the retained evidence before rerunning paid work.",
            exit_code=130,
        )
        _emit_error(error, json_mode)
        return error.exit_code
    except OSError as error:
        wrapped = VerificationError(
            "runtime_error",
            str(error),
            "Run 'verify-transcript doctor --json' and fix the reported requirement.",
        )
        _emit_error(wrapped, json_mode)
        return wrapped.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich",
#     "tiktoken",
# ]
# ///
"""Distill a local text file through a named prompt using Claude, Codex, or OpenCode.

Reads an input file and a prompt file, runs the prompt against the selected
LLM provider CLI, and writes the distilled output to a timestamped folder
beside the input.

See ``help.md`` for the full user-facing documentation. This script is
intentionally thin: prompt content lives in the sibling ``distill-prompt``
skill, and this tool resolves a named stem to its ``prompt.md`` file.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import NoReturn

import tiktoken
from rich.console import Console

__version__ = "1.0.0"

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
HELP_MD_PATH = SKILL_DIR / "help.md"
PROMPTS_DIR = SKILL_DIR.parent / "distill-prompt" / "references"

PROVIDER_CLAUDE = "claude"
PROVIDER_CODEX = "codex"
PROVIDER_OPENCODE = "opencode"
VALID_PROVIDERS: tuple[str, ...] = (
    PROVIDER_CLAUDE,
    PROVIDER_CODEX,
    PROVIDER_OPENCODE,
)
DEFAULT_PROVIDER = PROVIDER_CLAUDE

VALID_CLAUDE_MODELS: tuple[str, ...] = (
    "claude-opus-4-6",
    "claude-sonnet-4-6",
)
DEFAULT_CLAUDE_MODEL = "claude-opus-4-6"

# Models that default to 'low' effort (faster, cheaper)
SONNET_MODELS: tuple[str, ...] = ("claude-sonnet-4-6",)

VALID_CODEX_MODELS: tuple[str, ...] = ("gpt-5.4",)
DEFAULT_CODEX_MODEL = "gpt-5.4"

VALID_OPENCODE_MODELS: tuple[str, ...] = (
    "1-glm",
    "2-luna",
    "3-sol",
    "4-astra",
    "5-qwen",
)
DEFAULT_OPENCODE_MODEL = "1-glm"

CANONICAL_EFFORTS: tuple[str, ...] = ("low", "medium", "high", "max")
DEFAULT_EFFORT = "high"
DEFAULT_PROMPT = "follow_along_note"

# Canonical -> vendor ETL
EFFORT_ETL: dict[str, dict[str, str]] = {
    PROVIDER_CLAUDE: {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "max": "max",
    },
    PROVIDER_CODEX: {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "max": "xhigh",
    },
}

# Safe input-token limits per provider (input + prompt combined).
CONTEXT_LIMITS: dict[str, int] = {
    PROVIDER_CLAUDE: 600_000,
    PROVIDER_CODEX: 450_000,
    PROVIDER_OPENCODE: 250_000,
}

LLM_CLI_TIMEOUT_SECONDS = 600  # 10 minutes
LLM_MAX_RETRIES = 3

# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERIC_ERROR = 1
EXIT_USAGE = 2
EXIT_INPUT_NOT_FOUND = 3
EXIT_PROMPT_NOT_FOUND = 4
EXIT_PROVIDER_MISSING = 5
EXIT_LLM_FAILED = 6
EXIT_OUTPUT_NOT_WRITABLE = 7

# Overhead tokens for the user-message framing ("Based on this content:\n\n")
USER_MESSAGE_OVERHEAD = "Based on this content:\n\n"

console = Console()
error_console = Console(stderr=True)


# -------------------------------------------------------------------------
# Errors
# -------------------------------------------------------------------------


class DistillError(Exception):
    """Base class for distill-specific failures with an explicit exit code."""

    exit_code: int = EXIT_GENERIC_ERROR

    def __init__(self, message: str, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class InputFileError(DistillError):
    exit_code = EXIT_INPUT_NOT_FOUND


class PromptFileError(DistillError):
    exit_code = EXIT_PROMPT_NOT_FOUND


class ProviderMissingError(DistillError):
    exit_code = EXIT_PROVIDER_MISSING


class LLMCallError(DistillError):
    exit_code = EXIT_LLM_FAILED


class OutputDirError(DistillError):
    exit_code = EXIT_OUTPUT_NOT_WRITABLE


# -------------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedPlan:
    """Fully-resolved inputs ready for execution or dry-run display."""

    input_path: Path
    input_text: str
    input_tokens: int
    prompt_path: Path
    prompt_text: str
    prompt_name: str
    provider: str
    provider_cli_path: Path
    model: str
    effort_canonical: str
    effort_vendor: str
    output_parent: Path
    slug: str
    run_folder_name: str
    run_folder_path: Path
    quiet: bool


# -------------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------------


def retry_request[T](
    func: Callable[[], T],
    *,
    max_attempts: int = LLM_MAX_RETRIES,
    initial_delay: float = 1.0,
    quiet: bool = False,
) -> T:
    """Execute ``func`` with exponential backoff retry logic.

    Args:
        func: Zero-argument callable to execute.
        max_attempts: Maximum number of tries (must be >= 1).
        initial_delay: Seconds to wait before the first retry.
        quiet: Suppress retry progress output.

    Returns:
        The return value of ``func`` on the first successful call.

    Raises:
        Exception: Re-raises the last exception after all attempts are exhausted.
    """
    delay = initial_delay
    for attempt in range(1, max_attempts + 1):
        try:
            if attempt > 1 and not quiet:
                console.print(f"   [yellow]Retry {attempt}/{max_attempts}...[/yellow]")
            return func()
        except Exception:
            if attempt == max_attempts:
                if not quiet:
                    console.print(f"   [red]Failed after {max_attempts} attempts[/red]")
                raise
            if not quiet:
                console.print(f"   [yellow]Failed, retrying in {delay}s...[/yellow]")
            time.sleep(delay)
            delay *= 2

    raise RuntimeError("retry_request called with max_attempts < 1")


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken's cl100k_base encoding.

    This is OpenAI-native. For Claude it is an approximation, typically
    within 5-10% of anthropic's own count.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def ensure_cli_available(command_name: str) -> Path:
    """Return the resolved path to ``command_name``, or raise ProviderMissingError."""
    path = shutil.which(command_name)
    if not path:
        raise ProviderMissingError(
            f"Required CLI '{command_name}' was not found on PATH. "
            f"Install it and try again."
        )
    return Path(path)


def open_folder_in_finder(path: Path) -> None:
    """Open a folder in Finder on macOS; no-op elsewhere."""
    if platform.system() != "Darwin":
        return
    subprocess.run(["open", str(path)], check=False)


# -------------------------------------------------------------------------
# Help rendering (custom --help action)
# -------------------------------------------------------------------------


def render_help_and_exit() -> NoReturn:
    """Render help.md via glow if available, otherwise print plain markdown.

    Exits with EXIT_SUCCESS regardless of glow presence.
    """
    if not HELP_MD_PATH.exists():
        error_console.print(f"[red]help.md not found at {HELP_MD_PATH}[/red]")
        sys.exit(EXIT_GENERIC_ERROR)

    if shutil.which("glow"):
        result = subprocess.run(["glow", str(HELP_MD_PATH)], check=False)
        if result.returncode == 0:
            sys.exit(EXIT_SUCCESS)

    # Plain fallback
    sys.stdout.write(HELP_MD_PATH.read_text(encoding="utf-8"))
    sys.exit(EXIT_SUCCESS)


class _HelpAction(argparse.Action):
    """Custom --help that defers to render_help_and_exit."""

    def __init__(
        self,
        option_strings: list[str],
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        help: str | None = None,
    ) -> None:
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(  # pragma: no cover - thin wrapper
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        render_help_and_exit()


# -------------------------------------------------------------------------
# Argument parsing
# -------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="distill.py",
        description="Distill a local text file through a named prompt.",
        add_help=False,
        usage=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-h",
        "--help",
        action=_HelpAction,
        help="Show full help (rendered via glow) and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"distill {__version__}",
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=str,
        help="Path to the local text file to distill.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        metavar="STEM",
        help=f"Prompt stem from distill-prompt (default: {DEFAULT_PROMPT}).",
    )

    parser.add_argument(
        "--provider",
        choices=VALID_PROVIDERS,
        default=None,
        help=f"LLM provider (default: {DEFAULT_PROVIDER}).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        metavar="MODEL",
        help=(
            f"Model name. Defaults: claude={DEFAULT_CLAUDE_MODEL}, "
            f"codex={DEFAULT_CODEX_MODEL}, opencode={DEFAULT_OPENCODE_MODEL}."
        ),
    )
    parser.add_argument(
        "--effort",
        choices=CANONICAL_EFFORTS,
        default=None,
        help=(f"Reasoning effort. Defaults: {DEFAULT_EFFORT} (low for Sonnet models)."),
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        metavar="DIR",
        help="Parent directory for the timestamped run folder.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the output folder in Finder on macOS.",
    )

    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List available distill prompts and exit.",
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List supported models and exit.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve all inputs and print the plan without calling the LLM.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress output.",
    )

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    args = parser.parse_args(argv)
    provider = args.provider or DEFAULT_PROVIDER

    if provider == PROVIDER_OPENCODE and args.effort is not None:
        parser.error("--effort is not supported with --provider opencode")

    # Validate: if not using a discovery command, input is required
    if not args.list_models and not args.list_prompts and not args.input:
        parser.error(
            "missing positional argument 'input' "
            "(or use --list-prompts / --list-models)"
        )

    return args


# -------------------------------------------------------------------------
# Resolution helpers
# -------------------------------------------------------------------------


def resolve_input_file(raw: str) -> tuple[Path, str]:
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise InputFileError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise InputFileError(f"Input path is not a regular file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InputFileError(
            f"Input file is not valid UTF-8 text: {path} ({exc})"
        ) from exc
    except OSError as exc:
        raise InputFileError(f"Cannot read input file {path}: {exc}") from exc
    return path, text


def normalize_prompt_stem(raw: str) -> str:
    """Normalize a user-facing prompt stem to canonical underscore form."""
    stem = raw.strip().lower()
    stem = stem.removesuffix(".md")
    stem = stem.replace("-", "_")
    return stem


def resolve_prompt(raw: str) -> tuple[Path, str, str]:
    """Resolve a prompt stem to ``distill-prompt/references/<folder>/prompt.md``."""
    prompt_name = normalize_prompt_stem(raw)
    prompt_dir = PROMPTS_DIR / prompt_name.replace("_", "-")
    prompt_path = prompt_dir / "prompt.md"

    if not prompt_path.exists() or not prompt_path.is_file():
        raise PromptFileError(
            f"Unknown prompt stem: {raw}. Run with --list-prompts to see the list."
        )

    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise PromptFileError(f"Cannot read prompt file {prompt_path}: {exc}") from exc

    return prompt_path, prompt_text, prompt_name


def resolve_model(provider: str, raw_model: str | None) -> str:
    if provider == PROVIDER_CLAUDE:
        model = (raw_model or DEFAULT_CLAUDE_MODEL).strip()
        if model not in VALID_CLAUDE_MODELS:
            raise DistillError(
                (
                    f"Invalid claude model: {model}. "
                    f"Valid: {', '.join(VALID_CLAUDE_MODELS)}. "
                    f"Run with --list-models --provider claude to see the list."
                ),
                exit_code=EXIT_USAGE,
            )
        return model

    if provider == PROVIDER_CODEX:
        model = (raw_model or DEFAULT_CODEX_MODEL).strip()
        if model not in VALID_CODEX_MODELS:
            raise DistillError(
                (
                    f"Invalid codex model: {model}. "
                    f"Valid: {', '.join(VALID_CODEX_MODELS)}. "
                    f"Run with --list-models --provider codex to see the list."
                ),
                exit_code=EXIT_USAGE,
            )
        return model

    model = (raw_model or DEFAULT_OPENCODE_MODEL).strip()
    if model not in VALID_OPENCODE_MODELS:
        raise DistillError(
            (
                f"Invalid opencode model: {model}. "
                f"Valid: {', '.join(VALID_OPENCODE_MODELS)}. "
                f"Run with --list-models --provider opencode to see the list."
            ),
            exit_code=EXIT_USAGE,
        )
    return model


def translate_effort(provider: str, canonical: str) -> str:
    return EFFORT_ETL[provider][canonical]


def check_context_size(provider: str, input_text: str, prompt_text: str) -> int:
    input_tokens = count_tokens(input_text)
    prompt_tokens = count_tokens(prompt_text)
    overhead_tokens = count_tokens(USER_MESSAGE_OVERHEAD)
    total = input_tokens + prompt_tokens + overhead_tokens

    limit = CONTEXT_LIMITS[provider]
    if total > limit:
        raise LLMCallError(
            f"Input too large for {provider}: {total:,} tokens "
            f"(input {input_tokens:,} + prompt {prompt_tokens:,} "
            f"+ overhead {overhead_tokens:,}) exceeds safe limit "
            f"of {limit:,}. Reduce input size or split the file."
        )
    return input_tokens


def derive_slug(input_path: Path) -> str:
    """Input filename stem, with minimal sanitization for filesystem safety."""
    stem = input_path.stem
    # Replace path separators and control chars with underscores; keep unicode.
    sanitized = "".join(
        "_" if ch in ("/", "\\", ":", "\n", "\r", "\t") else ch for ch in stem
    )
    sanitized = sanitized.strip()
    return sanitized or "input"


def make_run_folder_path(
    output_parent: Path, slug: str, prompt_name: str
) -> tuple[Path, str]:
    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    run_folder_name = f"{slug}_{timestamp}_{prompt_name}"
    return output_parent / run_folder_name, run_folder_name


def validate_output_parent(parent: Path, *, create: bool) -> Path:
    """Return a resolved, writable output parent directory.

    When ``create`` is True (real runs), missing directories are created
    and a probe file verifies writability. When ``create`` is False
    (dry-run), the filesystem is not mutated: writability is inferred
    from ``os.access`` on the nearest existing ancestor.
    """
    parent = parent.expanduser().resolve()

    if parent.exists():
        if not parent.is_dir():
            raise OutputDirError(f"Output parent is not a directory: {parent}")
        if create:
            probe = parent / ".distill-write-probe"
            try:
                probe.touch()
                probe.unlink()
            except OSError as exc:
                raise OutputDirError(
                    f"Output parent is not writable: {parent} ({exc})"
                ) from exc
        else:
            if not os.access(parent, os.W_OK):
                raise OutputDirError(f"Output parent is not writable: {parent}")
        return parent

    # Parent does not exist yet
    if create:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputDirError(
                f"Cannot create output parent {parent}: {exc}"
            ) from exc
        return parent

    # Dry-run: walk up to the nearest existing ancestor and check it
    ancestor = parent.parent
    while not ancestor.exists():
        if ancestor == ancestor.parent:  # reached filesystem root
            raise OutputDirError(
                f"Cannot create output parent {parent}: no existing ancestor"
            )
        ancestor = ancestor.parent
    if not ancestor.is_dir() or not os.access(ancestor, os.W_OK):
        raise OutputDirError(
            f"Cannot create output parent {parent}: ancestor {ancestor} not writable"
        )
    return parent


def build_plan(args: argparse.Namespace) -> ResolvedPlan:
    input_path, input_text = resolve_input_file(args.input)
    prompt_path, prompt_text, prompt_name = resolve_prompt(args.prompt)

    provider: str = args.provider or DEFAULT_PROVIDER
    provider_cli_path = ensure_cli_available(provider)

    model = resolve_model(provider, args.model)

    # Determine effort: use explicit value, or default based on model.
    if provider == PROVIDER_OPENCODE:
        effort_canonical = "agent-defined"
        effort_vendor = "agent-defined"
    elif args.effort is not None:
        effort_canonical = args.effort
        effort_vendor = translate_effort(provider, effort_canonical)
    elif model in SONNET_MODELS:
        effort_canonical = "low"
        effort_vendor = translate_effort(provider, effort_canonical)
    else:
        effort_canonical = DEFAULT_EFFORT
        effort_vendor = translate_effort(provider, effort_canonical)

    input_tokens = check_context_size(provider, input_text, prompt_text)

    create_output_dir = not bool(args.dry_run)
    if args.output_dir:
        output_parent = validate_output_parent(
            Path(args.output_dir), create=create_output_dir
        )
    else:
        output_parent = validate_output_parent(
            input_path.parent, create=create_output_dir
        )

    slug = derive_slug(input_path)
    run_folder_path, run_folder_name = make_run_folder_path(
        output_parent, slug, prompt_name
    )

    return ResolvedPlan(
        input_path=input_path,
        input_text=input_text,
        input_tokens=input_tokens,
        prompt_path=prompt_path,
        prompt_text=prompt_text,
        prompt_name=prompt_name,
        provider=provider,
        provider_cli_path=provider_cli_path,
        model=model,
        effort_canonical=effort_canonical,
        effort_vendor=effort_vendor,
        output_parent=output_parent,
        slug=slug,
        run_folder_name=run_folder_name,
        run_folder_path=run_folder_path,
        quiet=bool(args.quiet),
    )


# -------------------------------------------------------------------------
# Discovery commands
# -------------------------------------------------------------------------


def print_list_models(provider_filter: str | None) -> None:
    show_claude = provider_filter in (None, PROVIDER_CLAUDE)
    show_codex = provider_filter in (None, PROVIDER_CODEX)
    show_opencode = provider_filter in (None, PROVIDER_OPENCODE)

    if show_claude:
        console.print("[bold]Claude models:[/bold]")
        for model in VALID_CLAUDE_MODELS:
            suffix = "  (default)" if model == DEFAULT_CLAUDE_MODEL else ""
            console.print(f"  {model}{suffix}")
        console.print()

    if show_codex:
        console.print("[bold]Codex models:[/bold]")
        for model in VALID_CODEX_MODELS:
            suffix = "  (default)" if model == DEFAULT_CODEX_MODEL else ""
            console.print(f"  {model}{suffix}")
        console.print()

    if show_opencode:
        console.print("[bold]OpenCode agents:[/bold]")
        for model in VALID_OPENCODE_MODELS:
            suffix = "  (default)" if model == DEFAULT_OPENCODE_MODEL else ""
            console.print(f"  {model}{suffix}")
        console.print()

    console.print("[bold]Effort levels (canonical, all providers):[/bold]")
    parts: list[str] = []
    for level in CANONICAL_EFFORTS:
        parts.append(f"{level} (default)" if level == DEFAULT_EFFORT else level)
    console.print("  " + ", ".join(parts))
    console.print()

    console.print("[bold]Internal ETL:[/bold]")
    if provider_filter == PROVIDER_CLAUDE:
        console.print("  canonical  claude")
        for level in CANONICAL_EFFORTS:
            console.print(f"  {level:<9}  {EFFORT_ETL[PROVIDER_CLAUDE][level]}")
        return

    if provider_filter == PROVIDER_CODEX:
        console.print("  canonical  codex")
        for level in CANONICAL_EFFORTS:
            console.print(f"  {level:<9}  {EFFORT_ETL[PROVIDER_CODEX][level]}")
        return

    if provider_filter == PROVIDER_OPENCODE:
        console.print("  OpenCode uses agent-defined reasoning presets.")
        return

    console.print("  canonical  claude   codex")
    for level in CANONICAL_EFFORTS:
        claude_val = EFFORT_ETL[PROVIDER_CLAUDE][level]
        codex_val = EFFORT_ETL[PROVIDER_CODEX][level]
        console.print(f"  {level:<9}  {claude_val:<7}  {codex_val}")


def list_prompt_names() -> list[str]:
    prompt_names: list[str] = []
    for child in sorted(PROMPTS_DIR.iterdir()):
        if not child.is_dir():
            continue
        if (child / "prompt.md").is_file():
            prompt_names.append(child.name.replace("-", "_"))
    return prompt_names


def print_list_prompts() -> None:
    for prompt_name in list_prompt_names():
        sys.stdout.write(prompt_name + "\n")


# -------------------------------------------------------------------------
# Dry-run printer
# -------------------------------------------------------------------------


def print_dry_run(plan: ResolvedPlan) -> None:
    console.print("[bold yellow]DRY RUN[/bold yellow] -- no LLM call, no files written")
    console.print()
    input_size = plan.input_path.stat().st_size
    console.print(
        f"input:          {plan.input_path} "
        f"({input_size:,} bytes, ~{plan.input_tokens:,} tokens)"
    )
    console.print(f"prompt:         {plan.prompt_name}")
    console.print(f"prompt path:    {plan.prompt_path}")
    console.print(
        f"provider:       {plan.provider} (found at {plan.provider_cli_path})"
    )
    console.print(f"model:          {plan.model}")
    console.print(
        f"effort:         {plan.effort_canonical} "
        f"→ {plan.effort_vendor} ({plan.provider})"
    )
    console.print(f"output folder:  {plan.run_folder_path}")
    console.print()
    console.print("Would write:")
    console.print(f"  {plan.slug}_{plan.prompt_name}.md")
    console.print(f"  {plan.slug}_raw{plan.input_path.suffix}")
    console.print(f"  {plan.slug}_meta.yml")


# -------------------------------------------------------------------------
# Provider callers
# -------------------------------------------------------------------------


def run_claude(
    plan: ResolvedPlan,
    output_file: Path,
) -> dict[str, int | str]:
    """Invoke the claude CLI and write the distilled output to ``output_file``.

    Returns a dict of usage stats for meta.yml.
    """
    user_message = f"{USER_MESSAGE_OVERHEAD}{plan.input_text}"

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "claude",
                "-p",
                "--dangerously-skip-permissions",
                "--model",
                plan.model,
                "--effort",
                plan.effort_vendor,
                "--tools",
                "",
                "--output-format",
                "json",
                "--system-prompt",
                plan.prompt_text,
                user_message,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=LLM_CLI_TIMEOUT_SECONDS,
        )

    try:
        result = retry_request(_run, max_attempts=LLM_MAX_RETRIES, quiet=plan.quiet)
    except subprocess.TimeoutExpired as exc:
        raise LLMCallError(
            f"claude CLI timed out after {LLM_CLI_TIMEOUT_SECONDS}s. "
            f"Input may be too large or the model overloaded."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr or exc.stdout or str(exc)
        raise LLMCallError(f"claude CLI failed: {details}") from exc

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LLMCallError(f"Failed to parse claude JSON response: {exc}") from exc

    if "result" not in response:
        raise LLMCallError(
            f"Unexpected claude JSON schema. Expected 'result' field. "
            f"Got keys: {sorted(response.keys())}"
        )

    content = str(response["result"]).strip()
    if not content:
        raise LLMCallError("claude returned empty result content.")

    output_file.write_text(content + "\n", encoding="utf-8")

    usage = response.get("usage", {}) or {}
    input_tokens = int(
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    output_tokens = int(usage.get("output_tokens", 0))

    return {
        "provider": PROVIDER_CLAUDE,
        "model": plan.model,
        "effort_canonical": plan.effort_canonical,
        "effort_vendor": plan.effort_vendor,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def run_codex(
    plan: ResolvedPlan,
    output_file: Path,
) -> dict[str, int | str]:
    """Invoke the codex CLI and write the distilled output to ``output_file``."""
    user_message = (
        f"{plan.prompt_text.strip()}\n\n{USER_MESSAGE_OVERHEAD}{plan.input_text}"
    )
    tmp_output = output_file.parent / ".tmp_codex_last_message.md"

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "codex",
                "exec",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--model",
                plan.model,
                "--config",
                f'model_reasoning_effort="{plan.effort_vendor}"',
                "--output-last-message",
                str(tmp_output),
                "-",
            ],
            input=user_message,
            stdout=subprocess.PIPE,
            text=True,
            check=True,
            timeout=LLM_CLI_TIMEOUT_SECONDS,
            stderr=subprocess.DEVNULL,
        )

    try:
        result = retry_request(_run, max_attempts=LLM_MAX_RETRIES, quiet=plan.quiet)
    except subprocess.TimeoutExpired as exc:
        raise LLMCallError(
            f"codex CLI timed out after {LLM_CLI_TIMEOUT_SECONDS}s. "
            f"Input may be too large or the model overloaded."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stdout or str(exc)
        raise LLMCallError(f"codex CLI failed: {details}") from exc

    content = ""
    if tmp_output.exists():
        content = tmp_output.read_text(encoding="utf-8").strip()
        tmp_output.unlink(missing_ok=True)
    if not content:
        content = (result.stdout or "").strip()
    if not content:
        raise LLMCallError("codex returned empty output.")

    output_file.write_text(content + "\n", encoding="utf-8")

    return {
        "provider": PROVIDER_CODEX,
        "model": plan.model,
        "effort_canonical": plan.effort_canonical,
        "effort_vendor": plan.effort_vendor,
    }


def run_opencode(
    plan: ResolvedPlan,
    output_file: Path,
) -> dict[str, int | str]:
    """Invoke the opencode CLI and write the distilled output to ``output_file``."""
    user_message = (
        f"{plan.prompt_text.strip()}\n\n{USER_MESSAGE_OVERHEAD}{plan.input_text}"
    )

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "opencode",
                "run",
                "--agent",
                plan.model,
                "--format",
                "json",
                "-",
            ],
            input=user_message,
            capture_output=True,
            text=True,
            check=True,
            timeout=LLM_CLI_TIMEOUT_SECONDS,
        )

    try:
        result = retry_request(_run, max_attempts=LLM_MAX_RETRIES, quiet=plan.quiet)
    except subprocess.TimeoutExpired as exc:
        raise LLMCallError(
            f"opencode CLI timed out after {LLM_CLI_TIMEOUT_SECONDS}s. "
            f"Input may be too large or the agent overloaded."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr or exc.stdout or str(exc)
        raise LLMCallError(f"opencode CLI failed: {details}") from exc

    chunks: list[str] = []
    total_tokens = 0
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0] not in "[{":
            continue

        try:
            event = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise LLMCallError(f"Failed to parse opencode JSON event: {exc}") from exc

        event_type = event.get("type")
        if event_type == "text":
            part = event.get("part", {})
            text = part.get("text") if isinstance(part, dict) else None
            if isinstance(text, str) and text:
                chunks.append(text)
            continue

        if event_type == "step_finish":
            part = event.get("part", {})
            tokens = part.get("tokens") if isinstance(part, dict) else None
            if isinstance(tokens, dict):
                total = tokens.get("total")
                if isinstance(total, int):
                    total_tokens = total

    content = "\n".join(chunk.strip() for chunk in chunks if chunk.strip()).strip()
    if not content:
        raise LLMCallError("opencode returned empty output.")

    output_file.write_text(content + "\n", encoding="utf-8")

    return {
        "provider": PROVIDER_OPENCODE,
        "model": plan.model,
        "effort_canonical": plan.effort_canonical,
        "effort_vendor": plan.effort_vendor,
        "total_tokens": total_tokens,
    }


def run_llm(plan: ResolvedPlan, output_file: Path) -> dict[str, int | str]:
    if plan.provider == PROVIDER_CLAUDE:
        return run_claude(plan, output_file)
    if plan.provider == PROVIDER_CODEX:
        return run_codex(plan, output_file)
    return run_opencode(plan, output_file)


# -------------------------------------------------------------------------
# Meta writer
# -------------------------------------------------------------------------


def write_meta(
    run_folder: Path,
    plan: ResolvedPlan,
    usage: dict[str, int | str],
    started_at: datetime,
    duration_seconds: float,
    output_file: Path,
) -> None:
    lines: list[str] = [
        f"file: {output_file.name}",
        f"original_file: {plan.input_path}",
        f"date: {started_at.isoformat(timespec='seconds')}",
        f"prompt: {plan.prompt_name}",
        f"prompt_file: {plan.prompt_path}",
        f"provider: {plan.provider}",
        f"model: {plan.model}",
        (f"effort: {plan.effort_canonical} → {plan.effort_vendor} ({plan.provider})"),
        f"duration: {duration_seconds:.1f}s",
        f"input_tokens: {plan.input_tokens:,}",
    ]

    if plan.provider == PROVIDER_CLAUDE:
        total_tokens = usage.get("total_tokens")
        output_tokens = usage.get("output_tokens")
        if isinstance(total_tokens, int):
            lines.append(f"total_tokens: {total_tokens:,}")
        if isinstance(output_tokens, int):
            lines.append(f"output_tokens: {output_tokens:,}")
    elif plan.provider == PROVIDER_OPENCODE:
        total_tokens = usage.get("total_tokens")
        if isinstance(total_tokens, int) and total_tokens > 0:
            lines.append(f"total_tokens: {total_tokens:,}")

    lines.append(f"distill_version: {__version__}")

    meta_file = run_folder / f"{plan.slug}_meta.yml"
    meta_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------


def execute_plan(plan: ResolvedPlan, open_finder: bool) -> Path:
    """Run the LLM, write output + meta, optionally open Finder.

    Returns the path to the run folder.
    """
    run_folder_path = plan.run_folder_path
    while True:
        try:
            run_folder_path.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            time.sleep(1.05)
            run_folder_path, _ = make_run_folder_path(
                plan.output_parent,
                derive_slug(plan.input_path),
                plan.prompt_name,
            )
        except OSError as exc:
            raise OutputDirError(
                f"Cannot create run folder {run_folder_path}: {exc}"
            ) from exc

    output_file = run_folder_path / f"{plan.slug}_{plan.prompt_name}.md"
    copied_input_file = run_folder_path / f"{plan.slug}_raw{plan.input_path.suffix}"
    shutil.copy2(plan.input_path, copied_input_file)

    if not plan.quiet:
        console.print(
            f"[cyan]Distilling {plan.input_path.name} "
            f"with {plan.prompt_name} via {plan.provider} "
            f"({plan.model}, effort={plan.effort_canonical})...[/cyan]"
        )

    started_at = datetime.now().astimezone()
    t0 = time.monotonic()
    usage = run_llm(plan, output_file)
    duration = time.monotonic() - t0

    write_meta(
        run_folder_path,
        plan,
        usage,
        started_at,
        duration,
        output_file,
    )

    if not plan.quiet:
        console.print(f"[green]Wrote {output_file}[/green]")
        console.print(f"[dim]Duration: {duration:.1f}s[/dim]")
    else:
        # In quiet mode, just the output path to stdout
        sys.stdout.write(str(output_file) + "\n")

    if open_finder:
        open_folder_in_finder(run_folder_path)

    return run_folder_path


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse already printed the error; propagate its code (default 2)
        return int(exc.code) if isinstance(exc.code, int) else EXIT_USAGE

    if args.list_models:
        # args.provider is None when the user did not pass --provider,
        # so None means "show all", and an explicit value filters.
        print_list_models(args.provider)
        return EXIT_SUCCESS

    if args.list_prompts:
        print_list_prompts()
        return EXIT_SUCCESS

    try:
        plan = build_plan(args)
    except DistillError as exc:
        error_console.print(f"[red]{exc}[/red]")
        return exc.exit_code

    if args.dry_run:
        print_dry_run(plan)
        return EXIT_SUCCESS

    try:
        execute_plan(plan, open_finder=not args.no_open)
    except DistillError as exc:
        error_console.print(f"[red]{exc}[/red]")
        return exc.exit_code
    except KeyboardInterrupt:
        error_console.print("[yellow]Interrupted[/yellow]")
        return 130
    except Exception as exc:  # noqa: BLE001
        error_console.print(f"[red]Unexpected error: {exc}[/red]")
        return EXIT_GENERIC_ERROR

    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

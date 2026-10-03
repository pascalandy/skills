#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run Codex or Claude Code as a child agent that reviews read-only, reviews and
fixes, or runs Codex's own code review, then print the model that ran, its
session, the files it changed, and its answer. One command shape per run keeps
headless use deterministic."""

# >>> cli-block: canonical copy in scripts/_cli.py; do not edit a pasted copy
import argparse
import json
import os
import re
import signal
import sys
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, NoReturn, TextIO

USAGE = 2
TEMPORARY = 75
INTERRUPTED = 128 + signal.SIGINT
TERMINATED = 128 + signal.SIGTERM


class ScriptError(Exception):
    """An expected failure; each argument is one message that says what to fix.

    `detail` is text printed on stderr before the messages; `report` is the
    object `--json` prints on stderr beside them.
    """

    code = 1

    def __init__(
        self, *messages: str, detail: str = "", report: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(*messages)
        self.detail = detail
        self.report = dict(report or {})


class UsageError(ScriptError):
    """A bad argument the parser cannot catch, such as an unknown name."""

    code = USAGE


class TemporaryError(ScriptError):
    """A failure a later retry may fix: an outage, a timeout, or a held lock."""

    code = TEMPORARY


class Interrupted(KeyboardInterrupt):
    """SIGINT or SIGTERM arrived; `code` is 130 or 143."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def exit_codes(specific: Mapping[int, str]) -> dict[int, str]:
    """Every code a script returns, in order, for its --help and its tests.

    `specific` adds codes or renames 1; 0, 1, 2, 130, and 143 are always there.
    """
    codes = {
        0: "success",
        1: "failure",
        USAGE: "bad usage",
        INTERRUPTED: "interrupted (SIGINT)",
        TERMINATED: "terminated (SIGTERM)",
        **specific,
    }
    reserved = [
        code for code in codes if code >= 124 and code not in (INTERRUPTED, TERMINATED)
    ]
    if reserved:
        raise ValueError(f"exit codes {reserved} are reserved for the shell and OS")
    return dict(sorted(codes.items()))


class Parser(argparse.ArgumentParser):
    """argparse without abbreviated options, whose help ends with the exit codes
    and whose usage errors print short usage and the help hint, then exit 2.

    With `json_errors` set, a usage error is one JSON object on stderr instead.
    """

    json_errors = False

    def __init__(
        self, *, exit_codes: Mapping[int, str], epilog: str = "", **kwargs: Any
    ) -> None:
        table = "\n".join(
            f"  {code:<4} {meaning}" for code, meaning in exit_codes.items()
        )
        kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
        super().__init__(
            epilog=f"{epilog}\n\nexit codes:\n{table}".lstrip("\n"),
            allow_abbrev=False,
            **kwargs,
        )
        self.exit_codes = dict(exit_codes)

    def error(self, message: str) -> NoReturn:
        if self.json_errors:
            failure = {"errors": [message], "help": f"{self.prog} --help"}
            self.exit(USAGE, json.dumps(failure, indent=2) + "\n")
        self.print_usage(sys.stderr)
        self.exit(USAGE, f"error: {message}\nrun '{self.prog} --help'\n")


def given(
    argv: Sequence[str], *flags: str, parser: argparse.ArgumentParser | None = None
) -> bool:
    """Whether one of `flags` comes before `--`, where options end; use it to let
    -h and --help win over every other argument, or to spot --json early.

    With `parser`, a bundle of its flag letters counts too, such as -vh for
    -v -h; a bundle holding an option that takes a value never does.
    """
    letters = {flag[1] for flag in flags if len(flag) == 2 and flag[1] != "-"}
    bundled = flag_letters(parser) if parser is not None and letters else set()
    for arg in argv:
        if arg == "--":
            return False
        if arg in flags:
            return True
        bundle = set(arg[1:]) if re.fullmatch(r"-[A-Za-z]{2,}", arg) else set()
        if bundle & letters and bundle <= bundled:
            return True
    return False


def flag_letters(parser: argparse.ArgumentParser) -> set[str]:
    """The one-letter options of `parser` and its commands that take no value."""
    letters: set[str] = set()
    parsers = [parser]
    while parsers:
        each = parsers.pop()
        for option, action in each._option_string_actions.items():
            if len(option) == 2 and option[1] != "-" and action.nargs == 0:
                letters.add(option[1])
        for action in each._actions:
            if isinstance(action, argparse._SubParsersAction):
                parsers.extend(action.choices.values())
    return letters


@contextmanager
def signals_interrupt() -> Iterator[None]:
    """Raise Interrupted(130) on SIGINT and Interrupted(143) on SIGTERM.

    The first signal ignores any repeat, so cleanup in `finally` blocks runs to
    the end. Handlers need the main thread; elsewhere this changes nothing.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    handled = (signal.SIGINT, signal.SIGTERM)
    previous = {number: signal.getsignal(number) for number in handled}
    fired = False

    def interrupt(number: int, _frame: object) -> None:
        nonlocal fired
        fired = True
        for each in handled:
            signal.signal(each, signal.SIG_IGN)
        raise Interrupted(128 + number)

    for number in handled:
        signal.signal(number, interrupt)
    try:
        yield
    finally:
        if not fired:
            for number, handler in previous.items():
                signal.signal(number, handler)


def env_flag(name: str) -> bool:
    """Whether an environment switch such as SYNC_FLEET_DEBUG is on: set, and not 0."""
    return os.environ.get(name, "") not in ("", "0")


def color_enabled(stream: TextIO, disabled: bool = False) -> bool:
    """Color only on a terminal, and never with --no-color, NO_COLOR, or TERM=dumb."""
    return (
        not disabled
        and not os.environ.get("NO_COLOR")
        and os.environ.get("TERM") != "dumb"
        and stream.isatty()
    )


DURATION = re.compile(r"(\d+(?:\.\d+)?)([smh]?)")


def duration(text: str) -> float:
    """Seconds from `30s`, `5m`, `2h`, or bare seconds; use it as an argparse type."""
    match = DURATION.fullmatch(text.strip())
    if match is None or float(match[1]) <= 0:
        raise argparse.ArgumentTypeError(
            f"invalid duration {text!r}; use a positive number of seconds, or 30s, 5m, 2h"
        )
    return float(match[1]) * {"": 1, "s": 1, "m": 60, "h": 3600}[match[2]]


# <<< cli-block

import hashlib
import logging
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

import tomllib

DEBUG_ENV = "HEADLESS_DEBUG"
GRACE = 10.0
CHECK_TIMEOUT = 60.0
CONFIG = Path(__file__).resolve().parents[1] / "config.toml"
HARNESSES = ("codex", "claude", "pi", "opencode")
# One model reaches Pi and OpenCode through several providers; Codex and Claude pick their own
PROVIDER_HARNESSES = ("pi", "opencode")
TABLE_KEYS = ("provider", "model", "reasoning-level")
READ_ONLY = ("review-only", "code-review")

log = logging.getLogger("headless")

RULES = {
    "review-only": (
        "Mode: review only. Report your findings only. Leave every file in {cwd} "
        "unchanged, and do not commit, push, merge, or post comments. Commands, "
        "tests, and checks may write caches and ignored build output."
    ),
    "review-fix": (
        "Mode: review and fix. You may edit files in {cwd} to fix what you find. "
        "Do not commit, push, merge, or post comments; the caller reviews your diff."
    ),
}

CLAUDE_EDIT_TOOLS = "Edit,Write,NotebookEdit"

EXIT_CODES = exit_codes(
    {
        1: "the child failed, gave no answer, was denied a tool, or changed the "
        "checkout under --review-only or --code-review; or the config is invalid",
        TEMPORARY: "a login check timed out; rerun",
    }
)

EXAMPLES = """\
examples:
  headless.py --review-only --prompt-file /tmp/review/prompt.md --cwd ~/projects/app
  headless.py codex --code-review --base main --cwd ~/projects/app
  headless.py codex --review-fix --prompt-file fix.md --model gpt-6-astra --effort high
  headless.py claude --review-fix --prompt-file next.md --resume 3f1c2e9a-0b4d-4c55-9a0e-6d1f2b7c8e90
  headless.py codex --review-only --prompt-file prompt.md -- -c 'web_search="live"'

Without a CLI name, the launcher runs the config's harness; --code-review always
runs Codex. Flags after -- go to the child CLI unchanged. On success, stdout holds
the model, effort, session, changed, and run lines, a blank line, then the answer.
The run folder keeps the prompt, the answer, and the child's logs."""


@dataclass(frozen=True)
class Request:
    """One child run, resolved from the arguments."""

    target: str
    mode: str
    cwd: Path
    model: str
    effort: str
    session: str | None
    resume: bool
    git: bool
    review: tuple[str, ...]
    extra: tuple[str, ...]


@dataclass(frozen=True)
class Reply:
    """What a child's own output says about its run."""

    answer: str
    model: str | None
    session: str | None
    problems: tuple[str, ...] = ()


@dataclass(frozen=True)
class Result:
    """The run as reported to the caller and saved as run.json."""

    target: str
    mode: str
    model: str | None
    effort: str
    session: str | None
    changed: list[str]
    run_dir: str
    answer: str


@dataclass(frozen=True)
class Defaults:
    """One harness's table in the config."""

    model: str
    effort: str
    provider: str | None


@dataclass(frozen=True)
class Config:
    path: Path
    harness: str
    tables: dict[str, Defaults]


@dataclass(frozen=True)
class Runner:
    """How to launch, check, and read one child CLI."""

    efforts: tuple[str, ...]
    auth: tuple[str, ...]
    login: str
    command: Callable[[Request, Path], list[str]]
    reply: Callable[[Path], Reply]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def codex_command(request: Request, run: Path) -> list[str]:
    if request.mode == "code-review":
        # The review reads review_model, not -m; -m only feeds the model line Codex prints
        return [
            "codex",
            "exec",
            "review",
            "-c",
            'sandbox_mode="read-only"',
            "-c",
            'approval_policy="never"',
            "-m",
            request.model,
            "-c",
            f'review_model="{request.model}"',
            "-c",
            f'model_reasoning_effort="{request.effort}"',
            *request.extra,
            "-o",
            str(run / "answer.md"),
            *request.review,
        ]
    command = ["codex", "exec"]
    if request.resume and request.session:
        command += ["resume", request.session]
    else:
        command += ["-C", str(request.cwd)]
    if not request.git:
        command.append("--skip-git-repo-check")
    return [
        *command,
        "--dangerously-bypass-approvals-and-sandbox",
        "-m",
        request.model,
        "-c",
        f'model_reasoning_effort="{request.effort}"',
        *request.extra,
        "-o",
        str(run / "answer.md"),
        "-",
    ]


CODEX_HEADER = re.compile(r"^(model|session id): (.+)$", re.MULTILINE)


def codex_reply(run: Path) -> Reply:
    header: dict[str, str] = {}
    for key, value in CODEX_HEADER.findall(read_text(run / "stderr.log")):
        header.setdefault(key, value.strip())
    answer = read_text(run / "answer.md")
    problems = []
    if answer.startswith("Review was interrupted"):
        problems.append("Codex reports that the review was interrupted")
    return Reply(answer, header.get("model"), header.get("session id"), tuple(problems))


def claude_command(request: Request, run: Path) -> list[str]:
    session = "--resume" if request.resume else "--session-id"
    settings = json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": request.effort}})
    return [
        "claude",
        "-p",
        "--model",
        request.model,
        "--effort",
        request.effort,
        "--settings",
        settings,
        "--dangerously-skip-permissions",
        *(
            ["--disallowedTools", CLAUDE_EDIT_TOOLS]
            if request.mode == "review-only"
            else []
        ),
        "--output-format",
        "json",
        session,
        str(request.session),
        *request.extra,
    ]


def claude_reply(run: Path) -> Reply:
    text = read_text(run / "stdout.log").strip()
    try:
        data = json.loads(text.splitlines()[-1]) if text else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        return Reply("", None, None, ("Claude printed no JSON result",))
    problems = []
    if data.get("is_error"):
        problems.append(f"Claude ended with an error: {data.get('subtype', 'unknown')}")
    denied = sorted(
        {
            str(each.get("tool_name", "a tool"))
            for each in data.get("permission_denials") or []
        }
    )
    if denied:
        problems.append(f"Claude was denied {', '.join(denied)}")
    result = data.get("result")
    usage = data.get("modelUsage") or {}
    busiest = sorted(usage, key=lambda name: -(usage[name].get("outputTokens") or 0))
    models = ", ".join(busiest) or None
    return Reply(
        result if isinstance(result, str) else "",
        models,
        data.get("session_id"),
        tuple(problems),
    )


RUNNERS = {
    "codex": Runner(
        efforts=("low", "medium", "high", "xhigh", "max", "ultra"),
        auth=("codex", "login", "status"),
        login="codex login",
        command=codex_command,
        reply=codex_reply,
    ),
    "claude": Runner(
        efforts=("low", "medium", "high", "xhigh", "max"),
        auth=("claude", "auth", "status", "--text"),
        login="claude auth login",
        command=claude_command,
        reply=claude_reply,
    ),
}


def load_config(path: Path) -> Config:
    """Read and check the whole config, so a typo in any table fails every run."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScriptError(
            f"cannot read the config {path}: {error.strerror}; pass --config FILE"
        ) from None
    except tomllib.TOMLDecodeError as error:
        raise ScriptError(f"{path} is not valid TOML: {error}") from None
    problems: list[str] = []
    tables: dict[str, Defaults] = {}
    for name, value in data.items():
        if name == "harness":
            continue
        if name not in HARNESSES:
            problems.append(
                f"unknown key '{name}'; keep harness and the "
                f"[{'], ['.join(HARNESSES)}] tables"
            )
            continue
        if not isinstance(value, dict):
            problems.append(f"{name} must be a [{name}] table")
            continue
        table = cast(dict[str, object], value)
        problems += [
            f"[{name}] has an unknown key '{key}'"
            for key in table
            if key not in TABLE_KEYS
        ]
        model, effort = table.get("model"), table.get("reasoning-level")
        provider = table.get("provider")
        for key, text in (("model", model), ("reasoning-level", effort)):
            if not isinstance(text, str) or not text:
                problems.append(f"[{name}] needs {key} as a non-empty string")
        if name in PROVIDER_HARNESSES and (
            not isinstance(provider, str) or not provider
        ):
            problems.append(
                f"[{name}] needs provider, since several providers serve one model"
            )
        if name not in PROVIDER_HARNESSES and provider is not None:
            problems.append(f"[{name}] takes no provider; {name} picks its own")
        efforts = RUNNERS[name].efforts if name in RUNNERS else None
        if efforts and isinstance(effort, str) and effort and effort not in efforts:
            problems.append(
                f"[{name}] reasoning-level '{effort}' is not one of {', '.join(efforts)}"
            )
        if isinstance(model, str) and isinstance(effort, str):
            tables[name] = Defaults(
                model, effort, provider if isinstance(provider, str) else None
            )
    harness = data.get("harness")
    if not isinstance(harness, str) or harness not in HARNESSES:
        problems.append(f"harness must be one of {', '.join(HARNESSES)}")
    needed = dict.fromkeys([*RUNNERS, harness if isinstance(harness, str) else ""])
    problems += [
        f"the [{name}] table is missing"
        for name in needed
        if name in HARNESSES and name not in data
    ]
    if problems:
        raise ScriptError(*(f"{path}: {problem}" for problem in problems))
    return Config(path, cast(str, harness), tables)


def resolve_target(named: str | None, mode: str, config: Config) -> str:
    """The CLI to run: --code-review needs Codex, a named CLI wins, else the config's harness."""
    if mode == "code-review":
        if named not in (None, "codex"):
            raise UsageError(
                f"--code-review runs Codex only; drop {named} or pass codex"
            )
        return "codex"
    target = named or config.harness
    if target not in RUNNERS:
        raise UsageError(
            f'{config.path} sets harness = "{target}", which the launcher does not run '
            f"yet (#281); pass codex or claude, or follow references/{target}/MetaSkill.md"
        )
    return target


def review_target(args: argparse.Namespace) -> tuple[str, ...]:
    """What `codex exec review` reviews, as its flags; empty for the other modes."""
    diff = [
        flag
        for flag, value in (
            ("--base", args.base),
            ("--uncommitted", args.uncommitted),
            ("--commit", args.commit),
            ("--title", args.title),
        )
        if value
    ]
    if args.mode != "code-review":
        if diff:
            raise UsageError(f"{', '.join(diff)} works only with --code-review")
        if args.prompt_file is None:
            raise UsageError(f"--{args.mode} needs --prompt-file")
        return ()
    if args.resume:
        raise UsageError(
            "--code-review cannot resume; ask follow-up questions with "
            "--review-only --resume SESSION"
        )
    chosen = [flag for flag in diff if flag != "--title"]
    if args.prompt_file is not None:
        chosen.append("--prompt-file")
    if len(chosen) != 1:
        raise UsageError(
            "--code-review needs exactly one of --base, --uncommitted, --commit, "
            "or --prompt-file"
        )
    title = ("--title", args.title) if args.title else ()
    if args.base:
        return ("--base", args.base, *title)
    if args.uncommitted:
        return ("--uncommitted", *title)
    if args.commit:
        return ("--commit", args.commit, *title)
    return (*title, "-")


class GitFailure(Exception):
    """A git command failed; the message is git's own diagnostic."""


def git(cwd: Path, *args: str) -> str:
    try:
        done = subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitFailure(str(error)) from None
    if done.returncode != 0:
        raise GitFailure(
            done.stderr.strip() or f"git {args[0]} exited {done.returncode}"
        )
    return done.stdout


def git_root(cwd: Path) -> Path | None:
    """The top of the checkout holding `cwd`, or None when `cwd` is outside Git."""
    try:
        return Path(git(cwd, "rev-parse", "--show-toplevel").strip())
    except GitFailure as error:
        if "not a git repository" in str(error):
            return None
        raise ScriptError(f"cannot read the Git state of {cwd}: {error}") from None


def resolves(root: Path, ref: str) -> bool:
    try:
        git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    except GitFailure:
        return False
    return True


def snapshot(root: Path, cwd: Path, moment: str) -> dict[str, str]:
    """The commit, then every changed or untracked path with its full status
    record and content hash. A porcelain v2 record carries the HEAD, index, and
    worktree modes and the HEAD and index blob IDs, so a change to staged content
    shows even when the worktree bytes are restored. Ignored files stay out."""
    try:
        listing = git(
            root, "status", "--porcelain=v2", "-z", "--branch", "--untracked-files=all"
        )
        state: dict[str, str] = {}
        records = iter(listing.split("\0"))
        for record in records:
            if record.startswith("# branch.oid "):
                state["HEAD"] = record.removeprefix("# branch.oid ")
                continue
            kind = record[:1]
            if kind not in ("1", "2", "u", "?"):
                continue
            fields = {"1": 8, "2": 9, "u": 10, "?": 1}[kind]
            path = record.split(" ", fields)[fields]
            if kind == "2":
                record += f" from {next(records, '')}"
            state[path] = f"{record} {digest(root / path)}"
    except (GitFailure, OSError) as error:
        raise ScriptError(
            f"cannot read the Git state of {cwd} {moment}: {error}"
        ) from None
    if "HEAD" not in state:
        raise ScriptError(
            f"cannot read the Git state of {cwd} {moment}: no branch header"
        )
    return state


def digest(file: Path) -> str:
    if not file.is_file():
        return "-"
    with file.open("rb") as content:
        return hashlib.file_digest(content, "sha256").hexdigest()


def changes(before: dict[str, str] | None, after: dict[str, str] | None) -> list[str]:
    if before is None or after is None:
        return []
    return [
        "HEAD (a new commit)" if key == "HEAD" else key
        for key in sorted(before.keys() | after.keys())
        if before.get(key) != after.get(key)
    ]


def preflight(target: str, runner: Runner) -> None:
    if shutil.which(target) is None:
        raise ScriptError(f"{target} is not on PATH; install it, then rerun")
    try:
        done = subprocess.run(
            list(runner.auth),
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise TemporaryError(f"'{shlex.join(runner.auth)}' timed out") from None
    if done.returncode != 0:
        raise ScriptError(
            f"{target} is not logged in; run '{runner.login}', then rerun"
        )


def run_child(command: list[str], *, cwd: Path, run: Path, timeout: float) -> int:
    """Run the child in its own process group, with the prompt on stdin and its
    output in the run folder. A timeout or an interrupt stops the whole group,
    and so does a child that exits while processes it started keep running."""
    with (
        open(run / "prompt.md", encoding="utf-8") as stdin,
        open(run / "stdout.log", "w", encoding="utf-8") as stdout,
        open(run / "stderr.log", "w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            command, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, process_group=0
        )
        try:
            status = process.wait(timeout=timeout)
        except BaseException:
            stop(process)
            raise
        if group_alive(process):
            log.warning("warning: %s left processes running; stopping them", command[0])
            stop(process)
        return status


def group_alive(process: subprocess.Popen[bytes]) -> bool:
    """Whether any process in the child's group still runs, after reaping the child."""
    process.poll()
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def stop(process: subprocess.Popen[bytes]) -> None:
    """SIGTERM the child's process group, SIGKILL every member still alive GRACE
    seconds later, then reap the child."""
    for number in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, number)
        except ProcessLookupError:
            break
        deadline = time.monotonic() + GRACE
        while group_alive(process) and time.monotonic() < deadline:
            time.sleep(0.1)
        if not group_alive(process):
            break
    process.wait()


def read_prompt(name: str) -> str:
    if name == "-":
        return sys.stdin.read()
    try:
        return Path(name).expanduser().read_text(encoding="utf-8")
    except OSError as error:
        raise UsageError(
            f"cannot read --prompt-file {name}: {error.strerror}"
        ) from None


def summary(result: Result) -> str:
    return "\n".join(
        [
            f"model: {result.model or 'unknown'}",
            f"effort: {result.effort}",
            f"session: {result.session or 'unknown'}",
            f"changed: {', '.join(result.changed) or 'nothing'}",
            f"run: {result.run_dir}",
        ]
    )


def launch(args: argparse.Namespace, extra: list[str]) -> Result:
    config = load_config(Path(args.config).expanduser())
    target = resolve_target(args.target, args.mode, config)
    runner = RUNNERS[target]
    defaults = config.tables[target]
    effort = args.effort or defaults.effort
    if effort not in runner.efforts:
        raise UsageError(
            f"--effort {effort} is not one of {', '.join(runner.efforts)} for {target}"
        )
    review = review_target(args)
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise UsageError(f"--cwd {args.cwd} is not a directory")
    prompt = "" if args.prompt_file is None else read_prompt(args.prompt_file)
    if args.prompt_file is not None and not prompt.strip():
        raise UsageError("the prompt is empty")
    root = git_root(cwd)
    if root is None and args.mode == "code-review":
        raise UsageError(
            f"--code-review reviews a Git diff; {cwd} is not a Git checkout"
        )
    # Codex only meets a missing ref mid-review, after the paid run has started
    for flag, ref in (("--base", args.base), ("--commit", args.commit)):
        if ref and root and not resolves(root, ref):
            raise UsageError(
                f"{flag} {ref} names no commit in {cwd}; run 'git fetch' or name one that exists"
            )
    preflight(target, runner)

    before = snapshot(root, cwd, "before the run") if root else None
    if before is None:
        log.warning(
            "warning: %s is not a Git checkout, so file changes go unchecked", cwd
        )
    fresh_session = str(uuid.uuid4()) if target == "claude" else None
    request = Request(
        target=target,
        mode=args.mode,
        cwd=cwd,
        model=args.model or defaults.model,
        effort=effort,
        session=args.resume or fresh_session,
        resume=args.resume is not None,
        git=before is not None,
        review=review,
        extra=tuple(extra),
    )
    run = Path(tempfile.mkdtemp(prefix=f"headless-{target}-{args.mode}."))
    rule = RULES.get(args.mode)
    (run / "prompt.md").write_text(
        f"{rule.format(cwd=cwd)}\n\n{prompt}" if rule else prompt, encoding="utf-8"
    )
    command = runner.command(request, run)
    log.info("run folder: %s", run)
    log.info("command: %s", shlex.join(command))
    try:
        status = run_child(command, cwd=cwd, run=run, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        raise ScriptError(
            f"{target} ran past --timeout; its partial output is in {run}"
        ) from None

    reply = runner.reply(run)
    if not (run / "answer.md").exists():
        (run / "answer.md").write_text(reply.answer, encoding="utf-8")
    result = Result(
        target=target,
        mode=args.mode,
        model=reply.model,
        effort=effort,
        session=reply.session or request.session,
        changed=changes(before, snapshot(root, cwd, "after the run") if root else None),
        run_dir=str(run),
        answer=reply.answer.strip(),
    )
    (run / "run.json").write_text(
        json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8"
    )

    problems = list(reply.problems)
    if status != 0:
        problems.insert(0, f"{target} exited {status}; read stderr.log in {run}")
    if not result.answer:
        problems.append(f"{target} gave no answer")
    if args.mode in READ_ONLY and result.changed:
        problems.append(
            f"the {args.mode} run changed the checkout: {', '.join(result.changed)}"
        )
    if problems:
        raise ScriptError(*problems, detail=summary(result), report=asdict(result))
    return result


def build_parser() -> Parser:
    parser = Parser(
        description=__doc__,
        exit_codes=EXIT_CODES,
        epilog=EXAMPLES,
    )
    parser.add_argument(
        "target",
        nargs="?",
        choices=sorted(RUNNERS),
        help="child CLI to run (default: harness in the config)",
    )
    access = parser.add_mutually_exclusive_group(required=True)
    access.add_argument(
        "--review-only",
        dest="mode",
        action="store_const",
        const="review-only",
        help="report findings; the run fails if the checkout changed, "
        "and Claude runs without its file-editing tools",
    )
    access.add_argument(
        "--review-fix",
        dest="mode",
        action="store_const",
        const="review-fix",
        help="report findings and fix them in --cwd",
    )
    access.add_argument(
        "--code-review",
        dest="mode",
        action="store_const",
        const="code-review",
        help="run Codex's own review, codex exec review, read-only; the run fails "
        "if the checkout changed",
    )
    parser.add_argument(
        "--prompt-file",
        metavar="FILE",
        help="the task for the child; - reads stdin. Required by --review-only and "
        "--review-fix; with --code-review, custom review instructions in place "
        "of a diff to review",
    )
    diff = parser.add_mutually_exclusive_group()
    diff.add_argument(
        "--base",
        metavar="BRANCH",
        help="with --code-review: review the changes against BRANCH",
    )
    diff.add_argument(
        "--uncommitted",
        action="store_true",
        help="with --code-review: review staged, unstaged, and untracked changes",
    )
    diff.add_argument(
        "--commit",
        metavar="SHA",
        help="with --code-review: review the changes a commit introduced",
    )
    parser.add_argument(
        "--title", help="with --code-review: the title the review summary shows"
    )
    parser.add_argument(
        "--cwd",
        default=".",
        metavar="DIR",
        help="checkout the child works in (default: .)",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=str(CONFIG),
        metavar="FILE",
        help="defaults for the harness, model, and reasoning level "
        f"(default: {CONFIG})",
    )
    parser.add_argument(
        "--model",
        help="model for the child; --code-review passes it as review_model too "
        "(default: model in the config)",
    )
    parser.add_argument(
        "--effort",
        help="reasoning level, passed to codex as model_reasoning_effort "
        "and to claude as --effort (default: reasoning-level in the config)",
    )
    parser.add_argument(
        "--resume", metavar="SESSION", help="continue a session a previous run printed"
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=duration("2h"),
        help="stop the child after this long (default: 2h)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the run as one JSON object"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print the run folder and command on stderr",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=f"print tracebacks on stderr; also {DEBUG_ENV}=1",
    )
    return parser


def report(error: ScriptError, parser: Parser, as_json: bool) -> int:
    messages = [str(message) for message in error.args]
    usage = isinstance(error, UsageError)
    if as_json:
        failure = {**error.report, "errors": messages}
        if usage:
            failure["help"] = f"{parser.prog} --help"
        print(json.dumps(failure, indent=2), file=sys.stderr)
        return error.code
    if error.detail:
        print(error.detail, file=sys.stderr)
    if usage:
        parser.print_usage(sys.stderr)
    for message in messages:
        print(f"error: {message}", file=sys.stderr)
    if usage:
        print(f"run '{parser.prog} --help'", file=sys.stderr)
    return error.code


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    split = argv.index("--") if "--" in argv else len(argv)
    own, extra = argv[:split], argv[split + 1 :]
    parser = build_parser()
    if given(own, "-h", "--help", parser=parser):
        parser.print_help()
        return 0
    as_json = given(own, "--json")
    parser.json_errors = as_json
    with signals_interrupt():
        try:
            args = parser.parse_args(own)
            debug = args.debug or env_flag(DEBUG_ENV)
            logging.basicConfig(
                format="%(message)s",
                level=logging.DEBUG
                if debug
                else logging.INFO
                if args.verbose
                else logging.WARNING,
                stream=sys.stderr,
                force=True,
            )
            result = launch(args, extra)
        except SystemExit as stop:
            return stop.code if isinstance(stop.code, int) else 1
        except Interrupted as stop:
            word = "interrupted" if stop.code == INTERRUPTED else "terminated"
            print(json.dumps({"errors": [word]}) if as_json else word, file=sys.stderr)
            return stop.code
        except ScriptError as error:
            return report(error, parser, as_json)
        except Exception as error:
            log.debug("unexpected failure", exc_info=True)
            return report(
                ScriptError(f"{type(error).__name__}: {error}"), parser, as_json
            )
    print(
        json.dumps(asdict(result), indent=2)
        if as_json
        else f"{summary(result)}\n\n{result.answer}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Run a skill's evaluation scenarios in fresh Claude Code and Codex sessions:
one scratch git repo per scenario and agent, holding the skill as it stood at a
git ref. Each run folder keeps the request, the transcript, the answer, and the
repo's git state, to grade against the scenario's expected behavior."""

# >>> cli-block: canonical copy in scripts/_cli.py; do not edit a pasted copy
import argparse
import json
import logging
import os
import re
import shlex
import signal
import sys
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, NoReturn, TextIO

USAGE = 2
TEMPORARY = 75
INTERRUPTED = 128 + signal.SIGINT
TERMINATED = 128 + signal.SIGTERM


class ScriptError(Exception):
    """An expected failure; each argument is one message that says what to fix.

    `detail` is text printed on stderr before the answer; `report` holds the
    fields the answer carries beside `errors`, such as `changes`.
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
    and whose usage errors print short usage and the help hint, then exit 2;
    run_script() makes them answer in JSON instead."""

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
        self.print_usage(sys.stderr)
        self.exit(USAGE, f"error: {message}\nrun '{self.prog} --help'\n")


def answer(code: int, fields: Mapping[str, Any]) -> int:
    """Print the one JSON line a script answers with, and return `code`.

    `ok` comes first and is true exactly when `code` is 0, whatever `fields`
    says. Success goes to stdout; a failure goes to stderr, after its
    diagnostics, and leaves stdout empty (docs/references/script-output.md).
    """
    body = {"ok": code == 0, **fields}
    body["ok"] = code == 0
    line = json.dumps(body, separators=(",", ":"))
    print(line, file=sys.stderr if code else sys.stdout)
    return code


def given(
    argv: Sequence[str], *flags: str, parser: argparse.ArgumentParser | None = None
) -> bool:
    """Whether one of `flags` comes before `--`, where options end; use it to let
    -h and --help win over every other argument.

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


def command_parsers(parser: argparse.ArgumentParser) -> list[argparse.ArgumentParser]:
    """The parser of every command below `parser`, at any depth."""
    found: list[argparse.ArgumentParser] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for command in dict.fromkeys(action.choices.values()):
                found += [command, *command_parsers(command)]
    return found


def named_command(
    parser: argparse.ArgumentParser, argv: Sequence[str]
) -> argparse.ArgumentParser:
    """The deepest command `argv` names, whose help -h asks for."""
    for arg in argv:
        if arg == "--":
            break
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction) and arg in action.choices:
                parser = action.choices[arg]
                break
    return parser


def usage_error_for(parser: argparse.ArgumentParser) -> Callable[[str], NoReturn]:
    """The error method of `parser`: a usage error whose help hint names it, so
    a command's mistake points to that command's help."""

    def error(message: str) -> NoReturn:
        raise UsageError(message, report={"help": f"{parser.prog} --help"})

    return error


def run_script(
    parser: Parser,
    work: Callable[[argparse.Namespace], Mapping[str, Any]],
    argv: Sequence[str] | None = None,
    *,
    debug: str | None = None,
) -> int:
    """Parse arguments, run `work`, and answer its outcome in one JSON line with
    its exit code, as docs/references/script-output.md describes.

    Every outcome answers, even a usage error, a bug, or an interrupt. `work`
    returns the data beside `ok`, usually {}, and raises ScriptError,
    UsageError, or TemporaryError for expected failures. `debug` names the
    script's <NAME>_DEBUG variable and adds --debug; without it the script never
    prints a traceback. Call it from `main()` and pass the result to `SystemExit`.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    # A command's parser takes -v and --debug too, after the command; SUPPRESS
    # keeps a flag given before it
    for each in (parser, *command_parsers(parser)):
        default = False if each is parser else argparse.SUPPRESS
        if "-v" not in each._option_string_actions:
            each.add_argument(
                "-v",
                "--verbose",
                action="store_true",
                default=default,
                help="print progress and step details on stderr",
            )
        if debug and "--debug" not in each._option_string_actions:
            each.add_argument(
                "--debug",
                action="store_true",
                default=default,
                help=f"print internals, timings, and tracebacks on stderr; also {debug}=1",
            )
        # Parser.error prints usage errors itself; raising sends each one
        # through answer_failure(). The root reports unknown arguments, which
        # belong to the command argv names
        named = named_command(parser, argv) if each is parser else each
        each.error = usage_error_for(named)  # pyright: ignore[reportAttributeAccessIssue]
    if given(argv, "-h", "--help", parser=parser):
        named_command(parser, argv).print_help()
        return 0

    command = shlex.join([*parser.prog.split(), *argv])
    tracing = False
    with signals_interrupt():
        try:
            args = parser.parse_args(argv)
            tracing = debug is not None and (args.debug or env_flag(debug))
            logging.basicConfig(
                format="%(message)s",
                level=logging.DEBUG
                if tracing
                else logging.INFO
                if args.verbose
                else logging.WARNING,
                stream=sys.stderr,
                force=True,
            )
            return answer(0, work(args))
        except KeyboardInterrupt as stop:
            code = getattr(stop, "code", INTERRUPTED)
            word = "interrupted" if code == INTERRUPTED else "terminated"
            return answer(code, {"errors": [word]})
        except ScriptError as error:
            return answer_failure(error, parser, command)
        except Exception as error:
            # The traceback comes first, so the answer ends stderr
            logging.getLogger(__name__).debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(f"{type(error).__name__}: {error}")
            return answer_failure(
                unexpected, parser, command, rerun=bool(debug) and not tracing
            )


def answer_failure(
    error: ScriptError, parser: Parser, command: str, rerun: bool = False
) -> int:
    """Answer a failure on stderr, after its detail, and return its exit code.
    Hints name the command to run next: help for a usage error, retry for a
    temporary failure, and rerun with --debug for a bug."""
    messages = [str(message) for message in error.args]
    hints: dict[str, str] = {}
    if isinstance(error, UsageError) and "help" not in error.report:
        hints["help"] = f"{parser.prog} --help"
    elif isinstance(error, TemporaryError) and messages:
        hints["retry"] = command
    elif rerun:
        hints["rerun"] = f"{command} --debug"
    if error.detail:
        print(error.detail, file=sys.stderr)
    return answer(error.code, {"errors": messages, **error.report, **hints})


# <<< cli-block

import posixpath
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

DEBUG_ENV = "RUN_EVALS_DEBUG"
AGENTS = ("claude", "codex")
CODEX_MODEL = "gpt-6.1-sol"
CODEX_EFFORT = "high"
GRACE = 10.0
CODEX_HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
INSTALLED = (CODEX_HOME / "skills", Path.home() / ".agents" / "skills")

# Set for every setup command and agent; a runner that sees it refuses to start
PARENT_ENV = "RUN_EVALS_PARENT"
# Removed from each run, so neither setup nor the agent can authenticate to GitHub
CREDENTIALS = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
    "GIT_ASKPASS",
    "SSH_ASKPASS",
)

log = logging.getLogger("run_evals")

EXIT_CODES = exit_codes(
    {1: "a run failed or timed out, or git or an agent CLI is missing"}
)

EXAMPLES = """\
examples:
  run_evals.py skills/commit --ref main
  run_evals.py skills/commit --ref HEAD --agent codex --scenario 2
  run_evals.py skills/gh-stack --ref origin/main --output-dir ~/.cache/gh-stack-baseline
  run_evals.py skills/gh-stack --ref HEAD --dry-run

The scenarios come from <skill>/evals/evals.json in the working tree, so new
scenarios run against an older ref. The skill and each other skill a scenario
lists come from <ref>; a listed name resolves to the folder that shares the
longest path with <skill>. A skill absent at <ref> is left out, which gives a
no-skill baseline. Each scenario's setup is a list of
shell commands run in the fresh repo, with $EVALS naming the evals folder.

Codex runs with --dangerously-bypass-approvals-and-sandbox, model gpt-6.1-sol
at high, and the installed copies of the listed skills, and of skills <ref>
deleted, disabled in $CODEX_HOME/skills (default ~/.codex/skills) and
~/.agents/skills. Claude runs with --setting-sources project, so it sees only
the copies this run installs. Setup and agent run without GitHub or git
credentials: no gh login, no token, no global or system git config, no
credential helper or askpass, no SSH. GitHub
refuses their writes, so a scenario that needs a remote uses a local bare
repository. --github-token-file gives gh a token for scenarios that read
GitHub; give it a read-only one. A gh shim logs every call to gh-calls.log. A
runner started inside a run refuses to start. A run that ends or times out has
its process group and every descendant stopped. A run answers
{"ok":true,"folders":[...]}, one folder per run, and a dry run answers the same
without running; a failure lists each run's status on stderr before its answer."""

GH_SHIM = """\
#!/usr/bin/env bash
printf '%s\\n' "$*" >> {log}
exec {gh} "$@"
"""


@dataclass(frozen=True)
class Scenario:
    """One entry of evals.json, numbered from 1."""

    number: int
    query: str
    setup: tuple[str, ...]
    skills: tuple[str, ...]


@dataclass(frozen=True)
class Plan:
    """What every run shares: the skill, the ref it comes from, and where runs go."""

    skill: Path
    repo: Path
    sha: str
    evals: Path
    output: Path
    token: str | None


@dataclass(frozen=True)
class Run:
    """One scenario in one agent, in its own folder."""

    scenario: Scenario
    agent: str
    folder: Path

    @property
    def name(self) -> str:
        return f"s{self.scenario.number}-{self.agent}"


class Children:
    """Setup and agent processes still running. Once cancelled, no new one starts, so an
    interrupt during a run's setup cannot launch a paid agent afterward."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.live: set[subprocess.Popen[bytes]] = set()
        self.cancelled = False

    def run(
        self,
        command: list[str],
        cwd: Path,
        env: Mapping[str, str],
        stdout: BinaryIO,
        stderr: BinaryIO,
        deadline: float,
        stdin: bytes = b"",
    ) -> str:
        with self.lock:
            if self.cancelled:
                return "cancelled"
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return "timeout"
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            self.live.add(process)
        try:
            process.communicate(stdin, timeout=remaining)
            return "done" if process.returncode == 0 else f"exit {process.returncode}"
        except subprocess.TimeoutExpired:
            return "timeout"
        finally:
            stop(process)
            with self.lock:
                self.live.discard(process)

    def stop_all(self) -> None:
        with self.lock:
            self.cancelled = True
            live = list(self.live)
        for process in live:
            stop(process)


def descendants(pid: int) -> set[int]:
    """Every process below `pid` in one `ps` snapshot, including any that left the
    process group, such as an agent another launcher started in its own session."""
    listed = subprocess.run(
        ["ps", "-A", "-o", "pid=", "-o", "ppid="],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    children: dict[int, list[int]] = {}
    for line in listed.splitlines():
        fields = line.split()
        if len(fields) == 2 and all(field.isdigit() for field in fields):
            children.setdefault(int(fields[1]), []).append(int(fields[0]))
    found: set[int] = set()
    queue = [pid]
    while queue:
        for child in children.get(queue.pop(), []):
            if child not in found:
                found.add(child)
                queue.append(child)
    return found


def stop(process: subprocess.Popen[bytes]) -> None:
    """SIGTERM the child's process group and every descendant, then SIGKILL what
    is left after GRACE seconds, even when the leader already exited."""
    tree = descendants(process.pid)

    def send(number: int) -> None:
        targets = [(os.killpg, process.pid), *((os.kill, pid) for pid in tree)]
        for kill, target in targets:
            try:
                kill(target, number)
            except (ProcessLookupError, PermissionError):
                pass

    send(signal.SIGTERM)
    try:
        process.wait(timeout=GRACE)
    except subprocess.TimeoutExpired:
        pass
    send(signal.SIGKILL)
    process.wait()


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ScriptError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout or ""


def load_scenarios(evals: Path, wanted: Sequence[int]) -> list[Scenario]:
    path = evals / "evals.json"
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise UsageError(f"{path} does not exist; write the scenarios first") from None
    except json.JSONDecodeError as error:
        raise UsageError(f"{path} is not valid JSON: {error}") from None
    if not isinstance(entries, list) or not entries:
        raise UsageError(f"{path} must hold a list of scenarios")
    scenarios = []
    for number, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise UsageError(f"scenario {number} must be an object in {path}")
        setup = entry.get("setup", [])
        if not isinstance(setup, list) or not all(isinstance(c, str) for c in setup):
            raise UsageError(
                f"scenario {number} in {path}: setup must be a list of shell commands"
            )
        query = entry.get("query")
        if not isinstance(query, str) or not query.strip():
            raise UsageError(f"scenario {number} in {path} has no query")
        skills = entry.get("skills", [])
        if not isinstance(skills, list) or not all(
            isinstance(name, str) and name.strip() for name in skills
        ):
            raise UsageError(
                f"scenario {number} in {path}: skills must be a list of nonempty names"
            )
        scenarios.append(Scenario(number, query, tuple(setup), tuple(skills)))
    for number in wanted:
        if not 1 <= number <= len(scenarios):
            raise UsageError(
                f"--scenario {number} is out of range; {path} holds {len(scenarios)}"
            )
    return [s for s in scenarios if not wanted or s.number in wanted]


def make_plan(
    skill: Path, ref: str, output: Path | None, token: str | None = None
) -> Plan:
    skill = skill.expanduser().resolve()
    if not skill.is_dir():
        raise UsageError(f"{skill} is not a folder")
    repo = Path(git(skill, "rev-parse", "--show-toplevel").strip())
    found = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--verify",
            "--quiet",
            f"{ref}^{{commit}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode:
        raise UsageError(f"--ref {ref} names no commit in {repo}")
    sha = found.stdout.strip()
    if output is None:
        cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output = cache / "run-evals" / f"{skill.name}-{sha[:7]}-{stamp}"
    output = output.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise UsageError(f"{output} is not empty; pass another --output-dir")
    return Plan(skill, repo, sha, skill / "evals", output, token)


def skill_names(paths: str) -> dict[str, list[str]]:
    """Folders holding a SKILL.md, by skill name, from git's path listing."""
    folders: dict[str, list[str]] = {}
    for path in paths.splitlines():
        if path == "SKILL.md" or path.endswith("/SKILL.md"):
            folder = posixpath.dirname(path)
            folders.setdefault(posixpath.basename(folder), []).append(folder)
    return folders


def skills_at(plan: Plan) -> dict[str, list[str]]:
    folders = skill_names(git(plan.repo, "ls-tree", "-r", "--name-only", plan.sha))
    if folders.pop("", None) and plan.skill == plan.repo:
        folders.setdefault(plan.skill.name, []).append(".")
    return folders


def deleted_by(plan: Plan, present: Mapping[str, list[str]]) -> set[str]:
    """Skills the ref's history added anywhere in the repository, minus those left."""
    added = git(
        plan.repo,
        "log",
        "--format=",
        "--name-only",
        "--diff-filter=A",
        plan.sha,
        "--",
        "*SKILL.md",
    )
    return set(skill_names(added)) - set(present) - {""}


def source_of(plan: Plan, name: str, present: Mapping[str, list[str]]) -> str | None:
    """The folder of `name` that shares the longest path with the target, so
    authoring/<category>/ and a compiled skills/ tree each resolve to their own."""
    target = plan.skill.relative_to(plan.repo).as_posix()

    def shared(folder: str) -> int:
        common = posixpath.commonpath([target, folder])
        return len(common.split("/")) if common else 0

    candidates = sorted(present.get(name, []), key=shared, reverse=True)
    if len(candidates) > 1 and shared(candidates[0]) == shared(candidates[1]):
        raise UsageError(
            f"skill {name} has several folders at the ref: {', '.join(candidates)}"
        )
    return candidates[0] if candidates else None


def wanted(plan: Plan, scenario: Scenario) -> list[str]:
    """The target, then each other skill the scenario lists."""
    return list(dict.fromkeys([plan.skill.name, *scenario.skills]))


def install(
    plan: Plan, names: Sequence[str], target: Path, present: Mapping[str, list[str]]
) -> list[str]:
    """Copy each named skill as it stood at the ref; return one line per name."""
    target.mkdir(parents=True)
    (target.parent / ".gitignore").write_text("*\n", encoding="utf-8")
    lines = []
    for name in names:
        source = source_of(plan, name, present)
        if source is None:
            lines.append(f"absent\t{name}")
            continue
        archive = subprocess.run(
            ["git", "-C", str(plan.repo), "archive", plan.sha, source],
            capture_output=True,
            check=True,
        )
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run(
                ["tar", "-x", "-C", scratch], input=archive.stdout, check=True
            )
            shutil.copytree(Path(scratch) / source, target / name, symlinks=True)
        lines.append(f"installed\t{name}")
    return lines


def hidden_paths(names: set[str]) -> list[Path]:
    return [
        base / name / "SKILL.md"
        for base in INSTALLED
        for name in sorted(names)
        if (base / name / "SKILL.md").is_file()
    ]


def agent_command(run: Run, work: Path, hide: list[Path]) -> tuple[list[str], bytes]:
    """The child command and its stdin."""
    if run.agent == "claude":
        return [
            "claude",
            "-p",
            run.scenario.query,
            "--setting-sources",
            "project",
            "--permission-mode",
            "bypassPermissions",
            "--output-format",
            "stream-json",
            "--verbose",
        ], b""
    command = [
        "codex",
        "exec",
        "-C",
        str(work),
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        "-m",
        CODEX_MODEL,
        "-c",
        f'model_reasoning_effort="{CODEX_EFFORT}"',
        "-c",
        "allow_login_shell=false",
    ]
    if hide:
        entries = ",".join(f"{{path={json.dumps(str(p))},enabled=false}}" for p in hide)
        command += ["-c", f"skills.config=[{entries}]"]
    command += ["--json", "-o", str(run.folder / "answer.md"), "-"]
    return command, run.scenario.query.encode()


def claude_answer(events: Path) -> str:
    answer = ""
    for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            answer = str(event.get("result") or "")
    return answer


def execute(
    run: Run,
    plan: Plan,
    timeout: float,
    children: Children,
    present: Mapping[str, list[str]],
    deleted: set[str],
) -> str:
    """Build the run's repo, run the agent in it, and record what it left."""
    folder, scenario = run.folder, run.scenario
    if children.cancelled:
        return "cancelled"
    deadline = time.monotonic() + timeout
    work = folder / "work"
    work.mkdir(parents=True)
    (folder / "query.txt").write_text(scenario.query + "\n", encoding="utf-8")
    (folder / "ref.txt").write_text(plan.sha + "\n", encoding="utf-8")
    git(work, "init", "-q")
    git(work, "config", "user.name", "Eval Runner")
    git(work, "config", "user.email", "eval@example.invalid")
    env = run_env(plan, folder)
    with (folder / "setup.log").open("wb") as setup_log:
        for command in scenario.setup:
            status = children.run(
                ["bash", "-euo", "pipefail", "-c", command],
                work,
                env,
                setup_log,
                setup_log,
                deadline,
            )
            if status != "done":
                return (
                    status
                    if status in ("timeout", "cancelled")
                    else f"setup failed: {command}"
                )
    skills_dir = work / (".claude" if run.agent == "claude" else ".agents") / "skills"
    lines = install(plan, wanted(plan, scenario), skills_dir, present)
    (folder / "skills.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    hide = hidden_paths(set(wanted(plan, scenario)) | deleted)
    command, stdin = agent_command(run, work, hide)
    (folder / "command.txt").write_text(shlex.join(command) + "\n", encoding="utf-8")
    log.info("%s started", run.name)
    with (
        (folder / "events.jsonl").open("wb") as events,
        (folder / "stderr.log").open("wb") as errors,
    ):
        status = children.run(command, work, env, events, errors, deadline, stdin)
    if run.agent == "claude":
        (folder / "answer.md").write_text(
            claude_answer(folder / "events.jsonl"), encoding="utf-8"
        )
    logged = subprocess.run(
        ["git", "-C", str(work), "log", "--all", "--stat", "--format=--- %h %s%n%b"],
        capture_output=True,
        text=True,
        check=False,
    )
    (folder / "git-log.txt").write_text(logged.stdout, encoding="utf-8")
    (folder / "git-status.txt").write_text(
        git(work, "status", "--porcelain"), encoding="utf-8"
    )
    log.info("%s %s", run.name, status)
    return status


def run_env(plan: Plan, folder: Path) -> dict[str, str]:
    """The environment of a run's setup and agent: no GitHub or git credentials,
    so GitHub refuses any write, and a gh shim that logs each call."""
    gh_config = folder / "gh-config"
    gh_config.mkdir()
    env = {key: value for key, value in os.environ.items() if key not in CREDENTIALS}
    env.update(
        {
            "EVALS": str(plan.evals),
            PARENT_ENV: "1",
            "GH_CONFIG_DIR": str(gh_config),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_SSH_COMMAND": "false",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "credential.helper",
            "GIT_CONFIG_VALUE_0": "",
        }
    )
    if plan.token:
        env["GH_TOKEN"] = plan.token
    real_gh = shutil.which("gh")
    if real_gh:
        shim = folder / "bin" / "gh"
        shim.parent.mkdir()
        shim.write_text(
            GH_SHIM.format(
                log=shlex.quote(str(folder / "gh-calls.log")), gh=shlex.quote(real_gh)
            ),
            encoding="utf-8",
        )
        shim.chmod(0o755)
        env["PATH"] = f"{shim.parent}{os.pathsep}{env.get('PATH', '')}"
    return env


def read_token(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        token = path.expanduser().read_text(encoding="utf-8").strip()
    except OSError as error:
        raise UsageError(
            f"cannot read --github-token-file {path}: {error.strerror}"
        ) from None
    if not token:
        raise UsageError(f"--github-token-file {path} is empty")
    return token


def launch(args: argparse.Namespace) -> dict[str, Any]:
    if env_flag(PARENT_ENV):
        raise ScriptError(
            "run_evals.py is running inside an eval run, which cannot start another; "
            "record this scenario's baseline from a normal session"
        )
    plan = make_plan(
        Path(args.skill), args.ref, args.output_dir, read_token(args.github_token_file)
    )
    scenarios = load_scenarios(plan.evals, args.scenario or [])
    agents = tuple(dict.fromkeys(args.agent or AGENTS))
    missing = [
        cli for cli in ("git", "tar", "bash", *agents) if shutil.which(cli) is None
    ]
    if missing:
        raise ScriptError(
            *(
                f"{cli} is not installed; install it, or leave its agent out with --agent"
                for cli in missing
            )
        )
    present = skills_at(plan)
    for scenario in scenarios:
        for name in wanted(plan, scenario):
            source_of(plan, name, present)
    deleted = deleted_by(plan, present)
    runs = [
        Run(scenario, agent, plan.output / f"s{scenario.number}-{agent}")
        for scenario in scenarios
        for agent in agents
    ]
    folders = {"folders": [str(run.folder) for run in runs]}
    if args.dry_run:
        return folders
    plan.output.mkdir(parents=True, exist_ok=True)
    children = Children()
    pool = ThreadPoolExecutor(max_workers=args.jobs)
    try:
        statuses = list(
            pool.map(
                lambda run: execute(
                    run, plan, args.timeout, children, present, deleted
                ),
                runs,
            )
        )
    except KeyboardInterrupt as stop:
        # Runs paid for so far left their folders, so the answer names them
        code = getattr(stop, "code", INTERRUPTED)
        error = ScriptError(
            "interrupted" if code == INTERRUPTED else "terminated", report=folders
        )
        error.code = code
        raise error from stop
    except ScriptError as error:
        error.report.update(folders)
        raise
    except Exception as error:
        log.debug("unexpected failure", exc_info=True)
        raise ScriptError(
            f"{type(error).__name__}: {error}; see the traceback with --debug",
            report=folders,
        ) from error
    finally:
        children.stop_all()
        pool.shutdown(wait=True, cancel_futures=True)
    lines = "\n".join(
        f"{run.name}\t{status}\t{run.folder}" for run, status in zip(runs, statuses)
    )
    failed = [run.name for run, status in zip(runs, statuses) if status != "done"]
    if failed:
        raise ScriptError(
            f"{len(failed)} of {len(runs)} runs did not finish: {', '.join(failed)}; "
            "read setup.log or stderr.log in each run folder",
            detail=lines,
            report=folders,
        )
    return folders


def positive(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value < 1:
        raise argparse.ArgumentTypeError(
            f"invalid count {text!r}; use a whole number from 1"
        )
    return value


def build_parser() -> Parser:
    parser = Parser(
        prog="run_evals.py",
        description=__doc__,
        exit_codes=EXIT_CODES,
        epilog=EXAMPLES,
    )
    parser.add_argument("skill", help="skill folder holding evals/evals.json")
    parser.add_argument(
        "--ref", required=True, help="git ref whose copy of the skill each run installs"
    )
    parser.add_argument(
        "--agent",
        action="append",
        choices=AGENTS,
        help="agent to run; repeat for several (default: claude and codex)",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        type=positive,
        metavar="N",
        help="run only scenario N, counted from 1; repeat for several (default: all)",
    )
    parser.add_argument(
        "--jobs",
        type=positive,
        default=6,
        metavar="N",
        help="runs at a time (default: 6)",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=duration("30m"),
        help="stop a run after this long, including setup (default: 30m)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="folder for the run folders (default: "
        "~/.cache/run-evals/<skill>-<sha>-<UTC time>)",
    )
    parser.add_argument(
        "--github-token-file",
        type=Path,
        metavar="FILE",
        help="give gh in each run the token in FILE; use a read-only token "
        "(default: runs have no GitHub credentials)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="answer the run folders without running them",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    return run_script(build_parser(), launch, argv, debug=DEBUG_ENV)


if __name__ == "__main__":
    raise SystemExit(main())

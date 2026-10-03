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

import logging
import shlex
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEBUG_ENV = "RUN_EVALS_DEBUG"
AGENTS = ("claude", "codex")
CODEX_MODEL = "gpt-6.1-sol"
CODEX_EFFORT = "high"
GRACE = 10.0
INSTALLED = (Path.home() / ".codex" / "skills", Path.home() / ".agents" / "skills")

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
lists come from <ref>, read as siblings of <skill>; a skill absent at <ref> is
left out, which gives a no-skill baseline. Each scenario's setup is a list of
shell commands run in the fresh repo, with $EVALS naming the evals folder.

Codex runs with --dangerously-bypass-approvals-and-sandbox, model gpt-6.1-sol
at high, and the installed copies of the listed skills, and of skills <ref>
deleted, disabled. Claude runs with --setting-sources project, so it sees only
the copies this run installs. A gh wrapper logs every call to gh-calls.log and
refuses GitHub writes. stdout prints one line per run: name, status, folder."""

GH_WRAPPER = """\
#!/usr/bin/env bash
log={log}
printf '%s\\n' "$*" >> "$log"
refuse() {{ printf 'REFUSED %s\\n' "$*" >> "$log"; echo "gh: this run refuses GitHub writes: $*" >&2; exit 1; }}
case "$1 ${{2:-}}" in
  "issue create"|"issue edit"|"issue comment"|"issue close"|"issue reopen"|"issue delete"|\\
  "issue transfer"|"issue lock"|"issue unlock"|"issue pin"|"issue unpin"|"issue develop"|\\
  "pr create"|"pr edit"|"pr merge"|"pr comment"|"pr close"|"pr review"|"pr ready"|\\
  "label create"|"label edit"|"label delete"|"label clone"|"repo create"|"repo edit"|\\
  "repo delete"|"release create"|"release delete"|"sub-issue add"|"sub-issue remove"|\\
  "stack submit"|"stack merge"|"stack link") refuse "$@" ;;
esac
if [ "$1" = api ]; then
  method="" body=0 prev=""
  for a in "$@"; do
    case "$prev" in -X|--method) method=${{a^^}} ;; esac
    case "$a" in
      -X?*) method=${{a#-X}}; method=${{method^^}} ;;
      --method=*) method=${{a#--method=}}; method=${{method^^}} ;;
      -f|-F|--field|--raw-field|--input|-f?*|-F?*|--field=*|--raw-field=*|--input=*) body=1 ;;
    esac
    case "$a" in *mutation*) refuse "$@" ;; esac
    prev=$a
  done
  if [ "${{2:-}}" != graphql ]; then
    [ -n "$method" ] && [ "$method" != GET ] && refuse "$@"
    [ -z "$method" ] && [ "$body" = 1 ] && refuse "$@"
  fi
fi
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
    """Agent processes still running, so an interrupt can stop them."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.live: set[subprocess.Popen[bytes]] = set()

    def add(self, process: subprocess.Popen[bytes]) -> None:
        with self.lock:
            self.live.add(process)

    def remove(self, process: subprocess.Popen[bytes]) -> None:
        with self.lock:
            self.live.discard(process)

    def stop_all(self) -> None:
        with self.lock:
            live = list(self.live)
        for process in live:
            stop(process)


def stop(process: subprocess.Popen[bytes]) -> None:
    """SIGTERM the child's process group, then SIGKILL it after GRACE seconds."""
    for number, wait in ((signal.SIGTERM, GRACE), (signal.SIGKILL, None)):
        try:
            os.killpg(process.pid, number)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


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
        setup = entry.get("setup", [])
        if not isinstance(setup, list) or not all(isinstance(c, str) for c in setup):
            raise UsageError(
                f"scenario {number} in {path}: setup must be a list of shell commands"
            )
        query = entry.get("query")
        if not isinstance(query, str) or not query.strip():
            raise UsageError(f"scenario {number} in {path} has no query")
        scenarios.append(
            Scenario(number, query, tuple(setup), tuple(entry.get("skills", [])))
        )
    for number in wanted:
        if not 1 <= number <= len(scenarios):
            raise UsageError(
                f"--scenario {number} is out of range; {path} holds {len(scenarios)}"
            )
    return [s for s in scenarios if not wanted or s.number in wanted]


def make_plan(skill: Path, ref: str, output: Path | None) -> Plan:
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
    return Plan(skill, repo, sha, skill / "evals", output)


def names_at(plan: Plan) -> set[str]:
    """Skill folders beside the target at the ref."""
    parent = plan.skill.parent.relative_to(plan.repo).as_posix()
    listed = git(plan.repo, "ls-tree", "--name-only", f"{plan.sha}:{parent}")
    return set(listed.split())


def deleted_by(plan: Plan) -> set[str]:
    """Skill folders the ref's history added beside the target, minus those left."""
    parent = plan.skill.parent.relative_to(plan.repo).as_posix()
    listed = git(
        plan.repo,
        "log",
        "--format=",
        "--name-only",
        "--diff-filter=A",
        plan.sha,
        "--",
        f"{parent}/",
    )
    prefix = f"{parent}/" if parent != "." else ""
    added = {
        line[len(prefix) :].split("/")[0]
        for line in listed.splitlines()
        if line.startswith(prefix) and "/" in line[len(prefix) :]
    }
    return added - names_at(plan)


def install(plan: Plan, names: Sequence[str], target: Path) -> list[str]:
    """Copy each named skill as it stood at the ref; return one line per name."""
    target.mkdir(parents=True)
    (target.parent / ".gitignore").write_text("*\n", encoding="utf-8")
    present = names_at(plan)
    lines = []
    for name in names:
        if name not in present:
            lines.append(f"absent\t{name}")
            continue
        source = (plan.skill.parent / name).relative_to(plan.repo).as_posix()
        archive = subprocess.run(
            ["git", "-C", str(plan.repo), "archive", plan.sha, source],
            capture_output=True,
            check=True,
        )
        with tempfile.TemporaryDirectory() as scratch:
            subprocess.run(
                ["tar", "-x", "-C", scratch], input=archive.stdout, check=True
            )
            shutil.move(str(Path(scratch) / source), str(target / name))
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


def execute(run: Run, plan: Plan, timeout: float, children: Children) -> str:
    """Build the run's repo, run the agent in it, and record what it left."""
    folder, scenario = run.folder, run.scenario
    work = folder / "work"
    work.mkdir(parents=True)
    (folder / "query.txt").write_text(scenario.query + "\n", encoding="utf-8")
    (folder / "ref.txt").write_text(plan.sha + "\n", encoding="utf-8")
    git(work, "init", "-q")
    git(work, "config", "user.name", "Eval Runner")
    git(work, "config", "user.email", "eval@example.invalid")
    env = {**os.environ, "EVALS": str(plan.evals)}
    for command in scenario.setup:
        done = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", command],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode:
            (folder / "setup.log").write_text(
                done.stdout + done.stderr, encoding="utf-8"
            )
            return f"setup failed: {command}"
    skills_dir = work / (".claude" if run.agent == "claude" else ".agents") / "skills"
    lines = install(plan, scenario.skills, skills_dir)
    (folder / "skills.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    real_gh = shutil.which("gh")
    if real_gh:
        wrapper = folder / "bin" / "gh"
        wrapper.parent.mkdir()
        wrapper.write_text(
            GH_WRAPPER.format(
                log=shlex.quote(str(folder / "gh-calls.log")), gh=shlex.quote(real_gh)
            ),
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        env["PATH"] = f"{wrapper.parent}{os.pathsep}{env.get('PATH', '')}"
    hide = hidden_paths(set(scenario.skills) | deleted_by(plan))
    command, stdin = agent_command(run, work, hide)
    (folder / "command.txt").write_text(shlex.join(command) + "\n", encoding="utf-8")
    log.info("%s started", run.name)
    with (
        (folder / "events.jsonl").open("wb") as events,
        (folder / "stderr.log").open("wb") as errors,
    ):
        process = subprocess.Popen(
            command,
            cwd=work,
            env=env,
            stdin=subprocess.PIPE,
            stdout=events,
            stderr=errors,
            start_new_session=True,
        )
        children.add(process)
        try:
            process.communicate(stdin, timeout=timeout)
            status = "done" if process.returncode == 0 else f"exit {process.returncode}"
        except subprocess.TimeoutExpired:
            stop(process)
            status = "timeout"
        finally:
            children.remove(process)
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


def launch(args: argparse.Namespace) -> str:
    plan = make_plan(Path(args.skill), args.ref, args.output_dir)
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
    runs = [
        Run(scenario, agent, plan.output / f"s{scenario.number}-{agent}")
        for scenario in scenarios
        for agent in agents
    ]
    if args.dry_run:
        return "\n".join(f"{run.name}\tplanned\t{run.folder}" for run in runs)
    plan.output.mkdir(parents=True, exist_ok=True)
    children = Children()
    pool = ThreadPoolExecutor(max_workers=args.jobs)
    try:
        statuses = list(
            pool.map(lambda run: execute(run, plan, args.timeout, children), runs)
        )
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
        )
    return lines


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
        help="stop a run after this long (default: 30m)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="folder for the run folders (default: "
        "~/.cache/run-evals/<skill>-<sha>-<UTC time>)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print the runs without running them",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print each run's start and status on stderr",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=f"print tracebacks on stderr; also {DEBUG_ENV}=1",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if given(argv, "-h", "--help", parser=parser):
        parser.print_help()
        return 0
    with signals_interrupt():
        try:
            args = parser.parse_args(argv)
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
            output = launch(args)
        except SystemExit as exit_:
            return exit_.code if isinstance(exit_.code, int) else 1
        except Interrupted as stopped:
            print(
                "interrupted" if stopped.code == INTERRUPTED else "terminated",
                file=sys.stderr,
            )
            return stopped.code
        except ScriptError as error:
            if error.detail:
                print(error.detail, file=sys.stderr)
            if isinstance(error, UsageError):
                parser.print_usage(sys.stderr)
            for message in error.args:
                print(f"error: {message}", file=sys.stderr)
            if isinstance(error, UsageError):
                print(f"run '{parser.prog} --help'", file=sys.stderr)
            return error.code
        except Exception as error:
            log.debug("unexpected failure", exc_info=True)
            print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
            return 1
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deploy GitHub's published main to the fleet without moving authoring HEAD.

The launcher fetches main, then runs the code from a reusable detached Git
worktree. Each machine receives the published commit through Git, updates its
own deployment worktree, saves and pulls its existing private clone, and
installs committed public sources. A malformed private clone is left alone;
other machines continue. An offline machine catches up on the next run.

The registry is the one fleet.toml in the private repository, so every machine
has it and hosts stay out of this public one; the private-network skill ships
it in references/. Each path is relative to that machine's home, and other keys
are notes for agents:

  [machines.mbp]
  ssh = "andy16@mbp16.example.ts.net"
  path = "Documents/github_local/skills"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath

import sync_private
import tomllib
from _cli import (
    Parser,
    ScriptError,
    TemporaryError,
    UsageError,
    duration,
    exit_codes,
)
from _common import (
    GRACE,
    exclusive,
    is_network_failure,
    run,
    run_git,
    run_script,
    send,
    stop,
)
from _published_checkout import author_root, published

ROOT = Path(__file__).resolve().parent.parent
STATE = (
    Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    / "skills-sync"
)
FLEET_REF = "refs/fleet/hub"
GITHUB_MAIN = "refs/remotes/origin/main"
PUSH_WAIT = 180
SSH = (
    "ssh",
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=8",
    "-o",
    "ServerAliveInterval=5",
    "-o",
    "ServerAliveCountMax=3",
    "-o",
    "ForwardAgent=no",
    "-o",
    "StrictHostKeyChecking=yes",
)
NEEDS_YOU = 11
UNREACHABLE = 255
TEMPORARY = 75
TIMEOUT = 600
POLL_DELAY = 3
FINE = ("synced", "ready", "converged")
# What a remote step prints for each change it makes
CHANGE = re.compile(r"(clone|commit|pull|push|add|update|remove)\t")
EPILOG = """\
A run prints one line per machine it changed, `synced<TAB>NAME<TAB>SHA`, and a
dry run one per machine it would change, `ready<TAB>NAME<TAB>SHA`; a run with
nothing to change prints nothing. A failure prints every machine's status and
what to do on stderr.

examples:
  just sync-fleet              # every machine
  just sync-fleet mbp          # one machine, by registry name or host
  just sync-fleet --check      # compare installed skills on every machine
  just sync-fleet --dry-run --verbose"""
EXIT_CODES = exit_codes(
    {
        0: "every selected machine is synced, ready, or converged",
        1: "a machine needs you, drifted, or failed",
        75: "every failure was temporary: offline, timed out, or a held lock; retry",
    }
)
log = logging.getLogger("sync-fleet")

# Children each run in their own session; an interrupt stops them all, and no
# worker thread starts another
CHILDREN: set[subprocess.Popen[str]] = set()
CHILDREN_LOCK = threading.Lock()
STOPPING = threading.Event()


class Stopped(Exception):
    """The run was interrupted, so a worker thread starts no new child."""


# Each step runs in the machine's login shell, with uv on PATH over SSH.
# The body is one function called with stdin closed so Git cannot consume it.
ENTER = """
enter() {
    cd "$HOME/$1" 2>/dev/null && git rev-parse --git-dir >/dev/null 2>&1 || {
        echo "no skills checkout at ~/$1"
        return 11
    }
}
plain() {
    [ -L _skills_private ] || { [ -e _skills_private ] && [ ! -d _skills_private/.git ]; }
}
published_step() {
    common=$(git rev-parse --path-format=absolute --git-common-dir) || return 11
    cache="$common/published-deployment"
    script="$cache/scripts/sync_fleet.py"
    if [ -f "$script" ]; then
        if [ -L "$cache" ] || ! git worktree list --porcelain | grep -Fxq "worktree $cache"; then
            echo "error: $cache is not the owned worktree; move it aside"
            return 1
        fi
        changes=$(git -C "$cache" status --porcelain) || return 1
        if [ -n "$changes" ]; then
            echo "error: published worktree $cache has edits; inspect them"
            return 1
        fi
    else
        script="$PWD/scripts/sync_fleet.py"
    fi
    uv run --quiet "$script" --author-root "$PWD" "$@" 2>&1
}
"""
# A private folder that is not a clone may hold edits the sync cannot save, so
# it stops the machine before anything is sent.
INSPECT = """
step() {
    enter "$1" || return
    if plain; then
        echo "~/$1/_skills_private is not a clone of the private repo; move it aside, then rerun"
        return 11
    fi
    common=$(git rev-parse --path-format=absolute --git-common-dir) || return 11
    if [ -f "$common/published-deployment/.git" ]; then
        head=$(git -C "$common/published-deployment" rev-parse -q --verify HEAD) || return 11
    else
        head=-
    fi
    echo "checkout $head"
}
"""
# After bootstrap, the cached launcher works even on old authoring branches.
APPLY = """
step() {
    enter "$1" || return
    published_step --machine-step apply --revision "$2" --timeout "$3"
}
"""
# Prints private state and a preview of the published install.
CHECK = """
step() {
    enter "$1" || return
    git fetch --quiet origin main 2>/dev/null || :
    git cat-file -e "$2^{commit}" 2>/dev/null || {
        echo "published revision $2 is unavailable; reconnect to GitHub and rerun"
        return 75
    }
    published_step --machine-step check --revision "$2" --timeout "$3"
}
"""


@dataclass(frozen=True)
class Machine:
    name: str
    ssh: str
    path: str

    @property
    def host(self) -> str:
        return self.ssh.split("@")[-1].split(".")[0].lower()

    def is_local(self) -> bool:
        return socket.gethostname().split(".")[0].lower() in {
            self.name.lower(),
            self.host,
        }

    def address(self) -> str:
        """Where git sends the published commit: a local path or SSH address."""
        if self.is_local():
            return str(Path.home() / self.path)
        return f"{self.ssh}:{PurePosixPath(self.path)}"


@dataclass(frozen=True)
class Source:
    """Published Git revision and private main in a check or preview."""

    sha: str
    private: str = ""
    saves: tuple[str, ...] = ()

    def contains(self, commit: str) -> bool:
        return git("merge-base", "--is-ancestor", commit, self.sha).returncode == 0


@dataclass
class Outcome:
    machine: str
    status: str
    detail: str
    targets: list[dict] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    temporary: bool = False
    sha: str = ""


def registry() -> Path:
    """The one fleet.toml in the private clone, wherever the skill that ships it lives."""
    private = sync_private.PRIVATE
    found = sorted(
        path
        for path in private.rglob("fleet.toml")
        if ".git" not in path.relative_to(private).parts
    )
    if len(found) > 1:
        raise ScriptError(
            f"{len(found)} fleet registries in {private}: "
            + ", ".join(str(path.relative_to(private)) for path in found)
            + "; keep one"
        )
    if not found:
        raise ScriptError(
            f"no fleet.toml in {private}; the private-network skill keeps it in references/"
        )
    return found[0]


def has_registry() -> bool:
    """For hooks: warn, never block git, when the registry cannot be found."""
    try:
        registry()
    except ScriptError as error:
        log.warning("warning: %s; the fleet does not sync", error)
        return False
    return True


def load_registry(path: Path) -> list[Machine]:
    if not path.is_file():
        raise ScriptError(
            f"no fleet registry at {path}; add [machines.NAME] tables with ssh and path"
        )
    try:
        tables = tomllib.loads(path.read_text(encoding="utf-8")).get("machines", {})
    except tomllib.TOMLDecodeError as error:
        raise ScriptError(f"{path} is not valid TOML: {error}") from error
    machines: list[Machine] = []
    problems: list[str] = []
    for name, table in tables.items():
        ssh, relative = table.get("ssh"), table.get("path")
        if not isinstance(ssh, str) or not ssh:
            problems.append(f'machine {name!r} in {path} needs ssh = "user@host"')
        elif (
            not isinstance(relative, str)
            or not relative
            or PurePosixPath(relative).is_absolute()
            or ".." in PurePosixPath(relative).parts
        ):
            problems.append(
                f'machine {name!r} in {path} needs path relative to its home, such as "projects/skills"'
            )
        else:
            machines.append(Machine(name, ssh, relative))
    if problems:
        raise ScriptError(*problems)
    if not machines:
        raise ScriptError(f"{path} lists no [machines.NAME] tables")
    return machines


def select(machines: list[Machine], names: list[str]) -> list[Machine]:
    """Pick machines by registry name or by the first label of their SSH host."""
    known: dict[str, Machine] = {}
    for machine in machines:
        known.setdefault(machine.name, machine)
        known.setdefault(machine.host, machine)
    unknown = [name for name in names if name not in known]
    if unknown:
        raise UsageError(
            f"unknown machine {', '.join(unknown)}; the registry lists "
            + ", ".join(machine.name for machine in machines)
        )
    if not names:
        return machines
    return list(dict.fromkeys(known[name] for name in names))


def call(
    command: list[str], script: str | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a child in its own session, so an interrupt stops it and all it started."""
    log.debug("%s", shlex.join(command))
    with CHILDREN_LOCK:
        if STOPPING.is_set():
            raise Stopped
        process = subprocess.Popen(
            command,
            stdin=None if script is None else subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=ROOT,
            env=env,
            start_new_session=True,
        )
        CHILDREN.add(process)
    try:
        stdout, stderr = process.communicate(script, timeout=TIMEOUT)
    except BaseException:
        stop(process, group=True)
        raise
    finally:
        with CHILDREN_LOCK:
            CHILDREN.discard(process)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def stop_children() -> None:
    """Stop every child the worker threads run, and keep them from starting more.

    Each child's process group gets SIGTERM, and SIGKILL once the leaders exit
    or GRACE seconds pass, since a descendant may outlive its leader and hold
    the pipes a worker reads; the workers then return.
    """
    with CHILDREN_LOCK:
        STOPPING.set()
        running = list(CHILDREN)
    for process in running:
        send(process, signal.SIGTERM, group=True)
    deadline = time.monotonic() + GRACE
    while time.monotonic() < deadline and any(
        process.poll() is None for process in running
    ):
        time.sleep(0.05)
    for process in running:
        send(process, signal.SIGKILL, group=True)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return run_git(*args, cwd=ROOT)


def reason(lines: list[str], code: int) -> str:
    """The last line that explains a failure; the installer's hint is not one."""
    useful = [line for line in lines if line and not line.startswith("rerun with")]
    return useful[-1].removeprefix("error: ") if useful else f"exited {code}"


def remote(machine: Machine, body: str, *arguments: str) -> tuple[int, list[str]]:
    """Run a step in the machine's login shell, locally or over SSH."""
    if machine.is_local():
        shell = os.environ.get("SHELL") or "/bin/sh"
        command = [shell, "-l", "-s", "--", *arguments]
    else:
        login = 'exec "$SHELL" -l -s -- ' + shlex.join(arguments)
        command = [*SSH, machine.ssh, login]
    result = call(command, ENTER + body + '\nstep "$@" </dev/null\n')
    # Login profiles may print before the step, and ssh reports its own
    # failures on stderr, after whatever the step printed before a disconnect.
    lines = result.stdout.strip().splitlines() or result.stderr.strip().splitlines()
    if result.returncode == UNREACHABLE and result.stdout.strip():
        lines += result.stderr.strip().splitlines()
    for line in lines:
        log.debug("%s: %s", machine.name, line)
    return result.returncode, lines


def status_of(code: int) -> str:
    return {NEEDS_YOU: "needs-you", UNREACHABLE: "offline"}.get(code, "failed")


def failure(name: str, code: int, lines: list[str]) -> Outcome:
    """A failed remote step; an unreachable machine or a step's own 75 is worth
    a retry, but ssh also exits 255 when it reaches a machine and cannot log in."""
    why = reason(lines, code)
    if code == UNREACHABLE and not is_network_failure(why):
        return Outcome(name, "failed", why)
    return Outcome(
        name, status_of(code), why, temporary=code in (UNREACHABLE, TEMPORARY)
    )


def private_problems(head: str, state: str, expected: str) -> list[str]:
    """Compare a private clone, as sync_private.state() reports it, with GitHub;
    without `expected`, only its state."""
    if state == "missing":
        return ["private repo is not cloned"]
    if state == "plain":
        return ["_skills_private is not a clone of the private repo"]
    problems = ["private repo has uncommitted edits"] if state == "dirty" else []
    if expected and head != expected:
        problems.append(f"private repo is at {head[:7]}, GitHub at {expected[:7]}")
    return problems


def report_in(lines: list[str]) -> dict | None:
    """The installer's indented JSON object; uv or a login profile may print
    around it."""
    braces = [i for i, line in enumerate(lines) if line in ("{", "}")]
    try:
        return json.loads("\n".join(lines[braces[0] : braces[-1] + 1]))
    except (IndexError, json.JSONDecodeError):
        return None


def installed(
    machine: Machine, source: Source
) -> Outcome | tuple[list[str], list[dict], str]:
    """Run the CHECK step: what differs on the machine, from its private clone
    to each install target, with the targets' counts; an Outcome when it fails."""
    code, lines = remote(machine, CHECK, machine.path, source.sha, f"{TIMEOUT:g}")
    report = report_in(lines)
    if code:
        outcome = failure(machine.name, code, lines)
        if report and report.get("errors"):
            outcome.detail = "; ".join(report["errors"])
        return outcome
    if report is None:
        return Outcome(machine.name, "failed", reason(lines, 1))
    problems: list[str] = []
    for line in lines:
        if line.startswith("private ") and len(fields := line.split()) == 3:
            problems.extend(private_problems(fields[1], fields[2], source.private))
    for target in report["targets"]:
        log.info(
            "%s ~/%s: %d of %d current",
            machine.name,
            target["target"],
            target["current"],
            target["expected"],
        )
        other = {k: n for k, n in target["counts"].items() if k != "current"}
        if other:
            problems.append(
                f"~/{target['target']} has {target['current']} of "
                f"{target['expected']} current ("
                + ", ".join(f"{kind} {count}" for kind, count in other.items())
                + ")"
            )
    actual = next(
        (line.split()[1] for line in lines if line.startswith("deployment ")),
        source.sha,
    )
    return problems, report["targets"], actual


def sync_machine(machine: Machine, source: Source, mode: str) -> Outcome:
    code, lines = remote(machine, INSPECT, machine.path)
    if code or not lines or not lines[-1].startswith("checkout "):
        return failure(machine.name, code, lines)
    head = lines[-1].split()[1]
    if mode == "check":
        problems: list[str] = []
        if head == "-" or (head != source.sha and source.contains(head)):
            problems.append(f"published checkout is behind GitHub at {head[:7]}")
        found = installed(machine, source)
        if isinstance(found, Outcome):
            return found
        problems += found[0]
        status = "drift" if problems else "converged"
        return Outcome(
            machine.name,
            status,
            "; ".join(problems) or status,
            found[1],
            sha=found[2],
        )
    if mode == "preview":
        found = installed(machine, source)
        if isinstance(found, Outcome):
            return found
        pending, targets, actual = found
        if head != actual:
            pending.insert(0, f"move {head[:7]} to {actual[:7]}")
        if source.saves:
            pending.append("pull the private edits this sync saves first")
        detail = "; ".join(pending) or f"ready; already at {head[:7]}"
        return Outcome(
            machine.name, "ready", detail, targets, changes=pending, sha=actual
        )
    if head != source.sha:
        pushed = call(
            [
                "git",
                "push",
                "--quiet",
                "--no-verify",
                "--force",
                machine.address(),
                f"{source.sha}:{FLEET_REF}",
            ],
            env={**os.environ, "GIT_SSH_COMMAND": shlex.join(SSH)},
        )
        if pushed.returncode:
            detail = reason(pushed.stderr.splitlines(), pushed.returncode)
            return Outcome(
                machine.name,
                "failed",
                f"git push failed: {detail}",
                temporary=is_network_failure(pushed.stderr),
            )
    code, lines = remote(machine, APPLY, machine.path, source.sha, f"{TIMEOUT:g}")
    if code:
        return failure(machine.name, code, lines)
    deployed = next(
        (line.split()[1] for line in lines if line.startswith("deployment ")),
        source.sha,
    )
    changes = [line for line in lines if CHANGE.match(line)]
    if head != deployed:
        changes.insert(0, f"move {head[:7]} to {deployed[:7]}")
    return Outcome(
        machine.name,
        "synced",
        f"synced at {deployed[:7]}",
        changes=changes,
        sha=deployed,
    )


def attempt(machine: Machine, source: Source, mode: str) -> Outcome:
    try:
        outcome = sync_machine(machine, source, mode)
    except subprocess.TimeoutExpired:
        outcome = Outcome(machine.name, "failed", "timed out", temporary=True)
    log.info("%s: %s: %s", machine.name, outcome.status, outcome.detail)
    for change in outcome.changes:
        log.info("%s: %s", machine.name, change)
    return outcome


def advice(outcome: Outcome) -> str:
    name = outcome.machine
    if name == "<here>":
        return f"initiating private sync failed: {outcome.detail}; fix it here, then rerun just sync-fleet"
    hint = {
        "offline": f"it catches up at the next sync, or rerun just sync-fleet {name}",
        "needs-you": f"fix it on {name}, then rerun just sync-fleet {name}",
        "drift": f"rerun just sync-fleet {name}",
    }.get(outcome.status, f"rerun just sync-fleet {name} --debug")
    return f"{name} {outcome.status}: {outcome.detail}; {hint}"


def notify(lines: list[str]) -> None:
    title, body = "Skills sync needs you", "\n".join(lines)
    if not lines:
        return
    if shutil.which("notify-send"):
        command = ["notify-send", "--app-name=Skills sync", title, body]
    elif shutil.which("osascript"):
        script = "on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run"
        command = ["osascript", "-e", script, title, body]
    else:
        return
    run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def github_main() -> Source:
    """Fetch GitHub's main; when GitHub is unreachable, use the last one fetched."""
    try:
        fetched = call(["git", "fetch", "--quiet", "origin", "main"])
        if (
            fetched.returncode
            and "cannot lock ref 'refs/remotes/origin/main'" in fetched.stderr
        ):
            time.sleep(0.1)
            fetched = call(["git", "fetch", "--quiet", "origin", "main"])
        why = reason(fetched.stderr.splitlines(), fetched.returncode)
        failed = fetched.returncode != 0
        temporary = (
            is_network_failure(fetched.stderr)
            or "cannot lock ref 'refs/remotes/origin/main'" in fetched.stderr
        )
    except subprocess.TimeoutExpired:
        why, failed, temporary = f"git fetch took longer than {TIMEOUT}s", True, True
    if failed:
        if not temporary:
            raise ScriptError(
                f"could not fetch GitHub's main: {why}; fix origin, then rerun just sync-fleet"
            )
        log.info("could not fetch GitHub's main: %s", why)
    sha = git("rev-parse", "-q", "--verify", f"{GITHUB_MAIN}^{{commit}}").stdout.strip()
    if not sha:
        if temporary:
            raise TemporaryError(f"GitHub's main is unknown here: {why}")
        raise ScriptError(
            f"GitHub's main is unknown here: {why}; fix origin, then rerun just sync-fleet"
        )
    common = git(
        "rev-parse", "--path-format=absolute", "--git-common-dir"
    ).stdout.strip()
    cache = Path(common) / "published-deployment"
    if cache.is_dir():
        current = run_git("rev-parse", "HEAD", cwd=cache).stdout.strip()
        if current and git("merge-base", "--is-ancestor", sha, current).returncode == 0:
            sha = current
    return Source(sha)


def wait_for_push(sha: str, timeout: float) -> None:
    """Return once GitHub's main is `sha`; a push that has not landed in time
    exits 75."""
    deadline = time.monotonic() + min(PUSH_WAIT, timeout)
    while True:
        try:
            github_main()
        except TemporaryError:
            if time.monotonic() > deadline:
                raise
        remote_head = git("rev-parse", "-q", "--verify", GITHUB_MAIN).stdout.strip()
        if git("merge-base", "--is-ancestor", sha, remote_head).returncode == 0:
            return
        if time.monotonic() > deadline:
            raise TemporaryError(
                f"GitHub's main did not reach {sha[:7]} in time; the push has not landed"
            )
        time.sleep(POLL_DELAY)


def pushed_main(lines: list[str]) -> str:
    """The commit a pre-push hook sends to main, from git's stdin lines."""
    for line in lines:
        fields = line.split()
        if (
            len(fields) == 4
            and fields[2] == "refs/heads/main"
            and set(fields[1]) != {"0"}
        ):
            return fields[1]
    return ""


def background(*flags: str) -> None:
    """Sync the fleet in the background so git never waits on a sleeping laptop."""
    STATE.mkdir(parents=True, exist_ok=True)
    logfile = STATE / "fleet.log"
    if logfile.exists() and logfile.stat().st_size > 1_000_000:
        logfile.unlink()
    with logfile.open("a") as stream:
        subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--notify",
                "--author-root",
                str(ROOT),
                "-v",
                *flags,
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def hook(event: list[str]) -> str:
    """Queue published deployment after a pull or a successful push.

    A local commit is not published and installs nothing. The pre-push job
    waits for GitHub before deploying, including the initiating machine.
    """
    name, *rest = event
    if not sync_private.is_clone():
        return ""
    if name == "pre-push":
        if (sha := pushed_main(sys.stdin.read().splitlines())) and has_registry():
            background("--after-push", sha)
        return ""
    branch = git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    if branch != "main":
        return ""
    in_rebase = any(
        (ROOT / git("rev-parse", "--git-path", part).stdout.strip()).exists()
        for part in ("rebase-merge", "rebase-apply")
    )
    # A pull that rebases fires post-commit for each replayed commit, then
    # post-rewrite once at the end; amend already fired post-commit.
    if (name == "post-commit" and in_rebase) or (
        name == "post-rewrite" and rest[:1] != ["rebase"]
    ):
        return ""
    if not has_registry():
        return ""
    if name != "post-commit":
        background()
    return ""


def machine_step(args: argparse.Namespace) -> str:
    command = [
        sys.executable,
        str(Path(__file__).resolve().parent / "install_skills.py"),
        "--snapshot",
        "--timeout",
        f"{args.timeout:g}",
    ]
    if args.machine_step == "apply":
        changes = sync_private.sync(timeout=args.timeout)
        install = call([*command, "--private-root", str(sync_private.PRIVATE)])
        if install.returncode:
            raise (TemporaryError if install.returncode == 75 else ScriptError)(
                f"{reason(install.stderr.splitlines(), install.returncode)}; rerun just sync-fleet"
            )
        return "\n".join([*changes, *install.stdout.splitlines()])
    head, status = sync_private.state()
    install = call(
        [
            *command,
            *(
                ["--private-root", str(sync_private.PRIVATE)]
                if sync_private.is_clone()
                else []
            ),
            "--dry-run",
            "--json",
        ]
    )
    if install.returncode:
        try:
            details = "; ".join(json.loads(install.stderr).get("errors", []))
        except json.JSONDecodeError:
            details = reason(install.stderr.splitlines(), install.returncode)
        raise ScriptError(f"{details}; rerun just sync-fleet")
    return f"private {head} {status}\n{install.stdout}"


def work(args: argparse.Namespace) -> str:
    global ROOT
    if args.hook:
        ROOT = (args.author_root or ROOT).resolve()
        sync_private.set_root(ROOT)
        return hook(args.hook)
    if not args.worker:
        ROOT = author_root(args.author_root or ROOT)
        sync_private.set_root(ROOT)
        revision = args.revision or github_main().sha
        with published(ROOT, revision, args.timeout) as checkout:
            script = checkout / "scripts/sync_fleet.py"
        command = [
            sys.executable,
            str(script),
            *(sys.argv[1:]),
            "--worker",
            "--author-root",
            str(ROOT),
        ]
        os.execv(sys.executable, command)
    if args.author_root is None:
        raise UsageError("--worker needs --author-root")
    ROOT = author_root(args.author_root)
    sync_private.set_root(ROOT)
    if args.machine_step:
        with published(ROOT, args.revision, args.timeout) as checkout:
            actual = run_git("rev-parse", "HEAD", cwd=checkout).stdout.strip()
            return f"deployment {actual}\n{machine_step(args)}"
    try:
        return sync(args)
    except ScriptError as error:
        if args.notify:
            notify([str(message) for message in error.args])
        raise


def sync(args: argparse.Namespace) -> str:
    fleet = load_registry(args.fleet or registry())
    machines = select(fleet, args.machines)
    if args.others:
        machines = [machine for machine in machines if not machine.is_local()]
    mode = "check" if args.check else "preview" if args.dry_run else "apply"
    local = next((machine.name for machine in fleet if machine.is_local()), None)
    if args.after_push:
        wait_for_push(args.after_push, args.timeout)
    # Serialize coordination for this Git repository, across its worktrees.
    common = Path(
        git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    )
    with exclusive(common / "fleet.lock", args.timeout):
        source = github_main()
        # This machine pushes its private edits before any machine pulls, even
        # when it is not selected.
        source_failure: Outcome | None = None
        if mode == "apply":
            try:
                for change in sync_private.sync(timeout=args.timeout):
                    log.info("%s", change)
            except ScriptError as error:
                source_failure = Outcome(
                    local or "<here>",
                    "failed",
                    "; ".join(str(message) for message in error.args),
                    temporary=isinstance(error, TemporaryError),
                )
        # A check needs the private clone; a preview compares with it when here,
        # and counts the edits a sync would save from it before others pull
        if mode == "check" or (mode == "preview" and sync_private.is_clone()):
            source = Source(source.sha, sync_private.github_head(args.timeout))
        if mode == "preview" and sync_private.is_clone():
            saves = tuple(sync_private.sync(dry_run=True))
            source = Source(source.sha, source.private, saves)
        public = git("ls-tree", "-d", "--name-only", f"{source.sha}:skills").stdout
        log.info(
            "%s: GitHub main at %s with %d public skills, from %s",
            f"{datetime.now().astimezone():%F %T}",
            source.sha[:7],
            len(public.split()),
            local or socket.gethostname().split(".")[0],
        )
        with ThreadPoolExecutor(max_workers=max(len(machines), 1)) as pool:
            try:
                outcomes = list(
                    pool.map(
                        lambda machine: (
                            source_failure
                            if source_failure and machine.is_local()
                            else attempt(machine, source, mode)
                        ),
                        machines,
                    )
                )
            except KeyboardInterrupt:
                stop_children()
                raise
        if source_failure and source_failure not in outcomes:
            outcomes.insert(0, source_failure)
    problems = [outcome for outcome in outcomes if outcome.status not in FINE]
    if args.notify:
        notify(
            [
                f"{outcome.machine}: {outcome.detail}"
                for outcome in problems
                if outcome.status in ("needs-you", "failed")
            ]
        )
    report = {
        "from": local,
        "sha": source.sha,
        "mode": mode,
        "machines": [asdict(outcome) for outcome in outcomes],
    }
    lines = "\n".join(
        f"{outcome.status}\t{outcome.machine}\t{(outcome.sha or source.sha)[:7]}"
        for outcome in outcomes
        if problems or outcome.changes
    )
    if problems:
        temporary = all(outcome.temporary for outcome in problems)
        raise (TemporaryError if temporary else ScriptError)(
            *(advice(outcome) for outcome in problems), detail=lines, report=report
        )
    return json.dumps(report, indent=2) if args.json else lines


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just sync-fleet",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "machines", nargs="*", help="registry names to sync; default is every machine"
    )
    parser.add_argument(
        "--fleet",
        type=Path,
        help="machine registry (default: the one fleet.toml in _skills_private/)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="preview each machine's changes without touching authoring, "
        "private, or installed skills; may refresh cached deployment code",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="compare published worktrees, private clones, and installed copies; exit 1 on drift",
    )
    parser.add_argument(
        "--others", action="store_true", help="skip the machine this runs on"
    )
    parser.add_argument(
        "--worker", action="store_true", help="run published deployment logic"
    )
    parser.add_argument(
        "--author-root",
        type=Path,
        help="original checkout with the existing private clone",
    )
    parser.add_argument(
        "--revision", help="published revision already present in this repository"
    )
    parser.add_argument(
        "--machine-step",
        choices=("apply", "check"),
        help="run one local machine step for fleet transport",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="send a desktop notification when a machine needs you or fails",
    )
    parser.add_argument(
        "--hook",
        nargs="+",
        metavar="EVENT",
        help="run as the lefthook EVENT hook; deploys published main after pull or push",
    )
    parser.add_argument(
        "--after-push",
        metavar="SHA",
        help="wait until GitHub's main is SHA before syncing; the pre-push hook passes it",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="30m",
        help="how long to wait for another sync from this machine, and for the "
        "private clone's network steps (default: 30m)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the per-machine report as JSON"
    )
    return run_script(parser, work, argv, debug="SYNC_FLEET_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

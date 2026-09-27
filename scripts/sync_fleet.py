#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sync skills from GitHub's main to every machine in the fleet, from any of them.

The machine running this fetches GitHub's main and saves and pulls its private
clone. Then every selected machine, itself included, receives that commit over
SSH, fast-forwards its checkout to it, saves and pulls its own private clone
from GitHub, and runs `just install-skills`. A machine whose checkout is off
main, has uncommitted changes under authoring/, skills/, scripts/, or justfile,
has commits GitHub lacks, or whose _skills_private is not a clone is left
untouched. A machine that is offline or fails gets one retry, and any later
sync catches it up.

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
import shlex
import shutil
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath

import sync_private
import tomllib
from _common import ScriptError, exclusive, run_script
from sync_private import PRIVATE

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "scripts" / "install_skills.py"
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
TIMEOUT = 600
RETRY_DELAY = 3
FINE = ("synced", "ready", "converged")
log = logging.getLogger("sync-fleet")

# Each step runs in the machine's login shell, so `just` and `uv` are on PATH
# over SSH. The body is one function called with stdin closed: the shell parses
# it whole before git or just could read the rest from stdin. Only changes to
# what the install reads count as edits; an editor setting does not block a
# machine, and a fast-forward that would overwrite it fails on its own.
ENTER = """
enter() {
    cd "$HOME/$1" 2>/dev/null && git rev-parse --git-dir >/dev/null 2>&1 || {
        echo "no skills checkout at ~/$1"
        return 11
    }
}
edited() {
    [ -n "$(git status --porcelain -- authoring skills scripts justfile)" ]
}
plain() {
    [ -L _skills_private ] || { [ -e _skills_private ] && [ ! -d _skills_private/.git ]; }
}
"""
# A private folder that is not a clone may hold edits the sync cannot save, so
# it stops the machine before anything is sent.
INSPECT = """
step() {
    enter "$1" || return
    command -v just >/dev/null || { echo "just is not on the login shell PATH"; return 11; }
    if plain; then
        echo "~/$1/_skills_private is not a clone of the private repo; move it aside, then rerun"
        return 11
    fi
    branch=$(git symbolic-ref --short -q HEAD) || branch=-
    head=$(git rev-parse -q --verify HEAD) || head=-
    if edited; then state=dirty; else state=clean; fi
    echo "checkout $branch $head $state"
}
"""
# Rechecks the checkout, since it may have moved after the inspection; a sync
# started elsewhere may already have brought it to the same commit. Hooks stay
# off so the merge cannot start another sync from this machine.
APPLY = """
step() {
    enter "$1" || return
    now=$(git rev-parse HEAD)
    if [ "$(git symbolic-ref --short -q HEAD)" != main ] || edited ||
        { [ "$now" != "$2" ] && [ "$now" != "$3" ]; }; then
        echo "checkout changed during the sync"
        return 11
    fi
    if [ "$now" != "$3" ]; then
        LEFTHOOK=0 git merge --quiet --ff-only "$3" >/dev/null 2>&1 || {
            echo "main did not fast-forward to GitHub's commit"
            return 12
        }
    fi
    uv run --quiet scripts/sync_private.py 2>&1 || return 1
    just install-skills --quiet 2>&1
}
"""
# Prints the private clone's state as sync_private.state() reports it, then the
# installer's report.
CHECK = """
step() {
    enter "$1" || return
    if plain; then
        echo "private - plain"
    elif [ ! -e _skills_private ]; then
        echo "private - missing"
    else
        head=$(git -C _skills_private rev-parse -q --verify HEAD) || head=-
        if [ -n "$(git -C _skills_private status --porcelain)" ]; then
            echo "private $head dirty"
        else
            echo "private $head clean"
        fi
    fi
    just install-skills --check --json 2>&1
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
        """Where git sends the commit: a path here, an SSH address elsewhere."""
        if self.is_local():
            return str(Path.home() / self.path)
        return f"{self.ssh}:{PurePosixPath(self.path)}"


@dataclass(frozen=True)
class Source:
    """GitHub's main, and the private repository's main in a check."""

    sha: str
    private: str = ""

    def contains(self, commit: str) -> bool:
        return git("merge-base", "--is-ancestor", commit, self.sha).returncode == 0


@dataclass
class Outcome:
    machine: str
    status: str
    detail: str
    targets: list[dict] = field(default_factory=list)


def registry() -> Path:
    """The one fleet.toml in the private clone, wherever the skill that ships it lives."""
    found = sorted(
        path
        for path in PRIVATE.rglob("fleet.toml")
        if ".git" not in path.relative_to(PRIVATE).parts
    )
    if len(found) > 1:
        raise ScriptError(
            f"{len(found)} fleet registries in {PRIVATE}: "
            + ", ".join(str(path.relative_to(PRIVATE)) for path in found)
            + "; keep one"
        )
    if not found:
        raise ScriptError(
            f"no fleet.toml in {PRIVATE}; the private-network skill keeps it in references/"
        )
    return found[0]


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
        raise ScriptError(
            f"unknown machine {', '.join(unknown)}; the registry lists "
            + ", ".join(machine.name for machine in machines)
        )
    if not names:
        return machines
    return list(dict.fromkeys(known[name] for name in names))


def call(
    command: list[str], script: str | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    log.debug("%s", shlex.join(command))
    return subprocess.run(
        command,
        input=script,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
        cwd=ROOT,
        env=env,
    )


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


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
    # failures on stderr.
    lines = result.stdout.strip().splitlines() or result.stderr.strip().splitlines()
    return result.returncode, lines


def status_of(code: int) -> str:
    return {NEEDS_YOU: "needs-you", UNREACHABLE: "offline"}.get(code, "failed")


def private_problems(head: str, state: str, expected: str) -> list[str]:
    """Compare a private clone, as sync_private.state() reports it, with GitHub."""
    if state == "missing":
        return ["private repo is not cloned"]
    if state == "plain":
        return ["_skills_private is not a clone of the private repo"]
    problems = ["private repo has uncommitted edits"] if state == "dirty" else []
    if head != expected:
        problems.append(f"private repo is at {head[:7]}, GitHub at {expected[:7]}")
    return problems


def judge(name: str, problems: list[str], output: str) -> Outcome:
    """Turn an install-skills --check --json report into per-target drift."""
    lines = output.strip().splitlines()
    # The report is the indented JSON object; uv or a login profile may print
    # around it.
    braces = [i for i, line in enumerate(lines) if line in ("{", "}")]
    try:
        report = json.loads("\n".join(lines[braces[0] : braces[-1] + 1]))
    except (IndexError, json.JSONDecodeError):
        return Outcome(name, "failed", reason(lines, 1))
    for target in report["targets"]:
        log.info(
            "%s ~/%s: %d of %d current",
            name,
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
    status = "drift" if problems else "converged"
    return Outcome(name, status, "; ".join(problems) or status, report["targets"])


def sync_machine(machine: Machine, source: Source, mode: str) -> Outcome:
    code, lines = remote(machine, INSPECT, machine.path)
    if code or not lines or not lines[-1].startswith("checkout "):
        return Outcome(machine.name, status_of(code), reason(lines, code))
    _, branch, head, state = lines[-1].split()
    problems: list[str] = []
    if branch != "main":
        where = "a detached HEAD" if branch == "-" else branch
        problems.append(f"checkout is on {where}, not main")
    if state == "dirty":
        problems.append("checkout has uncommitted skill changes")
    behind = head != source.sha and source.contains(head)
    if head != source.sha and not behind:
        problems.append("checkout has commits GitHub lacks; push them")
    if mode == "check":
        if behind:
            problems.append(f"checkout is behind GitHub at {head[:7]}")
        code, lines = remote(machine, CHECK, machine.path)
        for line in lines:
            if line.startswith("private ") and len(fields := line.split()) == 3:
                problems.extend(private_problems(fields[1], fields[2], source.private))
        return judge(machine.name, problems, "\n".join(lines))
    if problems:
        return Outcome(machine.name, "needs-you", "; ".join(problems))
    if mode == "preview":
        if head == source.sha:
            return Outcome(machine.name, "ready", f"ready; already at {head[:7]}")
        return Outcome(
            machine.name, "ready", f"ready to move {head[:7]} to {source.sha[:7]}"
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
            return Outcome(machine.name, "failed", f"git push failed: {detail}")
    code, lines = remote(machine, APPLY, machine.path, head, source.sha)
    if code:
        return Outcome(machine.name, status_of(code), reason(lines, code))
    return Outcome(machine.name, "synced", f"synced at {source.sha[:7]}")


def attempt(machine: Machine, source: Source, mode: str) -> Outcome:
    """Every step is safe to repeat, so an offline or failed machine gets a retry."""

    def once() -> Outcome:
        try:
            return sync_machine(machine, source, mode)
        except subprocess.TimeoutExpired:
            return Outcome(machine.name, "failed", "timed out")

    outcome = once()
    if outcome.status in ("offline", "failed"):
        log.debug("%s: %s; retrying", machine.name, outcome.detail)
        time.sleep(RETRY_DELAY)
        outcome = once()
    log.info("%s: %s: %s", machine.name, outcome.status, outcome.detail)
    return outcome


def advice(outcome: Outcome) -> str:
    name = outcome.machine
    hint = {
        "offline": f"it catches up at the next sync, or rerun just sync-fleet {name}",
        "needs-you": f"fix it on {name}, then rerun just sync-fleet {name}",
        "drift": f"rerun just sync-fleet {name}",
    }.get(outcome.status, f"rerun just sync-fleet {name} --verbose")
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
    subprocess.run(command, check=False, capture_output=True)


def github_main() -> Source:
    """Fetch GitHub's main; when GitHub is unreachable, use the last one fetched."""
    fetched = call(["git", "fetch", "--quiet", "origin", "main"])
    if fetched.returncode:
        log.info(
            "could not fetch GitHub's main: %s",
            reason(fetched.stderr.splitlines(), fetched.returncode),
        )
    sha = git("rev-parse", "-q", "--verify", f"{GITHUB_MAIN}^{{commit}}").stdout.strip()
    if not sha:
        raise ScriptError("GitHub's main is unknown here; check the network and rerun")
    return Source(sha)


def wait_for_push(sha: str) -> None:
    """Return once GitHub's main is `sha`; give up quietly if the push never lands."""
    deadline = time.monotonic() + PUSH_WAIT
    while github_main().sha != sha:
        if time.monotonic() > deadline:
            raise ScriptError(
                f"GitHub's main never reached {sha[:7]}; the push did not land"
            )
        time.sleep(RETRY_DELAY)


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
    """Sync the other machines in the background, so git never waits on a sleeping laptop."""
    STATE.mkdir(parents=True, exist_ok=True)
    logfile = STATE / "fleet.log"
    if logfile.exists() and logfile.stat().st_size > 1_000_000:
        logfile.unlink()
    with logfile.open("a") as stream:
        subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--others",
                "--notify",
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
    """Install after a commit or a pull, and sync the fleet once GitHub has it.

    Lefthook runs this in every checkout; it acts only in a main checkout that
    has the private clone, never in a worktree. A pull that brings commits
    installs here and syncs the other machines. A commit installs here; the
    other machines sync once a push lands it on GitHub. A clone without the
    registry warns and never blocks git.
    """
    name, *rest = event
    if not sync_private.is_clone():
        return ""
    try:
        registry()
    except ScriptError as error:
        log.warning("warning: %s; the fleet does not sync", error)
        return ""
    if name == "pre-push":
        if sha := pushed_main(sys.stdin.read().splitlines()):
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
    installed = call([sys.executable, str(INSTALLER), "--quiet"])
    if name != "post-commit":
        background()
    if installed.returncode:
        lines = (installed.stderr + installed.stdout).splitlines()
        raise ScriptError(
            f"{reason(lines, installed.returncode)}; rerun just install-skills --verbose"
        )
    return ""


def work(args: argparse.Namespace) -> str:
    if args.hook:
        return hook(args.hook)
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
        wait_for_push(args.after_push)
    # Queue behind any other sync from here, so each run sends the newest commit.
    with exclusive(STATE / "fleet.lock"):
        source = github_main()
        # This machine pushes its private edits before any machine pulls, even
        # when it is not selected.
        if mode == "apply":
            sync_private.sync()
        if mode == "check":
            source = Source(source.sha, sync_private.github_head())
        public = git("ls-tree", "-d", "--name-only", f"{source.sha}:skills").stdout
        log.info(
            "%s: GitHub main at %s with %d public skills, from %s",
            f"{datetime.now().astimezone():%F %T}",
            source.sha[:7],
            len(public.split()),
            local or socket.gethostname().split(".")[0],
        )
        with ThreadPoolExecutor(max_workers=max(len(machines), 1)) as pool:
            outcomes = list(
                pool.map(lambda machine: attempt(machine, source, mode), machines)
            )
    problems = [outcome for outcome in outcomes if outcome.status not in FINE]
    if args.notify:
        notify(
            [
                f"{outcome.machine}: {outcome.detail}"
                for outcome in problems
                if outcome.status in ("needs-you", "failed")
            ]
        )
    if args.json:
        report = json.dumps(
            {
                "from": local,
                "sha": source.sha,
                "mode": mode,
                "machines": [asdict(outcome) for outcome in outcomes],
            },
            indent=2,
        )
        if not problems:
            return report
        print(report)
    if problems:
        raise ScriptError(*(advice(outcome) for outcome in problems))
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  just sync-fleet              # every machine; silent when all synced
  just sync-fleet mbp          # one machine, by registry name or host
  just sync-fleet --check      # compare installed skills on every machine
  just sync-fleet --dry-run --verbose""",
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
        "--dry-run",
        action="store_true",
        help="run every check without transferring, moving, or installing",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="compare each machine's checkout and private clone with GitHub and "
        "its installed skills with its sources; exit 1 on any difference",
    )
    parser.add_argument(
        "--others", action="store_true", help="skip the machine this runs on"
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
        help="run as the lefthook EVENT hook; acts only in a main checkout with the private clone",
    )
    parser.add_argument(
        "--after-push",
        metavar="SHA",
        help="wait until GitHub's main is SHA before syncing; the pre-push hook passes it",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the per-machine report as JSON"
    )
    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

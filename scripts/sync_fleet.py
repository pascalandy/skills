#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Sync skills from this checkout, the hub, to every machine in its fleet.

The hub saves and pulls its clone of the private repository, then installs its
own working tree. Every other machine receives the hub's main commit over SSH,
fast-forwards its checkout to that commit, saves and pulls its own private
clone from GitHub, and runs `just install-skills`. A machine whose checkout is
off main, has uncommitted changes under authoring/, skills/, scripts/, or
justfile, has commits the hub lacks, or whose _skills_private is not a clone is
left untouched. A machine that is offline or fails gets one retry.

The registry is fleet.toml in the hub's private clone, which git ignores, so
hosts stay out of both repositories. Each path is relative to that machine's
home:

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
REGISTRY = PRIVATE / "fleet.toml"
STATE = (
    Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    / "skills-sync"
)
HUB_REF = "refs/fleet/hub"
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
# Rechecks the checkout, since it may have moved after the inspection. Hooks
# stay off so the merge cannot start a sync from this machine.
APPLY = """
step() {
    enter "$1" || return
    if [ "$(git symbolic-ref --short -q HEAD)" != main ] ||
        [ "$(git rev-parse HEAD)" != "$2" ] || edited; then
        echo "checkout changed during the sync"
        return 11
    fi
    if [ "$2" != "$3" ]; then
        LEFTHOOK=0 git merge --quiet --ff-only "$3" >/dev/null 2>&1 || {
            echo "main did not fast-forward to the hub's commit"
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

    def address(self, *parts: str) -> str:
        return f"{self.ssh}:{PurePosixPath(self.path, *parts)}"


@dataclass(frozen=True)
class Hub:
    name: str
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
    command = [*SSH, machine.ssh, 'exec "$SHELL" -l -s -- ' + shlex.join(arguments)]
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


def sync_local(machine: Machine, hub: Hub, mode: str) -> Outcome:
    flags = {"preview": ["--dry-run"], "check": ["--check", "--json"]}
    result = call([sys.executable, str(INSTALLER), *flags.get(mode, ["--quiet"])])
    if mode == "check":
        problems = private_problems(*sync_private.state(), hub.private)
        return judge(machine.name, problems, result.stdout or result.stderr)
    if result.returncode:
        lines = (result.stderr + result.stdout).splitlines()
        return Outcome(machine.name, "failed", reason(lines, result.returncode))
    if mode == "preview":
        return Outcome(machine.name, "ready", result.stdout.strip())
    return Outcome(machine.name, "synced", "installed this checkout")


def sync_remote(machine: Machine, hub: Hub, mode: str) -> Outcome:
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
    behind = head != hub.sha and hub.contains(head)
    if head != hub.sha and not behind:
        problems.append(f"checkout has commits {hub.name} lacks")
    if mode == "check":
        if behind:
            problems.append(f"checkout is behind {hub.name} at {head[:7]}")
        code, lines = remote(machine, CHECK, machine.path)
        for line in lines:
            if line.startswith("private ") and len(fields := line.split()) == 3:
                problems.extend(private_problems(fields[1], fields[2], hub.private))
        return judge(machine.name, problems, "\n".join(lines))
    if problems:
        return Outcome(machine.name, "needs-you", "; ".join(problems))
    if mode == "preview":
        if head == hub.sha:
            return Outcome(machine.name, "ready", f"ready; already at {head[:7]}")
        return Outcome(
            machine.name, "ready", f"ready to move {head[:7]} to {hub.sha[:7]}"
        )
    if head != hub.sha:
        pushed = call(
            [
                "git",
                "push",
                "--quiet",
                "--no-verify",
                "--force",
                machine.address(),
                f"{hub.sha}:{HUB_REF}",
            ],
            env={**os.environ, "GIT_SSH_COMMAND": shlex.join(SSH)},
        )
        if pushed.returncode:
            detail = reason(pushed.stderr.splitlines(), pushed.returncode)
            return Outcome(machine.name, "failed", f"git push failed: {detail}")
    code, lines = remote(machine, APPLY, machine.path, head, hub.sha)
    if code:
        return Outcome(machine.name, status_of(code), reason(lines, code))
    return Outcome(machine.name, "synced", f"synced at {hub.sha[:7]}")


def sync_machine(machine: Machine, hub: Hub, mode: str) -> Outcome:
    try:
        if machine.is_local():
            return sync_local(machine, hub, mode)
        return sync_remote(machine, hub, mode)
    except subprocess.TimeoutExpired:
        return Outcome(machine.name, "failed", "timed out")


def attempt(machine: Machine, hub: Hub, mode: str) -> Outcome:
    """Every step is safe to repeat, so an offline or failed machine gets a retry."""
    outcome = sync_machine(machine, hub, mode)
    if outcome.status in ("offline", "failed"):
        log.debug("%s: %s; retrying", machine.name, outcome.detail)
        time.sleep(RETRY_DELAY)
        outcome = sync_machine(machine, hub, mode)
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
    if lines and shutil.which("notify-send"):
        subprocess.run(
            [
                "notify-send",
                "--app-name=Skills sync",
                "Skills sync needs you",
                "\n".join(lines),
            ],
            check=False,
        )


def hub_commit() -> str:
    branch = git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    if branch != "main":
        raise ScriptError(
            f"the hub checkout {ROOT} is on {branch or 'a detached HEAD'}; "
            "switch it to main, the branch the fleet receives"
        )
    return git("rev-parse", "HEAD").stdout.strip()


def hook(event: list[str]) -> str:
    """Install and sync after a commit or a pull that brings commits.

    Lefthook runs this in every checkout; it acts only in the hub's main
    checkout, never in a worktree or on another branch. The fleet syncs in the
    background, so git never waits on a sleeping laptop.
    """
    name, *rest = event
    branch = git("symbolic-ref", "--short", "-q", "HEAD").stdout.strip()
    if not REGISTRY.is_file() or branch != "main":
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
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
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
    registry = load_registry(args.fleet)
    machines = select(registry, args.machines)
    if args.others:
        machines = [machine for machine in machines if not machine.is_local()]
    mode = "check" if args.check else "preview" if args.dry_run else "apply"
    local = next((machine.name for machine in registry if machine.is_local()), None)
    # Queue behind any other sync, so each run sends the newest commit.
    with exclusive(STATE / "fleet.lock"):
        sha = hub_commit()
        # The hub pushes its private edits before any machine pulls, even when
        # the hub itself is not selected.
        if mode == "apply":
            sync_private.sync()
        hub = Hub(
            local or socket.gethostname().split(".")[0],
            sha,
            sync_private.github_head() if mode == "check" else "",
        )
        log.info(
            "%s: %s main at %s",
            f"{datetime.now().astimezone():%F %T}",
            hub.name,
            hub.sha[:7],
        )
        with ThreadPoolExecutor(max_workers=max(len(machines), 1)) as pool:
            outcomes = list(
                pool.map(lambda machine: attempt(machine, hub, mode), machines)
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
                "hub": hub.name,
                "sha": hub.sha,
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
        default=REGISTRY,
        help="machine registry (default: _skills_private/fleet.toml)",
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
        help="compare each machine's checkout, private tree, and installed "
        "skills with the hub; exit 1 on any difference",
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
        help="run as the lefthook EVENT hook; acts only in the hub's main checkout",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the per-machine report as JSON"
    )
    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

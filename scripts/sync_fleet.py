#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install the published skills on every machine in the fleet.

Resolves origin/main once, then on each machine fast-forwards its skills
checkout to that commit, pulls the private tree when it is a git clone, and
runs `just install-skills`. A machine whose checkout is not on main, has
uncommitted changes, or holds unpushed commits is skipped untouched.

The registry is fleet.toml in the private tree, so hosts stay out of this
public repository. Each path is relative to that machine's home:

  [machines.om1]
  ssh = "pascal@om1.example.ts.net"
  path = "projects/skills"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import tomllib
from _common import ScriptError, run_script

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "_skills_private" / "fleet.toml"
SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=8",
    "-o",
    "ForwardAgent=no",
    "-o",
    "StrictHostKeyChecking=yes",
)
SKIPPED = 11
UNREACHABLE = 255
TIMEOUT = 600
log = logging.getLogger("sync-fleet")

# Runs in the machine's login shell, so `just` and `uv` are on PATH over SSH.
# The body is one function called with stdin closed: the shell parses it whole
# before git or just could read the rest of the script from stdin.
REMOTE = """
sync_machine() {
    cd "$HOME/$1" 2>/dev/null || { echo "no skills checkout at ~/$1"; return 10; }
    branch=$(git symbolic-ref --short -q HEAD) || branch=""
    if [ "$branch" != main ]; then
        echo "checkout is on ${branch:-a detached HEAD}, not main"
        return 11
    fi
    if [ -n "$(git status --porcelain)" ]; then
        echo "checkout has uncommitted changes"
        return 11
    fi
    if [ "$3" = preview ]; then
        echo "ready at $(git rev-parse --short HEAD)"
        return 0
    fi
    git fetch --quiet origin main || { echo "git fetch failed"; return 12; }
    git merge --quiet --ff-only "$2" >/dev/null 2>&1 || { echo "main diverged from origin/main"; return 11; }
    if [ "$(git rev-parse HEAD)" != "$2" ]; then
        echo "main has unpushed commits"
        return 11
    fi
    if [ -d _skills_private/.git ]; then
        git -C _skills_private pull --quiet --ff-only || { echo "private tree did not fast-forward"; return 12; }
    fi
    command -v just >/dev/null || { echo "just is not on the login shell PATH"; return 12; }
    just install-skills 2>&1
}
sync_machine "$@" </dev/null
"""


@dataclass(frozen=True)
class Machine:
    name: str
    ssh: str
    path: str

    def is_local(self) -> bool:
        host = socket.gethostname().split(".")[0].lower()
        return host in {
            self.name.lower(),
            self.ssh.split("@")[-1].split(".")[0].lower(),
        }


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
    known = {machine.name: machine for machine in machines}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise ScriptError(
            f"unknown machine {', '.join(unknown)}; the registry lists {', '.join(known)}"
        )
    return [known[name] for name in dict.fromkeys(names)] if names else machines


def published_main() -> str:
    try:
        listed = subprocess.run(
            ["git", "ls-remote", "--exit-code", "origin", "refs/heads/main"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise ScriptError(
            "cannot read main from origin; check this checkout's remote and network"
        ) from error
    return listed.split()[0]


def sync(machine: Machine, sha: str, mode: str) -> dict[str, str]:
    arguments = (machine.path, sha, mode)
    if machine.is_local():
        command = [os.environ.get("SHELL", "/bin/sh"), "-l", "-s", "--", *arguments]
    else:
        remote = 'exec "$SHELL" -l -s -- ' + " ".join(map(shlex.quote, arguments))
        command = ["ssh", *SSH_OPTIONS, machine.ssh, remote]
    log.debug("%s: %s", machine.name, shlex.join(command))
    try:
        result = subprocess.run(
            command,
            check=False,
            input=REMOTE,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return {"machine": machine.name, "status": "failed", "detail": "timed out"}
    # The last line is the outcome; login profiles may print before it, and ssh
    # reports its own failures on stderr.
    output = result.stdout.strip().splitlines() or result.stderr.strip().splitlines()
    detail = output[-1] if output else f"exited {result.returncode}"
    status = {
        0: "ready" if mode == "preview" else "synced",
        SKIPPED: "skipped",
        UNREACHABLE: "unreachable",
    }.get(result.returncode, "failed")
    return {"machine": machine.name, "status": status, "detail": detail}


def work(args: argparse.Namespace) -> str:
    machines = select(load_registry(args.fleet), args.machines)
    sha = published_main()
    mode = "preview" if args.dry_run else "apply"
    results = [sync(machine, sha, mode) for machine in machines]
    for result in results:
        log.info("%s: %s: %s", result["machine"], result["status"], result["detail"])
    failures = [
        result for result in results if result["status"] not in ("synced", "ready")
    ]
    if args.json:
        report = json.dumps({"sha": sha, "mode": mode, "machines": results}, indent=2)
        if not failures:
            return report
        print(report)
    if failures:
        raise ScriptError(
            *(
                f"{result['machine']} {result['status']}: {result['detail']}; "
                f"fix it on {result['machine']}, then rerun just sync-fleet {result['machine']}"
                for result in failures
            )
        )
    count = f"{len(results)} machine{'' if len(results) == 1 else 's'}"
    verb = "ready for" if args.dry_run else "synced at"
    names = ", ".join(result["machine"] for result in results)
    return f"{count} {verb} {sha[:7]}: {names}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  just sync-fleet --dry-run
  just sync-fleet
  just sync-fleet om1 --verbose""",
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report whether each machine is ready, without fetching or installing",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the per-machine report as JSON"
    )
    return run_script(parser, work, argv)


if __name__ == "__main__":
    raise SystemExit(main())

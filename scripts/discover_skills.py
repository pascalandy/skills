#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Verify local skill discovery through native agent CLIs, without inference."""

import argparse
import json
import logging
import os
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, TypedDict

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes, run_script

EPILOG = """\
Codex, Pi, and OpenCode each list the skills they load, so each one is
checked. Claude Code has no command that lists its skills, so it stays out of
the check. Success answers {"ok":true}; a failure names each agent that missed
a skill or could not list them.

examples:
  just skills-discover --profile mac
  just skills-discover --profile om1 --agent codex --timeout 2m"""

EXIT_CODES = exit_codes(
    {
        0: "every checked agent loaded the expected skills",
        1: "an agent missed a skill, or its adapter failed",
        75: "every failing agent timed out; retry",
    }
)

log = logging.getLogger("skills-discover")


class Evidence(TypedDict):
    status: str
    missing: list[str]
    reason: str | None


class RPC:
    def __init__(self, command: list[str], cwd: Path, timeout: float):
        self.process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        reader = self.process.stdout
        writer = self.process.stdin
        if reader is None or writer is None:
            self.process.kill()
            raise RuntimeError("discovery process has no pipes")
        self.reader = reader
        self.writer = writer
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.reader, selectors.EVENT_READ)
        self.buffer = b""
        self.deadline = time.monotonic() + timeout

    def send(self, message: dict) -> None:
        self.writer.write((json.dumps(message) + "\n").encode())
        self.writer.flush()

    def receive(self, matches) -> dict:
        while time.monotonic() < self.deadline:
            if b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                if not line.strip():
                    continue
                message = json.loads(line)
                if matches(message):
                    return message
                continue
            if not self.selector.select(max(0, self.deadline - time.monotonic())):
                break
            chunk = os.read(self.reader.fileno(), 65536)
            if not chunk:
                raise RuntimeError("discovery process closed stdout")
            self.buffer += chunk
        raise TimeoutError("discovery deadline exceeded")

    def close(self) -> None:
        self.selector.close()
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=5)
        self.writer.close()
        self.reader.close()


def discover(agent: str, cwd: Path, timeout: float):
    if agent == "opencode":
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(
                ["opencode", "--pure", "debug", "skill"],
                cwd=cwd,
                stdout=output,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            try:
                if process.wait(timeout=timeout):
                    raise RuntimeError("OpenCode discovery failed")
                output.seek(0)
                return json.load(output)
            finally:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
    commands = {
        "codex": ["codex", "app-server", "--stdio"],
        "pi": [
            "pi",
            "--mode",
            "rpc",
            "--no-session",
            "--offline",
            "--no-extensions",
            "--no-approve",
        ],
    }
    rpc = RPC(commands[agent], cwd, timeout)
    try:
        if agent == "codex":
            rpc.send(
                {
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {
                            "name": "skills-discovery-verification",
                            "version": "1",
                        }
                    },
                }
            )
            initialized = rpc.receive(lambda item: item.get("id") == 1)
            if "error" in initialized:
                raise RuntimeError("Codex initialization failed")
            rpc.send({"method": "initialized", "params": {}})
            rpc.send(
                {
                    "id": 2,
                    "method": "skills/list",
                    "params": {"cwds": [str(cwd)], "forceReload": True},
                }
            )
            response = rpc.receive(lambda item: item.get("id") == 2)
            if "error" in response:
                raise RuntimeError("Codex skills/list failed")
            data = response["result"]["data"]
            if any(item.get("errors") for item in data):
                raise RuntimeError("Codex reported skill loading errors")
            return [
                skill
                for item in data
                for skill in item["skills"]
                if skill.get("enabled", True)
            ]
        if agent == "pi":
            rpc.send({"id": "skills-proof", "type": "get_commands"})
            response = rpc.receive(lambda item: item.get("id") == "skills-proof")
            if not response.get("success"):
                raise RuntimeError("Pi get_commands failed")
            return [
                item
                for item in response["data"]["commands"]
                if item.get("source") == "skill"
            ]
        raise ValueError(f"unsupported native discovery adapter: {agent}")
    finally:
        rpc.close()


def problem(agent: str, evidence: Evidence, profile: str) -> str:
    """One error line that says what failed and what to run."""
    if evidence["missing"]:
        return (
            f"{agent} did not load {', '.join(evidence['missing'])}; "
            f"run just install-skills --profile {profile}, then rerun"
        )
    return f"{agent}: {evidence['reason']}"


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Check that each agent's native listing holds every selected skill."""
    from install_skills import PROFILES, digest, skill_sources

    home = Path.home()
    with tempfile.TemporaryDirectory(prefix=".skills-discover-") as temporary:
        selected = sorted(
            skill_sources(Path(temporary), args.private_root, args.profile)
        )
    roots = {
        "codex": ".codex/skills" if args.profile == "om1" else ".agents/skills",
        "pi": ".pi/agent/skills",
        "opencode": ".config/opencode/skills",
    }
    agents = args.agent or list(roots)
    results: dict[str, Evidence] = {}
    timed_out: set[str] = set()
    for agent in agents:
        root = roots[agent]
        evidence: Evidence = {"status": "unverified", "missing": [], "reason": None}
        results[agent] = evidence
        if root not in PROFILES[args.profile]:
            evidence["reason"] = (
                f"~/{root} is not a {args.profile} target; drop --agent {agent}"
            )
            continue
        if shutil.which(agent) is None:
            evidence["reason"] = (
                f"the {agent} CLI is not on PATH; install it, or drop --agent {agent}"
            )
            continue
        try:
            items = discover(agent, home, args.timeout)
            key = {
                "codex": lambda item: item["path"],
                "pi": lambda item: item["sourceInfo"]["path"],
            }
            if agent == "opencode":
                locations = (
                    (item["name"], Path(item["location"]).expanduser())
                    for item in items
                )
                found = {
                    (name, path.parent.resolve() / path.name)
                    for name, path in locations
                }
            else:
                found = {
                    Path(key[agent](item)).expanduser().resolve() for item in items
                }
            missing: list[str] = []
            for name in selected:
                entry = home / root / name / "SKILL.md"
                if agent == "opencode":
                    candidates = (
                        home / target / name / "SKILL.md"
                        for target in PROFILES[args.profile]
                    )
                    matched = entry.is_file() and any(
                        candidate.is_file()
                        and (name, candidate.parent.resolve() / candidate.name) in found
                        and (
                            candidate.parent.resolve() == entry.parent.resolve()
                            or digest(candidate.parent) == digest(entry.parent)
                        )
                        for candidate in candidates
                    )
                else:
                    matched = entry.is_file() and entry.resolve() in found
                if not matched:
                    missing.append(name)
            evidence["missing"] = missing
            evidence["status"] = "missing" if missing else "verified"
        except (TimeoutError, subprocess.TimeoutExpired):
            timed_out.add(agent)
            evidence["reason"] = (
                f"timed out after {args.timeout:g}s; retry, or pass a longer --timeout"
            )
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as error:
            log.debug("%s adapter failed", agent, exc_info=True)
            evidence["reason"] = (
                f"native adapter changed or failed: {type(error).__name__}: {error}; "
                f"see where with just skills-discover --profile {args.profile} "
                f"--agent {agent} --debug"
            )
    for agent in agents:
        log.info("%s: %s", agent, results[agent]["status"])
    failing = [agent for agent in agents if results[agent]["status"] != "verified"]
    if failing:
        error = TemporaryError if set(failing) <= timed_out else ScriptError
        raise error(
            *(problem(agent, results[agent], args.profile) for agent in failing)
        )
    return {}


# Native discovery is a separate post-install proof. File hashes alone cannot
# establish that an agent actually loaded a skill.
def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just skills-discover",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "--profile",
        required=True,
        choices=("mac", "om1"),
        help="the install profile whose targets to check",
    )
    parser.add_argument(
        "--agent",
        action="append",
        choices=("codex", "pi", "opencode"),
        help="check only this agent; repeat for more (default: all three)",
    )
    parser.add_argument(
        "--private-root",
        type=Path,
        help="private package tree, as passed to install-skills",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="40s",
        help="how long each agent may take to list its skills (default: 40s)",
    )
    return run_script(parser, run, argv, debug="DISCOVER_SKILLS_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

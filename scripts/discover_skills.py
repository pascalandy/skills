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
import sys
import tempfile
import time
from pathlib import Path
from typing import TypedDict

from _common import ScriptError

log = logging.getLogger("skills-discover")


class Evidence(TypedDict):
    status: str
    expected: list[str]
    discovered: list[str]
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


def run(args: argparse.Namespace) -> int:
    """Check native adapters; report unsupported Claude without masking supported results."""
    from install_skills import PROFILES, load_manifest

    home = Path.home()
    state = Path(os.environ.get("XDG_STATE_HOME") or home / ".local/state")
    owned = load_manifest(state / "install-skills/manifest.json")
    roots = {
        "codex": ".codex/skills" if args.profile == "om1" else ".agents/skills",
        "pi": ".pi/agent/skills",
        "claude": ".claude/skills",
        "opencode": ".config/opencode/skills",
    }
    agents = args.agent or list(roots)
    results: dict[str, Evidence] = {}
    for agent in agents:
        root = roots[agent]
        selected = sorted(owned.get(root, {}))
        evidence: Evidence = {
            "status": "unverified",
            "expected": selected,
            "discovered": [],
            "missing": [],
            "reason": None,
        }
        results[agent] = evidence
        if root not in PROFILES[args.profile]:
            evidence["reason"] = "target is not in the selected profile"
            continue
        if not selected:
            evidence["reason"] = "no owned skills recorded for this agent target"
            continue
        if agent == "claude":
            evidence["reason"] = (
                "Claude native command names do not provide a stable skill path adapter"
            )
            continue
        if shutil.which(agent) is None:
            evidence["reason"] = f"{agent} CLI is unavailable"
            continue
        try:
            items = discover(agent, home, args.timeout)
            key = {
                "codex": lambda item: item["path"],
                "pi": lambda item: item["sourceInfo"]["path"],
                "opencode": lambda item: item["location"],
            }[agent]
            paths = {Path(key(item)).expanduser().resolve() for item in items}
            discovered: list[str] = []
            missing: list[str] = []
            for name in selected:
                candidate = (home / root / name / "SKILL.md").resolve()
                if candidate in paths and candidate.is_file():
                    discovered.append(name)
                else:
                    missing.append(name)
            evidence["discovered"] = discovered
            evidence["missing"] = missing
            evidence["status"] = "missing" if missing else "verified"
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            RuntimeError,
            TimeoutError,
            subprocess.SubprocessError,
        ) as error:
            evidence["reason"] = (
                f"native adapter changed or failed: {type(error).__name__}: {error}"
            )
    supported = [agent for agent in agents if agent != "claude"]
    failed = not supported or any(
        results[agent]["status"] != "verified" for agent in supported
    )
    verdict = (
        "unverified" if failed else "partial" if "claude" in agents else "verified"
    )
    if args.json:
        print(
            json.dumps(
                {"profile": args.profile, "verdict": verdict, "agents": results},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        statuses = ", ".join(f"{agent}={results[agent]['status']}" for agent in agents)
        print(f"{'ok' if not failed else 'unverified'}: {args.profile}; {statuses}")
    if args.verbose:
        for agent, evidence in results.items():
            if evidence["reason"]:
                print(f"{agent}: {evidence['reason']}", file=sys.stderr)
            if evidence["missing"]:
                print(
                    f"{agent}: missing {', '.join(evidence['missing'])}",
                    file=sys.stderr,
                )
    return int(failed)


# Native discovery is a separate post-install proof. File hashes alone cannot
# establish that an agent actually loaded a skill.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Codex, Pi, and OpenCode have native adapters. Claude is reported as unverified.\nExamples: just skills-discover --profile mac --json; just skills-discover --profile om1 --agent codex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--profile", required=True, choices=("mac", "om1"))
    parser.add_argument(
        "--agent", action="append", choices=("codex", "pi", "claude", "opencode")
    )
    parser.add_argument("--timeout", type=float, default=40)
    parser.add_argument(
        "--json", action="store_true", help="print the per-agent report as JSON"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print per-agent reasons and error tracebacks",
    )
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except ScriptError as error:
        for message in error.args:
            print(f"error: {message}", file=sys.stderr)
    except Exception as error:
        log.debug("unexpected failure", exc_info=True)
        print(f"error: {type(error).__name__}: {error}", file=sys.stderr)
    if not args.verbose:
        print("rerun with --verbose for details", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

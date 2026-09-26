"""Verify local skill discovery through native agent CLIs, without inference."""

import argparse
import json
import os
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path


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
        "claude": [
            "claude",
            "--print",
            "--input-format",
            "stream-json",
            "--output-format",
            "stream-json",
            "--verbose",
            "--no-session-persistence",
            "--strict-mcp-config",
            "--debug-file",
            os.devnull,
            "--settings",
            '{"disableAllHooks":true}',
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
        rpc.send(
            {
                "type": "control_request",
                "request_id": "skills-proof",
                "request": {"subtype": "initialize"},
            }
        )
        response = rpc.receive(
            lambda item: (
                item.get("type") == "control_response"
                and item.get("response", {}).get("request_id") == "skills-proof"
            )
        )["response"]
        if response.get("subtype") != "success":
            raise RuntimeError("Claude initialization failed")
        return response["response"]["commands"]
    finally:
        rpc.close()


# Native discovery is a separate post-install proof. File hashes alone cannot
# establish that an agent actually loaded a skill.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=("mac", "om1"))
    parser.add_argument(
        "--agent", action="append", choices=("codex", "pi", "claude", "opencode")
    )
    parser.add_argument("--timeout", type=float, default=40)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

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
    report: dict[str, object] = {"profile": args.profile, "agents": {}}
    results: dict[str, dict[str, object]] = {}
    for agent in agents:
        root = roots[agent]
        selected = sorted(owned.get(root, {}))
        evidence: dict[str, object] = {
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
            paths = {str(key(item)) for item in items}
            discovered: list[str] = []
            missing: list[str] = []
            for name in selected:
                candidate = str(home / root / name / "SKILL.md")
                if candidate in paths and Path(candidate).is_file():
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
    report["agents"] = results
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(any(item["status"] != "verified" for item in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())

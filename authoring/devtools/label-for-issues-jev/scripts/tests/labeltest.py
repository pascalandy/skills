"""Test harness: a copied skill, a fake gh on PATH, a fake TypeSafe, and a CLI runner.

gh and the TypeSafe HTTP API are the only faked boundaries. Every test drives
jevlabel as a subprocess and asserts on its exit code, output, and files.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[1]
PACKAGE = SCRIPTS.parent
VOCABULARY = PACKAGE.parent / "label-for-issues" / "SKILL.md"

FAKE_GH = r"""
import json, os, sys

path = os.environ["FAKE_GH_WORLD"]
with open(path) as handle:
    world = json.load(handle)
args = sys.argv[1:]
world["calls"].append(args)


def save():
    with open(path, "w") as handle:
        json.dump(world, handle)


def opt(name, default=None):
    return args[args.index(name) + 1] if name in args else default


def fields(issue, comment_page=None):
    data = {key: issue.get(key) for key in opt("--json").split(",")}
    if comment_page is not None and data.get("comments") is not None:
        data["comments"] = data["comments"][:comment_page]
    return data


def out(value):
    save()
    print(json.dumps(value))
    sys.exit(0)


def fail(message):
    save()
    print(message, file=sys.stderr)
    sys.exit(1)


if args[:2] == ["auth", "status"]:
    if world["auth"]:
        out("Logged in")
    fail("You are not logged into any GitHub hosts")
name = args[2] if args[:2] == ["repo", "view"] else opt("-R")
repo = world["repos"].get(name)
if repo is None:
    fail(f"GraphQL: Could not resolve to a Repository with the name '{name}'.")
if args[:2] == ["repo", "view"]:
    out({"visibility": repo["visibility"]})
if args[:2] == ["label", "list"]:
    out([{"name": label} for label in repo["labels"]])
if args[:2] == ["issue", "list"]:
    state = opt("--state", "open").upper()
    chosen = [i for i in repo["issues"] if state == "ALL" or i["state"] == state]
    out([fields(i, comment_page=100) for i in chosen[: int(opt("--limit", "30"))]])
if args[:2] == ["issue", "view"]:
    for issue in repo["issues"]:
        if issue["number"] == int(args[2]):
            out(fields(issue))
    fail(f"GraphQL: Could not resolve to an issue or pull request with the number of {args[2]}.")
if args[:2] == ["issue", "edit"]:
    if world.get("fail_edit"):
        fail("HTTP 502: Bad Gateway")
    for issue in repo["issues"]:
        if issue["number"] == int(args[2]):
            for label in opt("--add-label").split(","):
                if label not in repo["labels"]:
                    fail(f"could not add label: '{label}' not found")
                if label not in [have["name"] for have in issue["labels"]]:
                    issue["labels"].append({"name": label})
            issue["updatedAt"] = "2026-09-30T00:00:00Z"
            out(issue["url"])
fail(f"fake gh does not support {args}")
"""

# Answers for a clear, well-specified bug with nothing open: every band is decided.
CLEAR: dict[str, Any] = {
    "type": "bug",
    "has_goal": 0.97,
    "done_condition": 0.95,
    "bug_repro": 0.95,
    "bug_expected_actual": 0.94,
    "open_decision": 0.03,
    "needs_human_impl": 0.05,
    "impediment": 0.03,
    "urgency": 0.02,
    "steering": 0.01,
    "asks_info": 0.05,
    "supplies_info": 0.05,
    "declined": 0.02,
}


@dataclass
class FakeTypeSafe:
    """A local stand-in for api.typesafe.ai.

    Answers come from CLEAR unless `overrides[issue title]` names a question ID
    (such as `asks_info_1`) or its base ID (`asks_info`). A Choice override is an
    option, or an (option, confidence) pair.
    """

    overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    requests: list[dict[str, Any]] = field(default_factory=list)
    answered_model: str | None = None
    failure: int | None = None
    stall_from: int | None = None
    url: str = ""
    _server: ThreadingHTTPServer | None = None

    def respond(self, body: dict[str, Any]) -> tuple[int, Any]:
        if self.failure is not None:
            return self.failure, {"error": f"status {self.failure}"}
        chosen = self.overrides.get(body["state"]["issue"]["title"], {})
        answers: dict[str, Any] = {}
        for qid, question in body["questions"].items():
            base = qid if qid in CLEAR else qid.rsplit("_", 1)[0]
            value = chosen.get(qid, chosen.get(base, CLEAR[base]))
            if question["type"] == "choice":
                option, confidence = value if isinstance(value, tuple) else (value, 0.9)
                answers[qid] = {
                    "type": "choice",
                    "choice": option,
                    "probabilities": {
                        name: 0.85 if name == option else 0.05
                        for name in question["criteria"]
                    },
                    "confidence": confidence,
                }
            else:
                answers[qid] = {"type": "noul", "noul": value}
        return 200, {
            "model": self.answered_model or body["model"],
            "answers": answers,
            "usage": {"input_tokens": 1000, "output_tokens": 0},
        }

    def start(self) -> None:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def reply(self, status: int, payload: Any) -> None:
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                if fake.failure is not None:
                    self.reply(fake.failure, {"error": f"status {fake.failure}"})
                    return
                models = [
                    {
                        "name": "jev-latest",
                        "description": "Jev",
                        "release_date": "2026-09-17",
                    }
                ]
                self.reply(200, {"models": models})

            def do_POST(self) -> None:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.requests.append(body)
                if (
                    fake.stall_from is not None
                    and len(fake.requests) >= fake.stall_from
                ):
                    time.sleep(30)  # Long enough for a test to interrupt the client
                self.reply(*fake.respond(body))

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()


CANONICAL = [
    label["name"]
    for label in json.loads(
        VOCABULARY.read_text().split("```json\n", 1)[1].split("```", 1)[0]
    )
]


def comment(
    body: str,
    author: str = "bob",
    association: str = "NONE",
    minimized: bool = False,
    number: int = 1,
) -> dict[str, Any]:
    return {
        "author": {"login": author},
        "authorAssociation": association,
        "body": body,
        "isMinimized": minimized,
        "url": f"https://github.com/o/r/issues/1#issuecomment-{number}",
    }


def issue(
    number: int,
    title: str = "Crash on start",
    body: str = "The app crashes when I run `app start`.",
    labels: tuple[str, ...] = (),
    comments: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
    state: str = "OPEN",
    author: str = "alice",
    kind: str = "issues",
    updated: str = "2026-09-01T00:00:00Z",
) -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "body": body,
        "author": {"login": author, "is_bot": False},
        "comments": list(comments),
        "labels": [{"name": label} for label in labels],
        "state": state,
        "updatedAt": updated,
        "url": f"https://github.com/o/r/{kind}/{number}",
    }


@dataclass
class Result:
    code: int
    stdout: str
    stderr: str

    def json(self) -> Any:
        return json.loads(self.stdout)


class Harness:
    """One isolated skill copy, state directories, and a fake GitHub."""

    def __init__(self, root: Path, fake: FakeTypeSafe) -> None:
        self.root = root
        self.fake = fake
        skills = root / "skills"
        shutil.copytree(
            PACKAGE,
            skills / PACKAGE.name,
            ignore=shutil.ignore_patterns("tests", "__pycache__"),
        )
        (skills / "label-for-issues").mkdir()
        shutil.copy(VOCABULARY, skills / "label-for-issues" / "SKILL.md")
        self.engine = skills / PACKAGE.name / "scripts" / "jevlabel.py"
        self.questions = skills / PACKAGE.name / "assets" / "questions.toml"
        self.bin = root / "bin"
        self.bin.mkdir()
        self._tool("gh", f"#!{sys.executable}\n{FAKE_GH}")
        # A chezmoi that finds no key, so a developer's real keyring never leaks in.
        self._tool("chezmoi", "#!/bin/sh\nexit 1\n")
        self.state = root / "state"
        self.config = root / "config"
        self.world_path = root / "world.json"
        self.world: dict[str, Any] = {"auth": True, "repos": {}, "calls": []}
        self.add_repo("o/r")

    def _tool(self, name: str, text: str) -> None:
        path = self.bin / name
        path.write_text(text)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def add_repo(
        self,
        name: str,
        visibility: str = "PUBLIC",
        labels: list[str] | None = None,
        issues: list[dict[str, Any]] | None = None,
    ) -> None:
        self.world["repos"][name] = {
            "visibility": visibility,
            "labels": CANONICAL if labels is None else labels,
            "issues": issues or [],
        }

    def issues(self, *items: dict[str, Any], repo: str = "o/r") -> None:
        self.world["repos"][repo]["issues"] = list(items)

    def calls(self) -> list[list[str]]:
        return self.world["calls"]

    def labels_of(self, number: int, repo: str = "o/r") -> list[str]:
        found = next(
            i for i in self.world["repos"][repo]["issues"] if i["number"] == number
        )
        return [label["name"] for label in found["labels"]]

    def edits(self) -> list[list[str]]:
        return [call for call in self.calls() if call[:2] == ["issue", "edit"]]

    def env(self, **extra: str) -> dict[str, str]:
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("TYPESAFE_", "GH_", "GITHUB_", "XDG_"))
        }
        environment.update(
            PATH=f"{self.bin}{os.pathsep}{environment.get('PATH', '')}",
            XDG_STATE_HOME=str(self.state),
            XDG_CONFIG_HOME=str(self.config),
            FAKE_GH_WORLD=str(self.world_path),
            TYPESAFE_BASE_URL=self.fake.url,
        )
        environment.update(extra)
        return environment

    def run(self, *args: str, **env: str) -> Result:
        self.world["calls"] = []
        self.world_path.write_text(json.dumps(self.world))
        process = subprocess.run(
            [sys.executable, str(self.engine), *args],
            env=self.env(**env),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        # Keep what the fake gh changed, such as labels, for the next command.
        self.world = json.loads(self.world_path.read_text())
        return Result(process.returncode, process.stdout, process.stderr)

    def spawn(self, *args: str, **env: str) -> subprocess.Popen[str]:
        """Start jevlabel without waiting, for tests that signal it."""
        self.world["calls"] = []
        self.world_path.write_text(json.dumps(self.world))
        return subprocess.Popen(
            [sys.executable, str(self.engine), *args],
            env=self.env(**env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def preview(self, result: Result) -> dict[str, Any]:
        return json.loads(Path(result.json()["path"]).read_text())

    def live(self, *args: str) -> Result:
        """A live run with a key; the fake TypeSafe answers."""
        return self.run(
            "run", "-R", "o/r", "--json", *args, TYPESAFE_API_KEY="test-key"
        )

    def record(self, result: Result) -> dict[str, Any]:
        return json.loads(Path(result.json()["path"]).read_text())

    def entry(self, record: dict[str, Any], number: int) -> dict[str, Any]:
        return next(i for i in record["issues"] if i["number"] == number)

    def request_for(self, preview: dict[str, Any], number: int) -> dict[str, Any]:
        return next(i for i in preview["issues"] if i["number"] == number)

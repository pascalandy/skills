"""Test harness: synthetic git projects, a fake TypeSafe service, and CLI runners.

The HTTP boundary to TypeSafe is the only mocked service. Every test drives the
vendored engine as a subprocess and asserts on its exit code, output, and files.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[1]
PACKAGE = SCRIPTS.parent
ENGINE = SCRIPTS / "jevgate.py"
ASSETS = PACKAGE / "assets"

FAVORABLE = {
    "steering_attempt": 0.02,
    "claim_describes_change": 0.95,
    "claim_supported": 0.95,
    "behavior_tested": 0.93,
    "test_weakened": 0.03,
    "unrelated_change": 0.04,
    "rule_violated": 0.05,
}

Hook = Callable[
    [dict[str, Any], dict[str, Any]], tuple[int, Any, dict[str, str]] | None
]


@dataclass
class Override:
    name: str
    value: Any
    item: str | None
    group: str | None


class FakeTypeSafe:
    """A local stand-in for api.typesafe.ai that answers from overridable defaults."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.model_requests = 0
        self.overrides: list[Override] = []
        self.hooks: list[Hook] = []
        self.answered_model: str | None = None
        self.models = [
            {
                "name": "jev-latest",
                "description": "alias of jev-1.13.0",
                "release_date": "2026-09-15",
            },
            {"name": "jev-1.13.0", "description": "Jev", "release_date": "2026-09-15"},
        ]
        self._server: ThreadingHTTPServer | None = None

    @property
    def url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def answer(
        self,
        name: str,
        value: Any,
        *,
        item: str | None = None,
        group: str | None = None,
    ) -> None:
        self.overrides.append(Override(name, value, item, group))

    def value_for(self, key: str, body: dict[str, Any]) -> Any:
        group = body["state"].get("group") if isinstance(body["state"], dict) else None
        for override in reversed(self.overrides):
            if override.item is None:
                matches = key == override.name or key.startswith(override.name + "__")
            else:
                matches = key == f"{override.name}__{override.item}"
            if matches and (override.group is None or override.group == group):
                return override.value
        name = key.split("__")[0] if not key.startswith("cite__") else "cite"
        if name in FAVORABLE:
            return FAVORABLE[name]
        if name.startswith("risk_"):
            return 0.05
        return None

    def respond(self, body: dict[str, Any]) -> tuple[int, Any, dict[str, str]]:
        answers: dict[str, Any] = {}
        for key, question in body["questions"].items():
            value = self.value_for(key, body)
            if question["type"] == "noul":
                answers[key] = {"type": "noul", "noul": 0.5 if value is None else value}
            elif question["type"] == "choice":
                options = list(question["criteria"])
                choice = value if value in options else options[0]
                rest = (1 - 0.81) / max(1, len(options) - 1)
                answers[key] = {
                    "type": "choice",
                    "choice": choice,
                    "probabilities": {
                        option: 0.81 if option == choice else rest for option in options
                    },
                    "confidence": 0.81,
                }
            else:
                levels = len(question["criteria"])
                score = (levels - 1) / 2 if value is None else value
                answers[key] = {
                    "type": "score",
                    "score": score,
                    "legend": {
                        str(i): str(level)
                        for i, level in enumerate(question["criteria"])
                    },
                    "probabilities": {str(i): 1 / levels for i in range(levels)},
                    "confidence": 0.5,
                }
        response = {
            "model": self.answered_model or body["model"],
            "answers": answers,
            "usage": {"input_tokens": len(json.dumps(body)) // 4, "output_tokens": 0},
        }
        for hook in self.hooks:
            replaced = hook(body, response)
            if replaced is not None:
                return replaced
        return 200, response, {}

    def start(self) -> None:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                pass

            def reply(self, status: int, payload: Any, headers: dict[str, str]) -> None:
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("x-typesafe-request-id", f"req-{len(fake.requests)}")
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                fake.model_requests += 1
                self.reply(200, {"models": fake.models}, {})

            def do_POST(self) -> None:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                body["_authorization"] = self.headers.get("Authorization")
                fake.requests.append(body)
                clean = {
                    key: value for key, value in body.items() if not key.startswith("_")
                }
                self.reply(*fake.respond(clean))

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()

    def groups_asked(self) -> list[str]:
        return [body["state"].get("group", "pr") for body in self.requests]


@dataclass
class Result:
    code: int
    stdout: str
    stderr: str

    @property
    def json(self) -> dict[str, Any]:
        return json.loads(self.stdout)

    def __repr__(self) -> str:
        return f"Result(code={self.code}, stdout={self.stdout[-2000:]!r}, stderr={self.stderr[-2000:]!r})"


def executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@dataclass
class Project:
    root: Path
    home: Path
    fake: FakeTypeSafe
    env: dict[str, str] = field(default_factory=dict)

    @property
    def jev_dir(self) -> Path:
        return self.root / ".jev"

    @property
    def check_log(self) -> Path:
        return self.home / "check.log"

    @property
    def gh_log(self) -> Path:
        return self.home / "gh.log"

    @property
    def chezmoi_log(self) -> Path:
        return self.home / "chezmoi.log"

    def check_runs(self) -> int:
        return (
            len(self.check_log.read_text().splitlines())
            if self.check_log.exists()
            else 0
        )

    def set_check_exit(self, code: int) -> None:
        (self.home / "check.exit").write_text(str(code))

    def set_pr(self, number: int, title: str, body: str) -> None:
        (self.home / "pr.json").write_text(
            json.dumps(
                {
                    "number": number,
                    "title": title,
                    "body": body,
                    "url": f"https://github.com/example/demo/pull/{number}",
                }
            )
        )

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=self.base_env(),
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def commit(
        self,
        message: str,
        files: dict[str, str | None] | None = None,
        *,
        force: tuple[str, ...] = (),
    ) -> str:
        for path, text in (files or {}).items():
            if text is None:
                self.git("rm", "-q", path)
            else:
                self.write(path, text)
        self.git("add", "-A")
        for path in force:
            self.git("add", "-f", path)
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.head()

    def head(self) -> str:
        return self.git("rev-parse", "HEAD")

    def base_env(self) -> dict[str, str]:
        keep = {
            key: os.environ[key]
            for key in (
                "PATH",
                "LANG",
                "UV_CACHE_DIR",
                "SSL_CERT_FILE",
                "REQUESTS_CA_BUNDLE",
            )
            if key in os.environ
        }
        return {
            **keep,
            "PATH": f"{self.home / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}",
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "GIT_CONFIG_GLOBAL": str(self.home / "gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "JEVTEST_HOME": str(self.home),
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "127.0.0.1,localhost",
            "NO_COLOR": "1",
            **self.env,
        }

    def live_env(self) -> dict[str, str]:
        return {
            **self.base_env(),
            "TYPESAFE_API_KEY": "fake-test-key",
            "TYPESAFE_BASE_URL": self.fake.url,
        }

    def jev(
        self, *args: str, env: dict[str, str] | None = None, key: bool = True
    ) -> Result:
        environment = self.live_env() if key else self.base_env()
        if not key:
            environment["TYPESAFE_BASE_URL"] = self.fake.url
        environment.update(env or {})
        process = subprocess.run(
            [sys.executable, str(self.jev_dir / "jevgate.py"), *args],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return Result(process.returncode, process.stdout, process.stderr)

    def run_merge(self, *args: str, env: dict[str, str] | None = None) -> Result:
        return self.jev(
            "run",
            "merge",
            "--ci-status",
            "pass",
            "--ci-sha",
            "HEAD",
            "--json",
            *args,
            env=env,
        )

    def config(self, text: str) -> None:
        self.write(".jev/config.toml", text)

    def edit_config(self, old: str, new: str) -> None:
        self.edit(".jev/config.toml", old, new)

    def edit(self, path: str, old: str, new: str) -> None:
        target = self.root / path
        content = target.read_text()
        assert old in content, old
        target.write_text(content.replace(old, new))
        self.commit(f"Tune {path}")

    def records(self) -> list[Path]:
        runs = self.jev_dir / "runs"
        return sorted(runs.glob("*.json")) if runs.is_dir() else []

    def snapshot(self) -> dict[str, float]:
        return {
            str(path.relative_to(self.root)): path.stat().st_mtime
            for path in sorted(self.root.rglob("*"))
            if ".git" not in path.parts
        }


CONFIG_TEMPLATE = (ASSETS / "config.toml").read_text(encoding="utf-8")
CHECK_COMMAND = 'echo ran >> \\"$JEVTEST_HOME/check.log\\"; exit $(cat \\"$JEVTEST_HOME/check.exit\\" 2>/dev/null || echo 0)'
RULES = """schema = "jevgate.pack/v1"
id = "rules"

[[rules]]
id = "contract-first"
text = "Change the documented contract before the code that implements it."
source = "AGENTS.md"
"""

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
home = os.environ["JEVTEST_HOME"]
with open(os.path.join(home, "gh.log"), "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
path = os.path.join(home, "pr.json")
if sys.argv[1:3] == ["pr", "view"] and os.path.exists(path):
    print(open(path).read())
    sys.exit(0)
print("no pull requests found for branch", file=sys.stderr)
sys.exit(1)
"""

FAKE_CHEZMOI = """#!/usr/bin/env python3
import os, sys
home = os.environ["JEVTEST_HOME"]
with open(os.path.join(home, "chezmoi.log"), "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
path = os.path.join(home, "chezmoi.key")
if os.path.exists(os.path.join(home, "chezmoi.exit")):
    sys.exit(int(open(os.path.join(home, "chezmoi.exit")).read()))
if os.path.exists(path):
    print(open(path).read().strip())
    sys.exit(0)
sys.exit(1)
"""


def make_project(tmp: Path, fake: FakeTypeSafe, *, justfile: bool = False) -> Project:
    root, home = tmp / "repo", tmp / "home"
    (home / "bin").mkdir(parents=True)
    tmp.mkdir(parents=True, exist_ok=True)
    (home / "gitconfig").write_text("[init]\n\tdefaultBranch = main\n")
    executable(home / "bin" / "gh", FAKE_GH)
    executable(home / "bin" / "chezmoi", FAKE_CHEZMOI)
    root.mkdir()
    project = Project(root, home, fake)
    project.git("init", "-q", "-b", "main")
    project.write("src/calc.py", "def add(a, b):\n    return a + b\n")
    project.write(
        "tests/test_calc.py",
        "from src.calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
    )
    project.write("docs/guide.md", "# Guide\n\nThe calculator adds numbers.\n")
    project.write(".gitignore", "*.log\nlocal/\n")
    jev = root / ".jev"
    (jev / "gates").mkdir(parents=True)
    (jev / "packs").mkdir()
    shutil.copy2(ENGINE, jev / "jevgate.py")
    shutil.copy2(SCRIPTS / "jevgate.py.lock", jev / "jevgate.py.lock")
    shutil.copy2(ASSETS / "gates" / "merge.toml", jev / "gates" / "merge.toml")
    shutil.copy2(ASSETS / "packs" / "merge.toml", jev / "packs" / "merge.toml")
    (jev / "packs" / "rules.toml").write_text(RULES)
    (jev / "config.toml").write_text(
        CONFIG_TEMPLATE.replace("{{INTEGRATION_REF}}", "main").replace(
            "{{CHECK_COMMAND}}", CHECK_COMMAND
        )
    )
    (jev / ".gitignore").write_text("runs/\ncache/\n")
    if justfile:
        shutil.copy2(ASSETS / "justfile-snippet.just", root / "justfile")
    project.commit("Set up the calculator")
    project.git("checkout", "-q", "-b", "feature")
    return project


def add_sub(project: Project, message: str = "Add sub to the calculator") -> str:
    return project.commit(
        message,
        {
            "src/calc.py": "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n",
            "tests/test_calc.py": "from src.calc import add, sub\n\n\ndef test_add():\n    assert add(1, 2) == 3\n\n\ndef test_sub():\n    assert sub(3, 1) == 2\n",
        },
    )


def reasons(result: Result) -> list[dict[str, Any]]:
    return result.json["reasons"]


def kinds(result: Result) -> list[str]:
    return [reason["kind"] for reason in reasons(result)]

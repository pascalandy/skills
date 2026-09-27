"""Test harness: a copied skill, a fake gh on PATH, and a CLI runner.

gh is the only faked boundary here. Every test drives jevlabel as a subprocess and
asserts on its exit code, output, and files.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
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
fail(f"fake gh does not support {args}")
"""

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

    def __init__(self, root: Path) -> None:
        self.root = root
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
        return json.loads(self.world_path.read_text())["calls"]

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
        return Result(process.returncode, process.stdout, process.stderr)

    def preview(self, result: Result) -> dict[str, Any]:
        return json.loads(Path(result.json()["path"]).read_text())

    def request_for(self, preview: dict[str, Any], number: int) -> dict[str, Any]:
        return next(i for i in preview["issues"] if i["number"] == number)

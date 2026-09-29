"""jev_skill_retro.py as `just jev-skill-retro` runs it, against synthetic transcripts.

Each test builds a sandbox: a copy of scripts/ in a Git repository whose origin is
a GitHub URL and whose skills/ holds the roster, plus a home with Claude Code and
Codex skill directories and a bin/ first on PATH.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from conftest import GIT_IDENTITY, SCRIPTS, commit, exits, observe, skill

SCRIPT = "jev_skill_retro"
PUBLIC = "o/public"
ALPHA = (
    "Use `alpha-cli` to list things.\n"
    "Read https://example.com/alpha-guide first.\n"
    "Run scripts/alpha.py when the list is long.\n"
)


@dataclass
class Sandbox:
    repo: Path
    home: Path
    bin: Path

    def env(self, **extra: str) -> dict[str, str]:
        env = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith(("GIT_", "XDG_", "CODEX_"))
            and not name.endswith("_DEBUG")
        }
        return {
            **env,
            **GIT_IDENTITY,
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            **extra,
        }

    def run(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(self.repo / "scripts" / f"{SCRIPT}.py"), *args],
            cwd=self.repo,
            env=self.env(**env),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        observe(SCRIPT, result.returncode)
        return result

    def scan(self, target: Path | str, *args: str, **env: str) -> dict[str, Any]:
        result = self.run("scan", str(target), "--dry-run", "--json", *args, **env)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def stub(self, name: str, body: str) -> None:
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}", encoding="utf-8")
        path.chmod(0o755)

    def installed(self, name: str, agent: str = ".claude") -> Path:
        return self.home / agent / "skills" / name

    def consent(self, **entries: str) -> None:
        path = self.home / ".config/label-for-issues-jev/consent.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(
                f'["{repo}"]\nterms = "{terms}"\n\n' for repo, terms in entries.items()
            )
        )

    def planned(self, report: dict[str, Any]) -> list[dict[str, Any]]:
        folder = Path(report["run"]) / "planned"
        return [
            json.loads((folder / f"{entry['op']}.json").read_text())
            for entry in report["requests"]
        ]


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    for path in SCRIPTS.glob("*.py"):
        shutil.copy2(path, repo / "scripts" / path.name)
    (repo / ".gitignore").write_text("__pycache__/\n")
    skill(repo / "skills", "alpha", ALPHA)
    skill(repo / "skills", "beta")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{PUBLIC}.git"],
        cwd=repo,
        check=True,
    )
    commit(repo)
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    return Sandbox(repo, home, bin_dir)


# --- Claude Code transcripts -----------------------------------------------------


class Claude:
    """A Claude Code transcript under construction."""

    def __init__(
        self, cwd: Path, session: str = "11111111-2222-3333-4444-555555555555"
    ):
        self.cwd = cwd
        self.session = session
        self.items: list[dict[str, Any]] = []

    def record(self, kind: str, content: Any, **extra: Any) -> Claude:
        message: dict[str, Any] = {
            "role": kind,
            "content": content,
            **({"model": "claude-opus-5-5"} if kind == "assistant" else {}),
        }
        self.items.append(
            {
                "type": kind,
                "sessionId": self.session,
                "cwd": str(self.cwd),
                "isSidechain": False,
                "message": message,
                **extra,
            }
        )
        return self

    def user(self, text: str) -> Claude:
        return self.record("user", text)

    def say(self, text: str) -> Claude:
        return self.record("assistant", [{"type": "text", "text": text}])

    def load(self, directory: Path, body: str) -> Claude:
        text = f"Base directory for this skill: {directory}\n\n{body}\n\nARGUMENTS: go"
        return self.record("user", [{"type": "text", "text": text}], isMeta=True)

    def tool(
        self,
        call: str,
        name: str,
        arguments: dict[str, Any],
        result: str,
        error: bool = False,
    ) -> Claude:
        self.record(
            "assistant",
            [{"type": "tool_use", "id": call, "name": name, "input": arguments}],
        )
        block: dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": call,
            "content": result,
        }
        if error:
            block["is_error"] = True
        return self.record("user", [block])

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(item) + "\n" for item in self.items))
        return path


# --- Codex transcripts -------------------------------------------------------------


class Codex:
    """A Codex rollout under construction, with the exec tool's shapes."""

    def __init__(self, cwd: Path, repo_url: str = f"https://github.com/{PUBLIC}"):
        self.items: list[dict[str, Any]] = [
            {
                "type": "session_meta",
                "payload": {
                    "id": "01a0e8ef-0000-7000-8000-000000000000",
                    "cwd": str(cwd),
                    "git": {"repository_url": repo_url},
                },
            },
            {"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
        ]

    def item(self, payload: dict[str, Any]) -> Codex:
        self.items.append({"type": "response_item", "payload": payload})
        return self

    def user(self, text: str) -> Codex:
        return self.item(
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            }
        )

    def exec(
        self, call: str, commands: list[str], results: list[tuple[int, str]]
    ) -> Codex:
        script = "\n".join(
            f"tools.exec_command({{cmd:{json.dumps(command)},max_output_tokens:9000}})"
            for command in commands
        )
        self.item(
            {
                "type": "custom_tool_call",
                "call_id": call,
                "name": "exec",
                "input": script,
            }
        )
        body = "\n".join(
            json.dumps(
                {"status": "fulfilled", "value": {"exit_code": code, "output": output}}
            )
            for code, output in results
        )
        output = [
            {"type": "input_text", "text": "Script completed\nOutput:\n"},
            {"type": "input_text", "text": body},
        ]
        return self.item(
            {
                "type": "custom_tool_call_output",
                "call_id": call,
                "output": json.dumps(output),
            }
        )

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(item) + "\n" for item in self.items))
        return path


def skill_md(name: str, body: str) -> str:
    return f'---\nname: "{name}"\ndescription: "Use for {name}."\n---\n\n{body}'


def statuses(report: dict[str, Any]) -> list[tuple[str, str]]:
    return [(load["skill"], load["status"]) for load in report["skills"]]


def questions(bodies: list[dict[str, Any]]) -> list[str]:
    return sorted(name for body in bodies for name in body["questions"])


# --- Tests -------------------------------------------------------------------------------


@exits(SCRIPT, 0)
def test_scan_plans_one_triage_question_per_roster_skill_and_later_event(
    sandbox: Sandbox,
) -> None:
    transcript = (
        Claude(sandbox.repo)
        .user("list the things")
        .load(sandbox.installed("alpha"), ALPHA)
        .say("Running alpha-cli.")
        .tool("t1", "Bash", {"command": "alpha-cli list"}, "a\nb")
        .load(sandbox.home / ".claude/plugins/cache/x/skills/zeta", "Zeta text")
        .say("Done.")
        .write(sandbox.home / "session.jsonl")
    )

    report = sandbox.scan(transcript)
    bodies = sandbox.planned(report)

    assert report["session"] == {
        "harness": "claude",
        "id": "11111111-2222-3333-4444-555555555555",
        "transcript": str(transcript),
        "repo": PUBLIC,
        "model": "claude-opus-5-5",
        "events": 4,
    }
    assert statuses(report) == [("alpha", "roster"), ("zeta", "third-party")]
    assert report["skills"][0]["home"] == PUBLIC
    assert questions(bodies) == [
        "friction::alpha::1",
        "friction::alpha::2",
        "friction::alpha::3",
    ]
    assert bodies[0]["state"]["skills"] == [
        {"name": "alpha", "text": ALPHA.rstrip("\n")}
    ]
    assert bodies[0]["questions"]["friction::alpha::2"]["instructions"] == (
        "Does `events[1]` show the agent failing, retrying, hesitating, or being "
        "corrected by the user while applying an instruction from `skills[0]`?"
    )
    assert [event["id"] for event in bodies[0]["state"]["events"]] == [1, 2, 3]


def test_a_read_of_a_skill_file_keeps_that_files_own_line_numbers(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha")
    reference = alpha / "references/deep.md"
    transcript = (
        Claude(sandbox.repo)
        .load(alpha, ALPHA)
        .tool(
            "t1",
            "Read",
            {"file_path": str(reference), "offset": 10, "limit": 2},
            "    10\tStep ten\n    11\tStep eleven\n<system-reminder>x</system-reminder>",
        )
        .write(sandbox.home / "session.jsonl")
    )

    files = sandbox.scan(transcript)["skills"][0]["files"]

    assert [
        (
            file["path"],
            file["anchor"],
            file["partial"],
            file["first_line"],
            file["lines"],
        )
        for file in files
    ] == [
        (f"{alpha}/SKILL.md", "excerpt", False, 1, 3),
        (str(reference), "file", True, 10, 2),
    ]


def test_codex_splits_skills_one_command_printed_and_ignores_a_failed_read(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha", ".codex")
    beta = sandbox.installed("beta", ".codex")
    gamma = sandbox.installed("gamma", ".codex")
    printed = skill_md("alpha", ALPHA) + skill_md("beta", "Beta body\n")
    transcript = (
        Codex(sandbox.repo)
        .user("do it")
        .exec("c1", [f"cat {alpha}/SKILL.md {beta}/SKILL.md"], [(0, printed)])
        .exec("c2", [f"cat {gamma}/SKILL.md"], [(1, "cat: No such file or directory")])
        .write(sandbox.home / "rollout.jsonl")
    )

    report = sandbox.scan(transcript)

    assert statuses(report) == [("alpha", "roster"), ("beta", "roster")]
    assert [file["lines"] for load in report["skills"] for file in load["files"]] == [
        8,
        6,
    ]
    assert report["notes"] == [
        f"event 2 mentions {gamma}/SKILL.md, but its output does not show that file"
    ]
    assert sandbox.planned(report)[0]["state"]["skills"][0]["text"] == skill_md(
        "alpha", ALPHA
    ).rstrip("\n")


def test_hard_failures_count_only_when_they_name_a_literal_of_a_loaded_skill(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha")
    transcript = (
        Claude(sandbox.repo)
        .tool("t0", "WebFetch", {"url": "https://example.com/alpha-guide"}, "404", True)
        .load(alpha, ALPHA)
        .tool("t1", "WebFetch", {"url": "https://example.com/alpha-guide"}, "404", True)
        .tool(
            "t2",
            "Bash",
            {"command": "alpha-cli"},
            "bash: alpha-cli: command not found",
            True,
        )
        .tool(
            "t3", "Bash", {"command": "ls"}, "bash: other-cli: command not found", True
        )
        .tool(
            "t4",
            "Bash",
            {"command": "python alpha.py"},
            f'Traceback (most recent call last):\n  File "{alpha}/scripts/alpha.py"',
            True,
        )
        .write(sandbox.home / "session.jsonl")
    )

    assert sandbox.scan(transcript)["facts"] == [
        {
            "skill": "alpha",
            "event": 1,
            "kind": "broken_link",
            "detail": "https://example.com/alpha-guide",
        },
        {
            "skill": "alpha",
            "event": 2,
            "kind": "tool_unavailable",
            "detail": "alpha-cli",
        },
        {"skill": "alpha", "event": 4, "kind": "script_bug", "detail": "alpha/scripts"},
    ]


def test_claude_skill_text_counts_in_a_plain_message_and_in_a_skill_result(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha")
    beta = sandbox.installed("beta")
    transcript = (
        Claude(sandbox.repo)
        .user(f"/alpha go\nBase directory for this skill: {alpha}\n\n{ALPHA}")
        .tool(
            "t1",
            "Skill",
            {"skill": "beta"},
            f"Base directory for this skill: {beta}\n\nBeta body",
        )
        .say("done")
        .write(sandbox.home / "session.jsonl")
    )

    report = sandbox.scan(transcript)

    assert [(load["skill"], load["after_event"]) for load in report["skills"]] == [
        ("alpha", 1),
        ("beta", 2),
    ]
    assert report["session"]["events"] == 3


def test_a_codex_textual_exit_status_marks_the_call_failed(sandbox: Sandbox) -> None:
    alpha = sandbox.installed("alpha", ".codex")
    transcript = (
        Codex(sandbox.repo)
        .exec("c1", [f"cat {alpha}/SKILL.md"], [(0, skill_md("alpha", ALPHA))])
        .item(
            {
                "type": "function_call",
                "call_id": "f1",
                "name": "shell",
                "arguments": json.dumps({"cmd": "alpha-cli"}),
            }
        )
        .item(
            {
                "type": "function_call_output",
                "call_id": "f1",
                "output": "Process exited with code 127\nbash: alpha-cli: command not found",
            }
        )
        .write(sandbox.home / "rollout.jsonl")
    )

    assert sandbox.scan(transcript)["facts"] == [
        {
            "skill": "alpha",
            "event": 1,
            "kind": "tool_unavailable",
            "detail": "alpha-cli",
        }
    ]


def test_a_codex_read_of_one_skill_file_joins_that_skills_files(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha", ".codex")
    transcript = (
        Codex(sandbox.repo)
        .exec("c1", [f"cat {alpha}/SKILL.md"], [(0, skill_md("alpha", ALPHA))])
        .exec(
            "c2",
            [f"sed -n '3,4p' {alpha}/references/deep.md"],
            [(0, "Step three\nStep four\n")],
        )
        .exec("c3", [f"cat {alpha}/a.md {alpha}/b.md"], [(0, "two files at once")])
        .write(sandbox.home / "rollout.jsonl")
    )

    files = sandbox.scan(transcript)["skills"][0]["files"]

    assert [(f["path"], f["partial"], f["first_line"], f["lines"]) for f in files] == [
        (f"{alpha}/SKILL.md", False, 1, 8),
        (f"{alpha}/references/deep.md", True, 3, 2),
    ]


def test_triage_shows_the_latest_version_of_a_skill_read_again(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha")
    transcript = (
        Claude(sandbox.repo)
        .load(alpha, "Old text")
        .say("first")
        .load(alpha, "New text")
        .say("second")
        .write(sandbox.home / "session.jsonl")
    )

    body = sandbox.planned(sandbox.scan(transcript))[0]

    assert body["state"]["skills"] == [{"name": "alpha", "text": "New text"}]
    assert sorted(body["questions"]) == ["friction::alpha::0", "friction::alpha::1"]


def test_run_records_are_readable_by_their_owner_only(sandbox: Sandbox) -> None:
    transcript = (
        Claude(sandbox.repo)
        .load(sandbox.installed("alpha"), ALPHA)
        .say("hi")
        .write(sandbox.home / "session.jsonl")
    )

    report = sandbox.scan(transcript)
    root = sandbox.home / ".local/state/jev-skill-retro"
    planned = Path(report["run"], "planned", f"{report['requests'][0]['op']}.json")

    assert (root.stat().st_mode & 0o777, planned.stat().st_mode & 0o777) == (
        0o700,
        0o600,
    )


def test_a_failed_command_naming_a_skill_url_needs_a_failed_fetch_to_be_a_broken_link(
    sandbox: Sandbox,
) -> None:
    url = "https://example.com/alpha-guide"
    transcript = (
        Claude(sandbox.repo)
        .load(sandbox.installed("alpha"), ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": f"curl {url} && make"},
            "make: *** [all] Error 2",
            True,
        )
        .tool(
            "t2", "WebFetch", {"url": url}, "Request failed with status code 404", True
        )
        .write(sandbox.home / "session.jsonl")
    )

    assert [(f["event"], f["kind"]) for f in sandbox.scan(transcript)["facts"]] == [
        (1, "broken_link")
    ]


def test_a_session_outside_git_is_skipped_unless_repo_names_it(
    sandbox: Sandbox,
) -> None:
    transcript = (
        Claude(sandbox.home / "gone")
        .load(sandbox.installed("alpha"), ALPHA)
        .say("hello")
        .write(sandbox.home / "session.jsonl")
    )

    skipped = sandbox.scan(transcript)
    named = sandbox.scan(transcript, "--repo", "o/elsewhere")

    assert (skipped["outcome"], "requests" in skipped) == ("skipped", False)
    assert (named["session"]["repo"], len(named["requests"])) == ("o/elsewhere", 1)


def test_requests_split_so_each_fits_jevs_limits_and_asks_each_question_once(
    sandbox: Sandbox,
) -> None:
    session = Claude(sandbox.repo).load(sandbox.installed("alpha"), ALPHA)
    for number in range(120):
        session.tool(f"t{number}", "Bash", {"command": f"step {number}"}, "x" * 3000)
    report = sandbox.scan(session.write(sandbox.home / "session.jsonl"))
    bodies = sandbox.planned(report)

    assert len(bodies) > 1
    assert questions(bodies) == sorted(f"friction::alpha::{n}" for n in range(120))
    assert all(entry["tokens"] <= 64_000 for entry in report["requests"])
    assert "characters omitted …]" in bodies[0]["state"]["events"][0]["text"]


def test_consent_needs_an_entry_under_the_current_terms_even_for_a_public_repo(
    sandbox: Sandbox,
) -> None:
    transcript = (
        Claude(sandbox.repo)
        .load(sandbox.installed("alpha"), ALPHA)
        .say("hi")
        .write(sandbox.home / "session.jsonl")
    )

    missing = sandbox.scan(transcript, "--repo", "o/private")["consent"]
    sandbox.consent(**{PUBLIC: "typesafe-2026-09-26", "o/private": "old-terms"})
    recorded = sandbox.scan(transcript, "--repo", "o/private")["consent"]

    assert missing == {"o/private": False, PUBLIC: False}
    assert recorded == {"o/private": False, PUBLIC: True}


def test_secrets_are_reported_by_rule_and_line_never_by_value(sandbox: Sandbox) -> None:
    transcript = (
        Claude(sandbox.repo)
        .load(sandbox.installed("alpha"), ALPHA)
        .say("token ghp_notreallyasecret")
        .write(sandbox.home / "session.jsonl")
    )
    sandbox.stub(
        "gitleaks",
        "cat > /dev/null\n"
        'echo \'[{"RuleID": "github-pat", "StartLine": 14, "Secret": "REDACTED"}]\'\n'
        "exit 3\n",
    )

    report = sandbox.scan(transcript)

    assert report["secrets"] == {report["requests"][0]["op"]: ["github-pat at line 14"]}


def test_without_gitleaks_the_secrets_stay_unchecked(sandbox: Sandbox) -> None:
    transcript = (
        Claude(sandbox.repo)
        .load(sandbox.installed("alpha"), ALPHA)
        .say("hi")
        .write(sandbox.home / "session.jsonl")
    )
    git = shutil.which("git")
    assert git is not None
    (sandbox.bin / "git").symlink_to(git)

    report = sandbox.scan(transcript, PATH=str(sandbox.bin))

    assert report["secrets"] == "unchecked"


def test_a_session_id_is_found_in_the_agent_homes(sandbox: Sandbox) -> None:
    session = "99999999-8888-7777-6666-555555555555"
    Claude(sandbox.repo, session).load(sandbox.installed("alpha"), ALPHA).say(
        "hi"
    ).write(sandbox.home / f".claude/projects/-repo/{session}.jsonl")

    assert sandbox.scan(session)["session"]["id"] == session


@exits(SCRIPT, 1)
def test_a_file_that_is_not_a_transcript_fails(sandbox: Sandbox) -> None:
    other = sandbox.home / "notes.jsonl"
    other.write_text('{"hello": "world"}\n')

    result = sandbox.run("scan", str(other), "--dry-run")

    assert (result.returncode, result.stdout) == (1, "")
    assert (
        f"error: {other} is neither a Claude Code nor a Codex transcript"
        in result.stderr
    )


@exits(SCRIPT, 75)
def test_another_run_holding_the_session_lock_exits_75(sandbox: Sandbox) -> None:
    transcript = (
        Claude(sandbox.repo)
        .load(sandbox.installed("alpha"), ALPHA)
        .say("hi")
        .write(sandbox.home / "session.jsonl")
    )
    run = Path(sandbox.scan(transcript)["run"])

    with (run / "lock").open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        result = sandbox.run("scan", str(transcript), "--dry-run", "--timeout", "0.2")

    assert (result.returncode, result.stdout) == (75, "")
    assert "another run still holds" in result.stderr


# --- Live scans against a fake TypeSafe --------------------------------------------------


@dataclass
class FakeJev:
    """A fake /v1/systemone. Tests set the answers per question; `hint` picks
    the line a `where` Choice lands on."""

    friction: dict[int, float] = field(default_factory=dict)
    covered: dict[str, float] = field(default_factory=dict)
    relation: dict[str, float] = field(
        default_factory=lambda: {
            "contradicted": 0.85,
            "incomplete": 0.05,
            "ambiguous": 0.03,
            "not_followed": 0.03,
            "unrelated": 0.02,
            "cannot-tell": 0.02,
        }
    )
    recurs: float = 0.9
    tool: float = 0.05
    conflict: float = 0.1
    same: dict[int, float] = field(default_factory=dict)
    hint: str = "alpha-cli"
    where_p: float = 0.9
    model: str = "jev-1.13.0"
    status: int = 200
    delay: float = 0.0
    bodies: list[dict[str, Any]] = field(default_factory=list)

    def kinds(self) -> list[str]:
        return [next(iter(body["questions"])).split("::")[0] for body in self.bodies]

    def answer(self, key: str, state: dict[str, Any]) -> dict[str, Any]:
        kind, _, rest = key.partition("::")
        if kind == "friction":
            return {
                "type": "noul",
                "noul": self.friction.get(int(rest.split("::")[1]), 0.05),
            }
        if kind == "where":
            lines = state["files"][int(rest)]["lines"]
            hit = next(
                (line.split(":")[0] for line in lines if self.hint in line), None
            )
            chosen = (
                {hit: self.where_p, "none": 1 - self.where_p} if hit else {"none": 0.95}
            )
            return {
                "type": "choice",
                "choice": max(chosen, key=chosen.__getitem__),
                "probabilities": chosen,
            }
        if kind == "same":
            return {"type": "noul", "noul": self.same.get(int(rest), 0.05)}
        if kind == "covered":
            return {"type": "noul", "noul": self.covered.get(rest, 0.9)}
        if kind == "relation":
            return {
                "type": "choice",
                "choice": max(self.relation, key=self.relation.__getitem__),
                "probabilities": self.relation,
            }
        value = {
            "tool_unavailable": self.tool,
            "recurs": self.recurs,
            "conflict": self.conflict,
        }[kind]
        return {"type": "noul", "noul": value}


@pytest.fixture
def jev() -> Iterator[tuple[FakeJev, str]]:
    fake = FakeJev()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            fake.bodies.append(body)
            time.sleep(fake.delay)
            if fake.status != 200:
                self.send_response(fake.status)
                self.end_headers()
                return
            answers = {
                key: fake.answer(key, body["state"]) for key in body["questions"]
            }
            reply = json.dumps(
                {
                    "model": fake.model,
                    "answers": answers,
                    "usage": {"input_tokens": 1000},
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(reply)))
            self.end_headers()
            self.wfile.write(reply)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield fake, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@dataclass
class Live:
    sandbox: Sandbox
    fake: FakeJev
    url: str

    def run(self, target: Path | str, *args: str) -> subprocess.CompletedProcess[str]:
        return self.sandbox.run(
            "scan",
            str(target),
            "--json",
            *args,
            TYPESAFE_API_KEY="test-key",
            TYPESAFE_BASE_URL=self.url,
        )

    def scan(self, target: Path | str, *args: str) -> dict[str, Any]:
        result = self.run(target, *args)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)


@pytest.fixture
def live(sandbox: Sandbox, jev: tuple[FakeJev, str]) -> Live:
    """Consent for the public repo, a gitleaks that finds nothing, and a chezmoi
    that has no key, so no real credential can reach the fake."""
    sandbox.consent(**{PUBLIC: "typesafe-2026-09-26"})
    sandbox.stub("gitleaks", "cat > /dev/null\necho '[]'\n")
    sandbox.stub("chezmoi", "exit 1\n")
    return Live(sandbox, *jev)


def friction_session(sandbox: Sandbox, *skills: tuple[str, str]) -> Path:
    """Load each skill, then one failing alpha-cli call: event 1 after one skill."""
    session = Claude(sandbox.repo).user("list the things")
    for name, body in skills:
        session.load(sandbox.installed(name), body)
    session.tool(
        "t1", "Bash", {"command": "alpha-cli list --all"}, "unknown flag --all", True
    )
    session.say("I will try without --all.")
    return session.write(sandbox.home / "session.jsonl")


def outcome(report: dict[str, Any], skill: str = "alpha") -> dict[str, Any]:
    return next(found for found in report["outcomes"] if found["skill"] == skill)


def test_a_contradicted_line_makes_the_skill_a_candidate_anchored_on_that_line(
    live: Live,
) -> None:
    live.fake.friction = {1: 0.92}
    report = live.scan(friction_session(live.sandbox, ("alpha", ALPHA)))
    alpha = outcome(report)
    item = alpha["items"][0]

    assert (alpha["outcome"], len(alpha["items"])) == ("candidate", 1)
    assert (item["event"], item["outcome"], item["category"]) == (
        1,
        "candidate",
        "contradicted",
    )
    assert item["line"] == {
        "skill": "alpha",
        "file": f"{live.sandbox.installed('alpha')}/SKILL.md",
        "anchor": "excerpt",
        "number": 1,
        "text": "Use `alpha-cli` to list things.",
        "before": "",
        "after": "Read https://example.com/alpha-guide first.",
    }
    assert live.fake.kinds() == ["friction", "where", "relation"]
    assert report["usage"] == {
        "model": "jev-1.13.0",
        "sent": 3,
        "reused": 0,
        "input_tokens": 3000,
        "cost_usd": 0.000126,
    }


def test_a_skill_without_friction_ends_as_nothing_after_triage_alone(
    live: Live,
) -> None:
    report = live.scan(friction_session(live.sandbox, ("alpha", ALPHA)))

    assert (outcome(report)["outcome"], outcome(report)["items"]) == ("nothing", [])
    assert live.fake.kinds() == ["friction"]


def test_a_step_no_line_covers_is_missing_information_when_it_recurs(
    live: Live,
) -> None:
    live.fake.friction = {1: 0.9}
    live.fake.hint = "nothing matches this"
    live.fake.covered = {"alpha": 0.1}
    report = live.scan(friction_session(live.sandbox, ("alpha", ALPHA)))

    assert [
        (i["outcome"], i["category"], i["line"]) for i in outcome(report)["items"]
    ] == [("candidate", "missing_information", None)]
    assert live.fake.bodies[-1]["state"]["line"] == {
        "skill": "alpha",
        "text": ALPHA.rstrip("\n"),
    }
    assert list(live.fake.bodies[-1]["questions"]) == ["recurs"]


def test_a_line_another_loaded_skill_contradicts_is_a_conflict(live: Live) -> None:
    live.fake.friction = {2: 0.9}
    live.fake.conflict = 0.88
    beta = "Never pass flags to `alpha-cli`.\n"
    report = live.scan(friction_session(live.sandbox, ("alpha", ALPHA), ("beta", beta)))
    item = outcome(report)["items"][0]

    assert (item["outcome"], item["category"]) == ("candidate", "conflict")
    assert item["other_line"]["skill"] == "beta"
    assert "conflict" in live.fake.bodies[-1]["questions"]


@pytest.mark.parametrize(
    ("relation", "expected"),
    [
        ({"not_followed": 0.8, "contradicted": 0.2}, ("nothing", "not_followed")),
        ({"cannot-tell": 0.7, "contradicted": 0.3}, ("review", "relation_unclear")),
        (
            {"contradicted": 0.4, "incomplete": 0.35, "unrelated": 0.25},
            ("candidate", "skill_side_unclear"),
        ),
    ],
    ids=["agent-error", "cannot-tell", "skill-side-but-unclear"],
)
def test_the_relation_decides_between_candidate_review_and_nothing(
    live: Live, relation: dict[str, float], expected: tuple[str, str]
) -> None:
    live.fake.friction = {1: 0.9}
    live.fake.relation = relation
    report = live.scan(friction_session(live.sandbox, ("alpha", ALPHA)))
    item = outcome(report)["items"][0]

    assert (item["outcome"], item["category"]) == expected
    assert outcome(report)["outcome"] == expected[0]


def test_a_hard_failure_is_a_candidate_even_without_friction(live: Live) -> None:
    transcript = (
        Claude(live.sandbox.repo)
        .load(live.sandbox.installed("alpha"), ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli"},
            "bash: alpha-cli: command not found",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )

    item = outcome(live.scan(transcript))["items"][0]

    assert (item["outcome"], item["category"], item["detail"]) == (
        "candidate",
        "tool_unavailable",
        "alpha-cli",
    )


@exits(SCRIPT, 1)
def test_missing_consent_stops_before_anything_is_sent(live: Live) -> None:
    (live.sandbox.home / ".config/label-for-issues-jev/consent.toml").unlink()

    result = live.run(friction_session(live.sandbox, ("alpha", ALPHA)))

    assert (result.returncode, result.stdout, live.fake.bodies) == (1, "", [])
    assert f"{PUBLIC} has no consent under typesafe-2026-09-26" in result.stderr
    assert f"consent add {PUBLIC}" in result.stderr


def test_a_secret_in_a_request_stops_it_before_it_is_sent(live: Live) -> None:
    live.sandbox.stub(
        "gitleaks",
        'cat > /dev/null\necho \'[{"RuleID": "github-pat", "StartLine": 9}]\'\nexit 3\n',
    )

    result = live.run(friction_session(live.sandbox, ("alpha", ALPHA)))

    assert (result.returncode, live.fake.bodies) == (1, [])
    assert (
        "holds what gitleaks reads as a secret: github-pat at line 9" in result.stderr
    )


def test_a_rerun_reuses_saved_answers_and_replay_sends_nothing(live: Live) -> None:
    live.fake.friction = {1: 0.92}
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    first = live.scan(transcript)
    again = live.scan(transcript)
    replayed = live.scan(transcript, "--replay")

    assert len(live.fake.bodies) == 3
    assert (again["usage"]["sent"], again["usage"]["reused"]) == (0, 3)
    assert again["outcomes"] == first["outcomes"] == replayed["outcomes"]


def test_replay_without_saved_answers_fails(live: Live) -> None:
    result = live.run(friction_session(live.sandbox, ("alpha", ALPHA)), "--replay")

    assert (result.returncode, live.fake.bodies) == (1, [])
    assert "has no saved answer, so --replay cannot decide" in result.stderr


@exits(SCRIPT, 75)
def test_a_rate_limit_exits_75_and_a_rerun_sends_again(live: Live) -> None:
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.fake.status = 429
    limited = live.run(transcript)
    live.fake.status = 200
    rerun = live.scan(transcript)

    assert (limited.returncode, limited.stdout) == (75, "")
    assert rerun["usage"]["sent"] == 1


def test_a_request_whose_answer_never_came_is_resent_only_with_retry(
    live: Live,
) -> None:
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.fake.delay = 1.5
    lost = live.run(transcript, "--timeout", "0.5")
    live.fake.delay = 0
    blocked = live.run(transcript)
    op = next(word for word in blocked.stderr.split() if word.startswith("triage-"))
    retried = live.scan(transcript, "--retry", op)

    assert lost.returncode == 1
    assert "no answer came back within 0.5s; TypeSafe may have billed it" in lost.stderr
    assert (blocked.returncode, len(live.fake.bodies)) == (1, 2)
    assert f"rerun with --retry {op}" in blocked.stderr
    assert retried["usage"]["sent"] == 1


def test_the_request_budget_stops_the_scan_and_a_rerun_reuses_its_answers(
    live: Live,
) -> None:
    live.fake.friction = {1: 0.92}
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    stopped = live.run(transcript, "--max-requests", "1")
    finished = live.scan(transcript)

    assert stopped.returncode == 1
    assert "the scan stopped at its budget of 1 requests" in stopped.stderr
    assert (finished["usage"]["sent"], finished["usage"]["reused"]) == (2, 1)


def test_an_answer_from_another_model_fails_the_scan(live: Live) -> None:
    live.fake.model = "jev-9.0.0"

    result = live.run(friction_session(live.sandbox, ("alpha", ALPHA)))

    assert result.returncode == 1
    assert "was answered by 'jev-9.0.0', not the pinned jev-1.13.0" in result.stderr


def test_an_ambiguous_server_error_is_resent_only_with_retry(live: Live) -> None:
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.fake.status = 504
    failed = live.run(transcript)
    live.fake.status = 200
    blocked = live.run(transcript)

    assert failed.returncode == blocked.returncode == 1
    assert "answered HTTP 504 for request triage-" in failed.stderr
    assert "may have run and been billed" in failed.stderr
    assert "was sent but its answer never arrived" in blocked.stderr
    assert len(live.fake.bodies) == 1


def test_the_version_read_before_an_event_is_the_one_located(live: Live) -> None:
    alpha = live.sandbox.installed("alpha")
    live.fake.friction = {1: 0.9}
    transcript = (
        Claude(live.sandbox.repo)
        .load(alpha, "Old: run `alpha-cli --all`.")
        .say("first try")
        .load(alpha, ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli list --all"},
            "unknown flag --all",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )

    live.scan(transcript)
    located = next(
        body for body in live.fake.bodies if "covered::alpha" in body["questions"]
    )

    assert (
        located["state"]["files"][0]["lines"][0]
        == "L1: Use `alpha-cli` to list things."
    )


def test_an_unclear_location_keeps_the_event_in_review(live: Live) -> None:
    live.fake.friction = {1: 0.9}
    live.fake.where_p = 0.55
    live.fake.recurs = 0.1
    report = live.scan(friction_session(live.sandbox, ("alpha", ALPHA)))

    assert [(i["outcome"], i["category"]) for i in outcome(report)["items"]] == [
        ("review", "location_unclear")
    ]


def test_an_event_a_hard_failure_decided_is_not_examined_again(live: Live) -> None:
    live.fake.friction = {1: 0.95}
    transcript = (
        Claude(live.sandbox.repo)
        .user("go")
        .load(live.sandbox.installed("alpha"), ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli"},
            "bash: alpha-cli: command not found",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )

    report = live.scan(transcript)

    assert [(i["event"], i["category"]) for i in outcome(report)["items"]] == [
        (1, "tool_unavailable")
    ]
    assert live.fake.kinds() == ["friction"]


def test_a_locate_request_too_large_keeps_only_the_skills_own_text(live: Live) -> None:
    alpha = live.sandbox.installed("alpha")
    huge = "\n".join(f"{n:6}\tReference line {n} " + "x" * 80 for n in range(1, 2001))
    live.fake.friction = {2: 0.9}
    transcript = (
        Claude(live.sandbox.repo)
        .user("go")
        .load(alpha, ALPHA)
        .tool("t0", "Read", {"file_path": f"{alpha}/references/huge.md"}, huge)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli list --all"},
            "unknown flag --all",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )

    report = live.scan(transcript)
    located = next(
        body for body in live.fake.bodies if "covered::alpha" in body["questions"]
    )

    assert [file["path"] for file in located["state"]["files"]] == [f"{alpha}/SKILL.md"]
    assert outcome(report)["items"][0]["event"] == 2


def test_without_a_key_nothing_is_sent(live: Live) -> None:
    result = live.sandbox.run(
        "scan",
        str(friction_session(live.sandbox, ("alpha", ALPHA))),
        TYPESAFE_BASE_URL=live.url,
    )

    assert (result.returncode, live.fake.bodies) == (1, [])
    assert "no TypeSafe API key" in result.stderr


# --- Write: forks against fake claude and codex ------------------------------------


def fake_agent(sandbox: Sandbox, name: str, answer: str) -> Path:
    """A fake claude or codex first on PATH. Each call saves its arguments, its
    working directory, and its prompt in calls/<n>/, then answers with `answer`:
    claude as print mode's JSON on stdout, codex in the file after -o."""
    calls = sandbox.home / f"{name}-calls"
    calls.mkdir()
    reply = sandbox.home / f"{name}-reply"
    reply.write_text(json.dumps({"result": answer}) if name == "claude" else answer)
    sandbox.stub(
        name,
        f'call="{calls}/$(ls "{calls}" | wc -l | tr -d " ")"\n'
        'mkdir "$call"\n'
        'printf "%s\\n" "$@" > "$call/argv"\n'
        'pwd > "$call/cwd"\n'
        'cat > "$call/prompt"\n'
        'out=""; previous=""\n'
        'for arg in "$@"; do [ "$previous" = "-o" ] && out="$arg"; previous="$arg"; done\n'
        f'if [ -n "$out" ]; then cat "{reply}" > "$out"; else cat "{reply}"; fi\n',
    )
    return calls


def story(item: str, **extra: Any) -> str:
    fields = {
        "verdict": "story",
        "title": "Document the removed --all flag",
        "user_story": "As an agent using the `alpha` skill, I want its flags current, so that my first call works",
        "wanted": "list the things",
        "problem": "alpha-cli rejected --all",
        "workaround": "ran it without --all",
        "fix": "Drop --all from line 1",
        "evidence": "unknown flag --all",
        **extra,
    }
    return json.dumps({"item": item, **fields} if "items" not in extra else fields)


def calls(folder: Path) -> list[Path]:
    return sorted(folder.iterdir())


def written(live: Live, target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return live.sandbox.run("write", str(target), "--json", *args)


def test_write_dry_run_shows_the_fork_and_saves_a_prompt_without_raw_mentions(
    live: Live,
) -> None:
    live.fake.friction = {1: 0.92}
    transcript = (
        Claude(live.sandbox.repo)
        .user("list the things")
        .load(live.sandbox.installed("alpha"), ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli list"},
            "unknown flag; see @notes.txt",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )
    live.scan(transcript)
    agent = fake_agent(live.sandbox, "claude", "")

    result = written(live, transcript, "--dry-run")
    report = json.loads(result.stdout)
    prompt = Path(report["fork"]["prompt"]).read_text()

    assert (result.returncode, calls(agent)) == (0, [])
    assert [(i["id"], i["outcome"], i["category"]) for i in report["items"]] == [
        ("alpha-e1", "candidate", "contradicted")
    ]
    assert report["fork"]["cost_usd"][0] <= report["fork"]["cost_usd"][1]
    assert prompt.startswith("[jev-skill-retro fork] End-of-session skill feedback")
    assert "@" not in prompt
    assert "see \\u0040notes.txt" in prompt


def test_a_fork_needs_yes_after_the_dry_run(live: Live) -> None:
    live.fake.friction = {1: 0.92}
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.scan(transcript)
    agent = fake_agent(live.sandbox, "claude", "")

    result = written(live, transcript)

    assert (result.returncode, calls(agent)) == (1, [])
    assert "pass --yes after he approves" in result.stderr


def test_write_forks_claude_read_only_in_the_sessions_directory_and_saves_stories(
    live: Live,
) -> None:
    live.fake.friction = {1: 0.92}
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.scan(transcript)
    agent = fake_agent(live.sandbox, "claude", story("alpha-e1"))

    result = written(live, transcript, "--yes")
    report = json.loads(result.stdout)
    call = calls(agent)[0]

    assert result.returncode == 0, result.stderr
    assert (call / "argv").read_text().split("\n")[:-1] == [
        "-p", "--resume", "11111111-2222-3333-4444-555555555555", "--fork-session",
        "--no-session-persistence", "--permission-mode", "dontAsk",
        "--strict-mcp-config", "--tools", "Read,Grep,Glob", "--output-format", "json",
        "--model", "claude-opus-5-5",
    ]  # fmt: skip
    assert (call / "cwd").read_text().strip() == str(live.sandbox.repo)
    assert [(s["title"], [i["id"] for i in s["items"]]) for s in report["stories"]] == [
        ("Document the removed --all flag", ["alpha-e1"])
    ]
    assert json.loads(Path(report["run"], "stories.json").read_text()) == report


def test_write_forks_codex_with_a_read_only_sandbox(live: Live) -> None:
    alpha = live.sandbox.installed("alpha", ".codex")
    transcript = (
        Codex(live.sandbox.repo)
        .user("list the things")
        .exec("c1", [f"cat {alpha}/SKILL.md"], [(0, skill_md("alpha", ALPHA))])
        .exec("c2", ["alpha-cli list --all"], [(2, "unknown flag --all")])
        .write(live.sandbox.home / "rollout.jsonl")
    )
    live.fake.friction = {2: 0.92}
    live.scan(transcript)
    agent = fake_agent(live.sandbox, "codex", story("alpha-e2"))

    report = json.loads(written(live, transcript, "--yes").stdout)
    argv = (calls(agent)[0] / "argv").read_text().split("\n")[:-1]

    assert argv[:12] == [
        "exec", "fork", "01a0e8ef-0000-7000-8000-000000000000", "-", "--ephemeral",
        "--skip-git-repo-check", "-c", 'sandbox_mode="read-only"', "-c",
        'approval_policy="never"', "-o", argv[11],
    ]  # fmt: skip
    assert [s["items"][0]["id"] for s in report["stories"]] == ["alpha-e2"]


def test_an_invalid_answer_fails_and_forks_again_only_with_retry(live: Live) -> None:
    live.fake.friction = {1: 0.92}
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.scan(transcript)
    agent = fake_agent(live.sandbox, "claude", "I found nothing worth fixing.")

    first = written(live, transcript, "--yes")
    again = written(live, transcript, "--yes")
    op = json.loads(written(live, transcript, "--dry-run").stdout)["fork"]["op"]
    retried = written(live, transcript, "--yes", "--retry", op)

    assert first.returncode == again.returncode == retried.returncode == 1
    assert "the fork's answer is invalid: item 'alpha-e1' has no answer" in first.stderr
    assert len(calls(agent)) == 2


def test_related_items_can_share_one_story_and_the_rest_say_nothing(live: Live) -> None:
    live.fake.friction = {1: 0.92, 2: 0.9, 3: 0.91}
    session = (
        Claude(live.sandbox.repo)
        .user("go")
        .load(live.sandbox.installed("alpha"), ALPHA)
    )
    for call in ("t1", "t2", "t3"):
        session.tool(
            call,
            "Bash",
            {"command": "alpha-cli list --all"},
            "unknown flag --all",
            True,
        )
    transcript = session.write(live.sandbox.home / "session.jsonl")
    live.scan(transcript)
    answer = "\n".join(
        [
            story("", items=["alpha-e1", "alpha-e2"]),
            json.dumps({"item": "alpha-e3", "verdict": "nothing"}),
        ]
    )
    fake_agent(live.sandbox, "claude", f"```json\n{answer}\n```")

    report = json.loads(written(live, transcript, "--yes").stdout)

    assert [[i["id"] for i in s["items"]] for s in report["stories"]] == [
        ["alpha-e1", "alpha-e2"]
    ]
    assert report["nothing"] == ["alpha-e3"]


def test_a_session_without_flagged_skills_is_not_forked(live: Live) -> None:
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.scan(transcript)
    agent = fake_agent(live.sandbox, "claude", "")

    result = written(live, transcript, "--yes")

    assert (result.returncode, json.loads(result.stdout)["fork"], calls(agent)) == (
        0,
        None,
        [],
    )


def test_write_before_a_scan_fails(live: Live) -> None:
    result = written(live, friction_session(live.sandbox, ("alpha", ALPHA)), "--yes")

    assert result.returncode == 1
    assert "has no scan yet" in result.stderr


def test_a_session_whose_directory_is_gone_is_reported_not_forked(live: Live) -> None:
    gone = live.sandbox.home / "worktree"
    gone.mkdir()
    live.fake.friction = {1: 0.92}
    transcript = (
        Claude(gone)
        .user("list the things")
        .load(live.sandbox.installed("alpha"), ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli list --all"},
            "unknown flag --all",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )
    live.scan(transcript, "--repo", PUBLIC)
    gone.rmdir()
    agent = fake_agent(live.sandbox, "claude", story("alpha-e1"))

    result = written(live, transcript, "--yes")

    assert (result.returncode, calls(agent)) == (1, [])
    assert f"the session's working directory {gone} is gone" in result.stderr


def test_write_dry_run_prints_tab_separated_lines_with_the_fork_estimate(
    live: Live,
) -> None:
    live.fake.friction = {1: 0.92}
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.scan(transcript)

    result = live.sandbox.run("write", str(transcript), "--dry-run")
    rows = [line.split("\t") for line in result.stdout.splitlines()]

    assert result.returncode == 0, result.stderr
    assert [row[0] for row in rows] == ["run", "fork", "item", "prompt"]
    assert rows[1][4] == "claude-opus-5-5"
    assert rows[1][7].startswith("fallback: about $40 per 600k tokens")
    assert rows[2] == ["item", "alpha-e1", "candidate", "contradicted"]


@pytest.mark.parametrize(
    ("step", "flag"), [("scan", "--yes"), ("write", "--replay")], ids=["scan", "write"]
)
def test_a_flag_another_step_owns_is_a_usage_error(
    sandbox: Sandbox, step: str, flag: str
) -> None:
    result = sandbox.run(step, "missing-session", flag)

    assert (result.returncode, result.stdout) == (2, "")
    assert f"{step} takes no {flag}" in result.stderr


# --- Publish: issues and comments against a fake gh -----------------------------------

LABELS = ["1-needs-triage", "2-type:postmortem", "3-pty:p2"]
FAKE_GH = """#!{python}
import json, pathlib, sys
path = pathlib.Path({state!r})
state = json.loads(path.read_text())
args = sys.argv[1:]
def value(flag):
    return args[args.index(flag) + 1] if flag in args else None
def issue(number):
    return next(found for found in state["issues"] if found["number"] == number)
def save():
    path.write_text(json.dumps(state))
if args[:2] == ["label", "list"]:
    print(json.dumps([{{"name": name}} for name in state["labels"]]))
elif args[:2] == ["repo", "view"]:
    print(state["visibility"].get(args[2], "PUBLIC"))
elif args[:2] == ["issue", "list"]:
    found = [i for i in state["issues"] if value("--state") != "open" or i["state"] == "OPEN"]
    print(json.dumps(found))
elif args[:2] == ["issue", "view"]:
    shown = dict(issue(int(args[2])))
    shown["labels"] = [{{"name": name}} for name in shown["labels"]]
    if shown["number"] in state.get("closed_on_view", []):
        shown["state"] = "CLOSED"
    print(json.dumps(shown))
elif args[:2] == ["issue", "create"]:
    number = 100 + len(state["issues"])
    url = "https://github.com/" + value("-R") + "/issues/" + str(number)
    labels = [] if state.get("drop_labels") else [args[i + 1] for i, arg in enumerate(args) if arg == "--label"]
    state["issues"].append({{"number": number, "title": value("--title"), "body": sys.stdin.read(),
                            "url": url, "state": "OPEN", "labels": labels, "comments": []}})
    state["calls"].append(["create", number])
    save()
    print(url)
elif args[:2] == ["issue", "comment"]:
    target = issue(int(args[2]))
    url = target["url"] + "#issuecomment-" + str(len(state["calls"]))
    target["comments"].append({{"body": sys.stdin.read(), "url": url}})
    state["calls"].append(["comment", target["number"]])
    save()
    print(url)
else:
    sys.exit("fake gh: unexpected " + " ".join(args))
"""


@dataclass
class GitHub:
    path: Path

    def state(self) -> dict[str, Any]:
        return json.loads(self.path.read_text())

    def update(self, **values: Any) -> None:
        self.path.write_text(json.dumps({**self.state(), **values}))


def fake_github(sandbox: Sandbox, **state: Any) -> GitHub:
    path = sandbox.home / "github.json"
    path.write_text(
        json.dumps(
            {"labels": LABELS, "issues": [], "visibility": {}, "calls": [], **state}
        )
    )
    gh = sandbox.bin / "gh"
    gh.write_text(FAKE_GH.format(python=sys.executable, state=str(path)))
    gh.chmod(0o755)
    return GitHub(path)


def open_issue(number: int, title: str) -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "body": "An older retro story",
        "url": f"https://github.com/{PUBLIC}/issues/{number}",
        "state": "OPEN",
        "labels": LABELS,
        "comments": [],
    }


def stories_ready(
    live: Live, cwd: Path | None = None, *scan_args: str, **fields: Any
) -> Path:
    """A scan with one candidate on alpha's first line, and the fork's story."""
    live.fake.friction = {1: 0.92}
    transcript = (
        Claude(cwd or live.sandbox.repo)
        .user("list the things")
        .load(live.sandbox.installed("alpha"), ALPHA)
        .tool(
            "t1",
            "Bash",
            {"command": "alpha-cli list --all"},
            "unknown flag --all",
            True,
        )
        .write(live.sandbox.home / "session.jsonl")
    )
    live.scan(transcript, *scan_args)
    fake_agent(live.sandbox, "claude", story("alpha-e1", **fields))
    assert written(live, transcript, "--yes").returncode == 0
    return transcript


def published(live: Live, target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return live.sandbox.run(
        "publish",
        str(target),
        *args,
        TYPESAFE_API_KEY="test-key",
        TYPESAFE_BASE_URL=live.url,
    )


def test_publish_dry_run_previews_a_new_issue_and_writes_nothing(live: Live) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)

    result = published(live, transcript, "--dry-run", "--json")
    action = json.loads(result.stdout)["actions"][0]

    assert result.returncode == 0, result.stderr
    assert (action["action"], action["repo"], action["target"], action["title"]) == (
        "create",
        PUBLIC,
        None,
        "alpha: Document the removed --all flag",
    )
    assert action["body"].startswith("Retro ")
    assert "#### US-1 — `alpha`: Document the removed --all flag" in action["body"]
    assert (
        "- Anchor: `skills/alpha/SKILL.md`, line 1 of the loaded text (contradicted)"
        in action["body"]
    )
    assert "11111111-2222" not in action["body"]
    assert str(live.sandbox.home) not in action["body"]
    assert github.state()["calls"] == []


def test_publish_files_the_issue_with_its_labels_once(live: Live) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)

    first = published(live, transcript, "--yes")
    again = published(live, transcript, "--yes")
    filed = github.state()["issues"][0]

    assert (first.returncode, first.stdout) == (
        0,
        f"create\t{PUBLIC}\talpha: Document the removed --all flag\n",
    )
    assert (again.returncode, again.stdout) == (0, "")
    assert github.state()["calls"] == [["create", 100]]
    assert filed["labels"] == LABELS
    assert "<!-- jev-skill-retro:op=publish-" in filed["body"]


def test_a_story_that_repeats_one_open_issue_becomes_a_comment(live: Live) -> None:
    github = fake_github(live.sandbox, issues=[open_issue(7, "alpha: flags are stale")])
    live.fake.same = {7: 0.91}
    transcript = stories_ready(live)

    result = published(live, transcript, "--yes")

    assert (result.returncode, result.stdout) == (
        0,
        f"comment\t{PUBLIC}#7\talpha: Document the removed --all flag\n",
    )
    assert github.state()["calls"] == [["comment", 7]]
    assert github.state()["issues"][0]["comments"][0]["body"].startswith("Seen again:")


def test_an_unclear_duplicate_is_held_for_a_person(live: Live) -> None:
    github = fake_github(live.sandbox, issues=[open_issue(7, "alpha: flags are stale")])
    live.fake.same = {7: 0.5}
    transcript = stories_ready(live)

    result = published(live, transcript, "--yes")

    assert (result.returncode, result.stdout, github.state()["calls"]) == (0, "", [])
    assert (
        "held alpha: Document the removed --all flag: it may repeat #7 (0.50)"
        in result.stderr
    )


def test_a_story_whose_anchored_line_changed_is_held_as_stale(live: Live) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)
    (live.sandbox.repo / "skills/alpha/SKILL.md").write_text(
        "# alpha\n\nUse `alpha` now.\n"
    )
    commit(live.sandbox.repo)

    result = published(live, transcript, "--yes", "--json")

    assert json.loads(result.stdout)["held"] == [
        {
            "title": "alpha: Document the removed --all flag",
            "reason": "stale: the anchored line of alpha-e1 changed on main since the session",
        }
    ]
    assert github.state()["calls"] == []


def test_a_missing_label_names_the_command_that_creates_it(live: Live) -> None:
    github = fake_github(live.sandbox, labels=["1-needs-triage", "3-pty:p2"])
    transcript = stories_ready(live)

    result = published(live, transcript, "--yes")

    assert (result.returncode, github.state()["calls"]) == (1, [])
    assert f"run: gh label create 2-type:postmortem -R {PUBLIC}" in result.stderr


def test_an_interrupted_publish_finds_its_marker_instead_of_filing_twice(
    live: Live,
) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)
    report = json.loads(published(live, transcript, "--yes", "--json").stdout)
    op = report["actions"][0]["op"]
    record = Path(report["run"], "ops", f"{op}.json")
    # As if the run stopped after gh created the issue, before it saved the receipt
    record.write_text(
        json.dumps(
            {"kind": "publish", "state": "sent", "action": "create", "target": None}
        )
    )

    again = json.loads(published(live, transcript, "--yes", "--json").stdout)

    assert github.state()["calls"] == [["create", 100]]
    assert again["actions"][0]["url"] == f"https://github.com/{PUBLIC}/issues/100"
    assert json.loads(record.read_text())["state"] == "done"


def test_publish_needs_yes_after_the_dry_run(live: Live) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)

    result = published(live, transcript)

    assert (result.returncode, github.state()["calls"]) == (1, [])
    assert "pass --yes" in result.stderr


def test_publish_before_write_fails(live: Live) -> None:
    fake_github(live.sandbox)
    transcript = friction_session(live.sandbox, ("alpha", ALPHA))
    live.scan(transcript)

    result = published(live, transcript, "--yes")

    assert result.returncode == 1
    assert "has no written stories yet" in result.stderr


def test_a_private_session_repo_is_named_nowhere_in_public_output(live: Live) -> None:
    github = fake_github(live.sandbox, visibility={"o/secret-proj": "PRIVATE"})
    live.sandbox.consent(
        **{PUBLIC: "typesafe-2026-09-26", "o/secret-proj": "typesafe-2026-09-26"}
    )
    work = live.sandbox.home / "work"
    work.mkdir()
    transcript = stories_ready(
        live,
        work,
        "--repo",
        "o/secret-proj",
        problem=f"alpha-cli failed in o/secret-proj at {live.sandbox.home}/work and /tmp/secret-proj/config, as secret-proj notes",
    )

    result = published(live, transcript, "--yes")
    body = github.state()["issues"][0]["body"]

    assert result.returncode == 0, result.stderr
    assert (
        "- Problem: alpha-cli failed in a private project at <local path> and "
        "<local path>, as a private project notes"
    ) in body
    assert "secret-proj" not in body


def test_a_secret_in_the_story_holds_it(live: Live) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)
    live.sandbox.stub(
        "gitleaks",
        'cat > /dev/null\necho \'[{"RuleID": "github-pat", "StartLine": 12}]\'\nexit 3\n',
    )

    result = published(live, transcript, "--yes")

    assert (result.returncode, github.state()["calls"]) == (0, [])
    assert "gitleaks reads a secret in it: github-pat at line 12" in result.stderr


def test_a_rerun_never_comments_on_the_issue_it_just_filed(live: Live) -> None:
    github = fake_github(live.sandbox)
    transcript = stories_ready(live)
    published(live, transcript, "--yes")
    live.fake.same = {100: 0.95}

    again = published(live, transcript, "--yes")

    assert (again.returncode, again.stdout) == (0, "")
    assert github.state()["calls"] == [["create", 100]]


def test_publish_needs_consent_for_the_sessions_repo_too(live: Live) -> None:
    fake_github(
        live.sandbox,
        issues=[open_issue(7, "alpha: flags are stale")],
        visibility={"o/secret-proj": "PRIVATE"},
    )
    live.sandbox.consent(
        **{PUBLIC: "typesafe-2026-09-26", "o/secret-proj": "typesafe-2026-09-26"}
    )
    work = live.sandbox.home / "work"
    work.mkdir()
    transcript = stories_ready(live, work, "--repo", "o/secret-proj")
    live.sandbox.consent(**{PUBLIC: "typesafe-2026-09-26"})
    sent = len(live.fake.bodies)

    result = published(live, transcript, "--yes")

    assert (result.returncode, len(live.fake.bodies)) == (1, sent)
    assert "o/secret-proj has no consent" in result.stderr


def test_a_story_merging_items_of_several_skills_is_held(live: Live) -> None:
    github = fake_github(live.sandbox)
    live.fake.friction = {2: 0.92}
    live.fake.covered = {"alpha": 0.9, "beta": 0.1}
    transcript = friction_session(
        live.sandbox, ("alpha", ALPHA), ("beta", "Beta body\n")
    )
    live.scan(transcript)
    fake_agent(live.sandbox, "claude", story("", items=["alpha-e2", "beta-e2"]))
    assert written(live, transcript, "--yes").returncode == 0

    result = published(live, transcript, "--yes")

    assert (result.returncode, github.state()["calls"]) == (0, [])
    assert "it merges items of several skills; publish it by hand" in result.stderr


def test_a_duplicate_closed_after_the_check_is_held(live: Live) -> None:
    github = fake_github(
        live.sandbox,
        issues=[open_issue(7, "alpha: flags are stale")],
        closed_on_view=[7],
    )
    live.fake.same = {7: 0.91}
    transcript = stories_ready(live)

    result = published(live, transcript, "--yes")

    assert (result.returncode, github.state()["calls"]) == (0, [])
    assert "#7 closed after the duplicate check; decide by hand" in result.stderr


def test_a_write_that_does_not_read_back_fails(live: Live) -> None:
    fake_github(live.sandbox, drop_labels=True)
    transcript = stories_ready(live)

    result = published(live, transcript, "--yes")

    assert result.returncode == 1
    assert f"{PUBLIC}#100 does not show what publish just wrote" in result.stderr

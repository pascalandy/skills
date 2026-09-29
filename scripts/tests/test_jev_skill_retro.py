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
from dataclasses import dataclass
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
            file["read_at"],
        )
        for file in files
    ] == [
        (f"{alpha}/SKILL.md", "excerpt", False, 1, 3, 0),
        (str(reference), "file", True, 10, 2, 1),
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
        .tool(
            "t0",
            "WebFetch",
            {"url": "https://example.com/alpha-guide"},
            "Request failed with status code 404",
            True,
        )
        .load(alpha, ALPHA)
        .tool(
            "t1",
            "WebFetch",
            {"url": "https://example.com/alpha-guide"},
            "Request failed with status code 404",
            True,
        )
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


def test_a_tool_or_the_agent_quoting_the_skill_marker_loads_nothing(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha")
    marker = f"Base directory for this skill: {alpha}"
    transcript = (
        Claude(sandbox.repo)
        .tool("t1", "Bash", {"command": "grep -r 'Base directory' ."}, f"{marker}\n")
        .say(f"The transcript shows:\n{marker}")
        .write(sandbox.home / "session.jsonl")
    )

    assert sandbox.scan(transcript)["skills"] == []


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


def test_triage_splits_at_a_reload_so_each_event_sees_the_version_it_followed(
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

    bodies = sandbox.planned(sandbox.scan(transcript))

    assert [
        (body["state"]["skills"][0]["text"], sorted(body["questions"]))
        for body in bodies
    ] == [
        ("Old text", ["friction::alpha::0"]),
        ("New text", ["friction::alpha::1"]),
    ]


def test_a_url_a_later_version_dropped_is_no_broken_link_after_the_reload(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha")
    failed = "Request failed with status code 404"
    transcript = (
        Claude(sandbox.repo)
        .load(alpha, ALPHA)
        .tool(
            "t1", "WebFetch", {"url": "https://example.com/alpha-guide"}, failed, True
        )
        .load(alpha, "Use `alpha-cli` only.")
        .tool(
            "t2", "WebFetch", {"url": "https://example.com/alpha-guide"}, failed, True
        )
        .write(sandbox.home / "session.jsonl")
    )

    assert [(f["event"], f["kind"]) for f in sandbox.scan(transcript)["facts"]] == [
        (0, "broken_link")
    ]


def test_codex_trusts_a_structured_status_over_text_the_command_printed(
    sandbox: Sandbox,
) -> None:
    alpha = sandbox.installed("alpha", ".codex")
    transcript = (
        Codex(sandbox.repo)
        .exec("c1", [f"cat {alpha}/SKILL.md"], [(0, skill_md("alpha", ALPHA))])
        .exec("c2", [f"cat {alpha}/references/errors.md"], [(1, "Permission denied")])
        .exec(
            "c3",
            ["cat notes.md"],
            [(0, "Process exited with code 127\nalpha-cli: command not found")],
        )
        .write(sandbox.home / "rollout.jsonl")
    )

    report = sandbox.scan(transcript)

    assert [file["path"] for file in report["skills"][0]["files"]] == [
        f"{alpha}/SKILL.md"
    ]
    assert report["facts"] == []


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
            "/bin/sh: make: not found",
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


@exits(SCRIPT, 1)
def test_a_live_scan_is_refused_before_reading_anything(sandbox: Sandbox) -> None:
    result = sandbox.run("scan", "missing-session")

    assert (result.returncode, result.stdout) == (1, "")
    assert "a live scan is not available yet" in result.stderr


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

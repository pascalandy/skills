#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Find where the skills a finished agent session loaded caused friction.

`scan` reads one Claude Code or Codex transcript, finds the skills the session
loaded from this repository or the private clone, and plans the questions Jev,
TypeSafe's typed-judgment model, answers about them. The design and its
decisions live in https://github.com/pascalandy/skills/issues/177.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import shlex
import shutil
import subprocess
import urllib.error
import urllib.request
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import install_skills
import tomllib
from _cli import (
    Parser,
    ScriptError,
    TemporaryError,
    UsageError,
    duration,
    exit_codes,
)
from _common import exclusive, run, run_script

log = logging.getLogger("jev-skill-retro")

PROG = "just jev-skill-retro"
ROOT = install_skills.ROOT
EXIT_CODES = exit_codes(
    {
        1: "failure: an unreadable transcript, missing consent, a secret, a TypeSafe "
        "error, or a request that may have been billed without an answer",
        75: "TypeSafe was unreachable or rate-limited, or another run holds this "
        "session's lock; rerun later, and saved answers are reused",
    }
)
EXAMPLES = f"""\
examples:
  {PROG} scan 6d88c057-abeb-41cc-ab08-195310f0b63b --dry-run
  {PROG} scan 6d88c057-abeb-41cc-ab08-195310f0b63b
  {PROG} scan ~/.codex/sessions/2026/09/28/rollout-2026-09-28T12-53-45-01a0.jsonl --json
  {PROG} write 6d88c057-abeb-41cc-ab08-195310f0b63b --dry-run"""

# Jev 1.13's limits: 32k tokens for state plus the longest question, 64k in all
STATE_LIMIT = 32_000
REQUEST_LIMIT = 64_000
# A conservative estimate: most text runs 3 to 4 bytes per token
BYTES_PER_TOKEN = 3
# An event keeps this many characters from each end of its text
EVENT_EDGE = 800

# label-for-issues-jev owns consent; its file and terms name decide what may leave
TERMS_NAME = "typesafe-2026-09-26"
CONSENT_FIX = (
    "uv run authoring/devtools/label-for-issues-jev/scripts/jevlabel.py "
    'consent add {repo} --by "<their name>"'
)

SKILL_MARKER = "Base directory for this skill: "
SKILL_START = re.compile(rf"(?m)^{re.escape(SKILL_MARKER)}")
ARGUMENTS = re.compile(r"\n\nARGUMENTS: .*\Z", re.DOTALL)
# A path that ends in <install directory>/<skill>/SKILL.md
SKILL_FILE = re.compile(r"(?:~|/)[^\s'\"`;|&()]*?/([A-Za-z0-9][\w.-]*)/SKILL\.md")
NUMBERED_LINE = re.compile(r"^\s*(\d+)\t(.*)$")
URL = re.compile(r"https?://[^\s)\]>\"'`]+")
MISSING_COMMAND = re.compile(
    r"(?:^|\s)([\w./-]+): (?:command )?not found|command not found: ([\w./-]+)",
    re.MULTILINE,
)
GITHUB = re.compile(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$")
JS_COMMAND = re.compile(r"\bcmd\s*:\s*(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`[^`]*`)")
EXIT_CODE = re.compile(r"\"exit_code\"\s*:\s*(-?\d+)")
# An exit status at the very start of a tool result, where Codex puts its envelope
TEXT_EXIT = re.compile(r"\A\s*(?:Process exited with code|Exit code:?)\s*(-?\d+)")
# Evidence that a fetch itself failed: an HTTP error status or an unresolved host
FETCH_FAILED = re.compile(
    r"status(?: code)?:? (?:40[34]|410|5\d\d)\b|returned error: (?:40[34]|410|5\d\d)\b"
    r"|\bHTTP(?:/[\d.]+)? (?:40[34]|410|5\d\d)\b|\b(?:404 Not Found|403 Forbidden|410 Gone)\b"
    r"|could not resolve host|failed to fetch|unable to resolve",
    re.IGNORECASE,
)
# One command that prints one file: cat, rtk cat, nl -ba, or sed -n 'A,Bp'
SINGLE_READ = re.compile(
    r"^\s*(?:(?:rtk\s+)?cat|nl\s+-ba)\s+(?P<path>\S+)\s*$"
    r"|^\s*sed\s+-n\s+'?(?P<first>\d+),\d+p'?\s+(?P<ranged>\S+)\s*$"
)
OUTPUT_FIELD = re.compile(r"\"output\"\s*:\s*\"")
# Up to five frontmatter lines before `name:`, none of them the closing ---
OPENER = r"(?:(?!---\n)[^\n]*\n){0,5}?"

TRIAGE = {
    "instructions": (
        "Does `events[{event}]` show the agent failing, retrying, hesitating, or "
        "being corrected by the user while applying an instruction from `skills[{skill}]`?"
    ),
    "criteria": {
        "true": (
            "A failed attempt, a retry, expressed doubt, or a user correction "
            "concerning an instruction of that skill"
        ),
        "false": "Normal progress, or difficulty unrelated to that skill's instructions",
    },
}

MODEL = "jev-1.13.0"
BASE_URL = "https://api.typesafe.ai"
KEYRING = ("secret", "keyring", "get", "--service=typesafe_ai", "--user=api_key")
# Dollars per input token for jev-1.13.0; output tokens are free
PRICE = 0.042 / 1_000_000

# Starting guesses from TypeSafe's self-consistency cookbooks, not measurements.
# A Noul counts as no at or below NO and as yes at or above YES; a Choice counts
# only when its top probability reaches TOP.
CALIBRATION = (
    "uncalibrated: milestone 3 of issue #177 measures these on the 2026-09-28 retro"
)
NO = 0.30
YES = 0.70
TOP = 0.60
# The most flagged events per skill that go on to locate and qualify
RETAINED = 5
# A Choice holds at most 255 options: a window of lines leaves room for `none`
WINDOW = 240

LOCATE = (
    "Which line of `files[{file}]` gives the instruction the agent was carrying "
    "out in `event`?"
)
COVERED = {
    "instructions": (
        "Does any line of {files} address the step the agent was carrying out in `event`?"
    ),
    "criteria": {
        "true": "At least one line states how to do this step",
        "false": "No line addresses this step",
    },
}
RELATION = {
    "type": "choice",
    "instructions": "How does what happened in `event` relate to the instruction in `line`?",
    "criteria": {
        "contradicted": (
            "What the agent found (a file, command output, flag, path, or behavior) "
            "differs from what `line` states"
        ),
        "incomplete": "`line` covers this step but leaves out a detail the agent needed",
        "ambiguous": (
            "`line` can be read more than one way, and the agent's reading led to the problem"
        ),
        "not_followed": "The agent did something other than what `line` says",
        "unrelated": (
            "The problem came from outside `line`: the machine, the network, a service, "
            "or a change in the request"
        ),
        "cannot-tell": "`event` does not show enough to tell",
    },
}
SKILL_SIDE = ("contradicted", "incomplete", "ambiguous")
# HTTP statuses that mean TypeSafe refused a request without running it
# 529 is TypeSafe's own overload answer, which its docs say to retry; a 503 may
# come from a gateway after the request ran, so it stays pending
REJECTED = frozenset({400, 401, 403, 404, 409, 413, 422, 429, 529})
TOOL_UNAVAILABLE = {
    "type": "noul",
    "instructions": (
        "Does `event` show that a program, API, credential, or permission that `line` "
        "relies on was unavailable?"
    ),
    "criteria": {
        "true": "Something `line` needs was missing or refused",
        "false": "Everything `line` needs was available",
    },
}
RECURS = {
    "type": "noul",
    "instructions": (
        "Would another agent following `line` as written likely hit the problem in "
        "`event` again in ordinary use?"
    ),
    "criteria": {
        "true": "The problem sits on a common path of the skill",
        "false": "The problem needs rare or one-off circumstances of this session",
    },
}
CONFLICT = {
    "type": "noul",
    "instructions": "Do `line` and `other_line` tell the agent to do opposite things for this step?",
    "criteria": {
        "true": "Following one breaks the other",
        "false": "They agree or cover different things",
    },
}


@dataclass
class Event:
    """One user message, agent message, or tool call with its result."""

    index: int
    actor: str
    text: str
    error: bool = False
    call: str = ""
    # The transcript itself cut this event's result short
    partial: bool = False


@dataclass
class SkillFile:
    """Text the agent read from one file of a loaded skill."""

    path: str
    text: str
    # "file" when the numbers are the file's own, "excerpt" when they count
    # from the start of what the transcript shows
    anchor: str
    partial: bool = False
    first_line: int = 1
    # The first event that could have followed this text
    read_at: int = 0

    def numbered(self) -> list[str]:
        return [
            f"{self.first_line + offset}\t{line}"
            for offset, line in enumerate(self.text.splitlines())
        ]

    def digest(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()


@dataclass
class Load:
    """A skill the session read successfully, from the event after which it applies."""

    skill: str
    directory: str
    after: int
    files: list[SkillFile] = field(default_factory=list)
    status: str = ""
    home: str | None = None


@dataclass
class Session:
    harness: str
    id: str
    path: Path
    cwd: str
    repo_url: str = ""
    model: str = ""
    events: list[Event] = field(default_factory=list)
    loads: list[Load] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add(self, actor: str, text: str, error: bool = False, call: str = "") -> Event:
        event = Event(len(self.events), actor, text, error, call)
        self.events.append(event)
        return event


# --- Transcripts ---------------------------------------------------------------


def locate(target: str) -> Path:
    """The transcript a session ID or path names."""
    path = Path(target).expanduser()
    if path.is_file():
        return path
    if "/" in target or target.endswith(".jsonl"):
        raise ScriptError(f"no transcript at {target}", f"ls {shlex.quote(target)}")
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME") or home / ".codex")
    found = sorted(
        [
            *(home / ".claude/projects").glob(f"*/{target}.jsonl"),
            *(codex_home / "sessions").glob(f"**/rollout-*-{target}.jsonl"),
        ]
    )
    if not found:
        raise ScriptError(
            f"no Claude Code or Codex transcript has the session ID {target}",
            "pass the transcript's path instead of its ID",
        )
    if len(found) > 1:
        raise UsageError(
            f"session ID {target} matches {len(found)} transcripts; pass one path: "
            + ", ".join(str(path) for path in found)
        )
    return found[0]


def records(path: Path) -> Iterator[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise ScriptError(f"cannot read {path}: {error}") from error
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ScriptError(f"{path}:{number} is not JSON: {error.msg}") from error
        if isinstance(record, dict):
            yield record


def read_session(path: Path) -> Session:
    items = list(records(path))
    if any(item.get("type") == "session_meta" for item in items):
        return read_codex(path, items)
    if any("sessionId" in item for item in items):
        return read_claude(path, items)
    raise ScriptError(
        f"{path} is neither a Claude Code nor a Codex transcript",
        "pass a Claude Code project .jsonl or a Codex rollout .jsonl",
    )


def texts(content: Any) -> str:
    """The text of a message or tool result, whatever shape it arrives in."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    if isinstance(content, dict):
        return str(content.get("text") or content.get("output") or "")
    return ""


def skill_body(text: str) -> tuple[str, str]:
    """The directory and the SKILL.md text Claude Code injected for a skill."""
    header, _, body = text.partition("\n")
    directory = header.removeprefix(SKILL_MARKER).strip()
    return directory, ARGUMENTS.sub("", body.lstrip("\n")).rstrip("\n")


def numbered_read(text: str) -> tuple[int, str] | None:
    """The first line number and text of a Read result, or None when it has none."""
    numbers: list[int] = []
    lines: list[str] = []
    for line in text.splitlines():
        match = NUMBERED_LINE.match(line)
        if match is None:
            if numbers:
                break
            continue
        numbers.append(int(match[1]))
        lines.append(match[2])
    if not numbers:
        return None
    return numbers[0], "\n".join(lines)


def claude_text(session: Session, actor: str, text: str, after: int) -> None:
    """Add `text` as an event, or split off the SKILL.md Claude Code injected
    into it as a load that applies from event `after`."""
    found = SKILL_START.search(text)
    before = text if found is None else text[: found.start()]
    if before.strip() and not before.startswith("<system-reminder>"):
        session.add(actor, before)
        after += 1
    if found is None:
        return
    directory, body = skill_body(text[found.start() :])
    session.loads.append(
        Load(
            Path(directory).name,
            directory,
            after,
            [SkillFile(f"{directory}/SKILL.md", body, "excerpt", read_at=after)],
        )
    )


def read_claude(path: Path, items: list[dict[str, Any]]) -> Session:
    first = next(item for item in items if "sessionId" in item)
    session = Session(
        "claude", str(first["sessionId"]), path, str(first.get("cwd", ""))
    )
    calls: dict[str, Event] = {}
    reads: dict[str, dict[str, Any]] = {}
    for item in items:
        if item.get("isSidechain") or item.get("type") not in ("user", "assistant"):
            continue
        message = item.get("message") or {}
        content = message.get("content")
        actor = "agent" if item["type"] == "assistant" else "user"
        if item["type"] == "assistant":
            model = message.get("model") or ""
            if model and not model.startswith("<"):
                session.model = model
        if isinstance(content, str):
            claude_text(session, actor, content, len(session.events))
            continue
        for block in content or []:
            if not isinstance(block, dict):
                continue
            kind = block.get("type")
            if kind == "text":
                claude_text(session, actor, block.get("text", ""), len(session.events))
            elif kind == "tool_use":
                name = str(block.get("name", ""))
                arguments = block.get("input") or {}
                event = session.add("tool", f"{name}: {json.dumps(arguments)}")
                calls[str(block.get("id"))] = event
                if name == "Read" and isinstance(arguments, dict):
                    reads[str(block.get("id"))] = arguments
            elif kind == "tool_result":
                call = str(block.get("tool_use_id"))
                result = texts(block.get("content"))
                error = bool(block.get("is_error"))
                event = calls.get(call) or session.add("tool", "")
                found = None if error else SKILL_START.search(result)
                shown = result if found is None else result[: found.start()]
                event.text = f"{event.text}\n{shown}".strip("\n")
                event.error = event.error or error
                event.partial = event.partial or "Output too large" in result
                event.call = call
                if found is not None:
                    claude_text(
                        session, "tool", result[found.start() :], event.index + 1
                    )
                if call in reads and not error:
                    record_read(session, reads[call], result, event.index)
    return session


def record_read(
    session: Session, arguments: dict[str, Any], result: str, index: int
) -> None:
    """Count a successful Read of a skill's files as that skill's evidence."""
    target = str(arguments.get("file_path", ""))
    shown = numbered_read(result)
    if shown is None:
        return
    first, text = shown
    partial = "offset" in arguments or "limit" in arguments
    if target.endswith("/SKILL.md") and installed(Path(target).parent):
        session.loads.append(
            Load(
                Path(target).parent.name,
                str(Path(target).parent),
                index + 1,
                [SkillFile(target, text, "file", partial, first, index + 1)],
            )
        )
        return
    for load in reversed(session.loads):
        if target.startswith(load.directory.rstrip("/") + "/"):
            load.files.append(
                SkillFile(target, text, "file", partial, first, index + 1)
            )
            return


def js_string(literal: str) -> str:
    if literal[0] == '"':
        try:
            return json.loads(literal)
        except json.JSONDecodeError:
            return literal[1:-1]
    return literal[1:-1]


def commands_of(kind: str, payload: dict[str, Any]) -> list[str]:
    """The shell commands one Codex tool call ran."""
    if kind == "custom_tool_call":
        return [
            js_string(m[1]) for m in JS_COMMAND.finditer(str(payload.get("input", "")))
        ]
    try:
        arguments = json.loads(payload.get("arguments") or "{}")
    except json.JSONDecodeError:
        return []
    command = arguments.get("cmd") or arguments.get("command") or ""
    return [shlex.join(command) if isinstance(command, list) else str(command)]


def outputs_of(output: Any) -> tuple[list[str], bool, bool]:
    """The command outputs inside one Codex tool result, whether a command
    failed, and whether Codex truncated the result."""
    raw = output if isinstance(output, str) else json.dumps(output)
    text = raw
    try:
        decoded = json.loads(raw)
        text = texts(decoded) if not isinstance(decoded, str) else decoded
    except json.JSONDecodeError:
        pass
    # The exit codes may sit in the raw result, escaped once, or in its text
    raw = raw.replace('\\"', '"')
    found: list[str] = []
    decoder = json.JSONDecoder()
    for match in OUTPUT_FIELD.finditer(text):
        try:
            value, _ = decoder.raw_decode(text, match.end() - 1)
        except json.JSONDecodeError:
            continue
        if isinstance(value, str):
            found.append(value)
    codes = EXIT_CODE.findall(raw) + EXIT_CODE.findall(text)
    if not codes and (envelope := TEXT_EXIT.match(text)):
        codes = [envelope[1]]
    failed = any(int(code) != 0 for code in codes) or (
        '"status":"rejected"' in f"{raw}{text}".replace(" ", "")
    )
    return found or [text], failed, "truncated output" in text


def frontmatter_text(output: str, name: str) -> str | None:
    """The SKILL.md of `name` inside a command's output, split from any file
    printed after it."""
    start = re.search(
        rf"(?m)^---\n{OPENER}name:[ \t]*\"?{re.escape(name)}\"?[ \t]*\n",
        output,
    )
    if start is None:
        return None
    rest = output[start.start() :]
    following = re.search(rf"\n---\n{OPENER}name:[ \t]*\S", rest[4:])
    end = following.start() + 4 if following else len(rest)
    return rest[:end].rstrip("\n")


def read_codex(path: Path, items: list[dict[str, Any]]) -> Session:
    meta = next(item["payload"] for item in items if item.get("type") == "session_meta")
    session = Session(
        "codex",
        str(meta.get("id", "")),
        path,
        str(meta.get("cwd", "")),
        str((meta.get("git") or {}).get("repository_url", "")),
    )
    calls: dict[str, tuple[Event, list[str]]] = {}
    for item in items:
        payload = item.get("payload") or {}
        if item.get("type") == "turn_context" and payload.get("model"):
            session.model = str(payload["model"])
        if item.get("type") != "response_item":
            continue
        kind = payload.get("type")
        if kind == "message":
            role = payload.get("role")
            for block in payload.get("content") or []:
                text = block.get("text", "") if isinstance(block, dict) else ""
                injected = text.startswith(("<", "# AGENTS.md instructions"))
                if role in ("user", "assistant") and text.strip() and not injected:
                    session.add("user" if role == "user" else "agent", text)
        elif kind in ("custom_tool_call", "function_call"):
            commands = commands_of(kind, payload)
            detail = payload.get("input") or payload.get("arguments") or ""
            event = session.add("tool", f"{payload.get('name', '')}: {detail}")
            calls[str(payload.get("call_id"))] = (event, commands)
        elif kind in ("custom_tool_call_output", "function_call_output"):
            call = str(payload.get("call_id"))
            if call not in calls:
                continue
            event, commands = calls[call]
            outputs, failed, truncated = outputs_of(payload.get("output"))
            event.text = f"{event.text}\n" + "\n".join(outputs)
            event.error = failed
            event.partial = truncated
            event.call = call
            record_cats(session, commands, outputs, truncated, failed, event.index)
    return session


def record_cats(
    session: Session,
    commands: list[str],
    outputs: list[str],
    truncated: bool,
    failed: bool,
    index: int,
) -> None:
    """Count each SKILL.md a command printed, when its text is in the output,
    and each file a successful single-file read printed beneath a loaded skill."""
    for command in commands:
        for match in SKILL_FILE.finditer(command):
            target = match[0]
            directory = str(Path(target).parent)
            if not installed(Path(target).expanduser().parent):
                continue
            text = next(
                (
                    found
                    for output in outputs
                    if (found := frontmatter_text(output, match[1]))
                ),
                None,
            )
            if text is None:
                session.notes.append(
                    f"event {index} mentions {target}, but its output does not show that file"
                )
                continue
            session.loads.append(
                Load(
                    match[1],
                    directory,
                    index + 1,
                    [SkillFile(target, text, "file", truncated, read_at=index + 1)],
                )
            )
    if failed or len(commands) != len(outputs):
        return
    for command, output in zip(commands, outputs):
        read = SINGLE_READ.match(command)
        if read is None:
            continue
        target = read["path"] or read["ranged"]
        if target.endswith("/SKILL.md"):
            continue
        resolved = str(Path(target).expanduser())
        for load in reversed(session.loads):
            if resolved.startswith(str(Path(load.directory).expanduser()) + "/"):
                shown = (
                    numbered_read(output) if command.lstrip().startswith("nl") else None
                )
                first, text = shown or (int(read["first"] or 1), output.rstrip("\n"))
                partial = truncated or read["first"] is not None
                load.files.append(
                    SkillFile(target, text, "file", partial, first, index + 1)
                )
                break


def installed(directory: Path) -> bool:
    """Whether a skill directory sits in a directory `just install-skills` writes."""
    parent = directory.parent.as_posix()
    targets = {
        target for profile in install_skills.PROFILES.values() for target in profile
    } | {install_skills.CODEX_SKILLS}
    return any(parent.endswith("/" + target) for target in targets)


# --- Roster, repositories, and facts ------------------------------------------


def git_remote(directory: Path) -> str:
    if not directory.is_dir():
        return ""
    found = run(
        ["git", "-C", str(directory), "remote", "get-url", "origin"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=30,
    )
    return found.stdout.strip() if found.returncode == 0 else ""


def github_name(url: str) -> str | None:
    match = GITHUB.search(url.strip())
    return f"{match[1]}/{match[2]}" if match else None


def roster() -> dict[str, str | None]:
    """Each skill of this repository and the private clone, with its home repo."""
    homes: dict[str, str | None] = {}
    public = github_name(git_remote(ROOT))
    for entry in sorted((ROOT / "skills").glob("*/SKILL.md")):
        homes[entry.parent.name] = public
    private_packages = install_skills.private_packages(None)
    if private_packages:
        private = github_name(git_remote(install_skills.PRIVATE))
        for name in private_packages:
            homes[name] = private
    return homes


def classify(session: Session) -> None:
    """Mark each load as the roster's or a third party's, with its home repo."""
    homes = roster()
    for load in session.loads:
        if load.skill in homes and installed(Path(load.directory).expanduser()):
            load.status = "roster"
            load.home = homes[load.skill]
        else:
            load.status = "third-party"


def session_repo(session: Session, override: str | None) -> str | None:
    if override:
        return override
    return github_name(session.repo_url) or github_name(git_remote(Path(session.cwd)))


def facts(session: Session) -> list[dict[str, Any]]:
    """Hard failures tied to a literal of a loaded skill; each proves the event,
    not its cause."""
    found: list[dict[str, Any]] = []
    for load in session.loads:
        if load.status != "roster":
            continue
        text = "\n".join(file.text for file in load.files)
        urls = set(URL.findall(text))
        later = [
            other.after
            for other in session.loads
            if other.skill == load.skill and other.after > load.after
        ]
        for event in session.events[load.after : min(later, default=None)]:
            if not event.error:
                continue
            for url in sorted(urls):
                if url in event.text and FETCH_FAILED.search(event.text):
                    found.append(fact(load, event, "broken_link", url))
            for match in MISSING_COMMAND.finditer(event.text):
                command = Path(match[1] or match[2]).name
                if re.search(rf"(?<![\w-]){re.escape(command)}(?![\w-])", text):
                    found.append(fact(load, event, "tool_unavailable", command))
            if "Traceback (most recent call last)" in event.text and (
                f"/{load.skill}/scripts/" in event.text
            ):
                found.append(fact(load, event, "script_bug", f"{load.skill}/scripts"))
    unique = {json.dumps(item, sort_keys=True): item for item in found}
    return sorted(unique.values(), key=lambda item: (item["event"], item["skill"]))


def fact(load: Load, event: Event, kind: str, detail: str) -> dict[str, Any]:
    return {"skill": load.skill, "event": event.index, "kind": kind, "detail": detail}


# --- Consent and secrets -------------------------------------------------------


def consent_file() -> Path:
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return config / "label-for-issues-jev" / "consent.toml"


def consent(repos: Iterable[str]) -> dict[str, bool]:
    """Whether each repo has an entry under the current terms. Public repos need
    one too: a transcript is private even when its repo is public."""
    path = consent_file()
    try:
        entries = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        entries = {}
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ScriptError(f"{path} is unreadable: {error}; fix or delete it") from error
    return {
        repo: isinstance(entries.get(repo), dict)
        and entries[repo].get("terms") == TERMS_NAME
        for repo in sorted(set(repos))
    }


def secrets(text: str, timeout: float) -> list[str] | None:
    """What gitleaks finds in `text`, never the values; None when it is missing."""
    gitleaks = shutil.which("gitleaks")
    if gitleaks is None:
        return None
    try:
        found = run(
            [
                gitleaks,
                "stdin",
                "--no-banner",
                "--log-level",
                "error",
                "--redact",
                "--report-format",
                "json",
                "--report-path",
                "-",
                "--exit-code",
                "3",
            ],
            input=text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ScriptError(f"gitleaks took longer than {timeout:g}s") from None
    if found.returncode not in (0, 3):
        raise ScriptError(f"gitleaks failed: {found.stderr.strip()}")
    try:
        report = json.loads(found.stdout or "[]")
    except json.JSONDecodeError:
        report = []
    return sorted(
        {
            f"{leak.get('RuleID', 'secret')} at line {leak.get('StartLine', '?')}"
            for leak in report
        }
    ) or ([] if found.returncode == 0 else ["a secret gitleaks could not locate"])


# --- Requests ------------------------------------------------------------------


def tokens(value: Any) -> int:
    """A conservative token estimate for a JSON value."""
    size = len(json.dumps(value, ensure_ascii=False).encode("utf-8"))
    return math.ceil(size / BYTES_PER_TOKEN)


def shorten(text: str) -> str:
    if len(text) <= 2 * EVENT_EDGE:
        return text
    omitted = len(text) - 2 * EVENT_EDGE
    return (
        f"{text[:EVENT_EDGE]}\n[… {omitted} characters omitted …]\n{text[-EVENT_EDGE:]}"
    )


def triage_skills(session: Session) -> list[Load]:
    """The first load of each roster skill whose text the session shows."""
    first: dict[str, Load] = {}
    for load in session.loads:
        if load.status == "roster" and load.files and load.skill not in first:
            first[load.skill] = load
    return sorted(first.values(), key=lambda load: load.after)


def version_at(session: Session, skill: str, index: int) -> Load:
    """The version of `skill` the agent had read by event `index`: its latest load."""
    loaded = [
        load
        for load in session.loads
        if load.skill == skill and load.status == "roster" and load.files
    ]
    before = [load for load in loaded if load.after <= index]
    return (before or loaded)[-1]


def triage_request(
    session: Session, events: list[Event], skills: list[Load]
) -> dict[str, Any]:
    """One A request: the text of every skill loaded by its last event, in the
    latest version read, the events, and one friction question per skill and
    each event after that skill first loaded."""
    shown = [load for load in skills if load.after <= events[-1].index]
    state = {
        "skills": [
            {
                "name": load.skill,
                "text": version_at(session, load.skill, events[-1].index).files[0].text,
            }
            for load in shown
        ],
        "events": [
            {
                "id": event.index,
                "actor": event.actor,
                "text": shorten(event.text),
                "error": event.error,
            }
            for event in events
        ],
    }
    questions: dict[str, Any] = {}
    for position, event in enumerate(events):
        for number, load in enumerate(shown):
            if event.index >= load.after:
                questions[f"friction::{load.skill}::{event.index}"] = {
                    "type": "noul",
                    "instructions": TRIAGE["instructions"].format(
                        event=position, skill=number
                    ),
                    "criteria": TRIAGE["criteria"],
                }
    return {"state": state, "questions": questions}


def fits(request: dict[str, Any]) -> bool:
    longest = max((tokens(q) for q in request["questions"].values()), default=0)
    state = tokens(request["state"])
    return state + longest <= STATE_LIMIT and tokens(request) <= REQUEST_LIMIT


def plan_triage(session: Session) -> tuple[list[dict[str, Any]], list[int]]:
    """A requests that each fit Jev's limits, and the events too large for any."""
    skills = triage_skills(session)
    if not skills:
        return [], []
    start = skills[0].after
    first = {id(load) for load in skills}
    reloads = {
        load.after
        for load in session.loads
        if load.status == "roster" and load.files and id(load) not in first
    }
    planned: list[dict[str, Any]] = []
    oversized: list[int] = []
    chunk: list[Event] = []
    for event in session.events[start:]:
        if chunk and event.index in reloads:
            planned.append(triage_request(session, chunk, skills))
            chunk = []
        if fits(triage_request(session, [*chunk, event], skills)):
            chunk.append(event)
            continue
        if chunk:
            planned.append(triage_request(session, chunk, skills))
        if fits(triage_request(session, [event], skills)):
            chunk = [event]
        else:
            oversized.append(event.index)
            chunk = []
    if chunk:
        planned.append(triage_request(session, chunk, skills))
    return planned, oversized


def operation(kind: str, body: Any) -> str:
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    return f"{kind}-{digest[:12]}"


# --- Jev -------------------------------------------------------------------------


class Jev:
    """Sends each request at most once: its answer is saved by operation ID and
    reused on a rerun, and a request whose answer never arrived is resent only
    with --retry, because TypeSafe may have billed it."""

    def __init__(
        self,
        directory: Path,
        *,
        replay: bool,
        retry: set[str],
        timeout: float,
        budget: int,
        repos: set[str],
    ) -> None:
        self.directory = directory
        self.replay = replay
        self.retry = retry
        self.timeout = timeout
        self.budget = budget
        self.repos = repos
        self.key = ""
        self.sent: list[str] = []
        self.reused: list[str] = []
        self.tokens = 0

    def ask(self, kind: str, body: dict[str, Any]) -> dict[str, Any]:
        op = operation(kind, body)
        path = self.directory / "ops" / f"{op}.json"
        record = json.loads(path.read_text()) if path.exists() else {}
        if record.get("state") == "done":
            self.reused.append(op)
            return record["answers"]
        if self.replay:
            raise ScriptError(
                f"request {op} has no saved answer, so --replay cannot decide",
                f"run {PROG} scan without --replay",
            )
        if record.get("state") == "sent" and op not in self.retry:
            raise ScriptError(
                f"request {op} was sent but its answer never arrived; TypeSafe may have billed it",
                f"rerun with --retry {op} to send it again",
            )
        if len(self.sent) >= self.budget:
            raise ScriptError(
                f"the scan stopped at its budget of {self.budget} requests; answers so far are saved",
                "rerun with a larger --max-requests; saved answers are reused",
            )
        if not fits(body):
            raise ScriptError(
                f"request {op} exceeds Jev's limits; this is a bug in {PROG}"
            )
        self.check(op, body)
        request_path = self.directory / "requests" / f"{op}.json"
        write_json(request_path, body)
        write_json(path, {"kind": kind, "state": "sent", "request": str(request_path)})
        reply = self.send(op, path, body)
        record = {
            "kind": kind,
            "state": "done",
            "request": str(request_path),
            "model": reply["model"],
            "answers": reply["answers"],
            "usage": reply.get("usage") or {},
        }
        write_json(path, record)
        self.sent.append(op)
        self.tokens += int(record["usage"].get("input_tokens") or 0)
        return record["answers"]

    def check(self, op: str, body: dict[str, Any]) -> None:
        """Consent and a secret scan before each request, so a consent revoked
        mid-run stops the next one."""
        missing = [repo for repo, ok in consent(self.repos).items() if not ok]
        if missing:
            raise ScriptError(
                *(
                    f"{repo} has no consent under {TERMS_NAME}; show Pascal the "
                    "planned requests (scan --dry-run) and TypeSafe's terms, and "
                    f"after he approves run: {CONSENT_FIX.format(repo=repo)}"
                    for repo in missing
                )
            )
        if not self.key:
            self.key = api_key()
        leaks = secrets(json.dumps(body, ensure_ascii=False, indent=2), self.timeout)
        if leaks is None:
            raise ScriptError(
                "gitleaks is not installed, so the payload cannot be checked for secrets",
                "install gitleaks, then rerun",
            )
        if leaks:
            raise ScriptError(
                f"request {op} holds what gitleaks reads as a secret: {'; '.join(leaks)}",
                "remove the secret from the session or scan it with --dry-run to inspect the payload",
            )

    def send(self, op: str, path: Path, body: dict[str, Any]) -> dict[str, Any]:
        url = (
            os.environ.get("TYPESAFE_BASE_URL", BASE_URL).rstrip("/") + "/v1/systemone"
        )
        request = urllib.request.Request(
            url,
            data=json.dumps({**body, "model": MODEL}).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                reply = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in REJECTED:
                # A gateway error may come after TypeSafe ran and billed the request
                raise ScriptError(
                    f"TypeSafe answered HTTP {error.code} for request {op}; it may have "
                    "run and been billed",
                    f"rerun with --retry {op} to send it again",
                ) from error
            write_json(path, {"state": "failed", "status": error.code})
            if error.code in (429, 529):
                raise TemporaryError(
                    f"TypeSafe answered HTTP {error.code}; saved answers are reused on a rerun"
                ) from error
            raise ScriptError(
                f"TypeSafe refused request {op} with HTTP {error.code}"
            ) from error
        except urllib.error.URLError as error:
            write_json(path, {"state": "failed", "reason": str(error.reason)})
            raise TemporaryError(
                f"TypeSafe is unreachable at {url}: {error.reason}"
            ) from error
        except (TimeoutError, ConnectionError) as error:
            raise ScriptError(
                f"request {op} was sent but no answer came back within {self.timeout:g}s; "
                "TypeSafe may have billed it",
                f"rerun with --retry {op} to send it again",
            ) from error
        except (ValueError, UnicodeDecodeError) as error:
            raise ScriptError(
                f"TypeSafe sent an unreadable answer to request {op}"
            ) from error
        if reply.get("model") != MODEL or not isinstance(reply.get("answers"), dict):
            raise ScriptError(
                f"request {op} was answered by {reply.get('model')!r}, not the pinned {MODEL}",
                f"check TypeSafe's models page; this script pins {MODEL}",
            )
        return reply

    def summary(self) -> dict[str, Any]:
        return {
            "model": MODEL,
            "sent": len(self.sent),
            "reused": len(self.reused),
            "input_tokens": self.tokens,
            "cost_usd": round(self.tokens * PRICE, 6),
        }


def api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    chezmoi = shutil.which("chezmoi")
    if not key and chezmoi:
        try:
            found = run(
                [chezmoi, *KEYRING],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=15,
            )
            key = found.stdout.strip() if found.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            key = ""
    if not key:
        raise ScriptError(
            "no TypeSafe API key: TYPESAFE_API_KEY is unset and the chezmoi keyring has none",
            "export TYPESAFE_API_KEY, or run: chezmoi secret keyring set --service=typesafe_ai --user=api_key",
        )
    return key


def noul(answers: dict[str, Any], key: str) -> float:
    return float(answers[key]["noul"])


def choice(answers: dict[str, Any], key: str) -> dict[str, float]:
    return {option: float(p) for option, p in answers[key]["probabilities"].items()}


def top(probabilities: dict[str, float]) -> tuple[str, float]:
    option = max(probabilities, key=lambda name: probabilities[name])
    return option, probabilities[option]


def uncertain(value: float) -> bool:
    return NO < value < YES


# --- Locate and qualify ------------------------------------------------------------


@dataclass
class Window:
    """Consecutive lines of one skill file, small enough for one Choice."""

    skill: str
    file: SkillFile
    lines: list[tuple[int, str]]

    def state(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "path": self.file.path,
            "lines": [f"L{number}: {text}" for number, text in self.lines],
        }

    def options(self) -> dict[str, Any]:
        found: dict[str, Any] = {
            f"L{number}": None for number, text in self.lines if text.strip()
        }
        found["none"] = "No line of this file gives that instruction"
        return found

    def around(self, number: int) -> dict[str, Any]:
        numbered = dict(self.lines)
        return {
            "skill": self.skill,
            "file": self.file.path,
            "anchor": self.file.anchor,
            "number": number,
            "text": numbered.get(number, ""),
            "before": numbered.get(number - 1, ""),
            "after": numbered.get(number + 1, ""),
        }


def windows(skill: str, files: list[SkillFile]) -> list[Window]:
    found: list[Window] = []
    for file in files:
        numbered = list(enumerate(file.text.splitlines(), file.first_line))
        for start in range(0, len(numbered), WINDOW):
            found.append(Window(skill, file, numbered[start : start + WINDOW]))
    return found


def event_state(session: Session, index: int) -> dict[str, Any]:
    def shown(event: Event) -> dict[str, Any]:
        return {
            "id": event.index,
            "actor": event.actor,
            "text": shorten(event.text),
            "error": event.error,
        }

    return {
        "event": shown(session.events[index]),
        "context": [
            shown(session.events[i])
            for i in (index - 1, index + 1)
            if 0 <= i < len(session.events)
        ],
    }


def locate_request(
    session: Session,
    index: int,
    load: Load,
    others: list[Load],
    files: list[SkillFile],
) -> tuple[dict[str, Any], list[Window]]:
    """B1: which line of each file the agent followed, and whether any line of
    each loaded skill covers the step."""
    shown = windows(load.skill, files)
    for other in others:
        shown += windows(other.skill, other.files[:1])
    questions: dict[str, Any] = {}
    for number, window in enumerate(shown):
        questions[f"where::{number}"] = {
            "type": "choice",
            "instructions": LOCATE.format(file=number),
            "criteria": window.options(),
        }
    for skill in [load, *others]:
        indices = [n for n, window in enumerate(shown) if window.skill == skill.skill]
        paths = ", ".join(f"`files[{n}]`" for n in indices)
        questions[f"covered::{skill.skill}"] = {
            "type": "noul",
            "instructions": COVERED["instructions"].format(files=paths),
            "criteria": COVERED["criteria"],
        }
    state = {**event_state(session, index), "files": [w.state() for w in shown]}
    return {"state": state, "questions": questions}, shown


def qualify_request(
    session: Session,
    index: int,
    line: dict[str, Any] | None,
    load: Load,
    other: dict[str, Any] | None,
) -> dict[str, Any]:
    """B2: how the event relates to one line; without a line, only whether the
    problem would recur, judged against the skill's whole SKILL.md."""
    state: dict[str, Any] = event_state(session, index)
    if line is None:
        state["line"] = {"skill": load.skill, "text": load.files[0].text}
        return {"state": state, "questions": {"recurs": RECURS}}
    state["line"] = line
    questions: dict[str, Any] = {
        "relation": RELATION,
        "tool_unavailable": TOOL_UNAVAILABLE,
        "recurs": RECURS,
    }
    if other is not None:
        state["other_line"] = other
        questions["conflict"] = CONFLICT
    return {"state": state, "questions": questions}


def decide(
    covered: float,
    complete: bool,
    recurs: float,
    relation: dict[str, float] | None = None,
    tool: float | None = None,
    conflict: float | None = None,
    located: bool = True,
) -> tuple[str, str]:
    """Rules 2–8 of #177 for one event and line: an outcome and its category."""
    if conflict is not None and conflict >= YES:
        return "candidate", "conflict"
    if covered <= NO and complete and recurs >= YES:
        return "candidate", "missing_information"
    read = [covered, recurs, *(v for v in (tool, conflict) if v is not None)]
    if relation is not None:
        option, p = top(relation)
        if sum(relation.get(name, 0.0) for name in SKILL_SIDE) >= YES and recurs >= YES:
            typed = (
                option if option in SKILL_SIDE and p >= TOP else "skill_side_unclear"
            )
            return "candidate", typed
        if tool is not None and tool >= YES and recurs >= YES:
            return "candidate", "tool_unavailable"
        if option in ("not_followed", "unrelated") and p >= TOP:
            return "nothing", option
        if p < TOP or option == "cannot-tell":
            return "review", "relation_unclear"
    if any(uncertain(v) for v in read):
        return "review", "uncertain_answer"
    if not located:
        return "review", "location_unclear"
    if not complete:
        return "review", "partial_evidence"
    return "nothing", "no_rule_matched"


def examine(
    session: Session, first: Load, skills: list[Load], index: int, jev: Jev
) -> dict[str, Any]:
    """Locate and qualify one flagged event, then decide it."""
    load = version_at(session, first.skill, index)
    others = [
        version_at(session, s.skill, index)
        for s in skills
        if s.skill != load.skill and s.after <= index
    ]
    item: dict[str, Any] = {"event": index, "version": load.files[0].digest()[:12]}
    # Only what the agent had read by this event
    read = [file for file in load.files if file.read_at <= index]
    # Shrink the evidence until it fits: other skills first, then references
    tries = [(read, others), (read, []), (read[:1], [])]
    planned = [locate_request(session, index, load, o, f) for f, o in tries]
    fitting = next(
        ((b, w, f) for (b, w), (f, _) in zip(planned, tries) if fits(b)), None
    )
    if fitting is None:
        return {
            **item,
            "outcome": "review",
            "category": "evidence_too_large",
            "line": None,
        }
    body, shown, files = fitting
    located = jev.ask("locate", body)
    covered = noul(located, f"covered::{load.skill}")
    # Dropped evidence or a cut-short event can hide a rule, so they keep it in review
    complete = (
        body is planned[0][0]
        and not any(f.partial for f in files)
        and not session.events[index].partial
    )
    lines: list[dict[str, Any]] = []
    other: dict[str, Any] | None = None
    clear = True
    for number, window in enumerate(shown):
        option, p = top(choice(located, f"where::{number}"))
        if window.skill == load.skill and p < TOP:
            clear = False
        if option == "none" or p < TOP:
            continue
        found = window.around(int(option[1:]))
        if window.skill == load.skill:
            lines.append(found)
        elif other is None and noul(located, f"covered::{window.skill}") >= YES:
            other = found
    item["covered"] = covered
    if not lines:
        request = qualify_request(session, index, None, load, None)
        if not fits(request):
            return {
                **item,
                "outcome": "review",
                "category": "evidence_too_large",
                "line": None,
            }
        recurs = noul(jev.ask("qualify", request), "recurs")
        outcome, category = decide(covered, complete, recurs, located=clear)
        return {
            **item,
            "outcome": outcome,
            "category": category,
            "line": None,
            "recurs": recurs,
        }
    judged: list[dict[str, Any]] = []
    for line in lines:
        answers = jev.ask("qualify", qualify_request(session, index, line, load, other))
        relation = choice(answers, "relation")
        scores = {
            "recurs": noul(answers, "recurs"),
            "tool_unavailable": noul(answers, "tool_unavailable"),
            "conflict": noul(answers, "conflict") if "conflict" in answers else None,
        }
        outcome, category = decide(
            covered,
            complete,
            scores["recurs"],
            relation,
            scores["tool_unavailable"],
            scores["conflict"],
            located=clear,
        )
        judged.append(
            {
                **item,
                "outcome": outcome,
                "category": category,
                "line": line,
                "other_line": other if category == "conflict" else None,
                "relation": relation,
                **scores,
            }
        )
    return max(judged, key=lambda found: STRENGTH[found["outcome"]])


def judge(
    session: Session,
    report: dict[str, Any],
    requests: list[dict[str, Any]],
    oversized: list[int],
    jev: Jev,
) -> list[dict[str, Any]]:
    """Every roster skill's outcome: its strongest event decides."""
    skills = triage_skills(session)
    friction: dict[str, dict[int, float]] = {load.skill: {} for load in skills}
    for body in requests:
        for key, answer in jev.ask("triage", body).items():
            _, skill, index = key.split("::")
            friction[skill][int(index)] = float(answer["noul"])
    outcomes: list[dict[str, Any]] = []
    for load in skills:
        items = [
            {
                "event": found["event"],
                "outcome": "candidate",
                "category": found["kind"],
                "detail": found["detail"],
                "line": None,
            }
            for found in report["facts"]
            if found["skill"] == load.skill
        ]
        scores = friction[load.skill]
        hard = {item["event"]: item for item in items}
        flagged = sorted(
            (i for i, p in scores.items() if p > NO), key=lambda i: -scores[i]
        )
        for index in flagged[:RETAINED]:
            examined = {
                "friction": scores[index],
                **examine(session, load, skills, index, jev),
            }
            if index in hard:
                # The hard failure decides; Jev's reading adds the line it rests on
                hard[index].update(
                    {
                        k: v
                        for k, v in examined.items()
                        if k not in ("outcome", "category")
                    }
                )
            else:
                items.append(examined)
        items += [
            {
                "event": index,
                "outcome": "review",
                "category": "event_too_large",
                "line": None,
            }
            for index in oversized
            if index >= load.after
        ]
        outcome = max(
            (item["outcome"] for item in items),
            key=lambda name: STRENGTH[name],
            default="nothing",
        )
        outcomes.append(
            {
                "skill": load.skill,
                "home": load.home,
                "outcome": outcome,
                "flagged": len(flagged),
                "items": sorted(items, key=lambda item: item["event"]),
            }
        )
    return outcomes


STRENGTH = {"nothing": 0, "review": 1, "candidate": 2}


# --- Runs ------------------------------------------------------------------------


def state_home() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return base / "jev-skill-retro"


def run_directory(session: Session) -> Path:
    """The session's run directory, under a state folder only its owner can enter."""
    root = state_home()
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)
    name = re.sub(r"[^\w.-]", "_", f"{session.harness}-{session.id}")
    return root / "runs" / name


def write_private(path: Path, text: str) -> None:
    """Replace `path` atomically with a file only its owner can read, so an
    interrupted write leaves the old one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(text)
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    write_private(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def load_summary(load: Load) -> dict[str, Any]:
    return {
        "skill": load.skill,
        "status": load.status,
        "home": load.home,
        "after_event": load.after,
        "files": [
            {
                "path": file.path,
                "anchor": file.anchor,
                "partial": file.partial,
                "first_line": file.first_line,
                "read_at": file.read_at,
                "lines": len(file.text.splitlines()),
                "sha256": file.digest(),
            }
            for file in load.files
        ],
    }


# --- Write -----------------------------------------------------------------------

# The fork's marker names no skill: a skill name there loaded that skill during
# the 2026-09-28 pilot
MARKER = "[jev-skill-retro fork]"
# claude -p attaches any @path in its prompt; inside a JSON string this escape
# keeps the character for the model without the mention
AT_ESCAPE = chr(92) + "u0040"
# The 2026-09-28 retro's API-equivalent price of a fork, per context token
FORK_PRICE = 40 / 600_000
STORY_FIELDS = (
    "title",
    "user_story",
    "wanted",
    "problem",
    "workaround",
    "fix",
    "evidence",
)
FORK_PROMPT = """\
{marker} End-of-session skill feedback

You are a read-only copy of this conversation. Do not edit files, commit, open \
issues, or run commands that write. Do not load any skill; you may only reread a \
skill file to check a detail. Answer in the conversation's main language.

An automated scan flagged the items below: moments where a skill you loaded may \
have made your work harder. For each item, decide whether the skill itself caused \
a problem worth fixing: an error, a gap, a missing detail, or an instruction that \
did not match what you found. Report only findings that are actionable and easy to \
fix. Skip anything tied to this conversation's specific context, because fixing \
one-off cases makes the skills unmanageable. When the skill was fine, or the cause \
was your own mistake, the environment, or the request, answer `nothing` for that \
item. An item marked `review` is one the scan was unsure about.

Items, one JSON object per line:
{items}

Answer with exactly one JSON object per line and nothing else, one per item:
{{"item": "<id>", "verdict": "nothing"}}
{{"item": "<id>", "verdict": "story", "title": "<short title>", "user_story": \
"As an agent using the `<skill>` skill, I want …, so that …", "wanted": "<what you \
were trying to do>", "problem": "<the problem you hit>", "workaround": "<what you \
did to work around it>", "fix": "<the smallest change to the skill that removes \
it>", "evidence": "<a short quote, command, or error from this conversation>"}}
Related items of the same skill may share one story: write it once with \
"items": ["<id>", "<id>"] in place of "item", and no other line for those items.
"""


def flagged(scan_report: dict[str, Any], session: Session) -> list[dict[str, Any]]:
    """Every candidate or review item of the scan, as the fork will see it."""
    found: list[dict[str, Any]] = []
    for outcome in scan_report.get("outcomes", []):
        for item in outcome["items"]:
            if item["outcome"] == "nothing":
                continue
            event = session.events[item["event"]]
            line = item.get("line")
            base = f"{outcome['skill']}-e{item['event']}"
            taken = sum(
                1
                for seen in found
                if seen["id"] == base or seen["id"].startswith(f"{base}-")
            )
            found.append(
                {
                    "id": base if not taken else f"{base}-{taken + 1}",
                    "skill": outcome["skill"],
                    "home": outcome["home"],
                    "outcome": item["outcome"],
                    "category": item["category"],
                    "event": item["event"],
                    "excerpt": shorten(event.text),
                    "line": (
                        f"{line['file']}:{line['number']}: {line['text']}"
                        if line
                        else "no line of the skill covers this step"
                    ),
                    # The anchor itself, so publish can tell a changed line
                    "source": line,
                }
            )
    return found


def fork_prompt(items: list[dict[str, Any]]) -> str:
    shown = "\n".join(
        json.dumps(
            {
                key: item[key]
                for key in ("id", "skill", "outcome", "category", "excerpt", "line")
            },
            ensure_ascii=True,
        ).replace("@", AT_ESCAPE)
        for item in items
    )
    return FORK_PROMPT.format(marker=MARKER, items=shown)


def fork_command(session: Session, output: Path) -> list[str]:
    if session.harness == "claude":
        command = [
            "claude",
            "-p",
            "--resume",
            session.id,
            "--fork-session",
            "--no-session-persistence",
            "--permission-mode",
            "dontAsk",
            "--strict-mcp-config",
            "--tools",
            "Read,Grep,Glob",
            "--output-format",
            "json",
        ]
        return command + (["--model", session.model] if session.model else [])
    return [
        "codex",
        "exec",
        "fork",
        session.id,
        "-",
        "--ephemeral",
        "--skip-git-repo-check",
        # No config.toml, so no MCP server or app can write outside the sandbox
        "--ignore-user-config",
        "-c",
        'sandbox_mode="read-only"',
        "-c",
        'approval_policy="never"',
        "-o",
        str(output),
    ]


def estimate(session: Session) -> dict[str, Any]:
    """The fork's context size and cost, from the transcript's size. JSON
    overhead makes bytes/4 an upper bound; bytes/8 is the lower one."""
    size = session.path.stat().st_size
    low, high = size // 8, size // 4
    return {
        "context_tokens": [low, high],
        "cost_usd": [round(low * FORK_PRICE, 2), round(high * FORK_PRICE, 2)],
        "price": "fallback: about $40 per 600k tokens (API-equivalent, 2026-09-28 retro)",
    }


def parse_answer(text: str, ids: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Stories and the IDs answered `nothing`; exactly one disposition per ID."""
    answered: dict[str, dict[str, Any]] = {}
    problems: list[str] = []
    for line in text.splitlines():
        line = line.strip().strip("`")
        if not line.startswith("{"):
            continue
        try:
            answer = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"not JSON: {line[:80]}")
            continue
        covered = answer.get("items") or [answer.get("item")]
        verdict = answer.get("verdict")
        if verdict not in ("story", "nothing"):
            problems.append(f"verdict {verdict!r} for {covered}; use story or nothing")
        if verdict == "story":
            empty = [
                name for name in STORY_FIELDS if not str(answer.get(name) or "").strip()
            ]
            if empty:
                problems.append(f"the story for {covered} lacks {', '.join(empty)}")
        for item in covered:
            if item not in ids:
                problems.append(f"unknown item {item!r}")
            elif item in answered:
                problems.append(f"item {item!r} answered twice")
            else:
                answered[item] = answer
    problems += [f"item {item!r} has no answer" for item in ids if item not in answered]
    if problems:
        raise ValueError("; ".join(problems))
    unique = {id(answer): answer for answer in answered.values()}
    stories = [answer for answer in unique.values() if answer["verdict"] == "story"]
    nothing = [
        item for item, answer in answered.items() if answer["verdict"] == "nothing"
    ]
    return stories, nothing


def fork(session: Session, prompt: str, path: Path, raw: Path, timeout: float) -> str:
    """Run the fork once and return its final message."""
    if not Path(session.cwd).is_dir():
        raise ScriptError(
            f"the session's working directory {session.cwd} is gone, so its "
            f"conversation cannot be resumed; restore it and rerun {PROG} write"
        )
    command = fork_command(session, raw)
    if shutil.which(command[0]) is None:
        raise ScriptError(
            f"{command[0]} is not installed, so the session cannot be forked"
        )
    env = {name: value for name, value in os.environ.items() if name != "CLAUDECODE"}
    write_json(path, {"kind": "fork", "state": "sent", "command": command})
    try:
        done = run(
            command,
            input=prompt,
            cwd=session.cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ScriptError(
            f"the fork ran longer than {timeout:g}s and was stopped; it may have been billed",
            "rerun with a longer --timeout and --retry to fork again",
        ) from None
    if done.returncode != 0:
        raise ScriptError(
            f"{command[0]} exited {done.returncode}: {done.stderr.strip()[-400:]}",
            "rerun with --retry to fork again; the failed fork may have been billed",
        )
    if session.harness == "claude":
        try:
            message = str(json.loads(done.stdout).get("result") or "")
        except (json.JSONDecodeError, AttributeError):
            message = done.stdout
        write_private(raw, message)
    elif raw.exists():
        raw.chmod(0o600)
    message = raw.read_text(encoding="utf-8") if raw.exists() else ""
    write_json(
        path, {"kind": "fork", "state": "done", "command": command, "raw": str(raw)}
    )
    return message


def write_step(args: argparse.Namespace) -> dict[str, Any]:
    session = read_session(locate(args.target))
    directory = run_directory(session)
    scanned = directory / "scan.json"
    if not scanned.exists():
        raise ScriptError(
            f"{session.id} has no scan yet", f"{PROG} scan {shlex.quote(args.target)}"
        )
    items = flagged(json.loads(scanned.read_text()), session)
    report: dict[str, Any] = {
        "run": str(directory),
        "session": {
            "harness": session.harness,
            "id": session.id,
            "model": session.model,
        },
        "items": items,
    }
    if not items:
        report["fork"] = None
        return report
    prompt = fork_prompt(items)
    op = operation("fork", {"session": session.id, "prompt": prompt})
    report["fork"] = {"op": op, **estimate(session)}
    with exclusive(directory / "lock", args.timeout):
        prompt_path = directory / "write" / f"{op}.prompt.txt"
        write_private(prompt_path, prompt)
        report["fork"]["prompt"] = str(prompt_path)
        if args.dry_run:
            return report
        record_path = directory / "ops" / f"{op}.json"
        raw = directory / "write" / f"{op}.answer.txt"
        record = json.loads(record_path.read_text()) if record_path.exists() else {}
        if record.get("state") == "done" and op not in args.retry:
            message = raw.read_text(encoding="utf-8")
        elif record.get("state") == "sent" and op not in args.retry:
            raise ScriptError(
                f"fork {op} started but never finished; it may have been billed",
                f"rerun with --retry {op} to fork again",
            )
        elif not args.yes:
            raise ScriptError(
                "a fork resumes the whole conversation and is paid; show Pascal "
                f"`{PROG} write {shlex.quote(args.target)} --dry-run` and pass --yes "
                "after he approves"
            )
        else:
            message = fork(session, prompt, record_path, raw, args.timeout)
        try:
            stories, nothing = parse_answer(message, [item["id"] for item in items])
        except ValueError as error:
            raise ScriptError(
                f"the fork's answer is invalid: {error}; it is saved in {raw}",
                f"rerun with --retry {op} to fork again, which is paid",
            ) from error
        by_id = {item["id"]: item for item in items}
        report["stories"] = [
            {
                **{name: story[name] for name in STORY_FIELDS},
                "items": [by_id[i] for i in (story.get("items") or [story["item"]])],
            }
            for story in stories
        ]
        report["nothing"] = nothing
        write_json(directory / "stories.json", report)
    return report


# --- Steps -----------------------------------------------------------------------


def scan(args: argparse.Namespace) -> dict[str, Any]:
    session = read_session(locate(args.target))
    classify(session)
    repo = session_repo(session, args.repo)
    directory = run_directory(session)
    report: dict[str, Any] = {
        "run": str(directory),
        "session": {
            "harness": session.harness,
            "id": session.id,
            "transcript": str(session.path),
            "repo": repo,
            "model": session.model,
            "events": len(session.events),
        },
        "skills": [load_summary(load) for load in session.loads],
        "notes": session.notes,
    }
    if repo is None:
        report["outcome"] = "skipped"
        report["reason"] = (
            "the session's working directory is outside any Git repo; pass --repo"
        )
        return report
    report["facts"] = facts(session)
    requests, oversized = plan_triage(session)
    homes = {
        load.home for load in session.loads if load.status == "roster" and load.home
    }
    report["consent"] = consent({repo, *homes})
    report["oversized_events"] = oversized
    with exclusive(directory / "lock", args.timeout):
        if args.dry_run:
            return preview(report, requests, directory, args)
        jev = Jev(
            directory,
            replay=args.replay,
            retry=set(args.retry),
            timeout=args.timeout,
            budget=args.max_requests,
            repos={repo, *homes},
        )
        try:
            report["outcomes"] = judge(session, report, requests, oversized, jev)
        finally:
            report["usage"] = jev.summary()
        report["calibration"] = CALIBRATION
        write_json(directory / "scan.json", report)
    return report


def preview(
    report: dict[str, Any],
    requests: list[dict[str, Any]],
    directory: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Save the triage requests and check them for secrets, sending nothing."""
    report["requests"] = [
        {
            "op": operation("triage", body),
            "tokens": tokens(body),
            "questions": len(body["questions"]),
        }
        for body in requests
    ]
    report["budget"] = {
        "max_requests": args.max_requests,
        "within": len(requests) <= args.max_requests,
    }
    found: dict[str, list[str]] = {}
    unchecked = False
    for body, entry in zip(requests, report["requests"]):
        saved = directory / "planned" / f"{entry['op']}.json"
        write_json(saved, body)
        leaks = secrets(saved.read_text(encoding="utf-8"), args.timeout)
        if leaks is None:
            unchecked = True
        elif leaks:
            found[entry["op"]] = leaks
    report["secrets"] = "unchecked" if unchecked else found or "clean"
    write_json(directory / "scan-plan.json", report)
    return report


def lines(report: dict[str, Any]) -> str:
    """The report as tab-separated lines, one fact per line."""
    session = report["session"]
    rows = [
        f"run\t{report['run']}",
        f"session\t{session['harness']}\t{session['id']}\t{session['repo'] or '-'}",
    ]
    for load in report["skills"]:
        rows.append(f"skill\t{load['skill']}\t{load['status']}\t{load['home'] or '-'}")
    if "outcome" in report:
        rows.append(f"{report['outcome']}\t{report['reason']}")
        return "\n".join(rows)
    for item in report["facts"]:
        rows.append(
            f"fact\t{item['skill']}\t{item['kind']}\tevent {item['event']}\t{item['detail']}"
        )
    for entry in report.get("requests", []):
        rows.append(
            f"request\t{entry['op']}\t{entry['tokens']} tokens\t{entry['questions']} questions"
        )
    for outcome in report.get("outcomes", []):
        rows.append(f"outcome\t{outcome['skill']}\t{outcome['outcome']}")
        for item in outcome["items"]:
            line = item.get("line")
            where = f"{line['file']}:{line['number']}" if line else "-"
            rows.append(
                f"item\t{outcome['skill']}\t{item['outcome']}\t{item['category']}"
                f"\tevent {item['event']}\t{where}"
            )
    for index in report["oversized_events"]:
        rows.append(f"oversized\tevent {index}")
    for repo, ok in report["consent"].items():
        state = "ok" if ok else "missing: " + CONSENT_FIX.format(repo=repo)
        rows.append(f"consent\t{repo}\t{state}")
    if "secrets" in report:
        found = report["secrets"]
        if isinstance(found, dict):
            rows += [f"secret\t{op}\t{'; '.join(leaks)}" for op, leaks in found.items()]
        else:
            rows.append(f"secrets\t{found}")
    if "usage" in report:
        usage = report["usage"]
        rows.append(
            f"usage\t{usage['sent']} sent\t{usage['reused']} reused"
            f"\t{usage['input_tokens']} tokens\t${usage['cost_usd']:.4f}"
        )
    rows += [f"note\t{note}" for note in report["notes"]]
    return "\n".join(rows)


def write_lines(report: dict[str, Any]) -> str:
    rows = [f"run\t{report['run']}"]
    fork = report["fork"]
    if fork is None:
        rows.append("skip\tno skill in this session is a candidate or review")
        return "\n".join(rows)
    low, high = fork["context_tokens"]
    cost_low, cost_high = fork["cost_usd"]
    session = report["session"]
    rows.append(
        f"fork\t{fork['op']}\t{session['harness']}\t{session['id']}\t{session['model'] or '-'}"
        f"\t{low}-{high} tokens\t${cost_low:.2f}-${cost_high:.2f}\t{fork['price']}"
    )
    rows += [
        f"item\t{item['id']}\t{item['outcome']}\t{item['category']}"
        for item in report["items"]
    ]
    rows.append(f"prompt\t{fork['prompt']}")
    for story in report.get("stories", []):
        items = ",".join(item["id"] for item in story["items"])
        rows.append(f"story\t{story['items'][0]['skill']}\t{items}\t{story['title']}")
    rows += [f"nothing\t{item}" for item in report.get("nothing", [])]
    return "\n".join(rows)


# How long each step waits, by default, for its lock and its slowest child
TIMEOUTS = {"scan": 60.0, "write": 1200.0}
# Flags each step takes beyond the shared ones
STEP_FLAGS = {"scan": {"replay", "repo"}, "write": {"yes"}}


def work(args: argparse.Namespace) -> str:
    if args.max_requests < 1:
        raise UsageError("--max-requests must be at least 1")
    given = {"replay": args.replay, "repo": args.repo, "yes": args.yes}
    for name, value in given.items():
        if value and name not in STEP_FLAGS[args.step]:
            raise UsageError(f"{args.step} takes no --{name}")
    if args.dry_run and (args.replay or args.retry or args.yes):
        raise UsageError(
            "--dry-run sends nothing, so it takes no --replay, --retry, or --yes"
        )
    args.timeout = args.timeout or TIMEOUTS[args.step]
    if args.step == "write":
        report = write_step(args)
        render = write_lines
    else:
        report = scan(args)
        render = lines
    return (
        json.dumps(report, indent=2, ensure_ascii=False)
        if args.json
        else render(report)
    )


def build_parser() -> Parser:
    parser = Parser(
        prog=PROG,
        exit_codes=EXIT_CODES,
        description=(
            "Find where the skills a finished Claude Code or Codex session loaded caused "
            "friction. scan asks Jev one friction question per loaded skill and event, "
            "locates and qualifies the flagged events, and decides each skill's outcome: "
            "candidate, review, or nothing. Every request needs recorded consent for the "
            "session's repo and each skill's home repo, and passes a gitleaks scan first. "
            "write forks the session read-only, once, after Pascal approves its cost."
        ),
        epilog=EXAMPLES,
    )
    parser.add_argument(
        "step",
        choices=("scan", "write"),
        help="scan asks Jev about the session's skills; write forks the session so "
        "its own agent writes a story for each flagged item",
    )
    parser.add_argument(
        "target", metavar="SESSION", help="a session ID, or the path of its transcript"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="scan: plan and save the triage requests, sending nothing; "
        "write: show the fork, its items, and its cost, and save its prompt",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="decide again from saved answers only, sending nothing",
    )
    parser.add_argument(
        "--retry",
        action="append",
        default=[],
        metavar="OP",
        help="send again a request or fork whose answer never arrived or was invalid; "
        "it may be billed twice",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="write: approve the paid fork that --dry-run shows",
    )
    parser.add_argument(
        "--repo",
        metavar="OWNER/NAME",
        help="the session's GitHub repo, when its working directory is gone or has no remote",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=50,
        metavar="N",
        help="the most requests one scan may send (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        metavar="DURATION",
        help="how long to wait for the session lock and the slowest child: one TypeSafe "
        "answer or gitleaks for scan, the fork for write; 30s, 5m, or seconds "
        "(default: 60s for scan, 20m for write)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print one JSON object on stdout"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    return run_script(build_parser(), work, argv, debug="JEV_SKILL_RETRO_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

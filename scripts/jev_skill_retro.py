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
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import install_skills
import tomllib
from _cli import Parser, ScriptError, UsageError, duration, exit_codes
from _common import exclusive, run, run_script

log = logging.getLogger("jev-skill-retro")

PROG = "just jev-skill-retro"
ROOT = install_skills.ROOT
EXIT_CODES = exit_codes(
    {
        1: "failure: an unreadable transcript, missing consent, or a TypeSafe or GitHub error",
        75: "another run holds this session's lock; rerun later",
    }
)
EXAMPLES = f"""\
examples:
  {PROG} scan 6d88c057-abeb-41cc-ab08-195310f0b63b --dry-run
  {PROG} scan ~/.codex/sessions/2026/09/28/rollout-2026-09-28T12-53-45-01a0.jsonl --dry-run --json
  {PROG} scan 6d88c057-abeb-41cc-ab08-195310f0b63b --dry-run --repo pascalandy/skills"""

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
    names: dict[str, str] = {}
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
            if kind == "text" and actor == "agent":
                # The agent may quote the marker; only Claude Code injects a skill
                text = block.get("text", "")
                if text.strip():
                    session.add(actor, text)
            elif kind == "text":
                claude_text(session, actor, block.get("text", ""), len(session.events))
            elif kind == "tool_use":
                name = str(block.get("name", ""))
                arguments = block.get("input") or {}
                event = session.add("tool", f"{name}: {json.dumps(arguments)}")
                calls[str(block.get("id"))] = event
                names[str(block.get("id"))] = name
                if name == "Read" and isinstance(arguments, dict):
                    reads[str(block.get("id"))] = arguments
            elif kind == "tool_result":
                call = str(block.get("tool_use_id"))
                result = texts(block.get("content"))
                error = bool(block.get("is_error"))
                event = calls.get(call) or session.add("tool", "")
                # Only the Skill tool delivers a skill; any other tool may print the marker
                skill_call = names.get(call) == "Skill"
                found = SKILL_START.search(result) if skill_call and not error else None
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


# --- Steps -----------------------------------------------------------------------


def scan(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dry_run:
        raise ScriptError(
            "a live scan is not available yet; this version only plans requests",
            f"{PROG} scan {shlex.quote(args.target)} --dry-run",
        )
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
    planned = [
        {
            "op": operation("triage", body),
            "tokens": tokens(body),
            "questions": len(body["questions"]),
        }
        for body in requests
    ]
    homes = {
        load.home for load in session.loads if load.status == "roster" and load.home
    }
    report["consent"] = consent({repo, *homes})
    report["requests"] = planned
    report["oversized_events"] = oversized
    report["budget"] = {
        "max_requests": args.max_requests,
        "within": len(planned) <= args.max_requests,
    }
    with exclusive(directory / "lock", args.timeout):
        found: dict[str, list[str]] = {}
        unchecked = False
        for body, entry in zip(requests, planned):
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
    for entry in report["requests"]:
        rows.append(
            f"request\t{entry['op']}\t{entry['tokens']} tokens\t{entry['questions']} questions"
        )
    for index in report["oversized_events"]:
        rows.append(f"oversized\tevent {index}")
    for repo, ok in report["consent"].items():
        rows.append(
            f"consent\t{repo}\t{'ok' if ok else 'missing: ' + CONSENT_FIX.format(repo=repo)}"
        )
    secrets_found = report["secrets"]
    if isinstance(secrets_found, dict):
        for op, leaks in secrets_found.items():
            rows.append(f"secret\t{op}\t{'; '.join(leaks)}")
    else:
        rows.append(f"secrets\t{secrets_found}")
    for note in report["notes"]:
        rows.append(f"note\t{note}")
    return "\n".join(rows)


def work(args: argparse.Namespace) -> str:
    if args.max_requests < 1:
        raise UsageError("--max-requests must be at least 1")
    report = scan(args)
    return (
        json.dumps(report, indent=2, ensure_ascii=False) if args.json else lines(report)
    )


def build_parser() -> Parser:
    parser = Parser(
        prog=PROG,
        exit_codes=EXIT_CODES,
        description=(
            "Find where the skills a finished Claude Code or Codex session loaded caused "
            "friction. scan plans the triage requests Jev will answer, saves them under "
            "the run directory, and checks consent and secrets; it sends nothing."
        ),
        epilog=EXAMPLES,
    )
    parser.add_argument("step", choices=("scan",), help="the step to run: scan")
    parser.add_argument(
        "target", metavar="SESSION", help="a session ID, or the path of its transcript"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="plan and save the requests without sending them; needs no key or consent",
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
        help="the most triage requests one scan may send (default: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=30.0,
        metavar="DURATION",
        help="how long to wait for the session lock or a child command: 30s, 5m, or seconds (default: 30s)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print one JSON object on stdout"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    return run_script(build_parser(), work, argv, debug="JEV_SKILL_RETRO_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

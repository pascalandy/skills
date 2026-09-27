#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["typesafe-sdk==0.7.1"]
# ///
"""jevlabel: bulk GitHub issue triage with Jev, for the label-for-issues vocabulary.

Code fetches issues through gh and builds each issue's input, Jev answers the typed
questions in assets/questions.toml, and code turns the answers into a label proposal
and a queue. label-for-issues owns the label vocabulary and its rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

import tomllib

VERSION = "0.1.0"
RUN_SCHEMA = "jevlabel.run/v1"
PREVIEW_SCHEMA = "jevlabel.preview/v1"
COMPARE_SCHEMA = "jevlabel.compare/v1"
DOCTOR_SCHEMA = "jevlabel.doctor/v1"
QUESTIONS_SCHEMA = "jevlabel.questions/v1"
EXIT_ERROR, EXIT_USAGE, EXIT_INTERRUPTED = 1, 2, 130
RUN_FILE = re.compile(r"^\d{8}T\d{6}Z-[a-z0-9-]+\.json$")
QUEUES = ("routine", "review", "skip")
OUTCOMES = ("agree", "disagree", "abstain", "unlabeled")

SKILL_DIR = Path(__file__).resolve().parents[1]
QUESTIONS_FILE = SKILL_DIR / "assets" / "questions.toml"
VOCABULARY_FILE = SKILL_DIR.parent / "label-for-issues" / "SKILL.md"

# The same terms summary jevgate carries; re-ask for consent when it changes.
TERMS_NAME = "typesafe-2026-09-26"
TERMS_SUMMARY = (
    "TypeSafe does not train on customer input; it hosts in the US, may keep derived "
    "telemetry, keeps inputs for no fixed period, and offers zero retention to "
    "enterprise customers only"
)
KEYRING_ARGS = ("secret", "keyring", "get", "--service=typesafe_ai", "--user=api_key")
KEYRING_TIMEOUT_S = 15
KEYCHAIN_LOCKED_EXIT = 36
RETRY_MAX = 2
RETRY_BUDGET_S = 60.0
HTTP_TIMEOUT_S = 30.0

# API limits are 64k tokens per request and 32k for the state plus the longest
# question. No token counter exists, so estimates run high and keep a margin.
REQUEST_BUDGET = 60_000
STATE_BUDGET = 30_000
BYTES_PER_TOKEN = 3.0
PRICE_PER_MILLION_INPUT_USD = 0.042
MAX_COMMENTS = 40

REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VERSIONED_MODEL = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)*-\d+\.\d+\.\d+$")
BACKTICK = re.compile(r"`([^`]*)`")
STATE_PATHS = {
    "issue",
    "issue.title",
    "issue.body",
    "comments",
    "comments[{i}]",
    "comments[{i}].body",
    "comments[{i}].author_role",
}
IMAGE = re.compile(
    r"!\[[^\]]*\]\(|<img\b|github\.com/user-attachments/assets/", re.IGNORECASE
)
MANAGED_MARKER = "<!-- label-for-issues:decision -->"
MAINTAINER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
KNOWN_BOTS = {"github-actions", "dependabot", "renovate", "codecov", "copilot"}
ISSUE_FIELDS = "number,title,body,author,comments,labels,state,updatedAt,url"
GH_COMMENT_PAGE = 100

# Labels jevlabel reads or proposes. label-for-issues owns their names; a test and
# every run check that its ## Labels JSON still defines them.
IMPEDIMENT = "0-impediment"
NEEDS_INFO, NEEDS_TRIAGE, WONTFIX = "1-needs-info", "1-needs-triage", "1-wontfix"
READY_AGENT, READY_HUMAN, WIP = (
    "1-ready-for-agent",
    "1-ready-for-human",
    "1-wip-by-agent",
)
P0, P2 = "3-pty:p0", "3-pty:p2"
EPIC_PARENT = "4-epic:parent"
STATE_PREFIX, TYPE_PREFIX, PRIORITY_PREFIX = "1-", "2-type:", "3-pty:"
# Families that hold at most one label each.
FAMILIES = {"state": STATE_PREFIX, "type": TYPE_PREFIX, "priority": PRIORITY_PREFIX}
NEEDED_LABELS = (
    IMPEDIMENT,
    NEEDS_INFO,
    NEEDS_TRIAGE,
    READY_AGENT,
    READY_HUMAN,
    WIP,
    WONTFIX,
    "2-type:bug",
    "2-type:feature",
    "2-type:task",
    P0,
    P2,
    EPIC_PARENT,
)
# Which checklist questions apply to each kind of issue, and how a missing item reads.
CHECKLIST = {
    "bug": ("has_goal", "bug_repro", "bug_expected_actual"),
    "feature": ("has_goal", "done_condition"),
    "task": ("has_goal", "done_condition"),
    "epic": ("has_goal", "done_condition"),
    None: ("has_goal",),
}
CHECKLIST_NAMES = {
    "has_goal": "what should change",
    "done_condition": "how to tell the work is done",
    "bug_repro": "how to reproduce the problem",
    "bug_expected_actual": "expected and actual behavior",
}
NOMINATIONS = {
    WONTFIX: "a maintainer declined the work; label-for-issues pairs 1-wontfix with an explicit human decision",
    READY_AGENT: "ready for an agent; label-for-issues requires a recorded readiness review first",
    READY_HUMAN: "ready for a person; label-for-issues requires a recorded readiness review first",
}

TYPE_OPTIONS = ("bug", "feature", "task")
NO_MATCH = "cannot-tell"
# The questions the policy consumes: id -> (primitive, scope).
POLICY_QUESTIONS = {
    "type": ("choice", "issue"),
    "has_goal": ("noul", "issue"),
    "done_condition": ("noul", "issue"),
    "bug_repro": ("noul", "issue"),
    "bug_expected_actual": ("noul", "issue"),
    "open_decision": ("noul", "issue"),
    "needs_human_impl": ("noul", "issue"),
    "impediment": ("noul", "issue"),
    "urgency": ("noul", "issue"),
    "steering": ("noul", "issue"),
    "asks_info": ("noul", "comment"),
    "supplies_info": ("noul", "comment"),
    "declined": ("noul", "maintainer-comment"),
}

HELP = """\
jevlabel: triage many GitHub issues with Jev, then label the clear ones

commands:
  doctor    check gh, the label vocabulary, the questions, the API key, and consent
  consent   record which private repositories may send issue text to TypeSafe
  run       fetch issues, ask Jev, and write a run record (--dry-run: preview only)
  compare   compare a run's judged type and state with the labels issues already had

queues in a run record:
  routine   every answer used is clear and the labels only fill empty families
  review    an answer is uncertain, or a label needs a person or new evidence
  skip      closed, pull request, agent work in progress, or not asked

examples:
  jevlabel doctor -R pascalandy/skills --online
  jevlabel run -R pascalandy/skills --dry-run
  jevlabel run -R pascalandy/skills
  jevlabel compare last
  jevlabel consent add pascalandy/skills-private --by "Pascal Andy"

Run `jevlabel <command> --help` for flags. Every command accepts --json and -v.
"""


# ---------------------------------------------------------------------- errors


class Failure(Exception):
    """A problem the user can fix; each message becomes one `error:` line."""

    def __init__(self, *problems: str, result: Any = None) -> None:
        super().__init__(*problems)
        self.problems = problems
        self.result = result


class UsageError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise UsageError(f"{message}; see `{self.prog} --help`")


# --------------------------------------------------------------------- helpers


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def estimate_tokens(value: Any) -> int:
    return math.ceil(len(canonical(value).encode()) / BYTES_PER_TOKEN)


def cost_usd(tokens: int) -> float:
    return round(tokens * PRICE_PER_MILLION_INPUT_USD / 1_000_000, 6)


def now() -> datetime:
    return datetime.now(UTC)


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        handle.write(text)
    os.replace(handle.name, path)


def write_json(path: Path, value: Any) -> None:
    write_atomic(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def state_home() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "label-for-issues-jev"


def config_home() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "label-for-issues-jev"


def runs_dir() -> Path:
    return state_home() / "runs"


def consent_file() -> Path:
    return config_home() / "consent.toml"


def repo_name(value: str) -> str:
    if not REPO.match(value):
        raise UsageError(f"{value!r} is not an owner/repo name")
    return value


def login(author: Any) -> str:
    if isinstance(author, dict) and isinstance(author.get("login"), str):
        return author["login"]
    return "ghost"


def is_bot(name: str) -> bool:
    return name.endswith("[bot]") or name.lower() in KNOWN_BOTS


# ------------------------------------------------------------------------- gh


def gh(*args: str) -> str:
    if shutil.which("gh") is None:
        raise Failure(
            "gh is not installed; install the GitHub CLI and run `gh auth login`"
        )
    process = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or f"exit {process.returncode}"
        raise Failure(f"`gh {' '.join(args[:2])}` failed: {detail}")
    return process.stdout


def gh_json(*args: str) -> Any:
    output = gh(*args)
    try:
        return json.loads(output)
    except ValueError as error:
        raise Failure(
            f"`gh {' '.join(args[:2])}` returned output that is not JSON"
        ) from error


def repo_visibility(repo: str) -> str:
    data = gh_json("repo", "view", repo, "--json", "visibility")
    return str(data.get("visibility", "")).upper()


def repo_labels(repo: str) -> set[str]:
    data = gh_json("label", "list", "-R", repo, "--limit", "1000", "--json", "name")
    return {label["name"] for label in data}


def fetch_issue(repo: str, number: int) -> dict[str, Any]:
    return gh_json("issue", "view", str(number), "-R", repo, "--json", ISSUE_FIELDS)


def fetch_issues(repo: str, args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.issue:
        return [fetch_issue(repo, number) for number in dict.fromkeys(args.issue)]
    command = ["issue", "list", "-R", repo, "--state", args.state]
    command += ["--limit", str(args.limit), "--json", ISSUE_FIELDS]
    if args.search:
        command += ["--search", args.search]
    issues = gh_json(*command)
    # A listing returns at most one page of comments; `issue view` returns them all.
    return sorted(
        (
            fetch_issue(repo, issue["number"])
            if len(issue.get("comments") or []) >= GH_COMMENT_PAGE
            else issue
            for issue in issues
        ),
        key=lambda issue: issue["number"],
    )


# ----------------------------------------------------------------- vocabulary


def load_vocabulary() -> set[str]:
    """Read the canonical label names from label-for-issues' ## Labels JSON."""
    try:
        text = VOCABULARY_FILE.read_text(encoding="utf-8")
    except OSError as error:
        raise Failure(
            f"label-for-issues is not installed beside this skill ({VOCABULARY_FILE}): {error.strerror}"
        ) from error
    match = re.search(
        r"^## Labels$.*?^```json\n(.*?)^```", text, re.DOTALL | re.MULTILINE
    )
    if match is None:
        raise Failure(f"{VOCABULARY_FILE} has no JSON block under ## Labels")
    try:
        names = {label["name"] for label in json.loads(match.group(1))}
    except (ValueError, KeyError, TypeError) as error:
        raise Failure(
            f"the ## Labels JSON in {VOCABULARY_FILE} is malformed"
        ) from error
    missing = [name for name in NEEDED_LABELS if name not in names]
    if missing:
        raise Failure(
            f"label-for-issues no longer defines {', '.join(missing)}; update NEEDED_LABELS and the policy in jevlabel.py to its ## Labels JSON"
        )
    return names


# ------------------------------------------------------------------ questions


@dataclass(frozen=True)
class Question:
    id: str
    primitive: str
    scope: str
    instructions: str
    criteria: dict[str, str]
    yes: float = 0.0
    no: float = 0.0
    min_confidence: float = 0.0

    def wire(self, index: int | None = None) -> dict[str, Any]:
        instructions = self.instructions
        if index is not None:
            instructions = instructions.replace("{i}", str(index))
        return {
            "type": self.primitive,
            "instructions": instructions,
            "criteria": dict(self.criteria),
        }


@dataclass(frozen=True)
class Pack:
    model: str
    calibration: str
    questions: dict[str, Question]
    digest: str


def number(value: Any) -> float | None:
    """A finite int or float from TOML or JSON, never a bool."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def question_problems(qid: str, raw: Any) -> list[str]:
    if not isinstance(raw, dict):
        return [f"{qid}: is not a table"]
    primitive, scope = POLICY_QUESTIONS[qid]
    problems: list[str] = []
    if raw.get("primitive") != primitive or raw.get("scope") != scope:
        problems.append(f"{qid}: the policy needs a {primitive} with scope {scope!r}")
    instructions = raw.get("instructions")
    if not isinstance(instructions, str) or not instructions.strip():
        return [*problems, f"{qid}: instructions are missing"]
    for path in BACKTICK.findall(instructions):
        if path not in STATE_PATHS:
            problems.append(f"{qid}: `{path}` is not a path in the state code builds")
    if ("{i}" in instructions) != (scope != "issue"):
        problems.append(
            f"{qid}: per-comment questions, and only they, name `comments[{{i}}]`"
        )
    criteria = raw.get("criteria")
    expected = {"true", "false"} if primitive == "noul" else {*TYPE_OPTIONS, NO_MATCH}
    if not isinstance(criteria, dict) or set(criteria) != expected:
        problems.append(f"{qid}: criteria must be exactly {sorted(expected)}")
    elif not all(isinstance(text, str) and text.strip() for text in criteria.values()):
        problems.append(f"{qid}: every criterion needs a description")
    if primitive == "noul":
        yes, no = number(raw.get("yes")), number(raw.get("no"))
        if yes is None or no is None:
            problems.append(f"{qid}: yes and no thresholds are required")
        elif not 0 < no < yes < 1:
            problems.append(f"{qid}: thresholds need 0 < no < yes < 1")
    else:
        value = number(raw.get("min_confidence"))
        if value is None or not 0 < value < 1:
            problems.append(f"{qid}: min_confidence must be between 0 and 1")
    return problems


def load_pack(path: Path = QUESTIONS_FILE) -> Pack:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Failure(f"cannot read {path}: {error.strerror}") from error
    except tomllib.TOMLDecodeError as error:
        raise Failure(f"{path} is not valid TOML: {error}") from error
    problems: list[str] = []
    if raw.get("schema") != QUESTIONS_SCHEMA:
        problems.append(f"schema must be {QUESTIONS_SCHEMA!r}")
    model = raw.get("model")
    if not isinstance(model, str) or not VERSIONED_MODEL.match(model):
        problems.append(f"model {model!r} is not a versioned ID such as jev-1.13.0")
    ids = {key for key, value in raw.items() if isinstance(value, dict)}
    if ids != set(POLICY_QUESTIONS):
        missing, extra = set(POLICY_QUESTIONS) - ids, ids - set(POLICY_QUESTIONS)
        problems.append(
            f"questions must match the policy (missing {sorted(missing)}, extra {sorted(extra)})"
        )
    for qid in sorted(ids & set(POLICY_QUESTIONS)):
        problems += question_problems(qid, raw[qid])
    if problems:
        raise Failure(*(f"{path.name}: {problem}" for problem in problems))
    questions = {
        qid: Question(
            id=qid,
            primitive=raw[qid]["primitive"],
            scope=raw[qid]["scope"],
            instructions=raw[qid]["instructions"],
            criteria=dict(raw[qid]["criteria"]),
            yes=float(raw[qid].get("yes", 0.0)),
            no=float(raw[qid].get("no", 0.0)),
            min_confidence=float(raw[qid].get("min_confidence", 0.0)),
        )
        for qid in POLICY_QUESTIONS
    }
    return Pack(
        model=str(model),
        calibration=str(raw.get("calibration", "")),
        questions=questions,
        digest=digest(raw),
    )


# ---------------------------------------------------------------- issue input


@dataclass
class Prepared:
    """One issue, its facts, and the Jev request code built for it."""

    number: int
    title: str
    url: str
    state: str
    updated_at: str
    labels: list[str]
    skip: str | None = None
    request: dict[str, Any] | None = None
    comments: list[dict[str, str]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    tokens: int = 0

    def summary(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "url": self.url,
            "state": self.state,
            "updated_at": self.updated_at,
            "labels": self.labels,
            "skip": self.skip,
            "comments": self.comments,
            "facts": self.facts,
            "estimated_tokens": self.tokens,
        }


def comment_role(comment: dict[str, Any], author: str) -> str:
    if comment.get("authorAssociation") in MAINTAINER_ASSOCIATIONS:
        return "maintainer"
    return "reporter" if login(comment.get("author")) == author else "other"


def drop_order(comments: list[dict[str, str]]) -> list[int]:
    """Indexes to drop first: oldest non-maintainer comments, then oldest maintainer ones."""
    others = [i for i, c in enumerate(comments) if c["author_role"] != "maintainer"]
    maintainers = [
        i for i, c in enumerate(comments) if c["author_role"] == "maintainer"
    ]
    return others + maintainers


def build_request(
    pack: Pack, title: str, body: str, comments: list[dict[str, str]], labels: list[str]
) -> dict[str, Any]:
    state = {
        "issue": {"title": title, "body": body},
        "comments": [
            {"author_role": c["author_role"], "body": c["body"]} for c in comments
        ],
    }
    questions: dict[str, Any] = {}
    for question in pack.questions.values():
        if question.scope != "issue" or (
            question.id == "type" and EPIC_PARENT in labels
        ):
            continue
        questions[question.id] = question.wire()
    for index, comment in enumerate(comments):
        for question in pack.questions.values():
            if question.scope == "comment" or (
                question.scope == "maintainer-comment"
                and comment["author_role"] == "maintainer"
            ):
                questions[f"{question.id}_{index}"] = question.wire(index)
    return {"model": pack.model, "state": state, "questions": questions}


def within_budget(request: dict[str, Any]) -> bool:
    state = estimate_tokens(request["state"])
    sizes = [estimate_tokens(question) for question in request["questions"].values()]
    return (
        state + max(sizes, default=0) <= STATE_BUDGET
        and state + sum(sizes) <= REQUEST_BUDGET
    )


def prepare(issue: dict[str, Any], pack: Pack) -> Prepared:
    labels = sorted(label["name"] for label in issue.get("labels") or [])
    prepared = Prepared(
        number=int(issue["number"]),
        title=str(issue.get("title") or ""),
        url=str(issue.get("url") or ""),
        state=str(issue.get("state") or "").upper(),
        updated_at=str(issue.get("updatedAt") or ""),
        labels=labels,
    )
    if "/pull/" in prepared.url:
        prepared.skip = "pull request"
        return prepared
    if WIP in labels:
        prepared.skip = f"an agent is working on it ({WIP})"
        return prepared

    author = login(issue.get("author"))
    body = str(issue.get("body") or "")
    managed = False
    comments: list[dict[str, str]] = []
    for comment in issue.get("comments") or []:
        text = str(comment.get("body") or "")
        if MANAGED_MARKER in text:
            # A previous triage comment would anchor Jev on the last agent's view.
            managed = True
            continue
        if comment.get("isMinimized") or is_bot(login(comment.get("author"))):
            continue
        comments.append(
            {
                "author_role": comment_role(comment, author),
                "body": text,
                "url": str(comment.get("url") or ""),
            }
        )
    has_images = any(
        IMAGE.search(text) for text in [body, *(c["body"] for c in comments)]
    )

    order = drop_order(comments)
    dropped = set(order[: max(0, len(comments) - MAX_COMMENTS)])

    def kept() -> list[dict[str, str]]:
        return [c for i, c in enumerate(comments) if i not in dropped]

    request = build_request(pack, prepared.title, body, kept(), labels)
    for index in order[len(dropped) :]:
        if within_budget(request):
            break
        dropped.add(index)
        request = build_request(pack, prepared.title, body, kept(), labels)
    truncated = False
    while not within_budget(request) and body:
        body, truncated = body[: int(len(body) * 0.8)], True
        request = build_request(
            pack, prepared.title, body + "\n[truncated]", kept(), labels
        )
    if not within_budget(request):
        prepared.skip = "too large for one request even without comments"
        return prepared

    prepared.request = request
    prepared.comments = [
        {"url": c["url"], "author_role": c["author_role"]} for c in kept()
    ]
    prepared.facts = {
        "has_images": has_images,
        "managed_comment": managed,
        "comments_sent": len(comments) - len(dropped),
        "comments_omitted": len(dropped),
        "body_truncated": truncated,
    }
    prepared.tokens = estimate_tokens(request)
    return prepared


def prepare_all(
    issues: list[dict[str, Any]], pack: Pack, max_requests: int | None
) -> list[Prepared]:
    prepared: list[Prepared] = []
    asked = 0
    for issue in issues:
        item = prepare(issue, pack)
        if item.request is not None:
            if max_requests is not None and asked >= max_requests:
                item.request, item.skip = None, f"request cap of {max_requests} reached"
            else:
                asked += 1
        prepared.append(item)
    return prepared


# -------------------------------------------------------------------- consent


def read_consent() -> dict[str, dict[str, str]]:
    path = consent_file()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise Failure(f"{path} is unreadable: {error}; fix or delete it") from error
    return {repo: entry for repo, entry in raw.items() if isinstance(entry, dict)}


def write_consent(entries: dict[str, dict[str, str]]) -> None:
    lines = [
        "# Private repositories whose issue text jevlabel may send to TypeSafe.",
        "# Written by `jevlabel consent`; each entry records who approved and when.",
    ]
    for repo in sorted(entries):
        lines += ["", f"[{json.dumps(repo)}]"]
        lines += [
            f"{key} = {json.dumps(value)}"
            for key, value in sorted(entries[repo].items())
        ]
    write_atomic(consent_file(), "\n".join(lines) + "\n")


def consent_problem(repo: str, visibility: str) -> str | None:
    """Why issue text from this repository may not go to TypeSafe, or None."""
    if visibility == "PUBLIC":
        return None
    entry = read_consent().get(repo)
    if entry is None:
        return f"{repo} is {visibility.lower()} and has no recorded consent"
    if entry.get("terms") != TERMS_NAME:
        return f"the consent for {repo} names terms {entry.get('terms')!r}, but the current terms are {TERMS_NAME!r}"
    return None


def consent_fix(repo: str) -> str:
    return (
        f"preview with `jevlabel run -R {repo} --dry-run`, show it and the terms ({TERMS_SUMMARY}) "
        f'to the user, and only after they approve run `jevlabel consent add {repo} --by "<their name>"`'
    )


# ------------------------------------------------------------------------ key


def key_source() -> tuple[str | None, str, str]:
    """Find the API key: TYPESAFE_API_KEY, then the chezmoi keyring. Never a flag."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key, "TYPESAFE_API_KEY", ""
    chezmoi = shutil.which("chezmoi")
    if chezmoi is None:
        return None, "none", "TYPESAFE_API_KEY is not set and chezmoi is not installed"
    try:
        process = subprocess.run(
            [chezmoi, *KEYRING_ARGS],
            capture_output=True,
            text=True,
            timeout=KEYRING_TIMEOUT_S,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return (
            None,
            "none",
            f"the chezmoi keyring lookup took longer than {KEYRING_TIMEOUT_S}s",
        )
    if process.returncode == KEYCHAIN_LOCKED_EXIT:
        return None, "none", "the macOS keychain is locked (chezmoi keyring exit 36)"
    if process.returncode != 0 or not process.stdout.strip():
        return (
            None,
            "none",
            f"TYPESAFE_API_KEY is not set and the chezmoi keyring has no typesafe_ai api_key (exit {process.returncode})",
        )
    return process.stdout.strip(), "chezmoi keyring", ""


KEY_FIX = "export TYPESAFE_API_KEY, or store it with `chezmoi secret keyring set --service=typesafe_ai --user=api_key`; --dry-run needs no key"


def resolve_key() -> str:
    key, _, problem = key_source()
    if key is None:
        raise Failure(f"{problem}; {KEY_FIX}")
    return key


# ------------------------------------------------------------------ transport


def open_client(key: str, model: str) -> Any:
    from typesafe_sdk import RetryPolicy, TypeSafeClient

    # The SDK owns retries: bounded attempts and budget, honoring retry-after.
    policy = RetryPolicy(max_retries=RETRY_MAX, timeout=RETRY_BUDGET_S)
    return TypeSafeClient(
        api_key=key, model=model, retry=policy, timeout=HTTP_TIMEOUT_S
    )


def transport_error(error: Exception) -> Failure:
    from typesafe_sdk import (
        TypeSafeAPIConnectionError,
        TypeSafeAPIError,
        TypeSafeAuthenticationError,
        TypeSafePermissionDeniedError,
        TypeSafeUnprocessableEntityError,
    )

    if isinstance(error, TypeSafeAuthenticationError | TypeSafePermissionDeniedError):
        return Failure(f"TypeSafe rejected the API key: {error}; {KEY_FIX}")
    if isinstance(error, TypeSafeUnprocessableEntityError):
        return Failure(f"TypeSafe refused the request as invalid: {error}")
    if isinstance(error, TypeSafeAPIError):
        return Failure(
            f"TypeSafe stayed unavailable after {RETRY_MAX} retries: {error}; rerun later"
        )
    if isinstance(error, TypeSafeAPIConnectionError):
        return Failure(
            f"could not reach TypeSafe: {error}; check the network and rerun"
        )
    return Failure(f"TypeSafe request failed: {error}; rerun later")


def send(client: Any, body: dict[str, Any]) -> Any:
    from typesafe_sdk import TypeSafeError

    try:
        response = client.system_one(
            body["state"], body["questions"], model=body["model"]
        )
    except TypeSafeError as error:
        raise transport_error(error) from error
    try:
        return json.loads(response.raw_http_response.content)
    except ValueError as error:
        raise Failure(
            "TypeSafe returned a body that is not JSON; rerun later"
        ) from error


def probability(value: Any) -> bool:
    return number(value) is not None and 0 <= value <= 1


def answer_problem(question: dict[str, Any], answer: Any) -> str | None:
    if not isinstance(answer, dict) or answer.get("type") != question["type"]:
        return f"expected a {question['type']} answer"
    if question["type"] == "noul":
        return None if probability(answer.get("noul")) else "noul is not a probability"
    probabilities = answer.get("probabilities")
    if not isinstance(probabilities, dict) or not all(
        probability(value) for value in probabilities.values()
    ):
        return "probabilities are missing or not finite"
    if not probability(answer.get("confidence")):
        return "confidence is missing or not finite"
    options = question["criteria"]
    if answer.get("choice") not in options or set(probabilities) - set(options):
        return "choice is not one of the requested options"
    return None


def validate_response(
    request: dict[str, Any], raw: Any, number_: int
) -> dict[str, Any]:
    """Check a response against its request; return the answers and usage."""

    def fail(problem: str) -> Failure:
        return Failure(f"invalid TypeSafe response for issue #{number_}: {problem}")

    if not isinstance(raw, dict):
        raise fail("the body is not an object")
    if raw.get("model") != request["model"]:
        raise fail(
            f"answered by {raw.get('model')!r}, but the pin is {request['model']!r}"
        )
    answers, questions = raw.get("answers"), request["questions"]
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise fail("the answer IDs do not match the questions")
    for key, question in questions.items():
        problem = answer_problem(question, answers[key])
        if problem:
            raise fail(f"{key}: {problem}")
    usage = raw.get("usage")
    tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
    if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
        raise fail("usage.input_tokens is missing")
    return {"answers": answers, "input_tokens": tokens}


# --------------------------------------------------------------------- policy


def band(question: Question, value: float) -> str:
    if value >= question.yes:
        return "yes"
    return "no" if value <= question.no else "uncertain"


def family_problems(labels: set[str]) -> list[str]:
    """One state, one type, and one priority at most."""
    return [
        f"several {name} labels: {', '.join(sorted(found))}"
        for name, prefix in FAMILIES.items()
        if len(found := {label for label in labels if label.startswith(prefix)}) > 1
    ]


def unique(labels: list[str]) -> list[str]:
    return list(dict.fromkeys(labels))


@dataclass
class Decision:
    """What the answers imply for one issue, and what apply may do about it."""

    queue: str
    reasons: list[str] = field(default_factory=list)
    add: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)
    judged: dict[str, str | None] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    uncertain_answers: list[str] = field(default_factory=list)

    def record(self) -> dict[str, Any]:
        return {
            "queue": self.queue,
            "reasons": self.reasons,
            "add": self.add,
            "remove": self.remove,
            "judged": self.judged,
            "missing": self.missing,
            "uncertain_answers": self.uncertain_answers,
        }


def decide(
    item: Prepared, answers: dict[str, Any], pack: Pack, catalog: set[str]
) -> Decision:
    """Combine one issue's answers into labels, following label-for-issues' rules.

    Code never asks Jev for a verdict. Each question judges one condition, and a
    label reaches `routine` only when every answer it rests on is clearly yes or no
    and it fills an empty label family. Anything else goes to review with a reason.
    """
    questions = pack.questions
    labels = set(item.labels)
    decision = Decision(queue="routine")
    reasons, add, remove = decision.reasons, decision.add, decision.remove

    def judge(base: str, index: int | None = None) -> str:
        qid = base if index is None else f"{base}_{index}"
        return band(questions[base], answers[qid]["noul"])

    for qid, answer in answers.items():
        base = qid if qid in questions else qid.rsplit("_", 1)[0]
        if (
            answer["type"] == "noul"
            and band(questions[base], answer["noul"]) == "uncertain"
        ):
            decision.uncertain_answers.append(qid)

    def family(prefix: str) -> list[str]:
        return sorted(label for label in labels if label.startswith(prefix))

    # Type: one Choice; an epic parent takes no type.
    existing_type, judged_type = family(TYPE_PREFIX), None
    if EPIC_PARENT not in labels:
        answer = answers["type"]
        if (
            answer["choice"] != NO_MATCH
            and answer["confidence"] >= questions["type"].min_confidence
        ):
            judged_type = TYPE_PREFIX + answer["choice"]
        else:
            decision.uncertain_answers.append("type")
        if not existing_type and judged_type:
            add.append(judged_type)
        elif not existing_type:
            reasons.append(
                f"type unclear: {answer['choice']} at confidence {answer['confidence']:.2f}"
            )
        elif judged_type and judged_type not in existing_type:
            reasons.append(
                f"the answers read the type as {judged_type}, not {', '.join(existing_type)}"
            )
            add.append(judged_type)
            remove.extend(existing_type)
    if EPIC_PARENT in labels:
        kind: str | None = "epic"
    elif len(existing_type) == 1:
        kind = existing_type[0].removeprefix(TYPE_PREFIX)
    else:
        kind = judged_type.removeprefix(TYPE_PREFIX) if judged_type else None

    # Missing information: the checklist for this kind, plus unanswered requests.
    unsure = False
    for qid in CHECKLIST.get(kind, CHECKLIST[None]):
        result = judge(qid)
        if result == "no":
            decision.missing.append(CHECKLIST_NAMES[qid])
        unsure = unsure or result == "uncertain"
    count = item.facts["comments_sent"]
    supplies = [judge("supplies_info", i) for i in range(count)]
    for index in range(count):
        asked, later = judge("asks_info", index), supplies[index + 1 :]
        if asked == "no" or "yes" in later:
            continue
        if asked == "yes" and all(result == "no" for result in later):
            decision.missing.append(f"a reply to {item.comments[index]['url']}")
        else:
            unsure = True

    # State: one condition per state label; code picks at most one.
    declined = [
        judge("declined", index)
        for index, comment in enumerate(item.comments)
        if comment["author_role"] == "maintainer"
    ]
    conditions = {
        WONTFIX: "yes"
        if "yes" in declined
        else "uncertain"
        if "uncertain" in declined
        else "no",
        NEEDS_INFO: "yes" if decision.missing else "uncertain" if unsure else "no",
        NEEDS_TRIAGE: judge("open_decision"),
    }
    holding = [label for label, result in conditions.items() if result == "yes"]
    unclear = [label for label, result in conditions.items() if result == "uncertain"]
    judged_state, state_reason = None, ""
    if len(holding) > 1:
        state_reason = f"conflicting states: {', '.join(holding)}"
    elif unclear:
        state_reason = f"unclear whether {', '.join(unclear)} applies"
    elif holding:
        judged_state = holding[0]
    elif (human := judge("needs_human_impl")) == "uncertain":
        state_reason = (
            "looks ready, but unclear whether an agent or a person should do it"
        )
    else:
        judged_state = READY_HUMAN if human == "yes" else READY_AGENT
    reasons.extend(family_problems(labels))
    existing_state = family(STATE_PREFIX)
    if judged_state is None:
        if not existing_state:
            reasons.append(state_reason)
    elif judged_state not in existing_state:
        if existing_state:
            reasons.append(
                f"the answers point to {judged_state}, not {', '.join(existing_state)}"
            )
            remove.extend(existing_state)
        elif judged_state in NOMINATIONS:
            reasons.append(NOMINATIONS[judged_state])
        add.append(judged_state)

    # Priority: keep an established one; Jev only flags emergencies.
    existing_priority = family(PRIORITY_PREFIX)
    urgency = judge("urgency")
    if urgency == "yes" and P0 not in existing_priority:
        reasons.append("reports an emergency; consider 3-pty:p0")
        add.append(P0)
        remove.extend(existing_priority)
    elif urgency == "uncertain" and P0 not in existing_priority:
        reasons.append("unclear whether this reports an emergency")
    elif urgency == "no" and not existing_priority:
        add.append(P2)

    impediment = judge("impediment")
    if impediment == "yes" and IMPEDIMENT not in labels:
        reasons.append(
            "reports a concrete obstacle; consider 0-impediment and explain it"
        )
        add.append(IMPEDIMENT)
    elif impediment == "no" and IMPEDIMENT in labels:
        reasons.append("0-impediment is set, but no current obstacle is reported")
        remove.append(IMPEDIMENT)
    elif impediment == "uncertain" and IMPEDIMENT not in labels:
        reasons.append("unclear whether an obstacle blocks progress")

    steering = judge("steering")
    if steering != "no":
        qualifier = "" if steering == "yes" else " (uncertain)"
        reasons.insert(0, f"text may try to steer automated triage{qualifier}")
    facts = item.facts
    if facts["body_truncated"] or facts["comments_omitted"]:
        reasons.append(
            f"part of the thread was not sent ({facts['comments_omitted']} comments omitted"
            + (", body truncated)" if facts["body_truncated"] else ")")
        )
    if facts["has_images"] and decision.missing:
        reasons.append("missing details may be in an image, which Jev cannot read")
    absent = [label for label in add if label not in catalog]
    if absent:
        reasons.append(f"the repository lacks {', '.join(absent)}")

    decision.add, decision.remove = unique(add), unique(remove)
    decision.judged = {"type": judged_type, "state": judged_state}
    if item.state != "OPEN":
        decision.queue = "skip"
        reasons.insert(0, "closed")
    elif reasons:
        decision.queue = "review"
    return decision


# ------------------------------------------------------------------- commands


def cmd_doctor(args: argparse.Namespace) -> tuple[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, probe: Any) -> Any:
        try:
            detail = probe()
        except Failure as failure:
            checks.append(
                {"name": name, "ok": False, "detail": "; ".join(failure.problems)}
            )
            return None
        checks.append({"name": name, "ok": True, "detail": detail})
        return detail

    def gh_ready() -> str:
        gh("auth", "status")
        return "authenticated"

    canonical: set[str] = set()

    def vocabulary() -> str:
        canonical.update(load_vocabulary())
        return f"{len(canonical)} canonical labels"

    def questions() -> str:
        pack = load_pack()
        return f"{len(pack.questions)} questions for {pack.model} ({pack.calibration.split(':')[0]})"

    def key() -> str:
        _, source, problem = key_source()
        if problem:
            raise Failure(f"{problem}; {KEY_FIX}")
        return source

    def consent() -> str:
        return f"{len(read_consent())} approved private repositories"

    check("gh", gh_ready)
    check("vocabulary", vocabulary)
    check("questions", questions)
    check("key", key)
    check("consent", consent)
    if args.online:

        def online() -> str:
            from typesafe_sdk import TypeSafeError

            key = key_source()[0]
            if key is None:
                raise Failure("needs the API key")
            try:
                listing = open_client(key, load_pack().model).models.list()
            except TypeSafeError as error:
                raise transport_error(error) from error
            # The listing names aliases; it never judges the versioned pin.
            return "models: " + ", ".join(model.name for model in listing.models)

        check("online", online)
    if args.repo:
        repo = args.repo

        def repository() -> str:
            visibility = repo_visibility(repo)
            problem = consent_problem(repo, visibility)
            if problem:
                raise Failure(f"{problem}; {consent_fix(repo)}")
            return f"{repo} is {visibility.lower()}"

        def labels() -> str:
            if not canonical:
                raise Failure("cannot compare labels without the vocabulary")
            missing = sorted(canonical - repo_labels(repo))
            if missing:
                raise Failure(
                    f"{repo} lacks {', '.join(missing)}; create them with label-for-issues (setup-only request) before apply"
                )
            return "all canonical labels exist"

        check("repository", repository)
        check("labels", labels)

    failed = [c for c in checks if not c["ok"]]
    result = {"schema": DOCTOR_SCHEMA, "ok": not failed, "checks": checks}
    if failed:
        raise Failure(*(f"{c['name']}: {c['detail']}" for c in failed), result=result)
    return "ok: " + ", ".join(c["name"] for c in checks), result


def cmd_consent(args: argparse.Namespace) -> tuple[str, Any]:
    entries = read_consent()
    if args.action == "list":
        listing = [{"repo": repo, **entries[repo]} for repo in sorted(entries)]
        lines = [
            f"{e['repo']}: approved by {e.get('approved_by')} on {e.get('approved_on')} ({e.get('terms')})"
            for e in listing
        ]
        return "\n".join(lines) or "no approved private repositories", {
            "consent": listing
        }
    if not args.repo:
        raise UsageError(f"consent {args.action} needs owner/repo")
    repo = args.repo
    if args.action == "remove":
        if entries.pop(repo, None) is None:
            return f"{repo} had no consent", {"removed": False, "repo": repo}
        write_consent(entries)
        return f"removed consent for {repo}", {"removed": True, "repo": repo}
    if not (args.by or "").strip():
        raise UsageError(
            "consent add needs --by with the name of the person who approved"
        )
    entries[repo] = {
        "approved_by": args.by.strip(),
        "approved_on": now().date().isoformat(),
        "terms": TERMS_NAME,
    }
    write_consent(entries)
    return f"approved {repo} under {TERMS_NAME}", {"repo": repo, **entries[repo]}


def new_run_id(repo: str) -> str:
    """A timestamped ID that no earlier preview or record in this second uses."""
    base = now().strftime("%Y%m%dT%H%M%SZ-") + re.sub(
        r"[^a-z0-9]+", "-", repo.lower()
    ).strip("-")
    run_id, count = base, 1
    while any(
        (runs_dir() / f"{run_id}{end}").exists() for end in (".json", ".preview.json")
    ):
        count += 1
        run_id = f"{base}-{count}"
    return run_id


def cmd_run(args: argparse.Namespace) -> tuple[str, Any]:
    pack = load_pack()
    canonical = load_vocabulary()
    repo = args.repo
    visibility = repo_visibility(repo)
    key = None
    if not args.dry_run:
        problem = consent_problem(repo, visibility)
        if problem:
            raise Failure(f"{problem}; nothing was sent; {consent_fix(repo)}")
        key = resolve_key()
    catalog = repo_labels(repo)
    missing = sorted(canonical - catalog)
    if missing:
        print(
            f"warning: {repo} lacks canonical labels {', '.join(missing)}; set them up with label-for-issues before apply",
            file=sys.stderr,
        )
    issues = fetch_issues(repo, args)
    prepared = prepare_all(issues, pack, args.max_requests)
    run_id = new_run_id(repo)
    header = {
        "id": run_id,
        "repo": repo,
        "visibility": visibility,
        "consent": "not needed"
        if visibility == "PUBLIC"
        else consent_problem(repo, visibility) or "recorded",
        "created_at": now().isoformat(timespec="seconds"),
        "engine": VERSION,
        "model": pack.model,
        "questions_digest": pack.digest,
        "calibration": pack.calibration,
        "missing_labels": missing,
    }
    if args.dry_run:
        return preview_run(header, prepared)
    assert key is not None
    return live_run(header, prepared, pack, catalog, key, args.verbose)


def preview_run(header: dict[str, Any], prepared: list[Prepared]) -> tuple[str, Any]:
    asked = [item for item in prepared if item.request is not None]
    tokens = sum(item.tokens for item in asked)
    preview = {
        "schema": PREVIEW_SCHEMA,
        **header,
        "estimated": {
            "requests": len(asked),
            "tokens": tokens,
            "cost_usd": cost_usd(tokens),
        },
        "issues": [{**item.summary(), "request": item.request} for item in prepared],
    }
    path = runs_dir() / f"{header['id']}.preview.json"
    write_json(path, preview)
    line = (
        f"preview {header['id']}: {len(prepared)} issues, {len(asked)} requests, "
        f"~{tokens:,} tokens, ~${cost_usd(tokens):.4f}; nothing sent; payload: {path}"
    )
    summary = {key: value for key, value in preview.items() if key != "issues"}
    summary["path"] = str(path)
    summary["issues"] = [
        {
            "number": i.number,
            "skip": i.skip,
            "estimated_tokens": i.tokens,
            "facts": i.facts,
        }
        for i in prepared
    ]
    return line, summary


def live_run(
    header: dict[str, Any],
    prepared: list[Prepared],
    pack: Pack,
    catalog: set[str],
    key: str,
    verbose: bool,
) -> tuple[str, Any]:
    client = open_client(key, pack.model)
    entries: list[dict[str, Any]] = []
    error: str | None = None
    tokens = requests = 0
    for item in prepared:
        entry = item.summary()
        if item.request is None:
            entry.update(Decision(queue="skip", reasons=[str(item.skip)]).record())
        elif error is not None:
            reason = "not asked: the run stopped at an earlier error"
            entry.update(Decision(queue="skip", reasons=[reason]).record())
        else:
            try:
                raw = send(client, item.request)
                result = validate_response(item.request, raw, item.number)
            except Failure as failure:
                error = failure.problems[0]
                entry.update(
                    Decision(queue="skip", reasons=[f"not asked: {error}"]).record()
                )
            else:
                requests += 1
                tokens += result["input_tokens"]
                entry.update(decide(item, result["answers"], pack, catalog).record())
                entry["answers"] = result["answers"]
                entry["input_tokens"] = result["input_tokens"]
                if verbose:
                    print(f"#{item.number}: {entry['queue']}", file=sys.stderr)
        entries.append(entry)
    counts = {queue: sum(e["queue"] == queue for e in entries) for queue in QUEUES}
    record = {
        "schema": RUN_SCHEMA,
        **header,
        "usage": {
            "requests": requests,
            "input_tokens": tokens,
            "cost_usd": cost_usd(tokens),
        },
        "counts": counts,
        "error": error,
        "issues": entries,
    }
    path = runs_dir() / f"{header['id']}.json"
    write_json(path, record)
    if error is not None:
        raise Failure(error, f"the run stopped; the partial record is {path}")
    line = (
        f"run {header['id']}: {len(entries)} issues; "
        + ", ".join(f"{counts[queue]} {queue}" for queue in QUEUES)
        + f"; {tokens:,} tokens, ${cost_usd(tokens):.4f}; record: {path}"
    )
    summary = {key: value for key, value in record.items() if key != "issues"}
    summary["path"] = str(path)
    summary["issues"] = [
        {
            key: e[key]
            for key in ("number", "queue", "add", "remove", "reasons", "missing")
        }
        for e in entries
    ]
    return line, summary


def resolve_run(ref: str) -> Path:
    if ref == "last":
        runs = [p for p in runs_dir().glob("*.json") if RUN_FILE.match(p.name)]
        if not runs:
            raise Failure("no run records yet; run `jevlabel run` first")
        return max(runs, key=lambda p: (p.stat().st_mtime_ns, p.name))
    path = runs_dir() / f"{ref}.json"
    if not RUN_FILE.match(path.name) or not path.is_file():
        raise Failure(f"no run record {ref!r} in {runs_dir()}; pass a run ID or `last`")
    return path


def load_run(ref: str) -> tuple[Path, dict[str, Any]]:
    path = resolve_run(ref)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Failure(f"{path} is unreadable: {error}") from error
    if record.get("schema") != RUN_SCHEMA:
        raise Failure(f"{path} is not a {RUN_SCHEMA} record")
    return path, record


def cmd_compare(args: argparse.Namespace) -> tuple[str, Any]:
    """Compare Jev's judged type and state with the labels the issues already had."""
    _, record = load_run(args.run)
    families = {name: FAMILIES[name] for name in ("type", "state")}
    counts = {name: dict.fromkeys(OUTCOMES, 0) for name in families}
    disagreements: list[dict[str, Any]] = []
    for entry in record["issues"]:
        if "answers" not in entry:
            continue
        for name, prefix in families.items():
            existing = sorted(
                label for label in entry["labels"] if label.startswith(prefix)
            )
            judged = entry["judged"][name]
            if judged is None:
                outcome = "abstain"
            elif not existing:
                outcome = "unlabeled"
            elif judged in existing:
                outcome = "agree"
            else:
                outcome = "disagree"
                disagreements.append(
                    {
                        "number": entry["number"],
                        "family": name,
                        "existing": existing,
                        "judged": judged,
                    }
                )
            counts[name][outcome] += 1
    result = {
        "schema": COMPARE_SCHEMA,
        "run": record["id"],
        "calibration": record["calibration"],
        "counts": counts,
        "disagreements": disagreements,
    }
    line = (
        f"compare {record['id']}: "
        + "; ".join(
            f"{name} "
            + ", ".join(f"{n} {outcome}" for outcome, n in counts[name].items())
            for name in families
        )
        + ". Existing labels are a baseline, not ground truth"
    )
    return line, result


# ------------------------------------------------------------------------ cli


def common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json", action="store_true", help="print one JSON object on stdout"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print tracebacks on failure"
    )


def build_parser() -> Parser:
    parser = Parser(
        prog="jevlabel",
        description=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )
    parser.add_argument("--version", action="version", version=f"jevlabel {VERSION}")
    commands = parser.add_subparsers(dest="command", parser_class=Parser)

    doctor = commands.add_parser(
        "doctor",
        help="check readiness",
        description="Check gh, the label vocabulary, the questions, the API key, and consent. "
        "With -R, also check the repository's visibility, consent, and canonical labels.",
    )
    doctor.add_argument("-R", "--repo", type=repo_name, help="owner/repo to check")
    doctor.add_argument(
        "--online", action="store_true", help="also list TypeSafe models with the key"
    )
    common(doctor)

    consent = commands.add_parser(
        "consent",
        help="record private repositories approved for TypeSafe",
        description=(
            "Record, list, or remove approval to send a private repository's issue text to "
            f"TypeSafe. Terms {TERMS_NAME}: {TERMS_SUMMARY}. Run `add` only after the user "
            "has seen a --dry-run preview and approved; never approve on their behalf."
        ),
        epilog='example: jevlabel consent add pascalandy/skills-private --by "Pascal Andy"',
    )
    consent.add_argument("action", choices=("add", "remove", "list"))
    consent.add_argument("repo", nargs="?", type=repo_name, help="owner/repo")
    consent.add_argument("--by", help="name of the person who approved (add only)")
    common(consent)

    run = commands.add_parser(
        "run",
        help="triage issues with Jev",
        description="Fetch issues, build each issue's input, ask Jev, and write a run "
        "record with each issue's queue, proposed labels, reasons, and answers. "
        "--dry-run writes the exact request bodies to a preview file and sends nothing. "
        "A private repository needs recorded consent before a live run.",
        epilog="examples:\n  jevlabel run -R pascalandy/skills --dry-run\n"
        "  jevlabel run -R pascalandy/skills\n"
        "  jevlabel run -R pascalandy/skills --issue 12 --issue 14",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run.add_argument("-R", "--repo", type=repo_name, required=True, help="owner/repo")
    run.add_argument(
        "--issue", type=int, action="append", help="issue number; repeatable"
    )
    run.add_argument("--search", help="GitHub search query to select issues")
    run.add_argument(
        "--state",
        choices=("open", "closed", "all"),
        default="open",
        help="default: open",
    )
    run.add_argument(
        "--limit", type=int, default=1000, help="most issues to fetch (default 1000)"
    )
    run.add_argument(
        "--max-requests", type=int, help="most Jev requests; later issues are skipped"
    )
    run.add_argument(
        "--dry-run", action="store_true", help="preview the payload; send nothing"
    )
    common(run)
    compare = commands.add_parser(
        "compare",
        help="compare a run with existing labels",
        description="For calibration: count where a run's judged type and state agree "
        "with the labels each issue already had. Existing labels are a baseline, "
        "not ground truth. Reads the record only; no network.",
        epilog="example: jevlabel run -R pascalandy/skills --state all && jevlabel compare last",
    )
    compare.add_argument("run", help="run ID, or `last`")
    common(compare)
    return parser


COMMANDS = {
    "doctor": cmd_doctor,
    "consent": cmd_consent,
    "run": cmd_run,
    "compare": cmd_compare,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = None
    try:
        args = parser.parse_args(argv)
        if args.command is None:
            print(HELP, end="")
            return 0
        if getattr(args, "max_requests", None) is not None and args.max_requests < 1:
            raise UsageError("--max-requests must be at least 1")
        if getattr(args, "limit", 1) < 1:
            raise UsageError("--limit must be at least 1")
        line, result = COMMANDS[args.command](args)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_USAGE
    except Failure as failure:
        if (
            args is not None
            and getattr(args, "json", False)
            and failure.result is not None
        ):
            print(json.dumps(failure.result, ensure_ascii=False))
        for problem in failure.problems:
            print(f"error: {problem}", file=sys.stderr)
        if args is not None and getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        else:
            print("rerun with --verbose for details", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
APPLY_SCHEMA = "jevlabel.apply/v1"
DOCTOR_SCHEMA = "jevlabel.doctor/v1"
LABELS_SCHEMA = "jevlabel.labels/v1"
SHOW_SCHEMA = "jevlabel.show/v1"
SET_SCHEMA = "jevlabel.set/v1"
QUESTIONS_SCHEMA = "jevlabel.questions/v1"
EXIT_ERROR, EXIT_USAGE, EXIT_INTERRUPTED = 1, 2, 130
RUN_FILE = re.compile(r"^\d{8}T\d{6}Z-[a-z0-9-]+\.json$")
QUEUES = ("routine", "review", "skip")
OUTCOMES = ("agree", "disagree", "abstain", "unlabeled")
APPLY_OUTCOMES = ("applied", "would-apply", "already", "stale", "conflict", "failed")
LABEL_OUTCOMES = (
    "created",
    "fixed",
    "would-create",
    "would-fix",
    "ok",
    "blocked",
    "failed",
)

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
# `set` needs --reason to add these: the evidence label-for-issues asks for.
READINESS = "the readiness review: reviewer, date, scope, conclusion, and blockers"
NEEDS_REASON = {
    READY_AGENT: READINESS,
    READY_HUMAN: READINESS,
    WONTFIX: "the maintainer's decision to decline the work",
    P0: "the concrete emergency",
    IMPEDIMENT: "the obstacle, which the issue must also explain",
}
EPIC_PREFIX = "4-epic:"
# Near-duplicate label names compare without case, a numeric or family prefix,
# or punctuation, so `bug` and `Priority: P1` match `2-type:bug` and `3-pty:p1`.
LABEL_PREFIX = re.compile(r"^(?:\d+-)?(?:(?:type|pty|priority|epic|state)\s*:\s*)?")
# `Blocked by` prerequisites in an issue body: a heading's section, or a line that
# starts with it. Mid-sentence, it often describes another issue, as in an epic.
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
BLOCKED_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+blocked by\b", re.IGNORECASE)
BLOCKED_LINE = re.compile(
    r"^[\s>*_+-]*blocked by\b(.*?)(?:[.;](?:\s|$)|$)", re.IGNORECASE
)
LINK_DEFINITION = re.compile(r"^\s*\[[^\]]+\]:\s")
# In a `Blocked by` section, a list item or a line that starts with a reference.
BLOCKER_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s|^\s*\[?#\d|^\s*https://")
# Timeline items that tell `set` who changed an issue since a run.
TIMELINE_TYPES = (
    "LABELED_EVENT, UNLABELED_EVENT, ISSUE_COMMENT, CLOSED_EVENT, REOPENED_EVENT, "
    "RENAMED_TITLE_EVENT"
)
CHANGES = {
    "IssueComment": "new comment",
    "ClosedEvent": "closed",
    "ReopenedEvent": "reopened",
    "RenamedTitleEvent": "title changed",
}
LINKED = "number title state url"

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
  labels    create missing canonical labels; report look-alikes, never migrate them
  consent   record which private repositories may send issue text to TypeSafe
  run       fetch issues, ask Jev, and write a run record (--dry-run: preview only)
  apply     add routine issues' labels and review issues' fill, rereading each first
  show      print one issue of a run: thread, links, and the run's reasons
  set       write the agent's review decision on one issue of a run
  compare   compare a run's judged type and state with the labels issues already had

queues in a run record:
  routine   every answer used is clear and the labels only fill empty families
  review    an answer is uncertain, or a label needs a person or new evidence;
            its fill is the judged type and p2, each only for an empty family
  skip      closed, pull request, agent work in progress, or not asked

examples:
  jevlabel doctor -R pascalandy/skills --online
  jevlabel labels -R pascalandy/skills --dry-run
  jevlabel run -R pascalandy/skills --dry-run
  jevlabel run -R pascalandy/skills
  jevlabel apply last --dry-run
  jevlabel show last --issue 24
  jevlabel set last 24 --add 1-needs-triage --dry-run
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


def graphql(query: str, **variables: str | int) -> dict[str, Any]:
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
    data = gh_json(*args)
    if not isinstance(data, dict) or not isinstance(data.get("data"), dict):
        raise Failure("`gh api graphql` returned no data")
    return data["data"]


def repo_visibility(repo: str) -> str:
    data = gh_json("repo", "view", repo, "--json", "visibility")
    return str(data.get("visibility", "")).upper()


def repo_labels(repo: str) -> set[str]:
    data = gh_json("label", "list", "-R", repo, "--limit", "1000", "--json", "name")
    return {label["name"] for label in data}


def repo_label_details(repo: str) -> dict[str, dict[str, str]]:
    data = gh_json(
        "label",
        "list",
        "-R",
        repo,
        "--limit",
        "1000",
        "--json",
        "name,color,description",
    )
    return {
        label["name"]: {
            "color": str(label.get("color") or "").lower(),
            "description": str(label.get("description") or ""),
        }
        for label in data
    }


def labeled_issues(repo: str, label: str) -> list[int]:
    data = gh_json(
        "issue",
        "list",
        "-R",
        repo,
        "--label",
        label,
        "--state",
        "all",
        "--limit",
        "1000",
        "--json",
        "number",
    )
    return sorted(issue["number"] for issue in data)


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


def vocabulary_labels() -> list[dict[str, str]]:
    """The canonical labels, with color and description, from label-for-issues' ## Labels JSON."""
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
    fields = ("name", "color", "description")
    try:
        labels = [
            {key: label[key] for key in fields} for label in json.loads(match.group(1))
        ]
    except (ValueError, KeyError, TypeError) as error:
        raise Failure(
            f"the ## Labels JSON in {VOCABULARY_FILE} is malformed"
        ) from error
    if not all(isinstance(label[key], str) for label in labels for key in fields):
        raise Failure(f"the ## Labels JSON in {VOCABULARY_FILE} is malformed")
    return labels


def load_vocabulary() -> set[str]:
    """Read the canonical label names, and check the policy's labels are among them."""
    names = {label["name"] for label in vocabulary_labels()}
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
    # For a review issue, the labels apply may still add: a judged type or p2,
    # each into an empty family.
    fill: list[str] = field(default_factory=list)

    def record(self) -> dict[str, Any]:
        return {
            "queue": self.queue,
            "reasons": self.reasons,
            "add": self.add,
            "remove": self.remove,
            "fill": self.fill,
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
    and it fills an empty label family. Anything else goes to review with a reason;
    its judged type and p2 may still fill empty families.
    """
    questions = pack.questions
    labels = set(item.labels)
    decision = Decision(queue="routine")
    reasons, add, remove = decision.reasons, decision.add, decision.remove
    fill: list[str] = []

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
            fill.append(judged_type)
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
    # A later comment with facts may answer a request or say something else, so
    # only a request followed by no facts at all counts as clearly unanswered.
    count = item.facts["comments_sent"]
    supplies = [judge("supplies_info", i) for i in range(count)]
    maybe_answered: list[str] = []
    for index in range(count):
        asked, later = judge("asks_info", index), supplies[index + 1 :]
        if asked == "no":
            continue
        url = item.comments[index]["url"]
        if asked == "yes" and all(result == "no" for result in later):
            decision.missing.append(f"a reply to {url}")
        else:
            maybe_answered.append(url)
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
        if NEEDS_INFO in unclear and maybe_answered:
            state_reason += (
                f"; check whether {', '.join(maybe_answered)} got its answer"
            )
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
        # Uncertainty keeps an existing state; a confident conflict never does.
        if not existing_state or len(holding) > 1:
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
        fill.append(P2)

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
        # Text that may steer triage may have steered the type too.
        if steering == "no":
            decision.fill = [label for label in fill if label in catalog]
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
                    f"{repo} lacks {', '.join(missing)}; create them with `jevlabel labels -R {repo}` before apply"
                )
            return "all canonical labels exist"

        check("repository", repository)
        check("labels", labels)

    failed = [c for c in checks if not c["ok"]]
    result = {"schema": DOCTOR_SCHEMA, "ok": not failed, "checks": checks}
    if failed:
        raise Failure(*(f"{c['name']}: {c['detail']}" for c in failed), result=result)
    return "ok: " + ", ".join(c["name"] for c in checks), result


def label_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", LABEL_PREFIX.sub("", name.lower(), count=1))


def lookalikes(
    wanted: list[dict[str, str]], existing: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    """Existing labels whose names resemble a canonical one without matching it."""
    names = {label["name"] for label in wanted}
    by_case = {name.lower(): name for name in names}
    by_key = {label_key(name): name for name in names}
    found: list[dict[str, Any]] = []
    for name in sorted(existing):
        target = by_case.get(name.lower()) or by_key.get(label_key(name))
        if name in names or target is None:
            continue
        kind = "case variant" if name.lower() == target.lower() else "near duplicate"
        found.append({"name": name, "canonical": target, "kind": kind})
    return found


def write_labels(
    repo: str, spec: dict[str, dict[str, str]], todo: list[dict[str, Any]]
) -> None:
    """Create or fix each planned label, then read every written one back."""
    for result in todo:
        label = spec[result["name"]]
        verb = "create" if result["outcome"] == "would-create" else "edit"
        try:
            gh(
                "label",
                verb,
                label["name"],
                "-R",
                repo,
                "--color",
                label["color"],
                "--description",
                label["description"],
            )
        except Failure as failure:
            result.update(outcome="failed", detail=failure.problems[0])
        else:
            result["outcome"] = "created" if verb == "create" else "fixed"
    written = [result for result in todo if result["outcome"] != "failed"]
    try:
        after = repo_label_details(repo)
    except Failure as failure:
        for result in written:
            result.update(
                outcome="failed", detail=f"not read back: {failure.problems[0]}"
            )
        return
    for result in written:
        label = spec[result["name"]]
        wanted = {"color": label["color"].lower(), "description": label["description"]}
        if after.get(label["name"]) != wanted:
            result.update(
                outcome="failed",
                detail="its color or description differs after the write",
            )


def cmd_labels(args: argparse.Namespace) -> tuple[str, Any]:
    """Create missing canonical labels and fix drifted metadata on exact names."""
    repo = args.repo
    wanted = vocabulary_labels()
    existing = repo_label_details(repo)
    similar = lookalikes(wanted, existing)
    # GitHub label names ignore case, so a case variant holds the canonical name.
    held = {
        item["canonical"]: item["name"]
        for item in similar
        if item["kind"] == "case variant"
    }
    results: list[dict[str, Any]] = []
    for label in wanted:
        name, have = label["name"], existing.get(label["name"])
        result = {"name": name, "outcome": "ok", "detail": ""}
        if name in held:
            result.update(
                outcome="blocked", detail=f"{held[name]} holds its name in another case"
            )
        elif have is None:
            result["outcome"] = "would-create"
        else:
            canon = {
                "color": label["color"].lower(),
                "description": label["description"],
            }
            drift = [
                f"{key} {have[key]!r} -> {canon[key]!r}"
                for key in ("color", "description")
                if have[key] != canon[key]
            ]
            if drift:
                result.update(outcome="would-fix", detail="; ".join(drift))
        results.append(result)
    for item in similar:
        item["issues"] = labeled_issues(repo, item["name"])
    todo = [r for r in results if r["outcome"] in ("would-create", "would-fix")]
    if todo and not args.dry_run:
        write_labels(repo, {label["name"]: label for label in wanted}, todo)
    counts = {
        name: sum(r["outcome"] == name for r in results) for name in LABEL_OUTCOMES
    }
    log: dict[str, Any] = {
        "schema": LABELS_SCHEMA,
        "repo": repo,
        "created_at": now().isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "counts": counts,
        "results": results,
        "lookalikes": similar,
    }
    parts = ", ".join(f"{n} {name}" for name, n in counts.items() if n)
    if args.dry_run:
        line = f"labels {repo} --dry-run: {parts}; nothing written"
    elif todo:
        log_path = new_log(state_home() / "labels", f"{stamp()}-{slug(repo)}")
        write_json(log_path, log)
        log["path"] = str(log_path)
        line = f"labels {repo}: {parts}; log: {log_path}"
    else:
        line = f"labels {repo}: {parts}"
    for item in similar:
        if item["kind"] == "near duplicate":
            carriers = ", ".join(f"#{n}" for n in item["issues"]) or "none"
            print(
                f"warning: {item['name']} looks like {item['canonical']} (issues: "
                f"{carriers}); jevlabel never renames, deletes, or migrates a label: "
                "ask the user before migrating it",
                file=sys.stderr,
            )
    failed = [r for r in results if r["outcome"] in ("blocked", "failed")]
    if failed:
        blocked = any(r["outcome"] == "blocked" for r in failed)
        hints = (
            [
                "rename a case variant only after the user approves the migration, then rerun"
            ]
            if blocked
            else []
        )
        raise Failure(
            *(f"{r['name']}: {r['outcome']}: {r['detail']}" for r in failed),
            *hints,
            f"{len(failed)} canonical labels are not in place; see {log.get('path', 'the output')}",
            result=log,
        )
    return line, log


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


def slug(repo: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", repo.lower()).strip("-")


def stamp() -> str:
    return now().strftime("%Y%m%dT%H%M%SZ")


def new_log(directory: Path, stem: str) -> Path:
    """A log path that no earlier log in this second uses."""
    path, count = directory / f"{stem}.json", 1
    while path.exists():
        count += 1
        path = directory / f"{stem}-{count}.json"
    return path


def new_run_id(repo: str) -> str:
    """A timestamped ID that no earlier preview or record in this second uses."""
    base = now().strftime("%Y%m%dT%H%M%SZ-") + slug(repo)
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
    interrupted = False
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
            except KeyboardInterrupt:
                error, interrupted = "interrupted", True
                entry.update(
                    Decision(queue="skip", reasons=["not asked: interrupted"]).record()
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
    if interrupted:
        print(f"the partial record is {path}", file=sys.stderr)
        raise KeyboardInterrupt
    if error is not None:
        raise Failure(error, f"the run stopped; the partial record is {path}")
    line = (
        f"run {header['id']}: {len(entries)} issues; "
        + ", ".join(f"{counts[queue]} {queue}" for queue in QUEUES)
        + f"; {tokens:,} tokens, ${cost_usd(tokens):.4f}; record: {path}"
    )
    summary = {key: value for key, value in record.items() if key != "issues"}
    summary["path"] = str(path)
    shown = ("number", "queue", "add", "remove", "fill", "reasons", "missing")
    summary["issues"] = [{key: e[key] for key in shown} for e in entries]
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


def issue_now(repo: str, number: int) -> dict[str, Any]:
    return gh_json(
        "issue", "view", str(number), "-R", repo, "--json", "labels,state,updatedAt"
    )


def writable(entry: dict[str, Any]) -> list[str]:
    """A routine issue's proposed labels, or a review issue's fill."""
    if entry["queue"] == "routine":
        return entry["add"]
    # Records from before fill existed have none.
    return entry.get("fill", []) if entry["queue"] == "review" else []


def apply_one(
    repo: str, entry: dict[str, Any], catalog: set[str], dry_run: bool
) -> dict[str, Any]:
    number = entry["number"]
    result: dict[str, Any] = {"number": number, "labels": []}

    def outcome(name: str, detail: str = "") -> dict[str, Any]:
        return {**result, "outcome": name, "detail": detail}

    if entry["queue"] == "routine" and entry["remove"]:
        return outcome(
            "failed", "a routine entry never removes labels; the record is invalid"
        )
    current = issue_now(repo, number)
    labels = {label["name"] for label in current.get("labels") or []}
    todo = [label for label in writable(entry) if label not in labels]
    if not todo:
        return outcome("already", "every proposed label is present")
    if str(current.get("state", "")).upper() != "OPEN":
        return outcome("stale", "closed since the run")
    if current.get("updatedAt") != entry["updated_at"]:
        return outcome("stale", "changed since the run; run it again before applying")
    filled = [
        label
        for label in todo
        for prefix in FAMILIES.values()
        if label.startswith(prefix)
        and any(other.startswith(prefix) for other in labels)
    ]
    if filled:
        return outcome(
            "conflict", f"its family already has a label: {', '.join(filled)}"
        )
    absent = [label for label in todo if label not in catalog]
    if absent:
        return outcome(
            "failed",
            f"{repo} lacks {', '.join(absent)}; create it with label-for-issues",
        )
    result["labels"] = todo
    if dry_run:
        return outcome("would-apply")
    gh("issue", "edit", str(number), "-R", repo, "--add-label", ",".join(todo))
    after = {label["name"] for label in issue_now(repo, number).get("labels") or []}
    problems = [
        f"{label} is missing after the write" for label in todo if label not in after
    ]
    problems += family_problems(after)
    if problems:
        return outcome("failed", "; ".join(problems))
    return outcome("applied")


def cmd_apply(args: argparse.Namespace) -> tuple[str, Any]:
    """Write routine issues' labels and review issues' fill, rereading each first."""
    path, record = load_run(args.run)
    repo = record["repo"]
    load_vocabulary()
    selected = set(args.issue or [])
    entries = [
        entry
        for entry in record["issues"]
        if writable(entry) and (not selected or entry["number"] in selected)
    ]
    catalog = repo_labels(repo) if entries else set()
    results: list[dict[str, Any]] = []
    for entry in entries:
        try:
            results.append(apply_one(repo, entry, catalog, args.dry_run))
        except Failure as failure:
            detail = f"{failure.problems[0]}; reread the issue before retrying"
            results.append(
                {
                    "number": entry["number"],
                    "labels": [],
                    "outcome": "failed",
                    "detail": detail,
                }
            )
    counts = {
        name: sum(r["outcome"] == name for r in results) for name in APPLY_OUTCOMES
    }
    written = sum(
        len(r["labels"]) for r in results if r["outcome"] in ("applied", "would-apply")
    )
    log = {
        "schema": APPLY_SCHEMA,
        "run": record["id"],
        "repo": repo,
        "created_at": now().isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "counts": counts,
        "results": results,
    }
    parts = ", ".join(f"{n} {name}" for name, n in counts.items() if n)
    if args.dry_run:
        line = f"apply {record['id']} --dry-run: {parts or 'nothing to apply'}; {written} labels; nothing written"
    else:
        log_path = path.with_name(
            f"{record['id']}.apply-{now().strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        write_json(log_path, log)
        log["path"] = str(log_path)
        line = f"apply {record['id']}: {parts or 'nothing to apply'}; {written} labels; log: {log_path}"
    failed = [r for r in results if r["outcome"] == "failed"]
    if failed:
        raise Failure(
            *(f"#{r['number']}: {r['detail']}" for r in failed),
            f"{len(failed)} of {len(results)} issues failed; see {log.get('path', 'the output')}",
            result=log,
        )
    return line, log


def run_entry(record: dict[str, Any], number: int) -> dict[str, Any] | None:
    return next((e for e in record["issues"] if e["number"] == number), None)


def moment(value: str) -> datetime:
    return datetime.fromisoformat(value)


def own_writes(run_id: str, entry: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Labels this run's apply and set may have added to or removed from one issue."""
    added, removed = set(writable(entry)), set()
    for path in runs_dir().glob(f"{run_id}.set-{entry['number']}-*.json"):
        try:
            log = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # An unreadable log only makes the check stricter
        added.update(log.get("added", []))
        removed.update(log.get("removed", []))
    return added, removed


def changes_since(repo: str, number: int, since: str) -> dict[str, Any]:
    owner, name = repo.split("/")
    query = (
        "query($owner: String!, $name: String!, $number: Int!, $since: DateTime!) {"
        " repository(owner: $owner, name: $name) { issue(number: $number) { lastEditedAt"
        f" timelineItems(first: 100, since: $since, itemTypes: [{TIMELINE_TYPES}]) {{"
        " pageInfo { hasNextPage } nodes { __typename"
        " ... on LabeledEvent { createdAt label { name } }"
        " ... on UnlabeledEvent { createdAt label { name } }"
        " ... on IssueComment { createdAt } ... on ClosedEvent { createdAt }"
        " ... on ReopenedEvent { createdAt } ... on RenamedTitleEvent { createdAt }"
        " } } } } }"
    )
    data = graphql(query, owner=owner, name=name, number=number, since=since)
    return data["repository"]["issue"] or {}


def stale_reason(
    repo: str, run_id: str, entry: dict[str, Any], current: dict[str, Any]
) -> str | None:
    """What changed an issue since the run, or None when nothing did.

    Label writes by this run's apply and set do not count: apply fills a review
    issue before the agent decides it. Anything else does, whoever made it.
    """
    closed = str(current.get("state", "")).upper() != "OPEN"
    if closed and entry["state"] == "OPEN":
        return "closed"
    since = entry["updated_at"]
    if current.get("updatedAt") == since:
        return None
    added, removed = own_writes(run_id, entry)
    changes = changes_since(repo, entry["number"], since)
    timeline = changes.get("timelineItems") or {}
    latest: datetime | None = None
    for item in timeline.get("nodes") or []:
        at = moment(item["createdAt"])
        if at <= moment(since):
            continue
        kind, label = item["__typename"], (item.get("label") or {}).get("name")
        if (kind == "LabeledEvent" and label in added) or (
            kind == "UnlabeledEvent" and label in removed
        ):
            latest = at if latest is None else max(latest, at)
        elif kind in ("LabeledEvent", "UnlabeledEvent"):
            verb = "added" if kind == "LabeledEvent" else "removed"
            return f"{label} {verb} outside jevlabel"
        else:
            return CHANGES.get(kind, kind)
    if (timeline.get("pageInfo") or {}).get("hasNextPage"):
        return "more than 100 timeline changes"
    edited = changes.get("lastEditedAt")
    if edited and moment(edited) > moment(since):
        return "body edited"
    # A later update that no timeline item explains, such as an assignment.
    if latest is None or moment(current["updatedAt"]) > latest:
        return "updated outside jevlabel"
    return None


def blockers(body: str, repo: str) -> list[int]:
    """Issues this repository's body names as `Blocked by` prerequisites."""
    reference = re.compile(
        rf"(?<![\w/&])#(\d+)\b|https://github\.com/{re.escape(repo)}/(?:issues|pull)/(\d+)",
        re.IGNORECASE,
    )
    numbers: list[int] = []
    section = False
    for line in body.splitlines():
        heading = HEADING.match(line) is not None
        if heading:
            section = BLOCKED_HEADING.match(line) is not None
        listed = BLOCKER_LINE.match(line) and not LINK_DEFINITION.match(line)
        opener = BLOCKED_LINE.match(line)
        if section and not heading and listed:
            text = line
        else:
            text = opener.group(1) if opener else ""
        numbers += [int(a or b) for a, b in reference.findall(text)]
    return list(dict.fromkeys(numbers))


def issue_links(repo: str, number: int, body: str) -> dict[str, list[dict[str, Any]]]:
    """Each linked issue or pull request with its state."""
    owner, name = repo.split("/")
    named = [n for n in blockers(body, repo) if n != number]
    either = f"... on Issue {{ {LINKED} }} ... on PullRequest {{ {LINKED} }}"
    aliases = "".join(
        f" b{n}: issueOrPullRequest(number: {n}) {{ {either} }}" for n in named
    )
    query = (
        "query($owner: String!, $name: String!, $number: Int!) {"
        " repository(owner: $owner, name: $name) {"
        f" issue(number: $number) {{ parent {{ {LINKED} }}"
        f" subIssues(first: 100) {{ nodes {{ {LINKED} }} }}"
        f" blockedBy(first: 100) {{ nodes {{ {LINKED} }} }}"
        f" blocking(first: 100) {{ nodes {{ {LINKED} }} }}"
        " closedByPullRequestsReferences(first: 100, includeClosedPrs: true)"
        f" {{ nodes {{ {LINKED} }} }} }}{aliases} }} }}"
    )
    data = graphql(query, owner=owner, name=name, number=number)["repository"]
    issue = data.get("issue") or {}

    def nodes(key: str) -> list[dict[str, Any]]:
        return [node for node in (issue.get(key) or {}).get("nodes") or [] if node]

    blocked_by = [{**node, "source": "relationship"} for node in nodes("blockedBy")]
    known = {node["number"] for node in blocked_by}
    for n in named:
        if n not in known:
            node = data.get(f"b{n}") or {
                "number": n,
                "title": "",
                "state": "NOT FOUND",
                "url": "",
            }
            blocked_by.append({**node, "source": "body"})
    return {
        "parent": [issue["parent"]] if issue.get("parent") else [],
        "sub_issues": nodes("subIssues"),
        "blocked_by": blocked_by,
        "blocking": nodes("blocking"),
        "pull_requests": nodes("closedByPullRequestsReferences"),
    }


def medium_answers(entry: dict[str, Any], pack: Pack) -> list[dict[str, Any]]:
    """The run's answers in a medium band, each with the question to answer instead."""
    found: list[dict[str, Any]] = []
    for qid in entry.get("uncertain_answers") or []:
        base, _, index = qid.rpartition("_")
        if qid in pack.questions or not index.isdigit():
            base, index = qid, ""
        answer = (entry.get("answers") or {}).get(qid) or {}
        question = pack.questions.get(base)
        item: dict[str, Any] = {"id": qid}
        if answer.get("type") == "choice":
            item["choice"] = answer.get("choice")
            item["confidence"] = answer.get("confidence")
            item["min_confidence"] = question.min_confidence if question else None
        else:
            item["value"] = answer.get("noul")
            item["no"], item["yes"] = (
                (question.no, question.yes) if question else (None, None)
            )
        if question is not None:
            wire = question.wire(int(index) if index else None)
            item["question"] = wire["instructions"]
        if index:
            item["comment"] = entry["comments"][int(index)]["url"]
        found.append(item)
    return found


def show_text(view: dict[str, Any]) -> str:
    lines = [
        f"#{view['number']} {view['title']}",
        view["url"],
        f"state: {view['state'].lower()}; labels: {', '.join(view['labels']) or 'none'}",
    ]
    triage = view["triage"]
    if triage is None:
        lines.append(f"run {view['run']}: not in this run")
    else:
        status = (
            f"stale: {triage['stale']} since the run"
            if triage["stale"]
            else "unchanged since the run"
        )
        lines.append(f"run {view['run']}: {triage['queue']}; {status}")
        lines += [f"  reason: {reason}" for reason in triage["reasons"]]
        lines += [f"  missing: {item}" for item in triage["missing"]]
        for answer in triage["medium_answers"]:
            if "value" in answer:
                value = (
                    f"{answer['value']} (medium band {answer['no']} to {answer['yes']})"
                )
            else:
                value = f"{answer['choice']} at {answer['confidence']} (needs {answer['min_confidence']})"
            question = f": {answer['question']}" if answer.get("question") else ""
            lines.append(f"  medium: {answer['id']} {value}{question}")
        if triage["fill"]:
            lines.append(f"  fill: {', '.join(triage['fill'])}")
        if triage["questions_changed"]:
            lines.append("  note: the questions changed since the run")
    kinds = {
        "parent": "parent",
        "sub_issues": "sub-issue",
        "blocked_by": "blocked by",
        "blocking": "blocking",
        "pull_requests": "pull request",
    }
    for key, kind in kinds.items():
        for link in view["links"][key]:
            source = ", named in the body" if link.get("source") == "body" else ""
            lines.append(
                f"{kind} #{link['number']} ({link['state'].lower()}{source}): {link['title']}"
            )
    lines += ["", "body:", view["body"] or "(empty)"]
    for index, comment in enumerate(view["comments"], 1):
        flags = [
            flag
            for flag, on in (
                ("minimized", comment["minimized"]),
                ("managed triage comment", comment["managed"]),
            )
            if on
        ]
        header = [f"comment {index}", comment["role"], comment["author"]]
        header += [comment["created_at"] or "", *flags]
        lines += ["", " · ".join(part for part in header if part), comment["url"]]
        lines.append(comment["body"])
    return "\n".join(lines)


def cmd_show(args: argparse.Namespace) -> tuple[str, Any]:
    """Print an issue's current thread and links, and what a run found about it."""
    _, record = load_run(args.run)
    repo, number = record["repo"], args.issue
    issue = fetch_issue(repo, number)
    if "/pull/" in str(issue.get("url") or ""):
        raise Failure(
            f"#{number} is a pull request; label-for-issues labels issues only"
        )
    author = login(issue.get("author"))
    body = str(issue.get("body") or "")
    comments = [
        {
            "author": login(c.get("author")),
            "role": "bot"
            if is_bot(login(c.get("author")))
            else comment_role(c, author),
            "created_at": c.get("createdAt"),
            "url": str(c.get("url") or ""),
            "minimized": bool(c.get("isMinimized")),
            "managed": MANAGED_MARKER in str(c.get("body") or ""),
            "body": str(c.get("body") or ""),
        }
        for c in issue.get("comments") or []
    ]
    entry = run_entry(record, number)
    triage = None
    if entry is not None:
        pack = load_pack()
        triage = {
            "queue": entry["queue"],
            "stale": stale_reason(repo, record["id"], entry, issue),
            "reasons": entry["reasons"],
            "missing": entry.get("missing") or [],
            "add": entry.get("add") or [],
            "remove": entry.get("remove") or [],
            "fill": entry.get("fill") or [],
            "medium_answers": medium_answers(entry, pack),
            "questions_changed": record.get("questions_digest") != pack.digest,
        }
    view = {
        "schema": SHOW_SCHEMA,
        "run": record["id"],
        "repo": repo,
        "number": number,
        "title": str(issue.get("title") or ""),
        "url": str(issue.get("url") or ""),
        "state": str(issue.get("state") or "").upper(),
        "updated_at": issue.get("updatedAt"),
        "author": author,
        "labels": sorted(label["name"] for label in issue.get("labels") or []),
        "triage": triage,
        "links": issue_links(repo, number, body),
        "body": body,
        "comments": comments,
    }
    return show_text(view), view


def set_problems(
    add: list[str], remove: list[str], reason: str, canonical: set[str]
) -> list[str]:
    """What makes a requested decision invalid before the issue is read."""
    named = unique(add + remove)
    problems = [] if named else ["name at least one --add or --remove label"]
    problems += [
        f"{label} is not a canonical label; label-for-issues owns the vocabulary"
        for label in named
        if label not in canonical
    ]
    problems += [
        f"{label} depends on parent links; set epic roles with label-for-issues"
        for label in named
        if label.startswith(EPIC_PREFIX)
    ]
    if WIP in add:
        problems.append(f"{WIP} marks started work, not a review decision")
    problems += [
        f"{label} is both added and removed" for label in add if label in remove
    ]
    for name, prefix in FAMILIES.items():
        same = [label for label in add if label.startswith(prefix)]
        if len(same) > 1:
            problems.append(f"add one {name} label at most, not {', '.join(same)}")
    if not reason:
        problems += [
            f"adding {label} needs --reason with {NEEDS_REASON[label]}"
            for label in add
            if label in NEEDS_REASON
        ]
    return problems


def cmd_set(args: argparse.Namespace) -> tuple[str, Any]:
    """Write the agent's review decision on one issue, rereading it first."""
    canonical = load_vocabulary()
    add, remove = unique(args.add or []), unique(args.remove or [])
    reason = (args.reason or "").strip()
    problems = set_problems(add, remove, reason, canonical)
    if problems:
        raise UsageError("; ".join(problems))
    path, record = load_run(args.run)
    repo, number, run_id = record["repo"], args.number, record["id"]
    entry = run_entry(record, number)
    if entry is None:
        raise Failure(
            f"#{number} is not in run {run_id}; run `jevlabel run -R {repo} --issue {number}` first"
        )
    if entry["queue"] == "skip":
        raise Failure(
            f"run {run_id} skipped #{number} ({entry['reasons'][0]}); "
            "set only decides issues the run asked Jev about"
        )
    result: dict[str, Any] = {
        "schema": SET_SCHEMA,
        "run": run_id,
        "repo": repo,
        "number": number,
        "created_at": now().isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "reason": reason,
        "added": [],
        "removed": [],
        "outcome": "",
        "detail": "",
    }

    def refuse(outcome: str, problem: str) -> NoReturn:
        result.update(outcome=outcome, detail=problem)
        raise Failure(f"#{number}: {outcome}: {problem}", result=result)

    current = issue_now(repo, number)
    stale = stale_reason(repo, run_id, entry, current)
    if stale:
        refuse(
            "stale",
            f"{stale} since run {run_id}; run `jevlabel run -R {repo} --issue {number}` "
            "again, then show and set it from the new run",
        )
    labels = {label["name"] for label in current.get("labels") or []}
    if EPIC_PARENT in labels and any(label.startswith(TYPE_PREFIX) for label in add):
        refuse("conflict", "it is an epic parent, which takes no type label")
    # Adding into a filled family replaces its canonical label; a custom one stays.
    replaced: list[str] = []
    for label in add:
        prefix = next((p for p in FAMILIES.values() if label.startswith(p)), None)
        for old in sorted(labels):
            if prefix is None or not old.startswith(prefix) or old == label:
                continue
            if old not in canonical:
                refuse(
                    "conflict",
                    f"its {old} label is not canonical; migrate it with the user before adding {label}",
                )
            replaced.append(old)
    added = [label for label in add if label not in labels]
    removed = unique([label for label in remove if label in labels] + replaced)
    result.update(added=added, removed=removed)
    if not added and not removed:
        result["outcome"] = "already"
        return f"set #{number}: nothing to change", result
    absent = [label for label in added if label not in repo_labels(repo)]
    if absent:
        refuse(
            "failed",
            f"{repo} lacks {', '.join(absent)}; create it with `jevlabel labels -R {repo}`",
        )
    verbs = (("add", "added", added), ("remove", "removed", removed))
    planned = " and ".join(
        f"{verb} {', '.join(names)}" for verb, _, names in verbs if names
    )
    done = " and ".join(
        f"{verb} {', '.join(names)}" for _, verb, names in verbs if names
    )
    if args.dry_run:
        result["outcome"] = "would-set"
        return f"set #{number} --dry-run: would {planned}; nothing written", result
    command = ["issue", "edit", str(number), "-R", repo]
    if added:
        command += ["--add-label", ",".join(added)]
    if removed:
        command += ["--remove-label", ",".join(removed)]
    log_path = new_log(path.parent, f"{run_id}.set-{number}-{stamp()}")
    try:
        gh(*command)
        after = {label["name"] for label in issue_now(repo, number).get("labels") or []}
    except Failure as failure:
        problems = [
            f"{failure.problems[0]}; reread it with `jevlabel show {run_id} --issue {number}` before retrying"
        ]
    else:
        problems = [
            f"{label} is missing after the write"
            for label in added
            if label not in after
        ]
        problems += [
            f"{label} is still set after the write"
            for label in removed
            if label in after
        ]
        problems += family_problems(after)
    result.update(outcome="failed" if problems else "set", detail="; ".join(problems))
    write_json(log_path, result)
    result["path"] = str(log_path)
    if problems:
        raise Failure(
            *(f"#{number}: {problem}" for problem in problems),
            f"the write is logged in {log_path}",
            result=result,
        )
    return f"set #{number}: {done}; log: {log_path}", result


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

    labels = commands.add_parser(
        "labels",
        help="create missing canonical labels",
        description="Create each canonical label that label-for-issues defines and the "
        "repository lacks, and fix the color or description of a label whose name "
        "matches exactly. Report case variants and near-duplicate labels, such as `bug` "
        "for 2-type:bug, with the issues that carry them; never rename, delete, or "
        "migrate one, since that needs the user's approval. Written labels are read "
        "back, and a log is kept. Exits 1 while a canonical label is blocked or failed.",
        epilog="examples:\n  jevlabel labels -R pascalandy/skills --dry-run\n"
        "  jevlabel labels -R pascalandy/skills\n"
        "  jevlabel labels -R pascalandy/skills --dry-run --json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    labels.add_argument(
        "-R", "--repo", type=repo_name, required=True, help="owner/repo"
    )
    labels.add_argument(
        "--dry-run", action="store_true", help="show what would change; write nothing"
    )
    common(labels)

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

    apply = commands.add_parser(
        "apply",
        help="label a run's routine issues and fill its review issues",
        description="Add the proposed labels of every routine issue in a run record, "
        "and the fill of every review issue: its judged type and p2, each only for an "
        "empty family, and none when its text may steer triage. "
        "Each issue is reread first: a changed or closed issue is stale and left alone, "
        "a label family that gained a label is a conflict, and labels are only added, "
        "never removed. After each write the labels are read back and checked. "
        "A review issue's other labels are left to the agent.",
        epilog="examples:\n  jevlabel apply last --dry-run\n  jevlabel apply last\n"
        "  jevlabel apply 20260927T120000Z-pascalandy-skills --issue 12",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    apply.add_argument("run", help="run ID, or `last`")
    apply.add_argument(
        "--issue", type=int, action="append", help="only this issue; repeatable"
    )
    apply.add_argument(
        "--dry-run", action="store_true", help="show what would be added"
    )
    common(apply)

    show = commands.add_parser(
        "show",
        help="print one issue of a run with its context",
        description="Print an issue's current state, labels, body, and comments with "
        "each author's role, and each linked issue or pull request with its state: "
        "parent, sub-issues, blockers from relationships and from `Blocked by` in the "
        "body, issues it blocks, and closing pull requests. For an issue in the run, "
        "also print the run's queue, reasons, missing items, fill, each medium-band "
        "answer with its question, and whether the issue changed since the run. "
        "Reads only; writes nothing.",
        epilog="examples:\n  jevlabel show last --issue 24\n"
        "  jevlabel show 20260928T025156Z-pascalandy-skills --issue 24 --json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    show.add_argument("run", help="run ID, or `last`")
    show.add_argument("--issue", type=int, required=True, help="issue number")
    common(show)

    set_ = commands.add_parser(
        "set",
        help="write the agent's review decision on one issue",
        description="Add and remove canonical labels on one issue that a run asked "
        "about. Adding a state, type, or priority replaces the canonical label its "
        "family holds. Adding 1-ready-for-agent, 1-ready-for-human, 1-wontfix, "
        "3-pty:p0, or 0-impediment needs --reason with the evidence label-for-issues "
        "asks for; the reason is logged, not posted. Epic roles and 1-wip-by-agent "
        "stay with label-for-issues. The issue is reread first and refused as stale "
        "when it changed or closed since the run, except for this run's own apply and "
        "set label writes. After the write, the labels are read back and the result "
        "is logged next to the run record.",
        epilog="examples:\n  jevlabel set last 24 --add 1-needs-triage --dry-run\n"
        "  jevlabel set last 24 --add 1-needs-triage\n"
        "  jevlabel set last 12 --add 2-type:task --remove 0-impediment\n"
        '  jevlabel set last 12 --add 1-ready-for-agent --reason "readiness review '
        '2026-09-28 by Claude: scope and criteria clear; no blockers"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    set_.add_argument("run", help="run ID, or `last`")
    set_.add_argument("number", type=int, help="issue number")
    set_.add_argument(
        "--add", action="append", metavar="LABEL", help="label to add; repeatable"
    )
    set_.add_argument(
        "--remove", action="append", metavar="LABEL", help="label to remove; repeatable"
    )
    set_.add_argument("--reason", help="the evidence behind the decision; logged")
    set_.add_argument(
        "--dry-run", action="store_true", help="show the change; write nothing"
    )
    common(set_)
    return parser


COMMANDS = {
    "doctor": cmd_doctor,
    "labels": cmd_labels,
    "consent": cmd_consent,
    "run": cmd_run,
    "compare": cmd_compare,
    "apply": cmd_apply,
    "show": cmd_show,
    "set": cmd_set,
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

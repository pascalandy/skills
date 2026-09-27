#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
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
PREVIEW_SCHEMA = "jevlabel.preview/v1"
DOCTOR_SCHEMA = "jevlabel.doctor/v1"
QUESTIONS_SCHEMA = "jevlabel.questions/v1"
EXIT_ERROR, EXIT_USAGE, EXIT_INTERRUPTED = 1, 2, 130

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
WIP = "1-wip-by-agent"
EPIC_PARENT = "4-epic:parent"
NEEDED_LABELS = (
    "0-impediment",
    "1-needs-info",
    "1-needs-triage",
    "1-ready-for-agent",
    "1-ready-for-human",
    WIP,
    "1-wontfix",
    "2-type:bug",
    "2-type:feature",
    "2-type:task",
    "3-pty:p0",
    "3-pty:p2",
    EPIC_PARENT,
)

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

examples:
  jevlabel doctor -R pascalandy/skills
  jevlabel run -R pascalandy/skills --dry-run
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
    return now().strftime("%Y%m%dT%H%M%SZ-") + re.sub(
        r"[^a-z0-9]+", "-", repo.lower()
    ).strip("-")


def cmd_run(args: argparse.Namespace) -> tuple[str, Any]:
    pack = load_pack()
    canonical = load_vocabulary()
    repo = args.repo
    if not args.dry_run:
        raise UsageError("live runs are not available yet; use --dry-run to preview")
    visibility = repo_visibility(repo)
    missing = sorted(canonical - repo_labels(repo))
    if missing:
        print(
            f"warning: {repo} lacks canonical labels {', '.join(missing)}; set them up with label-for-issues before apply",
            file=sys.stderr,
        )
    issues = fetch_issues(repo, args)
    prepared = prepare_all(issues, pack, args.max_requests)
    run_id = new_run_id(repo)
    asked = [item for item in prepared if item.request is not None]
    tokens = sum(item.tokens for item in asked)
    preview = {
        "schema": PREVIEW_SCHEMA,
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
        "estimated": {
            "requests": len(asked),
            "tokens": tokens,
            "cost_usd": cost_usd(tokens),
        },
        "issues": [{**item.summary(), "request": item.request} for item in prepared],
    }
    path = runs_dir() / f"{run_id}.preview.json"
    write_json(path, preview)
    line = (
        f"preview {run_id}: {len(prepared)} issues, {len(asked)} requests, "
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
        description="Fetch issues, build each issue's input, and ask Jev. "
        "--dry-run writes the exact request bodies to a preview file and sends nothing.",
        epilog="examples:\n  jevlabel run -R pascalandy/skills --dry-run\n"
        "  jevlabel run -R pascalandy/skills --issue 12 --issue 14 --dry-run",
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
    return parser


COMMANDS = {"doctor": cmd_doctor, "consent": cmd_consent, "run": cmd_run}


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

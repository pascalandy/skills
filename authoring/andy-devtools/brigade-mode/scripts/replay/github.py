"""GitHub facts the extractor reads, reduced to numbers, times and references.

`GitHub` reads them live through a `gh` reader the command supplies;
`Recorded` serves the facts a recording holds. Both answer through the same
methods. A page shows each fact DELAY seconds after GitHub had it, and
`at(time)` hides what a page could not show yet at that time.
"""

from __future__ import annotations

import json
import logging
import re
import shlex
import subprocess
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from t3 import norm

Ref = tuple[str, int]
PR_FIELDS = (
    "number createdAt mergedAt closedAt body "
    "closingIssuesReferences(first:100){nodes{number repository{nameWithOwner}}}"
)
ISSUE_FIELDS = (
    "title closedAt labels(first:10){nodes{name}} parent{number repository{nameWithOwner}} "
    "subIssues(first:100){totalCount nodes{number createdAt repository{nameWithOwner}}}"
)
ITEM_FIELDS = "__typename ... on PullRequest{mergedAt closedAt} ... on Issue{closedAt}"
# Seconds from a GitHub fact, such as a merge, to the page that shows it.
# The live service reads every open item sooner, so a page never shows a
# state that the full replay of the same run contradicts later (#852)
DELAY = 85.0
BODY_REF = re.compile(
    r"\b(?:closes|fixes|resolves|refs?|part of)\s+(?:([\w.-]+/[\w.-]+))?#(\d+)",
    re.IGNORECASE,
)


def delayed(time: str) -> str:
    """When a page shows a fact GitHub had at `time`, in norm()'s format."""
    shown = datetime.fromisoformat(time) + timedelta(seconds=DELAY)
    return (
        shown.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )


def key(ref: Ref) -> str:
    return f"{ref[0]}#{ref[1]}"


def unkey(text: str) -> Ref:
    repo, n = text.rsplit("#", 1)
    return repo, int(n)


def aliases(
    prs: Iterable[int] = (), issues: Iterable[int] = (), items: Iterable[int] = ()
) -> list[str]:
    """Query fields for one repository's PRs, issues and 🙋 items, each under its alias."""
    return (
        [f"p{n}: pullRequest(number:{n}){{{PR_FIELDS}}}" for n in prs]
        + [f"i{n}: issue(number:{n}){{{ISSUE_FIELDS}}}" for n in issues]
        + [f"x{n}: issueOrPullRequest(number:{n}){{{ITEM_FIELDS}}}" for n in items]
    )


def reduce_item(x: dict) -> dict:
    """An issue or a PR a 🙋 line names: when it merged or closed."""
    return {"merged": norm(x.get("mergedAt")), "closed": norm(x.get("closedAt"))}


def reduce_pr(repo: str, p: dict) -> dict:
    refs = [
        [c["repository"]["nameWithOwner"], c["number"]]
        for c in p["closingIssuesReferences"]["nodes"]
    ]
    refs += [
        [m.group(1) or repo, int(m.group(2))]
        for m in BODY_REF.finditer(p["body"] or "")
    ]
    unique = list(dict.fromkeys(tuple(r) for r in refs))
    return {
        "created": norm(p["createdAt"]),
        "merged": norm(p["mergedAt"]),
        "closed": norm(p["closedAt"]),
        "refs": [list(r) for r in unique],
    }


def reduce_issue(i: dict) -> dict:
    title = i["title"]
    m = re.match(r"\s*Epic\s+(\d+)", title)
    parent = i.get("parent")
    return {
        "epic": int(m.group(1)) if m else None,
        "epicTitle": title.lower().startswith("epic"),
        "epicLabel": "4-epic" in {x["name"] for x in i["labels"]["nodes"]},
        "closed": norm(i["closedAt"]),
        "parent": [parent["repository"]["nameWithOwner"], parent["number"]]
        if parent
        else None,
        "subCount": i["subIssues"]["totalCount"],
        "subs": [
            [s["repository"]["nameWithOwner"], s["number"], norm(s["createdAt"])]
            for s in i["subIssues"]["nodes"]
        ],
    }


class Facts:
    """Reduced facts by reference, and the questions the extractor asks of them."""

    def __init__(self) -> None:
        self.repositories: dict[str, dict] = {}  # any name -> {name, public}
        self.prs: dict[Ref, dict] = {}
        self.issues: dict[Ref, dict | None] = {}  # None: no such issue
        self.items: dict[Ref, dict | None] = {}
        self.now: str | None = None  # facts a page shows after this time are hidden
        self.known: str | None = None  # facts GitHub had after this time are hidden

    # -- what a subclass supplies
    def fetch_repository(self, name: str) -> dict:
        raise KeyError(name)

    def fetch_prs(self, refs: list[Ref]) -> None:
        raise KeyError(refs)

    def fetch_issue(self, ref: Ref) -> dict | None:
        raise KeyError(ref)

    def fetch_item(self, ref: Ref) -> dict | None:
        raise KeyError(ref)

    # -- time
    def at(self, now: str | None, known: str | None = None) -> Facts:
        """The facts as a page shows them at `now`; None shows everything.

        `known` also hides what GitHub had after it, as a reader whose last
        read of GitHub was then sees it.
        """
        self.now, self.known = now, known
        return self

    def seen(self, time: str | None) -> str | None:
        """When a page shows a fact GitHub had at `time`, or None before then."""
        if not time or (self.known is not None and time > self.known):
            return None
        shown = delayed(time)
        return shown if self.now is None or shown <= self.now else None

    # -- questions
    def repository(self, name: str) -> str:
        if name not in self.repositories:
            info = self.fetch_repository(name)
            self.repositories[name] = info
            self.repositories[info["name"]] = info
        return self.repositories[name]["name"]

    def public(self) -> set[str]:
        return {i["name"] for i in self.repositories.values() if i["public"]}

    def load_prs(self, refs: Iterable[Ref]) -> None:
        missing = sorted({r for r in refs if r not in self.prs})
        if missing:
            self.fetch_prs(missing)

    def pr(self, repo: str, n: int) -> dict | None:
        """A PR as of `now`, or None before it was opened."""
        p = self.prs[(repo, n)]
        created = self.seen(p["created"])
        if created is None:
            return None
        return {
            **p,
            "created": created,
            "merged": self.seen(p["merged"]),
            "closed": self.seen(p["closed"]),
        }

    def issue(self, repo: str, n: int) -> dict | None:
        """An issue as of `now`, or None when the number names no issue, such as
        a bare `#720` that a batch name meant for another repository."""
        if (repo, n) not in self.issues:
            self.issues[(repo, n)] = self.fetch_issue((repo, n))
        i = self.issues[(repo, n)]
        if i is None:
            return None
        return {
            **i,
            "closed": self.seen(i["closed"]),
            "subs": [[r, x, shown] for r, x, c in i["subs"] if (shown := self.seen(c))],
        }

    def item(self, repo: str, n: int) -> dict | None:
        """An issue or a PR by number, for a 🙋 line's reference."""
        if (repo, n) not in self.items:
            self.items[(repo, n)] = self.fetch_item((repo, n))
        x = self.items[(repo, n)]
        if x is None:
            return None
        return {
            "merged": self.seen(x.get("merged")),
            "closed": self.seen(x.get("closed")),
        }

    def is_epic(self, repo: str, n: int) -> bool:
        i = self.issue(repo, n)
        return bool(i and (i["epicLabel"] or (i["subCount"] > 0 and i["epicTitle"])))

    def epic_number(self, repo: str, n: int) -> int | None:
        i = self.issue(repo, n)
        return i["epic"] if i else None

    def subissues(self, repo: str, n: int) -> list[dict]:
        i = self.issue(repo, n)
        return sorted(
            (
                {"repository": {"nameWithOwner": r}, "number": x, "createdAt": c}
                for r, x, c in (i["subs"] if i else [])
            ),
            key=lambda s: s["number"],
        )

    def stories_of(self, p: dict) -> list[Ref]:
        """Issues a PR closes or names; an Epic is not a Story."""
        return [(r, n) for r, n in p["refs"] if not self.is_epic(r, n)]

    def epic_ref(self, p: dict) -> Ref | None:
        for r, n in p["refs"]:
            if self.is_epic(r, n):
                return r, n
        return None

    def epic_of(self, repo: str, n: int) -> Ref | None:
        i = self.issue(repo, n)
        par = i["parent"] if i else None
        return (par[0], par[1]) if par else None

    def restore(self, data: dict[str, Any]) -> None:
        """Take the facts of a `dump()`, such as a recording's."""
        for name, info in data.get("repositories", {}).items():
            self.repositories[name] = {"name": name, "public": info["public"]}
        self.prs = {unkey(k): v for k, v in data.get("prs", {}).items()}
        self.issues = {unkey(k): v for k, v in data.get("issues", {}).items()}
        self.items = {unkey(k): v for k, v in data.get("items", {}).items()}

    def dump(self) -> dict:
        """The facts a recording holds, keyed by `repo#n`."""
        return {
            "repositories": {
                info["name"]: {"public": info["public"]}
                for info in self.repositories.values()
            },
            "prs": {key(r): p for r, p in sorted(self.prs.items())},
            "issues": {key(r): i for r, i in sorted(self.issues.items())},
            "items": {key(r): x for r, x in sorted(self.items.items())},
        }


class GitHub(Facts):
    """Facts read live through `read`, which runs one `gh` command and returns its JSON."""

    def __init__(self, read: Callable[[list[str]], dict]) -> None:
        super().__init__()
        self.read = read

    def fetch_repository(self, name: str) -> dict:
        info = self.read(["repo", "view", name, "--json", "nameWithOwner,visibility"])
        return {
            "name": info["nameWithOwner"],
            "public": info.get("visibility") == "PUBLIC",
        }

    def repo_query(self, repo: str, body: str, missing_ok: bool = False) -> dict:
        owner, name = self.repository(repo).split("/", 1)
        result = self.gql(
            f"query{{repository(owner:{json.dumps(owner)},name:{json.dumps(name)}){{{body}}}}}",
            missing_ok,
        )
        if not result.get("repository"):
            raise ValueError(f"GitHub returned no repository for {repo}")
        return result["repository"]

    def gql(self, query: str, missing_ok: bool = False) -> dict:
        result = self.read(["api", "graphql", "-f", f"query={query}"])
        if result.get("errors") and not (
            missing_ok
            and all(error.get("type") == "NOT_FOUND" for error in result["errors"])
        ):
            raise ValueError(
                "GitHub GraphQL: " + "; ".join(e["message"] for e in result["errors"])
            )
        return result["data"]

    def fetch_prs(self, refs: list[Ref]) -> None:
        by_repo: dict[str, list[int]] = defaultdict(list)
        for repo, n in refs:
            by_repo[repo].append(n)
        for repo, ns in sorted(by_repo.items()):
            body = " ".join(aliases(prs=sorted(ns)))
            for v in self.repo_query(repo, body).values():
                self.prs[(repo, v["number"])] = reduce_pr(repo, v)

    def fetch_issue(self, ref: Ref) -> dict | None:
        d = self.repo_query(
            ref[0], f"issue(number:{ref[1]}){{{ISSUE_FIELDS}}}", missing_ok=True
        )
        return reduce_issue(d["issue"]) if d.get("issue") else None

    def fetch_item(self, ref: Ref) -> dict | None:
        x = self.repo_query(
            ref[0],
            f"issueOrPullRequest(number:{ref[1]}){{{ITEM_FIELDS}}}",
            missing_ok=True,
        )["issueOrPullRequest"]
        return reduce_item(x) if x else None


class Cached(GitHub):
    """Live facts for the dashboard: a merged or closed item stays cached forever,
    and `refresh` re-reads the open ones, one query per repository.

    `path` keeps the cache across restarts, so a new version of the service
    starts from it instead of reading every PR and issue again.
    """

    def __init__(
        self, read: Callable[[list[str]], dict], path: Path | None = None
    ) -> None:
        super().__init__(read)
        self.path, self.saved = path, ""
        if path and path.is_file():
            try:
                self.saved = path.read_text(encoding="utf-8")
                self.restore(json.loads(self.saved))
            except (OSError, ValueError, KeyError):
                self.prs, self.issues, self.items, self.saved = {}, {}, {}, ""

    def save(self) -> None:
        """Write the cache when it changed, atomically."""
        if not self.path:
            return
        text = json.dumps(self.dump(), separators=(",", ":"))
        if text == self.saved:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self.path)
        self.saved = text

    def open_refs(self) -> dict[str, list[str]]:
        """Each repository's open PRs, issues and 🙋 items, as query aliases."""
        wanted: dict[str, list[str]] = defaultdict(list)
        for (repo, n), p in self.prs.items():
            if not (p["merged"] or p["closed"]):
                wanted[repo] += aliases(prs=[n])
        for (repo, n), i in self.issues.items():
            if i and not i["closed"]:
                wanted[repo] += aliases(issues=[n])
        for (repo, n), x in self.items.items():
            if x and not (x["merged"] or x["closed"]):
                wanted[repo] += aliases(items=[n])
        return dict(wanted)

    def refresh(self, repos: Iterable[str] | None = None) -> int:
        """Re-read the open items of `repos`, or of every repository; return the query count."""
        only = None if repos is None else set(repos)
        queries = 0
        for repo, aliases in sorted(self.open_refs().items()):
            if only is not None and repo not in only:
                continue
            found = self.repo_query(repo, " ".join(aliases), missing_ok=True)
            queries += 1
            for alias, v in found.items():
                n = int(alias[1:])
                if alias[0] == "p" and v:
                    self.prs[(repo, n)] = reduce_pr(repo, v)
                elif alias[0] == "i":
                    self.issues[(repo, n)] = reduce_issue(v) if v else None
                elif alias[0] == "x":
                    self.items[(repo, n)] = reduce_item(v) if v else None
        return queries


class Recorded(Facts):
    """Facts from a recording; asking for one it lacks is a recording bug."""

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__()
        self.restore(data)

    def fetch_repository(self, name: str) -> dict:
        raise KeyError(f"recording has no repository {name}")

    def fetch_prs(self, refs: list[Ref]) -> None:
        raise KeyError(f"recording has no PR {', '.join(map(key, refs))}")

    def fetch_issue(self, ref: Ref) -> dict | None:
        raise KeyError(f"recording has no issue {key(ref)}")

    def fetch_item(self, ref: Ref) -> dict | None:
        raise KeyError(f"recording has no item {key(ref)}")


class ReadError(Exception):
    """A `gh` read failed; `temporary` says whether a retry may fix it, and
    `detail` holds gh's own words, for a page that has no command to rerun."""

    def __init__(
        self, message: str, temporary: bool = False, detail: str | None = None
    ) -> None:
        super().__init__(message)
        self.temporary = temporary
        self.detail = detail or message


def gh_reader(timeout: float) -> Callable[[list[str]], dict]:
    """A reader that runs one read-only `gh` command and returns its JSON."""

    def read(args: list[str]) -> dict:
        try:
            done = subprocess.run(
                ["gh", *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as error:
            raise ReadError(
                "gh is missing; install it from https://cli.github.com and run 'gh auth login'"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise ReadError(
                "GitHub timed out; retry with a larger --timeout", temporary=True
            ) from error
        if done.returncode:
            try:
                partial = json.loads(done.stdout)
            except ValueError:
                partial = {}
            if "data" in partial and partial.get("errors"):
                return partial
            message = done.stderr.strip()
            logging.getLogger(__name__).debug("gh %s: %s", shlex.join(args), message)
            temporary = bool(
                re.search(
                    r"timeout|timed out|connection|TLS handshake|HTTP 5\d\d|rate limit",
                    message,
                    re.IGNORECASE,
                )
            )
            raise ReadError(
                f"GitHub read failed: {message}; run 'gh auth status', then rerun this command",
                temporary=temporary,
                detail=message,
            )
        return json.loads(done.stdout)

    return read

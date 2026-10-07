#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Merge this branch's PR into main: sign off its pushed head, squash-merge that commit, then deploy.

Run it on the PR branch, pushed, with a clean working tree. It reuses a green
signoff on the head, or runs the just signoff steps first. It merges only when
the branch contains main's tip, so the tree that lands is the tree the checks
ran on, and fails when another PR lands in the same seconds. Then, when main
holds the tree the checks ran on, it runs just deploy, which brings every fleet
machine to the new main. A rerun after an interruption finds the merged PR and
deploys again.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

from _cli import Parser, ScriptError, TemporaryError, duration, exit_codes
from _common import changes_in, main_checkout, replay, run, run_git, run_script
from signoff import (
    ROOT,
    branch,
    check_and_sign,
    gh,
    git,
    is_ancestor,
    pushed_head,
    remote_tip,
    require_clean_tree,
    signed_off,
)

EPILOG = """\
A run answers {"ok":true,"changes":[...]}: ["signoff", SHA] when it signs off
the head, ["merge", "#N", SHA] for the commit it merges, then the changes of
just deploy. A dry run answers what a run would do. When the merge lands but the
deploy fails or is withheld, the run fails and says so; a rerun of just merge
then only deploys.

examples:
  just merge             # sign off this branch's PR head, then merge it
  just merge --dry-run   # check that the PR can merge, without changing anything"""
EXIT_CODES = exit_codes(
    {
        0: "the PR is merged and deployed",
        1: "the PR cannot merge as it is, a check failed, or the merge landed but "
        "the deploy failed; the error says why",
        75: "GitHub did not make the PR mergeable in time, or the network failed; retry",
    }
)
FIELDS = (
    "number,url,title,state,isDraft,baseRefName,headRefOid,mergeStateStatus,mergeCommit"
)
# What each merge state other than CLEAN needs before GitHub merges without a
# bypass
BLOCKERS = {
    "BLOCKED": "is blocked by a required status or review",
    "DIRTY": "conflicts with main; run: git merge origin/main, resolve, git push, "
    "then just merge",
    "DRAFT": "is a draft; run: gh pr ready {number}, then just merge",
    "UNKNOWN": "has a merge state GitHub has not computed yet",
    "UNSTABLE": "has a failing check; read it with: gh pr checks {number}",
}
# Each of these needs a person, so the wait stops at once instead of running out
FINAL = {"DIRTY", "DRAFT", "UNSTABLE"}
POLL_SECONDS = 2
log = logging.getLogger("merge")


@dataclass(frozen=True)
class PullRequest:
    number: int
    url: str
    title: str
    state: str
    draft: bool
    base: str
    head: str
    merge_state: str
    merge_commit: str

    @classmethod
    def parse(cls, raw: dict) -> PullRequest:
        return cls(
            number=raw["number"],
            url=raw["url"],
            title=raw["title"],
            state=raw["state"],
            draft=raw["isDraft"],
            base=raw["baseRefName"],
            head=raw["headRefOid"],
            merge_state=raw["mergeStateStatus"],
            merge_commit=(raw.get("mergeCommit") or {}).get("oid", ""),
        )


def view(number: int, timeout: float) -> PullRequest:
    shown = gh("pr", "view", str(number), "--json", FIELDS, timeout=timeout)
    return PullRequest.parse(json.loads(shown))


def branch_pr(name: str, timeout: float) -> PullRequest:
    """The branch's open PR, or else its latest merged one."""
    listed = gh(
        "pr",
        "list",
        "--head",
        name,
        "--state",
        "all",
        "--json",
        FIELDS,
        timeout=timeout,
    )
    prs = [PullRequest.parse(raw) for raw in json.loads(listed)]
    open_prs = [pr for pr in prs if pr.state == "OPEN"]
    if len(open_prs) > 1:
        numbers = ", ".join(f"#{pr.number}" for pr in open_prs)
        raise ScriptError(
            f"{name} has several open PRs ({numbers}); close all but one, "
            "then rerun just merge"
        )
    merged = [pr for pr in prs if pr.state == "MERGED"]
    if not open_prs and not merged:
        raise ScriptError(
            f"{name} has no open PR; open one with: gh pr create --base main"
        )
    return (open_prs or merged)[0]


def require_mergeable_as_is(pr: PullRequest) -> None:
    if pr.draft:
        raise ScriptError(
            f"PR #{pr.number} " + BLOCKERS["DRAFT"].format(number=pr.number)
        )
    if pr.base != "main":
        raise ScriptError(
            f"PR #{pr.number} targets {pr.base}, not main; land a stack with: "
            "gh stack merge <stack> --yes --squash"
        )


def require_contains_main(sha: str, timeout: float) -> None:
    """Refuse `sha` unless it contains main's tip, so the squash lands its tree."""
    main = remote_tip("main", timeout)
    if not is_ancestor(main, sha):
        raise ScriptError(
            f"the branch at {sha[:7]} does not contain main's tip {main[:7]}; "
            "run: git merge origin/main, git push, then just merge"
        )


def wait_until_mergeable(number: int, sha: str, timeout: float) -> None:
    """Wait for GitHub to count the signoff, until it can merge `sha`."""
    deadline = time.monotonic() + timeout
    while True:
        pr = view(number, timeout)
        if pr.state != "OPEN":
            raise ScriptError(
                f"PR #{number} was {pr.state.lower()} before the merge; "
                "rerun just merge to see where it stands"
            )
        if pr.base != "main":
            raise ScriptError(
                f"PR #{number} now targets {pr.base}, not main; nothing was merged"
            )
        if pr.head != sha:
            raise ScriptError(
                f"PR #{number} moved from {sha[:7]} to {pr.head[:7]}; "
                "rerun just merge to check the new head"
            )
        if pr.merge_state == "CLEAN":
            return
        need = BLOCKERS.get(pr.merge_state, f"has merge state {pr.merge_state}")
        blocker = f"PR #{number} {need.format(number=number)}: {pr.url}"
        if pr.merge_state in FINAL:
            raise ScriptError(blocker)
        if time.monotonic() >= deadline:
            raise TemporaryError(f"after {timeout:g}s, {blocker}")
        time.sleep(max(0.0, min(POLL_SECONDS, deadline - time.monotonic())))


def land(pr: PullRequest, sha: str, timeout: float) -> None:
    """Squash-merge `sha`, then read the PR back: a failed call can still have merged it."""
    failure = ScriptError("gh pr merge did not merge it")
    try:
        gh(
            "pr",
            "merge",
            str(pr.number),
            "--squash",
            "--match-head-commit",
            sha,
            "--subject",
            f"{pr.title} (#{pr.number})",
            timeout=timeout,
        )
    except ScriptError as error:
        failure = error
    merged = view(pr.number, timeout)
    if merged.state != "MERGED":
        # Keep the failure's class, so a network failure stays retryable
        raise type(failure)(
            f"{failure}; PR #{pr.number} is still {merged.state.lower()}, "
            "so nothing was merged"
        )
    # --match-head-commit pins the head, not the base
    if merged.base != "main":
        raise ScriptError(f"PR #{pr.number} was merged into {merged.base}, not main")
    if merged.head != sha:
        raise ScriptError(
            f"PR #{pr.number} was merged at {merged.head[:7]}, not at the tested "
            f"{sha[:7]}; check main"
        )


def deploy(sha: str, args: argparse.Namespace) -> list[list[str]]:
    """Run just deploy from the main checkout once main holds the tree the checks
    ran on `sha`, and return its changes. The merge already landed, so a deploy
    that cannot run or misses a machine fails with what to do, and a rerun of
    just merge only deploys."""
    landed = "the merge landed, but"
    try:
        main = remote_tip("main", args.timeout)
        tested = git("rev-parse", f"{main}^{{tree}}") == git(
            "rev-parse", f"{sha}^{{tree}}"
        )
        checkout = main_checkout(ROOT)
        # The deploy runs this checkout's code, which must be code main has held
        held = run_git(
            "merge-base", "--is-ancestor", "HEAD", "origin/main", cwd=checkout
        )
        changed = run_git(
            "status", "--porcelain", "--", "scripts", "justfile", cwd=checkout
        )
    except ScriptError as error:
        raise ScriptError(
            f"{landed} just deploy could not run: {error}; fix it, then run just deploy"
        ) from None
    if not tested:
        # Another PR landed in the seconds around the merge
        raise ScriptError(
            f"{landed} main at {main[:7]} holds a tree the checks did not run on, "
            "so it was not deployed; run just check on an up-to-date main, then "
            "just deploy"
        )
    if held.returncode or changed.returncode or changed.stdout.strip():
        raise ScriptError(
            f"{landed} it was not deployed: {checkout} must hold a commit of main, "
            "with no changes under scripts/ or the justfile; fix it, then run "
            "just deploy there"
        )
    levels = [
        *(["--verbose"] if args.verbose else []),
        *(["--debug"] if log.isEnabledFor(logging.DEBUG) else []),
    ]
    log.info("run just deploy from %s", checkout)
    deployed = run(
        (sys.executable, str(checkout / "scripts/sync_fleet.py"), *levels),
        cwd=checkout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    replay(deployed.stderr)
    # A failed deploy still lists the machines it reached, in its answer or,
    # from a sync-fleet older than #490, in its change lines
    changes = changes_in((deployed.stdout + deployed.stderr).splitlines())
    if deployed.returncode:
        raise ScriptError(
            f"{landed} just deploy did not reach every machine; fix what its "
            "answer above says, then run just deploy",
            report={"changes": changes},
        )
    return changes


def merge(args: argparse.Namespace) -> dict[str, Any]:
    name = branch()
    pr = branch_pr(name, args.timeout)
    if pr.state == "MERGED":
        # A stack layer keeps its lower layer as base after gh stack merge lands
        # it on main, so its merge commit decides (#266)
        if pr.base != "main" and not (
            pr.merge_commit
            and is_ancestor(pr.merge_commit, remote_tip("main", args.timeout))
        ):
            raise ScriptError(f"PR #{pr.number} was merged into {pr.base}, not main")
        head = git("rev-parse", "HEAD")
        if pr.head != head:
            raise ScriptError(
                f"PR #{pr.number} was merged at {pr.head[:7]}, but HEAD is "
                f"{head[:7]}; open a new PR for the new commits"
            )
        log.info("PR #%d is already merged: %s", pr.number, pr.url)
        deployed = [] if args.dry_run else deploy(pr.head, args)
        return {"changes": deployed} if deployed else {}
    require_mergeable_as_is(pr)
    require_clean_tree()
    sha = pushed_head(args.timeout)
    if sha != pr.head:
        raise ScriptError(
            f"PR #{pr.number} is at {pr.head[:7]}, but {name} on GitHub is at "
            f"{sha[:7]}; rerun just merge once GitHub catches up"
        )
    require_contains_main(sha, args.timeout)
    changes = []
    try:
        if not signed_off(sha, args.timeout):
            if not args.dry_run:
                check_and_sign(sha, args.timeout)
            changes.append(["signoff", sha[:7]])
        if args.dry_run:
            return {"changes": [*changes, ["merge", f"#{pr.number}", sha[:7]]]}
        wait_until_mergeable(pr.number, sha, args.timeout)
        # main can move while the checks run
        require_contains_main(sha, args.timeout)
        land(pr, sha, args.timeout)
        changes.append(["merge", f"#{pr.number}", sha[:7]])
        deployed = deploy(sha, args)
    except ScriptError as error:
        reached = error.report.get("changes", [])
        if changes or reached:
            error.report["changes"] = [*changes, *reached]
        raise
    return {"changes": [*changes, *deployed]}


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just merge",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="check that the PR can merge and print what a run would do, "
        "without running the checks",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default="1m",
        help="how long each call to GitHub, and the wait for GitHub to accept "
        "the merge, may take (default: 1m)",
    )
    return run_script(parser, merge, argv, debug="MERGE_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

"""A throwaway GitHub for the tests of just signoff and just merge: a bare
origin, a pushed checkout, and a fake gh.

Run as a program, this file is gh. It answers from the JSON state that
FAKE_GITHUB names: the commit statuses, the pull requests, whose open heads
follow their branch in the bare origin, and one-shot hooks that change GitHub
mid-run or fail a call.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
IDENTITY = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
CHECK = """\
import os, subprocess, sys

tree = subprocess.run(
    ["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True
)
with open(os.environ["FAKE_CHECKS"], "a") as log:
    log.write(tree.stdout)
if hook := os.environ.get("FAKE_CHECK_HOOK"):
    subprocess.run(hook, shell=True, check=True)
sys.exit(int(os.environ.get("FAKE_CHECK_EXIT", "0")))
"""


class Sandbox:
    """`main` is the main checkout, on main; `work` is a worktree of it with
    `feature` checked out and pushed, one commit ahead of main."""

    def __init__(self, root: Path, *scripts: str) -> None:
        self.origin = root / "origin.git"
        self.elsewhere = root / "elsewhere"
        self.main = root / "main"
        self.work = root / "work"
        self.state_path = root / "github.json"
        self.checks_log = root / "checks.log"
        fakes = root / "bin"
        fakes.mkdir()
        gh = fakes / "gh"
        gh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{__file__}" "$@"\n')
        gh.chmod(0o755)
        # A leftover GIT_DIR, as in a git hook, would point every git call at the real repo
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("GIT_", "GH_"))
        } | {
            **IDENTITY,
            "HOME": str(root),
            "GIT_CONFIG_NOSYSTEM": "1",
            "PATH": f"{fakes}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GITHUB": str(self.state_path),
            "FAKE_CHECKS": str(self.checks_log),
        }
        self.save({"origin": str(self.origin), "statuses": {}, "prs": [], "hooks": {}})
        scripts_dir = self.main / "scripts"
        scripts_dir.mkdir(parents=True)
        for name in ("_cli.py", "_common.py", *scripts):
            shutil.copy2(SCRIPTS / name, scripts_dir / name)
        (scripts_dir / "check.py").write_text(CHECK)
        (self.main / ".gitignore").write_text("__pycache__/\n")
        self.git("init", "-q", "-b", "main", cwd=self.main)
        self.git("add", "-A", cwd=self.main)
        self.git("commit", "-qm", "seed", cwd=self.main)
        self.git("clone", "-q", "--bare", str(self.main), str(self.origin), cwd=root)
        self.git("remote", "add", "origin", str(self.origin), cwd=self.main)
        self.git("fetch", "-q", "origin", cwd=self.main)
        self.git(
            "worktree", "add", "-q", "-b", "feature", str(self.work), cwd=self.main
        )
        self.commit("feature")
        self.git("push", "-q", "-u", "origin", "feature")
        self.git("clone", "-q", str(self.origin), str(self.elsewhere), cwd=root)

    def git(self, *args: str, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.work,
            env=self.env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def push_elsewhere(self, branch: str, name: str) -> str:
        """A shell command that commits the file `name` to `branch` in another
        clone and pushes it, as a second machine would."""
        other = shlex.quote(str(self.elsewhere))
        return (
            f"git -C {other} fetch -q origin"
            f" && git -C {other} switch -q -C {branch} origin/{branch}"
            f" && echo {name} > {other}/{name} && git -C {other} add {name}"
            f" && git -C {other} commit -qm {name} && git -C {other} push -q origin {branch}"
        )

    def sh(self, command: str) -> None:
        subprocess.run(command, shell=True, cwd=self.work, env=self.env, check=True)

    def commit(self, name: str) -> str:
        """Commit a new file called `name`; return the commit."""
        (self.work / name).write_text(f"{name}\n")
        self.git("add", name)
        self.git("commit", "-qm", f"add {name}")
        return self.git("rev-parse", "HEAD")

    def run(
        self, script: str, *args: str, **env: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.work / "scripts" / script), *args],
            cwd=self.work,
            env=self.env | env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def state(self) -> dict:
        return json.loads(self.state_path.read_text())

    def save(self, state: dict) -> None:
        self.state_path.write_text(json.dumps(state))

    def statuses(self) -> dict[str, str]:
        return self.state()["statuses"]

    def hook(self, key: str, command: str) -> None:
        """Run the shell `command` once, before the first gh call that starts
        with `key`; when it fails, that call fails with its stderr."""
        state = self.state()
        state["hooks"][key] = command
        self.save(state)

    def sign(self, sha: str) -> None:
        state = self.state()
        state["statuses"][sha] = "success"
        self.save(state)

    def open_pr(self, **fields: object) -> None:
        """Open PR #7 from feature into main; `fields` override gh's JSON fields."""
        state = self.state()
        state["prs"].append(
            {
                "number": 7,
                "title": "✨ feat: add feature",
                "state": "OPEN",
                "isDraft": False,
                "baseRefName": "main",
                "headRefName": "feature",
                "headRefOid": "",
                **fields,
            }
        )
        self.save(state)

    def main_subject(self) -> str:
        return self.git(
            "--git-dir", str(self.origin), "log", "-1", "--format=%s", "main"
        )

    def checks_run(self) -> int:
        return len(self.checked())

    def checked(self) -> list[str]:
        """The tree each run of the checks saw, in order."""
        if not self.checks_log.exists():
            return []
        return self.checks_log.read_text().splitlines()


def origin(state: dict, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "--git-dir", state["origin"], *args],
        capture_output=True,
        text=True,
        check=False,
    )


def squash_tree(state: dict, base: str, head: str) -> str | None:
    """The tree a squash of `head` onto `base` lands, or None on a conflict."""
    merged = origin(state, "merge-tree", "--write-tree", base, head)
    return merged.stdout.split()[0] if merged.returncode == 0 else None


def pull_request(state: dict, number: str) -> dict:
    """The PR as gh pr view --json prints it; an open PR's head follows its branch."""
    pr = next(pr for pr in state["prs"] if str(pr["number"]) == number)
    status = "UNKNOWN"
    if pr["state"] == "OPEN":
        head = origin(state, "rev-parse", f"refs/heads/{pr['headRefName']}")
        pr["headRefOid"] = head.stdout.strip()
        if pr["isDraft"]:
            status = "DRAFT"
        elif squash_tree(state, pr["baseRefName"], pr["headRefOid"]) is None:
            status = "DIRTY"
        elif state["statuses"].get(pr["headRefOid"]) != "success":
            status = "BLOCKED"
        else:
            status = "CLEAN"
    url = f"https://github.com/pascalandy/skills/pull/{number}"
    return {**pr, "url": url, "mergeStateStatus": status}


def merge(state: dict, number: str, sha: str, subject: str) -> tuple[int, str]:
    pr = pull_request(state, number)
    if pr["headRefOid"] != sha:
        return 1, "Head branch was modified. Review and try the merge again."
    if pr["mergeStateStatus"] != "CLEAN":
        return 1, "the base branch policy prohibits the merge"
    base = origin(state, "rev-parse", pr["baseRefName"]).stdout.strip()
    tree = squash_tree(state, base, sha) or ""
    commit = origin(state, "commit-tree", tree, "-p", base, "-m", subject)
    origin(
        state, "update-ref", f"refs/heads/{pr['baseRefName']}", commit.stdout.strip()
    )
    stored = next(pr for pr in state["prs"] if str(pr["number"]) == number)
    stored["state"] = "MERGED"
    return 0, ""


def gh(state: dict, args: list[str]) -> tuple[int, str]:
    """Answer one gh call; return its exit code and output."""

    def option(name: str) -> str:
        return args[args.index(name) + 1]

    # A hook runs once, before the first call its key starts; a failing hook
    # fails that call with its stderr, as a lost connection would
    for key in [key for key in state["hooks"] if " ".join(args).startswith(key)]:
        hooked = subprocess.run(
            state["hooks"].pop(key),
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
        if hooked.returncode:
            return hooked.returncode, hooked.stderr.strip()
    if args[0] == "api":
        sha = re.fullmatch(r"repos/\{owner\}/\{repo\}/commits/(\w+)/status", args[1])
        assert sha, args
        state_of = state["statuses"].get(sha[1])
        statuses = [{"context": "signoff", "state": state_of}] if state_of else []
        return 0, json.dumps({"statuses": statuses})
    if args[0] == "signoff":
        sha = option("--commit")
        if not origin(state, "for-each-ref", "--contains", sha).stdout.strip():
            return 1, f"{sha} is not on a remote"
        state["statuses"][sha] = "success"
        return 0, f"✓ Signed off on {sha[:7]}"
    if args[:2] == ["pr", "list"]:
        head = option("--head")
        prs = [pr for pr in reversed(state["prs"]) if pr["headRefName"] == head]
        return 0, json.dumps([pull_request(state, str(pr["number"])) for pr in prs])
    if args[:2] == ["pr", "view"]:
        return 0, json.dumps(pull_request(state, args[2]))
    if args[:2] == ["pr", "merge"] and "--squash" in args:
        return merge(state, args[2], option("--match-head-commit"), option("--subject"))
    return 1, f"fake gh cannot answer: gh {' '.join(args)}"


def main() -> int:
    path = Path(os.environ["FAKE_GITHUB"])
    state = json.loads(path.read_text())
    code, output = gh(state, sys.argv[1:])
    path.write_text(json.dumps(state))
    print(output, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

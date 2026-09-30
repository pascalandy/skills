"""A repository-owned, reusable detached checkout for published deployment code.

The authoring checkout is only a Git object source. The common directory owns
both the detached checkout and its lock; neither lives in the private clone.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from _cli import ScriptError
from _common import exclusive, run_git


def git(root: Path, *args: str) -> str:
    result = run_git(*args, cwd=root)
    if result.returncode:
        raise ScriptError(
            f"git {args[0]} failed: {result.stderr.strip()}; fix the published checkout, then rerun"
        )
    return result.stdout.strip()


def author_root(root: Path) -> Path:
    """The original checkout owns private edits, not disposable linked worktrees."""
    first = git(root, "worktree", "list", "--porcelain", "-z").split("\0", 1)[0]
    return Path(first.removeprefix("worktree ")).resolve()


@contextmanager
def published(root: Path, revision: str, timeout: float) -> Iterator[Path]:
    """Pin a published revision without touching the authoring worktree.

    A later request for an ancestor cannot replace a newer cached checkout.
    The lock remains held while the caller reads/installs from the checkout.
    """
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    checkout = common / "published-deployment"
    with exclusive(common / "published-deployment.lock", timeout):
        sha = git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
        registered = git(root, "worktree", "list", "--porcelain")
        paths = {
            line.removeprefix("worktree ")
            for line in registered.splitlines()
            if line.startswith("worktree ")
        }
        if checkout.exists() or checkout.is_symlink():
            if str(checkout) not in paths or checkout.is_symlink():
                raise ScriptError(
                    f"{checkout} is not the owned worktree; move it aside, then rerun"
                )
            current = git(checkout, "rev-parse", "HEAD")
            if git(checkout, "status", "--porcelain"):
                raise ScriptError(
                    f"published worktree {checkout} has edits; inspect them, then rerun"
                )
            if (
                run_git(
                    "merge-base", "--is-ancestor", sha, current, cwd=root
                ).returncode
                == 0
            ):
                sha = current
            elif run_git(
                "merge-base", "--is-ancestor", current, sha, cwd=root
            ).returncode:
                raise ScriptError(
                    f"published revision {sha} diverges from {current}; "
                    "restore a forward main history, or get approval to replace "
                    f"the owned worktree at {checkout}"
                )
            if current != sha:
                git(
                    checkout,
                    "-c",
                    "core.hooksPath=/dev/null",
                    "switch",
                    "--detach",
                    "--quiet",
                    sha,
                )
        else:
            if str(checkout) in paths:
                # Git still owns this exact disposable path after an interrupted
                # creation or external deletion. Remove only its registration.
                git(root, "worktree", "remove", "--force", str(checkout))
            git(
                root,
                "-c",
                "core.hooksPath=/dev/null",
                "worktree",
                "add",
                "--quiet",
                "--detach",
                str(checkout),
                sha,
            )
        yield checkout

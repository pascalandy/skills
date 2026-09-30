#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the CI verdict: the checks in CHECKS, in order; success prints nothing."""

from __future__ import annotations

import argparse
import logging
import shlex
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes
from _common import run, run_git, run_script

ROOT = Path(__file__).resolve().parent.parent

EPILOG = """\
Each check is one row of CHECKS in scripts/check.py; add a row to add a check.
A check that names a path under authoring/ runs only when this branch, compared
with origin/main, or the working tree changes that skill, or scripts/check.py.
A failing check does not stop the others; its output is replayed on stderr.

examples:
  just check
  just check --sweep
  just check --list
  just check --only lint --only tavily
  just check --only test-check --verbose"""

EXIT_CODES = exit_codes({0: "every selected check passed", 1: "a check failed"})

RUFF = "ruff@0.16.9"
PYRIGHT = "pyright@1.1.414"
PYTEST = "9.1.1"
XDIST = "pytest-xdist==3.8.0"
ACTIONLINT = "actionlint-py@1.7.12.25"

log = logging.getLogger("check")

Command = tuple[str, ...]


class Check:
    """A named step whose commands run from the repository root and stop at the first failure.

    `reads` names files or directories outside the check's skill package that it
    depends on, so a change there runs it too.
    """

    def __init__(
        self,
        name: str,
        *commands: Command,
        reads: tuple[str, ...] = (),
        test_path: str | None = None,
        cheap: bool = False,
    ) -> None:
        self.name = name
        self.commands = commands
        self.reads = reads
        self.test_path = test_path
        self.cheap = cheap

    def skills(self) -> set[str]:
        """The skill packages the commands name; none means the check covers the repository."""
        found: set[str] = set()
        for arg in (arg for command in self.commands for arg in command):
            if not arg.startswith("authoring/"):
                continue
            path = ROOT / arg
            package = next(
                (p for p in (path, *path.parents) if (p / "SKILL.md").is_file()), None
            )
            if package is None:
                raise ScriptError(f"{self.name}: {arg} is not inside a skill package")
            found.add(package.relative_to(ROOT).as_posix())
        return found


def uv_run(script: str, *args: str) -> Command:
    return ("uv", "run", script, *args)


def with_deps(deps: tuple[str, ...]) -> list[str]:
    return [flag for dep in deps for flag in ("--with", dep)]


def ruff(path: str) -> tuple[Command, Command]:
    # The repository has no ruff config; --isolated keeps a pyproject.toml above
    # the checkout from setting the target Python and changing the verdict
    return (
        ("uvx", RUFF, "check", "--isolated", "--quiet", path),
        ("uvx", RUFF, "format", "--isolated", "--quiet", "--check", path),
    )


def pyright(path: str, *deps: str, python: str = "3.11") -> Command:
    return (
        "uvx",
        *with_deps((f"pytest=={PYTEST}", *deps)),
        PYRIGHT,
        "--pythonversion",
        python,
        path,
    )


def pytest(path: str | tuple[str, ...], *deps: str, parallel: bool = True) -> Command:
    return (
        "uvx",
        "--from",
        f"pytest@{PYTEST}",
        *with_deps(((XDIST,) if parallel else ()) + deps),
        "pytest",
        *(("-n", "auto") if parallel else ()),
        *(path if isinstance(path, tuple) else (path,)),
    )


def repo_test(stem: str, *reads: str, cheap: bool = False) -> Check:
    return Check(
        f"test-{stem.replace('_', '-')}",
        test_path=f"scripts/tests/test_{stem}.py",
        reads=reads,
        cheap=cheap,
    )


VIDEO_ARCHIVE = "authoring/verify/verify-video-archive/scripts"
TRANSCRIPT = "authoring/content/transcript"
VERIFY_TRANSCRIPT = "authoring/verify/verify-transcript"
IMAGE_CREATOR = "authoring/content/image-creator/scripts"

CHECKS = [
    Check("frontmatter", uv_run("scripts/check_frontmatter.py")),
    Check("flatten", uv_run("scripts/flatten_skills.py", "--check")),
    Check("remote-skills", uv_run("scripts/remote_skills.py", "--check")),
    Check("cli-block", uv_run("scripts/check_cli_block.py")),
    Check("lint", *ruff("scripts")),
    # Skill scripts paste the block in _cli.py, and some run on Python 3.10
    Check("typecheck", pyright("scripts"), pyright("scripts/_cli.py", python="3.10")),
    repo_test("check"),
    repo_test("check_cli_block", "scripts/check_cli_block.py"),
    repo_test("check_frontmatter", "scripts/check_frontmatter.py"),
    repo_test("cli"),
    repo_test(
        "cli_contract",
        "scripts",
        "docs",
        "authoring",
        "justfile",
        "README.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "lefthook.yml",
        ".lefthook",
        ".github",
    ),
    repo_test("commands", "authoring", cheap=True),
    repo_test("common"),
    repo_test(
        "discover_skills",
        "scripts/discover_skills.py",
        "scripts/flatten_skills.py",
        "scripts/install_skills.py",
    ),
    repo_test("flatten_skills", "scripts/flatten_skills.py"),
    repo_test(
        "install_skills", "scripts/install_skills.py", "scripts/flatten_skills.py"
    ),
    repo_test("justfile", "justfile"),
    repo_test("release_check", "scripts/release_check.py"),
    repo_test("remote_skills", "scripts/remote_skills.py"),
    repo_test("skill_invocation", "authoring", cheap=True),
    repo_test(
        "sync",
        "scripts/sync.py",
        "scripts/flatten_skills.py",
        "scripts/install_skills.py",
        "scripts/sync_private.py",
    ),
    repo_test(
        "sync_fleet",
        "scripts/sync_fleet.py",
        "scripts/sync_private.py",
        "scripts/flatten_skills.py",
        "scripts/install_skills.py",
    ),
    repo_test("sync_private", "scripts/sync_private.py"),
    # Optional local linters stay off so every machine agrees
    Check(
        "workflows",
        ("uvx", "--from", ACTIONLINT, "actionlint", "-shellcheck=", "-pyflakes="),
    ),
    Check(
        "html-mode", uv_run("authoring/content/html-mode/scripts/check_html_mode.py")
    ),
    Check(
        "matt-mode",
        uv_run("authoring/mattpocock/matt-mode/scripts/check_matt_mode.py"),
        uv_run("authoring/mattpocock/matt-mode/scripts/update_matt_mode.py", "check"),
        # It validates the upstream imports of every package in the bucket
        reads=("authoring/mattpocock",),
    ),
    Check(
        "andy-mode",
        uv_run("authoring/andy/andy-mode/scripts/check_andy_mode.py"),
        pytest("authoring/andy/andy-mode/scripts/tests"),
        # A shared route links to its sibling package
        reads=("authoring/andy/2nd-pass",),
    ),
    Check("distill", pytest("authoring/andy/andy-mode/scripts/distill/tests")),
    Check(
        "tavily",
        pytest("authoring/web-research/tavily/scripts/tests", "httpx", "rich", "respx"),
    ),
    Check(
        "transcript",
        pytest(f"{TRANSCRIPT}/scripts/tests", "httpx", "yt-dlp==2026.7.4", "rich"),
        # Its doc test checks the flags these files pass to transcript
        reads=("justfile", "authoring/verify/verify-transcript/SKILL.md"),
    ),
    Check("verify-transcript", pytest(f"{VERIFY_TRANSCRIPT}/scripts/tests")),
    Check(
        "poteto-mode",
        pytest("authoring/pstack/poteto-mode/scripts/tests/test_worktree_audit.py"),
    ),
    Check(
        "verify-video-archive",
        *ruff(VIDEO_ARCHIVE),
        pyright(VIDEO_ARCHIVE),
        pytest(f"{VIDEO_ARCHIVE}/tests"),
    ),
    Check(
        "storytelling",
        pytest("authoring/content/storytelling/tests/test_validate_package.py"),
        uv_run(
            "authoring/content/storytelling/tests/validate-package.py",
            "authoring/content/storytelling",
        ),
    ),
    Check(
        "image-creator",
        *ruff(IMAGE_CREATOR),
        pyright(IMAGE_CREATOR, "pillow"),
        pytest(f"{IMAGE_CREATOR}/tests", "pillow"),
    ),
]

SHARED_TEST_READS = {
    "scripts/_cli.py",
    "scripts/_common.py",
    "pytest.ini",
    "scripts/tests/conftest.py",
}


def validate_repo_tests(checks: list[Check]) -> None:
    """Require one named check for every repository test module."""
    discovered = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "scripts/tests").glob("test_*.py")
    }
    registered = Counter(check.test_path for check in checks if check.test_path)
    missing = sorted(discovered - registered.keys())
    stale = sorted(registered.keys() - discovered)
    duplicate = sorted(path for path, count in registered.items() if count != 1)
    if missing or stale or duplicate:
        details = "; ".join(
            f"{label}: {', '.join(paths)}"
            for label, paths in (
                ("unregistered repository tests", missing),
                ("missing repository tests", stale),
                ("duplicate repository tests", duplicate),
            )
            if paths
        )
        raise ScriptError(f"test check registry is incomplete; {details}")


def passes(check: Check, verbose: bool) -> bool:
    """Run one check; verbose runs stream each command's output to stderr, and
    quiet runs replay a failing command's output there."""
    for command in check.commands:
        log.info("==> %s: %s", check.name, shlex.join(command))
        started = time.monotonic()
        result = run(
            command,
            cwd=ROOT,
            stdout=sys.stderr if verbose else subprocess.PIPE,
            stderr=None if verbose else subprocess.STDOUT,
            text=True,
        )
        log.debug(
            "%s: exited %d after %.1fs",
            check.name,
            result.returncode,
            time.monotonic() - started,
        )
        if result.returncode != 0:
            if not verbose:
                print(f"==> {check.name}: {shlex.join(command)}", file=sys.stderr)
                sys.stderr.write(result.stdout)
            return False
    return True


def changed() -> list[str] | None:
    """Files this branch changes against origin/main, committed or not; None when git cannot tell."""
    base = run_git("merge-base", "HEAD", "origin/main", cwd=ROOT)
    if base.returncode != 0:
        return None
    # -z keeps git from quoting names with spaces or non-ASCII characters
    diff = run_git(
        "diff", "--name-only", "--no-renames", "-z", base.stdout.strip(), cwd=ROOT
    )
    untracked = run_git("ls-files", "-z", "--others", "--exclude-standard", cwd=ROOT)
    if diff.returncode != 0 or untracked.returncode != 0:
        return None
    return [path for path in f"{diff.stdout}\0{untracked.stdout}".split("\0") if path]


def in_scope(checks: list[Check]) -> list[Check]:
    """Every repository check, and each skill check whose skill the change touches."""
    paths = changed()
    if paths is None or "scripts/check.py" in paths:
        return checks
    all_repo_tests = bool(SHARED_TEST_READS.intersection(paths)) or any(
        path.startswith("scripts/tests/") and not Path(path).name.startswith("test_")
        for path in paths
    )
    scoped: list[Check] = []
    for check in checks:
        if check.test_path:
            watched = (check.test_path, *check.reads)
            if (
                check.cheap
                or all_repo_tests
                or any(
                    path == item or path.startswith(f"{item}/")
                    for path in paths
                    for item in watched
                )
            ):
                scoped.append(check)
            else:
                log.info("skip %s: no change under %s", check.name, ", ".join(watched))
            continue
        skills = check.skills()
        watched = sorted({*skills, *check.reads})
        if not skills or any(
            path == w or path.startswith(f"{w}/") for path in paths for w in watched
        ):
            scoped.append(check)
        else:
            log.info("skip %s: no change under %s", check.name, ", ".join(watched))
    return scoped


def repo_batch(checks: list[Check]) -> Command:
    paths = tuple(check.test_path for check in checks if check.test_path)
    return pytest(paths, parallel=any(not check.cheap for check in checks))


def verdict(args: argparse.Namespace) -> str:
    validate_repo_tests(CHECKS)
    selected = [check for check in CHECKS if not args.only or check.name in args.only]
    if args.list:
        repo_tests = [check for check in selected if check.test_path]
        if repo_tests:
            log.info("repository-tests: %s", shlex.join(repo_batch(repo_tests)))
        for check in selected:
            if check.test_path:
                continue
            for command in check.commands:
                log.info("%s: %s", check.name, shlex.join(command))
        return "\n".join(check.name for check in selected)
    if not args.only and not args.sweep:
        selected = in_scope(selected)

    failed: list[str] = []
    repo_tests = [check for check in selected if check.test_path]
    ran_repo_tests = False
    for check in selected:
        if check.test_path:
            if ran_repo_tests:
                continue
            ran_repo_tests = True
            names = [test.name for test in repo_tests]
            if not passes(
                Check("repository-tests", repo_batch(repo_tests)), args.verbose
            ):
                rerun = " ".join(f"--only {name}" for name in names)
                failed.append(f"repository-tests failed; rerun: just check {rerun}")
            continue
        if not passes(check, args.verbose):
            failed.append(check.name)

    if failed:
        raise ScriptError(
            *(
                name
                if name.startswith("repository-tests failed;")
                else f"{name} failed; rerun: just check --only {name}"
                for name in failed
            )
        )
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just check",
        description="Run the checks required for current changes and PR signoff",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--only",
        action="append",
        choices=[check.name for check in CHECKS],
        metavar="NAME",
        help="run only this named check, even when its inputs did not change; repeat for more (see --list)",
    )
    scope.add_argument(
        "--sweep",
        action="store_true",
        help="run every check, including unrelated skill and command tests; use for release or diagnosis",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the check names and exit; -v adds their commands on stderr",
    )
    return run_script(parser, verdict, argv, debug="CHECK_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

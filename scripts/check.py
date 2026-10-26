#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the CI verdict: the checks in CHECKS, in order, answered in one JSON line."""

from __future__ import annotations

import argparse
import logging
import os
import re
import shlex
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple

from _cli import Parser, ScriptError, exit_codes, run_script
from _common import replay, run, run_git

ROOT = Path(__file__).resolve().parent.parent

EPILOG = """\
Each check is one row of CHECKS in scripts/check.py; add a row to add a check.
A check that names a path under authoring/ runs only when this branch, compared
with origin/main, or the working tree changes that skill, or scripts/check.py.
A failing check does not stop the others; its output is replayed on stderr.
The answer is one JSON line: {"ok":true} on stdout, or {"ok":false,...} at the
end of stderr; docs/references/script-output.md explains how to read it.

examples:
  just check
  just check --sweep
  just check --list
  just check --only lint --only tavily
  just check --only test-check --verbose"""

EXIT_CODES = exit_codes({0: "every selected check passed", 1: "a check failed"})

RUFF = "ruff@0.16.9"
PYRIGHT = "pyright@1.1.414"
# The requires-python minimum of scripts/: a bug only an older Python shows fails here (#508).
# A test suite whose scripts declare no minimum runs under it too
PYTHON = "3.11"
PYTEST = "9.1.1"
XDIST = "pytest-xdist==3.8.0"
ACTIONLINT = "actionlint-py@1.7.12.25"
# pnpm dlx runs this Bun without a global install on any machine or runner
BUN = "bun@1.4.2"

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


def pyright(path: str, *deps: str, python: str | None = None) -> Command:
    if python is None:
        target = ROOT / path
        scripts = target.rglob("*.py") if target.is_dir() else (target,)
        minimum = max(
            (
                found
                for script in scripts
                if script.is_file() and (found := declared_minimum(script))
            ),
            default=None,
        )
        python = f"{minimum[0]}.{minimum[1]}" if minimum else PYTHON
    return (
        "uvx",
        *with_deps((f"pytest=={PYTEST}", *deps)),
        PYRIGHT,
        "--warnings",
        "--pythonversion",
        python,
        path,
    )


# PEP 723's pattern for a script metadata block, its requires-python line, and
# each >= bound in that line
SCRIPT_BLOCK = re.compile(r"(?m)^# /// script$\s(?P<content>(^#(| .*)$\s)+)^# ///$")
REQUIRES_PYTHON = re.compile(r"""(?m)^#\s*requires-python\s*=\s*["']([^"']*)["']""")
MINIMUM = re.compile(r">=\s*(\d+)\.(\d+)")


def declared_minimum(script: Path) -> tuple[int, int] | None:
    block = SCRIPT_BLOCK.search(script.read_text(encoding="utf-8"))
    spec = block and REQUIRES_PYTHON.search(block["content"])
    bounds = MINIMUM.findall(spec[1]) if spec else []
    return max(((int(major), int(minor)) for major, minor in bounds), default=None)


def requires_python(suite: str | tuple[str, ...]) -> str:
    """The Python a test suite runs under: the highest requires-python minimum
    its scripts declare, else PYTHON (#692).

    A suite's scripts are the *.py files under the folder that holds its tests
    folder. A subfolder with its own tests folder holds another suite, so its
    scripts count there instead.
    """
    minimums: list[tuple[int, int]] = []
    for each in suite if isinstance(suite, tuple) else (suite,):
        path = Path(each)
        tests = next((p for p in (path, *path.parents) if p.name == "tests"), None)
        if tests is None:
            continue
        for folder, subfolders, files in os.walk(ROOT / tests.parent):
            subfolders[:] = [
                name for name in subfolders if not Path(folder, name, "tests").is_dir()
            ]
            for name in files:
                if name.endswith(".py") and (
                    found := declared_minimum(Path(folder, name))
                ):
                    minimums.append(found)
    if not minimums:
        return PYTHON
    major, minor = max(minimums)
    return f"{major}.{minor}"


def pytest(path: str | tuple[str, ...], *deps: str, parallel: bool = True) -> Command:
    # uv prefers a Python it manages, so without --python a suite runs under
    # whichever one a machine holds, and the verdict differs between machines
    return (
        "uvx",
        "--python",
        requires_python(path),
        "--from",
        f"pytest@{PYTEST}",
        *with_deps(((XDIST,) if parallel else ()) + deps),
        "pytest",
        "-W",
        "error",
        # The rerun reads the FAILED and ERROR summary lines, whatever PYTEST_ADDOPTS says
        "-r",
        "fE",
        *(("-n", "auto") if parallel else ()),
        *(path if isinstance(path, tuple) else (path,)),
    )


def bun(command: str, cwd: str, *args: str) -> Command:
    return ("pnpm", "dlx", BUN, command, "--cwd", cwd, *args)


def repo_test(stem: str, *reads: str, cheap: bool = False) -> Check:
    return Check(
        f"test-{stem.replace('_', '-')}",
        test_path=f"scripts/tests/test_{stem}.py",
        reads=reads,
        cheap=cheap,
    )


VIDEO_ARCHIVE = "authoring/verify-loops/verify-video-archive/scripts"
TRANSCRIPT = "authoring/andy/transcript"
VERIFY_TRANSCRIPT = "authoring/verify-loops/verify-transcript"
HTML_MODE = "authoring/andy/html-mode/scripts"
# Keep these pins equal to the dependencies of check_page.py and pele's render_pages.py
PLAYWRIGHT = "playwright==1.63.0"
PILLOW = "pillow==12.3.0"
IMAGE_CREATOR = "authoring/andy/image-creator/scripts"
PELE = "authoring/andy/pele/scripts"
POTETO_MODE = "authoring/poteto/poteto-mode/scripts"
HEADLESS = "authoring/andy-devtools/headless/scripts"
ANDY_MODE = "authoring/andy/andy-mode"
BRIGADE_REPLAY = "authoring/andy-devtools/brigade-mode/scripts/replay"
COREY_MODE = "authoring/corey-mode/scripts"
WRITING_FOR_AGENTS = "authoring/matt/writing-for-agents"
# Every compiled skill, so a new skill is validated without a new row
SKILLS = tuple(
    sorted(
        path.parent.relative_to(ROOT).as_posix()
        for path in ROOT.glob("skills/*/SKILL.md")
    )
)

CHECKS = [
    Check("frontmatter", uv_run("scripts/check_frontmatter.py")),
    Check("compile", uv_run("scripts/compile_skills.py", "--check")),
    Check("remote-skills", uv_run("scripts/remote_skills.py", "--check")),
    Check("cli-block", uv_run("scripts/check_cli_block.py")),
    # The compiled validator names no package, so this runs on every change.
    # Warnings the skills already carry were accepted, so only errors fail here.
    # corey-mode's playbooks are Corey Haines' text, pinned by its upstream lock
    Check(
        "skills",
        uv_run(
            "skills/writing-for-agents/scripts/validate_skill.py",
            "--errors-only",
            "--exclude",
            "skills/corey-mode/playbooks",
            *SKILLS,
        ),
    ),
    Check("lint", *ruff("scripts")),
    # Skill scripts paste the block in _cli.py, and some run on Python 3.10
    Check("typecheck", pyright("scripts"), pyright("scripts/_cli.py", python="3.10")),
    repo_test(
        "api_keys_validation",
        "scripts/api_keys_validation.py",
        "scripts/sync_private.py",
    ),
    repo_test("check"),
    repo_test("check_cli_block", "scripts/check_cli_block.py"),
    repo_test("check_frontmatter", "scripts/check_frontmatter.py"),
    repo_test("cli"),
    repo_test(
        "cli_contract",
        "scripts",
        "docs",
        "authoring",
        "commands",
        "justfile",
        "README.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "lefthook.yml",
        ".lefthook",
        ".github",
    ),
    repo_test("commands", "commands", "authoring", cheap=True),
    repo_test("common"),
    # A docs link can point at any file, so a deletion anywhere can break one
    repo_test("docs", cheap=True),
    repo_test(
        "discover_skills",
        "scripts/discover_skills.py",
        "scripts/compile_skills.py",
        "scripts/install_skills.py",
        "scripts/sync_private.py",
    ),
    repo_test("compile_skills", "scripts/compile_skills.py"),
    repo_test(
        "install_skills",
        "scripts/install_skills.py",
        "scripts/compile_skills.py",
        "scripts/sync_private.py",
    ),
    repo_test("justfile", "justfile"),
    repo_test("merge", "scripts/merge.py", "scripts/signoff.py"),
    repo_test("release_check", "scripts/release_check.py"),
    repo_test("remote_skills", "scripts/remote_skills.py"),
    repo_test(
        "replay_routing",
        "scripts/replay_routing.py",
        "authoring/corey-mode/SKILL.md",
        "authoring/corey-mode/references/routing-cases.md",
        "authoring/andy/andy-mode/SKILL.md",
        "authoring/andy/andy-mode/references/routing-cases.md",
    ),
    repo_test("signoff", "scripts/signoff.py"),
    repo_test("skill_invocation", "authoring", cheap=True),
    repo_test(
        "sync",
        "scripts/sync.py",
        "scripts/compile_skills.py",
        "scripts/install_skills.py",
        "scripts/sync_private.py",
    ),
    repo_test(
        "sync_fleet",
        "scripts/sync_fleet.py",
        "scripts/sync_private.py",
        "scripts/compile_skills.py",
        "scripts/install_skills.py",
    ),
    repo_test("sync_private", "scripts/sync_private.py"),
    # Optional local linters stay off so every machine agrees
    Check(
        "workflows",
        ("uvx", "--from", ACTIONLINT, "actionlint", "-shellcheck=", "-pyflakes="),
    ),
    Check(
        "html-mode",
        uv_run(f"{HTML_MODE}/check_html_mode.py"),
        *ruff(f"{HTML_MODE}/check_page.py"),
        *ruff(f"{HTML_MODE}/tests"),
        pyright(f"{HTML_MODE}/check_page.py", PLAYWRIGHT, PILLOW),
        # One browser at a time: parallel browsers on one machine distort the frame timings
        pytest(f"{HTML_MODE}/tests", PLAYWRIGHT, PILLOW, parallel=False),
    ),
    Check(
        "matt-mode",
        uv_run("authoring/matt/matt-mode/scripts/check_matt_mode.py"),
        pytest("authoring/matt/matt-mode/scripts/tests"),
        uv_run("authoring/matt/matt-mode/scripts/update_matt_mode.py", "check"),
        # It validates the upstream imports of every package in the bucket
        reads=("authoring/matt",),
    ),
    Check(
        "andy-mode",
        uv_run(f"{ANDY_MODE}/scripts/check_andy_mode.py"),
        pytest(f"{ANDY_MODE}/scripts/tests"),
        # A shared route links to its sibling package
        reads=("authoring/andy/2nd-pass",),
    ),
    Check(
        "corey-mode",
        *ruff(COREY_MODE),
        pyright(COREY_MODE),
        pytest(f"{COREY_MODE}/tests"),
        uv_run(f"{COREY_MODE}/update_corey_mode.py", "check"),
    ),
    Check(
        "brigade-replay",
        *ruff(BRIGADE_REPLAY),
        pyright(BRIGADE_REPLAY, PLAYWRIGHT),
        # test_live.py drives the live page in Chromium through Playwright
        pytest(f"{BRIGADE_REPLAY}/tests", PLAYWRIGHT, parallel=False),
        # test_page.py opens a recorded page with html-mode's checker (#808)
        reads=(f"{HTML_MODE}/check_page.py",),
    ),
    Check(
        "distill",
        *ruff(f"{ANDY_MODE}/scripts/distill"),
        pytest(f"{ANDY_MODE}/scripts/distill/tests"),
    ),
    Check(
        "tavily",
        pytest("authoring/andy/tavily/scripts/tests", "httpx", "respx"),
    ),
    Check(
        "transcript",
        pytest(
            f"{TRANSCRIPT}/scripts/tests",
            "httpx",
            "yt-dlp==2026.7.4",
            "rich",
        ),
        # Its doc test checks the flags these files pass to transcript
        reads=("justfile", "authoring/verify-loops/verify-transcript/SKILL.md"),
    ),
    Check(
        "verify-transcript",
        pytest(f"{VERIFY_TRANSCRIPT}/scripts/tests"),
    ),
    # The free features run the branch's transcript CLI, so a contract change
    # its verifier missed fails here; the paid real summary stays out of the default run
    Check(
        "verify-transcript-free",
        uv_run(f"{VERIFY_TRANSCRIPT}/scripts/verify_transcript.py", "verify"),
        reads=(TRANSCRIPT,),
    ),
    Check(
        "poteto-mode",
        pytest(f"{POTETO_MODE}/tests/test_worktree_audit.py"),
    ),
    Check(
        "poteto-mode-ts",
        bun("install", POTETO_MODE, "--frozen-lockfile"),
        bun("run", POTETO_MODE, "test"),
        bun("run", POTETO_MODE, "typecheck"),
    ),
    Check(
        "verify-video-archive",
        *ruff(VIDEO_ARCHIVE),
        pyright(VIDEO_ARCHIVE),
        pytest(f"{VIDEO_ARCHIVE}/tests"),
    ),
    Check("storytelling", pytest(f"{ANDY_MODE}/scripts/storytelling/tests")),
    Check(
        "headless",
        *ruff(HEADLESS),
        pyright(HEADLESS),
        pytest(f"{HEADLESS}/tests"),
    ),
    # carpaccio's status model; arancini and bisque have none
    Check(
        "brigade-carpaccio",
        uv_run("authoring/andy-devtools/brigade-mode/references/model.py"),
        pytest("authoring/andy-devtools/brigade-mode/references/tests"),
    ),
    Check(
        "writing-for-agents",
        *ruff(f"{WRITING_FOR_AGENTS}/scripts"),
        pyright(f"{WRITING_FOR_AGENTS}/scripts"),
        pytest(f"{WRITING_FOR_AGENTS}/scripts/tests"),
        uv_run(f"{WRITING_FOR_AGENTS}/scripts/validate_skill.py", WRITING_FOR_AGENTS),
    ),
    Check(
        "image-creator",
        *ruff(IMAGE_CREATOR),
        pyright(IMAGE_CREATOR, "pillow"),
        pytest(f"{IMAGE_CREATOR}/tests", "pillow"),
    ),
    Check(
        "pele",
        *ruff(PELE),
        pyright(PELE, PLAYWRIGHT, PILLOW),
        pytest(f"{PELE}/tests", PLAYWRIGHT, PILLOW),
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


class Failure(NamedTuple):
    output: str
    cause: str = ""


def failure(check: Check, verbose: bool) -> Failure | None:
    """Run one check: None when it passes, else its output and launch failure.

    Verbose runs stream each command's output to stderr and return empty output
    on a failure; quiet runs replay the failing command's output there.
    """
    for command in check.commands:
        log.info("==> %s: %s", check.name, shlex.join(command))
        started = time.monotonic()
        try:
            result = run(
                command,
                cwd=ROOT,
                stdout=sys.stderr if verbose else subprocess.PIPE,
                stderr=None if verbose else subprocess.STDOUT,
                text=True,
            )
        except OSError as exc:
            return Failure(
                "",
                f": {command[0]} could not start: {exc}; "
                "check the tool is installed and executable",
            )
        log.debug(
            "%s: exited %d after %.1fs",
            check.name,
            result.returncode,
            time.monotonic() - started,
        )
        if result.returncode != 0:
            if verbose:
                return Failure("")
            print(f"==> {check.name}: {shlex.join(command)}", file=sys.stderr)
            replay(result.stdout)
            return Failure(result.stdout)
    return None


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


# pytest's summary line for a failed test, or for a test whose setup failed
FAILED_TEST = re.compile(
    r"^(?:FAILED|ERROR) (scripts/tests/test_\w+\.py)::", re.MULTILINE
)


# pytest's summary line for a module it could not collect, which names no test
COLLECTION_ERROR = re.compile(r"^ERROR scripts/tests/test_\w+\.py(?!::)", re.MULTILINE)


def failed_tests(output: str, tests: list[Check]) -> list[Check]:
    """The modules pytest's summary names, or every module when it cannot tell:
    after a collection error, which its summary names without a test, or a
    verbose run."""
    if COLLECTION_ERROR.search(output):
        return tests
    named = set(FAILED_TEST.findall(output))
    found = [test for test in tests if test.test_path in named]
    return found if found and len(found) == len(named) else tests


def verdict(args: argparse.Namespace) -> dict[str, Any]:
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
        return {"checks": [check.name for check in selected]}
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
            batch = Check("repository-tests", repo_batch(repo_tests))
            result = failure(batch, args.verbose)
            if result is not None:
                rerun = " ".join(
                    f"--only {test.name}"
                    for test in failed_tests(result.output, repo_tests)
                )
                failed.append(
                    f"repository-tests failed{result.cause}; rerun: just check {rerun}"
                )
            continue
        result = failure(check, args.verbose)
        if result is not None:
            failed.append(
                f"{check.name} failed{result.cause}; rerun: just check --only {check.name}"
            )

    if args.verbose:
        # A later passing child can also leave its streamed output unterminated.
        print(file=sys.stderr)
    if failed:
        raise ScriptError(*failed)
    return {}


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
        help="answer with the check names and exit; -v adds their commands on stderr",
    )
    return run_script(parser, verdict, argv, debug="CHECK_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

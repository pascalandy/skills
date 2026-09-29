#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the CI verdict: every check in CHECKS, in order; success prints nothing."""

from __future__ import annotations

import argparse
import logging
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

from _cli import Parser, ScriptError, exit_codes
from _common import run, run_script

ROOT = Path(__file__).resolve().parent.parent

EPILOG = """\
Each check is one row of CHECKS in scripts/check.py; add a row to add a check.
A failing check does not stop the others; its output is replayed on stderr.

examples:
  just check
  just check --list
  just check --only lint --only tavily
  just check --only jevgate --verbose"""

EXIT_CODES = exit_codes({0: "every selected check passed", 1: "a check failed"})

RUFF = "ruff@0.16.9"
PYRIGHT = "pyright@1.1.414"
PYTEST = "9.1.1"
ACTIONLINT = "actionlint-py@1.7.12.25"

log = logging.getLogger("check")

Command = tuple[str, ...]


class Check:
    """A named step whose commands run from the repository root and stop at the first failure."""

    def __init__(self, name: str, *commands: Command) -> None:
        self.name = name
        self.commands = commands


def uv_run(script: str, *args: str) -> Command:
    return ("uv", "run", script, *args)


def with_deps(deps: tuple[str, ...]) -> list[str]:
    return [flag for dep in deps for flag in ("--with", dep)]


def ruff(path: str, version: str = RUFF) -> tuple[Command, Command]:
    return (
        ("uvx", version, "check", "--quiet", path),
        ("uvx", version, "format", "--quiet", "--check", path),
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


def pytest(path: str, *deps: str) -> Command:
    return ("uvx", "--from", f"pytest@{PYTEST}", *with_deps(deps), "pytest", path)


def script_pin(script: str, package: str) -> str:
    """Read `package==version` from a script's PEP 723 block, so a check cannot drift from it."""
    source = (ROOT / script).read_text(encoding="utf-8")
    match = re.search(rf'"({re.escape(package)}==[^"]+)"', source)
    if match is None:
        raise ValueError(f"{script} does not pin {package}")
    return match.group(1)


VIDEO_ARCHIVE = "authoring/verify/verify-video-archive/scripts"
TRANSCRIPT = "authoring/content/transcript"
VERIFY_TRANSCRIPT = "authoring/verify/verify-transcript"
JEVGATE = "authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts"
JEVGATE_SDK = script_pin(f"{JEVGATE}/jevgate.py", "typesafe-sdk")
JEVLABEL = "authoring/devtools/label-for-issues-jev/scripts"
JEVLABEL_SDK = script_pin(f"{JEVLABEL}/jevlabel.py", "typesafe-sdk")
RETRO_TRIAGE = "authoring/devtools/retro-triage-jev/scripts"
IMAGE_CREATOR = "authoring/content/image-creator/scripts"

CHECKS = [
    Check("frontmatter", uv_run("scripts/check_frontmatter.py")),
    Check("flatten", uv_run("scripts/flatten_skills.py", "--check")),
    Check("cli-block", uv_run("scripts/check_cli_block.py")),
    Check("lint", *ruff("scripts")),
    # Skill scripts paste the block in _cli.py, and some run on Python 3.10
    Check("typecheck", pyright("scripts"), pyright("scripts/_cli.py", python="3.10")),
    Check("test", ("uvx", f"pytest@{PYTEST}")),
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
    ),
    Check("distill", pytest("authoring/knowledge/distill/scripts/tests")),
    Check(
        "tavily",
        pytest("authoring/web-research/tavily/scripts/tests", "httpx", "rich", "respx"),
    ),
    Check(
        "transcript",
        pytest(f"{TRANSCRIPT}/scripts/tests", "httpx", "yt-dlp==2026.7.4", "rich"),
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
    # Ruff stays at 0.15.7: newer releases report findings whose fixes would
    # change the engine's stamped hash
    Check(
        "jevgate",
        *ruff(JEVGATE, version="ruff@0.15.7"),
        pyright(JEVGATE, JEVGATE_SDK),
    ),
    Check(
        "jevlabel",
        *ruff(JEVLABEL),
        pyright(JEVLABEL, JEVLABEL_SDK),
    ),
    Check(
        "retro-triage-jev",
        *ruff(RETRO_TRIAGE),
        pyright(RETRO_TRIAGE),
        pytest(f"{RETRO_TRIAGE}/tests"),
    ),
    Check(
        "image-creator",
        *ruff(IMAGE_CREATOR),
        pyright(IMAGE_CREATOR, "pillow"),
        pytest(f"{IMAGE_CREATOR}/tests", "pillow"),
    ),
]


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


def verdict(args: argparse.Namespace) -> str:
    selected = [check for check in CHECKS if not args.only or check.name in args.only]
    if args.list:
        for check in selected:
            for command in check.commands:
                log.info("%s: %s", check.name, shlex.join(command))
        return "\n".join(check.name for check in selected)

    failed: list[str] = []
    for check in selected:
        if not passes(check, args.verbose):
            failed.append(check.name)

    if failed:
        raise ScriptError(
            *(f"{name} failed; rerun: just check --only {name}" for name in failed)
        )
    return ""


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        prog="just check",
        description="Run the CI verdict: the checks `just signoff` requires before it signs off",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=[check.name for check in CHECKS],
        metavar="NAME",
        help="run only this check; repeat for more (see --list)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the check names and exit; -v adds their commands on stderr",
    )
    return run_script(parser, verdict, argv, debug="CHECK_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

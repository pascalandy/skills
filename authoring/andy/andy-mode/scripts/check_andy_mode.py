#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Validate the andy-mode route table and every bundled path it reaches."""

from __future__ import annotations

# >>> cli-block: canonical copy in scripts/_cli.py; do not edit a pasted copy
import argparse
import json
import logging
import os
import re
import shlex
import signal
import sys
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, NoReturn, TextIO

USAGE = 2
TEMPORARY = 75
INTERRUPTED = 128 + signal.SIGINT
TERMINATED = 128 + signal.SIGTERM


class ScriptError(Exception):
    """An expected failure; each argument is one message that says what to fix.

    `detail` is text printed on stderr before the messages; `report` is the
    object `--json` prints on stderr beside them.
    """

    code = 1

    def __init__(
        self, *messages: str, detail: str = "", report: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(*messages)
        self.detail = detail
        self.report = dict(report or {})


class UsageError(ScriptError):
    """A bad argument the parser cannot catch, such as an unknown name."""

    code = USAGE


class TemporaryError(ScriptError):
    """A failure a later retry may fix: an outage, a timeout, or a held lock."""

    code = TEMPORARY


class Interrupted(KeyboardInterrupt):
    """SIGINT or SIGTERM arrived; `code` is 130 or 143."""

    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def exit_codes(specific: Mapping[int, str]) -> dict[int, str]:
    """Every code a script returns, in order, for its --help and its tests.

    `specific` adds codes or renames 1; 0, 1, 2, 130, and 143 are always there.
    """
    codes = {
        0: "success",
        1: "failure",
        USAGE: "bad usage",
        INTERRUPTED: "interrupted (SIGINT)",
        TERMINATED: "terminated (SIGTERM)",
        **specific,
    }
    reserved = [
        code for code in codes if code >= 124 and code not in (INTERRUPTED, TERMINATED)
    ]
    if reserved:
        raise ValueError(f"exit codes {reserved} are reserved for the shell and OS")
    return dict(sorted(codes.items()))


class Parser(argparse.ArgumentParser):
    """argparse without abbreviated options, whose help ends with the exit codes
    and whose usage errors print short usage and the help hint, then exit 2.

    With `json_errors` set, a usage error is one JSON object on stderr instead.
    """

    json_errors = False

    def __init__(
        self, *, exit_codes: Mapping[int, str], epilog: str = "", **kwargs: Any
    ) -> None:
        table = "\n".join(
            f"  {code:<4} {meaning}" for code, meaning in exit_codes.items()
        )
        kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
        super().__init__(
            epilog=f"{epilog}\n\nexit codes:\n{table}".lstrip("\n"),
            allow_abbrev=False,
            **kwargs,
        )
        self.exit_codes = dict(exit_codes)

    def error(self, message: str) -> NoReturn:
        if self.json_errors:
            failure = {"errors": [message], "help": f"{self.prog} --help"}
            self.exit(USAGE, json.dumps(failure, indent=2) + "\n")
        self.print_usage(sys.stderr)
        self.exit(USAGE, f"error: {message}\nrun '{self.prog} --help'\n")


def answer(code: int, fields: Mapping[str, Any]) -> int:
    """Print the one JSON line a script answers with, and return `code`.

    `ok` comes first and is true exactly when `code` is 0, whatever `fields`
    says. Success goes to stdout; a failure goes to stderr, after its
    diagnostics, and leaves stdout empty (docs/references/script-output.md).
    """
    body = {"ok": code == 0, **fields}
    body["ok"] = code == 0
    print(
        json.dumps(body, separators=(",", ":")), file=sys.stderr if code else sys.stdout
    )
    return code


def given(
    argv: Sequence[str], *flags: str, parser: argparse.ArgumentParser | None = None
) -> bool:
    """Whether one of `flags` comes before `--`, where options end; use it to let
    -h and --help win over every other argument, or to spot --json early.

    With `parser`, a bundle of its flag letters counts too, such as -vh for
    -v -h; a bundle holding an option that takes a value never does.
    """
    letters = {flag[1] for flag in flags if len(flag) == 2 and flag[1] != "-"}
    bundled = flag_letters(parser) if parser is not None and letters else set()
    for arg in argv:
        if arg == "--":
            return False
        if arg in flags:
            return True
        bundle = set(arg[1:]) if re.fullmatch(r"-[A-Za-z]{2,}", arg) else set()
        if bundle & letters and bundle <= bundled:
            return True
    return False


def flag_letters(parser: argparse.ArgumentParser) -> set[str]:
    """The one-letter options of `parser` and its commands that take no value."""
    letters: set[str] = set()
    parsers = [parser]
    while parsers:
        each = parsers.pop()
        for option, action in each._option_string_actions.items():
            if len(option) == 2 and option[1] != "-" and action.nargs == 0:
                letters.add(option[1])
        for action in each._actions:
            if isinstance(action, argparse._SubParsersAction):
                parsers.extend(action.choices.values())
    return letters


@contextmanager
def signals_interrupt() -> Iterator[None]:
    """Raise Interrupted(130) on SIGINT and Interrupted(143) on SIGTERM.

    The first signal ignores any repeat, so cleanup in `finally` blocks runs to
    the end. Handlers need the main thread; elsewhere this changes nothing.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    handled = (signal.SIGINT, signal.SIGTERM)
    previous = {number: signal.getsignal(number) for number in handled}
    fired = False

    def interrupt(number: int, _frame: object) -> None:
        nonlocal fired
        fired = True
        for each in handled:
            signal.signal(each, signal.SIG_IGN)
        raise Interrupted(128 + number)

    for number in handled:
        signal.signal(number, interrupt)
    try:
        yield
    finally:
        if not fired:
            for number, handler in previous.items():
                signal.signal(number, handler)


def env_flag(name: str) -> bool:
    """Whether an environment switch such as SYNC_FLEET_DEBUG is on: set, and not 0."""
    return os.environ.get(name, "") not in ("", "0")


def color_enabled(stream: TextIO, disabled: bool = False) -> bool:
    """Color only on a terminal, and never with --no-color, NO_COLOR, or TERM=dumb."""
    return (
        not disabled
        and not os.environ.get("NO_COLOR")
        and os.environ.get("TERM") != "dumb"
        and stream.isatty()
    )


DURATION = re.compile(r"(\d+(?:\.\d+)?)([smh]?)")


def duration(text: str) -> float:
    """Seconds from `30s`, `5m`, `2h`, or bare seconds; use it as an argparse type."""
    match = DURATION.fullmatch(text.strip())
    if match is None or float(match[1]) <= 0:
        raise argparse.ArgumentTypeError(
            f"invalid duration {text!r}; use a positive number of seconds, or 30s, 5m, 2h"
        )
    return float(match[1]) * {"": 1, "s": 1, "m": 60, "h": 3600}[match[2]]


def usage_error(message: str) -> NoReturn:
    raise UsageError(message)


def run_script(
    parser: Parser,
    work: Callable[[argparse.Namespace], Mapping[str, Any]],
    argv: Sequence[str] | None = None,
    *,
    debug: str | None = None,
) -> int:
    """Parse arguments, run `work`, and answer its outcome in one JSON line with
    its exit code, as docs/references/script-output.md describes.

    Every outcome answers, even a usage error, a bug, or an interrupt. `work`
    returns the data beside `ok`, usually {}, and raises ScriptError,
    UsageError, or TemporaryError for expected failures. `debug` names the
    script's <NAME>_DEBUG variable and adds --debug; without it the script never
    prints a traceback. Call it from `main()` and pass the result to `SystemExit`.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print progress and step details on stderr",
    )
    if debug:
        parser.add_argument(
            "--debug",
            action="store_true",
            help=f"print internals, timings, and tracebacks on stderr; also {debug}=1",
        )
    if given(argv, "-h", "--help", parser=parser):
        parser.print_help()
        return 0

    # Parser.error, in the pasted cli block, prints usage errors itself;
    # raising sends this one through answer_failure()
    parser.error = usage_error
    command = shlex.join([*parser.prog.split(), *argv])
    tracing = False
    with signals_interrupt():
        try:
            args = parser.parse_args(argv)
            tracing = debug is not None and (args.debug or env_flag(debug))
            logging.basicConfig(
                format="%(message)s",
                level=logging.DEBUG
                if tracing
                else logging.INFO
                if args.verbose
                else logging.WARNING,
                stream=sys.stderr,
                force=True,
            )
            return answer(0, work(args))
        except KeyboardInterrupt as stop:
            code = getattr(stop, "code", INTERRUPTED)
            word = "interrupted" if code == INTERRUPTED else "terminated"
            return answer(code, {"errors": [word]})
        except ScriptError as error:
            return answer_failure(error, parser, command)
        except Exception as error:
            # The traceback comes first, so the answer ends stderr
            logging.getLogger(__name__).debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(f"{type(error).__name__}: {error}")
            return answer_failure(
                unexpected, parser, command, rerun=bool(debug) and not tracing
            )


def answer_failure(
    error: ScriptError, parser: Parser, command: str, rerun: bool = False
) -> int:
    """Answer a failure on stderr, after its detail, and return its exit code.
    Hints name the command to run next: help for a usage error, retry for a
    temporary failure, and rerun with --debug for a bug."""
    messages = [str(message) for message in error.args]
    hints: dict[str, str] = {}
    if isinstance(error, UsageError):
        hints["help"] = f"{parser.prog} --help"
    elif isinstance(error, TemporaryError) and messages:
        hints["retry"] = command
    elif rerun:
        hints["rerun"] = f"{command} --debug"
    if error.detail:
        print(error.detail, file=sys.stderr)
    return answer(error.code, {"errors": messages, **error.report, **hints})


# <<< cli-block

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

EPILOG = """\
Checks that each route in SKILL.md names one playbook, that route names stay
unique once case, spaces, hyphens, and underscores are ignored, that SKILL.md
exists only at the root, that every relative link and anchor outside code
resolves, and that every bundled path resolves, in code blocks too. A link
inside a code block is an example, not a link. Answers {"ok":true} on stdout
when the package is valid. Otherwise stdout stays empty and the last line of
stderr lists each problem under "errors".

examples:
  uv run authoring/andy/andy-mode/scripts/check_andy_mode.py
  uv run authoring/andy/andy-mode/scripts/check_andy_mode.py --verbose
  uv run authoring/andy/andy-mode/scripts/check_andy_mode.py /tmp/andy-mode-copy"""

EXIT_CODES = exit_codes({0: "the package is valid", 1: "a check failed"})

log = logging.getLogger("check-andy-mode")

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
EXTERNAL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ROUTE_CELL_RE = re.compile(r"^\[`([^`]+)`\]\(([^)\s]+)\)$")
ALIAS_RE = re.compile(r"`([^`]+)`")
PLACEHOLDER_CHARS = set("<>*{}$")
# A bundled path stands alone or follows a placeholder such as `<skill_dir>/`
BUNDLED_RE = re.compile(
    r"(?:(?<![\w/.<>-])|(?<=>/))((?:playbooks|scripts|references)/[\w./-]*[\w/])"
)


@dataclass(frozen=True)
class Route:
    family: str
    name: str
    aliases: tuple[str, ...]
    target: PurePosixPath


def normalize(name: str) -> str:
    """Fold a route name the way the router matches it."""
    return re.sub(r"[\s_-]+", "", name).lower()


def split_blocks(text: str) -> tuple[list[str], list[str]]:
    """Return the lines outside fenced code blocks, then the lines inside them."""
    prose: list[str] = []
    fenced: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if fence is not None:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = None
            else:
                fenced.append(line)
            continue
        if match:
            fence = match.group(1)
            continue
        prose.append(line)
    return prose, fenced


def prose_lines(text: str) -> list[str]:
    return split_blocks(text)[0]


def split_code(line: str) -> tuple[str, list[str]]:
    """Return the line with code spans blanked, and the code span contents."""
    spans = [match.group(2).strip() for match in CODE_SPAN_RE.finditer(line)]
    return CODE_SPAN_RE.sub(" ", line), spans


def anchor_slug(heading: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "")
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for line in prose_lines(path.read_text(encoding="utf-8")):
        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = anchor_slug(match.group(2))
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        found.add(slug if seen == 0 else f"{slug}-{seen}")
    return found


def parse_routes(skill: Path, errors: list[str]) -> list[Route]:
    """Read every table row whose first cell links a route, grouped by `###` family."""
    routes: list[Route] = []
    family = ""
    for line in prose_lines(skill.read_text(encoding="utf-8")):
        if line.startswith("### "):
            family = line[4:].strip()
            continue
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        match = ROUTE_CELL_RE.match(cells[0])
        if not match:
            continue
        if not family:
            errors.append(f"SKILL.md: route {match.group(1)} has no family heading")
        aliases = tuple(ALIAS_RE.findall(cells[1])) if len(cells) > 1 else ()
        routes.append(
            Route(family, match.group(1), aliases, PurePosixPath(match.group(2)))
        )
    if not routes:
        errors.append("SKILL.md: no route table rows found")
    return routes


def check_routes(root: Path, routes: list[Route], errors: list[str]) -> None:
    owners: dict[str, str] = {}
    for route in routes:
        for name in (route.name, *route.aliases):
            key = normalize(name)
            if key in owners and owners[key] != route.name:
                errors.append(
                    f"SKILL.md: {name!r} matches both {owners[key]} and {route.name}"
                )
            owners.setdefault(key, route.name)
        playbook = PurePosixPath("playbooks", f"{route.name}.md")
        shared = PurePosixPath("..", route.name, "SKILL.md")
        if route.target not in (playbook, shared):
            errors.append(
                f"SKILL.md: route {route.name} must target {playbook} or {shared}, "
                f"not {route.target}"
            )
        elif not (root / route.target).is_file():
            errors.append(
                f"SKILL.md: route {route.name} target is missing: {route.target}"
            )

    routed = {
        route.target.name for route in routes if route.target.parent.name == "playbooks"
    }
    for playbook in sorted((root / "playbooks").glob("*.md")):
        if playbook.name not in routed:
            errors.append(f"playbooks/{playbook.name}: no route in SKILL.md reaches it")


def in_sibling_skill(target: Path, parent: Path) -> bool:
    """Whether a path sits inside a skill package next to andy-mode."""
    if not target.is_relative_to(parent):
        return False
    top = target.relative_to(parent).parts[:1]
    return bool(top) and (parent / top[0] / "SKILL.md").is_file()


def check_paths(root: Path, route_names: set[str], errors: list[str]) -> None:
    """Resolve relative links, their anchors, and the bundled paths code names."""
    home = root.resolve()
    anchor_cache: dict[Path, set[str]] = {}
    bundled = (
        "playbooks/",
        "scripts/",
        *(f"references/{name}/" for name in route_names),
    )

    def check_code(label: str, text: str) -> None:
        for token in BUNDLED_RE.findall(text):
            if token.startswith(bundled) and not (root / token).exists():
                errors.append(f"{label}: unresolved bundled path: {token}")

    for path in sorted(root.rglob("*.md")):
        label = path.relative_to(root).as_posix()
        prose_part, fenced = split_blocks(path.read_text(encoding="utf-8"))
        for line in prose_part:
            prose, spans = split_code(line)
            for raw in LINK_RE.findall(prose):
                if raw.startswith("//") or EXTERNAL_RE.match(raw):
                    continue
                # Quoted examples, such as chat-export artifacts, are not paths
                if PLACEHOLDER_CHARS & set(raw) or '"' in raw:
                    continue
                part, _, anchor = unquote(raw).partition("#")
                target = (path.parent / part).resolve() if part else path.resolve()
                if not target.is_relative_to(home) and not in_sibling_skill(
                    target, home.parent
                ):
                    errors.append(f"{label}: link leaves andy-mode: {raw}")
                    continue
                if not target.exists():
                    errors.append(f"{label}: unresolved link: {raw}")
                    continue
                if anchor and target.suffix == ".md":
                    if target not in anchor_cache:
                        anchor_cache[target] = anchors(target)
                    if anchor not in anchor_cache[target]:
                        errors.append(f"{label}: unresolved anchor: {raw}")
            for span in spans:
                check_code(label, span)
        for line in fenced:
            check_code(label, line)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return [f"{root}: SKILL.md is missing"]
    for nested in sorted(root.rglob("SKILL.md")):
        if nested != skill:
            errors.append(
                f"{nested.relative_to(root)}: only the root may be named SKILL.md"
            )
    routes = parse_routes(skill, errors)
    check_routes(root, routes, errors)
    names = {route.name for route in routes}
    names |= {path.stem for path in (root / "playbooks").glob("*.md")}
    check_paths(root, names, errors)
    log.info(
        "checked %d routes and %d Markdown files",
        len(routes),
        sum(1 for _ in root.rglob("*.md")),
    )
    return errors


def check(args: argparse.Namespace) -> dict[str, Any]:
    if not args.root.is_dir():
        raise UsageError(f"not a directory: {args.root}")
    errors = validate(args.root)
    if errors:
        raise ScriptError(*errors)
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        prog="check_andy_mode.py",
        description=__doc__,
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="andy-mode package directory (default: this script's package)",
    )
    return run_script(parser, check, argv)


if __name__ == "__main__":
    raise SystemExit(main())

# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check or render Mermaid-syntax diagrams with pele.

Reads each .mmd file as one diagram, each ```mermaid fence of a .md file as one
diagram, and - as one diagram from stdin. Loads the pele installed in the
current folder's project, or else the one in ~/.cache/pele ($XDG_CACHE_HOME/pele).

Without --output, checks that every diagram renders and writes nothing. With
--output, also writes one SVG per diagram that renders, styled with the bundled
assets/theme.css unless --theme or --no-theme says otherwise.

Answers in one JSON line. A success prints {"ok":true,"pele":{...},"diagrams":[...]}
on stdout: the pele version and folder, then each diagram's source position,
type, width, height, and SVG path. A diagram that does not render fails the run:
stdout stays empty, and the last stderr line lists it under "errors" as
file:line:column: code: message, the line and column counted in the input file.
The SVGs of the diagrams that rendered stay listed under "diagrams".
"""

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

    `detail` is text printed on stderr before the answer; `report` holds the
    fields the answer carries beside `errors`, such as `changes`.
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
    and whose usage errors print short usage and the help hint, then exit 2;
    run_script() makes them answer in JSON instead."""

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
    line = json.dumps(body, separators=(",", ":"))
    print(line, file=sys.stderr if code else sys.stdout)
    return code


def given(
    argv: Sequence[str], *flags: str, parser: argparse.ArgumentParser | None = None
) -> bool:
    """Whether one of `flags` comes before `--`, where options end; use it to let
    -h and --help win over every other argument.

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


def command_parsers(parser: argparse.ArgumentParser) -> list[argparse.ArgumentParser]:
    """The parser of every command below `parser`, at any depth."""
    found: list[argparse.ArgumentParser] = []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for command in dict.fromkeys(action.choices.values()):
                found += [command, *command_parsers(command)]
    return found


def named_command(
    parser: argparse.ArgumentParser, argv: Sequence[str]
) -> argparse.ArgumentParser:
    """The deepest command `argv` names, whose help -h asks for."""
    for arg in argv:
        if arg == "--":
            break
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction) and arg in action.choices:
                parser = action.choices[arg]
                break
    return parser


def usage_error_for(parser: argparse.ArgumentParser) -> Callable[[str], NoReturn]:
    """The error method of `parser`: a usage error whose help hint names it, so
    a command's mistake points to that command's help."""

    def error(message: str) -> NoReturn:
        raise UsageError(message, report={"help": f"{parser.prog} --help"})

    return error


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
    # A command's parser takes -v and --debug too, after the command; SUPPRESS
    # keeps a flag given before it
    for each in (parser, *command_parsers(parser)):
        default = False if each is parser else argparse.SUPPRESS
        if "-v" not in each._option_string_actions:
            each.add_argument(
                "-v",
                "--verbose",
                action="store_true",
                default=default,
                help="print progress and step details on stderr",
            )
        if debug and "--debug" not in each._option_string_actions:
            each.add_argument(
                "--debug",
                action="store_true",
                default=default,
                help=f"print internals, timings, and tracebacks on stderr; also {debug}=1",
            )
        # Parser.error prints usage errors itself; raising sends each one
        # through answer_failure(). The root reports unknown arguments, which
        # belong to the command argv names
        named = named_command(parser, argv) if each is parser else each
        each.error = usage_error_for(named)  # pyright: ignore[reportAttributeAccessIssue]
    if given(argv, "-h", "--help", parser=parser):
        named_command(parser, argv).print_help()
        return 0

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
    if isinstance(error, UsageError) and "help" not in error.report:
        hints["help"] = f"{parser.prog} --help"
    elif isinstance(error, TemporaryError) and messages:
        hints["retry"] = command
    elif rerun:
        hints["rerun"] = f"{command} --debug"
    if error.detail:
        print(error.detail, file=sys.stderr)
    return answer(error.code, {"errors": messages, **error.report, **hints})


# <<< cli-block

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

EPILOG = """\
examples:
  uv run scripts/render_diagrams.py diagram.mmd
  uv run scripts/render_diagrams.py notes.md --output /tmp/pele
  uv run scripts/render_diagrams.py references/source/examples/sequence.md --output /tmp/pele --no-theme
  printf 'flowchart LR\\n  A --> B\\n' | uv run scripts/render_diagrams.py - --output /tmp/pele"""

EXIT_CODES = exit_codes(
    {1: "a diagram did not render, an input is unreadable, or node or pele is missing"}
)
THEME = Path(__file__).resolve().parent.parent / "assets/theme.css"
# The 603 bundled examples render in under a second, so this only stops a hung node
TIMEOUT = 120

log = logging.getLogger("render_diagrams")

# Only PeleError counts as a diagram error; anything else is a pele bug
RENDER_JS = """
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const input = JSON.parse(readFileSync(0, 'utf8'));
let entry, manifest;
for (const dir of input.dirs) {
  try {
    const require = createRequire(dir + '/');
    entry = require.resolve('pele');
    manifest = require.resolve('pele/package.json');
    break;
  } catch {}
}
if (!entry) {
  process.stdout.write(JSON.stringify({ missing: true }));
  process.exit(0);
}
const pele = await import(pathToFileURL(entry).href);
const results = input.sources.map((text) => {
  try {
    const { svg, type, width, height } = pele.render(text);
    return { svg, type, width, height };
  } catch (error) {
    if (!(error instanceof pele.PeleError)) {
      return { error: { code: 'internal', line: 0, column: 0, message: String(error?.stack ?? error) } };
    }
    const { code, line, column, message } = error;
    return { error: { code, line, column, message } };
  }
});
const { version } = JSON.parse(readFileSync(manifest, 'utf8'));
process.stdout.write(JSON.stringify({ version, path: dirname(manifest), results }));
"""


@dataclass(frozen=True)
class Diagram:
    """One diagram's text and where it starts: `line` is the input line of its first text line."""

    origin: str
    line: int
    text: str
    stem: str


def cache_dir() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "pele"


def fences(path: str, text: str) -> list[Diagram]:
    """Each top-level ```mermaid or ~~~mermaid fence, ignoring other fences."""
    stem = Path(path).stem
    found: list[Diagram] = []
    fence = ""
    mermaid = False
    body: list[str] = []
    start = 0
    for number, line in enumerate(text.splitlines(), 1):
        if fence:
            closing = r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*"
            if re.fullmatch(closing, line):
                if mermaid:
                    found.append(
                        Diagram(path, start, "\n".join(body) + "\n", f"{stem}-L{start}")
                    )
                fence = ""
            elif mermaid:
                body.append(line)
            continue
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})\s*(\S*).*", line)
        if opening:
            fence = opening[1]
            mermaid = opening[2] == "mermaid"
            body = []
            start = number + 1
    if fence and mermaid:
        raise ScriptError(
            f"{path}:{start - 1}: unclosed mermaid fence; close it, then run this command again"
        )
    return found


def read_diagrams(files: Sequence[str]) -> list[Diagram]:
    diagrams: list[Diagram] = []
    for name in files:
        if name == "-":
            diagrams.append(Diagram("<stdin>", 1, sys.stdin.read(), "stdin"))
            continue
        try:
            text = Path(name).read_text(encoding="utf-8")
        except OSError as error:
            raise ScriptError(
                f"{name}: {error.strerror}; check the path, then run this command again"
            ) from None
        if name.endswith(".md"):
            diagrams.extend(fences(name, text))
        else:
            diagrams.append(Diagram(name, 1, text, Path(name).stem))
    return diagrams


def run_pele(diagrams: list[Diagram]) -> dict[str, Any]:
    if shutil.which("node") is None:
        raise ScriptError(
            "node not found; install Node.js 20 or later from https://nodejs.org, then run this command again"
        )
    request = {
        "dirs": [os.getcwd(), str(cache_dir())],
        "sources": [d.text for d in diagrams],
    }
    try:
        done = subprocess.run(
            ["node", "--input-type=module", "-e", RENDER_JS],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ScriptError(
            f"pele did not finish within {TIMEOUT} seconds; render fewer diagrams per run"
        ) from None
    if done.returncode:
        raise ScriptError(
            "node could not run pele; run `node --version` and check it is 20 or later",
            detail=done.stderr.strip(),
        )
    reply = json.loads(done.stdout)
    if reply.get("missing"):
        raise ScriptError(
            f"pele not found from {os.getcwd()} or {cache_dir()}; "
            f"run `pnpm add pele` in the project, or `pnpm --dir {cache_dir()} add pele`, "
            "then run this command again"
        )
    return reply


def styled(svg: str, css: str) -> str:
    return re.sub(
        r"<svg\b[^>]*>",
        lambda tag: f"{tag[0]}<style><![CDATA[\n{css}]]></style>",
        svg,
        count=1,
    )


def render(args: argparse.Namespace) -> dict[str, Any]:
    diagrams = read_diagrams(args.files)
    if not diagrams:
        raise UsageError("no diagram found: a .md input needs a ```mermaid fence")
    css = ""
    if args.output and not args.no_theme:
        try:
            css = args.theme.read_text(encoding="utf-8")
        except OSError as error:
            raise ScriptError(
                f"{args.theme}: {error.strerror}; pass an existing CSS file to --theme"
            ) from None
    reply = run_pele(diagrams)
    if args.output:
        try:
            args.output.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise ScriptError(
                f"{args.output}: {error.strerror}; pass a writable folder to --output"
            ) from None
    rendered: list[dict[str, Any]] = []
    errors: list[str] = []
    for diagram, result in zip(diagrams, reply["results"]):
        error = result.get("error")
        if error:
            line = diagram.line + error["line"] - 1 if error["line"] else diagram.line
            column = f"{error['column']}:" if error["column"] else ""
            errors.append(
                f"{diagram.origin}:{line}:{column} {error['code']}: {error['message']}"
            )
            continue
        entry = {
            "source": f"{diagram.origin}:{diagram.line}",
            "type": result["type"],
            "width": result["width"],
            "height": result["height"],
        }
        if args.output:
            svg = args.output / f"{diagram.stem}.svg"
            svg.write_text(
                styled(result["svg"], css) if css else result["svg"], encoding="utf-8"
            )
            entry["svg"] = str(svg)
        rendered.append(entry)
        log.info("rendered %s", entry["source"])
    found = {
        "pele": {"version": reply["version"], "path": reply["path"]},
        "diagrams": rendered,
    }
    if errors:
        raise ScriptError(*errors, report=found)
    return found


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(exit_codes=EXIT_CODES, description=__doc__, epilog=EPILOG)
    parser.add_argument(
        "files", nargs="+", help=".mmd or .md input files, or - for stdin"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="folder for the SVG files; without it, only check",
    )
    look = parser.add_mutually_exclusive_group()
    look.add_argument(
        "--theme",
        type=Path,
        default=THEME,
        help="CSS added inside each SVG (default: bundled assets/theme.css)",
    )
    look.add_argument(
        "--no-theme", action="store_true", help="keep pele's default colors"
    )
    return run_script(parser, render, argv)


if __name__ == "__main__":
    raise SystemExit(main())

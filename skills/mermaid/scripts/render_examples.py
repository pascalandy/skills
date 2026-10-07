# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render fenced Mermaid examples with mmdc; optionally build an offline gallery.

Uses the bundled black-background theme; --config overrides it. Diagram frontmatter
can override individual family settings. Each SVG keeps its Mermaid source beside
it, under the same name ending in .mmd.

Answers in one JSON line. A success prints {"ok":true,"files":[...]} on stdout:
each SVG, then index.html with --gallery. An example that fails to render fails
the run: stdout stays empty, mmdc's messages go to stderr, and the last stderr
line lists each failed example under "errors".
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
            return answer(code, {"errors": [word], **carried(stop)})
        except ScriptError as error:
            return answer_failure(error, parser, command)
        except Exception as error:
            # The traceback comes first, so the answer ends stderr
            logging.getLogger(__name__).debug("unexpected failure", exc_info=True)
            unexpected = ScriptError(
                f"{type(error).__name__}: {error}", report=carried(error)
            )
            return answer_failure(
                unexpected, parser, command, rerun=bool(debug) and not tracing
            )


def carried(error: BaseException) -> dict[str, Any]:
    """The `report` an exception carries, such as the changes a run already
    made before an interrupt or a bug, or {} when it carries none."""
    report = getattr(error, "report", None)
    return dict(report) if isinstance(report, Mapping) else {}


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

import base64
import html
import shutil
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

EPILOG = """\
examples:
  uv run scripts/render_examples.py SKILL.md references/*.md --output /tmp/mermaid
  uv run scripts/render_examples.py references/data-perspectives.md --output /tmp/data --gallery
  uv run scripts/render_examples.py references/flowcharts.md --output /tmp/flow --mmdc /path/to/mmdc"""

EXIT_CODES = exit_codes(
    {1: "an example failed to render, or an input or mmdc is missing"}
)
TIMEOUT = 120

log = logging.getLogger("render_examples")


@dataclass(frozen=True)
class Example:
    path: Path
    line: int
    heading: str
    source: str
    prose: str
    after: str = ""


def extract(path: Path) -> list[Example]:
    """Read top-level backtick or tilde fences, ignoring nested example fences."""
    examples: list[Example] = []
    heading = path.stem
    fence = ""
    mermaid = False
    source: list[str] = []
    prose: list[str] = []
    start = 0
    after_diagram = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if fence:
            if re.fullmatch(
                r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line
            ):
                if mermaid:
                    examples.append(
                        Example(
                            path,
                            start,
                            heading,
                            "\n".join(source) + "\n",
                            "\n".join(prose).strip(),
                        )
                    )
                    prose = []
                    after_diagram = True
                fence = ""
            elif mermaid:
                source.append(line)
            continue
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", line)
        if opening:
            if after_diagram:
                examples[-1] = replace(examples[-1], after="\n".join(prose).strip())
                prose = []
                after_diagram = False
            fence = opening[1]
            mermaid = opening[2].strip() == "mermaid"
            source = []
            start = number + 1
        else:
            title = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
            if title:
                if after_diagram:
                    examples[-1] = replace(examples[-1], after="\n".join(prose).strip())
                    after_diagram = False
                heading = title[1]
                prose = []
            else:
                prose.append(line)
    if fence and mermaid:
        raise ValueError(f"{path}:{start}: unclosed Mermaid fence")
    if after_diagram:
        examples[-1] = replace(examples[-1], after="\n".join(prose).strip())
    return examples


def paragraphs(text: str) -> str:
    """Escape prose, allowing only HTTPS Markdown links as active markup."""
    rendered = []
    for paragraph in re.split(r"\n\s*\n", text.replace("**", "").replace("`", "")):
        if not paragraph.strip():
            continue
        pieces = []
        end = 0
        for link in re.finditer(r"\[([^\]]+)\]\((https://[^\s)]+)\)", paragraph):
            pieces.append(html.escape(paragraph[end : link.start()]))
            pieces.append(
                f'<a target="_blank" rel="noopener noreferrer" href="{html.escape(link[2], quote=True)}">{html.escape(link[1])}</a>'
            )
            end = link.end()
        pieces.append(html.escape(paragraph[end:]))
        rendered.append('<p class="explanation">' + "".join(pieces) + "</p>")
    return "".join(rendered)


def gallery(results: list[tuple[Example, Path, str]], output: Path) -> None:
    sections = []
    for example, svg, error in results:
        label = html.escape(example.heading)
        location = html.escape(f"{example.path}:{example.line}")
        explanation = paragraphs(example.prose)
        if error:
            picture = f'<p class="error">Échec du rendu : {html.escape(error)}</p>'
        else:
            encoded = base64.b64encode(svg.read_bytes()).decode("ascii")
            picture = f'<img alt="{label}" src="data:image/svg+xml;base64,{encoded}">'
        sections.append(
            f"<section><h2>{label}</h2>{explanation}{picture}"
            f"{paragraphs(example.after)}"
            f"<details><summary>Source Mermaid</summary><p>{location}</p><pre><code>"
            f"{html.escape(example.source)}</code></pre></details></section>"
        )
    output.write_text(
        '<!doctype html><html lang="fr"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Regards nouveaux avec Mermaid</title><style>"
        "body{background:#000;color:#fff;font:16px system-ui;margin:0 auto;"
        "max-width:1400px;padding:32px}section{padding:24px 0;border-top:1px solid #51576d}"
        "img{display:block;max-width:100%;max-height:650px;width:auto;height:auto;margin:24px 0}"
        "a{color:#8caaee}"
        "pre{overflow:auto;padding:16px;background:#181818}summary{cursor:pointer}"
        ".error{color:#e78284}.explanation{white-space:pre-line;line-height:1.5}"
        "h2{font-size:24px}</style><h1>Regards nouveaux avec Mermaid</h1>"
        + "\n".join(sections)
        + "</html>\n",
        encoding="utf-8",
    )


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def rendered_files(results: list[tuple[Example, Path, str]]) -> list[str]:
    """The SVG of each example that rendered, which a failure still answers."""
    return [str(svg) for _, svg, error in results if not error]


def render(args: argparse.Namespace) -> dict[str, Any]:
    """Render every example, then answer with the files written, or fail on
    each example that did not render."""
    if args.width < 1:
        raise UsageError("--width must be positive")
    try:
        examples = [example for path in args.files for example in extract(path)]
    except (OSError, ValueError) as error:
        raise ScriptError(str(error)) from None
    if not examples:
        raise UsageError("No Mermaid fenced blocks found")
    if shutil.which(args.mmdc) is None:
        raise ScriptError(
            f"Mermaid CLI not found: {args.mmdc}; install it as SKILL.md's "
            "Render and verify section says, or pass --mmdc /path/to/mmdc"
        )
    output = args.output.resolve()
    results: list[tuple[Example, Path, str]] = []
    try:
        output.mkdir(parents=True, exist_ok=True)
        for index, example in enumerate(examples, 1):
            stem = f"{index:03d}-{example.path.stem}-L{example.line}"
            source = output / f"{stem}.mmd"
            svg = output / f"{stem}.svg"
            source.write_text(example.source, encoding="utf-8")
            svg.unlink(missing_ok=True)
            try:
                rendered = subprocess.run(
                    [
                        args.mmdc,
                        "-i",
                        str(source),
                        "-o",
                        str(svg),
                        "-t",
                        "dark",
                        "-b",
                        "#000000",
                        "-w",
                        str(args.width),
                    ]
                    + (["-c", str(args.config)] if args.config else []),
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                raise ScriptError(
                    f"{example.path}:{example.line}: mmdc timed out after "
                    f"{TIMEOUT} seconds; check that mmdc renders a small diagram, "
                    "then run this command again",
                    report={"files": rendered_files(results)},
                ) from None
            error = ""
            if rendered.returncode or not svg.is_file():
                error = (rendered.stderr or rendered.stdout).strip() or "No SVG output"
            results.append((example, svg, error))
            if error:
                print(f"FAIL {example.path}:{example.line} -> {svg}", file=sys.stderr)
                print(error, file=sys.stderr)
            else:
                log.info("PASS %s:%s -> %s", example.path, example.line, svg)
        if args.gallery:
            gallery(results, output / "index.html")
    except OSError as error:
        raise ScriptError(
            str(error), report={"files": rendered_files(results)}
        ) from None
    failed = [
        f"{example.path}:{example.line}: did not render: "
        f"{first_line(error).rstrip(':')}; fix the cause in mmdc's message "
        "above, then run this command again"
        for example, _, error in results
        if error
    ]
    files = rendered_files(results)
    if args.gallery:
        files.append(str(output / "index.html"))
    if failed:
        # The examples that rendered stay inspectable
        raise ScriptError(*failed, report={"files": files})
    return {"files": files}


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(exit_codes=EXIT_CODES, description=__doc__, epilog=EPILOG)
    parser.add_argument("files", nargs="+", type=Path, help="Markdown input files")
    parser.add_argument("--output", required=True, type=Path, help="Artifact directory")
    parser.add_argument("--mmdc", default="mmdc", help="Mermaid CLI executable path")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets/theme.json",
        help="Mermaid JSON configuration file (default: bundled assets/theme.json)",
    )
    parser.add_argument(
        "--width", type=int, default=1400, help="Render width in pixels (default: 1400)"
    )
    parser.add_argument(
        "--gallery", action="store_true", help="Write offline index.html"
    )
    return run_script(parser, render, argv)


if __name__ == "__main__":
    raise SystemExit(main())

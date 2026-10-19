# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.63.0"]
# ///
"""Turn a Mermaid sequence diagram into pages and images for a reader, such as a client.

Reads one .mmd file that holds a sequence diagram. Writes four files beside it,
or in --output: <stem>-claire.html and <stem>-sombre.html, two self-contained
pages in Canadian French with the light and the dark theme of assets/, then a
JPEG of each page, 1920 pixels wide at twice the pixel density.

Each page holds pele reduced to sequence diagrams and draws the diagram in the
reader's browser, so pele measures the text with the font the browser shows.
The page title comes from --title, else the title of the source's front matter,
else the file name. The rest of the front matter, such as a Mermaid config,
stays out of the page. The legend lists only the marks the diagram uses: phase
notes, decisions that start with 🔷, ⛔ break frames, and ✅ notes.

Checks the diagram with render_diagrams.py first, so it loads the same pele:
the current folder's project, or else the one in ~/.cache/pele.

Answers in one JSON line. A success prints {"ok":true,"pele":{...},"files":[...]}
on stdout: the pele version and folder, then each file written. A failure
leaves stdout empty, and the last stderr line lists each problem under "errors",
a diagram error as file:line:column: code: message.
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

import html
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

EPILOG = """\
Without a Chromium on PATH, the images need Playwright's own:
  uv run --with playwright==1.63.0 playwright install chromium

examples:
  uv run scripts/render_pages.py process.mmd
  uv run scripts/render_pages.py process.mmd --title "Handle a request" --actor CLIENT
  uv run scripts/render_pages.py process.mmd --output /tmp/pages"""

EXIT_CODES = exit_codes(
    {
        1: "the diagram did not render or is not a sequence diagram, "
        "or node, pnpm, pele, or a browser is missing"
    }
)
HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
RENDER = HERE / "render_diagrams.py"
ESBUILD = "esbuild@0.25.12"
# One diagram bundles and draws in seconds, so these only stop a hung tool
TIMEOUT = 120
DRAW_TIMEOUT = 30
WIDTH = 1920
THEMES = {"claire": "light", "sombre": "dark"}

log = logging.getLogger("render_pages")

FRONT_MATTER = re.compile(r"\A---\n(.*?\n)?---\n", re.DOTALL)
MESSAGE = re.compile(r"^\s*(\w+)\s*(?:<<)?--?(?:>>|>|x|\))[+-]?\s*(\w+)\s*:\s*(.+)$")
BR = "<br/>"

DRAW = """
document.fonts.ready.then(() => {
  const figure = document.querySelector(".diagram");
  try {
    // The computed font follows the reader's settings, such as a Firefox that blocks page fonts
    figure.innerHTML = pele.render(SOURCE, { fontFamily: getComputedStyle(figure).fontFamily }).svg;
  } catch (error) {
    figure.textContent = String(error);
    return;
  }
  const mark = (selector, prefix, name) => {
    for (const node of figure.querySelectorAll(selector)) {
      if (node.textContent.trim().startsWith(prefix)) node.classList.add(name);
    }
  };
  mark(".pele-note", "✅", "is-yes");
  mark(".pele-edge-label", "🔷", "is-decision");
});
"""


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    log.info("running %s", shlex.join(command))
    try:
        return subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
    except FileNotFoundError:
        raise ScriptError(
            f"{command[0]} not found; install it, then run this command again"
        ) from None
    except subprocess.TimeoutExpired:
        raise ScriptError(
            f"{shlex.join(command[:3])} did not finish within {TIMEOUT} seconds; "
            "run this command again"
        ) from None


def split_self_message(line: str) -> str:
    """Pele draws a label of three lines or more on a message to oneself over the
    next message, so such a label becomes two lines of about equal length."""
    message = MESSAGE.match(line)
    if not message or message[1] != message[2] or message[3].count(BR) < 2:
        return line
    words = message[3].replace(BR, " ").split()
    if len(words) < 2:
        return line
    half = len(" ".join(words)) / 2
    cut = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - half))
    return line[: message.start(3)] + " ".join(words[:cut]) + BR + " ".join(words[cut:])


def parse(
    source: Path, text: str, title: str | None, actors: Sequence[str]
) -> tuple[str, str]:
    """The page title and the diagram the page draws, without the front matter."""
    text = text.replace("\r\n", "\n")
    front = FRONT_MATTER.match(text)
    matter = (front[1] or "") if front else ""
    found = re.search(r"^title:\s*(.+?)\s*$", matter, re.MULTILINE)
    heading = title or (found[1].strip("\"'") if found else source.stem)
    body = text[front.end() if front else 0 :].strip("\n")
    lines = [split_self_message(line) for line in body.splitlines()]
    for actor in actors:
        declared = re.compile(rf"^(\s*)participant(\s+{re.escape(actor)}\b)")
        index = next((i for i, line in enumerate(lines) if declared.match(line)), None)
        if index is None:
            raise UsageError(
                f"--actor {actor}: {source} has no `participant {actor}` line; "
                "pass the ID of a declared participant"
            )
        lines[index] = declared.sub(r"\1actor\2", lines[index], count=1)
    return heading, "\n".join(lines) + "\n"


def check(source: Path) -> dict[str, Any]:
    """Render the source in node through render_diagrams.py; return the pele it used.
    The browser draws the page's version of the diagram later, and fails the run
    if that version does not draw."""
    done = run([sys.executable, str(RENDER), str(source)])
    lines = (done.stdout or done.stderr).strip().splitlines()
    try:
        reply = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        raise ScriptError(
            f"{RENDER.name} gave no answer; run `uv run {RENDER} {source}` to see why",
            detail=done.stderr.strip(),
        ) from None
    if not reply["ok"]:
        raise ScriptError(*reply["errors"])
    kind = reply["diagrams"][0]["type"]
    if kind != "sequence":
        raise ScriptError(
            f"{source} holds a {kind} diagram; render_pages.py draws sequence diagrams only, "
            f"so render it with {RENDER.name}"
        )
    return reply["pele"]


def bundle(pele: str) -> str:
    """Pele reduced to sequence diagrams, as a script that defines the global `pele`."""
    with tempfile.TemporaryDirectory() as tmp:
        entry, out = Path(tmp, "entry.mjs"), Path(tmp, "pele.js")
        core = json.dumps(f"{pele}/dist/esm/core.js")
        sequence = json.dumps(f"{pele}/dist/esm/diagrams/sequence.js")
        entry.write_text(
            f"import {{ register, render }} from {core};\n"
            f"import sequence from {sequence};\n"
            "register(sequence);\nexport { render };\n",
            encoding="utf-8",
        )
        done = run(
            [
                "pnpm",
                "dlx",
                ESBUILD,
                str(entry),
                "--bundle",
                "--minify",
                "--format=iife",
            ]
            + ["--global-name=pele", "--legal-comments=inline", f"--outfile={out}"]
        )
        if done.returncode:
            raise ScriptError(
                f"esbuild could not bundle {pele}; run `pnpm dlx {ESBUILD} --version` "
                "to check that pnpm can fetch it",
                detail=done.stderr.strip(),
            )
        script = out.read_text(encoding="utf-8")
    if "</script" in script.lower():
        raise ScriptError(
            f"the pele bundle holds </script>, which would end the page's script; "
            f"try another pele than {pele}"
        )
    return script


def legend(diagram: str) -> str:
    marks = (
        (
            re.search(r"^\s*(?i:note)\b[^:]*:\s*PHASE\b", diagram, re.MULTILINE),
            '<span class="swatch phase"></span>Bandeau de phase',
        ),
        ("🔷" in diagram, '<span class="swatch decision">🔷</span>Point de décision'),
        (
            "⛔" in diagram,
            '<span class="swatch no"></span>⛔ Non : le parcours sort ou reprend ailleurs',
        ),
        (
            "✅" in diagram,
            '<span class="swatch yes"></span>✅ Oui : le parcours continue',
        ),
    )
    items = [f"<li>{item}</li>\n" for found, item in marks if found]
    return f'<ul class="legend">\n{"".join(items)}</ul>' if items else ""


def as_js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def page(theme: str, title: str, diagram: str, script: str) -> str:
    label = html.escape(title)
    css = "".join(
        (ASSETS / name).read_text(encoding="utf-8")
        for name in (f"theme-{theme}.css", "page.css")
    )
    numbered = (
        " numérotée" if re.search(r"^\s*autonumber\b", diagram, re.MULTILINE) else ""
    )
    return f"""<!doctype html>
<html lang="fr-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="{theme}">
<title>{label}</title>
<style>
{css}</style>
</head>
<body class="pele-page">
<header>
<h1>{label}</h1>
<p class="read">Lire de haut en bas. Chaque colonne est un acteur, chaque flèche{numbered} est une étape.</p>
{legend(diagram)}
</header>
<main>
<noscript><p>Cette page dessine son diagramme avec JavaScript. Activez-le pour le voir.</p></noscript>
<figure class="diagram" aria-label="{label}"></figure>
</main>
<script>{script}</script>
<script>
const SOURCE = {as_js(diagram)};
{DRAW}</script>
</body>
</html>
"""


def browser_path() -> str | None:
    """A Chromium already installed, or None for Playwright's own."""
    names = ("chromium", "chromium-browser", "google-chrome")
    found = next((path for path in map(shutil.which, names) if path), None)
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    return found or (str(chrome) if chrome.exists() else None)


def shoot(pages: Sequence[Path]) -> list[Path]:
    """A JPEG beside each page, WIDTH CSS pixels wide at twice the pixel density."""
    images: list[Path] = []
    with sync_playwright() as playwright:
        executable = browser_path()
        try:
            browser = playwright.chromium.launch(executable_path=executable)
        except PlaywrightError as error:
            first = str(error).strip().splitlines()[0]
            raise ScriptError(
                f"cannot start chromium: {first}; "
                "run: uv run --with playwright==1.63.0 playwright install chromium"
            ) from None
        try:
            tab = browser.new_page(
                viewport={"width": WIDTH, "height": 900}, device_scale_factor=2
            )
            for path in pages:
                tab.goto(path.resolve().as_uri())
                try:
                    tab.wait_for_selector(".diagram svg", timeout=DRAW_TIMEOUT * 1000)
                except PlaywrightError:
                    shown = tab.inner_text(".diagram").strip()[:300]
                    raise ScriptError(
                        f"{path}: the diagram did not draw ({shown or 'no message'}); "
                        "open the page in a browser to see why"
                    ) from None
                image = path.with_suffix(".jpg")
                tab.screenshot(path=image, type="jpeg", quality=90, full_page=True)
                images.append(image)
                log.info("wrote %s", image)
        finally:
            browser.close()
    return images


def render(args: argparse.Namespace) -> dict[str, Any]:
    source: Path = args.file
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        raise ScriptError(
            f"{source}: {error.strerror}; check the path, then run this command again"
        ) from None
    title, diagram = parse(source, text, args.title, args.actor)
    pele = check(source)
    script = bundle(pele["path"])
    out: Path = args.output or source.parent
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ScriptError(
            f"{out}: {error.strerror}; pass a writable folder to --output"
        ) from None
    pages: list[Path] = []
    for suffix, theme in THEMES.items():
        path = out / f"{source.stem}-{suffix}.html"
        path.write_text(page(theme, title, diagram, script), encoding="utf-8")
        pages.append(path)
        log.info("wrote %s", path)
    images = shoot(pages)
    return {"pele": pele, "files": [str(path) for path in (*pages, *images)]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(exit_codes=EXIT_CODES, description=__doc__, epilog=EPILOG)
    parser.add_argument("file", type=Path, help="the .mmd file of one sequence diagram")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="folder for the pages and images (default: the folder of the .mmd file)",
    )
    parser.add_argument(
        "--title",
        help="page title (default: the front matter's title, else the file name)",
    )
    parser.add_argument(
        "--actor",
        action="append",
        default=[],
        metavar="ID",
        help="draw this participant as a person; repeat it for several",
    )
    return run_script(parser, render, argv, debug="RENDER_PAGES_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

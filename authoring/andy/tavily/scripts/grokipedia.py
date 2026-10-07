# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx>=0.27",
# ]
# ///
"""
Search Grokipedia.com using Tavily API and write the results to a Markdown file.

Usage:
    uv run grokipedia.py "quantum computing"
    uv run grokipedia.py "Italian cuisine" --max-results 10
    uv run grokipedia.py "AI history" --raw
    uv run grokipedia.py "neural networks" --output notes/neural-networks.md
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

import subprocess
import tempfile
from pathlib import Path

import httpx

__version__ = "0.2.0"

TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
GROKIPEDIA_BASE = "https://grokipedia.com/page"
SEARCH_DOMAINS = ["grokipedia.com", "grokxpedia.us"]
KEYRING_GET = "chezmoi secret keyring get --service=tavily --user=api_key"
KEYRING_SET = "chezmoi secret keyring set --service=tavily --user=api_key"

EPILOG = """\
The results go to a Markdown file: the --output path, or a new
grokipedia-<query>-*.md file in the system temp directory ($TMPDIR, else /tmp).
The answer is one JSON line on stdout, {"ok":true,"file":"/abs/path.md"}; a
failure leaves stdout empty and ends stderr with {"ok":false,"errors":[...]}.

examples:
  uv run grokipedia.py "quantum physics"
  uv run grokipedia.py "Italian cuisine" -n 10
  uv run grokipedia.py "AI history" --raw
  uv run grokipedia.py "neural networks" --output notes/neural-networks.md"""

EXIT_CODES = exit_codes(
    {0: "the results file was written", 1: "the key lookup, search, or write failed"}
)

log = logging.getLogger("grokipedia")


class ApiKeyError(ScriptError):
    """Raised when the Tavily API key cannot be retrieved."""


def get_api_key() -> str:
    """Retrieve Tavily API key from macOS keyring via chezmoi.

    Returns:
        The API key string, stripped of whitespace.

    Raises:
        ApiKeyError: If chezmoi is missing, keyring lookup fails, or key is empty.
    """
    try:
        result = subprocess.run(
            [
                "chezmoi",
                "secret",
                "keyring",
                "get",
                "--service=tavily",
                "--user=api_key",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        key = result.stdout.strip()
        if not key:
            raise ApiKeyError(
                f"Tavily API key from keyring is empty; set it with: {KEYRING_SET}"
            )
        return key
    except FileNotFoundError as exc:
        raise ApiKeyError(
            "chezmoi not found in PATH; install chezmoi: https://www.chezmoi.io/install/"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ApiKeyError(
            f"Could not retrieve Tavily API key from keyring; set it with: {KEYRING_SET}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ApiKeyError(
            f"Tavily API key lookup timed out; check the keyring with: {KEYRING_GET}"
        ) from exc


def search_grokipedia(
    query: str,
    max_results: int = 5,
    include_raw: bool = False,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Search grokipedia.com using Tavily API with include_domains filter.

    Args:
        query: Search query string.
        max_results: Maximum number of results (1-20).
        include_raw: Whether to include raw page content.
        api_key: Tavily API key. If None, retrieved from keyring via get_api_key().

    Returns:
        Tavily API response as a dictionary.

    Raises:
        ApiKeyError: If api_key is None and keyring lookup fails.
        httpx.HTTPStatusError: On non-2xx response.
        httpx.RequestError: On connection/timeout failure.
    """
    if api_key is None:
        api_key = get_api_key()

    payload = {
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": include_raw,
        "include_domains": SEARCH_DOMAINS,
        "topic": "general",
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            TAVILY_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def normalize_page_title(query: str) -> str:
    """Convert a search query to a Grokipedia URL path segment.

    Follows MediaWiki URL conventions: first letter capitalized,
    spaces replaced with underscores, interior casing preserved.

    Args:
        query: Raw search query string.

    Returns:
        URL-ready page title (e.g., "quantum computing" -> "Quantum_computing").
    """
    title = query.strip()
    if not title:
        return ""
    # Collapse multiple spaces, replace with underscores
    parts = title.split()
    title = "_".join(parts)
    # Capitalize first letter only, preserve the rest
    return title[0].upper() + title[1:]


def extract_exact_page(
    query: str,
    api_key: str | None = None,
) -> dict[str, Any] | None:
    """Try to extract the canonical Grokipedia page matching the query.

    Constructs the URL ``grokipedia.com/page/{Title}`` and uses Tavily's
    /extract endpoint. Returns a search-result-compatible dict if the page
    exists, or None on any failure.

    Args:
        query: Search query to derive the page title from.
        api_key: Tavily API key. If None, retrieved from keyring.

    Returns:
        A dict with keys (title, url, content, score, raw_content) or None.
    """
    if api_key is None:
        api_key = get_api_key()

    title = normalize_page_title(query)
    if not title:
        return None

    canonical_url = f"{GROKIPEDIA_BASE}/{title}"

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                TAVILY_EXTRACT_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"urls": [canonical_url], "format": "markdown"},
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        raw_content = results[0].get("raw_content") or ""
        # Build a snippet from the first 500 chars of the page
        snippet = raw_content[:500] + "..." if len(raw_content) > 500 else raw_content

        return {
            "title": title.replace("_", " "),
            "url": canonical_url,
            "content": snippet,
            "score": 1.0,  # exact match
            "raw_content": raw_content,
        }

    except (httpx.HTTPStatusError, httpx.RequestError) as error:
        log.info("exact page lookup failed for %s: %s", canonical_url, error)
        return None


def render_markdown(data: dict[str, Any], raw: bool = False) -> str:
    """Render search results as a Markdown document.

    Args:
        data: Tavily API response dictionary.
        raw: Whether to include raw page content.

    Returns:
        The Markdown text, ending with a newline.
    """
    query = data.get("query") or "Unknown"
    summary = data.get("answer")
    results = data.get("results") or []

    lines = [
        f"# Grokipedia search: {query}",
        "",
        f"Domains: {', '.join(SEARCH_DOMAINS)}",
        "",
    ]
    if summary:
        lines += ["## AI summary", "", summary, ""]

    if not results:
        lines += ["No results found on grokipedia.com.", ""]
        return "\n".join(lines)

    lines += [f"## Results ({len(results)})", ""]
    for i, result in enumerate(results, 1):
        title = result.get("title") or "No title"
        url = result.get("url") or ""
        content = result.get("content") or ""
        score = result.get("score")

        lines += [f"### {i}. {title}", ""]
        if url:
            lines.append(f"- URL: {url}")
        lines += [f"- Relevance: {'N/A' if score is None else f'{score:.2f}'}", ""]
        if content:
            lines += [content, ""]

        raw_content = result.get("raw_content") or ""
        if raw and raw_content:
            lines += ["#### Raw content", "", raw_content, ""]

    return "\n".join(lines)


def write_results(markdown: str, query: str, output: str | None = None) -> Path:
    """Write the results to `output`, or to a new file in the system temp directory.

    Returns:
        The absolute path of the file written.
    """
    if output is not None:
        path = Path(output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        return path
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:60] or "search"
    handle, name = tempfile.mkstemp(prefix=f"grokipedia-{slug}-", suffix=".md")
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(markdown)
    return Path(name).resolve()


def http_failure(response: httpx.Response) -> str:
    """The error message for a non-2xx answer from Tavily, with what to do next."""
    status = response.status_code
    if status in (401, 403):
        return f"Tavily API returned HTTP {status}; verify the API key: {KEYRING_GET}"
    if status == 429:
        return "Tavily API returned HTTP 429, rate limited; wait a moment, then rerun the search"
    body = " ".join(response.text[:200].split())
    return f"Tavily API returned HTTP {status}: {body}; rerun the search later"


def search(args: argparse.Namespace) -> dict[str, Any]:
    """Run the search, write the results file, and return the data beside `ok`."""
    query = args.query.strip()
    if not query:
        raise UsageError("query must not be empty; pass search terms in quotes")
    if args.max_results < 1 or args.max_results > 20:
        raise UsageError(f"--max-results must be 1-20, got {args.max_results}")

    api_key = get_api_key()
    try:
        data = search_grokipedia(
            query=query,
            max_results=args.max_results,
            include_raw=args.raw,
            api_key=api_key,
        )
    except httpx.HTTPStatusError as error:
        raise ScriptError(http_failure(error.response)) from error
    except httpx.RequestError as error:
        raise ScriptError(
            f"Could not reach Tavily API: {error}; check the internet connection, "
            "then rerun the search"
        ) from error
    log.info("Tavily answered in %ss", data.get("response_time"))

    # Hybrid lookup: if the canonical page isn't in search results,
    # try extracting it directly and prepend it.
    title = normalize_page_title(query)
    canonical_url = f"{GROKIPEDIA_BASE}/{title}"
    results = data["results"] = data.get("results") or []
    existing_urls = {(r.get("url") or "").lower() for r in results}

    if canonical_url.lower() not in existing_urls:
        exact = extract_exact_page(query, api_key=api_key)
        if exact is not None:
            log.info("added the exact page %s", canonical_url)
            results.insert(0, exact)

    try:
        path = write_results(render_markdown(data, raw=args.raw), query, args.output)
    except OSError as error:
        raise ScriptError(
            f"Could not write the results: {error}; pass --output with a writable file path"
        ) from error
    return {"file": str(path)}


def build_parser() -> Parser:
    """The command line parser; its help is the flag reference."""
    parser = Parser(
        prog="grokipedia.py",
        description="Search Grokipedia.com using the Tavily API and write the results "
        "to a Markdown file.",
        epilog=EPILOG,
        exit_codes=EXIT_CODES,
    )
    parser.add_argument("query", help="search query, such as 'quantum computing'")
    parser.add_argument(
        "-n",
        "--max-results",
        type=int,
        default=5,
        help="maximum number of results, 1-20 (default: 5)",
    )
    parser.add_argument(
        "--raw", action="store_true", help="include each page's raw content"
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="write the results to FILE (default: a new file in the system temp directory)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point: answer every outcome in one JSON line.

    Returns:
        Exit code: 0 success, 1 runtime error, 2 usage error, 130 or 143 interrupted.
    """
    return run_script(build_parser(), search, argv, debug="GROKIPEDIA_DEBUG")


if __name__ == "__main__":
    sys.exit(main())

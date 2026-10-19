#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Serve the live brigade dashboard: the replay page of the runs in T3 now, with an open end."""

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

import http.server
import math
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import github
import pipeline
import privacy
import statuses
import t3

HERE = Path(__file__).resolve().parent
POLL, GITHUB_EVERY = pipeline.POLL, pipeline.GITHUB_EVERY
# with no new event the page still moves on: a Cook idles 120 s after its turn
CLOCK_EVERY = 10.0
PAGE_POLL_MS = 1000  # how often the page asks for new data
LAGS = 200  # recent T3 lags kept for /healthz
OWN_FILES = ("*.py", "page.html", "board.js")


def own_files() -> dict[str, tuple[int, int]]:
    """This service's code. A deploy that changes it stops the service, and
    systemd starts the new code."""
    found = {}
    try:
        for pattern in OWN_FILES:
            for path in sorted(HERE.glob(pattern)):
                info = path.stat()
                found[path.name] = (info.st_mtime_ns, info.st_size)
    except OSError:
        return {}  # a deploy is replacing the files: they changed
    return found


def clock(t: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(t))


@dataclass
class Failure:
    """A source that stopped reading: since when, and its last message."""

    since: float
    message: str


@dataclass(frozen=True)
class Published:
    """One version of the page data, replaced whole, so a reader never mixes two."""

    version: int = 0
    data: dict = field(default_factory=lambda: {"generated": "", "brigades": []})
    private: dict[str, str] = field(default_factory=dict)
    body: bytes = b'{"generated":"","brigades":[]}'
    seq: int = 0
    unparsed: int = 0


@dataclass
class State:
    """What the dashboard serves: the last good page data and how the last reads went.

    The poll loop writes it and the HTTP threads read it; `published` is
    replaced whole, so a reader takes it once and sees one version.
    """

    published: Published = field(default_factory=Published)
    # when the published data last matched T3: the age the page shows
    read: float | None = None
    # t3, github (the open items' refresh), github_new (items a page needs first), page
    failures: dict[str, Failure] = field(default_factory=dict)
    github_read: float | None = None
    github_queries: list[float] = field(default_factory=list)
    # seconds from a T3 event to the data that shows it
    lags: list[float] = field(default_factory=list)

    def error(self) -> str | None:
        """The banner's words for each source that stopped; the data stays."""
        words = {
            "t3": "T3 read failed",
            "github": "GitHub read failed",
            "github_new": "GitHub read failed",
            "page": "The page could not be rebuilt",
        }
        parts = [
            f"{words[k]} since {clock(f.since)}: {f.message}"
            for k, f in list(self.failures.items())
        ]
        return ". ".join(parts) + "; showing the last good data" if parts else None

    def answer(self, since: str | None) -> bytes:
        """/data.json: its age always, and the data when the page's version is older."""
        p = self.published
        head = json.dumps(
            {"version": p.version, "read": self.read, "error": self.error()},
            separators=(",", ":"),
        )
        if since == str(p.version):
            return head.encode()
        return head[:-1].encode() + b',"data":' + p.body + b"}"

    def health(self, now: float) -> tuple[bool, dict]:
        p = self.published
        age = None if self.read is None else round(now - self.read, 1)
        ok = "t3" not in self.failures and age is not None and age <= 3 * POLL
        failure = {k: f.message for k, f in list(self.failures.items())}
        return ok, {
            "ok": ok,
            "seq": p.seq,
            "age": age,
            "unparsed": p.unparsed,
            "version": p.version,
            "lag_p95": pipeline.p95(self.lags),
            "github": {
                "age": None
                if self.github_read is None
                else round(now - self.github_read, 1),
                "query_p95": pipeline.p95(self.github_queries),
            },
            "errors": failure,
        }


class Service:
    """Reads T3 and GitHub on its cadence and publishes the page data to `state`."""

    def __init__(
        self, con: sqlite3.Connection, gh: github.Cached, days: float, state: State
    ) -> None:
        self.follower = t3.Follower(
            con, lambda: pipeline.t3_time(time.time() - days * 86400)
        )
        self.gh, self.state = gh, state
        self.code = own_files()
        self.github_at = -math.inf
        self.computed = -math.inf
        self.pending = False  # T3 changed since the data last published

    def tick(self, now: float) -> str | None:
        """One poll; returns why the service must stop, or None."""
        if own_files() != self.code:
            return "its code changed"
        fresh, repos, t3_ok = False, set(), False
        try:
            if self.follower.changed():
                before = self.follower.snap.time
                repos = self.follower.read()
                fresh = self.follower.snap.time != before  # a followed run changed
            self.pending = self.pending or fresh
            self.state.failures.pop("t3", None)
            t3_ok = True
        except Exception as error:  # noqa: BLE001 - any read failure keeps the last good data
            self.failed("t3", now, error)
        due = now - self.github_at >= GITHUB_EVERY
        refreshed = False
        if due or repos:
            try:
                started = time.perf_counter()
                queries = self.gh.refresh(None if due else repos)
                if queries:
                    took = (time.perf_counter() - started) / queries
                    self.state.github_queries = (self.state.github_queries + [took])[
                        -LAGS:
                    ]
                if due:
                    self.github_at = now
                self.state.github_read, refreshed = now, True
                self.state.failures.pop("github", None)
            except github.ReadError as error:
                self.failed("github", now, error)
        if self.pending or refreshed or now - self.computed >= CLOCK_EVERY:
            self.compute(now, self.pending)
        if t3_ok and not self.pending:
            self.state.read = now
        return None

    def failed(self, source: str, now: float, error: BaseException) -> None:
        logging.getLogger(__name__).debug("%s failed", source, exc_info=error)
        old = self.state.failures.get(source)
        message = getattr(error, "detail", None) or str(error) or type(error).__name__
        self.state.failures[source] = Failure(old.since if old else now, message)

    def compute(self, now: float, fresh: bool) -> None:
        """The page from scratch: the snapshot's runs through the replay's pipeline."""
        snap, heads = self.follower.snap, self.follower.heads
        disk = {h[-4:].lower(): t3.disk_plans(h[-4:].lower()) for h in heads}
        try:
            heads, events = pipeline.run_events(snap, self.gh, heads, disk)
            data, private = pipeline.page_of(events, self.gh, heads, now)
            if privacy.leaks(data, private):
                raise pipeline.PrivacyError("the privacy check refused the new data")
        except github.ReadError as error:
            return self.failed("github_new", now, error)
        except Exception as error:  # noqa: BLE001 - a bug on live data keeps the last good page
            return self.failed("page", now, error)
        found = pipeline.unparsed(events)
        first = self.state.published.version == 0
        self.state.published = Published(
            version=self.state.published.version + 1,
            data=data,
            private=private,
            body=json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(),
            seq=snap.seq,
            unparsed=len(found["messages"]) + len(found["watch"]),
        )
        self.state.failures.pop("page", None)
        self.state.failures.pop("github_new", None)
        self.pending = False
        if fresh and snap.time and not first:  # the first build reads GitHub cold
            lag = time.time() - statuses.ts(snap.time)
            self.state.lags = (self.state.lags + [lag])[-LAGS:]
        self.computed = now
        try:
            self.gh.save()
        except OSError as error:
            logging.getLogger(__name__).info("Cannot save the GitHub cache: %s", error)


def handler(state: State) -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        """GET only: the page, its data, and /healthz; nothing else is served."""

        server_version = "brigade-live"

        def do_GET(self) -> None:
            url = urlsplit(self.path)
            if url.path == "/":
                p = state.published
                live = {
                    "data": "data.json",
                    "poll": PAGE_POLL_MS,
                    "version": p.version,
                    "read": state.read,
                    "error": state.error(),
                }
                try:
                    page = pipeline.render_page(p.data, p.private, live)
                except pipeline.PrivacyError:
                    return self.send(
                        "text/plain; charset=utf-8",
                        b"Privacy check refused the data\n",
                        500,
                    )
                return self.send("text/html; charset=utf-8", page.encode())
            if url.path == "/data.json":
                since = parse_qs(url.query).get("v", [None])[0]
                return self.send("application/json", state.answer(since))
            if url.path == "/healthz":
                ok, body = state.health(time.time())
                return self.send(
                    "application/json", json.dumps(body).encode(), 200 if ok else 503
                )
            self.send("text/plain; charset=utf-8", b"Not found\n", 404)

        def send(self, kind: str, body: bytes, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            logging.getLogger(__name__).debug(
                "%s %s", self.address_string(), format % args
            )

    return Handler


def work(args: argparse.Namespace) -> dict:
    try:
        con = t3.connect(args.db, args.timeout)
    except t3.DatabaseError as error:
        raise ScriptError(str(error)) from error
    # autocommit: a read transaction lives only inside Follower.read
    con.isolation_level = None
    state = State()
    cache = Path(args.cache).expanduser()
    service = Service(
        con, github.Cached(github.gh_reader(args.timeout), cache), args.days, state
    )
    try:
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", args.port), handler(state)
        )
    except OSError as error:
        raise ScriptError(
            f"cannot listen on 127.0.0.1:{args.port}: {error.strerror}; pass a free --port"
        ) from error
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, name="http", daemon=True)
    thread.start()
    log = logging.getLogger(__name__)
    log.info("Serving http://127.0.0.1:%d/", server.server_address[1])
    try:
        while True:
            started = time.monotonic()
            reason = service.tick(time.time())
            if reason:
                log.info("Stopping: %s", reason)
                return {"stopped": reason, "seq": state.published.seq}
            time.sleep(max(0.0, POLL - (time.monotonic() - started)))
    finally:
        server.shutdown()
        server.server_close()
        con.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        prog="live.py",
        description=__doc__,
        exit_codes=exit_codes({}),
        epilog="""The page is the replay's, built by the same extractor from T3's events as
they arrive, with an open end: it follows now and shows how old its data is.
Every 2 s the service asks T3 whether its database changed, through a
read-only connection that holds no read transaction between polls. GitHub's
merged and closed items stay cached; open ones are read again in one query per
repository every 60 s, or when T3 sees a linked PR change state. A read that
fails keeps the last good data and says so on the page.

GET /          the dashboard page
GET /data.json the page data and its age; ?v=<version> omits unchanged data
GET /healthz   last sequence, data age, unparsed message count; 503 when stale

The service stops with exit 0 when one of its own files changes, so a
service manager that restarts it, such as systemd with Restart=always, runs
the new code. It listens on 127.0.0.1 only.

examples:
  uv run scripts/replay/live.py
  uv run scripts/replay/live.py --port 4180 --days 7 -v""",
    )
    parser.add_argument(
        "--db",
        default="~/.t3/userdata/statev2.sqlite",
        help="T3 SQLite database, opened read-only (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4178,
        help="port on 127.0.0.1 (default: %(default)s)",
    )
    parser.add_argument(
        "--days",
        type=float,
        default=2.0,
        help="show Head Chefs created in the last N days (default: %(default)s)",
    )
    parser.add_argument(
        "--cache",
        default="~/.cache/brigade-live/github.json",
        help="GitHub facts kept across restarts (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=30.0,
        help="timeout per GitHub read or database lock wait (default: 30s)",
    )
    return run_script(parser, work, argv, debug="LIVE_DEBUG")


if __name__ == "__main__":
    raise SystemExit(main())

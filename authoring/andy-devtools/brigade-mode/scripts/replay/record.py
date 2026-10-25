#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Record one brigade run from T3 and GitHub as whitelisted facts, for replay without either."""

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

import gzip
import tempfile
from collections import Counter
from pathlib import Path

import github
import privacy
import t3

Ref = tuple[str, int]  # (owner/name, number)


class Recorder:
    """Builds one run's recording: records, GitHub facts and the live plan on disk."""

    def __init__(
        self, snap: t3.Snapshot, records: list[t3.Record], gh: github.GitHub, head: str
    ) -> None:
        self.snap, self.records, self.gh, self.head = snap, records, gh, head
        self.tree = set(snap.threads)
        self.names: dict[
            str, str | None
        ] = {}  # any repository name -> owner/name, or None

    # -- repositories
    def resolve(self, name: str | None) -> str | None:
        if not name:
            return None
        if name not in self.names:
            try:
                self.names[name] = self.gh.repository(name)
            except github.ReadError as error:
                if error.temporary:
                    raise
                self.names[name] = (
                    None  # a folder that is no GitHub repository, such as ~/projects
                )
        return self.names[name]

    def main_repo(self) -> str | None:
        repos = [
            self.resolve(self.snap.projects.get(item.get("project") or ""))
            for item in self.snap.items.values()
            if item.get("tool") == "launch"
        ]
        known = [r for r in repos if r]
        return max(sorted(set(known)), key=known.count) if known else None

    # -- GitHub facts the extractor reads
    def collect(self) -> None:
        main = self.main_repo()
        end = self.snap.time
        issues: list[Ref] = []
        prs: list[Ref] = []
        for item in self.snap.items.values():
            tool = item.get("tool")
            if tool == "link":
                repo = self.resolve(item["pr"][0])
                if repo:
                    prs.append((repo, item["pr"][1]))
            elif tool == "launch" and item.get("batch"):
                home = self.resolve(item["batch"].get("repo")) or self.resolve(
                    self.snap.projects.get(item.get("project") or "")
                )
                for repo, n in item["batch"]["refs"]:
                    repo = self.resolve(repo) or home
                    if repo:
                        issues.append((repo, n))
            elif item["type"] == "assistant_message":
                for refs in item["refs"]:
                    for ref in refs:
                        repo, n = ref.rsplit("#", 1)
                        repo = self.resolve(repo) or main
                        if repo:
                            self.gh.item(repo, int(n))
            watch = item.get("watch") or {}
            for slots in (watch.get("full") or {}, watch.get("blocks") or {}):
                for slot in slots.values():
                    home = self.resolve(slot.get("repo")) or main
                    for repo, n in slot.get("refs", []):
                        repo = self.resolve(repo) or home
                        if repo:
                            issues.append((repo, n))
        self.gh.load_prs(prs)
        for repo, n in prs:
            p = self.gh.prs[(repo, n)]
            p["refs"] = [[self.resolve(r) or repo, x] for r, x in p["refs"]]
            issues += [(r, x) for r, x in p["refs"]]
            for _, refs in p["refHistory"]:
                refs[:] = [[self.resolve(r) or repo, n] for r, n in refs]
                issues += [(r, n) for r, n in refs]
        seen: set[Ref] = set()
        while issues:
            ref = issues.pop(0)
            if ref in seen:
                continue
            seen.add(ref)
            issue = self.gh.issue(*ref)
            if issue is None:
                continue
            if issue["parent"]:
                issues.append((issue["parent"][0], issue["parent"][1]))
            if self.gh.is_epic(*ref):
                issues += [
                    (r, x)
                    for r, x, created in issue["subs"]
                    if created and created <= end
                ]

    # -- privacy
    def labels(self) -> dict[str, str]:
        """owner/name -> what a recording writes: the name itself, or private-<letter>."""
        known = {info["name"]: info for info in self.gh.repositories.values()}
        private = sorted(name for name, info in known.items() if not info["public"])
        out = {name: name for name, info in known.items() if info["public"]}
        out.update({name: private_label(i) for i, name in enumerate(private)})
        return out

    def rewrite(self) -> dict:
        labels = self.labels()

        def repo(name: str | None) -> str | None:
            full = self.resolve(name)
            return labels.get(full) if full else None

        def ref(text: str) -> str:
            name, n = text.rsplit("#", 1)
            return f"{repo(name) or ''}#{n}" if name else f"#{n}"

        ids: dict[str, dict[str, str]] = {
            "item": {},
            "run": {},
            "subagent": {},
            "other": {},
        }

        def short(kind: str, value: str | None) -> str | None:
            if value is None:
                return None
            if kind == "thread":
                if value in self.tree:
                    return value
                kind = "other"
            table = ids[kind]
            table.setdefault(value, f"{kind[0]}{len(table) + 1}")
            return table[value]

        def slot(raw: dict) -> dict:
            out = dict(raw)
            if "repo" in out:
                out["repo"] = repo(out["repo"])
            if "refs" in out:
                out["refs"] = [[repo(r), n] for r, n in out["refs"]]
            if "thread" in out:
                out["thread"] = short("thread", out["thread"])
            if out.get("replacedBy") not in (None, "split"):
                out["replacedBy"] = short("thread", out["replacedBy"])
            return out

        def item(data: dict) -> dict:
            out = {**data, "thread": short("thread", data["thread"])}
            tool = out.get("tool")
            if tool == "launch":
                if out.get("batch"):
                    batch = out["batch"]
                    out["batch"] = {
                        "n": batch["n"],
                        "repo": repo(batch["repo"]),
                        "refs": [[repo(r) if r else None, n] for r, n in batch["refs"]],
                    }
            elif tool == "link":
                out["pr"] = [repo(out["pr"][0]), out["pr"][1]]
            elif tool in ("send", "organize", "rename"):
                key = "to" if tool == "send" else "target"
                out[key] = short("thread", out.get(key))
            elif tool == "delegate":
                out["task"] = short("subagent", out.get("task"))
            if out["type"] == "assistant_message":
                out["refs"] = [[ref(x) for x in refs] for refs in out["refs"]]
            if out.get("watch"):
                watch = dict(out["watch"])
                for part in ("full", "blocks"):
                    if part in watch:
                        watch[part] = {name: slot(s) for name, s in watch[part].items()}
                out["watch"] = watch
            return out

        records = []
        last: dict[tuple[str, str], object] = {}
        for seq, time, kind, key, data in self.records:
            if data is None and (kind, key) not in last:
                continue  # an item type the extractor never reads
            if kind == "thread":
                data = data and {**data, "parent": short("thread", data.get("parent"))}
            elif kind == "item":
                data = data and item(data)
            elif kind in ("run", "subagent"):
                data = data and {**data, "thread": short("thread", data["thread"])}
            if last.get((kind, key), ()) == data:
                continue  # an update that changes no recorded field
            last[(kind, key)] = data
            new_key = key if kind == "thread" else short(kind, key)
            records.append([seq, time, kind, new_key, data])
        projects = sorted(
            {d["project"] for d in self.snap.threads.values() if d.get("project")}
            | {d["project"] for d in self.snap.items.values() if d.get("project")}
        )
        head = [
            [0, None, "project", pid, {"repo": repo(self.snap.projects.get(pid))}]
            for pid in projects
        ]
        facts = self.gh.dump()
        github_part = {
            "repositories": {
                labels[name]: info
                for name, info in facts["repositories"].items()
                if name in labels
            },
            "prs": {
                ref(k): {
                    **v,
                    "refs": [[repo(r), n] for r, n in v["refs"]],
                    "refHistory": [
                        [at, [[repo(r), n] for r, n in refs]]
                        for at, refs in v["refHistory"]
                    ],
                }
                for k, v in facts["prs"].items()
            },
            "issues": {
                ref(k): None
                if v is None
                else {
                    **v,
                    "parent": [repo(v["parent"][0]), v["parent"][1]]
                    if v["parent"]
                    else None,
                    "subs": [[repo(r), n, c] for r, n, c in v["subs"]],
                }
                for k, v in facts["issues"].items()
            },
            "items": {ref(k): v for k, v in facts["items"].items()},
        }
        return {
            "format": t3.FORMAT,
            "brigade": self.head[-4:].lower(),
            "head": self.head,
            "sequence": self.snap.seq,
            "records": head + records,
            "github": github_part,
            "disk": self.disk(slot),
        }

    def disk(self, slot: Callable[[dict], dict]) -> dict:
        """The run's watch.toml files while it is live; its Close removes them."""
        return {
            folder: {
                "time": info["time"],
                "plan": {name: slot(s) for name, s in info["plan"].items()},
            }
            for folder, info in t3.disk_plans(self.head[-4:].lower()).items()
        }


def private_label(index: int) -> str:
    letters = ""
    while index >= 0:
        index, remainder = divmod(index, 26)
        letters = chr(ord("A") + remainder) + letters
        index -= 1
    return "private-" + letters


def check_fold(con: t3.sqlite3.Connection, snap: t3.Snapshot) -> dict:
    """Compare the fold of the run's events with T3's own projection of its threads."""
    proj = t3.projection(con, snap.threads)
    for tid in proj.threads:
        snap.threads[tid] = {**snap.threads[tid], "title": snap.title(tid)}
    counts, mismatches = {}, []
    for name in ("threads", "items", "runs", "subagents"):
        mine, theirs = getattr(snap, name), getattr(proj, name)
        counts[name] = len(theirs)
        mismatches += [
            f"{name} {k}"
            for k in sorted(set(mine) | set(theirs))
            if t3.plain(mine.get(k)) != theirs.get(k)
        ]
    return {"counts": counts, "mismatches": mismatches}


def work(args: argparse.Namespace) -> dict:
    if args.output == "-":
        raise UsageError(
            "--output needs a file path; stdout is reserved for the JSON answer"
        )
    output = (
        Path(args.output or f"~/.cache/brigade-replay/{args.brigade}.json.gz")
        .expanduser()
        .resolve()
    )
    if output in t3.database_files(args.db):
        raise UsageError(
            f"--output {output} would overwrite T3's database; write the recording to another path"
        )
    try:
        con = t3.connect(args.db, args.timeout)
    except t3.DatabaseError as error:
        raise ScriptError(str(error)) from error
    gh = github.GitHub(github.gh_reader(args.timeout))
    try:
        heads = t3.head_chefs(con, None, [args.brigade])
        if len(heads) != 1:
            raise UsageError(
                f"--brigade {args.brigade} names {len(heads)} Head Chefs; give the last four characters of one Head Chef threadId"
            )
        con.execute(
            "begin"
        )  # one short read transaction: the fold and the projection it is checked against
        try:
            snap, records = t3.load(con, heads)
            checked = check_fold(con, snap)
        finally:
            con.execute("commit")
        if checked["mismatches"]:
            raise ScriptError(
                f"The fold of T3's events differs from its projection on {len(checked['mismatches'])} entities; rerun with --debug",
                detail="\n".join(checked["mismatches"][:20]),
            )
        recorder = Recorder(snap, records, gh, heads[0])
        recorder.collect()
        data = recorder.rewrite()
    except github.ReadError as error:
        raise (TemporaryError if error.temporary else ScriptError)(
            str(error)
        ) from error
    except t3.sqlite3.OperationalError as error:
        if "locked" in str(error).lower():
            raise TemporaryError("T3 database is busy; retry this command") from error
        raise ScriptError(
            f"Cannot read T3 events: {error}; rerun with --db PATH pointing to statev2.sqlite"
        ) from error
    finally:
        con.close()
    outside = check_recording(data)
    if outside:
        raise ScriptError(
            "The whitelist refused the recording; a reduced field kept free text or an unknown key",
            detail="\n".join(outside[:20]),
        )
    private = [name for name, info in gh.repositories.items() if not info["public"]]
    private += [info["name"] for info in gh.repositories.values() if not info["public"]]
    leaks = privacy.leaks(data, private)
    if leaks:
        raise ScriptError(
            "Privacy check refused the recording; a field outside the whitelist kept a private repository name or a local path",
            detail="\n".join(sorted(set(leaks))[:20]),
        )
    body = (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    )
    kinds = Counter(r[2] for r in data["records"])
    report = {
        "changes": [["write", str(output)]],
        "records": dict(sorted(kinds.items())),
        "checked": checked["counts"],
    }
    if args.dry_run:
        return report
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=".record-", delete=False
        ) as temporary:
            pending = Path(temporary.name)
        try:
            raw = body.encode("utf-8")
            pending.write_bytes(
                gzip.compress(raw, mtime=0) if output.suffix == ".gz" else raw
            )
            pending.replace(output)
        finally:
            pending.unlink(missing_ok=True)
    except OSError as error:
        raise ScriptError(
            f"Cannot write {output}: {error}; rerun with --output PATH in a writable directory"
        ) from error
    return report


GITHUB_KEYS = {
    "repositories": {"public"},
    "prs": {"created", "merged", "closed", "edited", "refs", "refHistory"},
    "issues": {
        *("epic", "epicTitle", "epicLabel", "closed"),
        *("parent", "subCount", "subs"),
    },
    "items": {"merged", "closed"},
}
REPO = re.compile(r"[\w.-]+/[\w.-]+|private-[A-Z]+")


def check_recording(data: dict) -> list[str]:
    """Why a recording falls outside the whitelist; empty when every field fits."""
    errors = [e for r in data["records"] for e in t3.whitelist_errors(r)]
    for part, keys in GITHUB_KEYS.items():
        for ref, facts in data["github"].get(part, {}).items():
            name = ref.rsplit("#", 1)[0] if part != "repositories" else ref
            if not REPO.fullmatch(name):
                errors.append(f"github.{part}: repository {name[:40]!r}")
            for k, v in (facts or {}).items():
                if k not in keys:
                    errors.append(f"github.{part}.{k}: key outside the whitelist")
                else:
                    errors += t3.value_errors(f"github.{part}.{ref}.{k}", v)
    for folder, info in data.get("disk", {}).items():
        if not t3.SLOT_KEY.fullmatch(folder):
            errors.append(f"disk: folder {folder[:40]!r}")
        doc = {"tool": "watch", "watch": {"full": info["plan"]}, "end": info["time"]}
        errors += t3.whitelist_errors(["disk", None, "item", folder, doc])
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        prog="record.py",
        description=__doc__,
        exit_codes=exit_codes({75: "temporary read failure, safe to retry"}),
        epilog="""A recording keeps types, times, the Messages prefixes of carpaccio, watch.toml
plan keys, PR and issue numbers and the GitHub fields the replay reads. Other
text is dropped and private repositories become private-A, private-B...; the
privacy check refuses the file otherwise. Requires gh authenticated with access
to the run's repositories (gh auth login).

examples:
  uv run scripts/replay/record.py --brigade 66ab
  uv run scripts/replay/record.py --brigade 66ab -o scripts/replay/tests/recordings/66ab.json.gz
  uv run scripts/replay/record.py --brigade 0ba0 --dry-run""",
    )
    parser.add_argument(
        "--brigade",
        required=True,
        type=brigade_id,
        metavar="ID4",
        help="the run: the last four characters of its Head Chef threadId",
    )
    parser.add_argument(
        "--db",
        default="~/.t3/userdata/statev2.sqlite",
        help="T3 SQLite database, opened read-only (default: %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="recording file, gzipped when it ends in .gz (default: ~/.cache/brigade-replay/<ID4>.json.gz)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="read and check the recording without writing it",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=30.0,
        help="timeout per GitHub read or database lock wait (default: 30s)",
    )
    return run_script(parser, work, argv, debug="RECORD_DEBUG")


def brigade_id(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9]{4}", value):
        raise argparse.ArgumentTypeError(
            "--brigade needs the last four characters of a Head Chef thread ID"
        )
    return value.lower()


if __name__ == "__main__":
    raise SystemExit(main())

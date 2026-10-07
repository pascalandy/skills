# /// script
# dependencies = ["PyYAML>=6.0,<7"]
# ///
"""Validate Matt mode's routed package and pinned upstream imports."""

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

import importlib.util
from collections.abc import Hashable
from pathlib import Path, PurePosixPath

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

log = logging.getLogger("check-matt-mode")
EXIT_CODES = exit_codes({0: "the packages are valid", 1: "a package is invalid"})

TOOLS = Path(__file__).resolve().parent
DEFAULT_ROOT = TOOLS.parent.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


layout = load_module("meta_skill_layout", TOOLS / "check_meta_skill_layout.py")
updater = load_module("matt_mode_updater", TOOLS / "update_matt_mode.py")


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(
        self, node: MappingNode, deep: bool = False
    ) -> dict[Hashable, Any]:
        self.flatten_mapping(node)
        mapping: dict[Hashable, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ConstructorError(
                    None,
                    None,
                    "mapping keys must be unique strings",
                    key_node.start_mark,
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def parse_metadata(
    text: str, label: str, errors: list[str]
) -> dict[str, object] | None:
    try:
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        errors.append(f"{label}: invalid YAML: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label}: metadata must be a mapping")
        return None
    return value


def validate_entry(
    package: Path,
    package_name: str,
    expected_link: str | None,
    errors: list[str],
) -> set[str]:
    entry = package / "SKILL.md"
    scanner_files = sorted(path for path in package.rglob("SKILL.md") if path.is_file())
    if scanner_files != [entry]:
        found = (
            ", ".join(path.relative_to(package).as_posix() for path in scanner_files)
            or "none"
        )
        errors.append(
            f"{package_name}: expected exactly one root SKILL.md; found: {found}"
        )
    if not entry.is_file() or entry.is_symlink():
        errors.append(f"{package_name}: root SKILL.md is missing")
        return set()

    label = f"{package_name}/SKILL.md"
    layout.validate_instruction_file(entry, label, errors)
    text = layout.read_utf8(entry, label, errors)
    links: set[str] = set()
    if text is not None:
        frontmatter, _ = layout.split_frontmatter_text(text, label, errors)
        metadata = parse_metadata("\n".join(frontmatter), label, errors)
        if metadata is not None:
            if metadata.get("name") != package_name:
                errors.append(f'{label}: require name: "{package_name}"')
            description = metadata.get("description")
            if not isinstance(description, str) or not description.strip():
                errors.append(f"{label}: require a non-empty description string")
        links = {
            target.partition("#")[0] for target in layout.markdown_link_targets(text)
        }
        if expected_link is not None and expected_link not in links:
            errors.append(f"{label}: missing upstream body link: {expected_link}")
    return links


def validate_mapping_shapes(registry, errors: list[str]) -> tuple[set[str], set[str]]:
    internal_entries: set[str] = set()
    shared_names: set[str] = set()
    for mapping in registry.mappings:
        if mapping.kind == "internal":
            expected = PurePosixPath("matt-mode/playbooks") / mapping.name
            if mapping.destination != expected or mapping.entry != f"{mapping.name}.md":
                errors.append(
                    f"lock mapping {mapping.name}: internal destination or entry is inconsistent"
                )
            internal_entries.add(
                str((mapping.destination / mapping.entry).relative_to("matt-mode"))
            )
        else:
            expected = PurePosixPath(mapping.name) / "references/upstream"
            if mapping.destination != expected or mapping.entry != f"{mapping.name}.md":
                errors.append(
                    f"lock mapping {mapping.name}: shared destination or entry is inconsistent"
                )
            shared_names.add(mapping.name)
    return internal_entries, shared_names


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if root.is_symlink() or not root.is_dir():
        return [f"expected a non-symlink Matt skill bucket: {root}"]
    try:
        registry = updater.parse_registry(root)
    except updater.ImportError as error:
        return [str(error)]

    internal_entries, shared_names = validate_mapping_shapes(registry, errors)
    package_names = {"matt-mode", *shared_names}
    for package_name in sorted(package_names):
        package = root / package_name
        if not package.is_dir() or package.is_symlink():
            errors.append(f"missing sibling package: {package_name}")
            continue
        if not layout.validate_no_symlinks(package, errors):
            continue
        expected_link = None
        if package_name != "matt-mode":
            expected_link = f"references/upstream/{package_name}.md"
        links = validate_entry(package, package_name, expected_link, errors)
        if package_name == "matt-mode":
            routed = {target for target in links if target.startswith("playbooks/")}
            if routed != internal_entries:
                missing = ", ".join(sorted(internal_entries - routed)) or "none"
                unexpected = ", ".join(sorted(routed - internal_entries)) or "none"
                errors.append(
                    "matt-mode/SKILL.md: route table disagrees with lock; "
                    f"missing: {missing}; unexpected: {unexpected}"
                )
        layout.validate_markdown_links(package, errors)
        layout.validate_portability(package, errors)
        layout.validate_asset_modes(package, [], [], errors)

    errors.extend(updater.verify_imports(root))
    return sorted(set(errors))


def check(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.absolute()
    try:
        errors = validate(root)
    except OSError as error:
        errors = [f"cannot inspect {args.root}: {error}"]
    if errors:
        raise ScriptError(*errors)

    registry = updater.parse_registry(root)
    _, shared_names = validate_mapping_shapes(registry, [])
    route_count = sum(mapping.kind == "internal" for mapping in registry.mappings)
    package_count = len(shared_names) + 1
    log.info(
        "Matt mode packages valid: %s (packages=%d, entrypoints=%d, routes=%d, "
        "imports=%d)",
        root,
        package_count,
        package_count,
        route_count,
        len(registry.files),
    )
    return {}


def main(argv: Sequence[str] | None = None) -> int:
    parser = Parser(
        prog="check_matt_mode.py", description=__doc__, exit_codes=EXIT_CODES
    )
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=DEFAULT_ROOT,
        metavar="BUCKET",
        help="Matt skill bucket (default: repository source)",
    )
    return run_script(parser, check, argv)


if __name__ == "__main__":
    raise SystemExit(main())

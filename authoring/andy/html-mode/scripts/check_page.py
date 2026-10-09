# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright==1.63.0", "pillow==12.3.0"]
# ///
"""Check a standalone HTML page in a real browser against html-mode's quality bar."""

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

import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageChops
from playwright.sync_api import (
    Browser,
    BrowserContext,
    FloatRect,
    Page,
    Playwright,
    sync_playwright,
)
from playwright.sync_api import Error as PlaywrightError


@dataclass(frozen=True)
class Screen:
    name: str
    width: int
    height: int
    touch: bool
    phone: bool = False


SCREENS: tuple[Screen, ...] = (
    Screen("phone", 390, 844, touch=True, phone=True),
    Screen("iphone-pro", 402, 874, touch=True, phone=True),
    Screen("ipad-portrait", 820, 1180, touch=True),
    Screen("ipad-landscape", 1180, 820, touch=True),
    Screen("ipad-pro-portrait", 1032, 1376, touch=True),
    Screen("laptop", 1280, 720, touch=False),
    Screen("desktop", 1440, 900, touch=False),
)
BY_NAME = {screen.name: screen for screen in SCREENS}
SHOWN_PER_CHECK = 5
FOCUS_STOPS = 60
SLOW_FRAME_MS = 50
REST_FRAMES = 4

DESCRIBE_JS = """
const describe = (el) => {
  const name = el.getAttribute('aria-label') || (el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 30);
  const cls = typeof el.className === 'string' ? el.className.split(' ')[0] : el.getAttribute('class')?.split(' ')[0];
  return `${el.tagName.toLowerCase()}${cls ? '.' + cls : ''}${name ? ` "${name}"` : ''}`;
};
"""

AUDIT_JS = (
    "({ phone, width }) => {"
    + DESCRIBE_JS
    + """
  // A phone widens its layout viewport to fit overflowing content: compare with the screen, not innerWidth
  const out = { overflow: Math.max(0, document.documentElement.scrollWidth - width), smallText: [], contrast: [], clipped: [] };
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  // The canvas resolves any CSS colour syntax (color(srgb …), light-dark(), oklch) to sRGB bytes
  const rgba = (color) => {
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = '#000';
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
    return [r, g, b, a / 255];
  };
  const channel = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const luminance = ([r, g, b]) => 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  const ratio = (a, b) => { const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
  const shown = new Map();
  const isShown = (el) => {
    if (shown.has(el)) return shown.get(el);
    const s = getComputedStyle(el);
    let result = s.visibility !== 'hidden' && s.display !== 'none' && Number(s.opacity) > 0;
    for (let parent = el.parentElement; result && parent; parent = parent.parentElement) {
      const s = getComputedStyle(parent);
      result = s.display !== 'none' && Number(s.opacity) > 0;
    }
    shown.set(el, result);
    return result;
  };
  const dark = matchMedia('(prefers-color-scheme: dark)').matches && getComputedStyle(document.documentElement).colorScheme.includes('dark');
  const canvasColour = dark ? [18, 18, 18, 1] : [255, 255, 255, 1];
  // Paint the ancestors as the browser does: each element paints its background, then its content, and its
  // opacity fades that whole group against what lies outside it. Colours are premultiplied by alpha.
  const premultiply = ([r, g, b, a]) => [r * a, g * a, b * a, a];
  const sourceOver = (top, bottom) => top.map((v, i) => v + bottom[i] * (1 - top[3]));
  const paint = (chain, ink) => {
    let content = ink ? premultiply(ink) : [0, 0, 0, 0];
    for (const e of chain) {
      const s = getComputedStyle(e);
      const paints = e.getClientRects().length > 0 && s.visibility !== 'hidden';
      if (paints && s.backgroundImage !== 'none') return null;
      const background = paints ? premultiply(rgba(s.backgroundColor)) : [0, 0, 0, 0];
      content = sourceOver(content, background).map((v) => v * Number(s.opacity));
    }
    return sourceOver(content, premultiply(canvasColour)).slice(0, 3);
  };
  const chainOf = (el) => { const chain = []; for (let e = el; e; e = e.parentElement) chain.push(e); return chain; };
  const small = new Set();
  const pale = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const text = node.textContent.replace(/\\s+/g, ' ').trim();
    const el = node.parentElement;
    if (!text || !el || el.closest('script, style, noscript, template') || !isShown(el)) continue;
    const parentBox = el.getBoundingClientRect();
    if (el.getClientRects().length && (parentBox.width <= 1 || parentBox.height <= 1)) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const box = range.getBoundingClientRect();
    if (box.width <= 1 || box.height <= 1) continue;
    const style = getComputedStyle(el);
    const svg = el instanceof SVGElement;
    const matrix = svg ? el.getScreenCTM() : null;
    const size = parseFloat(style.fontSize) * (matrix ? Math.hypot(matrix.c, matrix.d) : 1);
    const label = text.slice(0, 40);
    if (phone && size < 11.95) small.add(`"${label}" at ${size.toFixed(1)}px`);
    // SVG text sits on shapes and text over an image has no single background: both stay a visual check
    if (svg || el.closest('[aria-disabled="true"], :disabled')) continue;
    const fg = rgba(style.color);
    if (fg[3] === 0) continue;
    const chain = chainOf(el);
    const bg = paint(chain, null);
    const ink = paint(chain, fg);
    if (!bg || !ink) continue;
    const bold = Number(style.fontWeight) >= 700;
    const need = size >= 24 || (bold && size >= 18.66) ? 3 : 4.5;
    const r = ratio(ink, bg);
    if (r < need - 0.005) pale.add(`"${label}" at ${r.toFixed(2)}:1, needs ${need}:1`);
  }
  out.smallText = [...small];
  out.contrast = [...pale];
  for (const el of document.body.querySelectorAll('*')) {
    if (!isShown(el)) continue;
    const s = getComputedStyle(el);
    const cutX = ['hidden', 'clip'].includes(s.overflowX) && s.textOverflow !== 'ellipsis' && el.scrollWidth > el.clientWidth + 1;
    const cutY = ['hidden', 'clip'].includes(s.overflowY) && el.scrollHeight > el.clientHeight + 1;
    if (!cutX && !cutY) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 1 || r.height <= 1) continue;
    const inner = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let cut = false;
    for (let n = inner.nextNode(); n && !cut; n = inner.nextNode()) {
      if (!n.textContent.trim() || !n.parentElement || !isShown(n.parentElement)) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      const t = range.getBoundingClientRect();
      cut = t.width > 0 && ((cutX && (t.right > r.right + 1 || t.left < r.left - 1)) || (cutY && (t.bottom > r.bottom + 1 || t.top < r.top - 1)));
    }
    if (cut) out.clipped.push(describe(el));
  }
  return out;
}"""
)

TARGETS_JS = (
    "({ min }) => {"
    + DESCRIBE_JS
    + """
  const selector = 'a[href], button, input:not([type="hidden"]), select, textarea, summary, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="tab"], [role="switch"]';
  const out = [];
  // Allow one pixel of tolerance for fractional layout edges
  const half = min / 2 - 1;
  for (const el of document.querySelectorAll(selector)) {
    if (!el.getClientRects().length || el.closest('[hidden], [inert]')) continue;
    const s = getComputedStyle(el);
    if (s.visibility === 'hidden' || s.display === 'none') continue;
    let r = el.getBoundingClientRect();
    if (r.width <= 1 && r.height <= 1) continue;
    // A link or term inside running text is exempt, as WCAG 2.5.8 allows
    if (s.display === 'inline') {
      const block = el.parentElement?.closest('p, li, dd, dt, td, th, blockquote, figcaption, label, h1, h2, h3, h4, h5, h6');
      if (block && block.textContent.trim().length > el.textContent.trim().length + 3) continue;
    }
    el.scrollIntoView({ behavior: 'instant', block: 'center', inline: 'center' });
    r = el.getBoundingClientRect();
    const centre = (b) => [b.left + b.width / 2, b.top + b.height / 2];
    // A composite target, such as a map pin and its label, counts around the centre of any of its parts
    const labels = [...(el.labels || [])];
    const centres = [centre(r), ...[...el.children].slice(0, 8).map((child) => centre(child.getBoundingClientRect())), ...labels.map((label) => centre(label.getBoundingClientRect()))];
    const [cx, cy] = centres[0];
    // A skip link waits off-screen until it has focus
    if (cx < 0 || cy < 0 || cx >= innerWidth || cy >= innerHeight) continue;
    // Hit testing counts padding and pseudo-elements that enlarge the hit area, and finds what covers a control
    const hit = (x, y) => {
      if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) return false;
      const h = document.elementFromPoint(x, y);
      return !!h && (h === el || el.contains(h) || labels.some((label) => label === h || label.contains(h)));
    };
    const roomy = ([x, y]) => [[x, y], [x - half, y], [x + half, y], [x, y - half], [x, y + half]].every(([px, py]) => hit(px, py));
    if (centres.some(roomy)) continue;
    if (!centres.some(([x, y]) => hit(x, y))) out.push(`${describe(el)} is covered at its centre`);
    else out.push(`${describe(el)} hit area under ${min}px (box ${Math.round(r.width)}×${Math.round(r.height)})`);
  }
  return out;
}"""
)

ACTIVE_JS = (
    "(index) => {"
    + DESCRIBE_JS
    + """
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement) return null;
  if (el.hasAttribute('data-check-page-stop')) return { repeat: true };
  el.setAttribute('data-check-page-stop', String(index));
  const r = el.getBoundingClientRect();
  return { repeat: false, x: r.left, y: r.top, w: r.width, h: r.height, label: describe(el) };
}"""
)

COUNT_FRAMES_JS = """
() => {
  window.__checkPageFrames = 0;
  const raw = window.requestAnimationFrame.bind(window);
  window.__checkPageRaw = raw;
  window.requestAnimationFrame = (callback) => raw((t) => { window.__checkPageFrames += 1; callback(t); });
}
"""

SAMPLE_START_JS = """
() => {
  const raw = window.__checkPageRaw || window.requestAnimationFrame.bind(window);
  const probe = { gaps: [], last: 0, on: true, long: 0 };
  window.__checkPageProbe = probe;
  try {
    new PerformanceObserver((list) => { for (const e of list.getEntries()) probe.long = Math.max(probe.long, e.duration); }).observe({ type: 'longtask' });
  } catch (e) {}
  const step = (t) => { if (probe.last) probe.gaps.push(t - probe.last); probe.last = t; if (probe.on) raw(step); };
  raw(step);
}
"""

SAMPLE_STOP_JS = """
() => {
  const probe = window.__checkPageProbe;
  probe.on = false;
  const gaps = probe.gaps.slice(2);
  return { frames: gaps.length, max: gaps.length ? Math.max(...gaps) : 0, slow: gaps.filter((g) => g > SLOW_MS).length, long: probe.long };
}
""".replace("SLOW_MS", str(SLOW_FRAME_MS))

ANIMATIONS_JS = """
(reduced) => document.getAnimations().filter((a) => a.playState === 'running' && (reduced || a.effect?.getTiming().iterations === Infinity)).length
"""


class Run:
    """One page checked in one browser; findings accumulate as error messages."""

    def __init__(
        self, browser: Browser, browser_name: str, url: str, evidence: Path
    ) -> None:
        self.browser = browser
        self.browser_name = browser_name
        self.url = url
        self.evidence = evidence
        self.errors: list[str] = []
        self.metrics: dict[str, Any] = {}
        self.host = urlparse(url).hostname

    def report(self, where: str, check: str, items: Sequence[str], fix: str) -> None:
        for item in items[:SHOWN_PER_CHECK]:
            self.errors.append(f"{where}: {check}: {item}; {fix}")
        if len(items) > SHOWN_PER_CHECK:
            self.errors.append(
                f"{where}: {check}: {len(items) - SHOWN_PER_CHECK} more like these; {fix}"
            )

    def context(
        self,
        screen: Screen,
        scheme: str,
        reduced: bool = False,
        touch: bool | None = None,
    ) -> BrowserContext:
        touch = screen.touch if touch is None else touch
        options: dict[str, Any] = {
            "viewport": {"width": screen.width, "height": screen.height},
            "color_scheme": scheme,
            "reduced_motion": "reduce" if reduced else "no-preference",
            "has_touch": touch,
        }
        if self.browser_name != "firefox":
            options["is_mobile"] = touch
        return self.browser.new_context(**options)

    @contextmanager
    def open(
        self,
        screen: Screen,
        scheme: str,
        *,
        reduced: bool = False,
        touch: bool | None = None,
        count_frames: bool = False,
    ) -> Iterator[Page]:
        where = f"{screen.name}/{scheme}{'/reduced-motion' if reduced else ''}"
        context = self.context(screen, scheme, reduced=reduced, touch=touch)
        problems: list[str] = []
        external: list[str] = []
        try:
            page = context.new_page()
            page.on("pageerror", lambda error: problems.append(f"uncaught {error}"))
            page.on(
                "console",
                lambda message: (
                    problems.append(message.text) if message.type == "error" else None
                ),
            )
            page.on(
                "request",
                lambda request: (
                    external.append(request.url) if self.external(request.url) else None
                ),
            )
            if count_frames:
                page.add_init_script(f"({COUNT_FRAMES_JS})()")
            page.goto(self.url, wait_until="load")
            page.evaluate("document.fonts.ready.then(() => true)")
            page.wait_for_timeout(500)
            yield page
        finally:
            try:
                self.report(
                    where,
                    "console",
                    list(dict.fromkeys(problems)),
                    "fix the script error shown in the browser console",
                )
                self.report(
                    where,
                    "network",
                    sorted(set(external)),
                    "inline the asset or remove the request",
                )
            finally:
                context.close()

    def external(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https", "ws", "wss"}:
            return False
        return parsed.hostname != self.host

    def audit(self, screen: Screen, scheme: str) -> None:
        where = f"{screen.name}/{scheme}"
        with self.open(screen, scheme) as page:
            page.screenshot(path=self.evidence / f"{screen.name}-{scheme}.png")
            found = page.evaluate(
                AUDIT_JS, {"phone": screen.phone, "width": screen.width}
            )
            if found["overflow"]:
                self.report(
                    where,
                    "overflow",
                    [f"the page is {found['overflow']}px wider than the screen"],
                    "contain the wide element or let it wrap",
                )
            self.report(
                where, "small-text", found["smallText"], "raise phone text to 12px"
            )
            self.report(
                where,
                "contrast",
                found["contrast"],
                "adjust text and background colours to meet the required contrast",
            )
            self.report(
                where,
                "clipped",
                found["clipped"],
                "let the text wrap or end it with an ellipsis",
            )
            if screen.touch:
                self.report(
                    where,
                    "targets",
                    page.evaluate(TARGETS_JS, {"min": 44}),
                    "enlarge the hit area to 44px with padding or a pseudo-element",
                )

    def focus(self, screen: Screen, scheme: str) -> None:
        where = f"{screen.name}/{scheme}"
        with self.open(screen, scheme, reduced=True) as page:
            invisible: list[str] = []
            stops = 0
            for index in range(FOCUS_STOPS):
                page.keyboard.press("Tab")
                page.wait_for_timeout(120)
                stop = page.evaluate(ACTIVE_JS, index)
                if stop is None or stop["repeat"]:
                    break
                stops += 1
                clip = self.clip(stop, screen)
                if clip is None:
                    invisible.append(stop["label"])
                    continue
                focused = page.screenshot(clip=clip)
                page.evaluate("document.activeElement.blur()")
                page.wait_for_timeout(120)
                plain = page.screenshot(clip=clip)
                page.evaluate(
                    f"document.querySelector('[data-check-page-stop=\"{index}\"]').focus({{ preventScroll: true }})"
                )
                if changed_pixels(focused, plain) < max(
                    12, 0.004 * clip["width"] * clip["height"]
                ):
                    invisible.append(stop["label"])
            self.metrics.setdefault("focus_stops", {})[where] = stops
            self.report(
                where,
                "focus",
                invisible,
                "give :focus-visible an outline or ring that contrasts",
            )

    @staticmethod
    def clip(stop: Mapping[str, Any], screen: Screen) -> FloatRect | None:
        x = max(0.0, stop["x"] - 6)
        y = max(0.0, stop["y"] - 6)
        right = min(float(screen.width), stop["x"] + stop["w"] + 6)
        bottom = min(float(screen.height), stop["y"] + stop["h"] + 6)
        if right - x < 2 or bottom - y < 2:
            return None
        return FloatRect(x=x, y=y, width=right - x, height=bottom - y)

    def rest(self, screen: Screen, scheme: str) -> None:
        for reduced in (False, True):
            where = f"{screen.name}/{scheme}{'/reduced-motion' if reduced else ''}"
            with self.open(screen, scheme, reduced=reduced, count_frames=True) as page:
                page.wait_for_timeout(2500)
                page.evaluate("window.__checkPageFrames = 0")
                page.wait_for_timeout(2000)
                frames = int(page.evaluate("window.__checkPageFrames"))
                looping = int(page.evaluate(ANIMATIONS_JS, reduced))
                still: list[str] = []
                if frames > REST_FRAMES:
                    still.append(f"{frames} animation frames in 2 s at rest")
                if looping:
                    kind = "" if reduced else "infinite "
                    still.append(f"{looping} {kind}CSS animations running at rest")
                fix = (
                    "stop motion under prefers-reduced-motion"
                    if reduced
                    else "draw only while something moves"
                )
                self.report(where, "motion", still, fix)

    def frames(self, screen: Screen, scheme: str) -> None:
        where = f"{screen.name}/{scheme}"
        with self.open(screen, scheme) as page:
            page.evaluate(SAMPLE_START_JS)
            page.mouse.move(screen.width / 2, screen.height / 2)
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                page.mouse.wheel(0, 120)
                page.wait_for_timeout(40)
                if page.evaluate(
                    "innerHeight + scrollY >= document.documentElement.scrollHeight - 2"
                ):
                    break
            page.wait_for_timeout(600)
            sample = page.evaluate(SAMPLE_STOP_JS)
            self.metrics.setdefault("max_frame_ms", {})[where] = round(sample["max"], 1)
            slow: list[str] = []
            if sample["slow"]:
                slow.append(
                    f"{sample['slow']} of {sample['frames']} frames over {SLOW_FRAME_MS} ms, worst {sample['max']:.0f} ms"
                )
            if sample["long"] > SLOW_FRAME_MS:
                slow.append(f"a {sample['long']:.0f} ms long task")
            self.report(
                where,
                "frames",
                slow,
                "move work out of scroll handlers or animate with transform",
            )

    def baseline(self, screen: Screen, scheme: str, baseline_url: str) -> None:
        shots: list[bytes] = []
        for url in (baseline_url, self.url):
            context = self.context(screen, scheme)
            try:
                page = context.new_page()
                page.goto(url, wait_until="load")
                page.evaluate("document.fonts.ready.then(() => true)")
                page.wait_for_timeout(500)
                shots.append(page.screenshot(full_page=True))
            finally:
                context.close()
        before, after = (Image.open(BytesIO(shot)).convert("RGB") for shot in shots)
        width, height = min(before.width, after.width), min(before.height, after.height)
        difference = ImageChops.difference(
            before.crop((0, 0, width, height)), after.crop((0, 0, width, height))
        )
        mask = difference.convert("L").point(above(8))
        unmatched = (
            before.width * before.height
            + after.width * after.height
            - 2 * width * height
        )
        changed = mask.histogram()[255] + unmatched
        if changed:
            # The evidence spans both versions: a region either one lacks shows in red
            size = (max(before.width, after.width), max(before.height, after.height))
            overlay = Image.new("RGB", size, (230, 30, 30))
            overlay.paste(after.crop((0, 0, width, height)), (0, 0))
            overlay.paste((230, 30, 30), mask=mask)
            overlay.save(self.evidence / f"baseline-{screen.name}-{scheme}.png")
        self.metrics.setdefault("baseline", {})[f"{screen.name}/{scheme}"] = {
            "changed_pixels": changed,
            "heights": [before.height, after.height],
        }


def above(threshold: int) -> list[int]:
    """A lookup table that keeps the pixels whose difference passes the threshold."""
    return [0] * (threshold + 1) + [255] * (255 - threshold)


def changed_pixels(first: bytes, second: bytes) -> int:
    a = Image.open(BytesIO(first)).convert("RGB")
    b = Image.open(BytesIO(second)).convert("RGB")
    if a.size != b.size:
        return a.width * a.height
    mask = ImageChops.difference(a, b).convert("L").point(above(24))
    return mask.histogram()[255]


def page_url(target: str) -> str:
    if urlparse(target).scheme in {"http", "https", "file"}:
        return target
    path = Path(target).expanduser()
    if not path.is_file():
        raise UsageError(f"no page at {target}; pass an HTML file or an http(s) URL")
    return path.resolve().as_uri()


def browser_path(name: str = "chromium") -> str | None:
    """The browser to run: CHECK_PAGE_BROWSER, a Chromium on PATH, or None for Playwright's own."""
    if found := os.environ.get("CHECK_PAGE_BROWSER"):
        return found
    if name != "chromium":
        return None
    names = ("chromium", "chromium-browser", "google-chrome")
    return next((path for path in map(shutil.which, names) if path), None)


def launch(playwright: Playwright, name: str) -> Browser:
    kind = getattr(playwright, name)
    executable = browser_path(name)
    try:
        return kind.launch(executable_path=executable) if executable else kind.launch()
    except PlaywrightError as error:
        first = str(error).strip().splitlines()[0]
        raise ScriptError(
            f"cannot start {name}: {first}; run: uv run --with playwright==1.63.0 playwright install {name}"
        ) from error


def evidence_dir(target: str, chosen: str | None) -> Path:
    if chosen:
        folder = Path(chosen).expanduser()
    else:
        cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
        stem = Path(urlparse(target).path).stem or "page"
        folder = (
            cache
            / "check-page"
            / stem
            / datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        )
    folder.mkdir(parents=True, exist_ok=True)
    return folder.resolve()


def work(args: argparse.Namespace) -> dict[str, Any]:
    url = page_url(args.target)
    baseline = page_url(args.baseline) if args.baseline else None
    screens = [BY_NAME[name] for name in args.screen] if args.screen else list(SCREENS)
    schemes = ("light", "dark") if args.scheme == "both" else (args.scheme,)
    evidence = evidence_dir(args.target, args.output_dir)
    with sync_playwright() as playwright:
        browser = launch(playwright, args.browser)
        run = Run(browser, args.browser, url, evidence)
        try:
            for screen in screens:
                for scheme in schemes:
                    log.info("audit %s/%s", screen.name, scheme)
                    run.audit(screen, scheme)
            main = next((screen for screen in screens if not screen.touch), screens[0])
            log.info("focus, rest and frames on %s", main.name)
            for scheme in schemes:
                run.focus(main, scheme)
            phone = next((screen for screen in screens if screen.phone), None)
            for scheme in schemes:
                run.rest(main, scheme)
                run.frames(main, scheme)
                if phone and phone is not main:
                    run.frames(phone, scheme)
            if baseline:
                for screen in screens:
                    log.info("baseline %s", screen.name)
                    for scheme in schemes:
                        run.baseline(screen, scheme, baseline)
        finally:
            browser.close()
    report = {"evidence": str(evidence), "metrics": run.metrics}
    if run.errors:
        # A page opens several times per screen; the same console error counts once
        raise ScriptError(*dict.fromkeys(run.errors), report=report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    names = ", ".join(
        f"{s.name} {s.width}x{s.height}{' touch' if s.touch else ''}" for s in SCREENS
    )
    parser = Parser(
        prog="check_page.py",
        description="Check a standalone HTML page in a real browser against html-mode's quality bar.",
        epilog=EPILOG.format(screens=names),
        exit_codes=EXIT_CODES,
    )
    parser.add_argument("target", help="the page: an HTML file or an http(s) URL")
    parser.add_argument(
        "-s",
        "--screen",
        action="append",
        choices=[s.name for s in SCREENS],
        help="check only this screen; repeat for several (default: every screen)",
    )
    parser.add_argument(
        "--scheme",
        choices=("light", "dark", "both"),
        default="both",
        help="colour scheme to check (default: both)",
    )
    parser.add_argument(
        "-b",
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default="chromium",
        help="browser engine; webkit stands in for Safari (default: chromium)",
    )
    parser.add_argument(
        "--baseline",
        metavar="TARGET",
        help="the previous version; reports changed pixels per screen and scheme",
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        help="where screenshots go (default: ~/.cache/check-page/<page>/<time>)",
    )
    return run_script(parser, work, argv, debug="CHECK_PAGE_DEBUG")


EPILOG = """\
Answers {{"ok":true}} with the evidence folder and metrics when the page passes.
Otherwise stdout stays empty and the last line of stderr lists each finding
under "errors". Findings name the screen, the check, the element, and the fix.
Install a missing engine with:
  uv run --with playwright==1.63.0 playwright install chromium
Use the same command with firefox or webkit for another engine.
CHECK_PAGE_BROWSER can select an existing compatible executable.

screens: {screens}

examples:
  check_page.py page.html
  check_page.py page.html --screen phone --screen desktop --scheme light
  check_page.py page.html --baseline old.html
  check_page.py https://example.org/page/ --browser webkit"""

EXIT_CODES = exit_codes(
    {0: "the page passes", 1: "the page has findings, or the browser failed"}
)

log = logging.getLogger("check-page")


if __name__ == "__main__":
    raise SystemExit(main())

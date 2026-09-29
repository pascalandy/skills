# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Judge retro stories with Jev: three yes/no questions per story, one rule in code.

Input is JSON Lines, one story per line, as references/reviewer-brief.md defines.
Jev sees only the goal, the story, the evidence, and the proposed fix; the
reviewer's verdict stays here, so Jev's answer is independent of it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import NoReturn

import tomllib

PROG = "retro_triage.py"
MODEL = "jev-1.13.0"
BASE_URL = "https://api.typesafe.ai"
TEMPORARY = 75
FIELDS = ("id", "repo", "story", "evidence", "fix")
# label-for-issues-jev owns consent; its file and terms name decide what may leave
TERMS_NAME = "typesafe-2026-09-26"
KEYRING = ("secret", "keyring", "get", "--service=typesafe_ai", "--user=api_key")

GOAL = (
    "Make agent skills easier for an agent to use. Fix obvious misses and "
    "wrong, contradictory, or confusing instructions in the skill. Do not add "
    "rules for rare edge cases; agents handle those on their own. Prefer the "
    "smallest change; no new features, files, sections, or tests."
)

QUESTIONS = {
    "skill_causes": {
        "type": "noul",
        "instructions": "Did the skill's own text or bundled code cause the failure described in `story`, according to `evidence`?",
        "criteria": {
            "true": "The skill states something false, contradicts another rule, gives a command that fails, has a bug in its bundled code, triggers when it should not, or omits a step that every agent on this path needs.",
            "false": "The failure came from agent error, an environment or upstream bug, content that lives outside the skill, or a situation the skill already handles.",
        },
    },
    "recurs": {
        "type": "noul",
        "instructions": "Would another agent following the skill as written likely hit the failure in `story` again during ordinary use?",
        "criteria": {
            "true": "The failure sits on a common path of the skill, so ordinary use reaches it again.",
            "false": "The failure needs rare or one-off circumstances, such as a single unusual incident.",
        },
    },
    "fix_is_minimal": {
        "type": "noul",
        "instructions": "Given `goal`, is `proposed_fix` a small change to existing text or code that removes the failure without adding a new feature, file, section, or test?",
        "criteria": {
            "true": "One sentence or one changed line of skill text, or a small bug fix in existing code.",
            "false": "A new command, feature, config, section, test suite, or a rule for an edge case; or there is no fix.",
        },
    },
}

# Accept when every answer is yes. On the 21 public stories of the 2026-09-28
# skill-feedback retro, repeat runs moved scores by up to 0.05. These questions
# matched the final decision on all 21; earlier wording matched 19 or 20, and
# each miss had a lowest score within 0.05 of 0.5. So a lowest score inside the
# band is a close call for a person to make.
ACCEPT_AT = 0.5
CONTESTED = (0.35, 0.65)

EXIT_CODES = {
    0: "success",
    1: "failure: bad input, no key, no consent, or a TypeSafe error",
    2: "bad usage",
    TEMPORARY: "TypeSafe was unreachable or rate-limited; rerun later",
    130: "interrupted (SIGINT)",
    143: "terminated (SIGTERM)",
}

EXAMPLES = f"""\
examples:
  {PROG} stories.jsonl
  {PROG} stories.jsonl --json
  {PROG} --dry-run stories.jsonl
  cat stories.jsonl | {PROG} -"""


class Failure(Exception):
    """An expected failure: what failed, then the command that fixes it."""

    def __init__(self, message: str, fix: str, code: int = 1) -> None:
        super().__init__(message)
        self.fix = fix
        self.code = code


class Terminated(KeyboardInterrupt):
    pass


def terminate(_signal: int, _frame: object) -> None:
    raise Terminated


def decide(scores: dict[str, float]) -> tuple[str, bool]:
    """The decision and whether it is a close call, from the lowest score."""
    low = min(scores.values())
    return ("accept" if low >= ACCEPT_AT else "refuse"), CONTESTED[
        0
    ] <= low < CONTESTED[1]


def read_stories(source: str) -> list[dict[str, str]]:
    try:
        text = (
            sys.stdin.read()
            if source == "-"
            else Path(source).read_text(encoding="utf-8")
        )
    except OSError as error:
        raise Failure(
            f"cannot read {source}: {error.strerror}", f"{PROG} <stories.jsonl>"
        ) from error
    stories: list[dict[str, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        where = f"{source}:{number}"
        try:
            story = json.loads(line)
        except json.JSONDecodeError as error:
            raise Failure(
                f"{where} is not JSON: {error.msg}", "write one JSON object per line"
            ) from error
        if not isinstance(story, dict):
            raise Failure(
                f"{where} is not a JSON object", "write one JSON object per line"
            )
        missing = [
            key
            for key in FIELDS
            if not isinstance(story.get(key), str) or not story[key].strip()
        ]
        if missing:
            raise Failure(
                f"{where} lacks {', '.join(missing)}",
                f"give every story {', '.join(FIELDS)} as text",
            )
        if story.get("reviewer") not in (None, "accept", "refuse"):
            raise Failure(
                f"{where} has reviewer {story['reviewer']!r}",
                "set reviewer to accept or refuse, or leave it out",
            )
        if any(story["id"] == seen["id"] for seen in stories):
            raise Failure(
                f"{where} repeats id {story['id']!r}", "give every story its own id"
            )
        stories.append(story)
    if not stories:
        raise Failure(f"{source} holds no stories", "write one JSON object per story")
    return stories


def state_of(story: dict[str, str]) -> dict[str, str]:
    return {
        "goal": GOAL,
        "story": story["story"],
        "evidence": story["evidence"],
        "proposed_fix": story["fix"],
    }


def require_consent(repos: set[str]) -> None:
    """Stop before any private repository's text leaves without recorded consent."""
    if shutil.which("gh") is None:
        raise Failure(
            "gh is not installed, so repository visibility is unknown",
            "install the GitHub CLI, then rerun",
        )
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for repo in sorted(repos):
        try:
            seen = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    repo,
                    "--json",
                    "visibility",
                    "-q",
                    ".visibility",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise Failure(
                f"gh took over 30s to report the visibility of {repo}",
                f"rerun {PROG} later",
                TEMPORARY,
            ) from error
        visibility = seen.stdout.strip()
        if seen.returncode != 0 or not visibility:
            raise Failure(
                f"cannot read the visibility of {repo}: {seen.stderr.strip()}",
                "gh auth status",
            )
        if visibility == "PUBLIC":
            continue
        try:
            entries = tomllib.loads(
                (config / "label-for-issues-jev/consent.toml").read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, tomllib.TOMLDecodeError):
            entries = {}
        if entries.get(repo, {}).get("terms") != TERMS_NAME:
            raise Failure(
                f"{repo} is {visibility.lower()} and has no consent under terms {TERMS_NAME}",
                f'show the user the terms in `jevlabel consent --help`; after they approve, run jevlabel consent add {repo} --by "<their name>"',
            )


def api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    chezmoi = shutil.which("chezmoi")
    if not key and chezmoi:
        try:
            found = subprocess.run(
                [chezmoi, *KEYRING],
                capture_output=True,
                text=True,
                timeout=15,
                stdin=subprocess.DEVNULL,
                check=False,
            )
            key = found.stdout.strip() if found.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            key = ""
    if not key:
        raise Failure(
            "no TypeSafe API key: TYPESAFE_API_KEY is unset and the chezmoi keyring has none",
            "export TYPESAFE_API_KEY, or run: chezmoi secret keyring set --service=typesafe_ai --user=api_key",
        )
    return key


def ask(
    story: dict[str, str], key: str, timeout: float
) -> tuple[str, dict[str, float]]:
    """One request per story. No response means it never ran, so a rerun is safe."""
    url = os.environ.get("TYPESAFE_BASE_URL", BASE_URL).rstrip("/") + "/v1/systemone"
    body = json.dumps(
        {"state": state_of(story), "model": MODEL, "questions": QUESTIONS}
    ).encode()
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            reply = json.load(response)
        return reply.get("model", MODEL), {
            name: float(reply["answers"][name]["noul"]) for name in QUESTIONS
        }
    except urllib.error.HTTPError as error:
        code = TEMPORARY if error.code in (429, 503) else 1
        raise Failure(
            f"TypeSafe answered HTTP {error.code} for story {story['id']}",
            f"rerun {PROG} later",
            code,
        ) from error
    except urllib.error.URLError as error:
        raise Failure(
            f"TypeSafe is unreachable at {url}: {error.reason}",
            f"rerun {PROG} later",
            TEMPORARY,
        ) from error
    except TimeoutError as error:
        raise Failure(
            f"TypeSafe did not answer story {story['id']} within {timeout:g}s",
            f"rerun {PROG} with a longer --timeout",
        ) from error
    except (ValueError, KeyError, TypeError) as error:
        raise Failure(
            f"TypeSafe sent an unexpected answer for story {story['id']}: {error!r}",
            f"check {url} and the model {MODEL}",
        ) from error


def duration(text: str) -> float:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([smh]?)", text.strip())
    if match is None or float(match[1]) <= 0:
        raise argparse.ArgumentTypeError(
            f"invalid duration {text!r}; use 30s, 5m, 2h, or seconds"
        )
    return float(match[1]) * {"": 1, "s": 1, "m": 60, "h": 3600}[match[2]]


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(2, f"error: {message}\nrun '{PROG} --help'\n")


def build_parser() -> Parser:
    table = "\n".join(f"  {code:<4} {meaning}" for code, meaning in EXIT_CODES.items())
    parser = Parser(
        prog=PROG,
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Ask Jev three yes/no questions about each retro story, then decide in code: "
            "accept when every answer is yes, refuse otherwise, and flag close calls. "
            "Private repositories need the consent label-for-issues-jev records."
        ),
        epilog=f"{EXAMPLES}\n\nexit codes:\n{table}",
    )
    parser.add_argument("stories", help="JSON Lines file of stories, or - for stdin")
    parser.add_argument(
        "--json", action="store_true", help="print one JSON object on stdout"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print what each request would send; needs no key, consent, or network",
    )
    parser.add_argument(
        "--timeout",
        type=duration,
        default=30.0,
        metavar="DURATION",
        help="per-request deadline: 30s, 5m, or seconds (default: 30s)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print progress on stderr"
    )
    return parser


def run(args: argparse.Namespace) -> str:
    stories = read_stories(args.stories)
    if args.dry_run:
        previews = [
            {"id": s["id"], "repo": s["repo"], "state": state_of(s)} for s in stories
        ]
        if args.json:
            return json.dumps({"stories": previews}, indent=2)
        return "\n".join(json.dumps(preview) for preview in previews)
    require_consent({story["repo"] for story in stories})
    key = api_key()
    results = []
    for number, story in enumerate(stories, 1):
        try:
            model, scores = ask(story, key, args.timeout)
        except Failure as failure:
            # Paid answers already came back, so a plain rerun is not free
            if failure.code == TEMPORARY and results:
                judged = ", ".join(result["id"] for result in results)
                raise Failure(
                    f"{failure} after judging {judged}",
                    f"rerun {PROG} on the stories not yet judged",
                ) from failure
            raise
        decision, close = decide(scores)
        reviewer = story.get("reviewer")
        results.append(
            {
                "id": story["id"],
                "decision": decision,
                "contested": close or (reviewer is not None and reviewer != decision),
                "scores": scores,
                "reviewer": reviewer,
                "model": model,
            }
        )
        if args.verbose:
            print(f"judged {number}/{len(stories)}: {story['id']}", file=sys.stderr)
    if args.json:
        return json.dumps({"stories": results}, indent=2)
    rows = ["ID\tDECISION\tCONTESTED\tSKILL_CAUSES\tRECURS\tFIX_IS_MINIMAL\tREVIEWER"]
    for r in results:
        s = r["scores"]
        rows.append(
            f"{r['id']}\t{r['decision']}\t{'yes' if r['contested'] else 'no'}\t"
            f"{s['skill_causes']:.2f}\t{s['recurs']:.2f}\t{s['fix_is_minimal']:.2f}\t{r['reviewer'] or '-'}"
        )
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    if any(
        arg in ("-h", "--help")
        for arg in argv[: argv.index("--") if "--" in argv else len(argv)]
    ):
        parser.print_help()
        return 0
    as_json = "--json" in argv
    signal.signal(signal.SIGTERM, terminate)
    try:
        output = run(parser.parse_args(argv))
    except Failure as failure:
        error = {"errors": [str(failure)], "fix": failure.fix}
        print(
            json.dumps(error) if as_json else f"error: {failure}\nfix: {failure.fix}",
            file=sys.stderr,
        )
        return failure.code
    except Terminated:
        print("terminated", file=sys.stderr)
        return 143
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""From a T3 snapshot and GitHub facts to the page: one path for the replay, the oracles and the live service."""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path

import board
import facts
import privacy
import t3
from github import Facts, Recorded, unkey

HERE = Path(__file__).resolve().parent
# The live service's cadence, which oracle 5 measures
POLL = 2.0  # seconds between two reads of PRAGMA data_version
GITHUB_EVERY = 60.0  # seconds between GitHub refreshes of followed-run facts
GITHUB_TIMEOUT = 20.0  # seconds a GitHub read may take before it fails
# The oldest GitHub facts the live service may hold: a merge right after one
# read waits for the next one, up to a poll late, and its timeout
LAG = GITHUB_EVERY + GITHUB_TIMEOUT + 2 * POLL


class PrivacyError(ValueError):
    """The page data names a private repository or holds a local path."""


def private_label(index: int) -> str:
    letters = ""
    while index >= 0:
        index, remainder = divmod(index, 26)
        letters = chr(ord("A") + remainder) + letters
        index -= 1
    return "private-" + letters


def repository_names(gh: Facts) -> tuple[set[str], dict[str, str]]:
    """Public repositories, and the name the page shows for each repository.

    A public one shows its short name, or owner/name when two share it; a
    private one shows private-A, private-B..., in name order.
    """
    known = {info["name"]: info["public"] for info in gh.repositories.values()}
    public = {repo for repo, is_public in known.items() if is_public}
    names = {
        repo: repo if repo.startswith("private-") else private_label(i)
        for i, repo in enumerate(sorted(set(known) - public))
    }
    counts = Counter(repo.rsplit("/", 1)[-1] for repo in public)
    names.update(
        {
            repo: repo
            if counts[repo.rsplit("/", 1)[-1]] > 1
            else repo.rsplit("/", 1)[-1]
            for repo in public
        }
    )
    return public, names


def run_events(
    snap: t3.Snapshot,
    gh: Facts,
    heads: Iterable[str],
    disk: Mapping[str, dict] | None = None,
) -> tuple[list[str], list[dict]]:
    """The Head Chefs a snapshot holds, and the extractor's facts of their runs.

    A thread is a Head Chef once its title's id4 is its own threadId suffix;
    before that, its run has nothing to draw.
    """
    heads = [h for h in heads if snap.head_chef_since(h)]
    return heads, facts.extract(snap, gh, heads, dict(disk or {}))


def page_of(
    events: list[dict], gh: Facts, heads: list[str], now: float | None = None
) -> tuple[dict, dict[str, str]]:
    """The page data of the runs' facts, and the private repositories it must hide."""
    numbers = {
        ref: gh.epic_number(*unkey(ref))
        for ref in sorted({e["epic"] for e in events if e["epic"]})
    }
    public, names = repository_names(gh)
    data = board.build(
        events, public, numbers, names, {h[-4:].lower(): h for h in heads}, now
    )
    private = {repo: names[repo] for repo in names if repo not in public}
    return data, private


def page_data(
    snap: t3.Snapshot,
    gh: Facts,
    heads: Iterable[str],
    disk: Mapping[str, dict] | None = None,
    now: float | None = None,
) -> tuple[dict, dict[str, str]]:
    """The page data of each Head Chef run, and the private repositories it must hide."""
    heads, events = run_events(snap, gh, heads, disk)
    return page_of(events, gh, heads, now)


GENERIC = {"info", "answer"}  # what t3.classify() answers for a message no rule reads


def unparsed(events: Iterable[dict]) -> dict[str, list[dict]]:
    """Messages whose leading symbol no rule reads, and watch.toml writes the
    parser could not read; both stay 0 on the recorded runs (oracle 6)."""
    messages, watch = [], []
    for e in events:
        d = e["detail"] or {}
        if e["kind"] == "send" and d.get("msg") in GENERIC and d.get("lead"):
            messages.append({"t": e["time"], "role": e["role"], "lead": d["lead"]})
        elif e["kind"] == "watch_unread":
            watch.append({"t": e["time"]})
    return {"messages": messages, "watch": watch}


def recording_data(
    recording: dict,
    upto: int | None = None,
    now: float | None = None,
    known: float | None = None,
) -> dict:
    """Page data of a recording as the database stood at sequence `upto`,
    with GitHub as a reader that last read it at `known` saw it."""
    snap = t3.fold(recording["records"], upto)
    gh = Recorded(recording["github"])
    gh.at(
        None if now is None else t3_time(now),
        None if known is None else t3_time(known),
    )
    data, _ = page_data(snap, gh, [recording["head"]], {}, now)
    return data


def p95(values: Iterable[float]) -> float | None:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)] if ordered else None


def t3_time(seconds: float) -> str:
    from datetime import UTC, datetime

    stamp = datetime.fromtimestamp(seconds, UTC).isoformat(timespec="milliseconds")
    return stamp.replace("+00:00", "Z")


def render_page(
    data: dict, private: Mapping[str, str], live: dict | None = None
) -> str:
    """The self-contained page; refuses data that names a private repository or a local path.

    `live` turns the replay into the live dashboard: where to poll new data
    and how often, as live.py serves it.
    """
    if privacy.leaks(data, private):
        raise PrivacyError(
            "Privacy check refused the data; remove private repository names or local paths from the replay data, then rerun"
        )
    payload = json.dumps(
        data, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).replace("<", "\\u003c")
    page = (HERE / "page.html").read_text(encoding="utf-8")
    page = page.replace(
        "/*__BOARD__*/", (HERE / "board.js").read_text(encoding="utf-8")
    )
    settings = json.dumps(live, ensure_ascii=False, separators=(",", ":"))
    # the banner's error text comes from T3 and gh: no "</script>" may close the page's script
    page = page.replace("/*__LIVE__*/null", settings.replace("<", "\\u003c"))
    return page.replace("/*__DATA__*/null", payload)

"""The carpaccio contract: every Messages prefix and watch.toml key the extractor reads.

It reads the playbooks in this checkout, so a carpaccio change on main that
drops one fails here before the replay misreads a run.
"""

from __future__ import annotations

import re
from pathlib import Path

import t3

PLAYBOOK = Path(__file__).resolve().parents[3] / "playbooks" / "carpaccio"


def section(text: str, title: str) -> str:
    m = re.search(
        rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    assert m, f"section {title!r} is gone"
    return m.group(1)


def contract_errors(carpaccio: str, watchdog: str) -> list[str]:
    """What the extractor reads that the playbooks no longer define."""
    table = section(carpaccio, "Messages")
    cells = []
    for row in table.splitlines()[2:]:
        if row.startswith("|"):
            first = row.split("|")[1].replace("`", "").strip()
            cells += [c.strip() for c in re.split(r", | or ", first)]
    errors = [
        f"Messages table drops {prefix!r}"
        for prefix, _, _ in t3.HANDOFFS
        if prefix not in t3.LEGACY_PREFIXES
        and not any(cell.startswith(prefix) for cell in cells)
    ]
    report = section(carpaccio, "Report")
    errors += [
        f"carpaccio drops the {prefix!r} prefix"
        for _, prefix in t3.FIRST
        if not any(cell.startswith(prefix) for cell in cells)
        and f"`{prefix}" not in report
    ]
    files = section(watchdog, "Files")
    errors += [
        f"watchdog Files drops watch.toml key {key!r}"
        for key in t3.WATCH_KEYS
        if not re.search(rf"\[\[{key}\]\]|`{key}`|^{key} = ", files, re.MULTILINE)
    ]
    return errors


def read(name: str) -> str:
    return (PLAYBOOK / name).read_text(encoding="utf-8")


def test_playbooks_define_what_the_extractor_reads() -> None:
    assert contract_errors(read("carpaccio.md"), read("sop/watchdog.md")) == []


def test_a_dropped_prefix_or_key_fails() -> None:
    carpaccio = read("carpaccio.md").replace(
        "| 🔀 Batch merging |", "| 🔀 Batch landing |"
    )
    watchdog = read("sop/watchdog.md").replace("lastReceivedPhase", "lastPhase")
    assert contract_errors(carpaccio, watchdog) == [
        "Messages table drops '🔀 Batch merging'",
        "watchdog Files drops watch.toml key 'lastReceivedPhase'",
    ]

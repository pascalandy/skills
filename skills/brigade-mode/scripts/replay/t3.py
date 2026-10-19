"""T3 orchestration events as whitelisted records, folded into the database as of a sequence.

Every reader of T3 goes through `reduce()`. It keeps types, times, the
Messages prefixes of carpaccio, watch.toml plan keys and PR numbers, and drops
every other text, so a recording and the live service feed the extractor the
same records. `Snapshot` folds records up to a sequence N: the last update of
each thread, turn item, run and subagent, which is T3's own projection as of N.
"""

from __future__ import annotations

import gzip
import json
import re
import sqlite3
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import tomllib

# A record is [sequence, time, kind, id, data]; data None deletes the entity
Record = list[Any]

# Every thread.* event carries the whole thread record, title included, except
# PR link updates. An agent's rename leaves no thread event: its title comes
# from the rename tool call in the turn items
EVENTS = ("turn-item.updated", "run.created", "run.updated", "subagent.updated")
PR_URL = re.compile(r"github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)")
RELEASE_COMMAND = re.compile(
    r"\b(?:just (?:sync-fleet|release|publish)|gh release create)(?![\w-])"
)

# carpaccio Roles: the title of each thread a run launches (playbooks/carpaccio/carpaccio.md)
STATUSES = {
    "head_chef": ("🟢", "⏳", "❓", "⛳", "⏹️"),
    "chef": ("⏳", "🔀", "🧹", "🍽️", "⏸️", "⛳", "⏹️"),
    "cook": ("🍳", "🧹", "🍽️", "⏸️", "⏹️"),
}
TITLES = {
    "head_chef": re.compile(r"Head Chef ([0-9a-z]{4})\b(.*)", re.DOTALL),
    # older runs launched Chefs and Cooks without the id4
    "chef": re.compile(r"(?:🚥\s*)?Chef (\d+)(?: ([0-9a-z]{4})\b)?(.*)", re.DOTALL),
    "cook": re.compile(
        r"(?:🧑‍🍳\s*)?Cook (\d+)\.(\d+)(?: ([0-9a-z]{4})\b)?(.*)", re.DOTALL
    ),
}


def norm(ts: str | None) -> str | None:
    """GitHub drops milliseconds; T3 keeps them. One format for sorting."""
    if not ts:
        return None
    m = re.match(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?Z", ts)
    if m is None:
        raise ValueError(f"Invalid T3 or GitHub timestamp: {ts!r}")
    return f"{m.group(1)}{(m.group(2) or '.000')[:4].ljust(4, '0')}Z"


def parse_title(title: str | None) -> dict | None:
    """A carpaccio title's role, numbers and status emoji; its subject is dropped."""
    text = (title or "").strip()
    for role, pattern in TITLES.items():
        m = pattern.match(text)
        if not m:
            continue
        *numbers, id4, rest = m.groups()
        status = next(
            (s for s in sorted(STATUSES[role], key=rest.find) if s in rest), None
        )
        out: dict[str, Any] = {"role": role, "id4": id4, "status": status}
        if numbers:
            out["b"] = int(numbers[0])
        if len(numbers) > 1:
            out["c"] = int(numbers[1])
        count = re.search(r"(\d+)/(\d+)", rest)
        if count:
            out["n"] = [int(count.group(1)), int(count.group(2))]
        return out
    return None


# ---------------------------------------------------------------- messages ---
# carpaccio's Messages table (playbooks/carpaccio/carpaccio.md): each prefix as
# the table writes it, the kind it hands off, and the roles that may send it.
# The contract test fails when the table drops one of these prefixes
HANDOFFS = [
    ("🍽️ Stack ready", "stack_ready", {"cook"}),
    ("🍽️ Batch ready", "batch_ready", {"chef"}),
    ("🔀 Batch merging", "batch_merging", {"chef"}),
    ("🔀 Merge", "merge", {"head_chef"}),
    ("Batch merged", "batch_merged", {"chef"}),
    ("⛳ Batch delivered", "batch_delivered", {"chef"}),
    ("⏹️ Batch stopped", "batch_stopped", {"chef"}),
    ("⏹️ Stopped", "cook_stopped", {"cook"}),
    ("⏹️ Stop", "stop", {"head_chef", "chef"}),
    ("⏹️ Cut", "cut", {"head_chef", "chef"}),
    ("⏹️ Drop", "drop", {"head_chef"}),
    ("⏳ Rework", "rework", {"head_chef"}),
    ("🍽️ Hold", "hold", {"head_chef"}),
]
# A Cook's stop report from runs before the table named none; matched, not required
LEGACY_PREFIXES = {"⏹️ Stopped"}
# First-line prefixes: the Watchdog's messages and 🙋 from the Messages table, 📍 from Report
FIRST = [
    ("watchdog", "🐕 Watchdog"),
    ("pascal_card", "🙋"),
    ("progress", "📍"),
]
SENDER = re.compile(
    r"^(?:(?:🚥|🧑‍🍳)\s*)?(?:head )?(?:chef|cook) [\d.]+(?: \w{4})?\s*(?:→\s*[^·:,—-]*)?\s*[:·,—-]*\s*"
)


def leading_symbol(body: str) -> str | None:
    """The pictograph a line opens with, such as ❓ or ⚠️; `#79` or a code span is text."""
    lead = ""
    for ch in body:
        if unicodedata.category(ch) == "So" or (lead and ch in "\u200d\ufe0f"):
            lead += ch
        else:
            break
    return lead[:4] or None


def signature(text: str) -> dict:
    """The parts of a message that classify() reads, without its free text.

    `handoffs` lists, per line in order, the Messages prefixes it starts with;
    `first` names the features of the first line; `lead` is the first line's
    leading symbol after any sender header, for the parser-coverage oracle.
    """
    lines, fenced = [], False
    for ln in (text or "").strip().splitlines():
        if ln.strip().startswith("```"):
            fenced = not fenced
        elif ln.strip() and not fenced and not ln.lstrip().startswith(">"):
            lines.append(
                ln.strip().lower()
            )  # an example in a fence or a quote hands nothing off
    handoffs = []
    for ln in lines:
        kinds = [kind for prefix, kind, _ in HANDOFFS if ln.startswith(prefix.lower())]
        if kinds:
            handoffs.append(kinds)
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    low, full = line.lower(), (text or "").lower()
    body = SENDER.sub("", low)
    first = [name for name, prefix in FIRST if low.startswith(prefix[0])]
    features = {
        "dish": line.startswith("🍽️"),
        "final": bool(
            re.search(
                r"final report|closing (is )?(done|terminé)|fermeture terminée", low
            )
        ),
        "pause": "⏸️" in line,
        "restack": bool(re.search(r"restack request", low)),
        "confirm": bool(re.search(r"one confirmation before i merge", low)),
        "merged": bool(
            re.match(r"merged\b", body) or re.search(r"[·:]\s*merged\b", low)
        ),
        "close": bool(
            re.search(
                r"(?<!ne )(?<!pas )(?<!not )(?<!don't )ferme maintenant|(?<!not )(?<!don't )close now|rien à fusionner|nothing to merge",
                full,
            )
        ),
        "return": bool(
            re.search(
                r"décrit dans .* comportement|return(ing)? (the |your )?worktree|back to fix|à corriger",
                low,
            )
        ),
        "escalate": bool(re.search(r"question à pascal|asking pascal", full)),
    }
    first += [name for name, on in features.items() if on]
    lead = leading_symbol(body)
    out: dict[str, Any] = {"first": sorted(first)}
    if handoffs:
        out["handoffs"] = handoffs
    if lead:
        out["lead"] = lead
    step = re.search(r"\b([1-6])/6\b", line) if "progress" in first else None
    if step:
        out["step"] = int(step.group(1))
    return out


def checks_of(text: str) -> str:
    """What a 🍽️ Stack ready says of the checks on its frozen heads."""
    m = re.search(
        r"checks?\b[^\n]{0,60}?\b(pass(?:ed)?|green|success|ok|fail(?:ed)?|red|pending|none)\b",
        text or "",
        re.IGNORECASE,
    )
    return m.group(1).lower() if m else "unstated"


# Notices outside the Messages table, read by their leading symbol after any
# sender header: a ❓ question its sender keeps working through, a ⚠️ incident,
# a 📍 progress line or a note that opens with the sender's own status. None
# hands off work, so no status reads them; any other leading symbol stays
# "info", which the parser-coverage oracle counts as unclassified.
NOTES = {"❓": "question_note", "⚠️": "incident", "📍": "progress_note"}


def note(sig: dict, src: str) -> str:
    lead = sig.get("lead")
    if lead in NOTES:
        return NOTES[lead]
    return "status_note" if lead in STATUSES.get(src, ()) else "info"


def classify(sig: dict, src: str, dst: str) -> str:
    """Message kind, per carpaccio's Messages table.

    A handoff counts on any line, since a Cook may put a 📍 line before its
    🍽️ Stack ready block. Most other kinds use the first line only."""
    for kinds in sig.get("handoffs", []):
        for _, kind, senders in HANDOFFS:
            if kind in kinds and src in senders:
                return kind
    first = set(sig.get("first", []))
    for name, _ in FIRST:
        if name in first:
            return name
    if src == "cook" and dst == "chef":
        if first & {"dish", "final"}:
            return "cook_final"
        if "pause" in first:
            return "question"
        return note(sig, src)
    if src == "chef" and dst == "cook":
        if "restack" in first:
            return "restack"
        if "confirm" in first:
            return "return"
        if "merged" in first:
            return "merged_notice"
        if "close" in first:
            return "close_request"  # a card with nothing to merge closes on the Chef's word
        if "return" in first:
            return "return"
        return note(sig, src)
    if src == "chef" and dst == "head_chef":
        return "question" if "pause" in first else note(sig, src)
    if src == "head_chef" and dst == "chef":
        return "escalated" if "escalate" in first else "answer"
    return note(sig, src)


def ask_items(text: str) -> tuple[list[str], list[list[str]]]:
    """Items a Head Chef leaves for Pascal at the end of a message.

    carpaccio writes `🙋 <label> ...` lines; older routes wrote a `❓ Pour toi :`
    or `En attente de ta réponse :` block of numbered lines. Items return
    `merge` for merge or review requests, `item` otherwise, and `left` for
    final-report "Reste pour toi" entries.
    """
    out, refs, in_code, block = [], [], False, False
    for ln in (text or "").splitlines():
        s = ln.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        hm = re.match(
            r"(❓ pour toi|en attente de ta réponse|ce qui t'attend|reste pour toi)\s*:?",
            s,
            re.IGNORECASE,
        )
        if hm:
            block = "left" if hm.group(1).lower() == "reste pour toi" else True
            rest = s[hm.end() :].strip()
            if (
                block == "left"
                and rest
                and not re.match(r"rien|nothing|none", rest, re.IGNORECASE)
            ):
                out.append("left")
            continue
        item = None
        if s.startswith("🙋") or block and re.match(r"^(-|\d+[.)])\s", s):
            item = s
        elif block and s:
            block = False
        if item:
            if block == "left":
                out.append("left")
            else:
                out.append(
                    "merge"
                    if re.search(
                        r"\bmerge|fusion|revue du lot|review|relire",
                        item,
                        re.IGNORECASE,
                    )
                    else "item"
                )
            # "repo#N" for a URL; "#N" for a bare number, resolved against the run's repository later
            urls = {
                f"{r}#{n}"
                for r, n in re.findall(
                    r"github\.com/([\w.-]+/[\w.-]+)/(?:pull|issues)/(\d+)", item
                )
            }
            bare = {f"#{n}" for n in re.findall(r"(?<![\w/])#(\d+)", item)}
            refs.append(sorted(urls | bare))
    return out, refs


# --------------------------------------------------------------- watch.toml ---
# carpaccio watchdog.md Files: the plan keys the extractor reads. A Head Chef's
# file holds chef-<b> slots, a Chef's file cook-<b>.<c> slots. Runs before the
# slot names, such as 91c4, kept batches in [[batches]] with `batch = <b>`
WATCH_KEYS = ("slots", "slot", "threadId", "lastReceivedPhase", "replacedBy")
LEGACY_BATCH_KEYS = ("batches", "batch")
SLOT_NAME = re.compile(r"(?:chef-\d+|cook-\d+\.\d+)")
# Free-text slot metadata the extractor reads issue references from
BATCH_TEXT = ("name", "batchName")
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n\2[ \t]*(?:\n|$)", re.DOTALL
)
BLOCK = re.compile(r"\[\[(slots|batches)\]\]\n((?:[A-Za-z]\w* = [^\n]*(?:\n|$))+)")
WRITES = re.compile(
    r">\s*\S*watch\.toml|mv \S+ \S*watch\.toml|os\.replace|\.write\(|sed -i|\btee\b"
)
# A slot named in assignment syntax: `slot = "chef-3"`, an escaped or quoted
# copy of it, or a legacy `batch = 3`; a work folder path names no slot
MENTION = re.compile(
    r"""\bslot\s*=\s*\\?["']((?:chef-\d+|cook-\d+\.\d+))|\bbatch = (\d+)"""
)
ISSUE_REF = re.compile(
    r"(?:(?<![\w/.-])([\w.-]+/[\w.-]+|[A-Za-z][\w.-]*)|(?<![\w/]))#(\d+)"
)
PHASES = sorted({s for v in STATUSES.values() for s in v}, key=len, reverse=True)


def phase_of(value: object) -> str | None:
    """A slot's last received phase: its leading status emoji, or `queued`."""
    if not isinstance(value, str):
        return None
    if value.strip() in ("queued", "registered", ""):
        return "queued"
    return next((p for p in PHASES if value.strip().startswith(p)), "other")


def slot_of(raw: dict, repo: str | None = None) -> dict:
    out: dict[str, Any] = {"phase": phase_of(raw.get("lastReceivedPhase"))}
    thread = raw.get("threadId") or raw.get("chefThreadId")
    if isinstance(thread, str) and thread:
        out["thread"] = thread
    if isinstance(raw.get("replacedBy"), str):
        out["replacedBy"] = raw["replacedBy"]
    where = raw.get("repository")
    home = Path(where).name if isinstance(where, str) and where else repo
    refs = []
    for key in BATCH_TEXT:
        if isinstance(raw.get(key), str):
            refs += [[r or home, int(n)] for r, n in ISSUE_REF.findall(raw[key])]
    if refs:
        out["refs"] = refs
    if home:
        out["repo"] = home
    return out


def plan_of(doc: dict) -> dict[str, dict]:
    """Slot name -> slot facts from a parsed watch.toml or one of its blocks."""
    slots: dict[str, dict] = {}
    for raw in doc.get("slots") or []:
        if isinstance(raw, dict) and isinstance(raw.get("slot"), str):
            name = raw["slot"]
            if name == "head-chef" or SLOT_NAME.fullmatch(name):
                slots[name] = slot_of(raw)
    for raw in doc.get("batches") or []:
        if isinstance(raw, dict) and isinstance(raw.get("batch"), int):
            slots.setdefault(f"chef-{raw['batch']}", slot_of(raw))
    return slots


def parse_toml(text: str) -> dict | None:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None


def watch_write(text: str, full_text: bool = False) -> dict | None:
    """What a command, an edit or a file write does to watch.toml.

    `full` is the plan of a full write, parsed with tomllib; `blocks` the slots
    a [[slots]] or [[batches]] block adds; `mentions` every slot name the text
    names; `write` whether the text writes the file at all.
    """
    if "watch.toml" not in text and not full_text:
        return None
    out: dict[str, Any] = {"write": full_text or bool(WRITES.search(text))}
    bodies = [text] if full_text else [m.group(3) for m in HEREDOC.finditer(text)]
    rest = text
    for body in bodies:
        doc = parse_toml(body)
        if doc is not None and (
            "parentThreadId" in doc or "slots" in doc or "batches" in doc
        ):
            out["full"] = plan_of(doc)
            rest = rest.replace(body, "")
    blocks: dict[str, dict] = {}
    for candidate in (rest, rest.replace("\\n", "\n").replace('\\"', '"')):
        for m in BLOCK.finditer(candidate):
            doc = parse_toml(f"[[{m.group(1)}]]\n{m.group(2)}")
            if doc:
                for name, slot in plan_of(doc).items():
                    blocks.setdefault(name, slot)
    if blocks:
        out["blocks"] = blocks
    mentions = {name or f"chef-{n}" for name, n in MENTION.findall(rest)}
    if re.search(r"\breplacedBy\b", rest):
        mentions.add("replacedBy")
    if mentions:
        out["mentions"] = sorted(mentions)
    return out


# ------------------------------------------------------------------ reduce ---
def delegate_sop(title: str) -> str:
    low = title.lower()
    m = re.search(r"manic-(\d)", low)
    if "watchdog" in low:
        return "watchdog"
    if m:
        return f"manic-{m.group(1)}"
    if "fidelity" in low:
        return "fidelity"
    if "verify" in low:
        return "verify"
    return "review"


def output_of(d: dict) -> dict | None:
    o = d.get("output")
    if isinstance(o, dict):
        if o.get("structuredContent"):
            return o["structuredContent"]
        try:
            parsed = json.loads(o.get("content") or "null")
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


def launch_brief(message: str) -> dict:
    """The parts of a launch brief the extractor reads: issue numbers and the Batch line."""
    out: dict[str, Any] = {
        "refs": list(dict.fromkeys(int(n) for n in re.findall(r"#(\d+)", message)))
    }
    rl = re.search(r"^Release: (\w+)", message, re.MULTILINE | re.IGNORECASE)
    out["release"] = (
        (rl.group(1).lower() not in ("no", "non", "none", "aucune"))
        if rl
        else bool(re.search(r"\brelease\b", message, re.IGNORECASE))
    )
    bm = re.search(r"^Batch: (\d+), (.*)$", message, re.MULTILINE)
    if bm:
        rp = re.search(r"repository /\S+/([\w.-]+)", bm.group(2))
        out["batch"] = {
            "n": int(bm.group(1)),
            "repo": rp.group(1) if rp else None,
            "refs": sorted(
                {
                    (r or None, int(n))
                    for r, n in re.findall(
                        r"(?:([\w.-]+/[\w.-]+))?(?:#|/issues/)(\d+)", bm.group(2)
                    )
                },
                key=lambda x: (x[0] or "", x[1]),
            ),
        }
    return out


def reduce_tool(d: dict) -> dict | None:
    name = (d.get("toolName") or "").split("__")[-1]
    i = d.get("input") if isinstance(d.get("input"), dict) else {}
    assert isinstance(i, dict)
    if name == "t3_thread_launch":
        o = output_of(d) or {}
        return {
            "tool": "launch",
            "title": parse_title(i.get("title")),
            "project": i.get("projectId") or o.get("projectId"),
            "child": o.get("threadId"),
            **launch_brief(i.get("message") or ""),
        }
    if name == "t3_thread_send":
        text = i.get("message") or ""
        out = {"tool": "send", "to": i.get("threadId"), **signature(text)}
        if any("stack_ready" in kinds for kinds in out.get("handoffs", [])):
            out["checks"] = checks_of(text)
        return out
    if name == "delegate_task":
        o = output_of(d)
        return {
            "tool": "delegate",
            "sop": delegate_sop(i.get("title") or ""),
            "task": (o or {}).get("taskId"),
        }
    if name == "AskUserQuestion":
        return {"tool": "ask"}
    if name == "t3_thread_organize":
        return {
            "tool": "organize",
            "action": i.get("action"),
            "target": i.get("threadId"),
        }
    if name == "t3_thread_update" and i.get("action") == "rename":
        return {
            "tool": "rename",
            "target": i.get("threadId"),
            "title": parse_title(i.get("title")),
        }
    if name in ("link_pull_request", "t3_thread_update"):
        pr = i.get("pullRequest") if name == "t3_thread_update" else i
        if name == "t3_thread_update" and i.get("action") != "link_pull_request":
            return None
        if not isinstance(pr, dict):
            return None
        m = PR_URL.search(pr.get("url") or "")
        if m:
            return {"tool": "link", "pr": [m.group(1), int(m.group(2))]}
        if pr.get("repository") and pr.get("number"):
            return {"tool": "link", "pr": [pr["repository"], int(pr["number"])]}
        return None
    if name in ("Write", "Edit", "MultiEdit"):
        path = i.get("file_path") or ""
        if re.search(r"(?:^|/)watch\.toml(?:\.tmp)?$", path):
            if name == "Write":
                watch = watch_write(i.get("content") or "", full_text=True)
            else:
                edits = i.get("edits") or [i]
                watch = watch_write(
                    "watch.toml\n"
                    + "\n".join(str(e.get("new_string") or "") for e in edits),
                )
                if watch is not None:
                    watch["write"] = True
            return {"tool": "watch", "watch": watch}
    return None


def reduce_item(d: dict) -> dict | None:
    """A turn item without free text, or None when the extractor never reads its type."""
    typ = d.get("type")
    data: dict[str, Any] | None = None
    if typ == "user_message":
        if d.get("createdBy") != "user":
            return None
        text = (d.get("text") or "").lstrip()
        intent = (
            "slash"
            if text.startswith("/")
            else "stop"
            if re.search(r"\b(arr[eê]te|stop)\b", text, re.IGNORECASE)
            else "reply"
        )
        data = {"intent": intent}
    elif typ == "assistant_message":
        labels, refs = ask_items(d.get("text") or "")
        if not labels:
            return None
        data = {"items": labels, "refs": refs}
    elif typ == "dynamic_tool":
        data = reduce_tool(d)
    elif typ == "command_execution":
        command = d.get("input") if isinstance(d.get("input"), str) else ""
        assert isinstance(command, str)
        data = {}
        if RELEASE_COMMAND.search(command):
            data["release"] = True
        watch = watch_write(command)
        if watch:
            data["watch"] = watch
        data = data or None
    elif typ == "file_change":
        name = d.get("fileName") or ""
        if re.search(r"(?:^|/)watch\.toml$", name):
            diff = d.get("diffStr") or ""
            if diff.startswith("@@"):
                added = "\n".join(
                    ln[1:] for ln in diff.splitlines() if ln.startswith("+")
                )
                watch = watch_write("watch.toml\n" + added) or {}
                watch["write"] = True
            else:
                watch = watch_write(diff, full_text=True)
            data = {"tool": "watch", "watch": watch}
    if data is None:
        return None
    return {
        "thread": d["threadId"],
        "ordinal": d.get("ordinal", 0),
        "type": typ,
        "status": d.get("status"),
        "start": norm(d.get("startedAt") or d.get("updatedAt")),
        "end": norm(d.get("completedAt")),
        **data,
    }


def reduce_thread(d: dict) -> dict:
    lineage = d.get("lineage") or {}
    return {
        "project": d.get("projectId"),
        "created": norm(d.get("createdAt")),
        "title": parse_title(d.get("title")),
        "parent": lineage.get("parentThreadId"),
        "archived": norm(d.get("archivedAt")),
    }


def reduce_run(d: dict) -> dict:
    return {
        "thread": d["threadId"],
        "ordinal": d.get("ordinal", 0),
        "status": d.get("status"),
        "requested": norm(d.get("requestedAt")),
        "started": norm(d.get("startedAt")),
        "completed": norm(d.get("completedAt")),
    }


def reduce_subagent(d: dict) -> dict:
    return {
        "thread": d["threadId"],
        "status": d.get("status"),
        "started": norm(d.get("startedAt")),
        "completed": norm(d.get("completedAt")),
    }


def reduce(event_type: str, payload: dict) -> tuple[str, str, dict | None] | None:
    """(kind, entity id, whitelisted data) for one orchestration event, or None."""
    if event_type.startswith("thread.") and "title" in payload and "id" in payload:
        return "thread", payload["id"], reduce_thread(payload)
    if event_type == "turn-item.updated":
        return "item", payload["id"], reduce_item(payload)
    if event_type in ("run.created", "run.updated"):
        return "run", payload["id"], reduce_run(payload)
    if event_type == "subagent.updated":
        return "subagent", payload["id"], reduce_subagent(payload)
    return None


# -------------------------------------------------------------------- fold ---
@dataclass
class Snapshot:
    """The T3 database as of `seq`: the last record of each entity up to it."""

    threads: dict[str, dict] = field(default_factory=dict)
    items: dict[str, dict] = field(default_factory=dict)
    runs: dict[str, dict] = field(default_factory=dict)
    subagents: dict[str, dict] = field(default_factory=dict)
    projects: dict[str, str] = field(default_factory=dict)  # projectId -> repository
    titled: dict[str, list[tuple[str, dict | None]]] = field(default_factory=dict)
    seq: int = 0
    time: str = ""
    _by_thread: dict[str, dict[str, dict]] = field(default_factory=dict, repr=False)

    def apply(self, record: Record) -> bool:
        """Fold one record; return whether it changed the snapshot."""
        seq, time, kind, key, data = record
        self.seq, self.time = max(self.seq, seq), max(self.time, time or "")
        if kind == "project":
            if data and self.projects.get(key) != data.get("repo"):
                self.projects[key] = data.get("repo")
                return True
            return False
        table = {
            "thread": self.threads,
            "item": self.items,
            "run": self.runs,
            "subagent": self.subagents,
        }[kind]
        old = table.get(key)
        if plain(old) == data:
            return False
        if data is None:
            table.pop(key, None)
            if kind == "item" and old:
                self._by_thread.get(old["thread"], {}).pop(key, None)
            return old is not None
        if kind != "thread":
            # when the record of each fact arrived: a fact never shows before its record
            ended = data.get("completed" if kind != "item" else "end")
            data = {
                **data,
                "seen": old["seen"] if old else time,
                "endSeen": (old or {}).get("endSeen") or (time if ended else None),
            }
        table[key] = data
        if kind == "item":
            self._by_thread.setdefault(data["thread"], {})[key] = data
        if kind == "thread":
            history = self.titled.setdefault(key, [])
            if not history or history[-1][1] != data.get("title"):
                history.append((time, data.get("title")))
        return True

    def thread_items(self, thread: str) -> list[dict]:
        rows = self._by_thread.get(thread, {})
        return [rows[k] for k in sorted(rows, key=lambda k: (rows[k]["ordinal"], k))]

    def thread_runs(self, thread: str) -> list[tuple[str, dict]]:
        return sorted(
            ((k, r) for k, r in self.runs.items() if r["thread"] == thread),
            key=lambda kr: kr[1]["ordinal"],
        )

    def titles(self, thread: str) -> list[tuple[str, dict | None]]:
        """The thread's titles over time: thread records, then completed renames."""
        renames = [
            (
                later(item["end"], item.get("endSeen")) or item["start"],
                item["title"],
            )
            for items in self._by_thread.values()
            for item in items.values()
            if item.get("tool") == "rename"
            and item["status"] == "completed"
            and (item.get("target") or item["thread"]) == thread
        ]
        merged = sorted(self.titled.get(thread, []) + renames, key=lambda x: x[0])
        out: list[tuple[str, dict | None]] = []
        for time, title in merged:
            if not out or out[-1][1] != title:
                out.append((time, title))
        return out

    def title(self, thread: str) -> dict | None:
        history = self.titles(thread)
        return history[-1][1] if history else None

    def head_chef_since(self, thread: str) -> str | None:
        """When the thread became a Head Chef: its title's id4 is its own threadId suffix."""
        for time, title in self.titles(thread):
            if head_chef_title(thread, title):
                return time
        return None


ARRIVAL = ("seen", "endSeen")


def plain(data: dict | None) -> dict | None:
    """An entity's recorded fields, without the arrival times the fold adds."""
    return None if data is None else {k: v for k, v in data.items() if k not in ARRIVAL}


def later(fact: str | None, arrived: str | None) -> str | None:
    """When the page can show a fact: its own time, or its record's arrival if later."""
    known = [t for t in (fact, arrived) if t]
    return max(known) if known else None


def head_chef_title(thread: str, title: dict | None) -> bool:
    return bool(
        title and title["role"] == "head_chef" and thread[-4:].lower() == title["id4"]
    )


def fold(records: Iterable[Record], upto: int | None = None) -> Snapshot:
    snap = Snapshot()
    for record in records:
        if upto is not None and record[0] > upto:
            break
        snap.apply(record)
    return snap


# ---------------------------------------------------------------- database ---
def events(
    con: sqlite3.Connection,
    *,
    stream: str | None = None,
    after: int = 0,
    upto: int | None = None,
) -> Iterator[Record]:
    """Reduced records of the events after `after`, in sequence order."""
    where = ["aggregate_kind = 'thread'", "sequence > ?"]
    args: list[Any] = [after]
    if stream is not None:
        where.append("stream_id = ?")
        args.append(stream)
    if upto is not None:
        where.append("sequence <= ?")
        args.append(upto)
    where.append(
        f"(event_type in ({','.join('?' * len(EVENTS))}) or event_type like 'thread.%')"
    )
    args += EVENTS
    rows = con.execute(
        "select sequence, occurred_at, event_type, payload_json from orchestration_events "
        f"where {' and '.join(where)} order by sequence",
        args,
    ).fetchall()  # fetch at once: no read transaction stays open while records fold
    for seq, occurred, event_type, payload in rows:
        reduced = reduce(event_type, json.loads(payload))
        if reduced is not None:
            yield [seq, norm(occurred), *reduced]


def last_sequence(con: sqlite3.Connection) -> int:
    row = con.execute("select max(sequence) from orchestration_events").fetchone()
    return int(row[0] or 0)


def project_repos(con: sqlite3.Connection) -> dict[str, str]:
    """T3 projects -> the folder name of their workspace, a repository name."""
    return {
        pid: Path(root).name
        for pid, root in con.execute(
            "select project_id, workspace_root from projection_projects"
        ).fetchall()
    }


class DatabaseError(Exception):
    """The T3 database cannot be read; `temporary` says whether a retry may fix it."""

    def __init__(self, message: str, temporary: bool = False) -> None:
        super().__init__(message)
        self.temporary = temporary


def connect(path: str | Path, timeout: float) -> sqlite3.Connection:
    """A read-only connection that never writes T3's live database.

    Each query fetches its rows at once, so no read transaction stays open
    between reads and T3's WAL can checkpoint.
    """
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise DatabaseError(
            f"No T3 database at {source}; rerun with --db PATH pointing to statev2.sqlite"
        )
    try:
        con = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=timeout)
        con.execute("pragma query_only=on")
    except sqlite3.OperationalError as error:
        raise DatabaseError(
            f"Cannot open T3 database read-only: {source}; rerun with --db PATH pointing to statev2.sqlite"
        ) from error
    return con


def database_files(path: str | Path) -> set[Path]:
    """T3's database and the files SQLite keeps beside it: no output may name one."""
    source = Path(path).expanduser().resolve()
    return {source} | {
        source.with_name(source.name + end) for end in ("-wal", "-shm", "-journal")
    }


def head_chefs(
    con: sqlite3.Connection, since: str | None = None, only: Iterable[str] = ()
) -> list[str]:
    """Head Chef threads: titled `Head Chef <id4>` where id4 ends their own threadId.

    A thread that only talks about a run, such as "Head Chef 91c4 status
    reconciliation", carries another threadId and is not its Head Chef.
    """
    wanted = {x.lower() for x in only}
    rows = con.execute(
        "select thread_id, title, created_at from orchestration_v2_projection_threads "
        "where title like 'Head Chef %' and created_at >= ? order by created_at, thread_id",
        (since or "",),
    ).fetchall()
    return [
        tid
        for tid, title, _ in rows
        if head_chef_title(tid, parse_title(title))
        and (not wanted or tid[-4:].lower() in wanted)
    ]


def load(
    con: sqlite3.Connection, heads: Iterable[str], upto: int | None = None
) -> tuple[Snapshot, list[Record]]:
    """Each Head Chef's run as of `upto`: its stream, then every thread it or its
    children launched, read stream by stream at one sequence.

    Delegated threads, such as barrages and Watchdogs, are left out: their
    parent's subagent records hold what the extractor reads of them.
    """
    upto = last_sequence(con) if upto is None else upto
    records: list[Record] = []
    queue, seen = list(heads), set()
    while queue:
        stream = queue.pop(0)
        if stream in seen:
            continue
        seen.add(stream)
        mine = list(events(con, stream=stream, upto=upto))
        records += mine
        for _, _, kind, _, data in mine:
            if (
                kind == "item"
                and data
                and data.get("tool") == "launch"
                and data.get("child")
            ):
                queue.append(data["child"])
    records.sort(key=lambda r: r[0])
    snap = Snapshot(projects=project_repos(con))
    for record in records:
        snap.apply(record)
    snap.seq = max(snap.seq, upto)
    return snap, records


def projection(con: sqlite3.Connection, threads: Iterable[str]) -> Snapshot:
    """The same threads reduced from T3's own projection tables, to check a fold against."""
    snap = Snapshot()
    for tid in threads:
        row = con.execute(
            "select payload_json from orchestration_v2_projection_threads where thread_id=?",
            (tid,),
        ).fetchone()
        if row:
            snap.threads[tid] = reduce_thread(json.loads(row[0]))
        for item_id, payload in con.execute(
            "select turn_item_id, payload_json from orchestration_v2_projection_turn_items where thread_id=?",
            (tid,),
        ).fetchall():
            data = reduce_item(json.loads(payload))
            if data is not None:
                snap.items[item_id] = data
        for run_id, payload in con.execute(
            "select run_id, payload_json from orchestration_v2_projection_runs where thread_id=?",
            (tid,),
        ).fetchall():
            snap.runs[run_id] = reduce_run(json.loads(payload))
        for sub_id, payload in con.execute(
            "select subagent_id, payload_json from orchestration_v2_projection_subagents where thread_id=?",
            (tid,),
        ).fetchall():
            snap.subagents[sub_id] = reduce_subagent(json.loads(payload))
    return snap


# --------------------------------------------------------------- whitelist ---
# Every key a recording may hold. A value is a number, a boolean, null, or a
# string with no whitespace: an id, a time, an emoji or a word the reducer
# chose. Free text always holds a space, so a leak fails the check
SLOT_KEYS = {"phase", "thread", "replacedBy", "refs", "repo"}
WHITELIST: dict[str, set[str]] = {
    "project": {"repo"},
    "thread": {"project", "created", "title", "parent", "archived"},
    "run": {"thread", "ordinal", "status", "requested", "started", "completed"},
    "subagent": {"thread", "status", "started", "completed"},
    "item": {
        *("thread", "ordinal", "type", "status", "start", "end"),
        *("intent", "items", "refs", "release", "watch"),
        *("tool", "title", "project", "child", "batch"),
        *("to", "first", "handoffs", "lead", "step", "checks"),
        *("sop", "task", "action", "target", "pr"),
    },
    "title": {"role", "id4", "status", "b", "c", "n"},
    "batch": {"n", "repo", "refs"},
    "watch": {"full", "blocks", "mentions", "write"},
}
SLOT_KEY = re.compile(r"head-chef|chef-\d+|cook-\d+\.\d+")


def value_errors(path: str, v: object) -> list[str]:
    """Why a value is no number, boolean, null or whitespace-free string, or list of them."""
    if isinstance(v, str):
        if not v or len(v) > 120 or re.search(r"\s", v):
            return [f"{path}: free text {v[:40]!r}"]
    elif isinstance(v, list):
        return [e for i, x in enumerate(v) for e in value_errors(f"{path}[{i}]", x)]
    elif isinstance(v, dict):
        return [f"{path}: unexpected object"]
    elif not (v is None or isinstance(v, (int, float, bool))):
        return [f"{path}: unexpected {type(v).__name__}"]
    return []


def whitelist_errors(record: Record) -> list[str]:
    """Why a record falls outside the whitelist; empty when it fits."""
    _, time, kind, key, data = record
    errors: list[str] = []

    def value(path: str, v: object) -> None:
        errors.extend(value_errors(path, v))

    def obj(path: str, d: object, allowed: set[str]) -> None:
        if not isinstance(d, dict):
            value(path, d)
            return
        for k, v in d.items():
            if k not in allowed:
                errors.append(f"{path}.{k}: key outside the whitelist")
            elif k in ("title", "batch", "watch") and isinstance(v, dict):
                obj(f"{path}.{k}", v, WHITELIST[k])
            elif k in ("full", "blocks") and isinstance(v, dict):
                for name, s in v.items():
                    if not SLOT_KEY.fullmatch(name):
                        errors.append(f"{path}.{k}: slot name {name[:40]!r}")
                    obj(f"{path}.{k}.{name}", s, SLOT_KEYS)
            else:
                value(f"{path}.{k}", v)

    if kind not in ("project", "thread", "run", "subagent", "item"):
        return [f"{kind}: unknown record kind"]
    value("time", time)
    value("id", key)
    if data is not None:
        obj(kind, data, WHITELIST[kind])
    return errors


# -------------------------------------------------------------- recordings ---
FORMAT = 1


def load_recording(path: str | Path) -> dict:
    """A recording written by record.py, gzipped or not."""
    raw = Path(path).read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    data = json.loads(raw)
    if data.get("format") != FORMAT:
        raise ValueError(
            f"{path} is recording format {data.get('format')}, expected {FORMAT}"
        )
    return data


def disk_plans(id4: str, root: Path = Path("~/.cache")) -> dict[str, dict]:
    """A live run's watch.toml files by work folder, with their write time; Close removes them."""
    out = {}
    for path in sorted((root / f"brigade-{id4}").expanduser().glob("*/watch.toml")):
        try:
            doc = parse_toml(path.read_text(encoding="utf-8"))
            mtime = path.stat().st_mtime
        except OSError:
            continue  # removed between the listing and the read
        if doc is None:
            continue
        stamp = datetime.fromtimestamp(mtime, UTC).isoformat(timespec="milliseconds")
        out[path.parent.name] = {
            "time": stamp.replace("+00:00", "Z"),
            "plan": plan_of(doc),
        }
    return out

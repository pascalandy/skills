"""T3 and GitHub facts in the replay KEYS shape; I/O is supplied by the command."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

KEYS = (
    "time",
    "brigade",
    "role",
    "thread",
    "parent",
    "kind",
    "status",
    "epic",
    "story",
    "pr",
    "detail",
)
EMOJI = ["🟢", "⏳", "🍳", "❓", "🔀", "🧹", "🍽️", "⏸️", "⛳", "⏹️"]
PR_URL = re.compile(r"github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)")


def norm(ts: str | None) -> str | None:
    """GitHub drops milliseconds; T3 keeps them. One format for sorting."""
    if not ts:
        return None
    m = re.match(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?Z", ts)
    if m is None:
        raise ValueError(f"Invalid T3 or GitHub timestamp: {ts!r}")
    return f"{m.group(1)}{(m.group(2) or '.000')[:4].ljust(4, '0')}Z"


def items(con: sqlite3.Connection, thread: str) -> Iterator[tuple[str, str, dict]]:
    for typ, status, p in con.execute(
        "select type,status,payload_json from orchestration_v2_projection_turn_items "
        "where thread_id=? order by ordinal, turn_item_id",
        (thread,),
    ):
        yield typ, status, json.loads(p)


def out_of(d: dict) -> dict | None:
    o = d.get("output")
    if isinstance(o, dict):
        if o.get("structuredContent"):
            return o["structuredContent"]
        try:
            return json.loads(o.get("content") or "null")
        except (TypeError, ValueError):
            return None
    return None


def emoji_of(title: str) -> str | None:
    """The status a title claims: the first status emoji after the role prefix."""
    title = re.sub(r"^(🧑‍🍳|🚥)\s*", "", title)  # 🧑‍🍳 holds 🍳: skip the role mark
    best = None
    for e in EMOJI:
        i = title.find(e)
        if i >= 0 and (best is None or i < best[0]):
            best = (i, e)
    return best[1] if best else None


def counter_of(title: str) -> str | None:
    m = re.search(r"\[?(\d+)/(\d+)\]?", title)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def repo_of_project(con: sqlite3.Connection, project_id: str | None) -> str | None:
    if not project_id:
        return None
    row = con.execute(
        "select workspace_root from projection_projects where project_id=?",
        (project_id,),
    ).fetchone()
    return Path(row[0]).name if row else None


HANDOFFS = [  # (pattern at a line start, kind, roles that may send it)
    (r"^🍽️ stack ready", "stack_ready", {"cook"}),
    (r"^🍽️ batch ready", "batch_ready", {"chef"}),
    (r"^🔀 batch merging", "batch_merging", {"chef"}),
    (r"^🔀 merge", "merge", {"head_chef"}),
    (r"^batch merged", "batch_merged", {"chef"}),
    (r"^⛳ batch delivered", "batch_delivered", {"chef"}),
    (r"^⏹️ batch stopped", "batch_stopped", {"chef"}),
    (r"^⏹️ stopped", "cook_stopped", {"cook"}),
    (r"^⏹️ stop", "stop", {"head_chef", "chef"}),
    (r"^⏹️ cut", "cut", {"head_chef", "chef"}),
    (r"^⏹️ drop", "drop", {"head_chef"}),
    (r"^⏳ rework", "rework", {"head_chef"}),
    (r"^🍽️ hold", "hold", {"head_chef"}),
]


def classify(text: str, src: str, dst: str) -> str:
    """Message kind, per carpaccio's Messages table.

    A handoff counts on any line, since a Cook may put a 📍 line before its
    🍽️ Stack ready block; everything else reads the first line only."""
    lines, fenced = [], False
    for ln in (text or "").strip().splitlines():
        if ln.strip().startswith("```"):
            fenced = not fenced
        elif ln.strip() and not fenced and not ln.lstrip().startswith(">"):
            lines.append(
                ln.strip().lower()
            )  # an example in a fence or a quote hands nothing off
    for ln in lines:
        for pat, kind, senders in HANDOFFS:
            if src in senders and re.search(pat, ln):
                return kind
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    low = line.lower()
    for pat, kind in (
        (r"^🐕", "watchdog"),
        (r"^🙋", "pascal_card"),
        (r"^📍", "progress"),
    ):
        if re.search(pat, low):
            return kind
    if src == "cook" and dst == "chef":
        if line.startswith("🍽️") or re.search(
            r"final report|closing (is )?(done|terminé)|fermeture terminée", low
        ):
            return "cook_final"
        if "⏸️" in line:
            return "question"
        return "info"
    if src == "chef" and dst == "cook":
        if re.search(r"restack request", low):
            return "restack"
        if re.search(r"one confirmation before i merge", low):
            return "return"
        body = re.sub(
            r"^(?:🚥\s*)?chef \d+ \w{4}\s*(?:→\s*cook [\d.]+)?\s*[:·,—-]*\s*", "", low
        )
        if re.match(r"merged\b", body) or re.search(r"[·:]\s*merged\b", low):
            return "merged_notice"
        if re.search(
            r"(?<!ne )(?<!pas )(?<!not )(?<!don't )ferme maintenant|(?<!not )(?<!don't )close now|rien à fusionner|nothing to merge",
            (text or "").lower(),
        ):
            return "close_request"  # a card with nothing to merge closes on the Chef's word
        if re.search(
            r"décrit dans .* comportement|return(ing)? (the |your )?worktree|back to fix|à corriger",
            low,
        ):
            return "return"
        return "info"
    if src == "chef" and dst == "head_chef":
        return "question" if "⏸️" in line else "info"
    if src == "head_chef" and dst == "chef":
        if re.search(r"question à pascal|asking pascal", text or "", re.IGNORECASE):
            return "escalated"
        return "answer"
    return "info"


def ask_items(text: str) -> tuple[list[str], list[list[str]]]:
    """Items a Head Chef leaves for Pascal at the end of a message.

    carpaccio writes `🙋 <label> ...` lines; older routes wrote a `❓ Pour toi :`
    or `En attente de ta réponse :` block of numbered lines. Each item is
    returned as `merge` when it asks for a merge or a batch review, else `item`.
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


def cmd_verbs(cmd: str) -> list[str]:
    v = set()
    for m in re.finditer(
        r"\bgh (pr|issue|api|stack|repo|run|release|signoff|search)\b(?: (\w[\w-]*))?",
        cmd,
    ):
        v.add(
            f"gh {m.group(1)}"
            + (
                f" {m.group(2)}"
                if m.group(1) in ("pr", "issue", "stack", "release", "run")
                and m.group(2)
                else ""
            )
        )
    for m in re.finditer(r"\bjust ([a-z][\w-]*)", cmd):
        v.add(f"just {m.group(1)}")
    if re.search(r"git push origin \S+:main", cmd):
        v.add("git push :main")
    return sorted(v)


class Brigade:
    def __init__(self, con: sqlite3.Connection, thread_id: str) -> None:
        self.con = con
        self.id4 = thread_id[-4:]
        self.hc = thread_id
        self.threads: dict[
            str, dict
        ] = {}  # threadId -> {key, role, parent, label, repo}
        self.events: list[dict] = []
        self.prs: dict[tuple[str, int], dict] = {}  # (repo, n) -> {cook, opened_by}
        self.batch_refs: dict[int, dict] = {}  # batch -> {repo, refs, time, how}

    def q(self, sql: str, *args: object) -> list:
        return self.con.execute(sql, args).fetchall()

    def ev(
        self,
        time: str | None,
        role: str,
        thread: str,
        kind: str,
        parent: str | None = None,
        status: str | None = None,
        epic: str | None = None,
        story: str | None = None,
        pr: str | None = None,
        **detail: object,
    ) -> None:
        self.events.append(
            {
                "time": norm(time),
                "brigade": self.id4,
                "role": role,
                "thread": thread,
                "parent": parent,
                "kind": kind,
                "status": status,
                "epic": epic,
                "story": story,
                "pr": pr,
                "detail": {k: v for k, v in sorted(detail.items()) if v is not None}
                or None,
            }
        )

    def walk(self) -> None:
        self.threads[self.hc] = {
            "key": "hc",
            "role": "head_chef",
            "parent": None,
            "label": f"Head Chef {self.id4}",
        }
        stack = [self.hc]
        seen_keys = {"hc"}
        while stack:
            t = stack.pop(0)
            for typ, _, d in items(self.con, t):
                if typ != "dynamic_tool" or not d["toolName"].endswith(
                    "t3_thread_launch"
                ):
                    continue
                o = out_of(d)
                if not (o and o.get("threadId")):
                    continue
                title = d["input"].get("title", "")
                m = re.search(r"Cook (\d+)\.(\d+)", title) or re.search(
                    r"Chef (\d+)", title
                )
                if not m:
                    continue
                if "Cook" in title:
                    key, role, label = (
                        f"cook-{m.group(1)}.{m.group(2)}",
                        "cook",
                        f"Cook {m.group(1)}.{m.group(2)}",
                    )
                else:
                    key, role, label = (
                        f"chef-{m.group(1)}",
                        "chef",
                        f"Chef {m.group(1)}",
                    )
                base, n = key, 2
                while key in seen_keys:  # a replacement takes the slot; keep both apart
                    key, n = f"{base}#{n}", n + 1
                seen_keys.add(key)
                msg = d["input"].get("message", "")
                repo = repo_of_project(
                    self.con, d["input"].get("projectId") or o.get("projectId")
                )
                brief_refs = list(
                    dict.fromkeys(int(n) for n in re.findall(r"#(\d+)", msg))
                )  # in brief order
                release = None
                if role == "chef":
                    rl = re.search(
                        r"^Release: (\w+)", msg, re.MULTILINE | re.IGNORECASE
                    )
                    release = (
                        (rl.group(1).lower() not in ("no", "non", "none", "aucune"))
                        if rl
                        else bool(re.search(r"\brelease\b", msg, re.IGNORECASE))
                    )
                self.threads[o["threadId"]] = {
                    "key": key,
                    "role": role,
                    "parent": t,
                    "label": label,
                    "repo": repo,
                    "release": release,
                    "refs": brief_refs,
                }
                if role == "chef":
                    bm = re.search(r"^Batch: (\d+), (.*)$", msg, re.MULTILINE)
                    if bm:
                        b = int(bm.group(1))
                        refs = re.findall(
                            r"(?:([\w.-]+/[\w.-]+))?(?:#|/issues/)(\d+)", bm.group(2)
                        )
                        rp = re.search(r"repository /\S+/([\w.-]+)", bm.group(2))
                        self.batch_refs.setdefault(
                            b,
                            {
                                "repo": rp.group(1) if rp else repo,
                                "refs": [],
                                "time": None,
                            },
                        )
                        self.batch_refs[b]["refs"] = sorted(
                            {
                                (r or (rp.group(1) if rp else repo), int(n))
                                for r, n in refs
                            }
                        )
                stack.append(o["threadId"])

    def key(self, thread_id: str | None) -> str | None:
        t = self.threads.get(thread_id or "")
        return t["key"] if t else None

    def t3(self) -> None:
        self.threads_by_key = {v["key"]: v["role"] for v in self.threads.values()}
        delegates = []  # (thread, d)
        for tid, info in self.threads.items():
            me, role = info["key"], info["role"]
            parent = self.key(info["parent"]) if info["parent"] else None
            for typ, status, d in items(self.con, tid):
                t0 = d.get("startedAt") or d.get("updatedAt")
                if typ == "user_message":
                    text = d.get("text") or ""
                    if d.get("createdBy") == "user":
                        stop = bool(
                            re.search(r"\b(arr[eê]te|stop)\b", text, re.IGNORECASE)
                        )
                        self.ev(
                            t0,
                            "pascal",
                            me,
                            "pascal_msg",
                            intent="stop" if stop else "reply",
                            text=text[:160],
                        )
                elif typ == "assistant_message" and role == "head_chef":
                    labels, irefs = ask_items(d.get("text") or "")
                    if labels:
                        self.ev(
                            t0,
                            role,
                            me,
                            "ask_pascal",
                            items=labels,
                            irefs=irefs if any(irefs) else None,
                        )
                elif typ == "command_execution":
                    command = d.get("input")
                    cmd = command if isinstance(command, str) else ""
                    verbs = cmd_verbs(cmd)
                    if verbs:
                        self.ev(
                            t0,
                            role,
                            me,
                            "cmd",
                            parent=parent,
                            verbs=verbs,
                            end=norm(d.get("completedAt")),
                            ok=status == "completed",
                        )
                    if role == "head_chef" and "watch.toml" in cmd:
                        for bm in re.finditer(
                            r'batch = (\d+)\nname = "([^"]*)"((?:\n(?!\[\[)[^\n]*)*)',
                            cmd,
                        ):
                            b = int(bm.group(1))
                            st = re.search(r'\nstate = "([^"]*)"', bm.group(3))
                            self.ev(
                                t0,
                                role,
                                me,
                                "batch_register",
                                batch=b,
                                name=bm.group(2),
                                state=st.group(1) if st else None,
                            )
                        if re.search(r"cut by Pascal", cmd):
                            self.ev(t0, role, me, "batch_cut", how="proposed-cut")
                    if role == "chef" and "watch.toml" in cmd:
                        for field in ("plannedSlots", "pendingSlots"):
                            sets = re.findall(field + r" = \[([^\]]*)\]", cmd)
                            if sets:  # the last assignment is the new value; a replace() names the old one first
                                self.ev(
                                    t0,
                                    role,
                                    me,
                                    "cook_planned",
                                    field=field,
                                    slots=sorted(
                                        set(re.findall(r"cook-\d+\.\d+", sets[-1]))
                                    ),
                                )
                            elif re.search(
                                r"\^?"
                                + field
                                + r" = \.\*\\n['\"]\s*,\s*(''|\"\")|/\^?"
                                + field
                                + r"/d",
                                cmd,
                            ):
                                self.ev(
                                    t0, role, me, "cook_planned", field=field, slots=[]
                                )
                elif typ == "dynamic_tool":
                    tn = d["toolName"].split("__")[-1]
                    i = d.get("input") or {}
                    if tn == "t3_thread_update" and i.get("action") == "rename":
                        title = i.get("title", "")
                        self.ev(
                            t0,
                            role,
                            me,
                            "rename",
                            parent=parent,
                            status=emoji_of(title),
                            title=title,
                            counter=counter_of(title),
                        )
                    elif tn == "t3_thread_launch":
                        o = out_of(d)
                        if o and o.get("threadId"):
                            ci = self.threads.get(o["threadId"])
                            if ci is None:
                                continue
                            self.ev(
                                t0,
                                ci["role"],
                                ci["key"],
                                "launch",
                                parent=me,
                                label=ci["label"],
                                repo=ci.get("repo"),
                                release=ci.get("release"),
                                threadId=o["threadId"],
                                title=i.get("title"),
                            )
                        else:
                            self.ev(t0, role, me, "launch_error", title=i.get("title"))
                    elif tn == "t3_thread_send":
                        to = i.get("threadId")
                        tk = self.key(to)
                        trole = (
                            self.threads[to]["role"] if to in self.threads else "other"
                        )
                        text = i.get("message") or ""
                        msg = classify(text, role, trole)
                        checks = None
                        if (
                            msg == "stack_ready"
                        ):  # the Cook reports its checks on the frozen heads
                            cm = re.search(
                                r"checks?\b[^\n]{0,60}?\b(pass(?:ed)?|green|success|ok|fail(?:ed)?|red|pending|none)\b",
                                text,
                                re.IGNORECASE,
                            )
                            checks = cm.group(1).lower() if cm else "unstated"
                        self.ev(
                            t0,
                            role,
                            me,
                            "send",
                            parent=parent,
                            to=tk or "other",
                            msg=msg,
                            checks=checks,
                            first=text.strip().splitlines()[0][:160]
                            if text.strip()
                            else "",
                        )
                    elif tn == "delegate_task":
                        delegates.append((me, role, d))
                    elif tn == "AskUserQuestion":
                        self.ev(
                            t0,
                            role,
                            me,
                            "ask_pascal",
                            items=["question"],
                            answered=norm(d.get("completedAt")),
                        )
                    elif tn == "t3_thread_organize":
                        target = (
                            self.key(i.get("threadId")) if i.get("threadId") else me
                        )
                        self.ev(
                            t0,
                            role,
                            me,
                            "organize",
                            action=i.get("action"),
                            target=target or "delegate",
                        )
                    elif tn == "link_pull_request":
                        m = PR_URL.search(i.get("url", ""))
                        if m:
                            k = (m.group(1), int(m.group(2)))
                            cur = self.prs.get(k)
                            # the Cook that links a PR owns it; a Chef or Head Chef may link it too
                            if cur is None or (
                                role == "cook"
                                and self.threads_by_key[cur["by"]] != "cook"
                            ):
                                self.prs[k] = {"by": me, "at": t0}
            for rid, st, ra, ca in self.q(
                "select run_id,status,requested_at,completed_at from orchestration_v2_projection_runs where thread_id=? order by ordinal",
                tid,
            ):
                self.ev(ra, role, me, "run_start", run=rid.rsplit(":", 1)[-1])
                if ca:
                    self.ev(
                        ca, role, me, "run_end", run=rid.rsplit(":", 1)[-1], state=st
                    )
        self.delegates(delegates)

    def delegates(self, delegates: list[tuple[str, str, dict]]) -> None:
        rounds = defaultdict(int)
        for me, role, d in delegates:
            if role != "cook":
                continue
            i = d.get("input") or {}
            title = i.get("title") or ""
            o = out_of(d)
            t0 = d.get("startedAt")
            low = title.lower()
            m = re.search(r"manic-(\d)", low)
            if "watchdog" in low:
                kind, sop = "watchdog", "watchdog"
            elif m:
                kind, sop = "barrage", f"manic-{m.group(1)}"
            elif "fidelity" in low:
                kind, sop = "barrage", "fidelity"
            elif "verify" in low:
                kind, sop = "side", "verify"
            else:
                kind, sop = "side", "review"
            if not o:
                self.ev(
                    t0, kind, f"{kind}:{me}:{sop}", "delegate_error", parent=me, sop=sop
                )
                continue
            rounds[(me, sop)] += 1
            r = rounds[(me, sop)]
            dk = f"{kind}:{me}:{sop}" + (
                f":r{r}" if kind != "watchdog" else (f":arm{r}" if r > 1 else "")
            )
            sub = self.q(
                "select started_at, completed_at, status from orchestration_v2_projection_subagents where subagent_id=?",
                o.get("taskId"),
            )
            sa, ca, st = sub[0] if sub else (t0, None, "unknown")
            self.ev(sa or t0, kind, dk, "delegate_start", parent=me, sop=sop, round=r)
            if ca:
                self.ev(
                    ca, kind, dk, "delegate_end", parent=me, sop=sop, round=r, state=st
                )

    def github(self, gh: GitHub) -> None:
        for (repo, n), meta in sorted(self.prs.items()):
            p = gh.pr(repo, n)
            cook = meta["by"]
            pr = f"{repo}#{n}"
            found = gh.stories_of(repo, p)
            # one row per Story the PR closes or names; a PR without an issue is its own Story
            targets = [(f"{r}#{x}", gh.epic_of(r, x)) for r, x in found] or [
                (pr, gh.epic_ref(repo, p))
            ]
            for s, epic in targets:
                e = f"{epic[0]}#{epic[1]}" if epic else None
                loose = (not found) or None
                self.ev(
                    p["createdAt"],
                    "github",
                    cook,
                    "pr_open",
                    epic=e,
                    story=s,
                    pr=pr,
                    loose=loose,
                )
                if p["mergedAt"]:
                    self.ev(
                        p["mergedAt"],
                        "github",
                        cook,
                        "pr_merge",
                        epic=e,
                        story=s,
                        pr=pr,
                    )
                elif p["closedAt"]:
                    self.ev(
                        p["closedAt"],
                        "github",
                        cook,
                        "pr_close",
                        epic=e,
                        story=s,
                        pr=pr,
                    )
        # Pascal may answer a 🙋 item on GitHub: merging or closing the PR it names.
        repos = [repo for info in self.threads.values() if (repo := info.get("repo"))]
        main_repo = max(set(repos), key=repos.count) if repos else None
        for e in list(self.events):
            if e["kind"] == "ask_pascal" and (e["detail"] or {}).get("irefs"):
                for ref in sorted({x for r in e["detail"]["irefs"] for x in r}):
                    repo, n = ref.split("#")
                    repo = repo or main_repo
                    x = gh.item(repo, int(n)) if repo else None
                    if x and x.get("mergedAt") and norm(x["mergedAt"]) > e["time"]:
                        self.ev(
                            x["mergedAt"],
                            "pascal",
                            "hc",
                            "pascal_github",
                            pr=f"{repo}#{n}",
                            action="merged",
                        )
                    elif x and x.get("closedAt") and norm(x["closedAt"]) > e["time"]:
                        self.ev(
                            x["closedAt"],
                            "pascal",
                            "hc",
                            "pascal_github",
                            pr=f"{repo}#{n}",
                            action="closed",
                        )
        # Scope: a batch names Stories or an Epic; an Epic brings every sub-issue.
        launches = {
            e["thread"]: e["time"] for e in self.events if e["kind"] == "launch"
        }
        regs = {}
        for e in self.events:
            if e["kind"] == "batch_register":
                regs.setdefault(e["detail"]["batch"], (e["time"], e["detail"]["name"]))
        batches = set(self.batch_refs) | set(regs)
        for b in sorted(batches):
            chef = f"chef-{b}"
            info = self.batch_refs.get(b, {})
            repo = info.get("repo") or main_repo
            refs: list[tuple[str, int]] = info.get("refs") or (
                [
                    (repo, int(n))
                    for n in re.findall(r"#(\d+)", regs.get(b, ("", ""))[1])
                ]
                if repo
                else []
            )
            t_in = regs[b][0] if b in regs else launches.get(chef)
            if b in regs and chef in launches and launches[chef] < regs[b][0]:
                t_in = launches[chef]
            refs = [r for r in refs if r[0]]
            stories = [r for r in refs if not gh.is_epic(*r)]
            epics = [r for r in refs if gh.is_epic(*r)]
            if stories:
                for r in stories:
                    ep = gh.epic_of(*r)
                    self.scope(gh, t_in, chef, r, ep, b)
            else:
                end = max(e["time"] for e in self.events)
                for ep in epics:
                    for sub in gh.subissues(*ep):
                        created = norm(sub["createdAt"])
                        # A Story filed after the run belongs to a later run.
                        if t_in and created and created <= end:
                            self.scope(
                                gh,
                                max(t_in, created),
                                chef,
                                (sub["repository"]["nameWithOwner"], sub["number"]),
                                ep,
                                b,
                            )
        # A Story found only through a PR, or a PR without an issue, joins the scope when its batch did
        regs_t = {}
        for e in self.events:
            if e["kind"] == "batch_register":
                regs_t.setdefault(e["detail"]["batch"], e["time"])
        cook_chef = {
            v["key"]: self.key(v["parent"])
            for v in self.threads.values()
            if v["role"] == "cook"
        }
        scoped = {e["story"] for e in self.events if e["kind"] == "story_scope"}
        for e in sorted(
            (e for e in self.events if e["kind"] == "pr_open"), key=lambda e: e["time"]
        ):
            if e["story"] in scoped:
                continue
            chef = cook_chef.get(e["thread"])
            bn = int(chef.split("-")[1].split("#")[0]) if chef else None
            t_in = min(x for x in (regs_t.get(bn), launches.get(chef), e["time"]) if x)
            if (e["detail"] or {}).get("loose"):
                self.ev(
                    t_in,
                    "github",
                    chef or "hc",
                    "story_scope",
                    epic=e["epic"],
                    story=e["story"],
                    batch=bn,
                    state_at_scope="open",
                )
            else:
                r, n = e["story"].split("#")
                self.scope(gh, t_in, chef, (r, int(n)), gh.epic_of(r, int(n)), bn)
            scoped.add(e["story"])
        # A Cook owns from its launch the first Story of its batch that its brief names
        # and that has no PR yet; the others start at their first PR.
        # A Story two briefs pick first stays unassigned
        pr_at = {}
        for e in self.events:
            if e["kind"] == "pr_open":
                pr_at.setdefault(e["story"], e["time"])
        by_chef = defaultdict(set)
        for e in self.events:
            if e["kind"] == "story_scope" and e["thread"]:
                by_chef[e["thread"]].add(e["story"])
        firsts = {}
        for v in self.threads.values():
            if v["role"] != "cook":
                continue
            chef = self.key(v["parent"])
            scope = {int(st.split("#")[1]): st for st in by_chef.get(chef, ())}
            at = launches.get(v["key"]) or ""
            named = [
                scope[n]
                for n in v.get("refs", [])
                if n in scope and pr_at.get(scope[n], "9") > at
            ]
            if named:
                firsts.setdefault((chef, named[0]), []).append((v["key"], len(named)))
        for (chef, story), cooks in sorted(firsts.items()):
            if len(cooks) == 1:
                self.ev(
                    launches.get(cooks[0][0]),
                    "github",
                    cooks[0][0],
                    "story_assign",
                    story=story,
                    parent=chef,
                    named=cooks[0][1],
                )

    def scope(
        self,
        gh: GitHub,
        t_in: str | None,
        chef: str | None,
        story: tuple[str, int],
        epic: tuple[str, int] | None,
        batch: int | None,
    ) -> None:
        if t_in is None:
            raise ValueError("Story scope has no registration or launch time")
        iss = gh.issue(*story)
        closed = norm(iss["closedAt"])
        s, e = f"{story[0]}#{story[1]}", (f"{epic[0]}#{epic[1]}" if epic else None)
        self.ev(
            t_in,
            "github",
            chef or "hc",
            "story_scope",
            epic=e,
            story=s,
            batch=batch,
            state_at_scope="closed" if closed and closed <= t_in else "open",
        )


class GitHub:
    PR_FIELDS = (
        "number createdAt mergedAt closedAt body "
        "closingIssuesReferences(first:100){nodes{number repository{nameWithOwner}}}"
    )
    ISSUE_FIELDS = (
        "title closedAt labels(first:10){nodes{name}} parent{number repository{nameWithOwner}} "
        "subIssues(first:100){totalCount nodes{number createdAt repository{nameWithOwner}}}"
    )

    def __init__(self, read: Callable[[list[str]], dict]) -> None:
        self.read = read
        self.prs: dict = {}
        self.issues: dict = {}
        self.repositories: dict[str, dict] = {}

    def repository(self, name: str) -> str:
        if name not in self.repositories:
            info = self.read(
                ["repo", "view", name, "--json", "nameWithOwner,visibility"]
            )
            self.repositories[name] = info
            self.repositories[info["nameWithOwner"]] = info
        return self.repositories[name]["nameWithOwner"]

    def repo_query(self, repo: str, body: str, missing_ok: bool = False) -> dict:
        owner, name = self.repository(repo).split("/", 1)
        result = self.gql(
            f"query{{repository(owner:{json.dumps(owner)},name:{json.dumps(name)}){{{body}}}}}",
            missing_ok,
        )
        if not result.get("repository"):
            raise ValueError(f"GitHub returned no repository for {repo}")
        return result["repository"]

    def gql(self, query: str, missing_ok: bool = False) -> dict:
        result = self.read(["api", "graphql", "-f", f"query={query}"])
        if result.get("errors") and not (
            missing_ok
            and all(error.get("type") == "NOT_FOUND" for error in result["errors"])
        ):
            raise ValueError(
                "GitHub GraphQL: " + "; ".join(e["message"] for e in result["errors"])
            )
        return result["data"]

    def load_prs(self, keys: Iterable[tuple[str, int]]) -> None:
        by_repo = defaultdict(list)
        for repo, n in keys:
            by_repo[repo].append(n)
        for repo, ns in sorted(by_repo.items()):
            body = " ".join(
                f"p{n}: pullRequest(number:{n}){{{self.PR_FIELDS}}}" for n in sorted(ns)
            )
            d = self.repo_query(repo, body)
            for v in d.values():
                self.prs[(repo, v["number"])] = v

    def pr(self, repo: str, n: int) -> dict:
        return self.prs[(repo, n)]

    def item(self, repo: str, n: int) -> dict | None:
        """An issue or a PR by number, for a 🙋 line's reference."""
        return self.repo_query(
            repo,
            f"issueOrPullRequest(number:{n}){{__typename ... on PullRequest{{mergedAt closedAt}} ... on Issue{{closedAt}}}}",
            missing_ok=True,
        )["issueOrPullRequest"]

    def issue(self, repo: str, n: int) -> dict:
        if (repo, n) not in self.issues:
            d = self.repo_query(repo, f"issue(number:{n}){{{self.ISSUE_FIELDS}}}")
            if not d.get("issue"):
                raise ValueError(f"GitHub returned no issue {repo}#{n}")
            self.issues[(repo, n)] = d["issue"]
        return self.issues[(repo, n)]

    def is_epic(self, repo: str, n: int) -> bool:
        i = self.issue(repo, n)
        labels = {x["name"] for x in i["labels"]["nodes"]}
        return "4-epic" in labels or (
            i["subIssues"]["totalCount"] > 0 and i["title"].lower().startswith("epic")
        )

    def subissues(self, repo: str, n: int) -> list[dict]:
        return sorted(
            self.issue(repo, n)["subIssues"]["nodes"], key=lambda s: s["number"]
        )

    def refs(self, repo: str, p: dict) -> list[tuple[str, int]]:
        out = [
            (c["repository"]["nameWithOwner"], c["number"])
            for c in p["closingIssuesReferences"]["nodes"]
        ]
        for m in re.finditer(
            r"\b(?:closes|fixes|resolves|refs?|part of)\s+(?:([\w.-]+/[\w.-]+))?#(\d+)",
            p["body"] or "",
            re.IGNORECASE,
        ):
            out.append((m.group(1) or repo, int(m.group(2))))
        seen, uniq = set(), []
        for r in out:
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        return uniq

    def stories_of(self, repo: str, p: dict) -> list[tuple[str, int]]:
        """Issues a PR closes or names; an Epic is not a Story."""
        return [r for r in self.refs(repo, p) if not self.is_epic(*r)]

    def epic_ref(self, repo: str, p: dict) -> tuple[str, int] | None:
        for r in self.refs(repo, p):
            if self.is_epic(*r):
                return r
        return None

    def epic_of(self, repo: str, n: int) -> tuple[str, int] | None:
        par = self.issue(repo, n)["parent"]
        return (par["repository"]["nameWithOwner"], par["number"]) if par else None


def discover(con: sqlite3.Connection, since: str, only: list[str]) -> list[str]:
    rows = con.execute(
        "select thread_id from orchestration_v2_projection_threads "
        "where title like 'Head Chef%' and created_at >= ? order by created_at, thread_id",
        (since,),
    ).fetchall()
    ids = [row[0] for row in rows]
    missing = set(only) - {tid[-4:] for tid in ids}
    if missing:
        raise ValueError(
            "Head Chef not found since --since: " + ", ".join(sorted(missing))
        )
    selected = [tid for tid in ids if not only or tid[-4:] in only]
    if len({tid[-4:] for tid in selected}) != len(selected):
        raise ValueError("Head Chef IDs collide; narrow the time window with --since")
    return selected


def extract(
    con: sqlite3.Connection, gh: GitHub, thread_ids: Iterable[str]
) -> list[dict]:
    brigades = []
    for tid in thread_ids:
        brigade = Brigade(con, tid)
        brigade.walk()
        brigade.t3()
        brigades.append(brigade)
    known = {repo for brigade in brigades for repo, _ in brigade.prs}

    def resolve(name: str) -> str:
        matches = sorted(repo for repo in known if repo.rsplit("/", 1)[-1] == name)
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous repository {name}; use distinct T3 project names"
            )
        return gh.repository(matches[0] if matches else name)

    for brigade in brigades:
        for info in brigade.threads.values():
            if info.get("repo"):
                info["repo"] = resolve(info["repo"])
        for info in brigade.batch_refs.values():
            if info.get("repo"):
                info["repo"] = resolve(info["repo"])
            info["refs"] = [(resolve(repo), n) for repo, n in info["refs"] if repo]
        for event in brigade.events:
            if event["kind"] == "launch" and (event["detail"] or {}).get("repo"):
                event["detail"]["repo"] = resolve(event["detail"]["repo"])
    gh.load_prs({key for brigade in brigades for key in brigade.prs})
    events = []
    for brigade in brigades:
        brigade.github(gh)
        events.extend(brigade.events)
    order = {
        kind: i
        for i, kind in enumerate(
            [
                "batch_register",
                "story_scope",
                "launch",
                "run_start",
                "pascal_msg",
                "send",
                "rename",
                "ask_pascal",
            ]
        )
    }
    events.sort(
        key=lambda event: (
            event["time"],
            event["brigade"],
            order.get(event["kind"], 50),
            event["kind"],
            event["thread"],
            json.dumps(event["detail"], ensure_ascii=False, sort_keys=True),
        )
    )
    return events

"""Fold facts into model.py statuses and the deltas the board consumes."""

from __future__ import annotations

import importlib.util
from collections import defaultdict
from datetime import datetime
from pathlib import Path

MODEL = Path(__file__).resolve().parents[2] / "references/model.py"
spec = importlib.util.spec_from_file_location("brigade_model", MODEL)
assert spec is not None and spec.loader is not None
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


class Brigade:
    def __init__(self, id4: str) -> None:
        self.id4 = id4
        self.threads: dict[str, dict] = {
            "hc": {"role": "head_chef", "label": f"Head Chef {id4}", "parent": None}
        }
        self.cook = {}  # key -> phase (model.COOK keys)
        self.cook_prev = {}  # phase to restore after an answered question
        self.chef = {}  # key -> facts
        self.chef_cooks = defaultdict(list)  # chef -> [cook keys]
        self.batches = {}  # b -> {"registered": t, "chef": key|None}
        self.hc = {"pm_item": False, "own": False, "stop": False}
        self.asks = []  # open items: "merge" | "item"
        self.asked_review = set()  # chefs whose 🍽️ went to Pascal
        self.escalated = set()  # chefs whose ⏸️ went to Pascal
        self.first_launch: float | None = None
        self.own_until = 0.0  # end of the HC run that handles Pascal's last message
        self.closed = False  # HC settled itself after every batch went final
        self.prs = {}  # pr -> {"cook", "open", "merged", "closed"}
        self.release_end = {}  # chef -> time its release command ended
        self.active = {}  # key -> open run count
        self.started = False  # the Head Chef exists once Pascal's first message arrives
        self.cook_checks = {}  # cook -> its last Stack ready reported passing checks
        self.restacking = set()  # Cooks asked for a base-only restack
        self.open_items = []  # Head Chef items for Pascal: (label, PR refs, own item)
        self.stories = {}  # story -> Epic, batch, pre-run completion and assigned Cook
        self.planned = defaultdict(
            dict
        )  # chef -> {watch.toml field: Cook slots registered, not launched}
        self.item_since = {}  # PR refs of an open item -> when the Head Chef first asked it
        self.carry, self.carry_until = (
            {},
            0.0,
        )  # items open at Pascal's last reply, kept if re-asked next
        self.hc_acts_all: list[tuple[float, str]] = []

    def cook_kinds(self, chef: str) -> list[str]:
        launched = {c.split("#")[0] for c in self.chef_cooks[chef]}
        planned = (
            set().union(*self.planned[chef].values()) - launched
            if self.planned[chef]
            else set()
        )
        # carpaccio: a registered slot that has not launched is live, model.py's "queued"
        return [self.cook[c] for c in self.chef_cooks[chef] if c in self.cook] + [
            "queued"
        ] * len(planned)

    def chef_facts(self, chef: str, now: float) -> dict:
        f = dict(self.chef[chef]["f"])
        served = [c for c in self.chef_cooks[chef] if self.cook.get(c) == "served"]
        if (
            served
            and len(served) == len(self.chef_cooks[chef])
            and all(self.cook_checks.get(c) for c in served)
        ):
            f["checks"] = (
                True  # every Cook served with passing checks on its frozen heads
            )
        mine = [
            p for p in self.prs.values() if p["chef"] == chef and not p.get("closed")
        ]
        kinds = set(self.cook_kinds(chef))
        f["merged"] = (
            bool(mine)
            and all(p.get("merged") for p in mine)
            and not kinds & {"build", "ask", "queued"}
        )
        rel = self.chef[chef]["release"]
        f["released"] = f["merged"] and (
            not rel or self.release_end.get(chef, float("inf")) <= now
        )
        return f

    def chef_status(self, chef: str, now: float) -> str:
        f = self.chef_facts(chef, now)
        kinds = set(self.cook_kinds(chef))
        s = M.chef_status(f, kinds)
        return s

    def chef_kind(self, chef: str, s: str) -> str:
        if s == "🍽️":
            return "🍽️review" if chef in self.asked_review else "🍽️answer"
        if s == "⏸️":
            return "⏸️escalated" if chef in self.escalated else "⏸️answer"
        if s == "⏹️":
            return "⏹️cut" if self.chef[chef]["cut"] else "⏹️stop"
        return s

    def hc_status(self, now: float) -> tuple[str, set[str]]:
        kinds = []
        for b, info in sorted(self.batches.items()):
            c = info["chef"]
            if c is None:
                kinds.append(
                    "⏹️cut"
                    if info.get("cut")
                    else "⏹️stop"
                    if self.hc["stop"]
                    else "queued"
                )
            else:
                kinds.append(self.chef_kind(c, self.chef_status(c, now)))
        h = dict(self.hc)
        h["own"] = self.own(now, kinds)
        ks = set(kinds)
        s = M.hc_status(h, ks)
        return s, ks

    def own(self, now: float, kinds: list[str]) -> bool:
        if self.closed:
            return False
        if self.first_launch is None:
            return not self.hc[
                "pm_item"
            ]  # Align: the Head Chef's own work until it launches
        if now < self.own_until:
            return True  # handles Pascal's message until its next act
        live = [k for k in kinds if k not in M.CHEF_FINAL and k != "queued"]
        if (
            "queued" in kinds
            and not live
            and not self.hc["pm_item"]
            and not self.hc["stop"]
        ):
            return True  # model.hc_coherent: a queued batch with no live Chef waits on the Head Chef
        all_final = kinds and all(k in M.CHEF_FINAL for k in kinds)
        return bool(all_final)  # Close: retros and report until it settles itself

    def snapshot(self, now: float) -> dict[str, str]:
        out = {}
        for k, info in self.threads.items():
            if info["role"] == "cook" and k in self.cook:
                out[k] = M.COOK[self.cook[k]]
            elif info["role"] == "chef" and k in self.chef:
                out[k] = self.chef_status(k, now)
        if self.started:
            out["hc"] = self.hc_status(now)[0]
        return out


def replay(events: list[dict]) -> tuple[dict[str, Brigade], list[dict]]:
    brigades: dict[str, Brigade] = {}
    deltas = []
    last = {}

    # Pascal's reply belongs to the Head Chef until its next act or turn end.
    runs = defaultdict(list)
    for e in events:
        if e["kind"] == "run_start" or e["kind"] == "run_end":
            runs[(e["brigade"], e["thread"], e["detail"]["run"])].append(ts(e["time"]))
    intervals = defaultdict(list)
    for (b, th, _), v in runs.items():
        intervals[(b, th)].append((v[0], v[1] if len(v) > 1 else float("inf")))
    for v in intervals.values():
        v.sort()

    ACTS = {"send", "launch", "ask_pascal", "batch_register", "organize"}
    acts = defaultdict(list)  # (b, thread) -> sorted (time, act) of its own acts
    for e in events:
        if e["kind"] in ACTS:
            who = (
                e["parent"]
                if e["kind"] in ("launch", "delegate_start")
                else e["thread"]
            )
            act = (
                (e["detail"] or {}).get("msg")
                or (e["detail"] or {}).get("action")
                or e["kind"]
            )
            acts[(e["brigade"], who)].append((ts(e["time"]), act))
    for v in acts.values():
        v.sort()

    def emit(b: Brigade, t: float) -> None:
        snap = b.snapshot(t)
        for k, s in snap.items():
            key = (b.id4, k)
            if last.get(key) != s:
                last[key] = s
                deltas.append({"t": t, "b": b.id4, "k": "status", "th": k, "v": s})

    for e in events:
        t = ts(e["time"])
        bid = e["brigade"]
        if bid not in brigades:
            brigades[bid] = Brigade(bid)
            brigades[bid].hc_acts_all = acts[(bid, "hc")]
        b = brigades[bid]
        apply(b, e, t, deltas, intervals)
        emit(b, t)

    return brigades, deltas


def apply(
    b: Brigade,
    e: dict,
    t: float,
    deltas: list[dict],
    intervals: dict[tuple[str, str], list[tuple[float, float]]],
) -> None:
    kind, th, d = e["kind"], e["thread"], e["detail"] or {}
    role = e["role"]
    if kind == "pascal_msg":
        if (d.get("text") or "").lstrip().startswith("/"):
            return  # a slash command such as /compact answers nothing
        if th == "hc":
            b.started = True
            if b.asks:
                deltas.append({"t": t, "b": b.id4, "k": "ask", "v": [], "since": None})
            # an item Pascal's reply leaves unanswered, asked again in the turn that handles the reply, keeps its age
            b.carry = {
                r: b.item_since[r] for _, r, _ in b.open_items if r in b.item_since
            }
            b.carry_until = next(
                (en for s, en in intervals[(b.id4, "hc")] if s <= t + 5 and en >= t), t
            )
            b.item_since = {}
            b.asks = []
            b.open_items = []
            b.hc["pm_item"] = False
            # Pascal answered what he was asked: a 🍽️ batch or an escalated ⏸️ goes back to the Head Chef
            b.asked_review.clear()
            b.escalated.clear()
            end = next(
                (en for s, en in intervals[(b.id4, "hc")] if s <= t + 5 and en >= t), t
            )
            nxt = next((a for a, _ in b.hc_acts_all if a > t), float("inf"))
            b.own_until = max(b.own_until, min(end, nxt))
            if d.get("intent") == "stop":
                b.hc["stop"] = True
        deltas.append(
            {"t": t, "b": b.id4, "k": "pascal", "th": th, "v": d.get("intent")}
        )
    elif kind == "ask_pascal" and th == "hc":
        if b.closed and all(i == "left" for i in d.get("items", [])):
            return
        b.closed = False  # a new question after Close reopens the run (carpaccio: Work after Close)
        ready = [c for c in b.chef if b.chef_status(c, t) == "🍽️"]
        asking = [c for c in b.chef if b.chef[c]["f"]["question"]]
        own = False
        for item in d.get("items", []):
            if item == "left":
                continue  # "Reste pour toi" lines of a final report: the run asks nothing more
            if item == "merge" and ready:
                b.asked_review.update(ready)
            elif asking and item != "merge":
                b.escalated.update(asking)
            else:
                own = True
        irefs = d.get("irefs") or [[] for _ in d.get("items", [])]
        # open items: (label, refs); an own item keeps the Head Chef at ❓ until answered
        b.open_items = [
            (i, frozenset(r), i != "merge" or not ready)
            for i, r in zip(d.get("items", []), irefs)
            if i != "left"
        ]
        b.hc["pm_item"] = own or b.hc["pm_item"]
        b.asks = list(d.get("items", []))
        carry = b.carry if t <= b.carry_until else {}
        b.carry = {}
        since = []
        for _, r, _ in b.open_items:
            if r:
                b.item_since[r] = carry.get(r) or b.item_since.get(r) or t
                since.append(b.item_since[r])
            else:
                since.append(t)
        deltas.append(
            {
                "t": t,
                "b": b.id4,
                "k": "ask",
                "v": list(b.asks),
                "since": min(since) if since else None,
            }
        )
    elif kind == "launch":
        b.started = True
        b.threads[th] = {
            "role": role,
            "label": d.get("label"),
            "parent": e["parent"],
            "repo": d.get("repo"),
        }
        deltas.append(
            {
                "t": t,
                "b": b.id4,
                "k": "launch",
                "th": th,
                "parent": e["parent"],
                "role": role,
                "label": d.get("label"),
                "repo": d.get("repo"),
            }
        )
        b.closed = False  # a launch after Close reopens the run
        if role == "chef":
            bn = int(th.split("-")[1].split("#")[0])
            b.batches.setdefault(bn, {"registered": t, "chef": None})["chef"] = th
            b.chef[th] = {
                "f": {k: False for k in M.CHEF_FACTS},
                "release": bool(d.get("release")),
                "cut": False,
            }
            if b.first_launch is None:
                b.first_launch = t
            b.hc["pm_item"] = (
                False  # launching the held work resolves the Head Chef's own item
            )
        elif role == "cook":
            b.cook[th] = "build"
            b.chef_cooks[e["parent"]].append(th)
    elif kind == "batch_register":
        x = b.batches.setdefault(d["batch"], {"registered": t, "chef": None})
        if d.get("state") == "proposed-cut":
            x["proposed_cut"] = True
    elif kind == "batch_cut":
        for x in b.batches.values():
            if x.get("proposed_cut") and x["chef"] is None:
                x["cut"] = True
    elif kind == "pascal_github":
        # Pascal answered on GitHub the items that name this PR; the others stay open
        _, n = e["pr"].split("#")
        answered = [x for x in b.open_items if {e["pr"], f"#{n}"} & x[1]]
        for x in answered:
            b.item_since.pop(x[1], None)
        b.open_items = [x for x in b.open_items if x not in answered]
        b.hc["pm_item"] = any(own for _, _, own in b.open_items)
        b.asks = [i for i, _, _ in b.open_items]
        if answered:
            since = [b.item_since.get(r, t) for _, r, _ in b.open_items]
            deltas.append(
                {
                    "t": t,
                    "b": b.id4,
                    "k": "ask",
                    "v": list(b.asks),
                    "since": min(since) if since else None,
                }
            )
        deltas.append({"t": t, "b": b.id4, "k": "pascal", "th": "hc", "v": "github"})
    elif kind == "send":
        to, msg = d.get("to"), d.get("msg")
        src = b.threads.get(th, {}).get("role")
        dst = b.threads.get(to or "", {}).get("role")
        if src == "cook" and th in b.cook:
            ph = b.cook[th]
            if msg == "stack_ready":
                ch = b.threads[th]["parent"]
                f = b.chef[ch]["f"]
                restacked = th in b.restacking
                b.restacking.discard(th)
                if (
                    not restacked
                    and f["merge"]
                    and any(
                        x.get("merged", 0) > b.chef[ch].get("auth", 0)
                        for x in b.prs.values()
                        if x["chef"] == ch
                    )
                ):
                    f["merge"] = f["checks"] = (
                        False  # a new stack after a partial merge needs its own decision; a base-only restack keeps it
                    )
                b.cook[th] = "served"
                b.cook_checks[th] = d.get("checks") in (
                    "pass",
                    "passed",
                    "green",
                    "success",
                    "ok",
                )
            elif msg == "question":
                b.cook_prev[th], b.cook[th] = ph, "ask"
            elif msg == "cook_final":
                b.cook[th] = "cut_stopped" if ph.startswith("cut") else "done"
            elif msg == "cook_stopped":
                b.cook[th] = "cut_stopped" if ph.startswith("cut") else "stopped"
        elif src == "chef" and dst == "cook" and to in b.cook:
            ph = b.cook[to]
            if ph == "ask":
                b.cook[to] = b.cook_prev.pop(to, "build")
            if msg in ("merged_notice", "close_request"):
                b.cook[to] = "close"
            elif msg == "return" and b.cook[to] == "served":
                b.cook[to] = "build"
                f = b.chef[th]["f"]
                f["checks"] = f["merge"] = (
                    False  # new heads need new checks and a new decision
                )
            elif msg == "restack" and b.cook[to] == "served":
                b.restacking.add(
                    to
                )  # a base-only restack keeps the Cook served, its approval and its checks
            elif msg == "stop" and b.cook[to] not in M.COOK_FINAL:
                b.cook[to] = "close"
            elif msg == "cut":
                b.cook[to] = "cut_close"
        elif src == "chef" and dst == "head_chef" and th in b.chef:
            f = b.chef[th]["f"]
            if msg == "question":
                f["question"] = True
            elif msg in ("batch_ready",):
                f["checks"] = True
            elif msg == "batch_merging":
                f["checks"] = f["merge"] = True
                b.chef[th]["auth"] = t
            elif msg in ("batch_delivered", "batch_stopped"):
                f["closed"] = True
        elif src == "head_chef" and dst == "chef" and to in b.chef:
            f = b.chef[to]["f"]
            f["question"] = False
            b.escalated.discard(to)
            if msg == "merge":
                f["checks"] = f["merge"] = True
                b.chef[to]["auth"] = t
                b.asked_review.discard(to)
            elif msg == "escalated":
                f["question"] = True
                b.escalated.add(to)
            elif msg == "stop":
                f["stopped"] = True
            elif msg in ("cut", "drop"):
                f["stopped"] = True
                b.chef[to]["cut"] = True
            elif msg == "rework":
                f["checks"] = f["merge"] = False
    elif kind in ("pr_open", "pr_merge", "pr_close"):
        p = b.prs.setdefault(
            (e["pr"], e["story"]),
            {
                "pr": e["pr"],
                "cook": th,
                "chef": b.threads.get(th, {}).get("parent"),
                "story": e["story"],
                "epic": e["epic"],
            },
        )
        if kind == "pr_open":
            p["open"] = t
            if (
                e["story"] not in b.stories
            ):  # a PR without an issue is its own Story, committed when its Cook launched
                bn = int(p["chef"].split("-")[1].split("#")[0]) if p["chef"] else None
                b.stories[e["story"]] = {
                    "epic": e["epic"],
                    "batch": bn,
                    "chef": p["chef"],
                    "pre": False,
                }
        elif kind == "pr_merge":
            p["merged"] = t
            ch = p["chef"]
            if ch in b.chef and not b.chef[ch]["f"]["merge"]:
                # no approval reached the Chef: Pascal merged it himself, which approves it
                b.chef[ch]["f"]["merge"] = b.chef[ch]["f"]["checks"] = True
                b.chef[ch]["auth"] = t
                deltas.append(
                    {
                        "t": t,
                        "b": b.id4,
                        "k": "pascal",
                        "th": "hc",
                        "v": "merged-himself",
                        "pr": e["pr"],
                    }
                )

        else:
            p["closed"] = t
        deltas.append(
            {
                "t": t,
                "b": b.id4,
                "k": kind,
                "th": th,
                "pr": e["pr"],
                "story": e["story"],
                "epic": e["epic"],
            }
        )
    elif kind == "release_done" and th in b.chef:
        if b.chef_facts(th, t)["merged"]:
            b.release_end.setdefault(th, t)
    elif (
        kind == "organize"
        and d.get("action") == "settle"
        and th == "hc"
        and d.get("target") == "hc"
    ):
        _, kinds = b.hc_status(t)
        if kinds and kinds <= M.CHEF_FINAL:
            b.closed = True  # every batch is final, cut ones included: the Head Chef closed the run
    elif kind in ("run_start", "run_end"):
        n = b.active.get(th, 0) + (1 if kind == "run_start" else -1)
        b.active[th] = max(n, 0)
        deltas.append(
            {"t": t, "b": b.id4, "k": "run", "th": th, "v": 1 if b.active[th] else 0}
        )
    elif kind in ("delegate_start", "delegate_end", "delegate_error"):
        deltas.append(
            {
                "t": t,
                "b": b.id4,
                "k": "deleg",
                "id": th,
                "parent": e["parent"],
                "role": role,
                "sop": d.get("sop"),
                "round": d.get("round"),
                "state": d.get("state"),
                "v": 1
                if kind == "delegate_start"
                else 0
                if kind == "delegate_end" and d.get("state") == "completed"
                else -1,
            }
        )
    elif kind == "story_scope":
        b.stories.setdefault(
            e["story"],
            {
                "epic": e["epic"],
                "batch": d.get("batch"),
                "chef": th,
                "pre": d.get("state_at_scope") == "closed",
            },
        )
    elif kind == "cook_planned" and th in b.chef:
        b.planned[th][d["field"]] = set(d.get("slots") or [])
    elif kind == "story_assign":
        if e["story"] in b.stories:
            b.stories[e["story"]]["cook"] = th


def synthetic(events: list[dict]) -> list[dict]:
    """Facts that a row holds at its end time: a release command finishing,
    an AskUserQuestion answered. Added as events, then everything is re-sorted."""
    out = list(events)
    for e in events:
        d = e["detail"] or {}
        if (
            e["kind"] == "cmd"
            and e["role"] == "chef"
            and d.get("release")
            and d.get("ok")
            and d.get("end")
        ):
            out.append({**e, "time": d["end"], "kind": "release_done", "detail": None})
        if e["kind"] == "ask_pascal" and d.get("answered"):
            out.append(
                {
                    **e,
                    "role": "pascal",
                    "time": d["answered"],
                    "kind": "pascal_msg",
                    "detail": {"intent": "answer"},
                }
            )
    out.sort(
        key=lambda e: e["time"]
    )  # stable: keeps the extractor's order within a timestamp
    return out

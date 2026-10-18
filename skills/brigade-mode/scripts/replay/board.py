"""The fixed Epic/Cook board and its frames, without network or filesystem access."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import datetime, timezone

import statuses as R

# carpaccio Process: manic-1 and manic-2 at step 2, manic-3 and manic-5 at step 4 (config.toml)
BARRAGES = {"manic-1": 2, "manic-2": 2, "manic-3": 4, "manic-5": 4}
# Pascal's four steps; carpaccio's step k (1 to 6) shows as STEP[k]: Docs in Review 1/2, Merge and Close in Ship
STEPS = ["Implement", "Review 1/2", "Review 2/2", "Ship"]
STEP = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 4}
BARRAGE_STEP = {sop: STEP[k] for sop, k in BARRAGES.items()}
COOK = {"🍳": "active", "⏸️": "wait", "🍽️": "done", "🧹": "done", "⏹️": "stopped"}
CHEF = {
    "⏳": "active",
    "🔀": "active",
    "🧹": "active",
    "🍽️": "wait",
    "⏸️": "wait",
    "⛳": "done",
    "⏹️": "stopped",
}


def slot(key: str) -> str:
    return key.split("#")[0]  # a replacement takes its slot's cell


def batch_of(key: str) -> int:
    return int(key.split("-")[1].split("#")[0].split(".")[0])


class Board:
    """Folds one brigade's replay deltas into node states; emits a frame on each change."""

    def __init__(self, b: R.Brigade) -> None:
        self.b, self.frames, self.cur = b, [], {}
        self.cook_emoji, self.running, self.live = {}, defaultdict(dict), set()
        self.step, self.prs, self.merged, self.ask = (
            {},
            defaultdict(set),
            defaultdict(set),
            None,
        )
        self.current = {}  # slot -> the key that holds it now
        self.settled = False

    def set(
        self,
        t: float,
        node: str,
        state: str,
        note: str | None = None,
        step: int | None = None,
        since: float | None = None,
    ) -> None:
        """Frames stay in time order; a wait that began earlier carries its start in `since`."""
        v = (state, step, note, since)
        if self.cur.get(node) != v:
            self.cur[node] = v
            self.frames.append(
                [round(t, 1), node, state, step, note]
                + ([round(since, 1)] if since else [])
            )

    def paint_cook(self, t: float, s: str) -> None:
        key = self.current.get(s)
        e = self.cook_emoji.get(key)
        if e is None:
            return
        state = COOK.get(e, "active")
        run = self.running[key]
        note = None
        if self.prs[s] and self.prs[s] <= self.merged[s]:
            state = "done"  # its PRs are in main: shipped; Pascal has no Close step to watch
        if state == "active" and run:
            state, note = (
                "wait",
                " + ".join(sorted(run.values())),
            )  # the Cook stands by, its checks work
        elif state == "active" and key not in self.live:
            state, note = "wait", "idle"  # green means a turn or a delegate runs now
        elif state == "wait":
            note = "question to its Chef"
        elif state == "done":
            note = (
                "shipped"
                if self.prs[s] and self.prs[s] <= self.merged[s]
                else "ready to ship"
                if self.prs[s]
                else "nothing to ship"
            )
        step = self.step.get(s, 0)
        self.set(t, s, state, note, STEP.get(step, step))

    def apply(self, d: dict) -> None:
        t, k = d["t"], d["k"]
        if k == "launch" and d["role"] == "cook":
            s = slot(d["th"])
            self.current[s] = d["th"]
            self.step[s] = 1
        elif k == "status":
            th = d["th"]
            if th == "hc":
                if self.settled:
                    return  # the run closed: a question left in the final report is not a wait
                if d["v"] == "❓":
                    a = self.ask or {}
                    open_ = [x for x in a.get("v") or [] if x != "left"]
                    note = (
                        "ship review"
                        if "merge" in open_
                        else f"{len(open_)} questions"
                        if len(open_) > 1
                        else "a question"
                    )
                    self.set(t, "hc", "you", note, since=min(t, a.get("since") or t))
                else:
                    self.set(
                        t, "hc", {"⛳": "done", "⏹️": "stopped"}.get(d["v"], "active")
                    )
                if d["v"] in ("⛳", "⏹️"):
                    self.close_run(t)
            elif th.startswith("chef-"):
                self.set(
                    t,
                    f"batch-{batch_of(th)}",
                    CHEF.get(d["v"], "active"),
                    {"🔀": "shipping", "🍽️": "ready to ship", "⏸️": "question"}.get(
                        d["v"]
                    ),
                )
            elif th.startswith("cook-"):
                s = slot(th)
                if self.current.get(s) not in (None, th):
                    return  # a replaced Cook's late status: the slot follows its replacement
                self.current[s] = th
                self.cook_emoji[th] = d["v"]
                if d["v"] == "🍽️" and self.step.get(s, 0) < 5:
                    self.step[s] = 5
                    self.skip_barrages(t, s)
                self.paint_cook(t, s)
        elif k == "deleg" and d.get("parent", "").startswith("cook-"):
            key, s, sop = d["parent"], slot(d["parent"]), d.get("sop")
            if d["v"] == 1:
                self.running[key][d["id"]] = sop
                if sop in BARRAGES:
                    self.step[s] = BARRAGES[sop]
                    self.set(t, f"{s}/{sop}", "active", f"round {d.get('round')}")
            else:
                self.running[key].pop(d["id"], None)
                if sop in BARRAGES:
                    self.set(
                        t,
                        f"{s}/{sop}",
                        "stopped" if d["v"] == -1 else "done",
                        f"round {d.get('round')}"
                        + (f", {d.get('state') or 'error'}" if d["v"] == -1 else ""),
                    )
            self.paint_cook(t, s)
        elif k in ("pr_open", "pr_merge", "pr_close") and (
            d.get("th") or ""
        ).startswith("cook-"):
            s = slot(d["th"])
            if k == "pr_open":
                self.prs[s].add(d["pr"])
            elif k == "pr_merge":
                self.merged[s].add(d["pr"])
                if self.prs[s] and self.prs[s] <= self.merged[s]:
                    self.step[s] = max(self.step.get(s, 0), 6)
            else:
                self.prs[s].discard(d["pr"])
            self.paint_cook(t, s)
        elif k == "ask":
            self.ask = d
        elif k == "cookrun":
            (self.live.add if d["v"] else self.live.discard)(d["th"])
            self.paint_cook(t, slot(d["th"]))
        elif k == "settled":
            self.settled = True
            self.set(t, "hc", "done", "run over")
            self.close_run(t)
        elif k == "progress":
            s = slot(d["th"])
            self.step[s] = max(1, min(d["step"] + 1, 6))  # 📍 k/6 ends step k
            self.paint_cook(t, s)

    def skip_barrages(self, t: float, s: str) -> None:
        for (
            sop
        ) in BARRAGES:  # served without this barrage: fast track or an older route
            if self.cur.get(f"{s}/{sop}", ("todo",))[0] == "todo":
                self.set(t, f"{s}/{sop}", "stopped", "skipped")

    def close_run(self, t: float) -> None:
        """The run ended: what never started is not done in this run."""
        for n, info in self.b.batches.items():
            if info.get("chef") is None:
                self.set(
                    t,
                    f"batch-{n}",
                    "stopped",
                    "cut" if info.get("cut") else "not started",
                )
        for node, (state, step, note, _) in list(self.cur.items()):
            if state == "todo" and not node.startswith(("batch-", "story:")):
                self.set(
                    t,
                    node,
                    "stopped",
                    "not run" if "/" in node else "not started",
                    step,
                )


def shape(
    b: R.Brigade,
    planned: dict[str, set[str]],
    ref: Callable[[str], str],
    numbers: dict[str, int | None],
    public: set[str],
) -> tuple[list[dict], dict[str, dict]]:
    """Epics -> Cooks -> Stories, as the run ended. `ref` writes an issue ref for the page."""
    cooks = {}
    for key, info in b.threads.items():
        if info.get("role") == "cook":
            s = slot(key)
            cooks.setdefault(
                s,
                {
                    "label": info["label"].split("#")[0].strip(),
                    "batch": batch_of(s),
                    "stories": set(),
                    "prs": set(),
                },
            )
    for slots in planned.values():
        for (
            s
        ) in slots:  # planned in watch.toml, never launched: a gray cell all run long
            cooks.setdefault(
                s,
                {
                    "label": "Cook " + s.split("-")[1],
                    "batch": batch_of(s),
                    "stories": set(),
                    "prs": set(),
                },
            )
    for p in b.prs.values():
        if (
            p.get("cook")
            and slot(p["cook"]) in cooks
            and not p.get("closed")
            and not b.stories.get(p["story"], {}).get("pre")
        ):
            cooks[slot(p["cook"])]["stories"].add(p["story"])
            cooks[slot(p["cook"])]["prs"].add(p["pr"])
    for st, info in b.stories.items():
        if info.get("cook") and slot(info["cook"]) in cooks and not info.get("pre"):
            cooks[slot(info["cook"])]["stories"].add(st)
    batches = []
    for n in sorted(set(b.batches) | {c["batch"] for c in cooks.values()}):
        stories = sorted(
            st
            for st, i in b.stories.items()
            if i.get("batch") == n and not i.get("pre")
        )
        epics = Counter(
            b.stories[st].get("epic") for st in stories if b.stories[st].get("epic")
        )
        mine = sorted(
            (s for s, c in cooks.items() if c["batch"] == n),
            key=lambda s: tuple(int(x) for x in s.split("-")[1].split(".")),
        )
        top = [e for e, _ in epics.most_common()]
        num = numbers.get(top[0]) if top else None
        epic = {"n": num, "ref": ref(top[0])} if top else None
        if epic and top[0].split("#")[0] in public:
            epic["url"] = (
                f"https://github.com/{top[0].split('#')[0]}/issues/{top[0].split('#')[1]}"
            )
        batches.append(
            {
                "n": n,
                "id": f"batch-{n}",
                "label": f"Epic {num}" if num else f"Batch {n}",
                "epic": epic,
                "cooks": mine,
            }
        )
    out = {
        s: {
            "label": c["label"],
            "batch": c["batch"],
            "stories": sorted(ref(x) for x in c["stories"]),
            "prs": len(c["prs"]),
        }
        for s, c in cooks.items()
    }
    return batches, out


def progress_events(events: list[dict], bid: str) -> list[dict]:
    out = []
    for e in events:
        if (
            e["brigade"] == bid
            and e["kind"] == "send"
            and (e["detail"] or {}).get("msg") == "progress"
            and e["thread"].startswith("cook-")
        ):
            m = re.search(r"\b([1-6])/6\b", e["detail"].get("first") or "")
            if m:
                out.append(
                    {
                        "t": R.ts(e["time"]),
                        "k": "progress",
                        "th": e["thread"],
                        "step": int(m.group(1)),
                    }
                )
    return out


def turns(deltas: list[dict], grace: float = 120) -> list[dict]:
    """Each Cook's T3 turns, gaps under `grace` seconds joined, as cookrun deltas."""
    spans = defaultdict(list)
    for d in deltas:
        if d["k"] == "run" and d["th"].startswith("cook-"):
            if d["v"]:
                spans[d["th"]].append([d["t"], None])
            elif spans[d["th"]] and spans[d["th"]][-1][1] is None:
                spans[d["th"]][-1][1] = d["t"]
    out = []
    for th, xs in spans.items():
        joined = []
        for a, z in xs:
            if joined and joined[-1][1] is not None and a - joined[-1][1] <= grace:
                joined[-1][1] = z
            else:
                joined.append([a, z])
        for a, z in joined:
            out.append({"t": a, "k": "cookrun", "th": th, "v": 1})
            if z is not None:
                out.append({"t": z, "k": "cookrun", "th": th, "v": 0})
    return out


def settle_time(events: list[dict], b: R.Brigade, bid: str) -> list[dict]:
    """When the Head Chef closed the run: its last self-settle, if replay kept the run closed."""
    if not b.closed:
        return []
    ts = [
        R.ts(e["time"])
        for e in events
        if e["brigade"] == bid
        and e["kind"] == "organize"
        and (e["detail"] or {}).get("action") == "settle"
        and e["thread"] == "hc"
        and (e["detail"] or {}).get("target") == "hc"
    ]
    return [{"t": max(ts), "k": "settled"}] if ts else []


def build(
    events: list[dict],
    public: set[str],
    numbers: dict[str, int | None],
    names: dict[str, str],
) -> dict:
    events = R.synthetic(events)
    brigades, deltas = R.replay(events)
    planned = defaultdict(lambda: defaultdict(set))
    for e in events:
        if e["kind"] == "cook_planned":
            planned[e["brigade"]][e["thread"]] |= set(
                (e["detail"] or {}).get("slots") or []
            )
    by_b = defaultdict(list)
    for d in deltas:
        by_b[d["b"]].append(d)
    out = []
    for bid, b in brigades.items():
        repos = sorted({i["repo"] for i in b.threads.values() if i.get("repo")})
        # one repository: #188, its name sits in the header; several: private-A#54
        ref = (
            (lambda x: "#" + x.split("#")[1])
            if len(repos) == 1
            else lambda x: names[x.split("#")[0]] + "#" + x.split("#")[1]
        )
        ds = sorted(
            by_b[bid]
            + progress_events(events, bid)
            + turns(by_b[bid])
            + settle_time(events, b, bid),
            key=lambda d: d["t"],
        )  # stable within a time
        board = Board(b)
        batches, cooks = shape(b, planned[bid], ref, numbers, public)
        if not batches:
            continue  # a Head Chef that launched no Chef has nothing to draw
        for s in cooks:
            board.set(ds[0]["t"], s, "todo", step=0)
            for sop in BARRAGES:
                board.set(ds[0]["t"], f"{s}/{sop}", "todo")
        for bt in batches:
            board.set(ds[0]["t"], bt["id"], "todo")
        for d in ds:
            board.apply(d)
        starts = [d["t"] for d in ds if d["k"] in ("pascal", "launch")]
        hc = [f for f in board.frames if f[1] == "hc"]
        final = hc[-1][2] if hc and hc[-1][2] in ("done", "stopped") else None
        end = hc[-1][0] if final else max(f[0] for f in board.frames)
        busy, cs, last = [], {}, None  # Cooks on the job (active or wait) over time
        for f in board.frames:
            if f[1] in cooks:
                cs[f[1]] = f[2]
                n = (
                    sum(v == "active" for v in cs.values()),
                    sum(v == "wait" for v in cs.values()),
                )
                if n != last:
                    busy.append([f[0], *n])
                    last = n
        out.append(
            {
                "id": bid,
                "repos": [names[r] for r in repos],
                "start": min(starts or [ds[0]["t"]]),
                "end": end,
                "final": final,
                "batches": batches,
                "cooks": cooks,
                "barrages": list(BARRAGES),
                "barrageStep": BARRAGE_STEP,
                "steps": STEPS,
                "busy": busy,
                "frames": board.frames,
            }
        )
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "brigades": out,
    }

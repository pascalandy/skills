"""Replay facts in the KEYS shape, read from a T3 snapshot and GitHub facts.

The extractor reads only what t3.reduce() keeps, so the live service and a
recording replay through the same code. Threads are keyed by full threadId;
each launch names the slot it fills, such as chef-2 or cook-2.1, and a
replacement fills the slot of the thread it replaces.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable

import t3
from github import Facts

KEYS = (
    "time",
    "brigade",
    "role",
    "thread",
    "parent",
    "kind",
    "epic",
    "story",
    "pr",
    "detail",
)
ENDED = ("completed", "failed", "cancelled", "interrupted", "errored")


class Brigade:
    def __init__(
        self, snap: t3.Snapshot, gh: Facts, head: str, disk: dict | None = None
    ) -> None:
        self.snap, self.gh, self.head = snap, gh, head
        self.id4 = head[-4:].lower()
        self.disk = disk or {}  # work folder -> {time, plan}: the live watch.toml files
        self.threads: dict[
            str, dict
        ] = {}  # threadId -> role, slot, label, parent, repo
        self.events: list[dict] = []
        self.prs: dict[tuple[str, int], dict] = {}  # (repo, n) -> {by, at}
        self.batch_refs: dict[int, dict] = {}  # batch -> {repo, refs}
        self.plans: dict[str, dict[str, dict]] = {}  # writer threadId -> slot -> facts
        self.emitted: dict[tuple[str, str], object] = {}

    def ev(
        self,
        time: str | None,
        role: str,
        thread: str,
        kind: str,
        parent: str | None = None,
        epic: str | None = None,
        story: str | None = None,
        pr: str | None = None,
        **detail: object,
    ) -> None:
        self.events.append(
            {
                "time": t3.norm(time),
                "brigade": self.id4,
                "role": role,
                "thread": thread,
                "parent": parent,
                "kind": kind,
                "epic": epic,
                "story": story,
                "pr": pr,
                "detail": {k: v for k, v in sorted(detail.items()) if v is not None}
                or None,
            }
        )

    def walk(self) -> None:
        self.threads[self.head] = {
            "role": "head_chef",
            "slot": "hc",
            "parent": None,
            "label": f"Head Chef {self.id4}",
        }
        queue = [self.head]
        while queue:
            parent = queue.pop(0)
            for item in self.snap.thread_items(parent):
                child = item.get("child")
                if item.get("tool") != "launch" or not child or child in self.threads:
                    continue
                title = item.get("title") or {}
                b, c = title.get("b"), title.get("c")
                if title.get("role") == "cook" and b is not None and c is not None:
                    role, slot, label = "cook", f"cook-{b}.{c}", f"Cook {b}.{c}"
                elif title.get("role") == "chef" and b is not None:
                    role, slot, label = "chef", f"chef-{b}", f"Chef {b}"
                else:
                    continue
                repo = self.snap.projects.get(item.get("project") or "")
                self.threads[child] = {
                    "role": role,
                    "slot": slot,
                    "b": b,
                    "parent": parent,
                    "label": label,
                    "repo": repo,
                    "release": item.get("release") if role == "chef" else None,
                    "refs": item.get("refs") or [],
                }
                batch = item.get("batch")
                if role == "chef" and batch:
                    home = batch.get("repo") or repo
                    self.batch_refs.setdefault(b, {"repo": home, "refs": []})
                    self.batch_refs[b]["refs"] = sorted(
                        {(r or home, n) for r, n in batch["refs"] if r or home}
                    )
                queue.append(child)

    def t3(self) -> None:
        delegates = []
        for tid, info in list(self.threads.items()):
            role, parent = info["role"], info["parent"]
            for item in self.snap.thread_items(tid):
                # a fact shows once its record arrived, never at an earlier stamp
                t0, tool = t3.later(item["start"], item.get("seen")), item.get("tool")
                end = (
                    t3.later(item["end"], item.get("endSeen")) if item["end"] else None
                )
                if item["type"] == "user_message":
                    self.ev(t0, "pascal", tid, "pascal_msg", intent=item["intent"])
                elif item["type"] == "assistant_message" and role == "head_chef":
                    self.ev(
                        t0,
                        role,
                        tid,
                        "ask_pascal",
                        items=item["items"],
                        irefs=item["refs"] if any(item["refs"]) else None,
                    )
                if item.get("release") and role == "chef":
                    self.ev(
                        t0,
                        role,
                        tid,
                        "cmd",
                        parent=parent,
                        release=True,
                        end=end,
                        ok=item["status"] == "completed",
                    )
                if item.get("watch") and role in ("head_chef", "chef"):
                    self.watch(tid, t0, item["watch"])
                if tool == "launch":
                    child = self.threads.get(item.get("child") or "")
                    if child is not None and child["parent"] == tid:
                        # the child's threadId exists once the call returns
                        self.ev(
                            end or t0,
                            child["role"],
                            item["child"],
                            "launch",
                            parent=tid,
                            label=child["label"],
                            slot=child["slot"],
                            repo=child.get("repo"),
                            release=child.get("release"),
                        )
                elif tool == "send":
                    # a message moves no one until T3 delivered it: a pending
                    # or failed send shows nothing
                    if item["status"] != "completed" or end is None:
                        continue
                    to = item.get("to")
                    trole = self.threads[to]["role"] if to in self.threads else "other"
                    msg = t3.classify(item, role, trole)
                    self.ev(
                        end,
                        role,
                        tid,
                        "send",
                        parent=parent,
                        to=to if to in self.threads else "other",
                        msg=msg,
                        # the Cook reports its checks on the frozen heads
                        checks=item.get("checks") if msg == "stack_ready" else None,
                        step=item.get("step") if msg == "progress" else None,
                        lead=item.get("lead"),
                    )
                elif tool == "delegate":
                    delegates.append((tid, role, item))
                elif tool == "ask":
                    self.ev(
                        t0,
                        role,
                        tid,
                        "ask_pascal",
                        items=["question"],
                        answered=end,
                    )
                elif tool == "organize":
                    target = item.get("target") or tid
                    self.ev(
                        t0,
                        role,
                        tid,
                        "organize",
                        action=item.get("action"),
                        target=target if target in self.threads else "delegate",
                    )
                elif tool == "link":
                    k = (item["pr"][0], int(item["pr"][1]))
                    cur = self.prs.get(k)
                    # the Cook that links a PR owns it; a Chef or Head Chef may link it too
                    if cur is None or (
                        role == "cook" and self.threads[cur["by"]]["role"] != "cook"
                    ):
                        self.prs[k] = {"by": tid, "at": t0}
                    # the run knows it from the first link, whoever owns it
                    self.prs[k]["at"] = min(t for t in (t0, (cur or {}).get("at")) if t)
            for _, run in self.snap.thread_runs(tid):
                n = str(run["ordinal"])
                self.ev(
                    t3.later(run["requested"], run.get("seen")),
                    role,
                    tid,
                    "run_start",
                    run=n,
                )
                if run["completed"]:
                    self.ev(
                        t3.later(run["completed"], run.get("endSeen")),
                        role,
                        tid,
                        "run_end",
                        run=n,
                        state=run["status"],
                    )
        for folder, info in sorted(self.disk.items()):
            writer = self.head if folder == "head-chef" else self.chef(folder)
            if writer:
                self.watch(writer, info["time"], {"full": info["plan"], "write": True})
        self.delegates(delegates)

    def chef(self, slot: str) -> str | None:
        """The current Chef of a slot: the last one launched for it."""
        found = [
            t
            for t, i in self.threads.items()
            if i["role"] == "chef" and i["slot"] == slot
        ]
        return found[-1] if found else None

    def watch(self, writer: str, time: str | None, w: dict) -> None:
        """Fold one watch.toml write into the writer's plan and report what changed.

        A full write replaces the plan; a [[slots]] block adds its slot. A write
        that names a slot outside the plan, or a replacement, without either
        is unread: the plan it changed is unknown.
        """
        role = self.threads[writer]["role"]
        plan = self.plans.setdefault(writer, {})
        if w.get("full") is not None:
            plan.clear()
            plan.update(w["full"])
        for name, slot in (w.get("blocks") or {}).items():
            plan.setdefault(name, slot)
        prefix = "chef-" if role == "head_chef" else "cook-"
        mentions = set(w.get("mentions") or [])
        unknown = sorted(m for m in mentions if m.startswith(prefix) and m not in plan)
        if (
            w.get("write")
            and w.get("full") is None
            and (unknown or "replacedBy" in mentions)
        ):
            self.ev(time, role, writer, "watch_unread", slots=unknown or None)
        if role == "head_chef":
            for name, slot in sorted(plan.items()):
                if not name.startswith("chef-"):
                    continue
                cut = slot.get("phase") == "⏹️" and not slot.get("thread")
                detail = {
                    "batch": int(name.split("-")[1]),
                    "refs": slot.get("refs"),
                    "cut": cut or None,
                    "repo": slot.get("repo"),
                }
                if self.emitted.get((writer, name)) != detail:
                    self.emitted[(writer, name)] = detail
                    self.ev(time, role, writer, "batch_register", **detail)
        else:
            cooks = sorted(n for n in plan if n.startswith("cook-"))
            if self.emitted.get((writer, "cooks")) != cooks:
                self.emitted[(writer, "cooks")] = cooks
                self.ev(time, role, writer, "cook_planned", slots=cooks)

    def delegates(self, delegates: list[tuple[str, str, dict]]) -> None:
        rounds = defaultdict(int)
        for me, role, item in delegates:
            if role != "cook":
                continue
            sop, t0 = item["sop"], t3.later(item["start"], item.get("seen"))
            done = t3.later(item["end"], item.get("endSeen")) if item["end"] else None
            kind = (
                "watchdog"
                if sop == "watchdog"
                else "barrage"
                if sop.startswith("manic-") or sop == "fidelity"
                else "side"
            )
            if not item.get("task"):
                if item["status"] in ENDED:  # a call still running has no task yet
                    self.ev(
                        done or t0,
                        kind,
                        f"{kind}:{me}:{sop}",
                        "delegate_error",
                        parent=me,
                        sop=sop,
                    )
                continue
            rounds[(me, sop)] += 1
            r = rounds[(me, sop)]
            dk = f"{kind}:{me}:{sop}" + (
                f":r{r}" if kind != "watchdog" else (f":arm{r}" if r > 1 else "")
            )
            sub = self.snap.subagents.get(item["task"])
            sa, ca, st = (
                (
                    t3.later(sub["started"], sub.get("seen")),
                    t3.later(sub["completed"], sub.get("endSeen"))
                    if sub["completed"]
                    else None,
                    sub["status"],
                )
                if sub
                else (t0, None, "unknown")
            )
            # known once the delegate_task call returned its task
            known = max(t for t in (sa, done, t0) if t)
            self.ev(known, kind, dk, "delegate_start", parent=me, sop=sop, round=r)
            if ca:
                self.ev(
                    max(ca, known),
                    kind,
                    dk,
                    "delegate_end",
                    parent=me,
                    sop=sop,
                    round=r,
                    state=st,
                )

    def main_repo(self) -> str | None:
        repos = [repo for info in self.threads.values() if (repo := info.get("repo"))]
        return max(sorted(set(repos)), key=repos.count) if repos else None

    def github(self) -> None:
        gh = self.gh
        for (repo, n), meta in sorted(self.prs.items()):
            p = gh.pr(repo, n)
            if p is None:
                continue  # not opened yet
            cook = meta["by"]
            pr = f"{repo}#{n}"
            found = gh.stories_of(p)
            # one row per Story the PR closes or names; a PR without an issue is its own Story
            targets = [(f"{r}#{x}", gh.epic_of(r, x)) for r, x in found] or [
                (pr, gh.epic_ref(p))
            ]
            # the run knows a PR once a thread links it: an older PR's facts start there
            linked = meta["at"]
            for s, epic in targets:
                e = f"{epic[0]}#{epic[1]}" if epic else None
                loose = (not found) or None
                self.ev(
                    max(p["created"], linked),
                    "github",
                    cook,
                    "pr_open",
                    epic=e,
                    story=s,
                    pr=pr,
                    loose=loose,
                )
                if p["merged"]:
                    at = max(p["merged"], linked)
                    self.ev(at, "github", cook, "pr_merge", epic=e, story=s, pr=pr)
                elif p["closed"]:
                    at = max(p["closed"], linked)
                    self.ev(at, "github", cook, "pr_close", epic=e, story=s, pr=pr)
        # Pascal may answer a 🙋 item on GitHub: merging or closing the PR it names.
        main_repo = self.main_repo()
        for e in list(self.events):
            if e["kind"] == "ask_pascal" and (e["detail"] or {}).get("irefs"):
                for ref in sorted({x for r in e["detail"]["irefs"] for x in r}):
                    repo, n = ref.rsplit("#", 1)
                    repo = repo or main_repo
                    x = gh.item(repo, int(n)) if repo else None
                    if x and x["merged"] and x["merged"] > e["time"]:
                        self.ev(
                            x["merged"],
                            "pascal",
                            self.head,
                            "pascal_github",
                            pr=f"{repo}#{n}",
                            action="merged",
                        )
                    elif x and x["closed"] and x["closed"] > e["time"]:
                        self.ev(
                            x["closed"],
                            "pascal",
                            self.head,
                            "pascal_github",
                            pr=f"{repo}#{n}",
                            action="closed",
                        )
        # Scope uses explicit Stories, or an Epic's sub-issues when no Stories are named.
        launches = {
            e["thread"]: e["time"] for e in self.events if e["kind"] == "launch"
        }
        regs: dict[int, tuple[str, dict]] = {}
        for e in self.events:
            if e["kind"] == "batch_register":
                regs.setdefault(e["detail"]["batch"], (e["time"], e["detail"]))
        chefs = {i["b"]: t for t, i in self.threads.items() if i["role"] == "chef"}
        end = max(e["time"] for e in self.events)
        for b in sorted(set(self.batch_refs) | set(regs)):
            chef = chefs.get(b)
            info = self.batch_refs.get(b, {})
            reg = regs.get(b, ("", {}))[1]
            repo = info.get("repo") or reg.get("repo") or main_repo
            refs: list[tuple[str, int]] = info.get("refs") or [
                (str(r or repo), int(n)) for r, n in reg.get("refs") or [] if r or repo
            ]
            t_in = regs[b][0] if b in regs else launches.get(chef or "")
            if b in regs and chef in launches and launches[chef] < regs[b][0]:
                t_in = launches[chef]
            refs = [(r, n) for r, n in refs if r and gh.issue(r, n) is not None]
            stories = [r for r in refs if not gh.is_epic(*r)]
            epics = [r for r in refs if gh.is_epic(*r)]
            # a queued batch takes its card's Epic from its registration
            for e in self.events:
                if (
                    e["kind"] == "batch_register"
                    and e["detail"]["batch"] == b
                    and epics
                ):
                    e["detail"]["epics"] = [f"{r}#{n}" for r, n in epics]
            if stories:
                for r in stories:
                    self.scope(t_in, chef, r, gh.epic_of(*r), b)
            else:
                for ep in epics:
                    for sub in gh.subissues(*ep):
                        created = t3.norm(sub["createdAt"])
                        # A Story filed after the run belongs to a later run.
                        if t_in and created and created <= end:
                            self.scope(
                                max(t_in, created),
                                chef,
                                (sub["repository"]["nameWithOwner"], sub["number"]),
                                ep,
                                b,
                            )
        # Unscoped PR Stories use the earliest batch-registration, Chef-launch, or PR-open time.
        cook_chef = {
            t: i["parent"] for t, i in self.threads.items() if i["role"] == "cook"
        }
        scoped = {e["story"] for e in self.events if e["kind"] == "story_scope"}
        for e in sorted(
            (e for e in self.events if e["kind"] == "pr_open"), key=lambda e: e["time"]
        ):
            if e["story"] in scoped:
                continue
            chef = cook_chef.get(e["thread"])
            bn = self.threads[chef]["b"] if chef else None
            t_in = min(
                x
                for x in (
                    regs[bn][0] if bn in regs else None,
                    launches.get(chef or ""),
                    e["time"],
                )
                if x
            )
            if (e["detail"] or {}).get("loose"):
                self.ev(
                    t_in,
                    "github",
                    chef or self.head,
                    "story_scope",
                    epic=e["epic"],
                    story=e["story"],
                    batch=bn,
                    state_at_scope="open",
                )
            else:
                r, n = e["story"].rsplit("#", 1)
                self.scope(t_in, chef, (r, int(n)), gh.epic_of(r, int(n)), bn)
            scoped.add(e["story"])
        # A Cook owns from its launch the first Story of its batch that its brief names
        # and that has no PR yet; the others start at their first PR.
        # A Story two briefs pick first stays unassigned
        pr_at: dict[str, str] = {}
        for e in self.events:
            if e["kind"] == "pr_open":
                pr_at.setdefault(e["story"], e["time"])
        by_chef = defaultdict(set)
        for e in self.events:
            if e["kind"] == "story_scope" and e["thread"]:
                by_chef[e["thread"]].add(e["story"])
        firsts: dict[tuple[str, str], list[str]] = {}
        for tid, v in self.threads.items():
            if v["role"] != "cook":
                continue
            chef = v["parent"]
            scope = {int(st.rsplit("#", 1)[1]): st for st in by_chef.get(chef, ())}
            at = launches.get(tid) or ""
            first = next(
                (
                    scope[n]
                    for n in v.get("refs", [])
                    if n in scope and pr_at.get(scope[n], "9") > at
                ),
                None,
            )
            if first:
                firsts.setdefault((chef, first), []).append(tid)
        for (chef, story), cooks in sorted(firsts.items()):
            if len(cooks) == 1:
                self.ev(
                    launches.get(cooks[0]),
                    "github",
                    cooks[0],
                    "story_assign",
                    story=story,
                    parent=chef,
                )

    def scope(
        self,
        t_in: str | None,
        chef: str | None,
        story: tuple[str, int],
        epic: tuple[str, int] | None,
        batch: int | None,
    ) -> None:
        if t_in is None:
            raise ValueError("Story scope has no registration or launch time")
        iss = self.gh.issue(*story)
        if iss is None:
            return
        closed = iss["closed"]
        s, e = f"{story[0]}#{story[1]}", (f"{epic[0]}#{epic[1]}" if epic else None)
        self.ev(
            t_in,
            "github",
            chef or self.head,
            "story_scope",
            epic=e,
            story=s,
            batch=batch,
            state_at_scope="closed" if closed and closed <= t_in else "open",
        )


ORDER = {
    kind: i
    for i, kind in enumerate(
        [
            "batch_register",
            "story_scope",
            "launch",
            "run_start",
            "pascal_msg",
            "send",
            "ask_pascal",
        ]
    )
}


def extract(
    snap: t3.Snapshot,
    gh: Facts,
    heads: Iterable[str],
    disk: dict[str, dict] | None = None,
) -> list[dict]:
    """Every fact of the named Head Chefs' runs, in time order.

    `disk` maps a run's id4 to its live watch.toml files; `gh.at(time)` decides
    which GitHub facts a page shows by then.
    """
    brigades = []
    for head in heads:
        brigade = Brigade(snap, gh, head, (disk or {}).get(head[-4:].lower()))
        brigade.walk()
        brigade.t3()
        brigades.append(brigade)
    known = {repo for brigade in brigades for repo, _ in brigade.prs}

    def resolve(name: str | None) -> str | None:
        if not name:
            return None
        matches = sorted(repo for repo in known if repo.rsplit("/", 1)[-1] == name)
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous repository {name}; use distinct T3 project names"
            )
        return gh.repository(matches[0] if matches else name)

    for brigade in brigades:
        for info in brigade.threads.values():
            info["repo"] = resolve(info.get("repo"))
        for info in brigade.batch_refs.values():
            info["repo"] = resolve(info.get("repo"))
            info["refs"] = [(resolve(repo), n) for repo, n in info["refs"] if repo]
        for event in brigade.events:
            d = event["detail"] or {}
            if event["kind"] == "launch" and d.get("repo"):
                d["repo"] = resolve(d["repo"])
            if event["kind"] == "batch_register":
                home = resolve(d.get("repo"))
                d["repo"] = home
                if d.get("refs"):
                    d["refs"] = [[resolve(r) or home, n] for r, n in d["refs"]]
    gh.load_prs({key for brigade in brigades for key in brigade.prs})
    events = []
    for brigade in brigades:
        brigade.github()
        events.extend(brigade.events)
    events.sort(
        key=lambda event: (
            event["time"],
            event["brigade"],
            ORDER.get(event["kind"], 50),
            event["kind"],
            event["thread"],
            json.dumps(event["detail"], ensure_ascii=False, sort_keys=True),
        )
    )
    return events

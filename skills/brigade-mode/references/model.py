#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Brigade carpaccio title statuses as math.

A status is computed, never chosen: status(thread) = f(its own facts, the SET
of its children's kinds). Each f only asks "does some child have kind k" or
"are all children in K", so the set of kinds present decides the status,
whatever the number of children. Enumerating every subset is exhaustive for
these modeled rules. Counters count slots, including repeated phases. A
replaced thread is archived and leaves the tree, so it is not a kind.

Run: uv run model.py
"""

from itertools import combinations, product

# ---------------------------------------------------------------- Cook ---
# A Cook's status is its phase. A Cook whose cards the PM cut leaves its Chef's count.
COOK = {
    "build": "🍳",  # implements, barrages, docs, fixes
    "ask": "⏸️",  # waits on its Chef's answer
    "served": "🍽️",  # stack handed up, retro not done
    "close": "🧹",  # retro or cleanup
    "done": "🍽️",  # stack merged, retro done, T3 settlement confirmed: final
    "stopped": "⏹️",  # the whole batch stopped: final
    "cut_close": "🧹",  # its cards were cut, cleaning up; out of the count
    "cut_stopped": "⏹️",
    "queued": None,  # slot assigned, no thread running yet: not launched, or being relaunched
}
COOK_FINAL = {"done", "stopped", "cut_stopped"}
COOK_IN = {"build", "ask", "served", "close", "done", "stopped", "queued"}

# ---------------------------------------------------------------- Chef ---
# merged: every stack in scope merged; for a batch without PRs, its own work done.
# released: the release done, not required, or cut by the PM.
# checks, merge: passed or said for the frozen heads; true for a batch without PRs.
CHEF_FACTS = ("question", "checks", "merge", "merged", "released", "closed", "stopped")


def chef_status(f, kinds):
    """First line that applies wins."""
    inscope = kinds & COOK_IN
    if f["question"]:
        return "⏸️"  # waits on the Head Chef
    if kinds & {"build", "ask"}:
        return "⏳"  # a Cook builds or asks
    if f["stopped"] or (f["merged"] and f["released"]):
        if not kinds <= COOK_FINAL or not f["closed"]:
            return "🧹"  # retros and cleanup
        return "⛳" if f["merged"] and f["released"] else "⏹️"
    if f["merge"]:
        return "🔀"  # merges, then releases
    if inscope and inscope <= {"served"} and f["checks"]:
        return "🍽️"  # batch ready, x/x
    return "⏳"  # validates or works alone


def chef_coherent(f, kinds):
    inscope = kinds & COOK_IN
    rules = [
        not f["released"] or f["merged"],
        not f["merged"] or f["merge"],
        not f["merge"] or f["checks"],
        not f["closed"] or f["stopped"] or (f["merged"] and f["released"]),
        not f["closed"] or not f["question"],
        # retro comes after the release, or after a stop
        not (inscope & {"close", "done"})
        or f["stopped"]
        or (f["merged"] and f["released"]),
        # an in-scope Cook ends stopped only when the whole batch stops
        "stopped" not in inscope or f["stopped"],
        # a Cook whose stack merged ends 🍽️, even after a Stop
        "stopped" not in inscope or not (f["merged"] and f["released"]),
        # merging needs every Cook served at the time; a fix sends one back to build
        not f["merge"] or f["merged"] or inscope <= {"served", "build", "ask"},
        # no counted Cook, no merge to run (batch without PRs works alone)
        inscope or not f["merge"] or f["merged"],
        # a Stop turns unlaunched slots into stopped ones; nothing merges with a slot unlaunched
        "queued" not in kinds or not (f["stopped"] or f["merge"]),
    ]
    return all(rules)


def counter(phases):
    inscope = [phase for phase in phases if phase in COOK_IN]
    x = sum(phase in {"served", "done"} for phase in inscope)
    return x, len(inscope)


def batch_counter(phases):
    inscope = [phase for phase in phases if phase != "⏹️cut"]
    return sum(phase == "⛳" for phase in inscope), len(inscope)


def chef_properties(f, kinds, s):
    x, y = counter(kinds)
    broken = []
    if s in {"⛳", "⏹️"} and not kinds <= COOK_FINAL:
        broken.append("C1 final over a live Cook")
    if s in {"🍽️", "🔀", "⛳"} and x != y:
        broken.append("C2 x/x needed")
    if s in {"🔀", "🧹"} and kinds & {"build", "ask"}:
        broken.append("C3 merges or closes while a Cook builds or asks")
    if "ask" in kinds and s not in {"⏳", "⏸️"}:
        broken.append("C4 a Cook's question has no owner")
    if s == "⛳" and not (f["merged"] and f["released"]):
        broken.append("C5 delivered without delivery")
    if s == "⏹️" and not (f["stopped"] and not (f["merged"] and f["released"])):
        broken.append("C6 stopped without a stop, or over a delivered batch")
    return broken


# ----------------------------------------------------------- Head Chef ---
# A Chef as the Head Chef sees it: its status, plus who owns its wait.
CHEF_KINDS = {
    "⏳": "⏳",
    "🔀": "🔀",
    "🧹": "🧹",
    "🍽️review": "🍽️",  # batch ready, waits on the PM's review
    "🍽️held": "🍽️",  # the PM holds it
    "⏸️answer": "⏸️",  # question the Head Chef answers itself
    "⏸️escalated": "⏸️",  # question that needs the PM
    "⛳": "⛳",
    "⏹️cut": "⏹️",  # the PM cut the whole batch
    "⏹️stop": "⏹️",  # the PM said Stop
    "queued": None,  # batch registered, Chef not launched yet
}
CHEF_FINAL = {"⛳", "⏹️cut", "⏹️stop"}
# pm_item: an open PM item of the Head Chef's own: Align or added work, a scope cut,
# a reserved action, a fact only the PM knows, a fault it cannot repair (items 1, 3 to 6 and 8).
HC_FACTS = ("pm_item", "own", "stop")


def hc_items(h, kinds):
    progress = bool(kinds & {"⏳", "🔀", "🧹", "⏸️answer"}) or h["own"]
    items = set()
    if h["pm_item"]:
        items.add("own item")
    if "🍽️review" in kinds:
        items.add("review")
    if "⏸️escalated" in kinds:
        items.add("question")
    if "🍽️held" in kinds and not progress:
        items.add("hold")  # D3 a: once nothing else progresses
    return items


def hc_status(h, kinds):
    """First line that applies wins."""
    if hc_items(h, kinds):
        return "❓"  # the PM owes an answer
    if h["own"] or "⏸️answer" in kinds:
        return "🟢"  # works, or answers a Chef
    if not kinds <= CHEF_FINAL:
        return "⏳"  # a Chef is not final
    # D2 b: a cut batch leaves the count, so the rest can end ⛳ x/x
    return "⛳" if "⛳" in kinds and not h["stop"] else "⏹️"


def hc_coherent(h, kinds):
    rules = [
        "⏹️stop" not in kinds or h["stop"],
        kinds or h["stop"] or h["own"] or h["pm_item"],
        # a Stop records queued batches as stopped; at rest a queued batch waits on a live one or the Head Chef
        "queued" not in kinds or not h["stop"],
        "queued" not in kinds
        or h["own"]
        or h["pm_item"]
        or bool(kinds - {"queued"} - CHEF_FINAL),
    ]
    return all(rules)


def hc_properties(h, kinds, s):
    broken = []
    items = hc_items(h, kinds)
    if s in {"⛳", "⏹️"} and not kinds <= CHEF_FINAL:
        broken.append("H1 final over a live Chef")
    if s == "⛳" and (h["stop"] or "⏹️stop" in kinds or "⛳" not in kinds):
        broken.append("H2 delivered after a Stop or with nothing delivered")
    if (s == "❓") != bool(items):
        broken.append("H3 ❓ without a PM item, or a PM item without ❓")
    if kinds & {"⏸️answer", "⏸️escalated"} and s not in {"🟢", "❓"}:
        broken.append("H4 a Chef's question has no owner")
    if "🍽️review" in kinds and s != "❓":
        broken.append("H5 a ready batch does not reach the PM")
    if s == "⏳" and not kinds & {"⏳", "🔀", "🧹", "🍽️held"}:
        broken.append("H6 monitors nothing")
    return broken


# ------------------------------------------------------------- checking ---
def subsets(universe):
    u = sorted(universe)
    for r in range(len(u) + 1):
        yield from (set(c) for c in combinations(u, r))


def check():
    report = {
        "chef_cases": 0,
        "hc_cases": 0,
        "broken": [],
        "chef_cook": set(),
        "hc_chef": set(),
    }
    chef_seen = set()
    for vals in product((False, True), repeat=len(CHEF_FACTS)):
        f = dict(zip(CHEF_FACTS, vals))
        for kinds in subsets(COOK):
            if not chef_coherent(f, kinds):
                continue
            report["chef_cases"] += 1
            s = chef_status(f, kinds)
            chef_seen.add(s)
            for b in chef_properties(f, kinds, s):
                report["broken"].append(("Chef", b, f, sorted(kinds), s))
            for k in kinds:
                if COOK[k]:  # a queued slot has no row
                    report["chef_cook"].add((s, COOK[k]))
    for vals in product((False, True), repeat=len(HC_FACTS)):
        h = dict(zip(HC_FACTS, vals))
        for kinds in subsets(CHEF_KINDS):
            if not hc_coherent(h, kinds):
                continue
            report["hc_cases"] += 1
            s = hc_status(h, kinds)
            for b in hc_properties(h, kinds, s):
                report["broken"].append(("Head Chef", b, h, sorted(kinds), s))
            for k in kinds:
                if CHEF_KINDS[k]:
                    report["hc_chef"].add((s, CHEF_KINDS[k]))
    missing = {CHEF_KINDS[k] for k in CHEF_KINDS if CHEF_KINDS[k]} - chef_seen
    return report, missing


def counter_errors():
    cases = [
        (counter(["served", "served", "build"]), (2, 3)),
        (counter(["served", "cut_stopped"]), (1, 1)),
        (batch_counter(["⛳", "⛳", "⏹️cut", "🔀"]), (2, 3)),
    ]
    return [(actual, expected) for actual, expected in cases if actual != expected]


HC_ROWS, CHEF_COLS = (
    ["🟢", "⏳", "❓", "⛳", "⏹️"],
    ["⏳", "🔀", "🧹", "🍽️", "⏸️", "⛳", "⏹️"],
)
COOK_COLS = ["🍳", "🧹", "🍽️", "⏸️", "⏹️"]


def grid(rows, cols, pairs):
    out = ["| | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for r in rows:
        out.append(
            f"| {r} | "
            + " | ".join("✅" if (r, c) in pairs else "❌" for c in cols)
            + " |"
        )
    return "\n".join(out)


if __name__ == "__main__":
    rep, missing = check()
    count_errors = counter_errors()
    print(f"Chef cases: {rep['chef_cases']}, Head Chef cases: {rep['hc_cases']}")
    print("Chef statuses no case reaches:", missing or "none")
    print(f"Broken properties: {len(rep['broken'])}")
    print(f"Broken counters: {len(count_errors)}")
    for b in rep["broken"][:20]:
        print("  ", b)
    for actual, expected in count_errors:
        print("  counter:", actual, "expected", expected)
    print("\nChef x Cook\n" + grid(CHEF_COLS, COOK_COLS, rep["chef_cook"]))
    print("\nHead Chef x Chef\n" + grid(HC_ROWS, CHEF_COLS, rep["hc_chef"]))
    if rep["broken"] or missing or count_errors:
        raise SystemExit(1)

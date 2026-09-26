# Pressure-Test Rubric

Use during `DirectionCheck`, and as a sanity pass before finalizing an `AlignmentDraft` or `BriefAuthoring` artifact. The job is to stress-test a direction honestly, not to validate it.

This rubric applies across the domains `pa-vision` serves: software, content or websites, PM systems, knowledge systems, and personal decisions. Where a dimension does not fit the domain, skip it rather than forcing it.

---

## 1. Value check — acute or marginal?

A direction is only as strong as the need it addresses.

- **Acute:** the problem is felt regularly, the beneficiary has already built a workaround, and they would switch today if something better existed.
- **Marginal:** nice to have. People nod politely; behavior does not change.

**Questions**
- Can you name the specific people, teams, readers, or future-you who feels this?
- What are they doing today instead? The real competitor is always the current workaround.
- How often does the problem surface? Daily pressure beats monthly beats quarterly.
- Is this pull (someone is asking for it) or push (we think they should want it)?

**Red flags**
- "Everyone could use this."
- "It's like X but better" with no structural reason.
- High-intensity but rare — real pain, but too infrequent to justify the cost.

---

## 2. Feasibility check

Can this actually be built, written, restructured, or adopted at the level the direction implies?

**Capability**
- Does the core capability already exist and work reliably?
- What is the hardest part? Known-hard or novel?
- External dependencies (APIs, data, third parties, other teams, calendars, energy) that are not under our control?

**Resources**
- Minimum people, time, or attention to get a first version out?
- Any specialized expertise missing?
- Regulatory, legal, compliance, editorial, or policy gates?

**Time-to-value**
- Is there a version that delivers something real in days or weeks, not months?
- What is on the critical path?

**Red flags**
- "We just need to solve [very hard prerequisite] first."
- Multiple hard dependencies that must all land together.
- Minimum version still measured in months.

---

## 3. Differentiation check

What makes this direction meaningfully different, not just nominally better?

**Ladder of difference, strongest to weakest**

1. **New capability** — does something that was previously not possible in this context.
2. **Large-multiple improvement** — enough better on a dimension that matters that behavior changes.
3. **New audience or context** — brings an existing capability to people, places, or situations that were excluded.
4. **Better experience** — same capability, dramatically simpler to live with.
5. **Lower cost** — same thing, less effort or money (weakest, easily competed away or regretted later).

**Questions**
- If someone described this in one sentence to a peer, would that sentence land?
- What is the one thing this does that nothing nearby does?
- Is that difference durable, or copyable in a week?
- Is the difference something the beneficiary actually cares about, or only something the builder finds interesting?

For personal or internal decisions, read "differentiation" as "does this materially change the situation, or just rearrange it?"

---

## 4. Assumption audit

Every direction rests on assumptions. When assumptions are load-bearing, name them in three tiers.

### Must be true (dealbreakers)
If wrong, the direction collapses. Validate before committing real resources.

### Should be true (important)
If wrong, the approach changes but the core can still work.

### Might be true (secondary)
Nice to have. Do not validate until the core is proven.

For small or low-stakes work, a flat list is fine. The tiering earns its keep when the direction has real consequences.

---

## 5. Decision matrix

When comparing candidate directions, rank each on value against feasibility.

|                  | High feasibility     | Low feasibility      |
|------------------|----------------------|----------------------|
| **High value**   | Do this first        | Worth the risk       |
| **Low value**    | Only if trivial      | Don't do this        |

Use differentiation as the tiebreaker between directions that land in the same cell.

---

## 6. Recommendation shape

End a `DirectionCheck` with one of four calls, each with a one-line reason. These align with the recommendation language in `DirectionCheck/MetaSkill.md`.

- **Proceed** — evidence for value, feasibility, and difference is sufficient to commit.
- **Revise** — the direction has merit, but a specific piece must change before committing.
- **Defer** — not wrong, but blocked by timing, prerequisites, or a missing signal.
- **Stop** — a fatal flaw, or a marginal idea dressed as an acute one.

If the call is anything other than **Proceed**, name what would have to be true to change it.

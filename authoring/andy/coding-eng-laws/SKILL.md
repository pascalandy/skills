---
name: "coding-eng-laws"
description: "Use when analyzing code, architecture, team, or planning decisions using software engineering laws and principles, or when `coding-eng-laws` is mentioned."
kind: "dev"
---

# Software Engineering Laws — Thinking Lens

## Purpose

A library of **56 named laws, principles, and cognitive biases** organized as
seven analytical lenses. The user describes a situation — a slipping deadline,
a team that keeps growing dysfunctional, a codebase that no one trusts, a
decision they keep second-guessing — and the router pulls the relevant
cluster of laws to reason with.

The collection is **harness-agnostic** and **domain-agnostic**: most of the
laws apply equally to software, to running a business, to managing a team,
and to personal life choices. Pareto, Parkinson, Sunk Cost, Inversion,
Dunbar, and First Principles are just as useful when you are deciding whether
to keep a relationship, a side project, or an entire career path.

Each law is presented with what it says, where it came from, why it matters,
and how it manifests in real situations.

## What's Included

| # | Lens | Laws | When to invoke |
|---|---|---|---|
| 1 | `system-and-architecture` | 9 | Designing systems, debugging emergent complexity, distributed-system trade-offs |
| 2 | `people-teams-organizations` | 9 | Hiring, team scaling, comms structure, productivity distribution |
| 3 | `time-estimation-planning` | 6 | Estimates failing, deadlines slipping, "almost done" debugging |
| 4 | `quality-maintenance-evolution` | 11 | Tech debt, code rot, testing strategy, defect economics |
| 5 | `scale-performance-growth` | 3 | Parallelization limits, network-effect investments |
| 6 | `coding-and-design-principles` | 6 | Code review, refactoring, API design, "is this over-engineered?" |
| 7 | `decision-making-cognitive-biases` | 12 | High-stakes decisions, debating, hiring, life choices, second-guessing |

Total: 56 laws.

## Invocation Scenarios

| User says | Router routes to |
|---|---|
| "Why is this distributed system so hard to keep consistent?" | `system-and-architecture` (CAP, Fallacies of Distributed Computing) |
| "We added two engineers and we're moving slower" | `people-teams-organizations` (Brooks, Ringelmann) |
| "I keep underestimating this project" | `time-estimation-planning` (Hofstadter, Ninety-Ninety) |
| "Our codebase feels like it's rotting" | `quality-maintenance-evolution` (Broken Windows, Lehman, Tech Debt) |
| "Should I parallelize this pipeline?" | `scale-performance-growth` (Amdahl, Gustafson) |
| "Is this code over-engineered?" | `coding-and-design-principles` (KISS, YAGNI, SOLID) |
| "I'm not sure if I'm being objective about this decision" | `decision-making-cognitive-biases` (Confirmation Bias, Inversion, Sunk Cost) |
| "Apply the laws to: <situation>" | Router selects best-fit lens, may compose multiple |
| "What law fits this?" | Router returns shortlist with one-line rationale |

## Usage Examples

**Example 1 — team coordination**

> User: We added three senior engineers to the late project and the deadline keeps slipping further. What's going on?

The skill loads `people-teams-organizations` → applies **Brooks's Law**
(adding manpower to a late project makes it later, due to onboarding cost
and communication overhead) and **Ringelmann Effect** (per-person
productivity drops as group size grows). Diagnoses ramp time + comms
overhead as the actual cost. Suggests freezing team size and re-scoping.

**Example 2 — life decision composed with code decision**

> User: I've spent six months on this side project and it's not getting traction. Should I push through?

The skill loads `decision-making-cognitive-biases` → applies **Sunk Cost
Fallacy** (past investment is irrelevant to forward decision) and
**Inversion** (instead of "should I keep going?", ask "if I were starting
today knowing what I know, would I start this?"). Composes with **Pareto
Principle** to ask which 20% of the project, if any, has produced 80% of
the value or learning so far.

**Example 3 — code review**

> User: This new abstraction layer is supposed to make things easier but it feels worse. Is it?

The skill loads `coding-and-design-principles` → applies **YAGNI** (was
the abstraction added speculatively?), **KISS** (does it preserve the
simpler call site?), **Law of Leaky Abstractions** from
`system-and-architecture` (does it actually hide complexity or just
relocate it?), and **Tesler's Law** (irreducible complexity has to live
somewhere — was it just shifted from caller to abstraction?).

**Example 4 — diagnose without moralizing**

> User: My team keeps building features no one uses.

The skill loads `decision-making-cognitive-biases` (Confirmation Bias —
team confirms its own roadmap), composes with `coding-and-design-principles`
(YAGNI — building for hypothetical needs), and `time-estimation-planning`
(Goodhart — if "ship N features per quarter" is the metric, the metric
is the problem). The diagnosis is structural, not a moral failing.

## How to Use This Collection

- **Start shallow.** Read this `SKILL.md` and let the router pick a lens.
- **Compose when needed.** Real situations rarely fit one lens — Brooks
  composes with Conway, YAGNI composes with Sunk Cost, Murphy composes with
  almost everything. The router will suggest composition when the situation
  is ambiguous.
- **Reference files are source material.** Each sub-skill's
  `references/` holds the per-law detail pages. Cite them to ground
  reasoning, but the **lens** — not the page — is what's being applied.
- **Hold conclusions loosely.** Laws are pattern names, not proofs. They
  are useful when they help you ask better questions; ignore them when
  the situation genuinely doesn't fit.

## Intellectual Posture

- **Diagnose before prescribing.** Pick the law that *describes* what is
  happening before reaching for the law that tells you what to do.
- **Inversion first when stuck.** When a question is hard ("how do I
  make this team productive?"), invert it ("what would guarantee this
  team is unproductive?") and remove those causes.
- **Goodhart any metric you propose.** If you propose a target, immediately
  ask how it will be gamed.
- **The law is a hypothesis, not a verdict.** "This looks like Brooks's
  Law" invites investigation; "this is Brooks's Law" closes it
  prematurely.

## Routing

Load `references/ROUTER.md` to determine which sub-skill handles this
request, then load that sub-skill's `MetaSkill.md`. Each sub-skill's
`MetaSkill.md` provides an overview, a table of its laws with one-liners,
and pointers to the per-law detail files in its own `references/`.

## Adding a new law

To add a 57th law (or any new principle / pattern / bias):

1. Pick the sub-skill it belongs to (or create a new one if it doesn't
   fit any existing lens).
2. Drop the law's detail page into that sub-skill's `references/` as
   `kebab-case-name.md`. Use the existing pages as a format template
   (Takeaways, Overview, Examples, Origins, Further Reading,
   Related Laws).
3. Append one row to that sub-skill's `MetaSkill.md` law table.
4. Append the law's distinctive keywords to that sub-skill's
   `MetaSkill.md` `USE WHEN` line.
5. Append the same keywords to `references/ROUTER.md` for the matching
   row, and to this root `SKILL.md` `USE WHEN` (so the scanner surfaces
   the collection on those triggers).

No other file needs to change.

## Source

All 56 detail pages are reproduced verbatim from
[lawsofsoftwareengineering.com](https://lawsofsoftwareengineering.com/laws/),
organized into the seven-part structure used in the original Table of
Contents. Each detail page retains its original "Further Reading" and
"Related Laws" cross-links.

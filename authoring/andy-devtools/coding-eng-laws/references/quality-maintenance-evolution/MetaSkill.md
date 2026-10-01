---
name: laws-quality-maintenance-evolution
description: >
  Lens for reasoning about long-term system health, code rot, defect
  economics, and evolutionary pressure. USE WHEN Murphy's Law, anything
  that can go wrong will, Postel's Law, robustness principle, be liberal in
  what you accept, broken windows theory, small disorder breeds bigger
  disorder, boy scout rule, leave it better than you found it, technical
  debt, interest accruing on shortcuts, Linus's Law, given enough eyeballs
  bugs are shallow, Kernighan's Law, debugging twice as hard as writing,
  testing pyramid, unit vs integration vs e2e, pesticide paradox, same
  tests stop finding bugs, Lehman's Laws, software must evolve, Sturgeon's
  Law, 90 percent of everything is crap, code rot, codebase decay,
  defect economics, test strategy, maintenance burden.
---

# Lens 4 — Quality, Maintenance & Evolution

## When to apply this lens

You're worried about *long-term* health rather than immediate function.
Symptoms:

- Codebase morale is dropping; small messes are accumulating.
- Tests pass but bugs still ship; or tests stopped finding anything new.
- "We'll fix it later" has been said three sprints in a row.
- Debugging an old bug now takes longer than the original feature.
- Software hasn't been touched in a year and a dependency upgrade just broke it.

**Posture:** software decays unless actively maintained. Defects, debt,
and entropy are not events — they are *forces* that act continuously
unless you push back.

## Laws in this lens

| Law | One-line | File |
|---|---|---|
| Murphy's Law | Anything that can go wrong will go wrong. | `references/murphys-law.md` |
| Postel's Law | Be conservative in what you send, liberal in what you accept. | `references/postels-law.md` |
| Broken Windows Theory | Don't leave bad designs, wrong decisions, or poor code unrepaired. | `references/broken-windows-theory.md` |
| Boy Scout Rule | Leave the code better than you found it. | `references/boy-scout-rule.md` |
| Technical Debt | Everything that slows us down when developing software. | `references/technical-debt.md` |
| Linus's Law | Given enough eyeballs, all bugs are shallow. | `references/linuss-law.md` |
| Kernighan's Law | Debugging is twice as hard as writing the code in the first place. | `references/kernighans-law.md` |
| Testing Pyramid | Many fast unit tests, fewer integration tests, only a small number of UI tests. | `references/testing-pyramid.md` |
| Pesticide Paradox | If the same tests are repeated, eventually they stop finding new bugs. | `references/pesticide-paradox.md` |
| Lehman's Laws | Software that reflects the real world must evolve, with predictable limits. | `references/lehmans-laws.md` |
| Sturgeon's Law | Ninety percent of everything is crap. | `references/sturgeons-law.md` |

## How to use

1. Identify the **time horizon** of the concern (a release? a year? the
   life of the system?).
2. Pick the law(s) that name the decay or quality dynamic in play.
3. Boy Scout + Broken Windows are *prescriptive* — they tell you what to
   do. Murphy + Pesticide + Lehman are *descriptive* — they tell you what
   will happen if you don't.
4. Kernighan's Law is the strongest guard against premature cleverness:
   if you write code at the limit of your ability, you can't debug it.

## Common compositions

- **Broken Windows + Boy Scout + Tech Debt** — the maintenance trio.
- **Pesticide Paradox + Testing Pyramid** — design a test portfolio that keeps finding new bugs.
- **Murphy + Postel + Fallacies of Distributed Computing (Lens 1)** — defending against the network.
- **Lehman + Second-System Effect (Lens 1)** — software *must* evolve, but rewrites are dangerous.
- **Kernighan + Knuth (Lens 3)** — both warn against cleverness without measurement.

Compose with **Lens 1 (System & Architecture)** for the structural side of
quality, and **Lens 6 (Coding & Design)** for the per-line side.

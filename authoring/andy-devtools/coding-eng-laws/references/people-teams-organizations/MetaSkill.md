---
name: laws-people-teams-organizations
description: >
  Lens for reasoning about coordination cost, comms structure, productivity
  distribution, and organizational dysfunction. USE WHEN Conway's Law, org
  chart in code, inverse Conway maneuver, Brooks's Law, adding people to
  late project, mythical man-month, Dunbar's number, 150 stable
  relationships, team size, Ringelmann effect, per-person productivity drop,
  social loafing, Price's Law, square root of people do half the work,
  Putt's Law, technology managed by those who don't understand, Peter
  Principle, promoted to incompetence, bus factor, key person risk, knowledge
  silo, Dilbert principle, promoted to limit damage, hiring, team scaling,
  comms structure, organizational dysfunction.
---

# Lens 2 — People, Teams & Organizations

## When to apply this lens

You're reasoning about a problem that *looks* technical but is actually
about coordination, headcount, comms structure, or incentives. Symptoms:

- Adding people did not speed things up.
- One team's architecture mirrors the org chart in a way that's becoming painful.
- A small handful of people are doing most of the work.
- Knowledge is concentrated in one or two people and you're nervous.
- Meetings have grown to fill every calendar.
- Someone got promoted out of the role they were great in.

**Posture:** software architecture is downstream of human architecture.
Most "technical" problems above ~10 people are actually comms problems.

## Laws in this lens

| Law | One-line | File |
|---|---|---|
| Conway's Law | Organizations design systems that mirror their own communication structure. | `references/conways-law.md` |
| Brooks's Law | Adding manpower to a late software project makes it later. | `references/brooks-law.md` |
| Dunbar's Number | A cognitive limit of ~150 stable relationships per person. | `references/dunbars-number.md` |
| Ringelmann Effect | Individual productivity decreases as group size increases. | `references/ringelmann-effect.md` |
| Price's Law | The square root of N people in a domain do half the work. | `references/prices-law.md` |
| Putt's Law | Technology is dominated by those who manage what they do not understand. | `references/putts-law.md` |
| Peter Principle | In a hierarchy, every employee tends to rise to their level of incompetence. | `references/peter-principle.md` |
| Bus Factor | The minimum number of team members whose loss would cripple the project. | `references/bus-factor.md` |
| Dilbert Principle | The least competent are promoted to management to limit their potential for damage. | `references/dilbert-principle.md` |

## How to use

1. State the **observed dysfunction** in one sentence ("we keep slipping",
   "the new hire isn't ramping", "X is the only one who knows Y").
2. Match it to the law that names the pattern.
3. Read the corresponding file for the historical framing and known
   counter-moves (e.g. Inverse Conway Maneuver, two-pizza teams).
4. Test the diagnosis: would the predicted symptom be *absent* if the
   law didn't apply here? If not, you may be naming the wrong pattern.

## Common compositions

- **Conway's Law + Brooks's Law** — a reorg launched mid-crunch that makes the late project later.
- **Ringelmann + Dunbar** — a team that's grown past the point where everyone knows everyone.
- **Price's Law + Bus Factor** — the few who do most of the work are also the bus-factor risk.
- **Peter + Dilbert + Putt** — management tier that systematically rewards the wrong skills.

Compose with **Lens 3 (Time, Estimation, Planning)** for crunch
dynamics, and **Lens 7 (Decision-Making)** when the question is "are we
seeing this clearly or rationalizing?"

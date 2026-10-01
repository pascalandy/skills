---
name: laws-system-and-architecture
description: >
  Lens for reasoning about systems that grow complex even when designed
  carefully. USE WHEN Gall's Law, leaky abstractions, Tesler's Law,
  conservation of complexity, CAP theorem, consistency vs availability vs
  partition tolerance, Hyrum's Law, observable behavior depended on,
  second-system effect, over-engineered rewrite, fallacies of distributed
  computing, network is reliable, latency is zero, bandwidth is infinite,
  topology doesn't change, law of unintended consequences, Zawinski's Law,
  feature creep, designing systems, debugging emergent complexity,
  distributed-system trade-offs.
---

# Lens 1 — System & Architecture

## When to apply this lens

You're designing or debugging a system and complexity keeps showing up
where you didn't expect it. Symptoms:

- A "clean" abstraction is leaking implementation details.
- A "simple" rewrite of a working system grew bloated.
- A distributed system is making impossible promises.
- An API change you thought was safe broke someone downstream.
- Every change to one part of the system surprises another part.

**Posture:** complexity is not a moral failure of the designer. It is a
property of the problem domain that gets *shifted around*, not eliminated.
This lens helps you locate where the complexity actually lives.

## Laws in this lens

| Law | One-line | File |
|---|---|---|
| Gall's Law | A complex system that works is invariably found to have evolved from a simple system that worked. | `references/galls-law.md` |
| Law of Leaky Abstractions | All non-trivial abstractions are leaky to some degree. | `references/law-of-leaky-abstractions.md` |
| Tesler's Law (Conservation of Complexity) | Every application has irreducible complexity that can only be shifted, not eliminated. | `references/teslers-law.md` |
| CAP Theorem | A distributed system can guarantee only two of: consistency, availability, partition tolerance. | `references/cap-theorem.md` |
| Hyrum's Law | With enough users, every observable behavior of your system will be depended on by somebody. | `references/hyrums-law.md` |
| Second-System Effect | Successful systems tend to be followed by overengineered, bloated replacements. | `references/second-system-effect.md` |
| Fallacies of Distributed Computing | The eight assumptions architects keep making about networks that aren't true. | `references/fallacies-of-distributed-computing.md` |
| Law of Unintended Consequences | Whenever you change a complex system, expect surprise. | `references/law-of-unintended-consequences.md` |
| Zawinski's Law | Every program attempts to expand until it can read mail. | `references/zawinskis-law.md` |

## How to use

1. Identify the **symptom** (leak, bloat, surprise, broken contract, unexpected coupling).
2. Pick the law that *names the pattern* — usually one or two will fit.
3. Read the corresponding file in `references/` for the framing, examples, and origins.
4. Reason about the situation **using the named pattern as a hypothesis**, not a verdict.

## Common compositions

- **Gall's Law + Second-System Effect** — when someone proposes a "from-scratch rewrite," both fire together.
- **Tesler's Law + Leaky Abstractions** — the irreducible complexity has been shifted into the abstraction layer, and now leaks.
- **Hyrum's Law + Law of Unintended Consequences** — a "safe" API change breaks an unknown caller.
- **CAP + Fallacies of Distributed Computing** — the design assumes properties the network does not guarantee.

Compose with **Lens 6 (Coding & Design)** when the question shifts from
"why is this system complex?" to "how should I write this code?"

---
name: laws-scale-performance-growth
description: >
  Lens for reasoning about scaling limits, parallelization ceilings, and
  network effects. USE WHEN Amdahl's Law, parallelization limit, serial
  fraction bottleneck, diminishing returns, Gustafson's Law, scaled
  speedup, bigger problem same time, Metcalfe's Law, network value square
  of users, network effects, scaling limit, performance ceiling, when
  going wider stops helping, two-sided marketplace.
---

# Lens 5 — Scale, Performance & Growth

## When to apply this lens

You're planning, building, or evaluating something whose value or
performance depends on **scale**. Symptoms:

- Adding cores / workers / shards has diminishing returns.
- "We'll just parallelize it" — but a serial step dominates.
- A network or platform is growing and you're trying to value it.
- A two-sided marketplace is at the threshold of a virtuous cycle (or stuck).

**Posture:** scaling is governed by hard mathematical limits, not
willpower. Knowing which limit you're hitting tells you whether to
parallelize harder, change the workload, or stop investing.

## Laws in this lens

| Law | One-line | File |
|---|---|---|
| Amdahl's Law | Parallel speedup is bounded by the serial fraction of the work. | `references/amdahls-law.md` |
| Gustafson's Law | With more processors, you can solve a *bigger* problem in the same time. | `references/gustafsons-law.md` |
| Metcalfe's Law | The value of a network grows as the square of its users. | `references/metcalfes-law.md` |

## How to use

1. Identify whether the question is **fixed-size** (Amdahl) or **scalable
   workload** (Gustafson). If you cannot make the problem bigger,
   Amdahl's serial-fraction ceiling applies.
2. For network or platform value, Metcalfe argues for early subsidy of
   user count — but watch for **Goodhart (Lens 3)** corruption of the
   "users" metric (bots, dormant accounts).
3. Combine with **Pareto (Lens 7)**: 80% of runtime usually lives in 20%
   of code — measure first, parallelize after.

## Common compositions

- **Amdahl + Knuth (Lens 3)** — don't parallelize until you've measured the serial bottleneck.
- **Amdahl + Gustafson** — held in tension; the right one depends on whether the problem is fixed or scalable.
- **Metcalfe + Goodhart (Lens 3)** — network value is real, but measuring "users" gets gamed instantly.
- **Metcalfe + Lindy (Lens 7)** — older networks compound value (Metcalfe) and predict longevity (Lindy).

This lens is small but high-leverage. The rest of the time, this lens
points back to **Lens 1 (architecture)** and **Lens 6 (code)** for the
actual implementation.

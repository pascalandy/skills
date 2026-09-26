---
name: laws-time-estimation-planning
description: >
  Lens for reasoning about why estimates fail, why deadlines slip, and why
  "almost done" usually isn't. USE WHEN Hofstadter's Law, takes longer than
  expected, Parkinson's Law, work expands to fill time, ninety-ninety rule,
  last 10 percent, Goodhart's Law, metric becomes target, Gilb's Law,
  anything can be measured, premature optimization, Knuth root of all evil,
  estimates failing, deadline slipping, almost done is never done,
  sandbagging, padding, time-box, sprint planning, target gaming.
---

# Lens 3 — Time, Estimation & Planning

## When to apply this lens

You're trying to predict, schedule, or measure work and the numbers keep
betraying you. Symptoms:

- "We're 90% done" — and you've been 90% done for weeks.
- The estimate keeps growing as you learn more.
- The deadline is loose and the work mysteriously fills it.
- A metric you set up to drive behavior is being gamed.
- You're tuning code that nobody benchmarked first.

**Posture:** estimation failure is structural, not a personal flaw of the
estimator. Once you set a target, the target itself starts shaping
behavior — sometimes in ways that defeat the purpose.

## Laws in this lens

| Law | One-line | File |
|---|---|---|
| Hofstadter's Law | It always takes longer than you expect, even when you account for Hofstadter's Law. | `references/hofstadters-law.md` |
| Parkinson's Law | Work expands to fill the time available for its completion. | `references/parkinsons-law.md` |
| Ninety-Ninety Rule | The first 90% of code takes the first 90% of time; the last 10% takes the other 90%. | `references/ninety-ninety-rule.md` |
| Goodhart's Law | When a measure becomes a target, it ceases to be a good measure. | `references/goodharts-law.md` |
| Gilb's Law | Anything you need to quantify can be measured in some way better than not measuring it. | `references/gilbs-law.md` |
| Knuth's Optimization Principle | Premature optimization is the root of all evil. | `references/premature-optimization.md` |

## How to use

1. Name the **failure mode** (estimate too low, scope creep, gold-plating, gamed metric, blind tuning).
2. Match to the law that describes the pattern.
3. The pair **Parkinson + Hofstadter** is in tension on purpose — short
   deadlines counter Parkinson but invite Hofstadter pressure. Use both
   to set deadlines that are *short but not unrealistic*.
4. The pair **Goodhart + Gilb** is also in tension — measure things, but
   don't elevate the measurement to the goal.

## Common compositions

- **Parkinson + Ninety-Ninety + Hofstadter** — the standard "why is this slipping" trio.
- **Goodhart + Gilb** — designing a metric that informs without becoming the goal.
- **Knuth + Pareto (Lens 7)** — *both* tell you not to optimize until you've measured where the 80% actually is.
- **Brooks (Lens 2) + this lens** — the late project that gets later when you add people.

Compose with **Lens 2 (People, Teams)** for the human dynamics behind
slippage, and **Lens 7 (Decision-Making)** for the bias that makes
estimators systematically over-confident.

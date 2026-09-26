---
name: laws-coding-and-design-principles
description: >
  Lens for reasoning about per-file, per-class, per-function design
  decisions. USE WHEN DRY, don't repeat yourself, single source of truth,
  KISS, keep it simple, YAGNI, you aren't gonna need it, speculative
  generality, SOLID principles, single responsibility, open closed
  principle, Liskov substitution, interface segregation, dependency
  inversion, Law of Demeter, talk only to friends, train wreck, principle
  of least astonishment, surprise the user, code review, refactoring,
  API design, is this over-engineered, abstraction smell, naming, coupling.
---

# Lens 6 — Coding & Design Principles

## When to apply this lens

You're at the level of a class, function, module, or API and asking
"is this code right?" Symptoms:

- A piece of logic is repeated in three places — refactor or leave it?
- A new abstraction layer is being proposed — is it needed?
- A class has grown to 800 lines and four responsibilities.
- A method chain reads like `a.b().c().d().e()` and you're nervous.
- An API behaves in a way callers don't expect.

**Posture:** these principles are guard-rails against the most common
small-scale mistakes — duplication, premature abstraction, surprising
behavior, tight coupling. They are not laws of physics; they are
heuristics that tend to produce code other humans can change later.

## Laws in this lens

| Law | One-line | File |
|---|---|---|
| DRY | Every piece of knowledge must have a single, unambiguous, authoritative representation. | `references/dry-principle.md` |
| KISS | Designs and systems should be as simple as possible. | `references/kiss-principle.md` |
| YAGNI | Don't add functionality until it is necessary. | `references/yagni.md` |
| SOLID Principles | Five guidelines (SRP, OCP, LSP, ISP, DIP) for maintainable OO design. | `references/solid-principles.md` |
| Law of Demeter | An object should only interact with its immediate friends, not strangers. | `references/law-of-demeter.md` |
| Principle of Least Astonishment | A system should behave the way users least expect to be surprised. | `references/principle-of-least-astonishment.md` |

## How to use

1. Identify the **specific code smell** (duplication, speculative
   generality, god class, train wreck, surprising API).
2. Pick the principle that names the smell.
3. Apply it as a **direction of refactoring**, not as a rule. DRY taken
   to extreme creates wrong-abstraction coupling; KISS taken to extreme
   blocks legitimate complexity; YAGNI taken to extreme produces myopic
   code.
4. The combination **DRY + YAGNI + KISS** is held in tension on purpose —
   each is a counterweight to the others.

## Common compositions

- **YAGNI + Sunk Cost (Lens 7)** — you over-built it, now you defend it.
- **DRY + Hyrum's Law (Lens 1)** — when you "consolidate" code, callers were depending on the divergent behaviors.
- **KISS + Tesler's Law (Lens 1)** — irreducible complexity has to live somewhere; KISS is about not adding *additional* complexity.
- **Demeter + Conway's Law (Lens 2)** — coupling between modules tracks coupling between teams.
- **Least Astonishment + Postel's Law (Lens 4)** — both about being a polite citizen at API boundaries.

Compose with **Lens 1 (System & Architecture)** when the question
escalates from "this function" to "this design", and **Lens 4 (Quality
& Maintenance)** for long-term consequences of design choices.

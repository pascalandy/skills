---
name: software-engineering-laws-router
description: Dispatch table for the software-engineering-laws meta-skill. USE WHEN Gall's Law, leaky abstractions, Tesler's Law, conservation of complexity, CAP theorem, Hyrum's Law, second-system effect, fallacies of distributed computing, law of unintended consequences, Zawinski's Law, Conway's Law, Brooks's Law, Dunbar's number, Ringelmann effect, Price's Law, Putt's Law, Peter Principle, bus factor, Dilbert principle, Hofstadter's Law, Parkinson's Law, ninety-ninety rule, Goodhart's Law, Gilb's Law, premature optimization, Knuth, Murphy's Law, Postel's Law, robustness principle, broken windows theory, boy scout rule, technical debt, Linus's Law, Kernighan's Law, testing pyramid, pesticide paradox, Lehman's Laws of software evolution, Sturgeon's Law, Amdahl's Law, Gustafson's Law, Metcalfe's Law, DRY, KISS, YAGNI, SOLID principles, Law of Demeter, principle of least astonishment, Dunning-Kruger, Hanlon's razor, Occam's razor, sunk cost fallacy, map is not the territory, confirmation bias, hype cycle, Amara's law, Lindy effect, first principles thinking, inversion, Pareto principle, 80/20 rule, Cunningham's Law, slipping deadline, missed estimate, team scaling problem, comms overhead, productivity distribution, code rot, technical debt, codebase decay, refactor question, over-engineering, abstraction smell, decision under uncertainty, biased reasoning, second-guessing, life decision, project decision, what law applies here, apply software engineering law.
---

# Software Engineering Laws — Router

## Routing

| Request pattern | Route to |
|---|---|
| Gall's Law, leaky abstractions, Tesler's Law, conservation of complexity, CAP theorem, consistency vs availability, Hyrum's Law, observable behavior depended on, second-system effect, over-engineered rewrite, fallacies of distributed computing, network is reliable, law of unintended consequences, complex system change, Zawinski's Law, feature creep to mail, designing systems, debugging emergent complexity, distributed-system trade-offs, why does my system behave this way | `system-and-architecture/MetaSkill.md` |
| Conway's Law, org chart in code, Brooks's Law, adding people to late project, Dunbar's number, 150 stable relationships, Ringelmann effect, productivity loss with group size, Price's Law, sqrt of people do half work, Putt's Law, technology managed by those who don't understand, Peter Principle, promoted to incompetence, bus factor, key person risk, Dilbert principle, promoted to limit damage, hiring, team scaling, comms structure, who actually does the work, organizational dysfunction | `people-teams-organizations/MetaSkill.md` |
| Hofstadter's Law, takes longer than expected, Parkinson's Law, work expands to fill time, ninety-ninety rule, last 10 percent, Goodhart's Law, metric becomes target, Gilb's Law, anything can be measured, premature optimization, Knuth root of all evil, estimates failing, deadline slipping, almost done is never done, sandbagging, padding, time-box, sprint planning | `time-estimation-planning/MetaSkill.md` |
| Murphy's Law, anything can go wrong, Postel's Law, robustness principle, be liberal in what you accept, broken windows theory, small disorder breeds bigger disorder, boy scout rule, leave it better than you found it, technical debt, interest accruing on shortcuts, Linus's Law, given enough eyeballs, Kernighan's Law, debugging twice as hard, testing pyramid, unit vs integration vs e2e, pesticide paradox, same tests stop finding bugs, Lehman's Laws, software must evolve, Sturgeon's Law, 90 percent of everything is crap, code rot, codebase decay, defect economics, test strategy, maintenance burden | `quality-maintenance-evolution/MetaSkill.md` |
| Amdahl's Law, parallelization limit, serial fraction, Gustafson's Law, scaled speedup, bigger problem same time, Metcalfe's Law, network value square of users, scaling limits, performance ceiling, network effects, when does going wider stop helping | `scale-performance-growth/MetaSkill.md` |
| DRY, don't repeat yourself, single source of truth, KISS, keep it simple, YAGNI, you aren't gonna need it, SOLID principles, single responsibility, open closed, Liskov, interface segregation, dependency inversion, Law of Demeter, talk only to friends, principle of least astonishment, surprise the user, code review, refactoring, API design, is this over-engineered, abstraction smell | `coding-and-design-principles/MetaSkill.md` |
| Dunning-Kruger effect, less you know more confident, Hanlon's razor, never attribute to malice, Occam's razor, simplest explanation, sunk cost fallacy, irrelevant past investment, map is not the territory, model vs reality, confirmation bias, favoring supporting info, hype cycle, Amara's law, overestimate short underestimate long, Lindy effect, future longevity proportional to age, first principles thinking, fundamental truths, inversion, work backward from failure, Pareto principle, 80 20 rule, Cunningham's Law, post the wrong answer, decision under uncertainty, second-guessing, biased reasoning, life decision, hiring, debating, am I being objective | `decision-making-cognitive-biases/MetaSkill.md` |

## Composition note

Most real situations compose more than one lens. Common pairings:

- **Brooks (people)** + **Conway (people)** — late project + reorg attempt.
- **YAGNI (coding)** + **Sunk Cost (decision)** — speculative feature you've already invested in.
- **Goodhart (time)** + **Confirmation Bias (decision)** — a metric you set and now defend.
- **Murphy (quality)** + **Fallacies of Distributed Computing (architecture)** — production failure across the wire.
- **Pareto (decision)** + **Amdahl (scale)** — performance tuning where 20% of code is 80% of runtime.
- **Inversion (decision)** + **Hofstadter (time)** — when stuck on an estimate, ask what would guarantee blowing it.

When the situation is broad (e.g. "review this whole project"), route to the
single best-fit lens but **list the composing lenses** in the reply so the
caller can ask to load them next.

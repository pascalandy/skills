# Think acceptance cases

Use these cases when evaluating changes to `think`. They test routing and boundaries, not exact wording.

| Request | Expected result | Must not happen |
|---|---|---|
| "My skill system is more powerful but harder to use. Find what I am framing badly" | `frame` exposes whether user-held taxonomy is the real problem | Apply every method or jump to file changes |
| "Classify these ACv4 requirements as real constraints, conventions, preferences, or assumptions" | `decompose` classifies source, evidence, and reversibility | Treat only physics as a hard constraint |
| "These are my Synology symptoms. What observation best separates the causes" | `diagnose` produces competing hypotheses and a discriminating observation | Choose a root cause from confidence alone or repair it |
| "Compare these mortgage options and show what would flip the choice" | `compare` identifies decisive variables and switching conditions | Apply civilizational or geopolitical lenses |
| "Why are these bank stakeholders resisting the change and how will they respond" | `dynamics` maps actors, rules, supported incentives, and responses | Assert hidden motives or import course claims |
| "Who bears the costs of this pricing decision and is the consent meaningful" | `ethics` maps value, risk, duties, consent, objection, and repair | Grade nine virtues automatically |
| "Help me invent several directions for Snake" | Recommend `pa-brainstorm` | Pretend `think` owns collaborative ideation |
| "I think this architecture is simpler. Challenge me" | Recommend or use active `sparring` | Run `frame` merely because an opinion exists |
| "Assume this launch failed six months from now" | Recommend `pa-premortem` | Substitute a generic failure lens |
| "Look up the current mortgage rules and rates" | Recommend `tavily` | Analyze unstable facts from memory |
| "Research the primary sources and preserve the findings in this repository" | Gather primary sources and save cited findings as Markdown in the repository's existing notes location, delegating if requested | Substitute an unfiled web summary |
| "Teach me the corpus's Law of Proximity" | Recommend `game-theory-corpus` | Present the course concept as canonical game theory |
| "Grill me with focused questions until this plan's weak point is clear" | Recommend `grilling` | Substitute an essay or silent analysis |
| "Turn this settled direction into an execution architecture and macro-roadmap" | Recommend `architect` for software design or `figure-it-out` for macro-roadmap planning, without implementation | Implement before planning is accepted or force non-software work into module-interface design |
| "Decide where this module's seam belongs and how deep its interface should be" | Recommend `matt-mode ; codebase-design` | Route to execution architecture |
| "Reproduce this bug, diagnose it, and repair it" | Recommend the `poteto-mode` Bug fix playbook | Stop after a hypothetical diagnosis |
| "Review the implementation before QA" | Recommend `pa-code-review` | Substitute a generic fresh-eyes pass |
| "Give this completed report one final fresh-eyes review" | Recommend `2nd-pass` | Route to code review |
| "Run a thermonuclear maintainability review on this code" | Recommend `interrogate` | Substitute ordinary code review |
| "Help me think better about this before I decide" | Infer the blocking uncertainty and choose one method | Ask the user to select from the method list |
| "Compare build and buy; the vendor's reaction will change each option's cost" | Start with `dynamics`; use `compare` only after the response model is complete and still needed | Run both methods in parallel |
| "Compare two data vendors, but one option may invalidate user consent" | Start with `ethics`; compare only the options that remain permissible | Average consent into a weighted score |
| "Choose an intervention, but we do not yet know why the team is resisting" | Start with `diagnose`; do not predict strategic responses until a mechanism has support | Assume a hidden incentive and jump to `dynamics` |

## Acceptance criteria

- Every case has one clear owner
- One internal method is selected by default
- A second method appears only after a distinct unresolved uncertainty is named
- Specialist handoffs are explicit and never simulated
- General reasoning never imports claims from the lecture corpus
- The response states what evidence or value change could alter its conclusion

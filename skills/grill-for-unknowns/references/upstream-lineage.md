# Upstream lineage

This local skill derives from Nico Bailon's [`grill-for-unknowns`](https://github.com/nicobailon/grill-for-unknowns). Nico's version adapts three Matt Pocock skills and incorporates the unknowns strategy from Thariq's ["A Field Guide to Fable: Finding Your Unknowns"](https://x.com/trq212/status/2073100352921215386).

## Source skills

- `grill-with-docs`: https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md
  - Minimal composition skill that runs a `/grilling` session while using `/domain-modeling`
  - Its behavior comes from combining the interview with domain-model maintenance
- `grilling`: https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md
  - Interview until shared understanding is reached
  - Work the current frontier of a design tree in rounds
  - Provide a recommended answer for each question
  - Look up facts in the environment while leaving decisions to the user
  - Do not enact the plan until shared understanding is confirmed
- `domain-modeling`: https://github.com/mattpocock/skills/tree/main/skills/engineering/domain-modeling
  - Build and sharpen domain terminology as design proceeds
  - Challenge fuzzy or conflicting language immediately
  - Cross-reference claims against code
  - Update `CONTEXT.md` inline when domain terms crystallize
  - Offer ADRs only for decisions that are hard to reverse, surprising without context, and the result of a real trade-off

## Article strategy being added

Thariq's article frames agentic coding quality as discovering the gap between:

- **Map**: prompt, plan, assumptions, skills, docs snippets, current agent mental model
- **Territory**: real codebase, APIs, product and domain constraints, deployment environment, tests, user taste, reviewer expectations

That gap is classified as:

- Known knowns
- Known unknowns
- Unknown knowns
- Unknown unknowns

The article's concrete tactics are: blindspot passes, brainstorming/prototypes, one-question-at-a-time interviews, references/source code as specs, implementation plans, implementation notes, explainers, and quizzes.

## This adaptation

`grill-for-unknowns` owns the investigation and interview while reusing domain documentation only when requested:

1. Keep the interview bounded to about five material questions
2. Ask dependent questions one at a time and batch up to three independent questions
3. Route explicitly requested domain documentation to the canonical `domain-modeling` procedure inside `matt-mode`
4. Ground factual claims in primary docs, source, and tests before asking the user
5. Use the known and unknown taxonomy as discovery lenses, then store each gap once in a lightweight ledger
6. Treat conflicts between observed and intended behavior as unknowns rather than trusting either automatically
7. Persist terminology and major trade-offs only when the user authorized project writes
8. Stop at a confirmed plan instead of extending the skill into implementation or handoff

The investigation does not require other skills or subagents. Optional documentation uses the `domain-modeling` procedure inside `matt-mode` as the single owner of glossary and ADR rules. Earlier copied rules and templates are preserved in the repository archives.

## Authoring notes for maintainers

Lessons from adapting the upstream skills. These are guidance for future edits to this package, not runtime behavior for the skill itself:

- **Inspect the full upstream composition.** Do not stop at the headline artifact when adapting a skill/article/framework. `grill-with-docs` looked tiny, but its real behavior came from its linked `grilling` + `domain-modeling` skills and their support files.
- **Treat a newly authored skill as a first pass.** Re-read it against the source material and ask what dependency, support file, template, or behavior is missing before calling it done.
- **Preserve attribution and licensing.** Keep this lineage file, its source links, and `LICENSE` when adapting the skill

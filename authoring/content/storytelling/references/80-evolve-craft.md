# Evolve the craft

Use this mode when the user asks to change the skill itself from a source, example,
preference, or observed result, or asks how such evidence could improve the skill.

The result of this mode is one of these decisions:

- sharpen existing guidance
- add a condition, failure mode, surface realization, mechanism combination, medium
  realization, or behavioral test
- add a genuinely missing mechanism or routing rule
- replace or remove guidance that the new evidence exposes as weak
- make no runtime change and explain why

## 1. Establish the learning contract

Follow [source inspection](06-source-analysis.md#1-inspect-the-available-evidence),
then determine the Evolve-specific contract:

- what the user explicitly says they value
- which effects are observable but not yet confirmed as preferences
- the future situations the lesson should improve
- whether the user authorized analysis only or an actual skill update

**Completion criterion**

The available evidence, the stated taste signal, the intended future reach, and the
authorization to edit can each be stated separately.

## 2. Inspect the current behavior selectively

Before editing, locate the repository-managed source of the skill and read its
applicable repository instructions. Do not assume that the loaded or installed copy is
the editable source. If no managed source is available, complete the analysis and name
the missing update target instead of changing an arbitrary copy.

Read only what can already own the lesson:

- [SKILL.md](../SKILL.md) for invocation, mode routing, or invariants
- [the shared narrative model](00-narrative-model.md) for the universal narrative model
- [narrative mechanisms](05-narrative-mechanisms.md) for causal craft
- one relevant operation branch
- one relevant medium reference
- [voice and style](50-voice-style.md) for voice or surface realization
- [truth and ethics](60-truth-and-ethics.md) for factual or lived material
- [behavior tests](../tests/behavior-tests.md) for the existing practice contract
- [evolution tests](../tests/evolution-tests.md) for evolution routing and admission
  behavior

Do not load every reference to prove thoroughness. Search first, then read the smallest
set that can reveal overlap, contradiction, or a missing decision.

**Completion criterion**

Every current rule that may already cover or conflict with the candidate lesson has
one authoritative location in view.

## 3. Analyze the source in three passes

Complete [the three analysis passes](06-source-analysis.md#2-analyze-each-source)
and their completion criterion before classifying candidate lessons below.

## 4. Decide whether the lesson is new

Classify each candidate:

- **Covered**: current guidance already makes the right decision and routes the agent
  to it
- **Latent**: the idea exists, but a weak pointer or missing condition makes it hard to
  reach
- **Extension**: an existing mechanism needs a boundary, realization, diagnostic, or
  combination rule
- **New**: no current concept can own the behavior without distortion
- **Incompatible**: the lesson would violate truth, ethics, author ownership, requested
  scope, or a stronger invariant
- **Source-bound**: the effect depends on unique content or execution and does not yet
  transfer into a useful instruction

Similarity of wording does not prove coverage. Ask whether a future agent would make
the desired decision from the current instruction.

**Completion criterion**

Every candidate has one classification supported by a comparison with current
behavior.

## 5. Pass the admission gate

Admit a lesson to the runtime only when all applicable answers are yes:

- Is the craft evidence observable rather than a style label?
- Is the causal hypothesis plausible after contrast, ablation, and rival explanations?
- Can the lesson transfer without copying the source's identity?
- Does it state when to use the mechanism and when not to use it?
- Will it change a future agent's decision or diagnosis?
- Does the proposed integration create a needed, nonduplicative decision or routing
  improvement?
- Does it preserve stronger truth, ethics, voice, and scope rules?
- Can a behavioral scenario distinguish the improved behavior from the old behavior?
- Is the benefit worth the instructions every affected run must load?

A single source may justify a narrow, conditional improvement. It rarely justifies a
universal law. Record uncertainty in the rule's scope instead of pretending confidence
or refusing all learning.

A **Covered** candidate stops unless a behavioral scenario disproves that
classification. A **Latent** candidate may pass when the missing behavior is the
pointer or condition required to reach guidance that already exists.

Reject identity presets such as "write like this author" as additions to storytelling.
Preserve useful evidence as analysis when appropriate, but do not make its runtime
carry rejected candidates or raw source archives.

**Completion criterion**

Every admitted lesson changes a testable future decision. Every rejected lesson has a
specific failed criterion.

## 6. Choose the narrowest authoritative home

Place the lesson where an agent first needs it:

- invocation, mode selection, or a universal invariant in [SKILL.md](../SKILL.md)
- universal ontology in [the shared narrative model](00-narrative-model.md)
- causal craft in [narrative mechanisms](05-narrative-mechanisms.md)
- operation-specific behavior in the matching branch
- medium-specific realization in one medium reference
- voice dimensions in [voice and style](50-voice-style.md)
- factual limits in [truth and ethics](60-truth-and-ethics.md)
- practice protection against regression in [behavior tests](../tests/behavior-tests.md)
- evolution routing or admission behavior in
  [evolution tests](../tests/evolution-tests.md)

Keep one source of truth. Strengthen or replace an existing rule before adding a nearby
restatement. A new source does not earn a new file, named framework, or mechanism
family by itself.

Treat an accepted taste signal as a conditional capability, not a new default. Change
a stable preference or invariant only when the user explicitly asks for that broader
default and contrast scenarios show where it should stop applying.

Keep raw excerpts, transcripts, screenshots, and rejected candidates outside the
installed runtime. Preserve durable research elsewhere only when the user requests it
or future verification depends on it. Record source and version in the work report or
repository change history when they affect an accepted rule, without copying long
passages.

**Completion criterion**

Each accepted lesson has one smallest authoritative home and a context pointer only
where another branch must reach it.

## 7. Freeze behavior before editing

Define at least one acceptance scenario that would expose the current gap. Include:

- a realistic user request and the minimum source material it needs
- expected mode and reference loads
- the decision or behavior the improved skill must produce
- a tempting but wrong behavior it must avoid

Add a contrast or regression scenario when the lesson could overgeneralize, conflict
with an invariant, or affect another medium or branch.

Do not freeze exact prose. Freeze routing, decisions, constraints, and observable
behavior.

**Completion criterion**

The proposed change can fail the scenario for a meaningful reason, and the scenario
does not require knowledge of the intended implementation.

## 8. Respect mutation authorization

Before editing, apply the authorization recorded in the learning contract:

- For analysis-only work, do not modify files. Use the applicable report fields from
  Step 11, then add the proposed authoritative home, patch shape, and acceptance
  scenarios and stop
- For an authorized update, continue with the integration below

**Completion criterion**

Mutation is explicitly authorized for this request, or the analysis-only proposal has
been delivered without changing files.

## 9. Integrate with a context budget

Make the smallest coherent edit that passes the scenario:

- replace or tighten before appending
- preserve quoted frontmatter and relative links
- keep detailed evolution mechanics in this reference
- keep the runtime mechanism map compact and causal
- update architecture documentation only when the architecture changed
- do not store the source as a runtime example merely to remember it

After editing, compare the added context with the behavior gained. If a rule benefits
one medium or operation, do not make every run pay for it.

**Completion criterion**

The new behavior is reachable, has one owner, and adds no unrelated load to other
branches.

## 10. Validate the integration

Verify:

- the new acceptance scenario
- every relevant contrast and regression scenario
- mode, branch, medium, and reference routing
- frontmatter, relative links, and skill structure
- consistency with truth, ethics, voice, and author ownership
- absence of duplicated rules, creator-named presets, long source excerpts, and stale
  superseded guidance

Use the repository's skill validator when one exists. A structural validator does not
replace behavioral review.

If the change cannot pass without broad or contradictory rules, revert the candidate
lesson rather than weakening the skill's invariants.

**Completion criterion**

The new scenario passes, relevant earlier behavior remains intact, and every modified
instruction earns its context cost.

## 11. Report the learning decision

Tell the user:

- what observable craft produced the valued effect
- which mechanism hypothesis was accepted and with what confidence
- what was changed and where
- which observations were rejected or left source-bound and why
- what scenarios were used to validate the change
- which source limits or open questions remain

Do not claim that the skill learned a creator's complete style. State the narrower
behavior it can now recognize, choose, or avoid.

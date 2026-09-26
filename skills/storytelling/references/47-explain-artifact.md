# Explain a designed artifact: reconstruct from evidence

Use this reference for a designed artifact, project, product, service, architecture,
research artifact, proposal, or operating process whose origin, rationale, behavior,
and value matter to the explanation.

Typical sources include repositories, documentation, architecture decisions, project
pages, research artifacts, demonstrations, interviews, and transcripts.

The artifact is usually not the attention carrier. Follow the person, team, community,
organization, or system that experiences the original situation. The artifact is the
intervention that changes what becomes possible.

This reference governs reconstruction. Do not read
[narrative delivery](48-explain-deliver.md) until the completion gate at the end passes.
For multi-source or continuing work, use the
[project narrative brief](../assets/20-project-narrative-brief.md).

## 1. Scope the source set

Inspect the sources that can establish or change a consequential claim. For a
repository, consider:

- README and project description
- file tree, core modules, tests, and current behavior
- examples, demonstrations, and sample configuration
- documentation and architecture notes
- issues, discussions, and recurring user friction
- changelog, releases, and significant commits
- project website
- creator talks, interviews, or videos
- current limitations and compatibility boundaries

Do not stop at the README when deeper inspection can change the explanation. Do not
inspect unrelated history or code merely because it exists.

Assign each source a role:

- current code, tests, documentation, and releases establish present behavior
- creator material establishes stated intent, origin, and rationale at that time
- issues and discussions reveal reported situations and recurring friction
- history establishes evolution, not a creator's private motivation

Keep dates and versions distinct. An old presentation may support origin and fail to
describe current behavior.

**Completion criterion**

The scoped source set can support or bound every major claim, and each source in it has
been inspected. Every used source has a defined role, date, and version where relevant.
Material omissions and unavailable sources are named.

## 2. Build the claim ledger

Use the basis and status fields defined in the shared narrative model. Record the
source, date, and version for every consequential claim.

Keep four questions separate:

- **Origin**: What caused the work to begin?
- **Problem**: What recurring situation makes it useful?
- **Rationale**: Why was this approach chosen?
- **Value**: What becomes possible or better, and for whom?

A source may answer only one of these questions. Do not turn an inferred problem into
a stated origin, or a plausible benefit into measured impact.

**Completion criterion**

Every major claim about origin, problem, rationale, and value has a basis, status, and
source. Unknowns and contradictions remain visible.

## 3. Define the audience's learning job

Identify:

- who needs to understand the subject
- what they are trying to decide, do, or explain
- what they already know
- what misconception or missing context blocks them
- what depth of technical or causal detail they need
- what they should be able to say or do afterward

Useful shifts include irrelevant to relevant, abstract to concrete, feature-aware to
value-aware, skeptical to able to evaluate, or interested to able to try.

**Completion criterion**

The audience and intended shift determine what belongs in the explanation, the depth
required, and what can be omitted.

## 4. Reconstruct the before-state

Make the situation before the subject legible:

- who was doing what
- the job or goal
- the environment and constraints
- the recurring friction
- the status quo or workaround
- available alternatives
- the cost, risk, delay, confusion, or missed possibility
- why the problem became worth addressing

Do not manufacture dramatic pain. A small repeated friction may be the truthful center
of the story. When evidence is incomplete, state what appears plausible and what the
sources do not establish.

**Completion criterion**

The subject has a source-grounded context that makes its relevance visible without
overstating pain, origin, or impact.

## 5. Identify the project insight

Find the idea that turns the artifact from a feature bundle into a reasoned response:

- what the creator or team came to see differently
- why existing approaches were mismatched
- which constraint shaped the design
- which tradeoff was accepted
- what distinguishes the approach
- what the subject deliberately refuses to do

If no distinctive insight is supported, do not invent one. The story may instead be
about a familiar problem solved with unusual care, accessibility, or fit.

**Completion criterion**

The subject reads as a response to an established situation and set of constraints.
Any inferred insight is marked.

## 6. Build the value bridge

For every important capability, trace:

```text
artifact fact
→ enabled capability
→ changed behavior or workflow
→ supported or plausible outcome
→ value
```

Classify the value at the level where it occurs:

- **User**: effort, understanding, capability, or experience
- **Developer or operational**: feedback, handoffs, errors, maintenance, observability,
  or toil
- **Organizational**: risk, throughput, quality, learning, delivery, or cost
- **Strategic**: optionality, differentiation, portability, or dependency
- **Community**: shared infrastructure, transparency, learning, participation, or
  interoperability

Do not jump directly from a feature to business value. Without adoption, baseline,
measurement, or organizational context, state a potential value pathway rather than a
realized result.

**Completion criterion**

Every value claim has a complete capability-to-value pathway, is assigned the right
level, is qualified by its evidence, and states the conditions required for the value
to occur.

## Completion gate

Reconstruction is sound only when every major claim needed by the audience appears in
the ledger, the four questions remain distinct, the value bridge has no unsupported
jump, and the important unknowns are visible.

If the requested deliverable is a project narrative brief, claim ledger, value
analysis, or set of questions for the creator, produce it and stop. Otherwise, read
[narrative delivery](48-explain-deliver.md).

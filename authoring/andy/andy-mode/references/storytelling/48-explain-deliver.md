# Explain through story: deliver the explanation

Read this reference only after the selected reconstruction reference passes its gate
and the requested deliverable needs a narrative explanation.

## 1. Choose one spine

Select the spine that best serves the audience:

- **Origin**: recurring friction → first attempts → insight → project
- **Before and after**: old way → pressure → intervention → changed way
- **Representative journey**: one user, job, or task reveals the system
- **Decision**: constraints → alternatives → tradeoffs → chosen design
- **Evolution**: early version → feedback → changes → current form
- **Discovery**: confusing domain → useful distinction → new understanding
- **Failure and recovery**: breakdown → investigation → insight → repair
- **Process journey**: starting condition → forces and interactions → transformation →
  resulting state
- **Inquiry**: question → observation → model → changed understanding

Use one primary spine. Supporting facts may branch from it, but the explanation must
not become a feature tour.

**Completion criterion**

The sequence has a clear force of progression and can be summarized without listing
features.

## 2. Reveal subject causality at the point of need

Read [narrative mechanisms](05-narrative-mechanisms.md) when the delivery needs a
deliberate narrative mechanism beyond the subject's causal model. Keep the narrative
mechanism of the telling distinct from the subject causality being explained.

Organize explanation causally:

- context before abstraction
- a concrete situation before the general model
- result before exhaustive implementation detail
- architecture when the audience has a reason to ask how the result is possible
- tradeoffs when the design choice becomes meaningful
- detail proportional to the audience's decision

Keep four explanatory layers distinct:

- **Story** supplies context, pressure, decisions, and change
- **Model** compresses the concepts and subject causal model
- **Demonstration** makes the model concrete and supplies evidence
- **Reference** provides exact commands, interfaces, options, and edge cases

Story supports onboarding and understanding. It does not replace reference material.
Use a real task or workflow to carry a repository walkthrough. Show code only when it
changes the audience's model of how the project works.

**Completion criterion**

The audience receives enough causal depth to trust, evaluate, use, or explain the
subject without losing access to exact reference material.

## 3. Shape the target medium

Load only the target medium reference selected in `playbooks/storytelling.md`. Make demonstrations act
as evidence inside the story rather than as detached showcases.

**Completion criterion**

The delivery uses a capability of its medium and keeps the causal story visible.

## 4. Produce only the requested deliverable

Possible deliverables include a concept explainer, source-grounded narrative,
presentation, README opening, repository overview, creator-video script, demo
narrative, stakeholder briefing, onboarding explanation, or architecture story.

Do not produce adjacent formats unless the user asked for them.

**Completion criterion**

For every subject, the intended audience can answer:

- What is happening or changing?
- Why does it matter in this context?
- How does it work at the needed level?
- Which claims are supported, inferred, or unknown?
- What are the limits of the explanation?

For a designed subject, the audience can also answer why it exists, who it serves, why
this approach was chosen, what changes after use, and what tradeoffs bound its value.

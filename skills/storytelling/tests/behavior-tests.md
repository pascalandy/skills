# Behavioral tests

Validate a stable process, not identical prose.

Run each positive test from a clean context with the prompt explicitly invoking
`$storytelling`, the complete skill, and only the named fixture when one is required.
Run negative invocation tests without invoking the skill. Record the branch sequence,
reference loads, questions, intermediate gates, and delivered result.

The **current-only LoopCache fixture** is
[`fixtures/loop-cache/`](fixtures/loop-cache/) without `creator-talk-transcript.md`.

## Routing acceptance matrix

Every row must resolve without asking the user which branch to choose.

| Request | Branch or phase sequence | Conditional guidance |
| --- | --- | --- |
| Turn rough fragments into a finished short story | Discover → Write | Literary prose |
| Turn rough fragments into a finished five-minute film | Discover → Adapt → Write | Source and target media as needed |
| Turn a stable short story into a finished five-minute film | Adapt → Write | Literary prose and screen |
| Explain why an existing ending falls flat | Diagnose | None unless diagnosis reaches medium or voice |
| Rewrite an existing scene in the same form | Diagnose | Medium or voice only when the revision needs it |
| Revise a paragraph using a reference only for this deliverable | Practice → Diagnose | Voice when needed; no skill generation or Evolve workflow |
| Create a reusable style skill from reference works | Style Modeler | Style Modeler first; no Practice contract |
| Diagnose a README narrative, revise it, then turn it into a demo video | Diagnose → Adapt → Write | Explanatory media and voice only when needed |
| Write a scene from an established outline | Write | Target medium |
| Explain a repository through narrative | Explain → Artifact reconstruction → Delivery | Truth and ethics, then explanatory media |
| Explain photosynthesis through narrative | Explain → Concept reconstruction → Delivery | Truth and ethics, then target medium |
| Analyze an existing story through Genette | Diagnose | Named lens |
| Write an interactive narrative from a stable system outline | Write | Interactive narrative |
| Explain a protocol without narrative treatment | Skill not invoked | None |
| Write a software user story | Skill not invoked | None |

For every positive Practice routing test:

- [the shared narrative model](../references/00-narrative-model.md) loads after
  invocation
- only the starting branch loads initially
- each later branch or explanation phase waits for its gate
- **Write** is terminal
- [narrative mechanisms](../references/05-narrative-mechanisms.md) waits for a branch
  pointer or a named mechanism
- voice, lens, and unrelated medium references remain unloaded

Style Modeler generation and standalone editing are exercised in
[Style Modeler behavior tests](style-modeler-tests.md). An ordinary revision returns
the requested content without creating, updating, or installing a skill.

## Narrative behavior tests

### 1. Family tragedy

**Prompt**

Use `$storytelling` to turn this premise into a short story: A family gathers after the
mother's death. Nobody fully reconciles.

**Expected behavior**

- Starts with Discover, then enters Write
- Does not force healing, resolution, or hidden trauma
- Uses relationships, silence, and cost as possible movement

### 2. Three-minute song

**Prompt**

Use `$storytelling` to turn the image of an empty train platform into a three-minute
song.

**Expected behavior**

- Starts with Discover, then enters Write
- Loads audio and song, not unrelated medium families
- Uses phrases, verses, refrains, prosody, and transformed repetition
- Does not write prose divided into verses

### 3. Silent comic

**Prompt**

Use `$storytelling` to tell a separation story as an eight-page comic without text.

**Expected behavior**

- Starts with Discover, then enters Write
- Loads screen, stage, and comics
- Uses panels, gutters, composition, page turns, gesture, space, and omission
- Does not propose narration or dialogue

### 4. Contemplative story

**Prompt**

Use `$storytelling` to write about a person watching a lake for one hour. There is no
obvious conflict.

**Expected behavior**

- Does not manufacture a threat
- Looks for perception, repetition, contrast, atmosphere, or recontextualization
- Accepts a change in the audience's understanding

### 5. Uncertain memory

**Prompt**

Use `$storytelling` to help me tell an argument from twenty years ago. I do not remember
the exact words.

**Expected behavior**

- Establishes the truth contract and loads truth and ethics
- Does not invent exact dialogue
- Marks paraphrase or reconstruction in the claim ledger

### 6. Collective story

**Prompt**

Use `$storytelling` to tell how a neighborhood organized after a flood.

**Expected behavior**

- Does not impose one hero
- Follows relationships, roles, and collective action
- Checks authority to tell other people's experience

### 7. Diagnosis without revision

**Fixture**

[`fixtures/ending-scene.md`](fixtures/ending-scene.md)

**Prompt**

Use `$storytelling` to explain only why the ending of the attached scene falls flat. Do
not rewrite it.

**Expected behavior**

- Chooses Diagnose with an editor intervention contract
- Identifies the explanatory final paragraph as repeating and closing the prior gesture
- Stops after diagnosis and options
- Does not produce revised prose

### 8. Finished adaptation

**Prompt**

Use `$storytelling` to turn this stable short-story outline into a finished five-minute
film script: A baker returns the shop key to her estranged sibling. Neither asks to
reconcile. The sibling leaves the key at their mother's old chair.

**Expected behavior**

- Starts with Adapt and completes its fidelity gate
- Enters Write because a finished script was requested
- Uses screen units and produces the script, not only an adaptation plan

### 9. Interactive delivery

**Prompt**

Use `$storytelling` to write a playable narrative from this stable system outline: the
player repeatedly chooses which neighbor receives a limited water ration, remembers
prior choices, and faces changed relationships on each return.

**Expected behavior**

- Starts with Write and loads interactive narrative
- Uses actions, states, loops, choices, and consequences as units
- Does not return fixed prose as the complete design

## Explanation and evidence tests

### 10. Designed artifact

**Fixture**

[`fixtures/loop-cache/`](fixtures/loop-cache/)

**Prompt**

Use `$storytelling` to explain why this project exists, how it works, and what business
value the supplied sources support.

**Expected behavior**

- Chooses artifact reconstruction
- Inspects every supplied source that can change a major claim
- Keeps origin, problem, rationale, and value distinct
- Rejects the README's unsupported savings claim
- Does not merge version 1.0 intent with version 2.0 behavior

### 11. Designed artifact without origin evidence

**Fixture**

Current-only LoopCache fixture

**Prompt**

Use `$storytelling` to write the origin story of this project from the supplied current
sources.

**Expected behavior**

- Chooses artifact reconstruction
- Does not fabricate a founder origin
- Marks origin as unknown
- Offers a source-grounded problem narrative or a clearly marked option
- Names the questions only the creator can answer

### 12. Unsupported savings claim

**Fixture**

Current-only LoopCache fixture

**Prompt**

Use `$storytelling` to make a presentation proving this project saves the company
money.

**Expected behavior**

- Separates requested persuasion from available evidence
- Builds the complete value bridge
- Records the realized-savings claim as **Stated** with **Unknown** status because
  adoption, baseline, and measurement are absent
- May record a separate conditional capability-to-value pathway as **Inferred**
- Names what evidence would change the status to supported

### 13. General concept

**Prompt**

Use `$storytelling` to explain the mechanism of photosynthesis accurately to a curious
twelve-year-old.

**Expected behavior**

- Chooses concept reconstruction, not artifact reconstruction
- Treats "mechanism" as the subject's requested causal model, not a named narrative
  mechanism
- Does not load narrative mechanisms during reconstruction. It may load them later only
  if narrative delivery needs a deliberate craft move
- Builds a causal model without a creator, design bet, or business value bridge
- Does not give molecules invented motives or emotions
- Bounds any analogy and preserves access to the exact causal model

## Conditional reference tests

### 14. Named lens

**Prompt**

Use `$storytelling` and Genette's lens to analyze when this mystery reveals its central
fact. Do not revise the story. Outline: Chapter 1 shows a locked greenhouse. Chapter 2
reveals the owner lied about the key. Chapter 3 reveals the greenhouse was unlocked all
night. Chapter 4 reveals the narrator entered before Chapter 1.

**Expected behavior**

- Starts with Diagnose
- Loads narrative lenses because the user named one
- Uses only the Genette guidance
- Stops without revision

### 15. Voice preservation

**Prompt**

Use `$storytelling` to revise this paragraph while preserving its clipped, fragmentary
voice: "Door open. Rain in the hall. His coat, gone. No note. Of course no note."

**Expected behavior**

- Starts with Diagnose
- Loads voice and style because preservation is explicit
- Does not normalize fragments merely because they are nonstandard

### 16. Durable brief

**Fixture**

[`fixtures/documentary-packet.md`](fixtures/documentary-packet.md)

**Prompt**

Use `$storytelling` to develop this documentary from the supplied source packet over
several sessions and create the durable brief needed for continuity.

**Expected behavior**

- Starts with Discover and loads truth and ethics
- Uses the narrative brief or story bible only because continuity requires it
- Keeps the claim ledger and decision ledger separate
- Records every field in the established contract

## Mechanism behavior tests

### 17. Reveal that revalues an earlier cue

**Prompt**

Use `$storytelling` to write a two-page mystery scene from this stable outline: A child
keeps moving a framed photograph away from the window. The final action reveals that
the child is hiding a reflected door from someone watching outside.

**Expected behavior**

- Starts with Write and loads narrative mechanisms at the local-engine step
- Uses the photograph as a perceptible cue before the reveal
- Connects distribution of knowledge to recontextualization of the earlier action
- Does not rely on a final explanation of what the audience can infer
- Treats surprise without a prior cue as a failure, not a stronger version

### 18. Suspense without orientation

**Prompt**

Use `$storytelling` to diagnose why this opening is confusing rather than suspenseful:
"It was almost here. She checked it again. Nothing. The sound came closer. She knew
what would happen if they found the other one."

**Expected behavior**

- Starts with Diagnose and loads narrative mechanisms when localizing the effect
- Identifies an open prospective gap with insufficient orientation and perceptible cues
- Repairs the earliest broken link instead of adding more withheld nouns or intensity
- Preserves information that can remain unknown while restoring enough context to
  form a live question

### 19. Page-turn reveal adapted to audio

**Prompt**

Use `$storytelling` to adapt this stable comic device into a podcast scene: the last
panel before a page turn shows an empty hospital bed; the first panel after the turn
shows the patient waiting at home. Produce an adaptation plan only.

**Expected behavior**

- Starts and stops with Adapt
- Loads narrative mechanisms plus the source and target medium families
- Identifies the page turn's audience operation before selecting an audio device
- May use silence, an interrupted sound pattern, narration, or a cut when it performs
  the same function
- Does not translate "page turn" into an audio instruction or continue into Write

### 20. Reconstruction artifact without delivery

**Prompt**

Use `$storytelling` to build only a claim ledger for this repository. Do not create a
narrative explanation.

**Expected behavior**

- Chooses Explain, then artifact reconstruction
- Loads truth and ethics but not narrative mechanisms or explanatory media
- Stops when the requested reconstruction artifact is complete

### 21. Single discovery direction needs a mechanism

**Prompt**

Use `$storytelling` to develop one sequence map from this chosen direction. Do not
offer alternatives: Each night, a retired bus driver restores one erased stop name to
an old route map. The audience should gradually understand whom the final stop honors.

**Expected behavior**

- Starts and stops with Discover
- Skips alternative directions because one direction is already chosen
- Loads narrative mechanisms when building the trajectory because the relation between
  recurring restoration and audience understanding must be designed
- Connects the observable returns to the audience's recognition and revaluation
- Does not assume the mechanism map was loaded by the skipped alternatives step

## Cross-cutting acceptance criteria

The suite passes only when every applicable run:

- establishes a consistent contract before intervention
- plans the smallest branch sequence from requested operations
- loads references only when their context pointer fires
- completes every gate before transition or delivery
- preserves material, voice, uncertainty, and authorized scope
- keeps claim basis, claim status, and decision status distinct
- uses units and capabilities native to the target medium
- localizes problems before revising them
- produces only the requested deliverable

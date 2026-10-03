# Writing levers

Levers that make any document an agent reads predictable. Each `BP_` section explains one best practice listed in `SKILL.md`.

## Context pointers and the two loads

A **context pointer** is a line in the agent's context that names material outside it and encodes when to reach it: a skill's description, or a line in `AGENTS.md` naming a doc. The pointer's wording, not its target, decides when the agent reaches the material and how reliably. A must-have target behind a weakly worded pointer is a variance bug: sharpen the wording first, and inline the material only if sharpening fails.

A pointer states what the material is and lists the **branches** that should reach it. A branch is a distinct case the document handles, so different runs take different paths through it. Every word of an always-loaded pointer costs on every turn, so prune pointers harder than bodies:

- Front-load the leading word (BP_04): the pointer is where it does its triggering work
- One trigger per branch. Synonyms that rename one branch are one branch written twice
- Cut identity the body already carries

Every document and pointer spends one of two budgets:

- **Context load**: always-loaded material, such as an `AGENTS.md` line or a skill description, spends tokens and attention every turn whether or not it fires
- **Cognitive load**: the human is the index of which documents exist and when to reach for each. It is the price of human agency: spend it where human judgment matters, remove it where it does not

Material behind a pointer costs only the pointer's line. Material with no pointer rides entirely on cognitive load.

## BP_01 Progressive disclosure

A document holds **steps**, the ordered actions the agent performs, and **reference**, the definitions, rules, and facts it consults on demand, in any mix. Place each piece on the **information hierarchy**, ranked by how soon the agent needs it:

1. **In-file step**: what the agent does, in order
2. **In-file reference**: consulted on demand. A flat peer set, such as every rule of a review on one rung, is fine
3. **Disclosed reference**: a separate file behind a pointer, loaded only when the pointer fires

Push too little down and the top bloats; push too much and the agent misses material it needs. Test by branch: inline what every branch needs, and disclose what only some branches reach. Reference that stays inline buries the steps and turns attending to them into a coin flip.

Keep disclosure one level deep: the top file links each reference file directly. A reference file that links to another hides the second behind two pointers.

**Sprawl** is a document simply too long, even when every line is live and unique. Attention thins across the excess. The cure is the ladder: disclose by branch, or split a sequence (BP_10).

## BP_02 One place per meaning

- **Single source of truth (DRY)**: each meaning lives in one place, so changing a behavior is a one-place edit. Duplication costs tokens and maintenance, and inflates a meaning's rank past its real weight
- **Co-location**: a concept's definition, rules, and caveats sit under one heading, so reading one part brings its neighbors. Scattering fragments one meaning across many places
- **The environment is a source too**: `package.json` scripts, config files, the directory layout, and `--help` output. A document that restates them is a **cache** that goes stale. Cache only what looking cannot find: the unwritten convention, the reason behind a choice, the gotcha no config confesses

## BP_03 One term per concept

Choose one term and use it throughout: always "API endpoint", never "URL" or "route" for the same thing; always "field"; always "extract". A second word makes the agent wonder whether a second thing exists.

## BP_04 Leading words

A **leading word** is a compact concept already in the model's pretraining that the agent thinks with: _lesson_, _fog of war_, _tracer bullets_. Repeated as a token, never as a sentence, it anchors a region of behavior in the fewest tokens. A coined word works if you define it, but it recruits no priors, so reach for an existing word first.

It anchors twice. In the body, the agent reaches for the same behavior each time the word appears. In a pointer, the same word in your prompts, docs, and code links that shared language to the material, so the agent reaches it more reliably.

Hunt for passages that collapse into one word:

- "fast, deterministic, low-overhead" becomes _tight_, as in a _tight_ loop
- "a loop you believe in" becomes _red_: the loop goes _red_ on the bug, or it doesn't

BP_03 keeps one word per concept; a leading word picks that word for the priors it brings.

## BP_05 Positive phrasing

A prohibition drags the forbidden behavior into context and makes it more available: _don't think of an elephant_, and the elephant is all there is. State the target behavior, such as "write one-line comments", so the banned one is never spoken. Keep a prohibition only as a hard guardrail you cannot phrase positively, and pair it with the positive target.

## BP_06 Every line relevant

- **Relevance**: a line loses it by never bearing on the task, as exposition or a branch that belongs behind a pointer, or by going stale. Without pruning, the default fate is **sediment**: stale layers that settle because adding feels safe and removing feels risky
- **No-ops**: an instruction the model already follows pays load to say nothing. The test is model-relative, so settle a disagreement by running the document, not by debate. Delete the whole failing sentence rather than trimming words from it
- **Weak words**: a word too weak to beat the default, such as _be thorough_, is a no-op too. The fix is a stronger word, such as _relentless_

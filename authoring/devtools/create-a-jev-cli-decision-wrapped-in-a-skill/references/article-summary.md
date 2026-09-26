# The brief: 168 Hours Since Jev

The full essay lives in [jev skill: Blog post](https://github.com/pascalandy/skills/issues/17). It is the premium design input: the live docs at docs.typesafe.ai settle API facts, the research refines the design, and neither overrides the article's intent. Its benchmark numbers are the author's reports, not verified facts. The article's install sidebar was lost when it was pasted; that gap stays documented and is not reconstructed.

## The operating model

- **An expert system is a knowledge base plus an inference engine.** The author built them from 1979 onward. Their winter was a winter of maintenance, not of the idea: rules were brittle and knowledge engineers were expensive.
- **Jev takes the novelist out of the inference engine.** Chat models write; Jev decides. You send state and typed questions, and every answer comes back at once with a probability, in 70 to 500 ms, for $0.042 per million input tokens. Output is free.
- **Three primitives are the whole instruction set.** Choice picks one of up to 255 options, Score places the state on an ordered rubric, and Noul says how likely a statement is true.
- **State in, decision out, act or escalate.** Code collects the state and performs every side effect. The decision is the only model step.
- **Calibration puts the model in the hot path.** "Act above 0.92, escalate between 0.6 and 0.92, refuse below": certainty factors came back.
- **The failure mode is bounded.** Jev cannot invent a fourth option or a haiku, but it can circle the wrong letter. You still need tests, and you still own the side effects.
- **Tight questions win. Lazy questions lose.** Mush in the state gets a confident shrug toward the least-mushy option. The knowledge engineer is not dead; they got a millisecond inference engine.
- **Guardrails belong in primitives.** Prompt-injection checks, "does this chunk support the claim?", and "is the agent done?" are Nouls, not paragraphs in a system prompt.
- **The LLM only gets the cases that survive the gate.** System Two models are summoned rarely, on purpose, with a budget.
- **The night shift.** At this price, a decision on every file, event, or record becomes routine, and a person is involved only when confidence drops.

## How this skill answers it

| The article says | The design answers |
| --- | --- |
| An expert system is a knowledge base plus an inference engine | Packs and project rules are the knowledge base. Jev is the inference engine. `jevgate` owns every side effect in code |
| "State in, decision out, act or escalate" | Code collects the state, Jev answers typed questions, and one verdict rule in code picks the outcome |
| "Act above 0.92, escalate between 0.6 and 0.92, refuse below" | Every question declares three bands. The article's numbers show the shape; the pilot's labeled cases tune the values |
| "Tight questions win. Lazy questions lose." | Many narrow questions per group, designed with `typesafe-ai` and reviewed against the principles checklist |
| Guardrails as Noul | `steering_attempt` and `claim_supported` in `merge` |
| "The LLM only gets the cases that survive the gate" | `escalate` names the review to run, so System Two is summoned rarely and on purpose |
| Jev can still circle the wrong letter | Advisory throughout v1; only deterministic preconditions block |

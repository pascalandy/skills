---
name: "automate-me"
description: "Use when the user wants their recurring working preferences captured or updated in a personal `-mode` skill. Do not use for a single task-specific workflow."
kind: "dev"
---

# Automate me

Read [the agent runtime contract](../poteto-mode/references/agent-runtime.md) before using runtime tools, loading related skills, or delegating. Use only capabilities and model IDs verified in this session.

A guided flow for turning the user's working conventions into a skill agents will follow. The output is one `-mode` skill tailored to them (e.g. `jay-mode`, `priya-mode`).

This skill combines an inline mining pass (see step 1), `writing-great-skills` for authoring, and the **unslop** skill for prose discipline. It sequences them and retains the preference-mining contract.

## Flow

### 0. Check for an existing skill

Search the repository's existing skill source and runtime-discovered skill directories for a matching `*-mode/SKILL.md`. Preserve its source and category. If one exists and the user has not specified update versus replacement, ask which outcome they want using an available question tool or plain chat.

- Update the existing skill (default for repeat runs)
- Start fresh (rare, ask why before doing it)

Update mode changes the rest of the flow:
- Step 1 mines only history since the skill was last edited (`git log -1 --format=%cI <path>`).
- Step 2 asks what's changed or missing, not what to capture from zero.
- Step 4 edits the existing file in place. Preserve sections the user hasn't contradicted. Revise ones with new evidence. Add new sections only for genuinely new rules.

### 1. Mine their history

Discover authorized workspace history or an explicit export using the runtime contract. If unavailable, use the visible session and the interview below, and report that history mining was incomplete.

Survey recent agent conversations within that scope for recurring patterns. Run multiple parallel subagents using the `Researcher` role across slices of history (e.g. last 2-4 weeks, split into 3 slices so each has enough material). Each slice mining subagent reads transcripts from the workspace-scoped path the parent provides, looks for the signals below, and returns a short structured list of patterns it saw with evidence pointers. Default signals worth hunting:

- Response preferences (length, tone, format, "dumb it down" corrections)
- Delegation habits (subagents, models, specialized workflows, parallelism)
- Verification posture (what "done" means, unit tests vs live repro, reviewers)
- Code and prose discipline (style, principles cited, lint/format tools)
- Process conventions (worktrees, commits, PRs, review/merge tooling)
- Meta preferences (fixing skills mid-task, proposing new ones)

Cross-check across slices before elevating a signal. Patterns seen in 2+ slices are high-confidence. Lone signals are weak and usually get dropped.

### 2. Ask the user directly

Mining misses intent that has not come up yet. Use an available structured question tool when suitable, respecting its actual schema and availability; otherwise ask in plain chat. Ask one or two focused questions about missing preferences. Offer concrete choices when they help, then leave room for an unlisted preference.

Don't dump 20 questions.

### 3. Cluster findings

Group the combined signals into sections. Common ones (use only what applies):

- **Response style**: length, tone, format.
- **Autonomy**: how much to do without asking, MCP tool use.
- **Understand first**: which skills to reach for when scoping or investigating a change.
- **Subagents**: default, parallelism, model-to-task, specialized workflows.
- **Prose / code discipline**: principles, lint tools, style guides.
- **Review and verify**: repro posture, verification skills, live-testing tools.
- **Process**: git worktrees, commits, PRs, review/merge tooling.
- **Skills**: skill-authoring habits, fix-the-skill-first, proposing new skills.

The **poteto-mode** skill shows the shape. Read it for granularity. Don't copy its content. The user's rules are not the same as poteto-mode's.

### 4. Draft the skill

Resolve and load `writing-great-skills` through the runtime contract. If the authority cannot be resolved, report the missing dependency and stop before drafting. Apply its authoring decisions while preserving these domain-specific placement requirements:

- Preserve an existing skill's source directory and category. For a new skill, use the repository's established source or a runtime-discovered install directory. A portable `.agents/skills/<handle>-mode/` source is also possible, but verify discovery or document explicit loading for each runtime
- Handle: the user's first name or chosen identifier.
- Frontmatter `description`: trigger on their name + `/<handle>-mode` + "work in their style", not on generic keywords like "write code" or "review PR".
- Frontmatter formatting: quote every string scalar and keep `description` on one line.
- Keep the mode skill available for agent invocation, with a precise trigger on the person's name or mode handle. Use supported persistent instructions if the user wants the mode loaded every turn.

### 5. Iterate on prose

Apply the **unslop** skill and `writing-great-skills` to every line.

Show the draft to the user and take feedback. Expect multiple iterations. Cut ruthlessly. A mode skill is not a manual.

### 6. Land it

Follow repository policy for placement, verification, and delivery. Create branches, commits, or PRs only within the authorized workflow.

## Guardrails

- **Don't overfit to one conversation.** A preference stated once and contradicted another time is noise. Require multiple instances before codifying it.
- **Don't be clever.** Restating other skills' contents, inventing metaphors, or writing "poetic" prose for an agent reader is cost without benefit. Keep it operational.
- **Reference, don't inline.** Other skills the user relies on should appear as path references, not pasted excerpts. Same for any principle docs they maintain elsewhere.
- **Keep sections minimal.** Only add a section if the user has a specific, non-default rule there. "Communicate clearly" is not a section. "Short paragraphs. Tables when comparing options. Bullets only when items are genuinely parallel." is.
- **Name conventions generic.** Use "the user" or "the human" in imperatives, not the author's first name.
- **Don't force symmetry.** If a user has no process rules worth writing down, skip the Process section entirely.

## Evaluation

A `-mode` skill is subjective output. A generic skill benchmark loop isn't useful here. Vibe-check with the user: does it read like them? Did it miss anything? Then ship.

Run a description-optimization loop only if the skill's trigger accuracy turns out to be a problem in practice.

## When not to use

- User wants a task-specific skill (not working conventions): route directly to `writing-great-skills`, with no preference mining.
- User wants to capture one narrow workflow (e.g. "how I write commit messages"). That's a regular skill, not a mode skill.

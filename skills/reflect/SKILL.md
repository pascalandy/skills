---
name: "reflect"
description: "Use when the user invokes `reflect`."
---

# Reflect

Read [the agent runtime contract](../poteto-mode/references/agent-runtime.md) before using runtime tools, loading related skills, or delegating. Use only capabilities and model IDs verified in this session.

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

Discover the active conversation through the runtime's authorized history API, workspace-scoped session files, or an explicit export, following the runtime contract. Confirm session identity and workspace before reading. If none is available, pass a digest of the visible session and label the missing history as an evidence gap. Do not assume a transcript schema or search unrelated conversations.

### 2. Spawn three reviewers in parallel

Launch three independent reviewers concurrently with read-only scope and access to the referenced evidence. Verify connector access per worker; the parent can fetch citations a worker cannot access.

| Lens | Model role | Prompt template |
|---|---|---|
| Judgment | `Reviewer` | `references/judgment-reviewer.md` |
| Tooling | `Worker` | `references/tooling-reviewer.md` |
| Divergent | `Reviewer` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings through the runtime's result channel.

### 3. Synthesize

Launch a read-only synthesizer using the `Reviewer` role. Use `references/synthesizer.md` verbatim with all reviewer findings. Give it access to citations or verified excerpts. It returns an Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

Report backlog items locally. File them to an external tracker only when the user has authorized that action.

Before applying any approved skill edit, resolve and load `writing-great-skills` through the runtime contract. If the authority cannot be resolved, report the missing dependency and leave the edit unapplied.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent applies it under the authority.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): follow the authority's authoring workflow and validate the result.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): follow the authority and validate the trigger wording against representative requests. Use a description-optimization loop only if available.
- `new skill: <kebab-name>`: follow the authority's creation workflow. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.

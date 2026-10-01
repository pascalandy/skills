# Doc Update Session

Explicit entry point: `andy-mode ; docs`.

Use Doc Update for one bounded documentation job after the relevant change, decision, or artifact already exists. For solo work, this may be batched at the end of a session or day instead of after every small change.

## Core Contract

For each documentation update:

1. Confirm the request is a bounded documentation job.
2. Select exactly one primary documentation mode.
3. Build an evidence baseline before drafting.
4. Identify the canonical target and output shape.
5. Update only the documentation needed for the current job.
6. Preserve existing structure, voice, and cross-reference conventions.
7. Verify the update against the evidence and project documentation map.
8. After writing, run the conditional Wiki Map postflight against every changed documentation file.
9. Report the target, evidence, change made or proposed, postflight result, unknowns, and next phase.

## Route

Load `references/docs/ROUTER.md`.

## Use This When

- You need to capture what changed while context is fresh.
- You need to record why something was decided, without running a full retrospective.
- You need current-state documentation for one concrete artifact.

## Internal Modes

| Mode | Owns | Use when |
|---|---|---|
| `ChangeCapture` | Recent change documentation | The anchor is what changed and where that update belongs |
| `RationaleCapture` | Lightweight decision rationale | The durable object is a decision: what was chosen, why it was chosen, and which alternatives were rejected |
| `ArtifactDocumenter` | One current-state artifact | The anchor is one module, page, workflow, board, or note set as it exists now |

## Boundaries

| If the real need is... | Use instead |
|---|---|
| stale-doc review, deduplication, frontmatter, routing, or doc governance | `docs-cleaner` route |
| planning or implementation | `architect`, `figure-it-out`, or a separate `poteto-mode` delivery session |

## Documentation Update Summary

Default to a concise documentation brief that covers:

1. documentation objective
2. primary target
3. evidence used, including git diff, existing docs, relevant postmortem, and `blast-radius` judgment when available
4. key content to capture
5. canonical placement or output shape
6. dependencies and unknowns
7. Wiki Map postflight result when files were changed
8. recommended next step

## Workflow

1. Confirm the request is an in-scope documentation update, not discovery, scoping, implementation, cleanup, or a new postmortem.
2. Load `references/docs/ROUTER.md` and select exactly one primary mode: `ChangeCapture`, `RationaleCapture`, or `ArtifactDocumenter`.
3. Build the evidence baseline before drafting:
   - inspect the target artifact and existing documentation;
   - in a git workspace, run `git status --short`, `git diff --stat`, and the relevant `git diff` for changed paths; include staged diff when staged changes matter;
   - record whether the target is a local filesystem path and, when it is, the bounded documentation or workspace root plus the pre-write paths and ancestor indexes needed to recognize later moves or deletions;
   - check whether a relevant `postmortem-*.md` artifact already exists, especially beside related lifecycle artifacts under the resolved `sdlc-pa` export root; if found, treat it as required context for lessons, rationale, risks, follow-ups, and cross-references.
4. Run the scope gate: if the documentation target, affected surface, blast radius, validation surface, or artifact relevance is unclear, use (and reload) `$blast-radius` first and feed its scope judgment back into this doc update; otherwise continue inline.
5. Run the documentation update loop.
6. Apply or export the final documentation update according to the selected mode.
7. Only after the update passes its own verification, run the Wiki Map prefilter against the exact documentation targets changed in this job:
   - if nothing was written, report `not run: no documentation targets changed`;
   - mark each non-local target `not applicable: no local filesystem Wiki Map surface`; if no local target remains, stop the postflight;
   - for each local target, compare its pre-write and current paths within the bounded root. Inspect the target itself only when it is `INDEX.md`, plus every ancestor `INDEX.md`. An inspected index is a candidate when its frontmatter contains `kind/wiki`, or when its frontmatter contains `schema_version` and either contains `wiki_type: collection` or its directory contains `references/`;
   - mark each local target without a candidate `skipped: no Wiki Map boundary`;
   - if any candidate remains, load `references/docs/WikiMapPostflight.md` for those candidates only. Do not load it earlier.
   This step is complete when every changed target is accounted for and every candidate boundary has a result.
8. Return the evidence used, files changed or proposed, Wiki Map postflight result, unresolved unknowns, and recommended next step.

## Documentation Update Loop

Use this loop for the selected documentation target:

1. **Target:** Choose the canonical documentation target and output shape.
2. **Draft:** Write the smallest update that captures the current change, rationale, or artifact state.
3. **Fit:** Preserve the target's existing structure, voice, headings, links, and metadata conventions.
4. **Ground:** Keep claims tied to collected evidence or explicit assumptions; do not invent context to make the document feel complete.
5. **Polish:** Use (and reload) the `write-with-clarity` route for a light clarity and concision pass without changing documented facts, rationale, scope, or canonical placement.
6. **Verify:** Check that the update is placed correctly, does not duplicate another canonical source, and leaves cross-references consistent.

## Documentation Discipline

Apply these rules while updating docs:

- **Simplicity first:** write the smallest durable update that captures the change, rationale, or artifact state. Do not add speculative sections, future plans, or process ceremony.
- **Surgical changes:** edit only the canonical target and directly affected cross-references. Do not rewrite nearby docs for tone or taste.
- **Surface conflicts, don't average them:** when code, docs, diffs, postmortems, or artifacts disagree, choose the stronger source when clear; otherwise report the candidates and ask before editing.
- **Read before you write:** inspect the target doc, relevant evidence, nearby docs, indexes, links, and conventions before drafting.
- **Proof verifies intent:** documentation claims should tie back to the reason the behavior, decision, or artifact matters, not merely repeat that a file changed.
- **Checkpoint after significant edits:** summarize target, evidence, changes made, links affected, and unresolved unknowns before closing.
- **Match documentation conventions:** preserve headings, frontmatter, wiki links, voice, metadata, and source-of-truth structure unless the task explicitly changes them.
- **Fail loud:** do not present guessed rationale, skipped evidence collection, broken links, stale targets, or ambiguous canonical placement as resolved.

## Placement Rule

Prefer updating an existing canonical document over creating a new one.

When multiple plausible targets exist, compare them by source-of-truth strength, existing ownership, nearby cross-references, and fit with the current documentation map. If the canonical target is still ambiguous, report the candidates and ask before editing.

## Anti-Patterns

Do not:

- turn a bounded documentation update into broad discovery, scoping, implementation, or cleanup
- write a new artifact when an existing canonical target should be updated
- document guesses, inferred intent, or likely future work as fact
- duplicate content that belongs in another canonical source
- rewrite structure or voice merely to make the target look cleaner
- bury durable implementation knowledge only in chat when it belongs in docs
- skip evidence collection because the change seems obvious
- create a lifecycle artifact merely to prove documentation work happened

## Export

Default behavior: update the canonical documentation target.

Do not create a new lifecycle artifact by default. Read [the shared export protocol](../references/docs/export-artifacts.md) only when the user explicitly asks for a separate documentation-update artifact.

## Shared artifact references

Other skills may read `references/docs/export-artifacts.md` directly for export paths and artifact profiles, or `references/docs/eval-rubric.md` for an explicitly requested scored evaluation. Resolve both from this skill's directory. Reading these references does not invoke the documentation-update workflow or authorize additional writes. Each caller keeps its own scope, execution method, and export trigger.

## Session Loop

After each bounded documentation update, share the documentation update summary and continue with the user's next documentation target, scope handoff, cleanup handoff, or stop signal.

## Non-Goals

Doc Update does not own discovery, scoping, product definition, technical planning, implementation, or documentation maintenance.

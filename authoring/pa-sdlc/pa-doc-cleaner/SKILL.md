---
name: "pa-doc-cleaner"
description: "Use only when explicitly invoked as `pa-doc-cleaner` for maintenance of existing documentation. For documenting a new change or decision, use `pa-doc-update`."
kind: "dev"
keywords: ["pa-doc-cleaner", "doc-cleaner", "drift-refresh", "consolidation", "structure-governance", "frontmatter", "routing"]
---

# Doc Cleaner

Explicit entry point: `pa-doc-cleaner`.

Use Doc Cleaner when the documentation system already exists and the job is maintenance. The work is to make existing documentation more accurate, canonical, navigable, and less redundant — not to invent new product direction, implementation plans, or fresh documentation from scratch.

## Core Contract

For each documentation cleanup request:

1. Confirm the cleanup objective and documentation surface.
2. Route to one primary maintenance mode.
3. Identify the current source of truth before editing or recommending deletion.
4. Classify findings as keep, update, consolidate, move, cross-link, or remove.
5. Apply only bounded maintenance changes that preserve canonical knowledge.
6. Verify navigation, frontmatter, routing, links, and affected references when relevant.
7. Report what changed, evidence used, unresolved risks, and the recommended next step.

## Route

Load `references/ROUTER.md`.

Choose one primary mode as part of the maintenance workflow. Use multiple modes only when the evidence shows the request genuinely combines drift, duplication, and structure concerns.

## Use This When

- You need to check whether docs still match reality.
- You need to merge overlap, condense repetition, or prune dead knowledge.
- You need to repair frontmatter, indexes, routing, taxonomy, or cross-references.
- You need to identify canonical placement for existing knowledge already present in the docs.

## Internal Modes

Use this table for step 2 of the maintenance workflow. Choose one primary mode based on the cleanup objective; add a secondary mode only when evidence genuinely combines concerns.

| Mode | Owns | Use when |
|---|---|---|
| `DriftRefresh` | Reality-vs-doc review | You need keep, update, replace, consolidate, or remove judgments |
| `ConsolidationPass` | Redundancy reduction | Canonical truth is already clear and the main job is cleanup |
| `StructureGovernance` | Structural doc hygiene | Metadata, indexes, routing, taxonomy, or navigation are broken |

## Boundaries

| If the real need is... | Use instead |
|---|---|
| documenting one concrete change, decision, or artifact | `pa-doc-update` |
| bounded current-state evidence before scoping | `pa-scope` |
| scoping a requested change | `pa-scope` |
| defining direction or planning execution | `pa-vision` or `architect` |
| applying a change or fixing a bug | a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook |
| creating a glossary or resolving canonical terminology | `pa-glossary` |
| capturing lessons, incidents, or retrospective feedback | `pa-postmortem` |

## Maintenance Workflow

1. Restate the maintenance objective and target documentation surface.
2. Load `references/ROUTER.md`, classify the request, and choose one primary mode from `Internal Modes`.
3. State the selected mode before planning edits; if using a secondary mode, name why the cleanup genuinely combines concerns.
4. Discover existing documentation structure before editing:
   - index or map files
   - frontmatter conventions
   - existing cross-references
   - nearby canonical pages
   - project instructions for docs, if present
   When `StructureGovernance` is selected, inspect the target's owning `INDEX.md` and ancestor indexes within the authorized documentation root. If their frontmatter identifies Wiki Map through `kind/wiki` or `schema_version` with a `wiki_type`, read `references/WikiMapStructure.md` before planning repairs. Ordinary documentation keeps the generic maintenance path.
5. Establish the source-of-truth baseline:
   - compare docs against current code, config, artifacts, decisions, or user-provided evidence when drift is claimed;
   - identify which page is canonical before merging duplicated content;
   - distinguish stale content from merely old but still valid content.
6. Make a bounded cleanup plan: classify each affected item as keep, update, consolidate, move, link, or remove.
7. Apply the smallest safe cleanup that satisfies the request.
8. Preserve useful language, examples, decisions, and domain terms unless they are wrong, duplicated, or misplaced.
9. Verify affected links, frontmatter, indexes, routing, and references when relevant.
10. Return the cleanup summary, changed files, evidence used, unresolved unknowns, and recommended next step.

## Cleanup Assessment

Before applying or recommending cleanup, decide whether the request is safe to complete in this skill.

### Continue in `pa-doc-cleaner` when

- the canonical source of truth is identifiable
- the task is bounded to existing documentation maintenance
- duplicate or stale content can be resolved without inventing new facts
- structural fixes preserve the existing documentation system's conventions
- removals are evidence-backed or reversible

### Hand off when

- fresh documentation needs to be authored from a completed change, decision, or artifact → `pa-doc-update`
- the current state or affected surface is unclear → `pa-scope`
- product direction, architecture, or implementation plan is unresolved → `pa-vision`, `architect`, or `figure-it-out`
- terminology ownership or canonical vocabulary is unclear → `pa-glossary`
- the cleanup reveals lessons, incident causes, or retrospective feedback → `pa-postmortem`

## Maintenance Discipline

Apply these rules while cleaning documentation:

- **Simplicity first:** make the smallest cleanup that restores accuracy, canonical placement, and navigation. Do not redesign the documentation system unless that is the explicit task.
- **Surgical changes:** touch only the target surface, affected links, indexes, routing, and directly duplicated or stale material.
- **Surface conflicts, don't average them:** identify the canonical source before merging or deleting. If two sources conflict and authority is unclear, preserve the conflict and ask instead of blending them.
- **Read before you edit or remove:** inspect maps, frontmatter, links, backlinks, nearby canonical pages, and current reality before changing or pruning content.
- **Proof verifies intent:** cleanup validation should prove the maintenance goal: drift resolved, duplicate consolidated, route repaired, or link/path fixed.
- **Checkpoint after significant classifications:** before applying edits, restate keep / update / consolidate / move / link / remove decisions and any risky assumptions.
- **Match documentation conventions:** preserve existing voice, taxonomy, metadata, naming, and link style unless the cleanup objective explicitly changes them.
- **Fail loud:** do not silently delete uncertain material, hide ambiguous authority, or claim navigation is fixed when links, indexes, or routing were not checked.

## Default Output

Default to a maintenance brief that covers:

1. maintenance objective
2. primary documentation surface
3. maintenance mode used
4. evidence reviewed
5. findings and classifications
6. actions applied or recommended
7. structural or cross-reference effects
8. risks, unknowns, or deferred items
9. recommended next step

## Export

Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its `pa-doc-cleaner` export profile.

- No new lifecycle artifact by default; this skill repairs existing documentation structure.
- Export only if the user explicitly wants a separate lifecycle artifact about the documentation cleanup itself.

## Anti-Patterns

Do not:

- merge documents before identifying the canonical source of truth
- delete stale-looking content without evidence that it is wrong, duplicated, superseded, or intentionally retired
- rewrite voice, style, or structure merely for preference when the existing convention is clear
- turn cleanup into fresh documentation authoring; use (and reload) `$pa-doc-update` instead
- collapse distinct concepts into one page just because wording overlaps
- preserve duplicated content in multiple places without a clear reason and cross-reference strategy
- break existing frontmatter, indexes, routing, anchors, backlinks, or wiki-style links
- hide uncertainty behind confident cleanup decisions
- use cleanup as an excuse to expand product scope, architecture, implementation, or retrospective analysis

## Session Loop

After each cleanup pass, share the maintenance brief and continue with the user's next documentation surface, doc-update handoff, scope question, or stop signal.

## Non-Goals

Doc Cleaner does not own fresh documentation authoring, discovery, scoping, product definition, technical planning, implementation, or retrospective lesson capture.

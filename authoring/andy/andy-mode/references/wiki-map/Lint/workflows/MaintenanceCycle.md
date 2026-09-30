# MaintenanceCycle Workflow

Run a wiki maintenance pass that turns health findings into a triaged repair plan. This workflow orchestrates existing wiki-map capabilities; it does not replace FullSweep, RecursiveUpdate, CompileWiki, Ingest, or Delete.

## When to Use

- periodic wiki maintenance pass
- user says "maintain wiki", "wiki maintenance", "maintenance cycle", "triage fixes", or "living wiki maintenance"
- user wants a repair plan for known wiki decay, not just a targeted diagnosis
- after a FullSweep when the user wants help deciding what to fix next

## Not for

- pure diagnosis only -> use `FullSweep.md` or `QuickCheck.md`
- targeted stale/outdated/freshness checks -> use `QuickCheck.md`
- nested index rebuild only -> use `RecursiveUpdate.md`
- creating missing entity pages -> use `../../Compile/workflows/CompileWiki.md`
- ingesting new external sources -> use `../../Ingest/workflows/IngestSingle.md` or `../../Ingest/workflows/IngestBatch.md`
- deleting pages -> use `../../Ingest/workflows/Delete.md`

## Core Rule

Maintenance is diagnosis plus triage plus a safe repair plan.

Do not silently rewrite truth claims. Contradictions, stale-content judgments, provenance replacements, merges, and deletions require explicit user direction.

## Steps

### 1. Orientation

- read `../../SCHEMA.md`
- follow the shared Session orientation protocol
- apply Collection routing and include every selected child boundary in the maintenance scope
- report concrete INDEX/filesystem drift without normalizing it
- if `references/_meta/topic-map.md` exists, read it when INDEX scale or topic coverage is relevant
- if the user explicitly asks about terminology drift or naming ambiguity, read `references/_meta/ubiquitous-language.md` when it exists; if it does not exist, report that terminology drift cannot be checked yet and recommend `../../Query/workflows/AddDDDGlossary.md`

Emit:

```text
Oriented: {wiki-name} | schema {version} | {content|collection} | {N} indexed pages | {drift status}
```

### 2. Run Maintenance Checks

Run the FullSweep check matrix from `FullSweep.md` Step 2, focused on living-wiki decay and repair planning.

Also check for terminology drift only when the user explicitly requested a glossary/terminology check and `references/_meta/ubiquitous-language.md` exists.

Closed pages follow the same inclusion and exclusion rules as FullSweep.

### 3. Classify Findings

Group every finding into exactly one action bucket. Within each bucket, order findings using the severity ordering in `../MetaSkill.md`.

| Bucket | Meaning |
|---|---|
| Safe fixes | Low-risk mechanical changes such as INDEX drift, safe tag-order correction, or adding obvious missing `## Related` links |
| Needs user decision | Contradictions, stale claims, merge/delete choices, page closure, root document role overlaps, or terminology policy decisions |
| Needs source review | Claims that require checking the cited source or a newer source before changing content |
| Schema upgrade candidates | Older schema or recognized legacy operational logs that require UpgradeSchema approval |
| Normalization candidates | Strong collection candidates that require NormalizeWikiMap approval |
| Compile candidates | Repeated entities/concepts that may deserve first-class pages via CompileWiki |
| Recursive update candidates | Nested wiki route or local INDEX refresh work suited to RecursiveUpdate |
| Ingest candidates | New or existing source material that should be processed through Ingest |
| Delete candidates | Pages that appear wrong, duplicate, or off-scope but require Delete workflow confirmation |
| No action / info | Observations that do not require immediate work |

### 4. Present Maintenance Plan

```markdown
## Maintenance Plan: {wiki name}

**Health summary:** {critical} critical | {warnings} warnings | {info} info

### Safe Fixes
1. {fix} — files touched: {list}

### Needs User Decision
1. {decision} — options: {options}

### Needs Source Review
1. {claim/source issue}

### Recommended Follow-Ups
1. `CompileWiki` — {reason}
2. `RecursiveUpdate` — {reason}
3. `UpgradeSchema` / `NormalizeWikiMap` — {reason}
4. `IngestSingle` / `IngestBatch` — {reason}
5. `Delete` — {reason}

Proceed with safe fixes only?
```

In interactive mode, wait for confirmation before applying safe fixes.

In automated mode, do not apply safe fixes unless the request explicitly authorized automated repairs. Still honor the 10-page mass-update gate from `../../SCHEMA.md`.

### 5. Apply Safe Fixes Only

Allowed safe fixes include:

- correcting INDEX entries for files that clearly exist or no longer exist
- refreshing direct child wiki route descriptions
- fixing tag axis order without changing tag meaning
- adding obvious missing `## Related` links when the relationship is already explicit in the page
- updating `date_updated` on files actually modified

Do not automatically:

- resolve contradictions
- rewrite stale claims
- infer missing provenance
- merge pages
- delete pages
- split long pages
- create new topic pages
- move or duplicate responsibilities between `AGENTS.md`, `INDEX.md`, and `README.md`
- enforce DDD terminology as a hard rule
- upgrade schema or remove legacy operational logs
- move child wikis or change `wiki_type`

If safe fixes would touch 10 or more pages, stop after the plan and ask for confirmation. In automated mode, halt without writing.

### 6. Verify and report

Re-read every modified page and index. Compare the approved safe-fix plan with the filesystem, and report any mismatch before suggesting a follow-up.

```markdown
## Maintenance Cycle Complete

**Safe fixes applied:** {count}
**Decisions still needed:** {count}
**Source reviews needed:** {count}
**Recommended follow-ups:** {list}
**Post-fix verification:** {passed|failed with first mismatch}
```

End with the next most useful action, not a long menu.

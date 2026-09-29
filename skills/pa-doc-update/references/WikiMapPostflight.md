# Wiki Map postflight

Run this branch only after `pa-doc-update` has written local documentation, passed its own verification, and detected a Wiki Map candidate. It checks the structure around the completed update without influencing drafting or widening the documentation job.

## 1. Freeze the change set

Receive every documentation file created, modified, moved, or deleted by the current job, its old and new paths, the bounded search root, and the candidate boundaries found by the prefilter. Use the pre-write evidence and the resulting diff to distinguish current changes from existing drift.

Keep a cumulative touched set. It includes files changed by the original update and any later postflight repair.

## 2. Detect Wiki Map boundaries cheaply

For each old and new path, include the path itself when it is `INDEX.md`, then walk upward in its matching pre-write or current tree and select the nearest `INDEX.md` that has a strong Wiki Map signal:

- frontmatter contains the `kind/wiki` tag
- or frontmatter contains `schema_version` and either contains `wiki_type: collection` or belongs to a directory that contains `references/`

Use the captured contents of a moved or deleted `INDEX.md` as a boundary candidate even when that file no longer exists. In a git workspace, use both the pre-write evidence and current worktree rather than assuming `HEAD` equals the start of this job.

Stop at the bounded root captured before writing. If no safe root was captured, report `blocked: boundary search root unresolved` instead of walking farther or guessing.

Group source and destination paths by their nearest boundary. A collection containing a misplaced leaf file is still the relevant boundary for reporting that error. When an `INDEX.md` or child route moved or disappeared, include both its old and new parent boundaries so route removal and addition are checked.

If the deeper comparison disproves every prefilter candidate, report `skipped: no Wiki Map boundary` and stop this branch.

## 3. Load Wiki Map after the documentation update

When the job only edits prose in existing pages and their `date_updated`, adding or removing no wikilink or heading, skip this load; the section 5 rules such a diff touches need no schema.

Use and reload `$wiki-map`, follow the `pa-doc-update postflight` route in its `references/ROUTER.md`, then read its `references/SCHEMA.md` as the conformance contract. This file remains the execution workflow. Do not load a generic Wiki Map sub-skill or operational workflow.

For each detected boundary:

1. Read its `INDEX.md`
2. Classify its schema version and wiki type
3. Resolve the nearest content wiki that owns each changed leaf page
4. Inspect only the files allowed by the scope budget below

Do not treat folder names, project names, or repository-specific paths as routing evidence.

## 4. Apply the scope budget

The postflight may inspect:

- the changed documentation files and their pre-write versions when available
- each owning or containing `INDEX.md`
- a direct parent collection `INDEX.md` only when a child route changed
- exact link targets needed to verify wikilinks added or changed in this job
- the minimum directory inventory needed to compare changed paths with their index entries

Do not scan the full wiki, refresh unrelated indexes, or inspect unrelated pages. Group checks by boundary so `$wiki-map` and its schema load only once.

## 5. Check current-change conformance

For a V3 boundary, verify every applicable rule below:

- a content wiki keeps changed leaf pages under its `references/` tree
- a collection keeps navigation at its root and contains no changed leaf page there
- every changed page has schema-valid frontmatter, tag order, filename, body shape, and provenance
- `date_created` remains unchanged on existing pages and `date_updated` reflects each content change
- each created, moved, renamed, or deleted page has exactly one correct entry or removal in its owning content `INDEX.md`; refresh an existing row only when the page's indexed name, description, or ownership changed
- a collection index lists only direct child wiki routes and routes each changed child once
- wikilinks added or changed by this job resolve within the rules of the owning content wiki
- changed pages still meet their kind's outbound-wikilink minimum and exemptions
- `sources` and `contradictions` changed by this job stay within their owning content wiki and agree with the body
- the diff does not push a page past 200 body lines, an index section past 50 entries, or a content index past 200 entries without applying the schema's required split, report, or approval behavior
- the resulting diff contains no documentation path outside the authorized job

Check only rules affected by the current diff. Record unrelated defects as existing drift rather than expanding the update.

## 6. Correct only direct, deterministic defects

Repair a defect before reporting success only when all of these conditions hold:

- the current documentation job introduced it
- the intended result follows unambiguously from the evidence and Wiki Map schema
- the repair stays within the changed page, its owning index, or a directly affected link
- the repair does not cross an approval gate

Examples include restoring `date_created`, bumping `date_updated`, fixing an index entry created by this job, or repairing a newly added wikilink whose target is certain.

A newly created page at a collection root may move only when the collection index and documentation evidence identify exactly one destination content wiki. Update every link and index entry introduced by the current job as part of that move. If ownership is ambiguous, stop and ask instead of choosing by directory name.

Do not repair existing drift. Report it separately with paths and evidence. Hand broad cleanup to `pa-doc-cleaner` only when the user requests that work.

After any repair, add every newly touched file and path to the cumulative set, resolve its old and new boundaries, and rerun the primary documentation checks plus every affected Wiki Map check. Repeat until the current change is clean or the same finding remains. If a finding repeats, report `blocked` instead of retrying indefinitely. Apply mass-update gates to the cumulative set.

## 7. Preserve approval gates

Never start `UpgradeSchema`, `NormalizeWikiMap`, `FullSweep`, `MaintenanceCycle`, `RecursiveUpdate`, `Compile`, `CompileWiki`, legacy-log cleanup, or a broad index rebuild from this postflight.

If a boundary is unstamped, older than V3, or ambiguous:

- leave its schema and topology unchanged
- report that full V3 validation was unavailable
- name the relevant Wiki Map migration or investigation as separate work
- require explicit approval before any schema upgrade or topology normalization

If repairs would touch 10 or more pages, move pre-existing content across a wiki boundary, alter pre-existing content beyond a directly affected index or link, or require a semantic choice, stop and request approval. The completed documentation edit remains visible, but do not claim the whole job passed while its conformance is unresolved.

## 8. Report deterministic results

Return one status per detected boundary:

- `passed`
- `blocked: current-change conformance unresolved`
- `deferred: legacy or ambiguous boundary`

Record `repaired` and `existing drift reported` as independent flags on each boundary so mixed outcomes remain visible.

Derive one global status in this order:

1. `blocked` if any boundary is blocked
2. `deferred` if none is blocked and any boundary is deferred
3. `passed` if every detected boundary passed

The prefilter owns `skipped`, `not applicable`, and `not run` when no boundary result exists.

Include the changed files checked, boundary types, direct repairs, existing drift, deferred migrations, and any required user decision. Keep this inside the normal `pa-doc-update` summary rather than creating a separate artifact.

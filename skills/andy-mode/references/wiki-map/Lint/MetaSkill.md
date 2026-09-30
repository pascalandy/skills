---
name: "lint"
description: "Health-check and maintain the wiki for contradictions, provenance gaps, cross-link issues, and drift."
---

## Customization

If the current assistant supports user-specific overrides, apply them before execution. Otherwise, use the defaults in this folder.

## Status Update

Before executing, emit a brief text status update such as:
`Running the **WorkflowName** workflow in the **Lint** skill...`

# Lint

Health-check the wiki and surface structural issues that degrade quality over time. Lint validates each discovered wiki boundary against the shared schema, reports findings in severity order, triages maintenance work, and refreshes content wikis and collections bottom-up.

For the full schema, hard rules, and orientation protocol, read `../SCHEMA.md`.

## Core Concept

Wikis decay silently. New sources contradict old claims. Provenance links break. Pages lose cross-references. INDEX drifts away from the filesystem. Lint treats the wiki like a codebase: run checks, report findings, then fix carefully.

## Workflow Routing

- Comprehensive health check -> `workflows/FullSweep.md`
- Check for one issue type -> `workflows/QuickCheck.md`
- Refresh a nested wiki tree bottom-up -> `workflows/RecursiveUpdate.md`
- Run a maintenance pass with triage and safe-fix planning -> `workflows/MaintenanceCycle.md`

## Severity Ordering

Within each severity tier, report issues in this order:

1. broken wikilinks
2. broken `sources:` provenance
3. contradictions
4. orphan pages and orphan webclips
5. missing pages
6. stale content
7. missing cross-references
8. tag and frontmatter issues
9. root document role overlaps
10. thin or long pages

## Principles

1. **Read the whole wiki** -- lint is comprehensive by default
2. **Use the shared schema** -- validate against one canonical rule set
3. **Exclude closed pages where required** -- orphan, stale, and weak-link checks skip them
4. **Report before fixing** -- especially for contradictions and provenance issues
5. **Route by wiki type** -- content children live under `references/`; collection children live directly under the collection root
6. **Preserve nested boundaries** -- only directories with their own `INDEX.md` count as child wikis
7. **Use best-effort recursion** -- continue sibling branches when one nested branch fails and report warnings at the end
8. **Separate diagnosis from maintenance** -- FullSweep reports health; MaintenanceCycle triages findings and plans safe repairs
9. **Never migrate as a safe fix** -- schema upgrades and topology normalization require their dedicated approval gates

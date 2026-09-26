# IngestBatch Workflow

Process multiple sources through one complete plan and one verified write set.

## When to Use

- Adding several sources at once
- Bulk import of webclips, articles, notes, or transcripts
- User says "process these sources", "batch ingest", "ingest all of these"

## Core Rule

This workflow is not sequential per-source ingestion:

1. Read everything
2. Plan everything
3. Apply one write pass
4. Verify the expected final state

## Workflow

### Phase 1. Orientation

1. Read `../../SCHEMA.md`
2. If the wiki exists, follow the shared Session orientation protocol
3. If the requested root is a collection, resolve the destination content wiki for every source before planning writes
4. Halt and offer UpgradeSchema before writing to a pre-V3 wiki
5. If a destination has 100 or more pages, search for the request topic before planning new pages
6. Report concrete INDEX/filesystem drift without normalizing it
7. Inventory the sources to be processed
8. In interactive mode, confirm scope with the user

```markdown
## Batch Ingest Plan

| # | Source | Destination Content Wiki | Status |
|---|---|---|---|
| 1 | {filename or title} | {wiki} | pending |
| 2 | {filename or title} | {wiki} | pending |
| 3 | {filename or title} | {wiki} | pending |

Proceed with batch ingestion?
```

In automated mode, skip the conversational confirmation but still honor the mass-update gate later.

### Phase 2. Read All Sources

1. Read every source file
2. Extract entities, concepts, claims, and relationships from each
3. Build one unified discovery map in memory covering:
   - all entities across all sources
   - all concepts across all sources
   - all cross-source relationships
   - all source pages that must appear in `sources:`

Partition that discovery map by destination content wiki before planning pages. Cross-wiki observations may inform the conversational report, but they do not become unqualified wikilinks or cross-boundary `sources:` entries.

### Phase 3. Plan All Writes

1. Search once for which entities and concepts already exist in the wiki
2. For each destination content wiki, decide independently which entities or concepts to create or update
3. Compute the full final state for every page to update
4. Resolve cross-references at planning time, including links between newly created pages
5. Resolve `sources:` frontmatter at planning time
6. Preserve `date_created` on existing pages and plan `date_created` plus `date_updated` for new pages
7. Plan `contradictions:` frontmatter updates anywhere conflicting claims are introduced
8. Enforce the schema's outbound-link minimums for both content kinds and operational kinds
9. Build one write plan containing:
   - pages to create with final content
   - pages to update with final content
   - one `INDEX.md` patch per destination content wiki
   - an expected-state checklist for post-write verification

Every planned page has exactly one owning content wiki, and every `sources:` entry resolves inside that same wiki. Split a cross-wiki synthesis into child-local pages or block it before the write plan.

### Phase 4. Mass-Update Gate

If total pages touched, created plus updated, is 10 or more:
- stop after planning
- present the full page list
- ask for confirmation in interactive mode

In automated mode:
- halt
- exit without writing page changes

### Phase 5. Write Once

1. Write all create pages
2. Write all update pages
3. Preserve `date_created`, bump `date_updated`, and write planned `contradictions:` updates
4. Update each destination `INDEX.md` once
5. Re-read every planned output and verify files, index membership, provenance, cross-references, and dates against the expected-state checklist
6. Report all changes and verification results in one summary

### Phase 6. Failure Handling

If any write or verification in Phase 5 fails, stop immediately. Compare the approved write plan with the filesystem and each `INDEX.md`, then report completed writes, pending writes, and the first mismatch. Do not guess or continue with later writes.

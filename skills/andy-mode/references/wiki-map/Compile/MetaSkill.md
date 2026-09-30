---
name: "compile"
description: "Promote implied-missing entities inside the wiki into first-class pages from the wiki's own content, under an approval gate."
---

## Status update

Before executing, state that CompileWiki is running

# Compile

Mine existing pages for repeatedly referenced entities that lack their own page, then create approved pages and back-edit siblings

Read `../SCHEMA.md` and `workflows/CompileWiki.md`

## Guardrails

- Compile uses existing wiki content only. External sources belong to Ingest
- Compile operates on one resolved V3 content wiki per pass
- At a collection root, use the collection index to select the destination child
- Compile runs its own structural preflight in the current session
- Compile does not rely on persisted lint reports or operational logs
- Compile does not rebuild routes or change topology

## Principles

1. Run the same-session preflight before mining
2. Mine in batches, then merge and deduplicate candidates
3. Apply the schema's two-source or central-subject threshold
4. Show the complete write plan before writing
5. Honor the mass-update gate
6. Patch INDEX once
7. Verify every planned create, back-edit, provenance link, and INDEX entry

## Subagent dispatch

When the harness supports user-authorized subagent fan-out, batches may be mined in parallel using the fixed worker contract in `workflows/CompileWiki.md`. Otherwise run the same batches sequentially. The output shape must remain identical

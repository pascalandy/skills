---
name: "query"
description: "Search the wiki, synthesize answers with citations, file durable query pages, and optionally create a DDD glossary."
---

## Customization

If the current assistant supports user-specific overrides, apply them before execution. Otherwise, use the defaults in this folder.

## Status Update

Before executing, emit a brief text status update such as:
`Running the **WorkflowName** workflow in the **Query** skill...`

# Query

Search the wiki and synthesize answers from its accumulated knowledge. Query workflows always start from the shared schema and then orient on the specific wiki before reading relevant pages.

For the full schema, hard rules, and orientation protocol, read `../SCHEMA.md`.

## Core Concept

The wiki is a pre-synthesized knowledge base. Query reads structured pages, follows cross-references, traces `sources:` back to source pages when useful, and answers from wiki content rather than from general memory.

## Workflow Routing

- Find relevant pages for a topic -> `workflows/Search.md`
- Synthesize an answer across multiple pages -> `workflows/DeepQuery.md`
- Save an answer back into the wiki as a new page -> `workflows/FileAnswer.md`
- Create or update an explicit DDD-style domain glossary -> `workflows/AddDDDGlossary.md`

## Principles

1. **Read SCHEMA first** -- use the canonical conventions
2. **Start from INDEX.md** -- orientation before deep reads
3. **Route collections first** -- use the collection index to select child wikis; never write at a collection root
4. **Qualify cross-boundary citations** -- identify the owning child and detect duplicate basenames
5. **Follow cross-references** -- use body links and `## Related`
6. **Cite everything** -- every answer should point back to wiki pages
7. **Preserve provenance** -- use `sources:` within one content wiki; do not file cross-boundary provenance in V3
8. **File only worthy answers** -- not every lookup should become a page
9. **Keep DDD opt-in** -- create or consult the ubiquitous-language glossary only when explicitly requested or directly relevant

---
name: "ingest"
description: "Organize wiki files, ingest sources, delete pages safely, upgrade schema, and normalize collection topology."
---

## Customization

If the current assistant supports user-specific overrides, apply them before execution. Otherwise, use the defaults in this folder.

## Status Update

Before executing, emit a brief text status update such as:
`Running the **WorkflowName** workflow in the **Ingest** skill...`

# Ingest

Two distinct classes of work live here: **organizing files** and **processing sources**. They have different rules and must not be conflated.

For the full schema, hard rules, and orientation protocol, read `../SCHEMA.md`.

## Critical Guardrail: Organize vs Process

**CreateWikiMap is read-only on file body content.** It moves files, renames them, adds frontmatter when missing, and builds the index. It never rewrites body text, never summarizes, and never adds cross-references to existing text.

**IngestSingle and IngestBatch are synthesis operations.** They read sources, synthesize knowledge, update or create wiki pages, maintain cross-references, and record provenance.

**Delete** removes a page only after inbound-link analysis.

**UpgradeSchema** migrates an older wiki to V3 without changing its topology or rewriting page bodies.

**NormalizeWikiMap** converts an approved V3 wrapper of child wikis into a wiki collection. It never upgrades schema.

## Core Concept

Ingestion is not indexing. The LLM reads a source, synthesizes what matters, writes or updates wiki pages, and records provenance through `sources:` frontmatter. Webclips are source snapshots. Synthesized pages point back to them.

## Workflow Routing

Route to the appropriate workflow based on the request.

- Create a wiki map / organize existing files / new wiki -> `workflows/CreateWikiMap.md`
- Process one source interactively -> `workflows/IngestSingle.md`
- Process multiple sources through one planned write set -> `workflows/IngestBatch.md`
- Delete one page safely -> `workflows/Delete.md`
- Upgrade an older wiki to V3 or clean recognized legacy operational logs -> `workflows/UpgradeSchema.md`
- Convert an approved wrapped-child topology into a wiki collection -> `workflows/NormalizeWikiMap.md`

## Principles

1. **Read SCHEMA first** -- every workflow starts from the canonical schema
2. **Preserve user structure** -- only NormalizeWikiMap may move wiki boundaries, after explicit approval
3. **Update over duplicate** -- prefer extending existing pages
4. **Track provenance** -- synthesized pages record `sources:`
5. **Record contradictions explicitly** -- use frontmatter, not prose only
6. **Respect approval gates** -- schema and topology migrations always require approval; large ordinary writes use the mass-update gate
7. **Use safe deletion** -- inbound-link analysis always precedes removal

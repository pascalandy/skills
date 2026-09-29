---
name: "wiki-map"
description: "Use only when explicitly invoked as `wiki-map`."
---

# Wiki Map

Build and maintain a persistent Markdown knowledge base with explicit provenance, navigable indexes, cross-references, and controlled structural migrations

## Route the request

Read `references/ROUTER.md` and load only the matched branch. An explicit combined schema-plus-topology request loads UpgradeSchema and NormalizeWikiMap in that order

When `pa-doc-update` invokes its bounded postflight, the caller's `WikiMapPostflight.md` remains the workflow. Read `references/SCHEMA.md` and do not load an operational Wiki Map sub-skill

Read `references/SCHEMA.md` whenever the request operates on a wiki. It defines V3, the orientation protocol, approval gates, and both supported wiki types

## V3 model

### Content wiki

A content wiki owns pages under `references/`

```text
wiki/
├── INDEX.md
└── references/
    └── page.md
```

### Wiki collection

A wiki collection owns navigation. Its independent child wikis live directly below it

```text
collection/
├── INDEX.md
├── child-a/
│   ├── INDEX.md
│   └── references/
└── child-b/
    ├── INDEX.md
    └── references/
```

The collection `INDEX.md` tells humans and agents which child to open next. It never catalogs descendant pages

## Operations

### Ingest

- Create a V3 content wiki from existing files
- Ingest one or many sources with provenance
- Delete one page after inbound-link analysis
- Upgrade an older schema to V3
- Normalize an approved wrapped-child topology into a wiki collection

### Query

- Find relevant pages
- Synthesize answers with wiki citations
- File substantial answers back into a content wiki
- Create an optional DDD-style ubiquitous-language glossary

### Lint

- Check INDEX integrity, frontmatter, tags, provenance, links, contradictions, aging, and structure
- Triage maintenance findings
- Refresh content wikis and collections bottom-up

### Compile

- Mine existing wiki pages for repeatedly referenced entities that lack pages
- Run a same-session structural preflight
- Plan all creates and back-edits before one verified write set

## Migration boundaries

`UpgradeSchema` and `NormalizeWikiMap` are independent

- UpgradeSchema changes schema and removes only recognized legacy Wiki Map operational logs
- NormalizeWikiMap changes topology and never upgrades schema
- Either workflow may recommend the other
- Neither workflow writes without explicit approval, including automated runs
- A single approval may cover both only when the plan separates their effects
- For a combined migration, verify UpgradeSchema and revalidate normalization preconditions before NormalizeWikiMap
- A request such as "apply wiki-map" authorizes inspection, not migration

V3 does not create, read, rotate, or append Wiki Map operational `LOG.md` files. User-authored log pages remain ordinary content

## Shared guarantees

- Start from `INDEX.md` and compare it with the filesystem
- At a collection, use the parent index to select relevant children
- Resolve a destination content wiki before writing a page
- Preserve user structure unless NormalizeWikiMap was approved
- Prefer updating an existing page over creating a duplicate
- Preserve source material and record provenance through `sources:`
- Report contradictions instead of silently replacing claims
- Plan before multi-file writes and verify expected state afterward
- Stop for approval before any schema change, topology change, or 10-page mass update
- Keep behavior project-agnostic. Never encode project names, category names, or repository-specific paths

## Included files

| Component | Path |
|---|---|
| AGENTS.md instructions | `references/AGENTS-instructions.md` |
| Router | `references/ROUTER.md` |
| Schema | `references/SCHEMA.md` |
| Ingest | `references/Ingest/MetaSkill.md` |
| Query | `references/Query/MetaSkill.md` |
| Lint | `references/Lint/MetaSkill.md` |
| Compile | `references/Compile/MetaSkill.md` |

The skill contains four sub-skills and fifteen workflows. Keep shared rules in `SCHEMA.md`; workflow files should state only their branch-specific decisions

## Typical requests

| Request | Workflow |
|---|---|
| "create a wiki map" | CreateWikiMap |
| "ingest these sources" | IngestSingle or IngestBatch |
| "upgrade this wiki to V3" | UpgradeSchema |
| "convert this wrapper into a wiki collection" | NormalizeWikiMap |
| "what does the wiki say about X?" | Search or DeepQuery |
| "health check the wiki" | FullSweep |
| "refresh the wiki tree" | RecursiveUpdate |
| "compile the wiki" | CompileWiki |

When "wiki-map update" is the entire request, orient read-only and ask which operation the user wants. Report migration opportunities, but never perform them implicitly

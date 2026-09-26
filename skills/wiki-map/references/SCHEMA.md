# Wiki schema

> The single source of truth for wiki conventions. All workflows reference this file. There is no per-wiki `SCHEMA.md`

## Wiki types

Schema V3 supports two shapes

### Content wiki

A content wiki owns pages. Its content stays under `references/`

```text
{wiki-name}/
  INDEX.md
  AGENTS.md                  # Optional agent instructions
  README.md                  # Optional end-user introduction
  references/
    {page}.md
    {child-wiki}/            # Optional nested wiki boundary
      INDEX.md
      references/
        {child-page}.md
    {plain-subdir}/          # Preserved ordinary directory
    _meta/
      topic-map.md
      ubiquitous-language.md
  assets/                    # Optional non-markdown files
```

Rules

- `wiki_type` is omitted for a content wiki
- All wiki content lives under `references/`
- A directory is a child wiki boundary only when it contains its own `INDEX.md`
- Child wiki routes point to `references/{child}/INDEX.md`
- Plain directories without `INDEX.md` remain ordinary content directories
- Preserve user-managed subdirectories and existing child boundaries
- Preserve optional `AGENTS.md` and `README.md` at the wiki root and do not index them as wiki content
- Never flatten or create child wiki boundaries during ordinary maintenance

### Wiki collection

A wiki collection owns navigation, not pages. Its direct children are independent wikis

```text
{collection-name}/
  INDEX.md                   # Collection router
  AGENTS.md                  # Optional agent instructions
  README.md                  # Optional end-user introduction
  {child-wiki}/
    INDEX.md
    references/              # When the child is a content wiki
  {child-collection}/
    INDEX.md
    {grandchild-wiki}/       # When the child is another collection
  assets/                    # Optional non-markdown files
```

Rules

- `INDEX.md` frontmatter must contain `wiki_type: collection`
- A collection has no local wiki pages and does not require `references/`
- Every direct child route points to `{child}/INDEX.md`
- Every direct wiki directory must contain `INDEX.md`
- The collection index lists direct children only, never descendant pages
- The index explains what each child owns so a human or agent can choose where to continue
- Optional `AGENTS.md`, `README.md`, `assets/`, and recognized repository control files may remain at the root. They are preserved and not indexed as wiki content
- Any other non-wiki directory or file makes collection classification ambiguous

### Collection routing

When an operation starts at a collection

- Read the collection `INDEX.md` and use its child descriptions as the routing authority
- If a selected child is another collection, repeat routing until reaching the needed content wiki
- Query operations may read one or more relevant child wikis
- Write operations must resolve the destination content wiki before planning writes
- If more than one destination is plausible, ask the user instead of choosing by folder name alone
- Never create a content page or `_meta` artifact at the collection root
- Lint and recursive maintenance traverse direct children and validate each child against its own declared type

## Root document roles

`AGENTS.md` and `README.md` are optional. When present, they stay beside `INDEX.md` at their wiki boundary

- `AGENTS.md` defines how the agent works
- `INDEX.md` is the canonical source for routing the agent
- `README.md` presents the project from the end user's point of view
- Avoid repeating the same information across these files (DRY principle)
- When one file needs context owned by another, link to the owning file or keep only the short pointer needed to route the reader
- Apply this DRY check only across these three root files. Do not deduplicate or rewrite wiki content unless the user explicitly requests that work

## Tag axes

Tag order is always

```text
area/* -> kind/* -> topic/* -> status/* -> pty/*
```

### area/*

- `area/ea` is required on every page

### kind/*

- `kind/task`
- `kind/bug`
- `kind/doc`
- `kind/plan`
- `kind/log`
- `kind/wiki`
- `kind/project`
- `kind/webclip`
- `kind/query`
- `kind/tracking`
- `kind/random`

`kind/log` remains valid for user-authored content. Wiki Map does not create or maintain operational logs

Notes

- `kind/relationship` is deprecated. Use `topic/relationship`
- `kind/query` is reserved for answers filed from Query workflows

### topic/*

- `topic/{name}`
- `topic/milestone`
- `topic/playbook`
- `topic/relationship`
- `topic/strategy`
- `topic/role`
- `topic/template`
- `topic/reference`

`topic/*` is optional. Use it for subject domain, not work type

### status/*

- `status/draft`
- `status/open`
- `status/stable`
- `status/blocked`
- `status/parked`
- `status/close`

### pty/*

- `pty/p1`
- `pty/p2`
- `pty/p3`

`pty/*` is optional and only valid for actionable kinds such as `kind/task`, `kind/bug`, `kind/plan`, and `kind/tracking`

## Page frontmatter

```yaml
---
name: Page Title
description: One-line summary
tags:
  - area/ea
  - kind/project
  - topic/example
  - status/open
  - pty/p2
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
sources:
  - source-page-name
contradictions:
  - conflicting-page-name
---
```

Rules

- Set `date_created` once and never change it
- Bump `date_updated` on every content change
- Within one content wiki, `sources` lists unqualified page names and is required for synthesized `kind/project`, `kind/doc`, and `kind/query` pages
- Do not file one synthesis whose provenance spans multiple content wikis. Cross-boundary source identity is intentionally undefined in V3
- Omit empty `sources` and `contradictions`
- Keep frontmatter `contradictions` synchronized with any body `## Contradictions` section

## Page body

```markdown
Summary paragraph

## Section name

Content

## Related

- [[related-page-one]]
- [[related-page-two]]
```

- Start with a summary paragraph
- Add only useful sections
- End with `## Related` unless the page kind is exempt
- Use Obsidian-style `[[wikilinks]]`

## INDEX.md

### Content wiki frontmatter

```yaml
---
name: Wiki Name
description: One-line description
schema_version: 3
tags:
  - area/ea
  - kind/wiki
  - status/open
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
---
```

### Collection frontmatter

```yaml
---
name: Collection Name
description: One-line routing description
schema_version: 3
wiki_type: collection
tags:
  - area/ea
  - kind/wiki
  - status/open
date_created: YYYY-MM-DD
date_updated: YYYY-MM-DD
---
```

### Content wiki body

```markdown
# Wiki Name

> Content catalog. Read this first to find relevant pages
> **Total pages:** N | **Last updated:** YYYY-MM-DD

## Wiki Map

### kind/project

| File | Description |
|------|-------------|
| `references/page-name.md` | One-line description |

### kind/wiki

| File | Description |
|------|-------------|
| `references/child-wiki/INDEX.md` | Child wiki description |
```

### Collection body

```markdown
# Collection Name

> Wiki collection. Choose a child wiki from this index, then read that child's `INDEX.md`
> **Child wikis:** N | **Last updated:** YYYY-MM-DD

{Short routing guidance that explains what belongs in each child}

## Wiki Map

### kind/wiki

| File | Description |
|------|-------------|
| `child-wiki/INDEX.md` | What this child owns and when to use it |
```

INDEX rules

- `INDEX.md` is the navigational entry point
- Organize content entries into `kind/*` sections
- Closed pages remain listed
- List each direct child wiki once under `kind/wiki`
- Never inline a child wiki's leaf pages into its parent
- Refresh child descriptions from child `INDEX.md` frontmatter, then fall back to the first body paragraph
- In a content wiki, index files in plain subdirectories directly
- In a collection, list only direct child wiki routes
- Split a section over 50 entries by first letter or `topic/*`
- At more than 200 entries, offer `references/_meta/topic-map.md` and ask before overwriting an existing one

## Schema version

The current version is **3**

- `schema_version` lives only in each wiki boundary's `INDEX.md`
- Pages inherit their owning wiki's version
- A wiki is current when its `INDEX.md` contains `schema_version: 3`
- If the field is absent or lower, use `Ingest/workflows/UpgradeSchema.md`
- Every workflow that patches `INDEX.md` preserves `schema_version` and `wiki_type`
- Schema upgrade and topology normalization are independent operations

## Legacy operational logs

V3 has no Wiki Map operational log. Do not create, read, rotate, or append one

A file is a recognized legacy operational log only when every signature element agrees

- Its path is `references/LOG.md` or `references/LOG-YYYY.md`
- Its frontmatter has `name: Log`
- Its description starts with the exact prefix `Append-only operational log for `
- Its tags contain `area/ea`, `kind/log`, and `status/stable`
- Its body starts with `# Log`
- Every remaining nonblank body record follows the historical `- [[YYYY-MM-DD]] action | details` shape

Never treat an arbitrary user-authored `kind/log` page or a file that merely contains `LOG` in its name as a legacy operational log

- `UpgradeSchema` may remove recognized legacy logs only after explicit approval
- UpgradeSchema reads a candidate only to validate this signature and inventories inbound links plus path consumers before deletion
- If any signature element or reference treatment is ambiguous, preserve the file and report it
- Any workflow that finds one reports it and offers the UpgradeSchema cleanup path
- Read-only requests do not authorize cleanup

## Naming

- Filenames use kebab-case such as `vitamin-d-and-sleep.md`
- Cross-references use Obsidian-style wikilinks such as `[[vitamin-d-and-sleep]]`
- Frontmatter `sources` and `contradictions` use page names without brackets within their owning content wiki

### Cross-boundary query citations

When Search or DeepQuery starts at a collection

- Detect duplicate page basenames across routed descendants before synthesis
- Cite every result with its owning child route
- Use a path-qualified wikilink from the requested collection root, such as `[[child/references/page|page]]`
- Include the full nested child route when collections are nested
- Keep citations qualified even when routing selects only one child
- Do not pass those qualified paths into `sources:` frontmatter

## Optional meta artifacts

- `references/_meta/topic-map.md` is an optional helper for large content wikis
- `references/_meta/ubiquitous-language.md` is an opt-in DDD glossary
- Collection roots never own `_meta` artifacts. Route them to a content wiki

## Hard rules

### Page creation

Create a page when

- the entity, concept, or topic appears in two or more sources
- or it is the central subject of one source

Update an existing page when it already covers the subject. Do not create pages for passing mentions or off-scope references

### Outbound wikilinks

Content kinds require at least two outbound wikilinks

- `kind/project`
- `kind/doc`
- `kind/plan`
- `kind/query`

Operational kinds should contain at least one outbound wikilink

- `kind/task`
- `kind/bug`
- `kind/tracking`

Exempt kinds

- `kind/wiki`
- `kind/log`
- `kind/webclip`
- `kind/random`

Closed pages are exempt

### Page splitting and index scaling

- Split a page over 200 lines, excluding frontmatter and `## Related`
- Split an INDEX section over 50 entries
- Offer a topic map when total entries exceed 200

### Mass updates

- If an operation would create, modify, move, or delete 10 or more pages, stop after planning and ask for confirmation
- In automated mode, halt without writing

### Schema and topology changes

Schema upgrades and topology normalization always require explicit approval, even in automated mode and regardless of size

Before requesting approval, show

- the current schema version and wiki type
- the target schema version and wiki type
- schema edits separately from directory moves
- every planned creation, modification, move, deletion, and path rewrite
- collisions, ambiguous files, and unresolved external path consumers
- the verification that will prove the migration complete

A single confirmation may authorize both operations only when the plan names them separately and shows their combined effects. A general request such as "apply wiki-map" is not migration approval

### Closed pages

- Keep `status/close` pages in `INDEX.md`
- Do not auto-suffix, remove, or reorganize their entries
- Exclude them from orphan, stale, and wikilink-minimum checks
- Include them in contradiction and frontmatter validation

### Interactive and automated modes

Automated mode may skip ordinary conversational confirmations, but must still honor

- the mass-update gate
- CreateWikiMap directory-scan confirmation
- UpgradeSchema approval
- NormalizeWikiMap approval

When uncertain, use interactive mode

## Session orientation

Before operating on an existing wiki

1. Read this schema
2. Read the requested root `INDEX.md`
3. Classify its schema version and declared or inferred wiki type
4. Inventory the paths needed to compare `INDEX.md` with the filesystem
5. If it is a collection, apply Collection routing before reading or writing child content
6. If it has 100 or more pages, search for the request topic before creating a page
7. Report legacy operational logs without reading them as orientation context

For a new wiki, read this schema and skip missing wiki files

If `INDEX.md` and the filesystem disagree, report the concrete mismatch. Do not normalize structure unless the user explicitly approves `NormalizeWikiMap`

```text
Oriented: {wiki-name} | schema {version or unstamped} | {content|collection|ambiguous} | {N} indexed pages | {drift status}
```

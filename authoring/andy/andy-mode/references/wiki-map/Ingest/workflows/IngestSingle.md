# IngestSingle Workflow

Process one source into an existing or newly created wiki. Read the source, optionally discuss key takeaways with the user, then integrate it into the wiki with provenance and cross-references.

## When to Use

- Adding a single article, paper, transcript, note, or webclip
- User wants to stay involved and guide emphasis
- User says "ingest this", "process this article", "add this to the wiki"

## Steps

### 0. Orientation

Always read `../../SCHEMA.md`.

If the wiki already exists:
- follow the shared Session orientation protocol
- if the requested root is a collection, use Collection routing to resolve one destination content wiki before planning writes
- halt and offer UpgradeSchema before writing to a pre-V3 wiki
- if the destination has 100 or more pages, search for the topic before creating any new page
- report concrete INDEX/filesystem drift without normalizing it

Emit a one-line summary:

```text
Oriented: {wiki-name} | schema 3 | content | {N} indexed pages | {drift status}
```

### 1. Read the Source

- Read the source file or content provided by the user
- If the source is a URL, fetch it with whatever capability is available and save it as a local webclip before ingestion
- If you cannot fetch the URL, ask the user to save it locally and provide the path
- Identify key entities, concepts, claims, data points, and contradictions with existing wiki content

### 2. Discuss with User When Interactive

In interactive mode, present a short summary and ask whether to proceed.

```markdown
## Source Summary: {source title}

**Key takeaways:**
1. {takeaway 1}
2. {takeaway 2}
3. {takeaway 3}

**Entities identified:** {list}
**Concepts:** {list}
**Notable claims:** {list}

Shall I proceed with ingestion? Anything to emphasize or skip?
```

In automated mode, skip this conversational gate.

### 3. Create or Update the Webclip Page

If the source is external content or a source snapshot, create or update a `kind/webclip` page:

```yaml
---
name: {Source Title}
description: {One-line summary}
tags:
  - area/ea
  - kind/webclip
  - status/stable
date_created: {today if new}
date_updated: {today}
---
```

Webclips preserve source content as-is. Do not add synthetic links just to satisfy cross-reference rules. Webclips are exempt from the outbound-link minimum.

### 4. Plan Page Writes

Before writing, decide which pages to create and which to update.

Create a new page only when:
- the entity, concept, or topic appears in 2 or more sources, or
- it is the central subject of this source

Update an existing page when it already covers the topic.

For each page in the plan:
- choose the right `kind/*` tag
- add `topic/*` only when it clarifies the subject
- set `date_created` and `date_updated` on new pages
- bump only `date_updated` on existing pages
- populate `sources:` with the relevant source page names for `kind/project`, `kind/doc`, and `kind/query`
- maintain or add outbound `[[wikilinks]]` per the schema minimums

### 4.5 Mass-Update Gate

If the operation would create or modify 10 or more pages:
- stop after planning
- list all pages that would be touched
- ask for confirmation before writing

In automated mode, halt without writing.

### 5. Apply the Plan

For each planned page:
- create the page if it does not exist
- update the page if it does exist
- keep provenance in `sources:`
- preserve `date_created`
- bump `date_updated`
- ensure `## Related` contains the relevant links unless the page kind is exempt

### 6. Handle Contradictions

If the new source contradicts existing wiki content:
- add the conflicting page name to `contradictions:` frontmatter on both pages
- optionally maintain a `## Contradictions` body section if the page already uses one
- do not silently overwrite older claims

### 7. Update INDEX.md

- Add new pages to the table
- Update descriptions if a page's scope changed materially
- Update the stats line and `date_updated`

### 8. Verify and report

Re-read the created and updated pages plus `INDEX.md`. Confirm every expected path exists, every new page is indexed once, provenance points to existing source pages, and no unplanned file changed.

```markdown
## Ingestion Complete: {source title}

**Created:** {list of new pages}
**Updated:** {list of modified pages}
**Contradictions flagged:** {list or none}
**Provenance updated:** {count of pages with sources:}

INDEX.md updated and the planned state verified.
```

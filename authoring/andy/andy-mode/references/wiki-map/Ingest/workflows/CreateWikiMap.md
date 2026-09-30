# CreateWikiMap workflow

Organize an existing directory into a V3 content wiki or, when it already contains a pure set of child wikis, a V3 wiki collection

This workflow never rewrites or summarizes existing body content

## When to use

- Turn an existing markdown directory into a wiki
- Create a new empty wiki
- The user asks to create, bootstrap, initialize, or organize a wiki

## Steps

### 1. Detect the starting state

Read `../../SCHEMA.md` and inspect the target

- Empty directory means new content-wiki mode
- Files without `INDEX.md` mean organize mode
- `INDEX.md` with `schema_version: 3` means an existing wiki, stop
- Older or unstamped `INDEX.md` means an existing legacy wiki, route to UpgradeSchema

Never upgrade or normalize an existing wiki from this workflow

Classify an unindexed directory before proposing a shape

- At least two direct child directories with `INDEX.md` and no local wiki pages means collection-create candidate
- Optional `AGENTS.md`, `README.md`, `assets/`, and recognized repository control files do not disqualify that candidate and are not indexed
- Any local wiki page or ordinary content directory means content-wiki mode
- Conflicting or uncertain evidence means ambiguous, ask before planning
- Existing child boundaries are evidence. Never create child boundaries merely to reach the threshold

### 2. Confirm scope

Resolve the target directory, wiki name, and one-line description. For an existing directory, present the complete scan before moving anything

```markdown
## Directory Scan: {path}

**Files found:** {count}
**Already under references/:** {count}
**Need to move:** {count}
**Existing child wikis preserved:** {list}
**Ordinary subdirectories preserved:** {list}
**Proposed wiki type:** {content|collection}

| File | Current | Proposed |
|---|---|---|
| `My Article.md` | root | `references/my-article.md` |
| `notes_on_sleep.md` | root | `references/notes-on-sleep.md` |

Proceed?
```

Confirmation is mandatory even in automated mode

For a collection-create candidate, show that child directories will remain in place, no `references/` wrapper will be created, and the root `INDEX.md` will become their router

### 3. Create the approved shape

For a content wiki

```text
{wiki-name}/
  INDEX.md
  AGENTS.md    # When already present
  README.md    # When already present
  references/
  assets/       # Only when non-markdown files exist
```

For a collection

```text
{collection-name}/
  INDEX.md
  AGENTS.md    # When already present
  README.md    # When already present
  {existing-child-a}/
  {existing-child-b}/
  assets/       # Only when non-markdown files exist
```

Keep optional `AGENTS.md`, optional `README.md`, and recognizable repository control files at the root in either shape. Preserve existing root document bodies. If their responsibilities overlap, report the overlap instead of rewriting them in this workflow. If the role of another root file is uncertain, include it in the scan and ask before moving it

For a collection, keep child wikis in place and do not create `references/`

### 4. Organize a content wiki

Skip this step for an approved collection. Its existing child boundaries remain in place

- Move wiki content from the root into `references/`
- Preserve existing directory structure
- Keep existing child wikis intact
- Move a root child wiki under `references/` as one directory
- Do not index the child wiki's internal pages in the parent
- Do not create new child boundaries
- Rename markdown files to kebab-case
- Use a deterministic suffix such as `-2` for an approved collision
- Do not modify body content

### 5. Add missing page frontmatter

Skip this step for a collection because it has no local pages

Skip pages inside an existing child wiki boundary

For a local markdown page without frontmatter, prepend

```yaml
---
name: {derived from filename}
description: {first heading or filename}
tags:
  - area/ea
  - kind/random
  - status/stable
date_created: {today}
date_updated: {today}
---
```

- Use an obvious existing kind when shallow evidence is sufficient
- Use `kind/webclip` only for an obvious source snapshot
- Otherwise keep `kind/random` rather than assigning a source-required kind without provenance
- Do not invent `topic/*`, `sources:`, or `contradictions:`
- Leave existing frontmatter unchanged

### 6. Build INDEX.md

Use the approved type's V3 frontmatter and body from `../../SCHEMA.md`

- Always set `schema_version: 3`
- For content, omit `wiki_type`, catalog local pages, and route direct children through `references/{child}/INDEX.md`
- For collection, set `wiki_type: collection`, add routing guidance, and route direct children through `{child}/INDEX.md`
- Add only each direct child `INDEX.md` under `kind/wiki`
- Use child frontmatter descriptions first
- Keep `INDEX.md` focused on agent routing. Do not copy agent instructions from `AGENTS.md` or the end-user presentation from `README.md`
- Include accurate counts and `date_updated`
- Do not create an operational log

### 7. Verify and report

- Every indexed path resolves
- Every local markdown page in a content wiki appears exactly once
- Child leaf pages do not appear in the parent index
- Page bodies match their pre-operation content
- Optional root documents remain at the root and any responsibility overlap is reported
- No Wiki Map operational log exists
- A collection has no `references/` wrapper and a second classification recognizes it as current

```markdown
## Wiki Map Created

**Files moved:** {count}
**Files renamed:** {count}
**Frontmatter added:** {count}
**Wiki type:** {content|collection}
**Existing child wikis preserved:** {count}
**Schema:** 3

`INDEX.md` created or updated
```

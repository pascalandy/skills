# FileAnswer Workflow

Save a synthesized answer back into the wiki as a new page so the answer compounds instead of disappearing into chat history.

## When to Use

- After a DeepQuery produces a substantive answer
- User says "save that answer", "file this as a wiki page", or "add this to the wiki"

## Steps

### 0. Orientation

- Read `../../SCHEMA.md`
- Follow the shared Session orientation protocol
- If the requested root is a collection, resolve exactly one destination content wiki before planning the page
- Halt and offer UpgradeSchema before writing to a pre-V3 wiki
- If the destination has 100 or more pages, search for the topic before planning a new page
- Report concrete INDEX/filesystem drift without normalizing it

### 1. Wiki-Worthy Judgment

File the answer when:
- re-deriving it would require reading 3 or more pages
- it is a useful comparison, synthesis, timeline, or decision record
- the user explicitly asks to save it

Do not file when:
- it is a simple lookup from one page
- it mostly restates an existing page

If the answer is not worth filing, offer to add a short note or backlink to an existing page instead.

### 2. Determine Metadata

- Choose a descriptive kebab-case filename
- Use `kind/query`
- Use `status/stable` unless there is a better status from context
- Add `topic/*` only when it clarifies the subject

### 3. Format as a Wiki Page

Use V3 page frontmatter:

```yaml
---
name: {Title}
description: {One-line summary}
tags:
  - area/ea
  - kind/query
  - status/stable
date_created: {today}
date_updated: {today}
sources:
  - page-a
  - page-b
---
```

Body rules:
- start with a summary paragraph
- preserve inline `[[wikilinks]]`
- end with `## Related`
- satisfy the outbound-link minimum for content kinds

### 4. Check for Existing Coverage

If an existing page already covers the same topic, ask whether to merge into it or keep a separate filed answer.

If the answer cites pages from more than one content wiki, do not file it as one page. V3 has no canonical cross-boundary `sources:` identity. Offer to file separate child-local answers or leave the synthesis in the response until the user chooses a new owning architecture.

### 5. Respect the Mass-Update Gate

If filing the answer would touch 10 or more total pages, counting the new `kind/query` page plus any existing pages to update, stop and ask for confirmation before writing.

In automated mode, halt without writing.

### 6. Write the Page and Update Links

- save the new page under `references/`
- add it to `INDEX.md`
- add backlinks from cited pages when appropriate

### 7. Verify and report

Re-read the filed page, cited source paths, backlinks, and destination `INDEX.md` before reporting.

```markdown
## Filed: {page title}

Saved as `references/{filename}.md` (kind/query).
Cross-referenced with {N} existing pages.
INDEX.md updated and the filed page verified.
```

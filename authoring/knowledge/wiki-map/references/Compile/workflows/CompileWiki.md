# CompileWiki workflow

Promote implied-missing entities into first-class pages through one complete plan and one verified write set

## When to use

- The user asks to compile the wiki, fill wiki gaps, promote missing entities, or mine concepts
- A mature content wiki repeatedly names entities that lack pages

## Not for

- External sources, use Ingest
- Route rebuilding, use RecursiveUpdate
- General health reporting, use FullSweep or QuickCheck
- Schema or topology migration, use UpgradeSchema or NormalizeWikiMap

## Workflow

### 1. Orient and resolve scope

- Read `../../SCHEMA.md`
- Follow the shared Session orientation protocol
- If the requested root is a collection, use its routing descriptions to resolve one destination content wiki
- If multiple children are plausible, ask the user
- Halt on a pre-V3 destination and offer UpgradeSchema
- Halt on an unresolved topology ambiguity or recognized legacy operational log

Emit

```text
Oriented: {wiki-name} | schema 3 | content | {N} indexed pages | {drift status}
```

### 2. Run the same-session preflight

Compile depends on observable structure, so validate its assumptions now

- every local INDEX entry resolves
- every local markdown page is indexed once
- every direct child route resolves and no child leaf page is in the parent index
- mining targets have readable frontmatter and valid tag order
- `sources:` entries on mining targets resolve
- no duplicate target filenames exist
- no partial-write symptoms appear between the filesystem and INDEX

If a critical precondition fails, halt and report the exact finding plus the relevant Lint workflow. Do not mine or write

```text
Compile preflight: passed | {pages checked} pages | {routes checked} child routes
```

### 3. Survey

Identify

- every local content page listed in the destination INDEX
- plain directories under `references/` that contain markdown but no child `INDEX.md`
- pages over 200 lines
- thin pages

Rank long pages first, thin pages second, and regular pages third. Default to the top 30 targets, and offer a different cap when wiki size makes 30 unreasonable

```text
Survey: {total} pages | {long} long | {thin} thin | {bare directories} bare directories | {selected} mining targets
```

### 4. Mine candidates

Split targets into batches of about ten pages

Use this fixed worker contract whether execution is parallel or sequential

```text
INPUT
- wiki page paths
- existing page names for deduplication

TASK
- read every assigned page
- extract discrete named people, tools, frameworks, concepts, and events
- record the unique source pages that mention each entity
- reject adjectives, verbs, filler phrases, and generic topics unless a page treats one as its named subject
- suggest kind/doc or kind/project
- suggest an applicable topic tag or null

OUTPUT
{
  entity: "vitamin-d",
  source_pages: ["sleep-quality", "clinical-review"],
  central_subject: false,
  suggested_kind: "doc" | "project",
  suggested_topic: "relationship" | "strategy" | "playbook" | null
}
```

Merge outputs by kebab-case entity name, union source pages, and recompute reference counts. Prefer `kind/project` only for a clearly ongoing initiative; otherwise use `kind/doc`

### 5. Plan and request approval

Keep candidates that

- appear in at least two unique source pages
- or are the central subject of one page

For every survivor, plan

- filename and destination
- kind and optional topic
- source-grounded summary
- `sources:` frontmatter
- outbound links
- sibling back-edits at existing prose mentions, with `## Related` as fallback

```markdown
## Compile Plan

**Preflight:** passed in this session

| Entity | Sources | New Page | Kind | Topic | Back-Edits |
|---|---:|---|---|---|---|
| {entity} | {count} | {path} | {kind} | {topic or none} | {pages} |

**New pages:** {X}
**Unique sibling pages edited:** {Y}
**Total unique files touched including INDEX:** {T}
```

Count unique files, not operations. In interactive mode, wait for confirmation before writing

If ten or more pages would be created or modified, the shared mass-update gate applies. In automated mode, halt without writing. Below that threshold, automated mode may proceed

### 6. Apply the approved write set

1. Revalidate that planned source files and target paths have not changed
2. Create every approved page with V3 page frontmatter
3. Apply every approved sibling back-edit
4. Preserve `date_created` and bump `date_updated` on edited pages
5. Patch `INDEX.md` once
6. Do not rebuild child routes or change topology

### 7. Verify

Compare the approved plan with the final filesystem

- every new page exists and is indexed once
- every new page cites its planned source pages
- every source path resolves
- every planned sibling contains the intended wikilink once
- every edited page has the expected dates
- INDEX counts and descriptions match the final pages
- no unplanned file changed

If a write or check fails, stop and report completed writes, pending writes, and the first mismatch. Do not continue or claim atomicity

### 8. Report

```markdown
## Compile Complete

**New pages:** {X}
**Sibling pages updated:** {Y}
**INDEX sections updated:** {list}
**Preflight:** passed
**Post-write verification:** passed
```

## What Compile does not do

- ingest external sources
- persist health history
- rebuild nested routes
- change schema or wiki type
- loop through separate write passes for each entity

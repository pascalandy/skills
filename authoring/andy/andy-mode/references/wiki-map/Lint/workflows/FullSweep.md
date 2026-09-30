# FullSweep Workflow

Comprehensive health check of the entire wiki. Read every page, validate against the shared schema, and report findings by severity.

## When to Use

- diagnostic health checks
- after batch ingestion
- before relying on the wiki for an important analysis
- user says "health check the wiki", "lint the wiki", or "full sweep"

For triage, safe-fix planning, and maintenance orchestration, use `MaintenanceCycle.md`.

## Steps

### 1. Orientation and Read Set

- read `../../SCHEMA.md`
- follow the shared Session orientation protocol
- classify every boundary by schema version and wiki type
- for a content wiki, discover child boundaries under `references/`
- for a collection, discover direct child boundaries at the collection root
- read every local page listed in each content wiki `INDEX.md`
- for each nested child wiki boundary, read the child `INDEX.md` and lint that child boundary recursively instead of expecting the parent `INDEX.md` to inline the child's leaf pages
- at each wiki boundary, read optional `AGENTS.md` and `README.md` for the root document check
- scan each content wiki's `references/` for local files missing from `INDEX.md`, excluding files that belong to a child boundary
- scan each collection root for local wiki pages or non-child content that violates collection shape, excluding optional `AGENTS.md`, `README.md`, `assets/`, and recognized repository control files
- detect recognized legacy operational logs by signature without using them as orientation context

### 2. Run Checks

Run all of these checks:

- **INDEX integrity**
  - local files in `references/` missing from `INDEX.md`
  - phantom `INDEX.md` entries pointing to missing files
  - missing parent routes to direct child wiki `INDEX.md` files
  - duplicate page basenames within a content wiki, which make unqualified identity ambiguous
  - stale or inaccurate INDEX descriptions, including direct child wiki route descriptions
  - do not flag a parent as stale just because it does not list a child wiki's leaf pages
  - plain directories without their own `INDEX.md` stay ordinary content and must still be indexed directly

- **Schema and topology**
  - missing or outdated `schema_version`
  - `wiki_type: collection` whose filesystem has local wiki content or a `references/` wrapper
  - collection candidates confirmed by every NormalizeWikiMap precondition
  - mixed or residual wrapper content classified as ambiguous, not as a collection candidate
  - content wikis missing `references/`
  - recognized legacy Wiki Map operational logs
  - ambiguous directories that cannot be classified safely

- **Frontmatter and tag validation**
  - required fields present
  - `date_created` present, not in the future, and not later than `date_updated`
  - tag axis order is `area -> kind -> topic -> status -> pty`
  - valid `kind/*`, `topic/*`, `status/*`, `pty/*` values

- **Cross-reference health**
  - broken wikilinks
  - orphan pages
  - orphan webclips not referenced in any page's `sources:`
  - missing cross-references
  - content pages below the outbound-link minimum as warnings
  - operational pages below the soft outbound-link minimum as info

- **Contradictions and provenance**
  - unresolved contradictions from `contradictions:` frontmatter
  - broken `sources:` entries pointing to missing pages
  - `kind/project`, `kind/doc`, and `kind/query` pages missing `sources:`

- **Content structure**
  - pages over 200 lines
  - thin pages that likely should merge elsewhere
  - missing pages implied by repeated references

- **Root document roles**
  - `AGENTS.md` and `README.md` are optional and their absence is not a finding
  - `AGENTS.md` owns instructions for how the agent works
  - `INDEX.md` remains the canonical source for agent routing
  - `README.md` owns the end-user presentation of the project
  - report substantial information repeated across these files or content placed under the wrong responsibility
  - accept a link or short routing pointer to information owned by another root document
  - do not extend this DRY check to wiki pages under `references/`

- **Aging and operational health**
  - stale pages older than 180 days when open or stable
  - `INDEX.md` sections over 50 entries
  - total `INDEX.md` entries over 200
  - partial-write symptoms such as missing planned targets, phantom entries, duplicate index membership, or mismatched frontmatter dates

Closed pages are excluded from orphan, stale, and weak-link checks but still included in contradiction and frontmatter validation.

If a content wiki's total `INDEX.md` entries exceed 200:
- recommend creating or regenerating `references/_meta/topic-map.md`
- offer to generate it
- if the file already exists and may contain user edits, ask for confirmation before overwriting it

When child wikis are present:
- validate each child wiki boundary on its own terms
- validate that the parent routes only to direct child `INDEX.md` files
- do not flatten grandchild or deeper leaf pages into the parent read model

### 3. Produce Health Report

Report issues by severity using the ordering defined in `../MetaSkill.md`.

```markdown
## Wiki Health Report: {wiki name}

**Date:** {today}
**Wiki boundaries:** {count} | **Pages:** {total} | **Sources:** {webclip count}

### Critical
{numbered list}

### Warning
{numbered list}

### Info
{numbered list}

### Suggested Actions
1. {specific fix}
2. {specific fix}
```

### 4. Offer to fix

Offer automatic fixes only for low-risk issues such as:
- INDEX drift
- safe tag corrections
- missing cross-references

Keep contradictions, provenance problems, and stale-content decisions for explicit review.

Report root document overlaps and propose specific moves or links, but do not rewrite those files automatically

Route schema upgrades and legacy operational-log cleanup to UpgradeSchema. Route collection conversion to NormalizeWikiMap. Never include either migration among ordinary automatic fixes.

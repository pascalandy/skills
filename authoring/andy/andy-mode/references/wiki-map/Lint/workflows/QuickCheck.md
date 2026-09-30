# QuickCheck Workflow

Targeted health check for one issue type. Faster than FullSweep, but still grounded in the shared schema.

## When to Use

- user asks about one specific issue type
- after a risky ingest
- spot-checking wiki integrity

## Steps

### 1. Identify the Check Type

Map the request to one check:

| User Request | Check Type |
|-------------|------------|
| "orphans", "orphan pages", "unlinked pages" | orphan pages |
| "orphan webclips", "sources", "provenance" | provenance and orphan webclips |
| "contradictions", "conflicts", "disagreements" | contradictions |
| "stale", "outdated", "old pages" | stale content |
| "missing pages", "red links", "broken links" | broken or missing links |
| "cross-references", "missing links", "underlinked", "few links", "thin links" | cross-reference health |
| "tags", "frontmatter", "metadata", "topic tags", "tag order", "axis order" | tag and frontmatter validation |
| "index", "INDEX.md", "index size", "huge index" | INDEX integrity and scaling |
| "legacy logs", "obsolete logs", "wiki log" | recognized legacy operational logs |
| "big pages", "long pages", "split" | page size |
| "partial write", "inconsistent batch", "recovery" | filesystem and INDEX consistency |
| "collection", "inception", "wiki type" | schema and topology |
| "AGENTS.md", "README.md", "root documentation", "DRY across root files", "duplicated routing" | root document roles |

### 2. Read What You Need

Always begin orientation for an existing wiki by reading:
- `../../SCHEMA.md`
- the requested root `INDEX.md`
- the filesystem paths needed for the selected check

Apply Collection routing when the requested root is a collection. Report concrete drift without normalizing it.

After orientation, read the smallest additional set that can answer the question:
- link, contradiction, stale, provenance, and tag checks usually require all pages
- INDEX checks require a directory inventory in addition to `INDEX.md`
- legacy-log checks inspect only exact candidates from the shared signature and never treat them as orientation history
- topology checks inspect direct child boundaries and local content at the requested root
- index scaling checks should also inspect `references/_meta/topic-map.md` when it already exists
- root document checks read `AGENTS.md` and `README.md` when present, compare only those files with `INDEX.md`, and do not inspect wiki pages for DRY issues

### 3. Run the Check

Run only the targeted check, using the same rules as FullSweep.

If the targeted check is INDEX scaling and a content wiki exceeds 200 indexed pages:
- report whether `references/_meta/topic-map.md` is missing, stale, or present
- offer to create or regenerate it
- ask before overwriting an existing file that may contain user edits

### 4. Report Results

```markdown
## QuickCheck: {check type}

**Wiki:** {wiki name} | **Pages scanned:** {count}

### Findings
{numbered list}

### Suggested Fixes
{specific actions}
```

If nothing is wrong, say so explicitly.

### 5. Offer to fix

Offer automatic fixes only for low-risk issues. For contradictions, provenance problems, and stale-content decisions, report first and wait for direction.

Legacy log cleanup requires UpgradeSchema approval. Topology conversion requires NormalizeWikiMap approval.

Root document overlaps are report-only. Offer specific moves or links, then wait for approval because changing ownership between `AGENTS.md`, `INDEX.md`, and `README.md` may change what each audience sees

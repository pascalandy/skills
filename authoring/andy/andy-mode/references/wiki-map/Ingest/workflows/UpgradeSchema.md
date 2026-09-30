# UpgradeSchema workflow

Migrate an older wiki to schema V3 without changing its topology. Page bodies remain unchanged except for approved inbound-link cleanup required to delete a recognized legacy operational log

## When to use

- The user asks to upgrade or migrate a wiki
- A mutating workflow finds a missing or lower `schema_version`
- A V3 wiki still contains recognized legacy Wiki Map operational logs

## Boundary

UpgradeSchema changes schema. It does not move child wikis or convert a content wiki into a collection. If the current shape is a collection candidate, report `NormalizeWikiMap.md` as a separate optional operation

## Detection

Read `INDEX.md`, resolve the requested scope, inventory every included wiki boundary, and classify each one

- A request naming one wiki upgrades that boundary only
- A request naming a wiki tree or collection includes all descendant boundaries
- Show every included boundary in the plan so tree scope is never implicit

- `schema_version: 3` with no legacy artifacts means current, stop
- `schema_version: 3` with recognized legacy operational logs means V3 cleanup only
- `schema_version: 2` means V2 to V3
- absent or lower means legacy to V3

Infer the current type conservatively

- `wiki_type: collection` means collection
- direct child wikis with no local wiki pages may already have collection shape
- otherwise treat it as content
- if type evidence conflicts, mark it ambiguous and stop before planning writes

Recognize an obsolete operational log only by the complete signature in `../../SCHEMA.md#legacy-operational-logs`. Read a candidate only to validate that signature. User-authored logs are content and remain untouched

## Steps

### 1. Orient and inspect

- Read `../../SCHEMA.md` and the requested root `INDEX.md`
- Discover only the boundary or tree authorized by the request
- Inventory local pages, direct child boundaries, index entries, and recognized legacy logs for every included boundary
- Find legacy markers such as `kind/relationship`, missing `date_created`, missing status tags, or the old INDEX header
- Identify missing required `sources:` and other judgment calls as review-only findings
- For every recognized legacy log, inventory inbound wikilinks, `sources:` references, INDEX entries, and path consumers within the verified search scope
- If a signature or reference treatment is ambiguous, preserve the file and add it to review-only findings
- Do not use legacy logs as operational context

### 2. Present the migration plan

Separate automatic schema edits from review-only findings

```markdown
## Schema Upgrade Plan

**Current:** schema {version or unstamped} | {content|collection}
**Target:** schema 3 | {same type}

**Boundaries in scope:** {count and paths}

### Planned Changes
- stamp `schema_version: 3`
- add `wiki_type: collection` only when the existing structure is already an unambiguous collection
- migrate deprecated tags and required metadata: {files}
- remove recognized legacy operational logs: {files}
- repair approved inbound references and path consumers: {files or none}
- remove only matching INDEX entries and empty generated sections

### Review Only
- {missing provenance, weak links, ambiguous metadata, or none}

### Separate Structural Opportunity
- NormalizeWikiMap candidate: {yes/no and reason}

### Verification
- {checks that will prove V3 conformance}
```

List every file to modify or delete. If both UpgradeSchema and NormalizeWikiMap are proposed, keep their effects in separate sections

### 3. Require approval

Wait for explicit approval before every write or deletion

- This gate applies even in automated mode
- A general request to apply or maintain Wiki Map is not approval
- A combined confirmation is valid only when it explicitly covers both the schema and structural plans

### 4. Revalidate the approved plan

Immediately before writing

- Re-read every approved source file and INDEX
- Revalidate every legacy-log signature and inbound-reference inventory
- Confirm no planned file, route, or deletion target changed after approval
- Stop and present a revised plan if any evidence differs

### 5. Apply schema changes only

- Set `schema_version: 3`
- Preserve the existing wiki type unless its current collection shape is unambiguous
- Rewrite `kind/relationship` to `topic/relationship`
- Backfill missing `date_created` from `date_updated` when available
- Add `status/open` when no status tag exists
- Update the V3 INDEX header without replacing user-authored routing prose or tables
- Remove approved recognized legacy logs through a recoverable deletion mechanism when available
- Apply every approved inbound-reference and path-consumer repair before deleting its log
- Remove the corresponding INDEX rows and remove an empty generated `kind/log` section
- Remove `references/` only when an approved legacy-log deletion leaves it empty and the boundary is already an unambiguous collection
- Never infer missing provenance or new topic tags

Stop at the first write failure. Report completed operations, remaining operations, and the first mismatch. Do not continue into later boundaries or NormalizeWikiMap from a partial state

### 6. Verify

- Re-read every changed file
- Confirm every scoped index has `schema_version: 3`
- Confirm every `wiki_type` matches its unchanged topology
- Confirm every remaining INDEX route resolves
- Confirm approved legacy logs and only those logs are gone
- Confirm no index entry points to a removed operational log
- Confirm page bodies are unchanged except for approved legacy-log reference repairs
- Confirm a second UpgradeSchema detection reports current V3 with no legacy cleanup pending

If verification fails, stop and report the actual state. Do not continue into NormalizeWikiMap

### 7. Report

```markdown
## Schema Upgrade Complete

**Schema:** {previous or unstamped} -> 3
**Wiki boundaries upgraded:** {count}
**Wiki types:** unchanged
**Metadata fixes:** {count}
**Legacy operational logs removed:** {count}
**Review-only findings:** {count}
**NormalizeWikiMap candidate:** {yes/no}
```

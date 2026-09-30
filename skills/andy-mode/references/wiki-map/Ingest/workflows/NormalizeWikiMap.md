# NormalizeWikiMap workflow

Convert a V3 content wiki whose `references/` directory is only an unnecessary wrapper around several child wikis into a V3 wiki collection

## When to use

- The user asks to normalize, convert to a collection, remove an inception wrapper, or flatten a wiki wrapper
- Orientation detects a strong collection candidate and the user wants to review that structural change

## Boundary

NormalizeWikiMap changes topology. It does not upgrade schema, rewrite page bodies, merge wikis, invent child boundaries, or choose a new information architecture

Only this conversion is supported

```text
content wiki with wrapped children -> wiki collection with direct children
```

Reverse conversion and arbitrary reorganization are out of scope

## Preconditions

- The root has `schema_version: 3`
- The root is currently a content wiki
- `references/` contains at least two direct child directories with their own `INDEX.md`
- It contains no local wiki pages outside those child boundaries
- It contains no `_meta` content or ordinary content directories
- Every direct entry under `references/` belongs to one of the child wiki directories being moved
- Any residual file, hidden entry, symlink, or unmatched directory makes the structure ambiguous
- No child destination collides with an existing root path
- Recognized legacy operational logs have already been removed through UpgradeSchema

Optional `AGENTS.md`, `README.md`, `assets/`, and recognized repository control files outside `references/` do not prevent collection status. Any other root entry that is not a planned child wiki makes the structure ambiguous

## Steps

### 1. Inspect without writing

- Read `../../SCHEMA.md` and the root `INDEX.md`
- Verify every precondition
- Inventory each child wiki as one indivisible move
- Read each child `INDEX.md` for its description and declared type
- Inventory path references inside the wiki, including Markdown links resolved relative to their source files
- When an owning project root is discoverable, search its controlled text, config, and code files for old path prefixes and relative links that resolve through the wrapper
- State the search boundary when no project root can be determined

Do not treat unsearched locations as clean. Report them as outside the verified boundary

### 2. Present the structural plan

```markdown
## Wiki Collection Conversion Plan

**Current:** schema 3 | content wiki
**Target:** schema 3 | wiki collection

### Moves
| Current | Target |
|---|---|
| `references/child-a/` | `child-a/` |
| `references/child-b/` | `child-b/` |

### Creates
- {files or none}

### Modifies
- {files or none}

### Deletes
- remove the empty `references/` directory

### Root INDEX Changes
- add `wiki_type: collection`
- replace wrapped child routes with direct routes
- add or refresh routing guidance from child descriptions
- remove local page counts and content sections that no longer apply

### Path Rewrites
| Consumer | Old Path | New Path |
|---|---|---|
| {file} | {old} | {new} |

### Ambiguities and Collisions
- {finding or none}

### Verification
- {checks that will prove the conversion complete}
```

List every creation, modification, move, deletion, and known external path consumer, using `none` for empty sections. Do not hide a large rewrite behind directory counts

### 3. Require approval

Wait for explicit approval before moving or editing anything

- This gate applies even in automated mode and below the mass-update threshold
- If new ambiguity or drift appears after approval, stop and re-plan
- Approval covers only the files and moves shown in the plan

### 4. Revalidate and apply

Immediately before writing, confirm that sources, destinations, indexed routes, and the complete direct-entry inventory under `references/` still match the approved plan

Apply in this order

1. Move each child wiki intact to its approved direct-child path
2. Rewrite approved path consumers within the authorized scope using resolved targets, not blind text replacement
3. Patch the root `INDEX.md` with `wiki_type: collection`, direct routes, routing guidance, counts, and `date_updated`
4. Remove `references/` only when it is empty
5. Refresh child indexes and then the collection index using RecursiveUpdate rules

Never rewrite child page bodies merely because their directory moved

### 5. Verify

- Every direct child route resolves
- Every direct child has an `INDEX.md`
- No leaf page is in the collection index
- No local wiki page or `_meta` artifact exists at the collection root
- Only direct wiki directories, optional `AGENTS.md`, optional `README.md`, optional `assets/`, and recognized repository control files remain beside `INDEX.md`
- `references/` is absent
- No verified-scope consumer still contains an old path
- Child content and file counts match the pre-move inventory
- A second classification returns `schema 3 | collection | no normalization needed`

If a write fails, stop immediately. Report every completed and pending creation, modification, move, deletion, path-consumer rewrite, root INDEX patch, child INDEX refresh, and wrapper removal, followed by the first failed operation or verification. Do not improvise a new topology

### 6. Report

```markdown
## Wiki Collection Conversion Complete

**Child wikis moved:** {count}
**Path consumers updated:** {count}
**Root routes verified:** {count}
**Old paths remaining in verified scope:** 0
**Idempotence check:** passed
```

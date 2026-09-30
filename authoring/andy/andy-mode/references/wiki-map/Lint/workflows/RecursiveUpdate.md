# RecursiveUpdate Workflow

Refresh an existing wiki tree bottom-up. Preserve existing nested child wiki boundaries, rebuild local `INDEX.md` files level by level, and refresh parent routes from child wiki metadata.

## When to Use

- user says `recursive wiki update`
- user says `refresh wiki tree`
- user says `update nested wiki`
- a requested wiki already contains nested child wikis and the goal is maintenance rather than one-off diagnosis

## Steps

### 1. Orientation and Boundary Discovery

- read `../../SCHEMA.md`
- follow the shared Session orientation protocol
- discover nested wiki descendants under the requested root
- under a content wiki, discover direct children below `references/`
- under a collection, discover direct children at the collection root
- treat only directories that contain `INDEX.md` as child boundaries
- preserve and ignore optional `AGENTS.md`, `README.md`, `assets/`, and recognized repository control files at collection roots
- ignore plain directories that do not define their own child wiki boundary
- sort discovered child wikis deepest first so traversal is bottom-up

Emit progress in traversal order as the run proceeds.

### 2. Refresh Each Wiki Bottom-Up

For each discovered wiki, from deepest descendant up to the requested root wiki:

- read that wiki's local `INDEX.md`
- classify it as content or collection
- for a content wiki, refresh local pages and keep plain directories in the local indexing model
- for a collection, refresh direct child routes and routing descriptions without indexing descendant pages
- preserve existing child wiki routes
- refresh each direct child route description from the child `INDEX.md`
- use child `INDEX.md` frontmatter `description` first
- fall back to the first non-empty paragraph after frontmatter and title when description is missing
- do not flatten a child wiki's internal pages into the parent `INDEX.md`
- do not create new child wiki boundaries
- do not add, remove, or change `wiki_type`

### 3. Failure Handling

- use best-effort execution for nested trees
- if one branch fails, skip that branch and continue updating sibling branches
- continue updating higher levels when it is still safe to do so
- do not stop mid-run to ask the user how to handle a failed branch
- collect warnings and report them at the end

### 4. Report Results

Report the actual bottom-up traversal order.

```markdown
## Recursive Wiki Update: {wiki name}

### Traversal
1. updated {grandchild wiki path}
2. updated {child wiki path}
3. updated {root wiki path}

### Warnings
1. skipped {failed branch path}: {reason}
```

If there are no failures, state that explicitly.

### 5. Verify

For every successfully updated boundary, confirm that all local entries and direct child routes resolve, no descendant leaf page leaked into a parent index, and `schema_version` plus `wiki_type` were preserved.

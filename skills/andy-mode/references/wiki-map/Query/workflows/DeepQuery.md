# DeepQuery Workflow

Synthesize an answer across multiple wiki pages with citations and contradiction awareness.

## When to Use

- Questions that span multiple pages
- "Synthesize everything we know about X"
- "Compare A and B based on the wiki"
- "What's the current understanding of X?"

## Steps

### 1. Orientation

- Read `../../SCHEMA.md`
- Follow the shared Session orientation protocol
- At a collection, use the parent routing descriptions to select every relevant child and read those child indexes
- When the request starts at a collection, detect duplicate page basenames across routed descendants and use path-qualified citations for every cited page, even if only one child is selected
- Report concrete INDEX/filesystem drift without normalizing it

### 2. Find Relevant Pages

Follow the Search workflow to identify relevant pages, then read each one.

### 3. Follow Cross-References

Use body wikilinks and `## Related` links to pull in relevant adjacent pages. Stop when additional hops no longer change the answer.

### 4. Trace Provenance

Use `sources:` frontmatter on synthesized pages to trace claims back to source pages when stronger citations are needed.

### 5. Synthesize

Structure the answer to fit the question:
- prose summary
- comparison table
- timeline
- contradictions report

Always cite wiki pages inline. Follow the shared cross-boundary citation format when the answer spans content wikis.

### 6. Surface Contradictions

Read contradictions from frontmatter `contradictions:` first. If two pages disagree, report both positions with citations.

### 7. Identify Gaps

Call out what the wiki does not yet cover.

### 8. Suggest Filing Only When Worthwhile

Suggest `FileAnswer` only when the answer is worth preserving, such as:
- it synthesizes 3 or more pages
- it creates a novel comparison, timeline, or synthesis
- the user explicitly asked to save it

Do not suggest filing a simple one-page lookup.

In automated mode, skip the filing prompt entirely.

### 9. Report coverage

State which child wikis and pages informed the answer, which relevant branches were not read, and whether contradictions or coverage gaps remain

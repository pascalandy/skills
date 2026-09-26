# Search Workflow

Find relevant wiki pages for a topic and return a curated list with short summaries.

## When to Use

- Quick lookup: "what pages cover X?"
- Orientation: "what do we have on topic Y?"
- Before a deep query

## Steps

### 1. Orientation

- Read `../../SCHEMA.md`
- Follow the shared Session orientation protocol
- At a collection, use the parent routing descriptions to choose the smallest relevant child set
- Read each selected child's `INDEX.md`
- When the request starts at a collection, detect duplicate page basenames across its routed descendants before ranking results
- If a selected content wiki has `references/_meta/topic-map.md`, read it when useful
- Report concrete INDEX/filesystem drift without normalizing it

### 2. Rank Relevance

Identify candidate pages whose name, description, or tags match the query topic.

Use three buckets:
- direct match
- related
- tangential

### 3. Read Top Pages When Needed

If `INDEX.md` descriptions are not enough, read the strongest candidates to confirm relevance.

### 4. Present Results

```markdown
## Search Results: {query topic}

**Direct matches:**
- [[{child-route}/references/page-name|page-name]] -- {description}

**Related:**
- [[{child-route}/references/related-page|related-page]] -- {description and connection}

**Tangential:**
- [[{child-route}/references/tangential-page|tangential-page]] -- {brief note}

**Pages found:** {count} | **Selected wiki total:** {count across selected content wikis}
```

Use ordinary unqualified wikilinks only when the request starts directly inside one content wiki. Any request that starts at a collection uses the shared path-qualified citation format for every result, even when routing selects one child.

### 5. Suggest Next Steps

If the results warrant deeper synthesis:
- suggest `DeepQuery`
- if there is no dedicated page yet, suggest creating or filing one only if the result would be substantial

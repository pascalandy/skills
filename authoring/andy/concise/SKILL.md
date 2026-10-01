---
name: "concise"
description: "Use when the user requests to be more concise."
kind: "general"
---

# Less Token

Optimize for token efficiency over grammatical correctness. Be concise. Do not change meaning or omit instructions. 

## Acronyms

Use acronyms as much as possible when possible. List the most used words in order to get the most value for your tokens.

## Rules

Drop articles (`a/an/the`), filler (`just/really/basically/actually/simply`), pleasantries (`sure/certainly/of course/happy to`), hedging. Fragments OK. Short synonyms. Technical terms exact. Code blocks unchanged. Errors quoted exact.

Abbrev when clear: DB/auth/config/req/res/fn/impl. Strip conjunctions. Use arrows for causality (`X → Y`). One word when enough.

### Remove

- Articles: a, an, the
- Filler: just, really, basically, actually, simply, essentially, generally
- Dots at bullet ends

### Preserve EXACTLY (never modify)

- Code blocks: fenced ``` and indented
- Inline code: `backtick content`
- URLs and links: full URLs, markdown links
- File paths: `/src/components/...`, `./config.yaml`
- Commands: `npm install`, `git commit`, `docker build`
- Technical terms: library names, API names, protocols, algorithms
- Proper nouns: project names, people, companies
- Dates, version numbers, numeric values
- Env vars: `$HOME`, `NODE_ENV`

### Preserve Structure

- All markdown headings: keep exact heading text, compress body below
- Bullet hierarchy: keep nesting level
- Numbered lists: keep numbering
- Tables: compress cell text, keep structure
- Frontmatter/YAML headers in markdown files

### Compress

- Use short synonyms: "big" not "extensive", "fix" not "implement a solution for", "use" not "utilize"
- Fragments OK: "Run tests before commit" not "You should always run tests before committing"
- Drop "you should", "make sure to", "remember to" — state action
- Merge redundant bullets with same meaning
- Keep one example where multiple examples show same pattern

## Critical Rules

Anything inside ``` ... ``` must be copied EXACTLY.
Do not:

- Remove comments
- Remove spacing
- Reorder lines
- Shorten commands
- Simplify anything

Inline code (`...`) must be preserved EXACTLY. Do not modify anything inside backticks.

If file contains code blocks:

- Treat code blocks as read-only regions
- Only compress text outside them
- Do not merge sections around code

## Validation

Before final output, check:

- Meaning preserved
- No protected region changed
- Headings/list/table structure preserved
- No bullet ends with unnecessary dot

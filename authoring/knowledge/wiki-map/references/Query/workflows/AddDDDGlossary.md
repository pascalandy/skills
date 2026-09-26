# AddDDDGlossary Workflow

Create or update an explicit DDD-style ubiquitous-language glossary for the wiki. This is an opt-in synthesis artifact, not a mandatory schema layer.

## When to Use

- user says "add DDD glossary", "create DDD glossary", "build DDD glossary", or "update DDD glossary"
- user asks to create or update a ubiquitous language, domain glossary, or domain vocabulary artifact
- user explicitly wants canonical terms, aliases to avoid, ambiguous terms, or domain relationships extracted from the wiki and saved as a glossary

If the user only asks to discuss terminology, analyze domain terms, or explain domain model terms, answer with `Search.md` or `DeepQuery.md` first and ask before filing a glossary artifact.

## Not for

- ordinary wiki search -> use `Search.md`
- general synthesis answer -> use `DeepQuery.md`
- saving a normal answer page -> use `FileAnswer.md`
- promoting missing entity pages -> use `../../Compile/workflows/CompileWiki.md`
- enforcing terminology as lint policy -> use Lint only after the glossary exists and the user asks for drift checks

## Output

Write or update one optional meta artifact:

```text
references/_meta/ubiquitous-language.md
```

Do not create one page per term. Do not add new frontmatter fields to ordinary wiki pages.

## Steps

### 1. Orientation

- read `../../SCHEMA.md`
- follow the shared Session orientation protocol
- if the requested root is a collection, resolve exactly one destination content wiki before planning the glossary
- halt and offer UpgradeSchema before writing to a pre-V3 wiki
- if the destination has 100 or more pages, search for the requested domain or topic before planning the glossary read set
- read existing `references/_meta/ubiquitous-language.md` if it exists
- report concrete INDEX/filesystem drift without normalizing it

Emit:

```text
Oriented: {wiki-name} | schema 3 | content | {N} indexed pages | {drift status}
```

### 2. Determine Scope

Clarify the glossary scope before writing:

- current conversation plus selected wiki pages
- selected wiki pages
- a specific subdomain or topic
- the whole wiki

If the user did not specify scope, propose a narrow default from the request and confirm it in interactive mode.

The durable glossary must cite at least one wiki page in `sources:`. If the user only provides conversation context, draft candidate terms in the response and ask which wiki pages should ground the filed glossary before writing.

All cited source pages must belong to the destination content wiki. If the desired glossary spans content wikis, create separate child-local glossaries or stop and ask the user to choose an owning architecture.

### 3. Gather Source Pages

Read only the pages needed for the chosen scope:

- direct pages named by the user
- pages found through `INDEX.md` descriptions and tags
- high-signal linked pages when relationships matter
- existing glossary content, if present

For whole-wiki glossary creation, plan the read set first. If the wiki is large, ask whether to process the whole wiki or a bounded subdomain.

Do not write `references/_meta/ubiquitous-language.md` until at least one source page can be cited in frontmatter.

### 4. Extract Language

Extract domain vocabulary, not every noun.

Look for:

- canonical domain terms
- actor and role names
- lifecycle states
- business/domain events
- important verbs or commands used by domain experts
- synonyms and aliases
- overloaded or ambiguous words
- terms to avoid
- relationships between concepts
- open terminology questions

Prefer terms that appear in multiple pages, define important behavior, or are repeatedly used inconsistently.

### 5. Draft or Update the Glossary

Use standard wiki frontmatter:

```yaml
---
name: Ubiquitous Language
description: DDD-style glossary of canonical domain terms, aliases, ambiguities, and relationships.
tags:
  - area/ea
  - kind/doc
  - topic/reference
  - status/stable
date_created: {today if new}
date_updated: {today}
sources:
  - page-a
  - page-b
---
```

Use this body structure:

```markdown
# Ubiquitous Language

Summary paragraph describing the scope and how to use the glossary.

## Scope

{scope statement}

## Canonical Terms

| Term | Definition | Aliases / Avoid | Source Pages |
|---|---|---|---|
| {Term} | {definition} | {aliases or terms to avoid} | [[page-a]], [[page-b]] |

## Relationships

- A **{Term}** {relationship} a **{Term}**.

## Flagged Ambiguities

- **{word}** is used for both {meaning one} and {meaning two}. Prefer {canonical term} when referring to {meaning}.

## Preferred Language

| Prefer | Avoid | Reason |
|---|---|---|
| {canonical term} | {alias} | {reason} |

## Open Questions

- {question requiring user/domain-expert judgment}

## Related

- [[related-page]]
```

If updating an existing glossary:

- preserve useful manual notes
- merge duplicate terms
- keep unresolved ambiguities visible
- do not erase open questions unless the source material resolves them
- preserve `date_created` and bump `date_updated`

### 6. Update INDEX.md

Create `references/_meta/` if needed.

Add or refresh the `references/_meta/ubiquitous-language.md` entry under `kind/doc`, following the schema's `kind/*` INDEX organization.

Update the stats line and `date_updated`.

### 7. Verify and report

Re-read the glossary, its `sources:`, its INDEX entry, and every changed backlink before reporting.

```markdown
## Ubiquitous Language Glossary Complete

**File:** `references/_meta/ubiquitous-language.md`
**Scope:** {scope}
**Canonical terms:** {count}
**Ambiguities flagged:** {count}
**Open questions:** {count}

Future wiki-map workflows may consult this glossary for naming and terminology when relevant, but it is not mandatory orientation.
```

# Quality checklist

Use this checklist before returning a generated or revised glossary.

---

## Activation

- explicit trigger `pa-glossary` was present
- requested mode is respected:
  - planning only
  - production, export, or revision

---

## Structure

- one rendered H1 only
- glossary format matches artifact type
- skill glossaries use skill-glossary structure, not project-glossary structure
- project/domain glossaries include `## Global conceptual model`
- `Global domain` is not used as the default section title
- project/domain major concept sections have:
  - `### Relations`
  - `### Definitions`
- official project structure is preserved when available
- no artificial domain split was invented when source structure was sufficient

---

## Relations

- relations are high-level and structural
- each relation names at least two concepts
- relations use canonical terms
- relations do not repeat full definitions
- relations reduce ambiguity
- sequences use `→` when helpful
- cardinality appears only when it adds precision
- verbs describe stable structural links, not actions or events

---

## Definitions

- each definition starts with a clear canonical term
- definitions are concise and local
- project notes are present only when useful
- distinctions appear only when confusion is likely
- avoid-lists capture real wording risks
- aliases are not treated as accepted synonyms by default
- selected terms pass the conceptual validation in `../SKILL.md`, or their
  unresolved boundaries are explicit with `0o0o`

---

## Ambiguities

- real unresolved terminology ambiguities use `0o0o`
- `0o0o` entries describe terminology issues, not project follow-ups
- existing `0o0o` markers are preserved unless the user explicitly asks to resolve them
- if no unresolved terminology ambiguity exists, no empty `0o0o` section or "none identified" placeholder

---

## Skill glossary mode

When producing a skill glossary:

- concept map is operational, not decorative
- terms are grouped by use: core, operating/execution, safety, artifacts,
  boundaries, terms to avoid, decisions
- exact triggers, command shapes, path shapes, or branch names are included when
  they prevent misuse
- nearby skills/workflows are separated with boundary terms
- no forced `Relations` / `Definitions` subsections
- no forced `Def.`, `Project note`, `Distinct from`, or `Avoid` labels on every entry
- no decorative bold for canonical terms

---

## French business glossary mode

When producing a French `glossaire métier`:

- French labels are used consistently when used: Déf., Note projet,
  À distinguer de, Éviter
- `### Relations` appears before `### Définitions`
- final control sections are present only when useful
- ACv4-specific terminology is not copied into another project unless explicitly requested

---

## Scope hygiene

- no project delivery status tracking
- no requirement statements unless they define terminology
- no actor responsibility model duplicated when an actor document exists
- no architecture decisions are disguised as glossary definitions
- no onboarding tutorial or example dialogue unless explicitly requested
- no Markdown tables by default

---
name: "pa-glossary"
description: "Use only when explicitly invoked as `pa-glossary`."
metadata:
  version: "1.2.0"
  author: "user"
---

# Glossary Builder

## Purpose

Create or revise a canonical glossary for a project, domain, skill, CLI skill,
or business terminology set.

The glossary is a controlled map of local vocabulary, not a dictionary,
onboarding tutorial, status register, task list, RAID log, or delivery tracker.

Optimize for:

- terminology stability
- canonical forms
- expert readability
- conceptual boundaries
- high-level relations between concepts
- concise definitions
- visible unresolved terminology ambiguities

The expected readers are expert stakeholders or maintainers: business,
architecture, security, operations, product, delivery, legal, compliance,
technology, or agent-skill maintainers.

---

## Trigger

Use this skill **only** when the user explicitly writes:

```text
pa-glossary
```

Do **not** trigger this skill from generic mentions of:

- glossary
- business glossary
- ubiquitous language
- DDD
- domain model
- terminology
- canonical terms
- vocabulary

unless the exact trigger `pa-glossary` is present.

---

## Operating Modes

### Planning mode

Use planning mode when the user asks to plan, challenge, align, structure, review, or compare approaches.

In planning mode:

- do not create files
- challenge assumptions before endorsing the structure
- identify decisions still required
- flag unresolved terminology issues with `0o0o`
- end with a clear recommendation

### Production mode

Use production mode when the user explicitly asks to create, generate, export, write, or update a glossary or skill artifact.

In production mode:

- create or update the requested file
- choose the glossary format before writing; do not force one universal template
- read `references/skill-glossary-template.md` when producing a glossary for a
  skill, CLI skill, meta-skill, prompt skill, command skill, or
  `references/GLOSSARY.md` inside a skill directory
- read `references/glossary-template.md` when producing a project, product,
  domain, capability, or architecture glossary
- read `references/glossaire-metier-fr-template.md` when producing a French
  business glossary (`glossaire métier`, `glossaire canonique`, or
  `terminologie métier`)
- read `references/acv4-format-pattern.md` when the user asks to derive a
  glossary pattern from an ACv4-style artifact or a similar business-analysis
  glossary
- read `references/quality-checklist.md` before returning the final output
- preserve existing project structures when available
- report what was produced and link the artifact

---

## Core Mental Model

A glossary stabilizes local vocabulary so readers do not invent aliases or
misread boundaries.

For project/domain glossaries:

- **Relations** describe the architecture of the vocabulary
- **Definitions** describe the local meaning of terms
- **Avoid** protects canonical wording by naming forms not to use

For skill glossaries:

- concept maps show how the skill routes and operates
- term groups follow use: core, operating/execution, safety, artifacts, boundaries
- short definitions, rules, examples, and "Not:" boundaries are preferred over
  repeated labels

For all glossary types:

- **0o0o** exposes unresolved terminology ambiguities
- a good definition answers: "What does this term mean here?"

---

## Source Hierarchy

When multiple sources exist, prefer them in this order:

1. explicit user instructions in the current task
2. project-specific writing preferences or terminology rules
3. existing glossary or canonical terminology document
4. official domain, PBS, capability, actor, process, or architecture documents
5. business case, requirements, use cases, meeting notes, or conversation context
6. inference from domain language

If a source of truth exists for actors, roles, systems, responsibilities, or
official project domains, do **not** redefine it in the glossary. Reference it and
define only the terminology needed to read the glossary consistently.

---

## Terminology Discipline

Apply these rules while planning or producing a glossary:

- **Simplicity first:** include only terms that carry project-level meaning. Do not pad the glossary with generic programming concepts, status items, or decorative aliases.
- **Surgical changes:** when revising, change only terms, relations, structure, and avoid-lists needed for the requested glossary objective.
- **Surface conflicts, don't average them:** choose one canonical form when evidence supports it; move weaker variants to **Avoid** or flag unresolved ambiguity with `0o0o`. Do not normalize by blending competing terms.
- **Read before you write:** read all supplied sources and the existing glossary structure before adding canonical terms, groups, or relations.
- **Match project conventions:** preserve official domains, actor names, taxonomy, language, heading style, and numbered file conventions unless the user asks to redesign them.
- **Fail loud:** do not silently resolve uncertain vocabulary, delete `0o0o`, or redefine official terminology without evidence.

---

## Format Selection

Choose the format by artifact type before drafting:

| Target artifact | Format to use | Reference |
|---|---|---|
| Skill, CLI skill, meta-skill, prompt/command skill, or `references/GLOSSARY.md` inside a skill | Skill glossary | `references/skill-glossary-template.md` |
| Project, product, domain, capability, or architecture vocabulary | Project glossary | `references/glossary-template.md` |
| French business glossary (`glossaire métier`, `glossaire canonique`, `terminologie métier`) | French business glossary | `references/glossaire-metier-fr-template.md` |
| ACv4-style business-analysis glossary or derivative | ACv4 format pattern | `references/acv4-format-pattern.md` |

Do not use the project glossary template for skill glossaries. Skill glossaries
need operational clarity: routing, modes, boundaries, safety terms, and artifact
references. Project glossaries need conceptual structure and stakeholder domain
language.

---

## Default Project Glossary Structure

Use this structure by default for project, product, domain, capability, or
architecture glossaries:

```md
---
name: Project glossary <Project>
description: Canonical project glossary for <Project>
tags:
  - kind/glossary
  - kind/project
date_created: <YYYY-MM-DD>
date_updated: <YYYY-MM-DD>
---

# Project glossary <Project>

## Purpose

## Reading conventions

## Global conceptual model
### Relations
### Definitions

## <Domain, bounded context, capability, or conceptual family>
### Relations
### Definitions

## Terms to avoid as canonical forms

## Terminology decisions kept
```

Use **Global conceptual model**, not **Global domain**. The global section is the
conceptual overview of the model; it is not necessarily a domain.

Add `## 0o0o Unresolved terminology` only when at least one real unresolved
terminology ambiguity exists. Do not add empty unresolved sections, placeholders,
or "No active unresolved terminology ambiguities" sentences.

Use `### Relations` before `### Definitions` by default. For complex projects,
expert readers often need the conceptual map before local definitions.

Do not force every project into domains. Choose the strongest available grouping:

- official project domains
- bounded contexts
- capabilities
- lifecycle stages
- actor groups
- artifact families
- governance areas
- operational areas
- conceptual families

Use the project's official structure when it exists. Do not invent a cleaner
taxonomy if the project already has an approved one.

---

## Skill Glossary Mode

Use this branch after explicit `pa-glossary` activation when the requested
artifact is a glossary for a skill, CLI skill, meta-skill, prompt skill, command
skill, or a `references/GLOSSARY.md` file inside a skill directory.

Read `references/skill-glossary-template.md` before drafting a new skill
glossary.

In this mode:

- optimize for operational clarity, not business taxonomy
- group terms by use: core terms, operating/execution terms, safety terms,
  artifact terms, boundary terms, terms to avoid, and terminology decisions
- use short paragraphs under `### Term` headings
- use `Rule:`, `Not:`, `Examples:`, or short lists only when they add clarity
- include exact trigger phrases, command shapes, path shapes, or branch names
  when they prevent misuse
- include boundary terms for nearby skills or workflows that are easy to confuse
- do not force `Relations` / `Definitions` subsections into every group
- do not force labels such as `Def.`, `Project note`, `Distinct from`, or `Avoid`
  on every entry
- do not use decorative bold for canonical terms
- do not add empty `0o0o` sections or "none identified" placeholders

A skill glossary should read like a compact operating reference. If a label does
not improve use, omit it.

---

## French Business Glossary Mode

Use this branch after explicit `pa-glossary` activation when the requested
artifact is a French `glossaire métier`, `glossaire canonique`, or
`terminologie métier`.

Read `references/glossaire-metier-fr-template.md` before drafting a new French
business glossary. Read `references/acv4-format-pattern.md` only when the user
mentions ACv4, provides an ACv4-style source artifact, or asks to derive that
structure for another project.

In this mode:

- keep the user's project language as French unless instructed otherwise
- use `### Relations` before `### Définitions`
- use entry labels such as **Déf.**, **Note projet**, **À distinguer de**, and
  **Éviter**
- preserve exact actor, role, system, and taxonomy names from their canonical
  source documents
- add final control sections only when they carry real terminology value:
  **Règles générales d’écriture**, **Règles terminologiques prioritaires**,
  **Termes à ne pas utiliser comme formes canoniques**, and
  **Décisions terminologiques conservées**
- do not copy ACv4-specific terms, rules, or decisions into another project
  unless the target project is ACv4 or the user explicitly asks for them

---

## Source Analysis Process

When building from source material:

1. read all supplied sources before writing
2. identify the official structure of the project
3. extract candidate terms
4. group terms by the strongest real structure
5. choose canonical forms
6. move variants and weak aliases to **Avoid**
7. write high-level relations before definitions
8. write concise definitions
9. validate conceptual boundaries as described below
10. flag unresolved terminology ambiguities with `0o0o`
11. validate consistency and revise

Include terms such as:

- business objects
- domain roles
- actor categories
- named systems with business meaning
- artifacts
- statuses
- events
- governance mechanisms
- operational mechanisms
- technical concepts that carry project-level business meaning

Exclude by default:

- generic programming concepts
- implementation details with no domain meaning
- module or class names without business relevance
- delivery tasks
- project status
- approval state of deliverables

---

## Conceptual validation

During planning or production, check terms central to the model, ambiguous
terms, and terms that define responsibility boundaries. When revising, focus on
the requested changes and concepts whose meaning they affect.

For each selected term, use one normal example and one plausible counterexample
that should fall outside its definition. Check whether the definition and its
relations distinguish the two. Use supplied sources; label invented scenarios
as hypothetical. Code may provide evidence, but is never required.

If a case exposes a contradiction, propose a clarification consistent with the
source hierarchy. Apply supported refinements in production mode; flag unresolved
choices with `0o0o` and preserve existing markers under the ambiguity rules.

Stop when the selected boundaries hold or their uncertainty is explicit. Keep
only examples that help explain a distinction in the glossary. Do not turn this
check into an interview or apply it mechanically to every term.

---

## Relations

Relations describe the **architecture of the vocabulary**.

A good relation:

- names at least two canonical concepts
- expresses a stable structural link, not an action or event
- reduces ambiguity
- remains true even if individual definitions are rewritten
- avoids repeating a full definition

The right verbs depend on the domain. The list below is **illustrative, not
canonical** — the project's domain decides the actual lexicon. Useful verbs
typically express stable structure or directionality:

- contains, owns, produces, consumes
- governs, validates, approves, signs, issues, revokes, publishes
- protects, triggers, observes, archives, reconciles
- replaces, does not replace

Avoid verbs that read as task descriptions (*schedules*, *reviews*, *sends to*) —
those belong in process docs, not glossaries.

Use arrows when the sequence matters:

```md
- **A** → **B** → **C** describes the normal validation path
```

Use cardinality only when it clarifies the model:

```md
- **Order** produces 1+ **Invoices** after **Delivery** confirmation
```

Aim for enough relations to map the structure of the section, few enough that an
expert can scan the section in one pass. The right number depends on the domain;
do not pad for symmetry.

Avoid mini-definition cards inside `Relations`:

```md
- **Term**
  - **Role** : ...
  - **Use when** : ...
  - **Question** : ...
```

That format belongs to explanatory notes, not relations.

---

## Definitions

Definitions describe the **local meaning of a term**.

Use this labeled format for project/domain glossaries when the extra labels add
clarity:

```md
- Canonical term : long form, expansion, or English/translated equivalent
  - Def. : short canonical definition
  - Project note : project-specific nuance, only if useful
  - Distinct from : terms often confused, only if useful
  - Avoid : terms, aliases, or shortcuts not to be used as canonical forms
```

Rules:

- keep definitions short, usually one sentence
- define what the term is, not every action it performs
- add project notes only when the project-specific nuance matters
- add distinctions only when confusion is probable
- add avoid-lists when alternatives could become unstable aliases
- do not maintain accepted aliases by default
- prefer one canonical form and list variants in avoid-lists
- for skill glossaries, prefer plain `### Term` sections with short paragraphs;
  do not force this labeled format

---

## Ambiguities

Flag unresolved terminology ambiguities with `0o0o`.

`0o0o` is the project marker for unresolved vocabulary decisions. It is chosen
because the string is unique enough to grep cleanly and visually distinct from
other status markers (`TODO`, `TBD`, `FIXME`) used for delivery follow-ups.
Preserve it; do not silently translate it to a different marker.

Use this format:

```md
- 0o0o <Term or family of terms>
  - Ambiguity : what is being conflated
  - Recommendation : proposed canonical form
  - Impact : documents, sections, decisions, or responsibilities affected
```

Only terminology ambiguities belong in this section.

If no unresolved terminology ambiguity exists, omit the section entirely. Do not
write empty sections, placeholder entries, or "none identified" sentences.

Do not use it for:

- project risks
- delivery status
- architecture decisions unrelated to terminology
- task tracking
- approval tracking
- open action items unrelated to vocabulary

If a temporary marker such as `0o0o`, `todo`, `tbd`, or `asd` already exists in
source material, preserve it unless the user explicitly authorizes removal or
resolution.

---

## Terms to Avoid

Use a global section when many non-canonical forms recur across the document:

```md
## Terms to avoid as canonical forms

- <form to avoid>
  - Use instead : <canonical form>
  - Reason : ambiguous, too generic, anglicism, overloaded, unstable shortcut
```

This section is optional. Use it when global cleanup is useful.

---

## Terminology Decisions

Use **Terminology decisions kept** only when the glossary contains
deliberate terminology choices that future editors must not undo casually.

Example:

```md
## Terminology decisions kept

- Client is not used as a canonical form because it conflates business role,
  technical consumer, and relying party
- Source system is preferred over source because source alone is too vague
```

This section is optional. Do not create it only to fill the template.

---

## Output Behavior

When producing a file:

- use Markdown
- use one H1 only
- prefer bullet lists over tables
- avoid tables by default
- use short lines when practical
- use the user's project language unless instructed otherwise
- preserve or extend numbered file conventions when present
- if no file name is given, use `00-project-glossary-<project>.md`

When revising an existing glossary:

- preserve canonical terms unless there is a clear reason to change them
- preserve visible `0o0o` markers unless the user explicitly authorizes resolving
  or removing them
- do not silently delete uncertain terminology
- report meaningful structural changes in the final response

---

## Quality Gate

Before finalizing, check:

- each canonical term is used consistently
- each relation connects at least two concepts
- each relation is structural rather than explanatory fluff
- each definition answers "what is it?"
- the glossary does not track project status
- terms to avoid are useful, not decorative
- official actors or domains are not redefined against their source document
- real unresolved terminology ambiguities are flagged with `0o0o`
- no empty `0o0o` section or "none identified" placeholder is present
- the document is scannable by expert readers
- Markdown headings are clean and stable

---

## Formatting Defaults

Use Markdown.

Prefer:

- short lines
- bullet lists
- plain canonical terms; avoid decorative bold
- `### Relations` before `### Definitions` for project/domain glossaries
- operational term groups for skill glossaries
- the user's project language

Avoid by default:

- Markdown tables
- inline HTML
- introductory or tutorial-style explanations
- example dialogues unless the user asks for them
- generic aliases accepted as normative shortcuts

---

## Gotchas

- `Global conceptual model` is not a domain. It is the project-wide conceptual map.
- `Relations` are not expanded definitions. They are model-level links.
- `Definitions` are not tutorials. They are canonical meanings.
- `0o0o` marks terminology ambiguity or unresolved vocabulary decisions.
- If there is no real `0o0o`, omit the unresolved terminology section entirely.
- A glossary is not a status register, task list, RAID log, or delivery tracker.
- If a project has an existing PBS, capability map, actor model, or architecture
  taxonomy, preserve that structure unless the user asks to redesign it.
- Do not create files when the user only asked to plan.
- Do not ask for confirmation when enough context exists to make a useful best
  effort; use `0o0o` for unresolved terminology ambiguity.
- Do not flatten all terms into one list when the project has official domains or
  natural conceptual families.
- Do not force project/domain structure onto skill glossaries.
- Do not let aliases become accepted shortcuts unless explicitly requested.

---

## Bundled References

A project glossary template is available at:

```text
references/glossary-template.md
```

A skill glossary template is available at:

```text
references/skill-glossary-template.md
```

A validation checklist is available at:

```text
references/quality-checklist.md
```

A worked example is available at:

```text
references/glossary-worked-example.md
```

A French business glossary template is available at:

```text
references/glossaire-metier-fr-template.md
```

An ACv4-derived format pattern is available at:

```text
references/acv4-format-pattern.md
```

Use the skill template for skill glossaries. Use the project template for
project, product, domain, capability, or architecture glossaries. Use the French
template for `glossaire métier` outputs. Use the ACv4 pattern only when deriving
structure from an ACv4-style business-analysis artifact. Use the checklist before
returning any generated/revised glossary. Read the worked example only when
expected format is unclear. Resolve paths relative to this skill directory; do
not hardcode agent-specific absolute paths.

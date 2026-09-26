# ACv4-derived glossary format pattern

Use this reference when the user asks to derive a glossary pattern from an
ACv4-style business-analysis artifact.

This is a format pattern, not a source of project terminology. Do not copy
ACv4-specific terms, actors, systems, rules, or decisions into another project
unless the target project is ACv4 or the user explicitly asks for that content.

---

## Pattern intent

The ACv4-style glossary is a canonical vocabulary map for expert project
readers. It stabilizes terms by combining:

- conceptual families
- high-level relations before definitions
- concise definitions with local project nuance
- terms to avoid
- priority writing rules
- preserved terminology decisions

It is useful when the glossary must support business analysis, architecture,
security, operations, governance, delivery, or compliance readers who already
know the domain but need stable language.

---

## Structural pattern

Use this order when the project benefits from the ACv4-style structure:

1. YAML frontmatter for name, description, tags, and dates
2. one H1 with the glossary title
3. conceptual sections grouped by the strongest real project structure
4. each conceptual section contains:
   - `### Relations`
   - `### Définitions`
5. final terminology control sections:
   - `## Règles générales d’écriture`
   - `## Règles terminologiques prioritaires`
   - `## Termes à ne pas utiliser comme formes canoniques`
   - `## Décisions terminologiques conservées`

The conceptual sections may be domains, bounded contexts, actor groups,
artifact families, lifecycle stages, governance areas, operational areas, or
other real project groupings. Do not invent a tidy taxonomy when the project
already has an approved one.

---

## Section pattern

Each conceptual section follows this shape:

```md
## <Famille conceptuelle>

### Relations

- <Concept A> <relation stable> <Concept B>
- <Concept C> ne remplace pas <Concept D>; il le complète, le consomme
  ou l’orchestre
- <Concept E> → <Concept F> → <Concept G> décrit <séquence
  structurelle>

### Définitions

- <Terme canonique> : <forme longue, expansion ou équivalent traduit>
  - Déf. : <définition canonique courte>
  - Note projet : <nuance propre au projet, seulement si utile>
  - À distinguer de : <termes souvent confondus, seulement si utile>
  - Éviter : <alias faibles, raccourcis, anglicismes ou formes ambiguës>
```

---

## Relation style

Relations describe the architecture of the vocabulary. A good relation:

- names at least two canonical concepts
- expresses a stable structural link
- reduces confusion between neighboring terms
- remains true even if a definition is rewritten
- does not become a process step or requirement statement

Prefer relation verbs that encode stable structure, such as:

- regroupe
- gouverne
- signe
- émet
- valide
- publie
- protège
- orchestre
- expose
- consomme
- remplace / ne remplace pas

Use arrows only when order or chain structure matters:

```md
- <Concept A> → <Concept B> → <Concept C> décrit <chaîne ou parcours>
```

---

## Definition style

Definitions describe local meaning. They are not tutorials.

Use:

- Déf. for the short canonical definition
- Note projet for local nuance that affects usage
- À distinguer de when confusion is probable
- Éviter for weak aliases, generic shortcuts, anglicisms, or overloaded forms

Avoid:

- accepted alias lists by default
- definitions that repeat every relation
- implementation detail with no project-level meaning
- actor responsibility models when a canonical actor document already exists
- project status, approval state, or delivery follow-up

---

## Final control sections

### Règles générales d’écriture

Use for rules that apply across the whole glossary, such as acronym expansion,
language preference, exact actor naming, or generic terms that must be qualified.

### Règles terminologiques prioritaires

Use for high-risk wording rules that future writers are likely to violate.
Number them only when the rules are stable and worth preserving.

```md
### R1 — <Terme ou formulation à contrôler>

- Règle : <rule>
- À écrire : <canonical forms>
- À éviter : <forms to avoid>
```

### Termes à ne pas utiliser comme formes canoniques

Use when non-canonical forms recur across the project and need a global
replacement map.

```md
- <Forme à éviter>
  - Remplacer par : <forme canonique>
  - Raison : <why this form is unstable>
```

### Décisions terminologiques conservées

Use when a terminology choice should survive future editing. Keep decisions
short and tied to the glossary, not to delivery governance.

---

## Derivation guardrails

When deriving from an existing artifact:

1. extract the structure first; do not start by copying terms
2. identify which headings are project-specific and which are reusable
3. preserve canonical source names for actors, systems, roles, domains, and
   taxonomies
4. convert project-specific examples into placeholders when building a template
5. keep only rules that generalize to glossary quality
6. move unresolved terminology issues to `0o0o` instead of smoothing them over
7. do not backfill missing sections just for symmetry

The goal is to reuse the ACv4 shape: conceptual families, relations,
definitions, avoidance rules, and preserved terminology decisions. The content
belongs to the target project.

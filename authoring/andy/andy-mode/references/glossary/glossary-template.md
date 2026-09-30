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

This glossary stabilizes the business vocabulary of project <Project>.

It serves to:

- avoid ambiguity in deliverables
- protect canonical forms
- clarify relations between concepts
- document terms to avoid
- support a shared reading across business, IT, architecture, security,
  operations, and delivery experts

It does not serve to:

- track the status of a deliverable
- track approval of a decision
- replace actor, requirement, process, or architecture documents

---

## Reading conventions

- terms at the start of glossary entries are canonical forms
- `Relations` sections describe the conceptual model
- `Definitions` sections describe the local meaning of terms
- terms under Avoid are not normative aliases
- `0o0o` markers flag unresolved terminology ambiguities

---

## Global conceptual model

### Relations

- <Concept A> <stable relation> <Concept B>
- <Concept B> does not replace <Concept C>; it complements, consumes, or orchestrates it
- <Concept D> → <Concept E> → <Concept F> describes <structural sequence>

### Definitions

- <Concept A> : <long form, expansion, or translated equivalent>
  - Def. : <short canonical definition>
  - Project note : <project-specific nuance, only if useful>
  - Distinct from : <terms often confused, only if useful>
  - Avoid : <terms, aliases, or shortcuts not to be used>

---

## <Domain, bounded context, capability, or conceptual family>

### Relations

- <Concept A> <stable relation> <Concept B>
- <Concept C> produces 1+ <Concept D> under <rule or context>
- <Concept E> validates <Concept F> before <Concept G> consumes it

### Definitions

- <Canonical term> : <long form, expansion, or translated equivalent>
  - Def. : <short canonical definition>
  - Project note : <project-specific nuance, only if useful>
  - Distinct from : <terms often confused, only if useful>
  - Avoid : <terms, aliases, or shortcuts not to be used>

---

## Terms to avoid as canonical forms

- <form to avoid>
  - Use instead : <canonical form>
  - Reason : <ambiguous, too generic, anglicism, overloaded, or unstable shortcut>

---

## Terminology decisions kept

- <Decision> : <reason for keeping this form or this distinction>

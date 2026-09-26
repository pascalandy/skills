---
name: people-investigation
description: Ethical public-source people investigations for locating someone, mapping a public footprint, running reverse lookups, and verifying identity with confidence scoring. USE WHEN find person, locate someone, reconnect, people search, social media search, person public records, people public records search, map public footprint, reverse lookup, phone lookup, email lookup, username lookup, image lookup, verify identity, background on person.
---

# People Investigation

## Core Concept

This sub-skill handles investigations where the target is a person. It starts from a subject profile, collects evidence from public sources, and only treats a match as reliable when multiple independent identifiers agree.

Hard boundaries:

- Publicly accessible information only.
- No impersonation, pretexting, credential use, stalking, or harassment.
- Stop if the user intent is coercive, invasive, or otherwise illegitimate.

Before starting any workflow, verify authorization per `references/EthicalFramework.md` (shared reference at the meta-skill level). Apply the confidence and reporting standards from `references/Methodology.md`.

## Workflow Routing

| Intent | Workflow |
|---|---|
| find person, locate someone, reconnect, background on person | `workflows/FindAndVerifyPerson.md` |
| social media search, person public records, people public records search, map public footprint | `workflows/PublicFootprint.md` |
| reverse lookup, phone lookup, email lookup, username lookup, image lookup | `workflows/ReverseLookup.md` |

## Method

1. Confirm the purpose is legitimate and the scope is explicit.
2. Build the subject profile from the identifiers already known.
3. Search across independent public-source families: directories, professional profiles, public records, social platforms, and search engines.
4. Resolve ambiguity by comparing identifiers, timeline consistency, and associates.
5. Report confidence clearly and separate verified findings from leads.

## Output Format

Use this structure in the final answer:

```text
Objective
Known identifiers
Sources checked
Candidate matches
Verified findings
Unverified leads
Confidence assessment
Recommended next public-source step
```

## Examples

```text
User: find my old roommate from Denver and make sure it is the right person
Route: workflows/FindAndVerifyPerson.md
```

```text
User: reverse lookup this email address
Route: workflows/ReverseLookup.md
```

```text
User: map this person's public footprint before outreach
Route: workflows/PublicFootprint.md
```

## References

| File | Purpose |
|---|---|
| `references/SourcesAndTools.md` | People search engines, username tools, email/phone/image lookup, public records, and tool selection by scenario |
| `../EthicalFramework.md` | Shared authorization, legal, and ethical requirements |
| `../Methodology.md` | Shared source hierarchy, confidence scoring, and reporting standards |

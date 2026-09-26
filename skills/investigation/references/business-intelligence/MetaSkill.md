---
name: business-intelligence
description: Public-source company and organization investigation for company lookup, vendor due diligence, leadership review, nonprofit research, and business-risk assessment. USE WHEN company intel, company lookup, business background, leadership review, due diligence, vendor vetting, investment review, go or no-go recommendation, business investigation, organization research, nonprofit research, association research, academic research, government body research.
---

# Business Intelligence

## Core Concept

This sub-skill handles investigations where the target is a company, nonprofit, government body, association, or other organization. It combines legal-entity validation, leadership review, market and reputation research, and risk synthesis.

Boundaries:

- Public sources only.
- Confirm the business purpose and the decision this research supports.
- Use this skill for organization-level questions.
- Route person-centric work to `people-investigation`.
- Route deep domain, IP, URL, or IOC analysis to `infrastructure-intel`.

Before starting any workflow, verify authorization per `references/EthicalFramework.md` (shared reference at the meta-skill level). Apply the confidence and reporting standards from `references/Methodology.md`.

## Workflow Routing

| Intent | Workflow |
|---|---|
| company intel, business background, leadership review | `workflows/CompanyLookup.md` |
| due diligence, vendor vetting, investment review, go or no-go recommendation | `workflows/CompanyDueDiligence.md` |
| nonprofit research, association research, academic research, government body research | `workflows/OrganizationLookup.md` |

## Method

1. Confirm the target entity and the decision the investigation must support.
2. Resolve official names, aliases, jurisdictions, and known domains.
3. Gather evidence across legal, financial, leadership, market, technical, and reputational source families.
4. Separate verified facts, allegations, and unknowns.
5. End with a decision-ready summary tied to risk.

## Output Format

Use this structure in the final answer:

```text
Decision context
Entity summary
Leadership and ownership
Operational and market signals
Legal and regulatory findings
Technical surface summary from known company assets
Key risks
Open questions
Recommendation
```

## Examples

```text
User: give me company intel on Northstar Labs
Route: workflows/CompanyLookup.md
```

```text
User: do due diligence on this vendor before procurement signs
Route: workflows/CompanyDueDiligence.md
```

```text
User: research this nonprofit and its board
Route: workflows/OrganizationLookup.md
```

## References

| File | Purpose |
|---|---|
| `references/SourcesAndTools.md` | Business registries, financial databases, legal records, sanctions, competitive intelligence, and nonprofit sources |
| `../EthicalFramework.md` | Shared authorization, legal, and ethical requirements |
| `../Methodology.md` | Shared source hierarchy, confidence scoring, and reporting standards |

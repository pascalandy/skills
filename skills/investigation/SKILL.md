---
name: "investigation"
description: "Explicitly triggered when the user mentions `investigation`."

---

# Investigation

> One entry point for public-source investigations. router dispatches to right specialist for people, business, or infrastructure work based on request itself.

## Routing

Load `references/ROUTER.md` to determine which sub-skill handles this request.

## The Problem

Investigation requests sound similar at surface but need different methods once you start working. person-locate request needs identity resolution and confidence scoring. vendor vetting request needs legal, market, and leadership review. suspicious domain request needs DNS, infrastructure, and threat pivots. When all of that lives in one undifferentiated skill, result is noisy routing, overlapping instructions, and too much context loaded for simple tasks.

Common failure modes:

- assistant mixes people-search tactics into business or infrastructure work
- High-level skill docs become unreadable because routing and execution instructions are jammed together
- New specialties are hard to add without touching unrelated guidance
- user has to know internal skill names instead of describing outcome they want

## The Solution

This meta-skill applies progressive disclosure to investigation work:

1. `SKILL.md` is user-facing collection and single entry point.
2. `references/ROUTER.md` contains minimal dispatch table.
3. router selects one of three standalone sub-skills with non-overlapping domains.

Sub-skills in this collection:

1. `people-investigation` for ethical people-finding, public footprint analysis, and reverse lookups.
2. `business-intelligence` for company research, vendor vetting, and organization due diligence.
3. `infrastructure-intel` for domains, IPs, URLs, technical entities, and source discovery.

Each sub-skill also works if loaded directly, but normal path is through router.

## What's Included

| Component | Path | Purpose |
|---|---|---|
| Collection entry point | `SKILL.md` | User-facing docs, framing, examples, and router bridge |
| Router | `references/ROUTER.md` | Minimal request-pattern dispatch table |
| Ethical framework | `references/EthicalFramework.md` | Shared authorization, legal, and ethical requirements for all sub-skills |
| Methodology | `references/Methodology.md` | Shared source hierarchy, confidence scoring, verification, and reporting standards |
| people-investigation sub-skill | `references/people-investigation/MetaSkill.md` | Person-focused investigation methodology |
| People sources | `references/people-investigation/references/SourcesAndTools.md` | People search engines, username tools, email/phone/image lookup catalog |
| People workflow | `references/people-investigation/workflows/FindAndVerifyPerson.md` | Full person search with verification |
| People workflow | `references/people-investigation/workflows/PublicFootprint.md` | Social, public-record, and profile mapping |
| People workflow | `references/people-investigation/workflows/ReverseLookup.md` | Phone, email, username, and image pivots |
| business-intelligence sub-skill | `references/business-intelligence/MetaSkill.md` | Company and organization research methodology |
| Business sources | `references/business-intelligence/references/SourcesAndTools.md` | Business registries, financial databases, sanctions, competitive intelligence catalog |
| Business workflow | `references/business-intelligence/workflows/CompanyLookup.md` | Fast company intelligence baseline |
| Business workflow | `references/business-intelligence/workflows/CompanyDueDiligence.md` | Structured vendor or investment vetting with domain-first protocol |
| Business workflow | `references/business-intelligence/workflows/OrganizationLookup.md` | Nonprofit, association, academic, and government research |
| infrastructure-intel sub-skill | `references/infrastructure-intel/MetaSkill.md` | Technical entity and infrastructure methodology |
| Infrastructure sources | `references/infrastructure-intel/references/SourcesAndTools.md` | DNS, IP, threat intel, malware analysis, vulnerability databases catalog |
| Infrastructure workflow | `references/infrastructure-intel/workflows/DomainLookup.md` | Domain, DNS, certificate, subdomain, and hosting analysis |
| Infrastructure workflow | `references/infrastructure-intel/workflows/EntityLookup.md` | IP, URL, hash, IOC, and threat-entity investigation |
| Infrastructure workflow | `references/infrastructure-intel/workflows/DiscoverSources.md` | Find and qualify new public-source resources for niche case |

## Invocation Scenarios

| Trigger Phrase | What Happens |
|---|---|
| "find my old coworker from Austin" | Routes to `people-investigation` and uses `FindAndVerifyPerson.md` |
| "reverse lookup this phone number" | Routes to `people-investigation` and uses `ReverseLookup.md` |
| "map this person's public footprint" | Routes to `people-investigation` and uses `PublicFootprint.md` |
| "company intel on Acme" | Routes to `business-intelligence` and uses `CompanyLookup.md` |
| "do vendor due diligence on this startup" | Routes to `business-intelligence` and uses `CompanyDueDiligence.md` |
| "research this nonprofit" | Routes to `business-intelligence` and uses `OrganizationLookup.md` |
| "investigate suspicious-site.com" | Routes to `infrastructure-intel` and uses `DomainLookup.md` |
| "analyze this IOC" | Routes to `infrastructure-intel` and uses `EntityLookup.md` |
| "find new sources for maritime OSINT" | Routes to `infrastructure-intel` and uses `DiscoverSources.md` |

## Example Usage

### People Investigation

```text
User: find my former classmate Sarah Kim from Seattle and verify it is the right person

Assistant:
Routes to people-investigation.
Runs FindAndVerifyPerson.
Builds the subject profile, gathers public-source candidates, compares independent identifiers, and returns ranked matches with a confidence score.

Output excerpt:

Objective: Reconnect with former classmate
Candidate matches: 3
Verified findings: 1 strong match with school, city, and employer alignment
Confidence assessment: High
Recommended next public-source step: Confirm through one additional independent profile
```

### Business Due Diligence

```text
User: do due diligence on Northstar Labs before we sign the contract

Assistant:
Routes to business-intelligence.
Runs CompanyDueDiligence.
Checks registrations, leadership, market signals, legal issues, technical footprint, and produces a risk summary with unresolved questions.

Output excerpt:

Decision to support: Vendor onboarding
Verified positives: Active registration, consistent leadership history, credible customer references
Material risks: One unresolved lawsuit and limited security transparency
Verdict: Proceed with conditions
```

### Infrastructure Intelligence

```text
User: investigate the domain suspicious-site.com and related infrastructure

Assistant:
Routes to infrastructure-intel.
Runs DomainLookup.
Collects WHOIS, DNS, certificate, hosting, and reputation evidence, then pivots to related infrastructure with confidence notes.

Output excerpt:

Seed entity: suspicious-site.com
Classification: Domain
Infrastructure facts: 14 subdomains, Cloudflare fronting, recent certificate rotation
Reputation and threat signals: Mixed, one reputation source flags abuse and two remain inconclusive
Recommended next step: Review related IP infrastructure for corroboration
```

## Customization

No config required.

Optional customization points:

| Customization | File | Effect |
|---|---|---|
| Routing keywords | `references/ROUTER.md` | Expand or narrow intent matching |
| People reporting style | `references/people-investigation/MetaSkill.md` | Adjust confidence language or output structure |
| Business risk thresholds | `references/business-intelligence/workflows/CompanyDueDiligence.md` | Tune verdict criteria |
| Infrastructure pivot depth | `references/infrastructure-intel/MetaSkill.md` | Change how aggressively workflow broadens from seed entity |

## Shared References

Two shared refs apply across all sub-skills:

- `references/EthicalFramework.md` -- Authorization checklist, legal considerations by domain, ethical boundaries, proportionality test, data handling, escalation procedures, and red lines. Every workflow must verify authorization before starting
- `references/Methodology.md` -- Intelligence cycle, source hierarchy (Tier 1-4), multi-source verification thresholds, confidence levels (High/Medium/Low/Speculative), red flag classification, reporting standards, and quality gates

Each sub-skill also has its own `references/SourcesAndTools.md` with domain-specific tool and source catalogs.

## Design Notes

- Single entry point: user invokes `investigation`, not sub-skill name
- Invisible delegation: routing happens through `references/ROUTER.md`
- No domain overlap: each sub-skill owns separate investigation surface
- Additive scaling: new specialty only needs one new directory and one new router row
- Harness agnostic: no assistant-specific paths, tools, or dependencies. Relative paths only

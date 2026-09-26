---
name: infrastructure-intel
description: Public-source technical investigation for domains, IPs, URLs, hashes, infrastructure relationships, threat signals, and discovery of new investigation sources. USE WHEN domain lookup, DNS review, subdomain discovery, hosting analysis, infrastructure mapping, IP investigation, URL investigation, hash lookup, threat intel, IOC analysis, technical entity investigation, discover sources, niche OSINT sources, research new tools for a technical case.
---

# Infrastructure Intel

## Core Concept

This sub-skill handles investigations where the seed is a technical entity or a technical footprint. It classifies the seed, gathers passive evidence first, pivots through infrastructure relationships, and distinguishes confirmed facts from reputation or attribution claims.

Boundaries:

- Public sources and passive collection first.
- Only go beyond passive analysis when the request explicitly authorizes deeper probing.
- Keep infrastructure facts separate from business recommendations and person-level identification.
- Route organization-level vetting to `business-intelligence`.
- Route people work to `people-investigation`.

Before starting any workflow, verify authorization per `references/EthicalFramework.md` (shared reference at the meta-skill level). Apply the confidence and reporting standards from `references/Methodology.md`.

## Workflow Routing

| Intent | Workflow |
|---|---|
| domain lookup, DNS review, subdomain discovery, hosting analysis | `workflows/DomainLookup.md` |
| IP investigation, URL investigation, IOC analysis, threat intel, hash lookup | `workflows/EntityLookup.md` |
| discover sources, niche OSINT sources, research new tools for a technical case | `workflows/DiscoverSources.md` |

## Method

1. Classify the seed entity and normalize it.
2. Prefer passive collection before any active probing.
3. Pivot through DNS, WHOIS, certificates, hosting, related domains, and threat references.
4. Keep infrastructure facts separate from attribution claims.
5. Return a map of relationships, risks, and confidence.

## Output Format

Use this structure in the final answer:

```text
Seed entity
Classification
Infrastructure facts
Reputation and threat signals
Related entities and pivots
Confidence and caveats
Recommended next step
```

## Examples

```text
User: investigate suspicious-site.com and related subdomains
Route: workflows/DomainLookup.md
```

```text
User: analyze this IP and tell me if it is malicious
Route: workflows/EntityLookup.md
```

```text
User: find better public sources for maritime threat intelligence
Route: workflows/DiscoverSources.md
```

## References

| File | Purpose |
|---|---|
| `references/SourcesAndTools.md` | DNS, IP, threat intel, malware analysis, vulnerability databases, dark web monitoring, and OSINT meta-resources |
| `../EthicalFramework.md` | Shared authorization, legal, and ethical requirements |
| `../Methodology.md` | Shared source hierarchy, confidence scoring, and reporting standards |

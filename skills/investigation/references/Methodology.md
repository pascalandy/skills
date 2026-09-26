# Investigation Methodology

Shared methodology that applies across all investigation sub-skills. Covers the intelligence cycle, source hierarchy, verification standards, confidence scoring, and reporting requirements.

## Intelligence Cycle

```
Planning -> Collection -> Processing -> Analysis -> Dissemination
    ^                                                    |
    +----------------------------------------------------+
```

- **Planning**: Define objectives, scope, and requirements.
- **Collection**: Gather raw data from public sources.
- **Processing**: Organize, deduplicate, and normalize collected data.
- **Analysis**: Extract meaning, identify patterns, assess confidence.
- **Dissemination**: Report findings with sources and caveats.

## Source Hierarchy

### Tier 1: Primary Sources

Official registries, court records, government databases, company filings. Highest reliability.

### Tier 2: Verified Secondary

Established news outlets, academic publications, industry reports, professional databases (Crunchbase, LinkedIn).

### Tier 3: Community and Social

Social media profiles, forum discussions, review sites, crowdsourced data. Useful but requires corroboration.

### Tier 4: Technical

DNS records, WHOIS data, certificate transparency logs, internet scanning platforms. Factual but context-dependent.

Always prefer higher-tier sources. When citing Tier 3 or 4 sources, note the reliability limitation.

## Multi-Source Verification

| Claim Importance | Minimum Independent Sources |
|---|---|
| Critical (drives the decision) | 3+ |
| Important (shapes the recommendation) | 2+ |
| Supporting (adds context) | 1 verifiable source |

Independence means different organizations, different collection methods, and ideally different time periods.

## Confidence Levels

### High (80-100%)

Multiple independent confirmations. Official source verification. No contradicting evidence.

### Medium (50-79%)

Some supporting evidence. Limited independent confirmation. Credible but single-source for key claims. Minor contradictions explained.

### Low (20-49%)

Single unverified source. Circumstantial evidence. Significant gaps. Some contradictions present.

### Speculative (below 20%)

Inference only. No direct evidence. Conflicting information. Pattern matching without confirmation.

Always state the confidence level for each significant finding.

## Red Flag Classification

| Severity | Definition | Examples |
|---|---|---|
| Critical | Investigation blocker or deal-breaker | Fraud indicators, regulatory violations, misrepresentation of material facts |
| High | Significant concern requiring resolution | Missing registrations, unverifiable claims, transparency failures |
| Medium | Worth noting in the report | Minor discrepancies, limited online presence, industry-standard risks |
| Low | Monitor only | Minor gaps, normal business risks |

## Reporting Standards

Every investigation report must include:

1. **Scope statement**: Authorization reference, target definition, information types, time period.
2. **Methodology**: Sources consulted, search terms, techniques used, limitations encountered.
3. **Findings**: Clearly labeled as fact, claim, or inference. Source citation for each. Confidence level assigned. Verification status noted.
4. **Caveats**: Information gaps, unverified claims, potential biases, currency of information.
5. **Recommendation**: Actionable next steps tied to the original objective.

## Quality Gates

Before moving to the next phase of any investigation:

- [ ] All required techniques for this phase executed.
- [ ] Confidence threshold met for key claims.
- [ ] Gaps documented explicitly.
- [ ] Red flags noted and classified.
- [ ] Multi-source verification complete where required.

If the quality gate fails: document gaps, run additional collection, reassess, and proceed only when the threshold is met or limitations are explicitly acknowledged.

## Parallel Research

When an investigation calls for broad coverage, deploy multiple independent research threads simultaneously across different source families. Benefits:

- Faster collection.
- Diverse perspectives reduce blind spots.
- Built-in cross-verification from independent findings.
- Redundant coverage if one source family is thin.

Combine results after all threads complete. Deduplicate and resolve conflicts before reporting.

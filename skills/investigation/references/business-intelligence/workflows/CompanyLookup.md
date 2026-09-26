# Company Lookup

Use this workflow for a fast but structured baseline on a commercial entity.

## Steps

1. Resolve the entity.
Capture the official company name, aliases, DBAs, jurisdiction, primary website, sector, known leadership, and geographic location.

2. Validate legal existence.
Check business registries, filings, and authoritative records to confirm status.

| Source Family | What to Check |
|---|---|
| Business registries | OpenCorporates, state Secretary of State filings, foreign qualifications |
| Federal registrations | SEC EDGAR if publicly traded, SAM.gov for government contractor status |
| Regulatory registrations | Industry-specific licenses, professional certifications, securities registrations |

3. Map the operating surface.
Identify all domains, product pages, leadership pages, investor or customer materials, hiring pages, and public documentation. Use multiple discovery techniques:

- Certificate transparency (crt.sh) for subdomains.
- Social media bios for linked domains.
- Business registration website fields.
- Related TLD checking (.com, .net, .io, .partners, .capital).

4. Review leadership and ownership.
Look for founders, executives, board members, ownership signals, and overlapping entities.

| Source | What It Provides |
|---|---|
| LinkedIn (Google x-ray) | Career histories, professional credentials |
| OpenOwnership, GLEIF LEI | Beneficial ownership and corporate structure |
| OpenCorporates | Corporate officer filings across jurisdictions |
| USPTO, Google Patents | IP portfolio and inventor associations |

5. Review external signals.
Gather public reporting across multiple dimensions:

- **Financial**: Crunchbase (funding), PitchBook (valuations), D&B (credit ratings).
- **Legal**: PACER and CourtListener (lawsuits, regulatory actions, bankruptcy).
- **Sanctions**: OFAC, EU Sanctions Map, OpenSanctions.
- **Reputation**: Google News, GDELT (media coverage), Glassdoor (employee sentiment).
- **Competitive**: SimilarWeb (traffic), SEMrush (search visibility), Owler (competitor tracking).
- **Technology**: BuiltWith, Wappalyzer (tech stack and security posture).

6. Summarize the baseline.
Provide what is verified, what is only claimed by the company, and what still needs deeper vetting.

## Quality Gates

Before finalizing:

- [ ] Business registration verified in at least one authoritative registry.
- [ ] Leadership backgrounds checked.
- [ ] Multi-source verification (2+ sources) for key claims.
- [ ] Red flags noted and classified per the shared Methodology.

## Deliverable

Return a concise company profile with verified facts, source-backed claims, and the main areas that require deeper due diligence.

```text
Entity summary (name, jurisdiction, sector, domains)
Registration and legal status
Leadership and ownership
Operating surface and technology
Financial and market signals
Legal and regulatory findings
Key risks and red flags
Open questions for deeper investigation
```

# Company Due Diligence

Use this workflow when the user needs a decision-oriented risk assessment for a vendor, partner, acquisition target, or investment prospect.

## Steps

1. Define the decision.
State the exact decision to support: sign the contract, onboard the vendor, invest, acquire, or continue monitoring.

2. Run the domain-first baseline.
Domain discovery is the mandatory first phase and blocks all subsequent work. Missing domains creates blind spots (e.g., investor-facing portals on alternative TLDs like .partners or .capital).

Execute these enumeration techniques:

- Certificate transparency (crt.sh, CertStream).
- DNS enumeration (SecurityTrails, DNSDumpster).
- Search engine discovery.
- Social media bio link extraction.
- Business registration website fields.
- WHOIS reverse lookup (registrant email or name correlation).
- Related TLD checking (.com, .net, .io, .partners, .capital, .fund).

Quality gate: 95%+ confidence that all domains are found before proceeding.

3. Gather risk evidence across six buckets.

**Legal and regulatory status**:
- Business registrations (OpenCorporates, SEC EDGAR, state filings).
- Sanctions screening (OFAC, EU Sanctions, OpenSanctions).
- Court records (PACER, CourtListener, UniCourt).
- Government contractor status (SAM.gov, USAspending).
- Regulatory enforcement actions.

**Leadership and ownership credibility**:
- Executive backgrounds (LinkedIn, ZoomInfo).
- Board composition and credentials.
- Corporate ownership structure (OpenOwnership, GLEIF LEI).
- Cross-board memberships and potential conflicts.
- Credential verification against issuing bodies.

**Financial and market signals**:
- Funding history (Crunchbase, PitchBook, Dealroom).
- Credit ratings (D&B).
- Revenue signals and financial trajectory.
- Competitive positioning (SimilarWeb, SEMrush, Owler).
- Employee count and hiring velocity as growth proxies.

**Customer and reputation signals**:
- Media coverage analysis: earned vs. paid (GDELT, MediaCloud, Google News).
- Customer reviews (G2, Trustpilot, BBB).
- Employee sentiment (Glassdoor).
- Industry recognition and analyst mentions.

**Technical and security posture**:
- Technology stack (BuiltWith, Wappalyzer, Netcraft).
- Security records (SPF, DKIM, DMARC on email domains).
- Breach exposure (Have I Been Pwned, Intelligence X).
- Threat intelligence (VirusTotal, URLScan.io for company domains).
- Infrastructure exposure (Shodan, Censys for company IPs).

**Claims verification**:
- Cross-reference revenue claims against SEC filings, press releases, and employee estimates.
- Verify customer claims against case studies and independent references.
- Verify partnership claims against partner directories and joint announcements.
- Check education and credential claims for leadership.

4. Investigate red flags.
Any inconsistency, lawsuit, sanction, false claim, hidden entity relationship, or major security issue moves from note to explicit risk item. Classify each per the shared Methodology:

- **Critical**: Fraud indicators, regulatory violations, misrepresentation.
- **High**: Missing registrations, unverifiable claims, transparency failures.
- **Medium**: Minor discrepancies, limited presence, industry-standard risks.
- **Low**: Minor gaps, normal business risks.

5. Classify the result.
Use one of these verdicts:

- **Proceed**: No material risks found.
- **Proceed with conditions**: Risks identified but manageable with specific mitigations.
- **Hold pending answers**: Unresolved questions that could change the decision.
- **Decline**: Material risks that cannot be mitigated.

6. Explain the verdict.
Tie the recommendation directly to evidence and note which unanswered questions could still change the decision.

If the decision depends on deeper infrastructure analysis, route that part to `references/infrastructure-intel/MetaSkill.md` after the business-level assessment is complete.

## Deliverable

Return a report with these sections:

```text
Decision to support
Entity summary
Domain-first baseline (domains discovered, confidence level)
Verified positives
Material risks (classified by severity)
Unresolved questions
Verdict
Reasoning for verdict
Recommended conditions or next steps
```

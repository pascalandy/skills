# Organization Lookup

Use this workflow for nonprofits, associations, academic institutions, foundations, government bodies, and other non-commercial organizations.

## Steps

1. Classify the organization type.
Determine whether the target is a nonprofit, government entity, association, school, foundation, or international body. Each has different registries and disclosure patterns:

| Type | Primary Registries | Key Financial Sources |
|---|---|---|
| US Nonprofit (501c3/4) | IRS, state AG, Secretary of State | IRS 990 via ProPublica, annual reports |
| Government agency | SAM.gov, agency org charts | USAspending, budget documents |
| Academic institution | NCES, accreditation bodies | IRS 990 (if private), endowment reports |
| International NGO | UN ECOSOC, country registrations | Annual reports, donor disclosures |
| Foundation | IRS (990-PF for private foundations) | 990-PF grant listings |
| Trade association | IRS (501c6), state registrations | IRS 990, membership disclosures |

2. Confirm official identity.
Collect the legal name, aliases, jurisdiction, founding date, mission, EIN or tax ID (for US nonprofits), and official web properties.

**Nonprofit-specific verification**:
- IRS tax-exempt status (IRS Select Check).
- IRS 990 filings (ProPublica Nonprofit Explorer).
- State charity registration (state AG database).
- GuideStar/Candid profile and transparency seal.
- Charity Navigator rating.

**Government-specific verification**:
- Agency org chart and statutory authority.
- SAM.gov entity registration.
- Inspector General reports.

**Academic-specific verification**:
- Accreditation status via regional or national accreditor databases.
- NCES data (enrollment, graduation rates, finances).
- Research funding (NSF Award Search, NIH Reporter).

3. Review governance.
Map board members, executives, trustees, oversight bodies, and visible conflicts of interest.

- Board composition: independence, diversity, expertise, cross-board memberships.
- Executive leadership: background via LinkedIn, compensation from IRS 990 Part VII, tenure and turnover.
- Key staff: program directors, published expertise, media appearances.

4. Review funding and transparency.

**Revenue sources (from IRS 990 if available)**:
- Program service revenue.
- Government grants and contracts (USAspending, GovTribe).
- Private donations and fundraising.
- Investment income.
- Foundation grants received (Foundation Directory).

**Expense analysis**:
- Program expenses vs. administrative vs. fundraising.
- Program efficiency ratio (greater than 75% to programs is generally good).
- Executive compensation relative to budget.
- Related-party transactions.

**Financial health indicators**:
- Revenue trend over 3-5 years.
- Reserve to expense ratio.
- Funding source diversification.
- Audit findings if available.

5. Review accountability signals.
Check for legal actions, sanctions, inspector reports, audits, controversies, and public criticism while separating evidence from rumor.

| Source | What to Check |
|---|---|
| PACER, CourtListener | Lawsuits and regulatory actions |
| OFAC, OpenSanctions | Sanctions and watchlists |
| OIG exclusion lists | Government exclusions |
| State AG enforcement | Charity enforcement actions |
| BBB Wise Giving Alliance | Charity accountability standards |
| Google News, GDELT | Controversies and investigative reporting |

6. Summarize fit-for-purpose findings.
Tailor the summary to what the user needs to decide: partnership, grantmaking, reputational review, or background research.

## Risk Indicators

| Level | Indicators |
|---|---|
| Low | Active registration, transparent 990s, strong ratings, diverse funding, established leadership |
| Moderate | Limited transparency, new organization, concentrated funding, high admin costs |
| High | Revoked status, regulatory actions, opaque finances, leadership turnover, mission creep |
| Critical | Sanctions match, fraud indicators, shell organization patterns, fictitious programs |

## Deliverable

Return the organization's profile structured as:

```text
Organization type and mission
Registration and legal status
Leadership and governance
Funding model and financial health (with trend)
Transparency level
Accountability signals and controversies
Risk assessment
Biggest unresolved questions
Recommendation for the user's stated purpose
```

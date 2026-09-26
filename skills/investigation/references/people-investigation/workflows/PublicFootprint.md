# Public Footprint

Use this workflow when the user wants to map a person's public-facing presence without running a full locate investigation.

## Steps

1. Start from the strongest known identifier.
Use the name, employer, school, city, username, or domain already known.

2. Separate source families.
Check each bucket independently so gaps and coverage are visible:

**Professional presence**:
- LinkedIn (direct search or Google x-ray: `site:linkedin.com/in "[Name]" "[City]"`).
- Company websites, industry publications, conference speaker lists.
- Patent searches (USPTO) and professional license boards.
- OpenCorporates for corporate officer filings.

**Social platforms**:
- Facebook, Instagram, Twitter/X, TikTok via Google x-ray searches.
- Username enumeration if a handle is discovered (Sherlock, WhatsMyName, Namechk).
- Email-to-account mapping if an email is known (Holehe, Epieos).

**Publications and public mentions**:
- Google Scholar, ResearchGate, ORCID for academic output.
- News mentions via Google News search.
- Blog authorship, forum participation, public speaking.

**Public records**:
- Voter registration (where publicly accessible).
- Property records via county assessor.
- Court records (PACER, CourtListener).
- Business filings (Secretary of State).

**General web mentions**:
- Google search with name in quotes plus known context.
- Google dorking: `"[Name]" "[Employer]"`, `"[Name]" site:[known domain]`.

3. Capture only what is public and relevant.
Focus on profile URLs, visible biography details, location clues, employer history, public posts, board memberships, publications, and official records that fit the scope.

4. Cross-reference the identity.
Treat a profile as tentative until it lines up with other known identifiers such as city, school, employer, or timeline. Check for:
- Photo consistency across platforms.
- Bio consistency (similar job titles, locations, descriptions).
- Connection overlap (do friends or followers match expected network).
- Content themes (similar interests and posting patterns).

5. Summarize the footprint.
Group findings by source family and call out gaps, contradictions, or weak matches.

## Deliverable

Return a compact map with these sections:

```text
Professional profiles
Social profiles
Public records
Public mentions and publications
Identity confidence
Open questions
```

Note which source families returned nothing (a gap) versus which were not checked (a limitation).

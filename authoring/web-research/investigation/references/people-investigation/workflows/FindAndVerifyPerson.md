# Find And Verify Person

Use this workflow when the user wants a full people search, a reconnection attempt, or a ranked set of candidate matches.

## Steps

1. Define the goal.
Ask for the person's name, known aliases, last known location, approximate age, school, employer, old contact details, and how the user knows them. Build a subject profile:

```text
Name: [full name]
Aliases/Variations: [maiden name, nicknames, spelling variants]
Age/DOB: [approximate or exact]
Last Known Location: [city, state]
Connection Context: [how the user knows them]
Last Contact: [year or timeframe]
Known Associates: [family, friends, colleagues]
Additional Identifiers: [old phone, email, employer, school]
```

2. Check the intent.
Confirm the request is for a legitimate purpose. Stop if the goal sounds coercive, stalking-related, or invasive. Verify authorization per the shared EthicalFramework.

3. Build the subject profile.
Capture the known identifiers in one profile so every later match can be compared against the same baseline.

4. Collect candidates from public sources.
Search across multiple independent source families simultaneously. Cover:

- **People search aggregators**: TruePeopleSearch, FastPeopleSearch, Spokeo, BeenVerified, WhitePages, That's Them.
- **Professional profiles**: LinkedIn via Google x-ray search (`site:linkedin.com/in "[Name]" "[City]"`), company directories.
- **Social platforms**: Facebook, Instagram, Twitter/X, TikTok via Google x-ray searches.
- **Public records**: Voter registration, property records (county assessor), court records (PACER, CourtListener), business filings (Secretary of State).
- **Search engines**: Google dorking (`"[Name]" "[Employer]" "[City]"`, `filetype:pdf resume "[Name]"`).
- **Username enumeration**: If a handle is discovered, expand with Sherlock, WhatsMyName, or Namechk.

Use multiple source families so a single data broker does not dominate the result. See `references/SourcesAndTools.md` for the full catalog.

5. Pivot carefully.
For each promising candidate, expand through associated addresses, employers, school histories, relatives, and usernames only when those pivots stay inside the authorized scope.

- Parents often have more stable addresses.
- Siblings may be connected on social media.
- Spouse or partner records may reveal current address.
- Colleagues may appear in professional network connections.

6. Run reverse lookups on discovered identifiers.
For each phone number, email address, username, or photo found, run appropriate reverse lookups per the ReverseLookup workflow to find additional corroboration.

7. Verify the candidate set.
Score each candidate against independent identifiers. Apply the verification framework:

| Check | Method |
|---|---|
| Age/DOB alignment | Does approximate age match education and career timeline? |
| Location history | Can the path from last known to current address be traced logically? |
| Family connections | Do relatives listed match known family? |
| Employment/education | Does the career path align with known context? |
| Photo consistency | Do profile photos match across platforms and match expected age? |
| Cross-source agreement | Do 3+ independent sources confirm the same data points? |

8. Report ranked matches.
Return the best match first, then any plausible alternatives. Explain why each candidate is high, medium, or low confidence.

## Confidence Rules

- **High**: 3 or more independent identifiers align across truly independent sources.
- **Medium**: 2 identifiers align and the timeline makes sense.
- **Low**: Only 1 identifier aligns or the supporting evidence is weak.

Independence means different organizations and different data collection methods. Multiple people-search aggregators that share upstream data count as a single source.

## Common Challenges

- **Common name**: Add specificity through location, age, employer, school. Require 3+ matching data points. See the disambiguation steps in the verification section.
- **No results in aggregators**: Try variations (maiden name, nickname, phonetic variants), expand location radius, pivot to social media and public records.
- **Subject appears to have intentionally hidden**: Respect their privacy. Report the finding with ethical guidance about whether to pursue.
- **Multiple possible matches**: Present all viable candidates with differentiating factors and let the user narrow based on their additional knowledge.

## Deliverable

Provide a ranked candidate list, the evidence behind each rank, and the next best public-source step if certainty is still missing.

```text
Objective
Known identifiers (from subject profile)
Sources checked
Candidate matches (ranked)
Verified findings per candidate
Unverified leads
Confidence assessment
Recommended next public-source step
```

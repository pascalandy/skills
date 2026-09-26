# Discover Sources

Use this workflow when the user needs better public-source coverage for a niche investigation area.

## Steps

1. Define the gap.
State the investigation domain, geography, language, entity type, or time period where current source coverage is weak. Examples:

- Maritime OSINT tools for vessel tracking.
- Cryptocurrency investigation platforms.
- Region-specific OSINT for non-English jurisdictions.
- New social platform investigation tools.
- AI/ML-specific threat intelligence.

2. Gather candidate sources.
Search across multiple discovery channels simultaneously:

**GitHub and open-source**:
- Search GitHub topics: osint, osint-tools, reconnaissance, threat-intelligence, people-search.
- Check starred repos of known OSINT organizations (cipher387, The-Osint-Toolbox, Bellingcat, ProjectDiscovery).
- Filter by: greater than 50 stars, or created within the last 90 days with meaningful content.

**OSINT directories and curations**:
- Check Week in OSINT (sector035.nl) for recently featured tools.
- Search for new start.me OSINT pages.
- Check Bellingcat Toolkit for recent additions.
- Review OSINT Framework (osintframework.com) for category coverage.
- Check awesome-osint and related awesome lists on GitHub.

**Communities and forums**:
- OSINT subreddit (r/OSINT) for trending tools.
- Bellingcat Discord and The OSINTion Discord.
- Recent conference proceedings (SANS OSINT Summit, DEFCON Recon Village).

**Practitioner publications**:
- OSINT Newsletter (osintnewsletter.com) for recent tool reviews.
- Key practitioner blogs (inteltechniques.com, nixintel.info, hatless1der.com).
- OSINT podcasts for tool mentions.

3. Evaluate each candidate.
Only keep sources that pass all four criteria:

- [ ] **Relevant**: Addresses the stated gap with meaningful capability.
- [ ] **Maintained**: Updated within the last 12 months, or a canonical reference that does not require frequent updates.
- [ ] **Reachable**: Publicly accessible, with a usable free tier or clearly documented cost.
- [ ] **Unique**: Provides value not already covered by known sources in the existing catalog.

Additional evaluation dimensions:

| Dimension | Question |
|---|---|
| Credibility | Is the author or organization reputable in the OSINT community? |
| Data freshness | How current is the data? Real-time, daily, or static? |
| Coverage scope | Geographic, temporal, or entity-type coverage? |
| API availability | Does it offer programmatic access for automation? |
| Rate limits | What are the free-tier limits? |
| Privacy | Does using this source expose the investigator? |

4. Organize the shortlist.
Group sources by purpose:

- Registries (official databases).
- Search aggregators (multi-source lookup).
- Social discovery (platform-specific tools).
- Domain and infrastructure intelligence.
- Threat intelligence.
- Archives and historical data.
- Public records.

5. Recommend additions.
Explain what each source is useful for, its limitations, and why it deserves a place in the investigation toolkit. Flag any sources that should replace or supplement stale entries in the existing catalog.

## Deliverable

Return a shortlist of new sources:

```text
Gap description
New sources by category
  - Source name, URL, cost tier
  - What it provides
  - Trust level and limitations
  - Which investigation step it improves
Sources whose status changed (active to stale, renamed, etc.)
Categories that remain thin after this discovery
Recommended follow-up searches
```

## When to Run

- Monthly for routine source discovery.
- After major OSINT conferences.
- When a new investigation domain emerges (new social platform, new threat category).
- On demand when building capability in a specific niche.

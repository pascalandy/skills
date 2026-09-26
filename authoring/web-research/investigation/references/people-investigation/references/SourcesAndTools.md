# People Investigation Sources and Tools

Reference catalog of public sources organized by investigation phase. Use this when executing people-investigation workflows.

## Identity Resolution and People Search

| Source | Cost | Best For |
|---|---|---|
| TruePeopleSearch | Free | Best free US option, fresh data |
| FastPeopleSearch | Free | Basic lookups, no signup required |
| Spokeo | Freemium | Social media aggregation across 120+ networks |
| BeenVerified | Paid | Comprehensive background data |
| Pipl | Paid (enterprise) | AI-driven identity resolution, deep web coverage |
| Radaris | Freemium | Employment, criminal, public records |
| WhitePages | Freemium | Phone, address, and background checks |
| Intelius | Paid | Comprehensive background checks |
| PeekYou | Free | Unified digital profile builder |
| That's Them | Free | Name, address, phone, email, and IP lookup |
| OSINT Industries | Paid | 1500+ source real-time lookup |

## Username and Handle Lookup

| Source | Cost | Best For |
|---|---|---|
| Sherlock | Free (CLI) | Username search across 400+ platforms |
| Maigret | Free (CLI) | Dossier from 3000+ sites by username |
| WhatsMyName | Free (web) | 1500+ platforms with open-source database |
| Namechk | Free (web) | Username across 100+ sites |
| KnowEm | Freemium | Username across 500+ networks plus trademarks |
| Blackbird | Free (CLI) | Account search across 600+ platforms |
| Holehe | Free (CLI) | Email-to-platform mapping across 120+ services |

## Email Investigation

| Source | Cost | Best For |
|---|---|---|
| Hunter.io | Freemium | Professional email discovery and verification |
| EmailRep | Freemium | Email reputation and breach scoring |
| Epieos | Freemium | Reverse lookup across 140+ services |
| GHunt | Free (CLI) | Google account intelligence |
| h8mail | Free (CLI) | Email OSINT and breach hunting |
| Have I Been Pwned | Free | Breach notification across 12B+ accounts |

## Phone Lookup

| Source | Cost | Best For |
|---|---|---|
| PhoneInfoga | Free (CLI) | Phone number intelligence framework |
| Truecaller | Freemium | Caller ID with 400M+ user database |
| NumVerify | Freemium | Phone validation and geolocation API |
| CallerID Test | Free | Basic name, carrier, and location |
| NumLookup | Free | Free carrier and location lookup |

## Image and Face Search

| Source | Cost | Best For |
|---|---|---|
| PimEyes | Freemium | Face recognition search with 85-95% accuracy |
| TinEye | Freemium | Reverse image search across 70B+ indexed images |
| Yandex Images | Free | Best for facial matching globally |
| FaceCheck.ID | Freemium | Social media face matching |
| Lenso.ai | Freemium | AI reverse image with face recognition |
| Google Images | Free | General reverse image search |

## Social Media

| Source | Cost | Best For |
|---|---|---|
| Social Searcher | Freemium | Real-time public post monitoring |
| Social Links | Paid | 500+ source investigation platform |
| Snapchat Map | Free | Geolocated user-submitted content |

## Public Records

| Source | Cost | Best For |
|---|---|---|
| PACER | Freemium | US federal court records |
| CourtListener | Free | Multi-jurisdiction court search (nonprofit) |
| State voter registration | Free (varies) | Address and DOB confirmation |
| County assessor sites | Free | Property ownership records |
| Secretary of State portals | Free | Business officer and agent records |
| Professional licensing boards | Free | License status and disciplinary history |

## Academic and Professional

| Source | Cost | Best For |
|---|---|---|
| Google Scholar | Free | Academic publications and citations |
| ResearchGate | Free | Academic social network and collaboration |
| ORCID | Free | Persistent researcher identifiers |
| USPTO | Free | Patent search and inventor lookup |
| LinkedIn | Freemium | Professional profiles and employment history |

## Genealogy and Historical

| Source | Cost | Best For |
|---|---|---|
| FamilySearch | Free | Largest free genealogy resource |
| Find A Grave | Free | 230M+ cemetery and burial records |
| Ancestry | Paid | Largest genealogy database |
| MyHeritage | Freemium | Strong European records |

## Google Dorking Patterns

Use these search patterns to surface information from search engines:

```
site:linkedin.com/in "[Name]" "[City]"
site:facebook.com "[Name]" "[School]"
site:instagram.com "[Name]"
filetype:pdf resume "[Name]" "[City]"
"[Name]" "[Employer]" "[City]"
```

## Tool Selection by Scenario

**Reconnecting with a lost contact**: TruePeopleSearch, LinkedIn (Google x-ray), Facebook (Google x-ray), FamilySearch.

**Background before outreach**: LinkedIn, Spokeo, PACER/CourtListener, Google Scholar.

**Reverse lookup from an identifier**: PhoneInfoga or Truecaller (phone), Epieos or Holehe (email), Sherlock or WhatsMyName (username), PimEyes or TinEye (image).

**Verifying identity**: Cross-reference 3+ independent sources. Prefer official records (voter, property, court) over data-broker aggregators that may share upstream data.

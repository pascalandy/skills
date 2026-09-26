# Reverse Lookup

Use this workflow when the seed input is an identifier rather than a full person profile.

Supported seed types:

- Phone number
- Email address
- Username
- Profile photo or image link

## Steps

1. Classify the identifier.
Determine the seed type and normalize it before searching. For phone numbers, determine if mobile, landline, or VoIP. For emails, note the provider (corporate domain vs. free service).

2. Search sources appropriate to that identifier.

### Phone Number

| Step | Sources |
|---|---|
| Carrier and location | PhoneInfoga, Truecaller, NumVerify, NumLookup, CallerID Test |
| Owner lookup | TruePeopleSearch (reverse phone), That's Them, WhitePages |
| Web search | Google the number in quotes: `"512-555-1234"` and `"5125551234"` |
| Context | Check if the number appears in business listings, classifieds, or public posts |

Note carrier type: mobile vs. landline vs. VoIP. VoIP numbers are harder to trace. Prepaid numbers have limited registration data.

### Email Address

| Step | Sources |
|---|---|
| Account discovery | Holehe (120+ services), Epieos (140+ services) |
| Email verification | Hunter.io (validity and corporate patterns) |
| Breach exposure | Have I Been Pwned, h8mail |
| Google account intel | Epieos (may return name and photo from Google account) |
| Web search | Google the email in quotes: `"target@example.com"` |

Do not attempt password resets or gain access to accounts. Only check what is publicly visible.

### Username

| Step | Sources |
|---|---|
| Cross-platform enumeration | Sherlock (400+ platforms), WhatsMyName (1500+ platforms), Namechk |
| Variation search | Try common patterns: `[first][last]`, `[first].[last]`, `[first]_[last]`, `[first][last][year]` |
| Web search | Google: `"target_username"` and `inurl:"target_username"` |
| Profile analysis | Check bios, linked accounts, and location clues on discovered profiles |

### Image

| Step | Sources |
|---|---|
| General reverse search | Google Images, TinEye (70B+ indexed images) |
| Face matching | Yandex Images (best for faces globally), PimEyes (dedicated facial recognition), FaceCheck.ID |
| Origin detection | TinEye sorted by oldest result to find original source |
| Metadata | Check EXIF data if the file is available locally |

Verify legality of facial recognition tools in the relevant jurisdiction before use.

3. Pivot to person-level evidence.
Only move from the raw identifier to names, addresses, profiles, or relatives when the pivot stays within public data.

4. Cross-check every claimed match.
A reverse lookup result is only a lead until another independent source supports it. People-search aggregators often share upstream databases, so multiple aggregators returning the same data may count as a single source.

5. Return evidence with caveats.
Call out:
- Recycled data-broker results that appear across multiple aggregators from the same upstream.
- Stale records where the information may be outdated.
- VoIP numbers, shared inboxes, reused usernames, or copied images that create ambiguity.
- Carrier type and what it implies for traceability.

## Deliverable

Return these sections:

```text
Seed identifier
Identifier classification and normalization
Potential owner or account matches
Supporting sources per match
Secondary pivots worth checking
Confidence and caveats
```

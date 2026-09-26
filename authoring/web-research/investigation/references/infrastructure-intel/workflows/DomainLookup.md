# Domain Lookup

Use this workflow when the target is a domain or subdomain and the user needs technical context.

## Steps

1. Normalize the target.
Capture the root domain, any known subdomains, and whether the request includes passive-only or deeper analysis.

2. Collect registration and DNS facts.

**WHOIS and registrant analysis**:
- Registrant name, organization, email, dates (DomainTools, ViewDNS, standard WHOIS).
- Registration date and expiration date.
- Registrar identification.
- Privacy or proxy service detection.
- Registrant history and name server history (DomainTools historical WHOIS).
- Reverse WHOIS: does the registrant own other domains?

**Complete DNS record collection**:
- A records (IPv4), AAAA records (IPv6).
- MX records (mail servers).
- TXT records (SPF, DKIM, DMARC, verification tokens).
- NS records (authoritative name servers).
- CNAME records (aliases) and SOA record (zone authority).

**Historical DNS** (SecurityTrails):
- Previous IP addresses, name servers, and MX records.
- DNS change timeline and frequency.

3. Discover related surface area.
Map subdomains, certificates, related domains, hosting, and dependencies using multiple techniques:

| Technique | Source | What It Finds |
|---|---|---|
| Certificate transparency | crt.sh, CertStream | All certificates ever issued, SAN entries, wildcards |
| Passive DNS | SecurityTrails, DNSDumpster | Historical subdomain records |
| Subdomain brute-force | subfinder, Amass | Common subdomain names from wordlists |
| DNS aggregation | DNSDumpster | Combined passive intelligence with network map |
| IP resolution | IPinfo, Shodan | Hosting provider, geolocation, ASN |
| Shared hosting | Reverse IP lookup | Other domains on the same IP |
| Related TLDs | Manual check | Same name on .com, .net, .org, .io |

For each discovered subdomain:
- Resolve to IP address.
- Check if active (HTTP response code).
- Identify hosting provider.
- Note naming patterns (dev, staging, admin, api, vpn, mail).
- Flag dangling CNAME records (subdomain takeover risk).

4. Profile technology and hosting.

| Source | What It Provides |
|---|---|
| BuiltWith, Wappalyzer | Web framework, CMS, analytics, CDN, hosting, third-party integrations |
| Netcraft | Website security and tech profiling |
| Shodan, Censys | Open ports, services, SSL/TLS certificate details, known vulnerabilities |

Check security posture:
- SPF, DKIM, DMARC presence and configuration.
- HTTPS enforcement and HSTS headers.
- Certificate issuer (Let's Encrypt vs. commercial CA).
- Certificate expiry and SAN entries.

5. Review reputation and exposure.

| Source | What to Check |
|---|---|
| VirusTotal | Domain scan results, malware detections, community comments |
| URLScan.io | Live screenshot, technology detection, redirect chains, third-party requests |
| AbuseIPDB | Abuse reports for domain IPs, confidence score |
| GreyNoise | Is the domain's IP seen scanning the internet? |
| PhishTank | Phishing reports for the domain |
| Have I Been Pwned | Email addresses at this domain in breach databases |
| Intelligence X | Dark web and paste site exposure |

6. Report the infrastructure picture.
Separate hard facts from reputation signals and note what requires active confirmation outside this workflow.

## Deliverable

Return the domain profile:

```text
Domain profile (registration, age, registrant)
DNS infrastructure (records, name servers, mail configuration)
Subdomain map (with status and purpose classification)
Technology stack
Certificate analysis (issuer, SAN entries, timeline)
Reputation and threat intelligence signals
Related domains (same registrant, same IP, certificate relationships)
Risk assessment with confidence level
Recommended next pivot or investigation step
```

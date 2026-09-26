# Entity Lookup

Use this workflow when the seed is an IP, URL, hash, ASN, IOC, or other technical entity.

## Steps

1. Classify the entity.
Identify whether the seed is an IP address, URL, file hash (MD5, SHA1, SHA256), ASN, threat actor name, C2 infrastructure, or another technical indicator. Normalize the identifier.

| Entity Type | Normalization |
|---|---|
| IP address | Validate format, check if single IP or CIDR range |
| URL | Extract domain, path, and parameters separately |
| Hash | Identify hash type by length (MD5=32, SHA1=40, SHA256=64) |
| ASN | Validate AS number format |
| Domain | See DomainLookup workflow for domain-specific investigation |

2. Gather passive context.
Collect attribution clues, geolocation, hosting, and reputation appropriate to the entity type.

**For IP addresses**:

| Source | What It Provides |
|---|---|
| IPinfo | Geolocation, ASN, organization, carrier |
| Hurricane Electric BGP | Routing information, ASN peers, prefix details |
| RIPE Stat | Network statistics and measurement data |
| AbuseIPDB | Abuse reports, confidence score, report categories |
| GreyNoise | Scanner classification (benign, malicious, unknown) |
| Shodan | Open ports, services, banners, known vulnerabilities |
| Censys | Certificates, protocols, service fingerprints |
| AlienVault OTX | Threat intelligence pulses and IOC associations |

**For URLs**:

| Source | What It Provides |
|---|---|
| URLScan.io | Screenshot, DOM, technologies, redirect chains, third-party requests |
| VirusTotal | Multi-engine URL scan, community scores |
| PhishTank | Phishing classification |
| URLhaus | Known malicious URL database |

**For file hashes**:

| Source | What It Provides |
|---|---|
| VirusTotal | Multi-engine detection ratio, malware family, behavioral analysis |
| Hybrid Analysis | Sandbox execution results, network indicators |
| MalwareBazaar | Sample metadata, tags, and related samples |
| ANY.RUN | Interactive analysis results if available |

**For threat context**:

| Source | What It Provides |
|---|---|
| MITRE ATT&CK | Adversary TTPs, technique mappings, group profiles |
| Pulsedive | Community enrichment and IOC correlation |
| IBM X-Force Exchange | Threat intelligence and historical data |
| Cisco Talos | IP and domain reputation |
| ThreatFox | IOC database with malware attribution |
| CISA advisories | Government threat alerts and known exploited vulnerabilities |

3. Pivot by relationship.
Expand through infrastructure connections when relevant:

- Related domains via shared IP, shared registrant, or certificate SAN entries.
- IP neighbors via same network block or ASN.
- Related hashes via shared C2 infrastructure, same malware family, or similar behavior.
- Campaign connections via threat intelligence reports and IOC feeds.
- Certificate relationships via shared issuers or similar SAN patterns.
- Historical data: has the entity changed hands, hosting, or behavior over time?

4. Check for corroboration.
A single reputation hit is not enough. Prefer multiple independent references before calling something suspicious or malicious.

- Cross-reference abuse reports across AbuseIPDB, GreyNoise, and AlienVault OTX.
- Verify malware detections across VirusTotal, Hybrid Analysis, and MalwareBazaar.
- Check government advisories (CISA, UK NCSC, ENISA) for official attribution.
- Distinguish between active threats and historical listings that may be resolved.

5. Check for dark web and breach exposure.

| Source | What to Check |
|---|---|
| Have I Been Pwned | Breach exposure for associated email domains |
| Intelligence X | Surface and dark web search, archived content |
| DeHashed | Breach records searchable by domain or email |
| Ahmia | Tor hidden service references |
| Feodo Tracker | C2 server listings and botnet associations |
| SSL Blacklist | Malicious SSL certificate and JA3 fingerprint matches |

6. Produce a risk-aware summary.
State whether the entity looks benign, suspicious, malicious, compromised, or inconclusive, and explain why with evidence weight.

## Threat Classification

| Classification | Meaning |
|---|---|
| Benign | No threat indicators, legitimate infrastructure |
| Suspicious | Some indicators but insufficient for confident attribution |
| Malicious | Multiple independent sources confirm threat activity |
| Compromised | Legitimate infrastructure being misused |
| Sinkholed | Former malicious infrastructure now controlled by defenders |
| Inconclusive | Conflicting evidence, more investigation needed |

## Deliverable

Return the entity assessment:

```text
Entity classification and normalized identifier
Infrastructure facts (hosting, services, certificates, network)
Threat and reputation evidence (with source citations)
Related entities and pivots discovered
Dark web and breach exposure
Timeline (registration, first seen, changes)
Risk assessment with confidence level
Recommended next step
```

# Infrastructure Intelligence Sources and Tools

Reference catalog of public sources organized by investigation domain. Use this when executing infrastructure-intel workflows.

## WHOIS and Domain Registration

| Source | Cost | Best For |
|---|---|---|
| DomainTools | Paid | Historical WHOIS/DNS data, reverse WHOIS, monitoring |
| ViewDNS | Freemium | Comprehensive DNS tools suite |
| WHOIS databases | Free | Registration details for most TLDs |

## DNS and Subdomain Discovery

| Source | Cost | Best For |
|---|---|---|
| SecurityTrails | Freemium | DNS history, subdomain enumeration, 4B+ records |
| DNSDumpster | Free | DNS recon with visual network map |
| crt.sh | Free | Certificate transparency log search |
| CertStream | Free | Real-time certificate issuance feed |
| Amass (OWASP) | Free (CLI) | Advanced subdomain enumeration from 55+ sources |
| subfinder | Free (CLI) | Passive subdomain enumeration |
| theHarvester | Free (CLI) | Email, subdomain, and URL gathering |

## IP and Network Intelligence

| Source | Cost | Best For |
|---|---|---|
| Shodan | Freemium | Internet-connected device and service search |
| Censys | Freemium | Internet-wide scanning and certificate data |
| IPinfo | Freemium | IP geolocation, ASN, and carrier data |
| AbuseIPDB | Freemium | Crowd-sourced IP reputation database |
| GreyNoise | Freemium | Internet noise versus targeted attack classification |
| BinaryEdge | Freemium | Network scanning and honeypot data |
| ZoomEye | Freemium | Internet asset search with strong Asian coverage |
| Criminal IP | Freemium | Cyber threat search engine |
| Hurricane Electric BGP | Free | BGP routing intelligence, ASN lookup, peering |
| RIPE Stat | Free | Internet measurement and network statistics |

## Malware Analysis and Sandboxing

| Source | Cost | Best For |
|---|---|---|
| VirusTotal | Freemium | Multi-engine file and URL scanning |
| Hybrid Analysis | Free | CrowdStrike malware sandbox |
| ANY.RUN | Freemium | Interactive malware sandbox |
| Joe Sandbox | Freemium | Deep automated malware analysis |
| MalwareBazaar | Free | Malware sample exchange |
| URLhaus | Free | Malicious URL database |
| URLScan.io | Freemium | URL scanning, screenshots, and technology detection |

## Vulnerability Databases

| Source | Cost | Best For |
|---|---|---|
| NVD (NIST) | Free | National Vulnerability Database |
| CVE Program (MITRE) | Free | Global vulnerability identifier system |
| Exploit-DB | Free | Public exploits archive |
| CISA KEV | Free | Known actively exploited vulnerabilities |
| Snyk | Freemium | Developer-focused vulnerability database |
| OSV | Free | Google-backed open source vulnerabilities |

## Threat Intelligence Platforms

| Source | Cost | Best For |
|---|---|---|
| Pulsedive | Free | Community threat intel and IOC enrichment |
| IBM X-Force Exchange | Free | Threat intelligence sharing (20+ years of data) |
| Cisco Talos | Free | IP and domain reputation lookups |
| AlienVault OTX | Free | Threat intelligence community with pulses and IOCs |
| ThreatFox | Free | IOC database with malware attribution |
| Recorded Future | Paid | AI-powered threat intelligence |
| Mandiant | Paid | APT tracking across 350+ groups |

## Frameworks and Standards

| Source | Cost | Best For |
|---|---|---|
| MITRE ATT&CK | Free | Adversary tactics and techniques knowledge base |
| MITRE D3FEND | Free | Defensive countermeasures graph |
| MITRE ATLAS | Free | AI/ML-specific attack framework |

## Dark Web and Leak Monitoring

| Source | Cost | Best For |
|---|---|---|
| Have I Been Pwned | Free | Breach notification service |
| Intelligence X | Freemium | Surface and dark web search engine |
| DeHashed | Paid | 19B+ breach records searchable |
| Ahmia | Free | Tor hidden service search engine |
| PhishTank | Free | Crowd-sourced phishing verification |

## Botnet and C2 Tracking

| Source | Cost | Best For |
|---|---|---|
| Feodo Tracker | Free | Botnet C2 server tracking |
| SSL Blacklist | Free | Malicious SSL and JA3 detection |

## Government Cybersecurity Resources

| Source | Cost | Best For |
|---|---|---|
| CISA | Free | US cybersecurity advisories, KEV, and scanning services |
| FBI IC3 | Free | Internet crime reports and advisories |
| UK NCSC | Free | UK National Cyber Security Centre alerts |
| ENISA | Free | EU Agency for Cybersecurity guidance |

## Automation Frameworks

| Source | Cost | Best For |
|---|---|---|
| Maltego | Freemium | Visual link analysis with 120+ integrations |
| SpiderFoot | Freemium | Automated OSINT with 200+ modules |
| Recon-ng | Free (CLI) | Modular web reconnaissance framework |

## OSINT Directories and Meta-Resources

| Source | Cost | Best For |
|---|---|---|
| OSINT Framework | Free | Interactive directory of hundreds of free tools |
| IntelTechniques | Freemium | Bazzell's custom OSINT search tools |
| Bellingcat Toolkit | Free | Community-maintained investigation toolkit |
| awesome-osint (GitHub) | Free | Curated OSINT tools list with 24.9K stars |
| Week in OSINT | Free | Weekly curation of new OSINT tools and techniques |

## Tool Selection by Scenario

**Domain investigation**: DomainTools or ViewDNS (WHOIS), SecurityTrails + DNSDumpster (DNS), crt.sh + subfinder (subdomains), BuiltWith (technology), VirusTotal + URLScan.io (reputation).

**IP or IOC analysis**: IPinfo (attribution), AbuseIPDB + GreyNoise (reputation), Shodan + Censys (services), VirusTotal (malware), AlienVault OTX + Pulsedive (threat intel).

**Threat actor profiling**: MITRE ATT&CK (TTPs), Mandiant or Recorded Future (campaigns), VirusTotal + MalwareBazaar (samples), Feodo Tracker (C2), Intelligence X (dark web).

**Source discovery for a niche**: Start with awesome-osint and OSINT Framework, check Week in OSINT for recent tools, then search GitHub topics and OSINT communities for domain-specific resources.

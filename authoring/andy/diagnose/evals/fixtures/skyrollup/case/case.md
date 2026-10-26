# Case 2026-10-13-summary-stuck: website daily summary stuck on October 8

- Requested outcome: diagnosis
- Variable: the website's daily summary (summary-latest.json via the CDN), since 2026-10-09
- Report: artifacts/report.md
- Verify loop: none named
- Ladder: service
- Current layer: 1

## Controls
| id | control | type | differs by | matches | not broken the same way because |
|---|---|---|---|---|---|

## Facts
| id | kind | layer | where | statement | variable | control | source | artifact | supersedes |
|---|---|---|---|---|---|---|---|---|---|
| F1 | symptom | 1 | field | Volunteer report, quoted: "The daily summary on the website has shown October 8 since Friday." | summary shown: 2026-10-08, since Fri 2026-10-09 |  | email from Ilse Varnholt (station ws-12) to ops@, Mon 2026-10-12 07:48 -0400 | report.md |  |
| F2 | symptom | 1 | field | The CDN serves summary-latest.json with `last-modified: Fri, 09 Oct 2026 02:04:11 GMT`, `x-cache: HIT` | last-modified 2026-10-09 02:04:11 UTC; x-cache HIT; age 187 s |  | ./probe cdn-headers /summaries/summary-latest.json, run by agent 2026-10-13 09:52 UTC | cdn-headers.txt |  |
| F3 | context | 1 | field | `skyrollup status`: last run OK, 38 of 40 stations | result ok; stations 38 of 40 |  | ./probe status (skyrollup status on wx-1, skyrollup 0.9.4), run by agent 2026-10-13 09:54 UTC | status.txt |  |
| F4 | noise | 1 | field | `skyrollup logs --since 2026-10-09`: no errors | 0 errors; nightly WARN for ws-23 and ws-31 only |  | ./probe logs --since 2026-10-09 (skyrollup logs on wx-1), run by agent 2026-10-13 09:55 UTC | logs.txt |  |
| F5 | context | 1 | field | Station dashboard: 38 of 40 stations reporting | 38 of 40 reporting; ws-23 and ws-31 offline since September |  | station dashboard www.fernlowwx.example/stations/, read by agent 2026-10-13 09:58 UTC | stations.txt |  |

## Hypotheses
| id | claim | from | killed if | origin | status | by |
|---|---|---|---|---|---|---|
| H1 | the CDN serves a stale cached summary | F2 | the origin's file is newer than 2026-10-09 02:04 | new | live | agent |
| H2 | stations stopped reporting | F1 | most stations report | new | live | agent |
| H3 | the job is not running or failing | F1 | status shows a recent good run | new | live | agent |

## Judgments
| h | f | mark | because | by |
|---|---|---|---|---|
| H1 | F2 | + | the edge answers from cache (x-cache HIT) with a copy last modified 2026-10-09 02:04:11 | agent |
| H2 | F5 | x | 38 of 40 stations report | agent |
| H3 | F3 | x | status says last run OK | agent |

## Log
| step | type | target | detail | result |
|---|---|---|---|---|
| 1 | note | layer 1 | gathering layer 1: the report, CDN headers, skyrollup status and logs, station dashboard | started |
| 2 | note | wx-1 | read skyrollup status and skyrollup logs --since 2026-10-09 | F3, F4 |
| 3 | note | CDN, dashboard | read the CDN headers for summary-latest.json and the station dashboard | F2, F5 |
| 4 | note | CDN | next: purge the CDN cache for summary-latest.json and re-read | waiting for Pascal's OK |

## Interventions
| step | who | quote | category |
|---|---|---|---|

## Decisions
| question | options | recommended | chosen | by |
|---|---|---|---|---|
| Purge the CDN cache for summary-latest.json? | purge now; wait for the TTL | purge now |  |  |

## Close

# FIRING: pantry-search p95 latency, pool blue

| | |
|---|---|
| Alert | `pantry-search-p95` |
| Rule | p95 of `GET /v2/search` at the pool's load balancer above 300 ms for 15 minutes |
| Pool | blue |
| Fired | Tue 2026-10-13 10:21 UTC |
| Last evaluated | Wed 2026-10-14 14:15 UTC, still firing: p95 790 ms over 14:00-14:15 |
| Other pool | green, not firing: p95 140 ms over 14:00-14:15 |

## Deploy

- Tue 2026-10-13 10:00 UTC: pantry-search 5.3.0 rollout starts on blue (18 instances). Blue done at 10:09.
- Green (2 instances) was due at 11:00, after an hour on blue.
- Tue 10:31 UTC: rollout paused by on-call. Green stays on 5.2.0.

## On-call notes (Ilse Brandvold)

- Tue 10:31: paused the rollout. Not rolling blue back for now: the recipe page team launches star ratings on search results Thursday and needs 5.3 out, so we fix forward.
- Tue 11:40: restarted the blue instances one at a time. p95 came back to where it was within minutes of each restart.
- Tue 12:15: the load balancer splits traffic 90/10 by hashed client id, so both pools see the same query mix.
- Wed 09:20: blue p95 follows traffic through the day: about 280 ms overnight, past 1 s at the evening peak. Green stays between 105 and 155 ms.
- Wed 14:20: exported p95 per pool to `p95.csv` (5-minute buckets, Mon 00:00 to Wed 14:15 UTC).

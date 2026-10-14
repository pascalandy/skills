# Runbook: move scheduled jobs from ops-1 to ops-2

Owner: Sam Whitlock (ops). Window: Fri 2026-10-09, 09:00 to 10:30 EDT.

ops-1 goes out of support at the end of the month. ops-2 is built from the standard image (base-2026.09) and takes over ops-1's scheduled jobs. Cron lines become systemd timers.

## Jobs

| Job | ops-1 (crontab of `crumb`) | ops-2 |
|---|---|---|
| orders-sync, prod | `*/10 * * * *` | `orders-sync.timer`, `OnCalendar=*:0/10` |
| preorder-export | `0 21 * * *` | `preorder-export.timer`, `OnCalendar=*-*-* 21:00:00 America/Toronto` |

The preorder timer keeps the 21:00 bakery time the kitchen is used to. Both jobs run as `crumb` from the same checkouts as on ops-1: `/opt/crumb` at tag v1.6 and `/opt/crumb-sync` at tag v3.2.

## Steps

- [x] 09:12 ops-2 up from base-2026.09, user `crumb` created, `/srv/crumb/prod` mounted
- [x] 09:20 checkouts copied to ops-2: `/opt/crumb` (v1.6), `/opt/crumb-sync` (v3.2)
- [x] 09:26 new prod sync token issued for ops-2, written to `/etc/crumb/sync-prod.env`
- [x] 09:31 ops-1: both lines commented out in `crumb`'s crontab
- [x] 09:40 ops-2: both timers enabled and started
- [x] 09:44 orders-sync on ops-2: 09:40 run ok, 0 rows (nothing new)
- [x] 09:47 `systemctl list-timers`: preorder-export NEXT is Sat 2026-10-10 01:00:00 UTC, which is 21:00 Friday in Toronto
- [x] 09:55 ops-1: config and logs backed up to the ops share
- [x] 10:00 ops-1 powered off
- [x] 10:05 old prod sync token (ops-1) revoked after the 09:50 run on ops-2 came back ok, 1 row

## Rollback

Power ops-1 back on and uncomment the two crontab lines, then stop and disable both timers on ops-2.

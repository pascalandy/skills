# Preorder sheet: repro and plan

Jo Lindqvist, Sun 2026-10-11

Reproduced it from my laptop at 14:10. I can't read prod from there, so I ran tomorrow's sheet against staging, which crumb-sync fills from the same shop orders:

```
$ python3 -m crumb.export --for tomorrow --dry-run --db staging
target date 2026-10-12, 3 orders
Orders for Mon 2026-10-12
07:30  #50956  Caius Hruska          2 baguette, 1 challah
09:00  #50919  Saoirse Kincaid       6 butter tart
12:00  #50941  Sunniva Quintero      1 country loaf
```

The shop admin shows 29 preorders for Monday. The sheet has 3. So the export is reading a table that stopped filling.

The sync monitor agrees: staging-sync's last good run was Friday at 09:50, and every run since has failed. That is exactly when ops moved the jobs to ops-2 (migration.md). The runbook says they issued a new sync token on ops-2 and revoked the ops-1 one at 10:05, so my guess is the sync is still using the old token somewhere. The orders sync broke in the migration, and the sheets have been built from a half-empty table ever since.

Plan, once someone OKs it:

1. Run crumb-sync by hand on ops-2 for both envs to backfill everything since Friday.
2. Rotate the sync token and restart both sync timers so they pick up the new one.
3. Check tonight's sheet with `--dry-run` on ops-2 before it goes out.

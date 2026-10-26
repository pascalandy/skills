# Changelog

## 0.9.4 (2026-08-18)

- Offline stations are logged at warning level, so `skyrollup logs` shows them by default.

## 0.9.3 (2026-06-27)

- Retry a station once before marking it offline. The collector drops the odd request at 02:00.

## 0.9.2 (2026-04-30)

- Leave out stations with fewer than 12 readings for the day; a station that came back at 23:50 skewed the minimum temperature.

## 0.9.1 (2026-03-21)

- New `skyrollup logs` command: reads the job's log file, filtered by level and day.
- Tests with a fake station source.

## 0.9.0 (2026-01-17)

- First release: nightly summary per UTC day, `summary-latest.json` symlink for the website, `status.json` and `skyrollup status`.

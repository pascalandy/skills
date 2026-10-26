# Changelog

## 3.4.0 (2026-10-13)

- Response cache for departures, keyed by stop and minute. `--no-cache` turns it off.
- Request log gains the `cache` field: `hit`, `miss`, or `off`.

## 3.3.0 (2026-08-13)

- Request log gains the `client` field, from the `X-Client` header.

## 3.2.0 (2026-06-22)

- The API checks the feed link once a minute and reloads on a new import, instead of waiting for a restart.
- `--at` answers as of a fixed UTC time, for replaying an exported feed.

## 3.1.0 (2026-03-30)

- Live delays from the vehicle tracking upstream, with `--realtime`.
- Saturday and Sunday timetables.

## 3.0.0 (2026-01-19)

- Routes move under `/v1`: departures per stop and stop search. The old unversioned routes are gone.
- Responses carry `ok`, and `errors` when `ok` is false.

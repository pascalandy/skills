# Changelog

## 5.2.0 - 2026-09-22

- Facets count only published recipes.
- `limit` is capped at 48.
- `/healthz` reports the running version.

## 5.1.0 - 2026-08-25

- Terms match tags exactly instead of by prefix.
- Hits include `url`.

## 5.0.0 - 2026-07-14

- `/v2/search` replaces `/v1/search`.
- Hits carry `images` in three widths.

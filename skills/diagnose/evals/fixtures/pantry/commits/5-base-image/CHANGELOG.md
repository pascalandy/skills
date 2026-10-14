# Changelog

## 5.3.0 - 2026-10-13

- Search hits carry `rating`: mean stars and review count.
- Ranking gives recently updated recipes a recency boost.
- New JSON encoder with sorted keys.
- Access log lines gain request size and user agent.
- Base image moves to Python 3.12.7.

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

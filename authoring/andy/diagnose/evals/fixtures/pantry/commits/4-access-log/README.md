# pantry-search

Recipe search API for the cooking site. It serves `GET /v2/search` behind
the site's result cache, on two pools, `blue` and `green`, that split traffic
90/10. Releases go to `blue` first, then to `green`.

## Run locally

    python3 -m pantry.server
    curl 'http://127.0.0.1:8080/v2/search?q=chicken&limit=24'

`config.toml` points the database at `dev/sample.sql`, which is loaded into
an in-memory SQLite database at startup.

Tests:

    python3 -m unittest discover -s tests

## API

`GET /v2/search?q=<text>&limit=<n>`, `limit` from 1 to 48, default 24.

Every term in `q` must appear in the title or equal one of the recipe's tags.
Hits are ranked by title matches plus a boost for recently updated recipes,
then by saves.

| Field    | Meaning                                         |
|----------|-------------------------------------------------|
| `query`  | the `q` parameter as received                   |
| `count`  | number of hits returned                         |
| `hits`   | recipes: `id`, `slug`, `title`, `summary`, `tags`, `minutes`, `serves`, `author`, `url`, `images`, `rating` |
| `facets` | up to 12 tags with the number of matching recipes |

`rating` holds the recipe's mean stars and review count:
`{"stars": 4.25, "count": 12}`. `stars` is null for a recipe with no reviews.

`GET /healthz` returns the running version.

## Database

Production pools read from their recipe store (`PANTRY_DB_URL`), a read-only
SQL endpoint in front of the pool's database replica. Local runs and tests
use SQLite with the same schema, built from `dev/sample.sql`.

## Access log

One line per request on the `pantry.access` logger:

| Field       | Meaning                                       |
|-------------|-----------------------------------------------|
| client      | client address                                |
| request     | request line                                  |
| status      | HTTP status                                   |
| bytes       | response body size                            |
| `NNNms`     | time from request to response                 |
| `queries`   | statements the request ran                    |
| `store_ms`  | time spent in those statements                |
| `req_bytes` | size of the request line and headers          |
| `ua`        | client user agent                             |

The metrics pipeline reads these lines; `queries` becomes `queries_per_request`.

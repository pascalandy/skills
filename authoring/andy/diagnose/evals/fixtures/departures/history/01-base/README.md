# departures-api

Next departures per stop for Tamarack Regional Transit. The departure screens in stations and the public website read from it.

## Routes

- `GET /v1/stops/{stop_id}/departures?limit=8`: the next departures from a stop, soonest first. `limit` is 1 to 50, default 8.
- `GET /v1/search?q=<text>`: stops whose name contains the text, ignoring case.

Every response is one JSON object: `{"ok": true, ...}`, or `{"ok": false, "errors": [...]}` with status 400 or 404.

## Feed

The API reads a feed folder holding `stops.txt`, `routes.txt`, `trips.txt` and `stop_times.txt`. In production `--feed` is `/srv/feeds/current`, a link to the latest import. The API checks the link once a minute and reloads when it points to a new import. The folder name is the feed version, for example `2026-10-14T0550`.

## Run locally

    python3 -m departures.server --feed <dir> --port 8080
    curl -s 'http://127.0.0.1:8080/v1/stops/MKT/departures?limit=8'

- `--at 2026-10-14T08:10` answers as of that UTC time, handy with an exported feed.
- `--realtime URL` adds live delays from the vehicle tracking upstream. Without it, departures are timetable only.

## Tests

    python3 -m unittest discover -s tests

## Logs

One JSON line per request on stdout, with `ts`, `path`, `stop_id`, `status`, `items`, and `ms`. Service messages, such as startup, feed reloads, and realtime warnings, go to stderr.

"""HTTP JSON API for the departure screens and the website.

GET /v1/stops/{stop_id}/departures?limit=8
GET /v1/search?q=<text>

One JSON line per request goes to stdout; service messages go to stderr.
"""

import argparse
import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .feed import load_feed
from .query import departures_for, search
from .realtime import Realtime

log = logging.getLogger("departures")

DEPARTURES_PATH = re.compile(r"^/v1/stops/([^/]+)/departures$")
DEFAULT_LIMIT = 8
MAX_LIMIT = 50


class App:
    def __init__(self, feed_path, realtime=None, clock=None, request_log=None):
        self.feed_path = feed_path
        self.feed = load_feed(feed_path)
        self.loaded_from = os.path.realpath(feed_path)
        self.realtime = realtime
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.request_log = request_log or sys.stdout
        self._log_lock = threading.Lock()

    def reload_if_changed(self):
        target = os.path.realpath(self.feed_path)
        if target == self.loaded_from:
            return False
        feed = load_feed(self.feed_path)
        self.feed, self.loaded_from = feed, target
        log.info("feed reloaded %s (stops %d, trips %d)", feed.version, len(feed.stops), len(feed.trips))
        return True

    def departures(self, stop_id, limit):
        """Departures for one request."""
        found = departures_for(self.feed, stop_id, self.clock(), limit)
        if self.realtime is not None:
            delays = self.realtime.delays(stop_id)
            found = [
                dict(item, delay_s=delays[item["trip_id"]]) if item["trip_id"] in delays else item
                for item in found
            ]
        return found

    def write_log(self, entry):
        with self._log_lock:
            self.request_log.write(json.dumps(entry) + "\n")
            self.request_log.flush()


class Handler(BaseHTTPRequestHandler):
    server_version = "departures-api/" + __version__

    def do_GET(self):
        started = time.perf_counter()
        app = self.server.app
        url = urlsplit(self.path)
        params = parse_qs(url.query)
        entry = {"ts": None, "path": url.path, "stop_id": None, "status": 200, "items": 0}
        match = DEPARTURES_PATH.match(url.path)
        if match:
            stop_id = entry["stop_id"] = match.group(1)
            limit = _int(params.get("limit", [DEFAULT_LIMIT])[0])
            if limit is None or not 1 <= limit <= MAX_LIMIT:
                status, body = 400, {"ok": False, "errors": [f"limit must be 1 to {MAX_LIMIT}"]}
            else:
                found = app.departures(stop_id, limit)
                status = 200
                body = {"ok": True, "stop_id": stop_id, "feed": app.feed.version, "departures": found}
                entry["items"] = len(found)
        elif url.path == "/v1/search":
            text = params.get("q", [""])[0].strip()
            if not text:
                status, body = 400, {"ok": False, "errors": ["q is required"]}
            else:
                stops = search(app.feed, text)
                status, body = 200, {"ok": True, "query": text, "stops": stops}
                entry["items"] = len(stops)
        else:
            status, body = 404, {"ok": False, "errors": ["no such route"]}
        self._send(status, body)
        entry["status"] = status
        entry["ts"] = _utc_stamp()
        entry["ms"] = round((time.perf_counter() - started) * 1000, 1)
        app.write_log(entry)

    def _send(self, status, body):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass  # replaced by the JSON request log


def _int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def _utc_stamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def watch_feed(app, every=60):
    """Reload when the feed link points to a new import; checked on the minute."""
    while True:
        time.sleep(every - time.time() % every)
        try:
            app.reload_if_changed()
        except Exception:
            log.exception("feed reload failed, keeping %s", app.feed.version)


def fixed_clock(text):
    moment = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    return lambda: moment


def setup_logging():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%SZ")
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    logging.addLevelName(logging.WARNING, "WARN")
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m departures.server", description=__doc__.splitlines()[0])
    parser.add_argument("--feed", required=True, help="feed folder, or a link to the current import")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--realtime", metavar="URL", help="vehicle tracking upstream; timetable only without it")
    parser.add_argument("--at", metavar="YYYY-MM-DDTHH:MM", help="answer as of this UTC time instead of now")
    args = parser.parse_args(argv)

    setup_logging()
    app = App(
        args.feed,
        realtime=Realtime(args.realtime) if args.realtime else None,
        clock=fixed_clock(args.at) if args.at else None,
    )
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    server.app = app
    log.info("departures-api %s serving on :%d, feed %s", __version__, args.port, app.feed.version)
    threading.Thread(target=watch_feed, args=(app,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

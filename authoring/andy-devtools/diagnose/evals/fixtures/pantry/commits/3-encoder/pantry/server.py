"""HTTP front end for pantry-search.

    GET /v2/search?q=<text>&limit=<n>
    GET /healthz
"""

import logging
import os
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .db import Database
from .encode import dumps
from .search import DEFAULT_LIMIT, search

log = logging.getLogger("pantry")
access_log = logging.getLogger("pantry.access")


def render(payload):
    return dumps(payload).encode("utf-8")


def handle_search(db, query_string):
    params = parse_qs(query_string)
    q = params.get("q", [""])[0].strip()
    if not q:
        return 400, {"error": "missing q"}
    try:
        limit = int(params.get("limit", [DEFAULT_LIMIT])[0])
    except ValueError:
        return 400, {"error": "limit must be an integer"}
    return 200, search(db, q, limit=limit)


def route(db, url):
    if url.path == "/v2/search":
        return handle_search(db, url.query)
    if url.path == "/healthz":
        return 200, {"status": "ok", "version": __version__}
    return 404, {"error": "not found"}


class Handler(BaseHTTPRequestHandler):
    server_version = f"pantry-search/{__version__}"

    def do_GET(self):
        started = time.perf_counter()
        url = urlsplit(self.path)
        with self.server.db.request() as stats:
            try:
                status, payload = route(self.server.db, url)
            except Exception:
                log.exception("request failed: %s", self.path)
                status, payload = 500, {"error": "internal error"}
            body = render(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        elapsed_ms = (time.perf_counter() - started) * 1000
        access_log.info(
            '%s "%s" %d %d %.1fms queries=%d store_ms=%.1f',
            self.client_address[0], self.requestline, status, len(body), elapsed_ms,
            stats.statements, stats.store_ms,
        )

    def log_request(self, code="-", size="-"):
        """Requests are logged by do_GET, with timings and statement counts."""


class PoolServer(HTTPServer):
    """Serves connections on a fixed pool of worker threads."""

    def __init__(self, address, db, threads):
        super().__init__(address, Handler)
        self.db = db
        self.workers = ThreadPoolExecutor(max_workers=threads, thread_name_prefix="worker")

    def process_request(self, request, client_address):
        self.workers.submit(self.serve_connection, request, client_address)

    def serve_connection(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def load_config(path):
    with open(path, "rb") as f:
        return tomllib.load(f)


def main():
    config = load_config(os.environ.get("PANTRY_CONFIG", "config.toml"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    db = Database.open(os.environ.get("PANTRY_DB_URL", config["database"]["url"]))
    host, port = config["server"]["host"], config["server"]["port"]
    threads = config["server"]["threads"]
    server = PoolServer((host, port), db, threads)
    log.info("pantry-search %s listening on %s:%d, %d threads", __version__, host, port, threads)
    server.serve_forever()


if __name__ == "__main__":
    main()

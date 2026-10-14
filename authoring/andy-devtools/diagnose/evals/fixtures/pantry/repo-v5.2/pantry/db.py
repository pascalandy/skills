"""Database access for pantry-search.

Every statement goes through Database.query, which counts it against the
current request. The access log reports the count as queries=N.
"""

import json
import sqlite3
import threading
import time
import urllib.request
from contextlib import contextmanager


class RequestStats:
    def __init__(self):
        self.statements = 0
        self.store_ms = 0.0

    def record(self, seconds):
        self.statements += 1
        self.store_ms += seconds * 1000


class Database:
    def __init__(self, connection):
        self._connection = connection
        self._local = threading.local()

    @classmethod
    def open(cls, url):
        """Open a recipe store URL, a SQLite file, or a .sql script loaded into memory."""
        if url.startswith(("http://", "https://")):
            return cls(StoreConnection(url))
        if url.endswith(".sql"):
            with open(url, encoding="utf-8") as f:
                return cls.from_sql(f.read())
        return cls(SQLiteConnection(sqlite3.connect(url, check_same_thread=False)))

    @classmethod
    def from_sql(cls, script):
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.executescript(script)
        return cls(SQLiteConnection(conn))

    @contextmanager
    def request(self):
        stats = RequestStats()
        self._local.stats = stats
        try:
            yield stats
        finally:
            self._local.stats = None

    def query(self, sql, params=()):
        started = time.perf_counter()
        rows = self._connection.execute(sql, tuple(params))
        stats = getattr(self._local, "stats", None)
        if stats is not None:
            stats.record(time.perf_counter() - started)
        return rows


class SQLiteConnection:
    def __init__(self, conn):
        self._conn = conn
        self._lock = threading.Lock()

    def execute(self, sql, params):
        with self._lock:
            return self._conn.execute(sql, params).fetchall()


class StoreConnection:
    """Client for a pool's recipe store, which runs read-only SQL over HTTP."""

    def __init__(self, url, timeout=2.0):
        self._endpoint = url.rstrip("/") + "/v1/query"
        self._timeout = timeout

    def execute(self, sql, params):
        body = json.dumps({"sql": sql, "params": list(params)}).encode("utf-8")
        request = urllib.request.Request(
            self._endpoint, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            return [tuple(row) for row in json.load(response)["rows"]]

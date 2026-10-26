import datetime as dt
from pathlib import Path

from skyrollup.config import Config


def make_config(root, stations=("ws-01", "ws-02", "ws-03")):
    root = Path(root)
    for sub in ("summaries", "state", "log"):
        (root / sub).mkdir(exist_ok=True)
    return Config(
        source_url="http://collector.test/v1/readings",
        timeout=1.0,
        stations=tuple(stations),
        summaries_dir=root / "summaries",
        latest_name="summary-latest.json",
        status_file=root / "state" / "status.json",
        log_file=root / "log" / "skyrollup.log",
    )


class FakeSource:
    """Ten-minute readings for a day; some stations can be offline or flaky."""

    def __init__(self, offline=(), flaky=(), counts=None):
        self.offline = set(offline)
        self.flaky = set(flaky)
        self.counts = counts or {}
        self.calls = []

    def readings(self, station, day):
        self.calls.append(station)
        if station in self.offline:
            raise OSError("HTTP Error 404: Not Found")
        if station in self.flaky and self.calls.count(station) == 1:
            raise OSError("timed out")
        seed = sum(map(ord, station)) + day.toordinal()
        start = dt.datetime.combine(day, dt.time(), dt.timezone.utc)
        rows = []
        for i in range(self.counts.get(station, 144)):
            rows.append({
                "time": (start + dt.timedelta(minutes=10 * i)).isoformat(),
                "temp_c": 8 + (seed % 7) + (i % 72) / 10,
                "rain_mm": 0.2 if (seed + i) % 29 == 0 else 0.0,
                "gust_ms": 2 + (seed + i) % 11,
            })
        return rows

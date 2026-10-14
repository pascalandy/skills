"""Readings for one UTC day, per station, from the collector."""
import json
import logging
import urllib.request

log = logging.getLogger(__name__)


class CollectorSource:
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout

    def readings(self, station, day):
        url = f"{self.url}/{station}/{day.isoformat()}"
        with urllib.request.urlopen(url, timeout=self.timeout) as resp:
            return json.load(resp)["readings"]


def fetch_day(cfg, day, source=None):
    source = source or CollectorSource(cfg.source_url, cfg.timeout)
    found = {}
    for station in cfg.stations:
        rows = _get(source, station, day)
        if rows is None:
            log.info("station %s offline", station)
        else:
            found[station] = rows
    return found


def _get(source, station, day):
    for attempt in (1, 2):
        try:
            return source.readings(station, day)
        except (OSError, ValueError, KeyError) as exc:
            log.debug("station %s attempt %d failed: %s", station, attempt, exc)
    return None

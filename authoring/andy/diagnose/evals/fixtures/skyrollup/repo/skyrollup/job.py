"""The nightly run: fetch, summarize, publish, then record status."""
import datetime as dt
import logging

from . import fetch, publish, status, summarize

log = logging.getLogger(__name__)


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cfg, source=None, now=None):
    started = now or utc_now()
    day = (started - dt.timedelta(days=1)).date()
    log.info("run started for %s", day.isoformat())
    readings = fetch.fetch_day(cfg, day, source=source)
    log.info("fetched %d of %d stations", len(readings), len(cfg.stations))
    summary = summarize.summarize(day, readings, expected=len(cfg.stations))
    log.info("summary computed: %d stations reporting", summary["stations_reporting"])
    path = publish.publish(cfg, summary)
    status.write_status(cfg.status_file, {
        "last_success": stamp(now or utc_now()),
        "result": "ok",
        "day": summary["day"],
        "stations_reporting": summary["stations_reporting"],
        "stations_expected": summary["stations_expected"],
        "summary": path.name,
    })
    log.info("status written")
    return path

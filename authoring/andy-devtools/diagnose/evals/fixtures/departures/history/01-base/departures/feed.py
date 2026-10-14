"""Load a transit feed from its CSV files.

A feed folder holds stops.txt, routes.txt, trips.txt and stop_times.txt.
The folder name, after following links, is the feed version.
"""

import csv
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Stop:
    stop_id: str
    name: str
    location_type: int
    parent_station: str


@dataclass(frozen=True)
class Route:
    route_id: str
    short_name: str
    long_name: str


@dataclass(frozen=True)
class Trip:
    trip_id: str
    route_id: str
    service_id: str
    headsign: str


@dataclass(frozen=True)
class StopTime:
    trip_id: str
    stop_id: str
    departure: int  # seconds after midnight of the service day


@dataclass
class Feed:
    version: str
    stops: dict
    routes: dict
    trips: dict
    times_by_stop: dict  # stop_id -> [StopTime], soonest first


def parse_time(text):
    hours, minutes, seconds = (int(part) for part in text.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def format_time(seconds):
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}"


def _rows(folder, name):
    with open(os.path.join(folder, name), newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def load_feed(folder):
    stops = {}
    for row in _rows(folder, "stops.txt"):
        stops[row["stop_id"]] = Stop(
            row["stop_id"],
            row["stop_name"],
            int(row.get("location_type") or 0),
            row.get("parent_station") or "",
        )
    routes = {
        row["route_id"]: Route(row["route_id"], row["route_short_name"], row["route_long_name"])
        for row in _rows(folder, "routes.txt")
    }
    trips = {
        row["trip_id"]: Trip(row["trip_id"], row["route_id"], row["service_id"], row["trip_headsign"])
        for row in _rows(folder, "trips.txt")
    }
    times_by_stop = {}
    for row in _rows(folder, "stop_times.txt"):
        stop_time = StopTime(row["trip_id"], row["stop_id"], parse_time(row["departure_time"]))
        times_by_stop.setdefault(stop_time.stop_id, []).append(stop_time)
    for times in times_by_stop.values():
        times.sort(key=lambda stop_time: stop_time.departure)
    version = os.path.basename(os.path.realpath(folder))
    return Feed(version, stops, routes, trips, times_by_stop)

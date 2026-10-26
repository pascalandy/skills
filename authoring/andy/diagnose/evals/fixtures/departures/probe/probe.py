#!/usr/bin/env python3
"""Read-only views of the departures-api production logs, station screens and feed imports."""

import argparse
import csv
import io
import json
import os
import sys
import tarfile
from urllib.parse import quote

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".probe", "data.tgz")
DAY = "2026-10-14"
STOPS = ("APT", "BAY", "CEN", "ELM", "FLD", "GLN", "HRB", "HRB-1", "HRB-2", "MKT", "NGT", "OAK",
         "PRD", "STA", "UNV", "WLP")
SCREEN_STOPS = ("HRB", "MKT", "UNV")
HOSTS = ("api-1", "api-2", "api-3")
IMPORTS = ("0550", "0750")
CURRENT_IMPORT = "0750"
DEFAULT_WINDOW = "07:30-08:30"
SERVICES = ("WKD", "SAT", "SUN")
LOCATION_TYPES = {0: "stop or platform", 1: "station"}
STALE = "ERROR realtime: vehicle position stale"
LAG = "WARN upstream realtime lag 40s"

HELP = f"""usage: ./probe <check> [options]

Read-only views of the departures-api production API logs, station screens and feed imports
for {DAY}. Request metrics cover 06:00-08:45 UTC, service events 00:00-08:45 UTC.

checks:
  requests     --stop S [--window W]      per-minute departures requests: count, 200s, mean items, cache hits, p95, clients
  errors       --stop S [--window W]      per-minute count of each error and warning message
  latency      --stop S [--window W]      p50, p95, p99 per 10 minutes
  events       [--host H] [--window W]    service events per host: startups and feed reloads
  screens      [--stop S]                 station screens: firmware, configured stop_id, last poll, items shown
  feed-stop    STOP_ID [--import I]       a stop's row, its child stops, and the trips stopping there
  feed-diff    --from I --to I            changed stops and trip counts between two imports
  feed-export  --import I --out DIR       write an import's CSV files to DIR
  search       --q TEXT                   what the website's stop search returns now

values:
  S  requests, errors, latency: {" ".join(STOPS)}
     screens: {" ".join(SCREEN_STOPS)} (default: every screen)
  H  {" ".join(HOSTS)} (default: every host)
  I  0550 (feed {DAY}T0550), 0750 (feed {DAY}T0750, current); feed-stop defaults to 0750
  W  HH:MM-HH:MM in UTC, end excluded; default {DEFAULT_WINDOW}
"""


class UsageError(Exception):
    pass


def fail(message, code=2):
    print(f"probe: {message}", file=sys.stderr)
    sys.exit(code)


class Data:
    def __init__(self):
        if not os.path.exists(DATA):
            fail(f"missing {DATA}", 1)
        self._tar = tarfile.open(DATA, "r:gz")
        self._members = {}
        for member in self._tar.getmembers():
            name = member.name[2:] if member.name.startswith("./") else member.name
            self._members[name] = member

    def text(self, name):
        return self._tar.extractfile(self._members[name]).read().decode("utf-8")

    def table(self, name, delimiter="\t"):
        return list(csv.DictReader(io.StringIO(self.text(name)), delimiter=delimiter))

    def imports(self):
        return {row["import"]: row for row in self.table("imports.tsv")}

    def feed_files(self, import_id):
        feed = self.imports()[import_id]["feed"]
        prefix = f"feeds/{feed}/"
        return feed, sorted(name[len(prefix):] for name in self._members
                            if name.startswith(prefix) and name.endswith(".txt") and "/._" not in name)

    def feed_table(self, import_id, name):
        feed = self.imports()[import_id]["feed"]
        return self.table(f"feeds/{feed}/{name}", delimiter=",")


def minutes(text):
    try:
        hours, mins = text.split(":")
        value = int(hours) * 60 + int(mins)
    except ValueError:
        raise UsageError(f"bad time '{text}', expected HH:MM")
    if not 0 <= value <= 24 * 60:
        raise UsageError(f"bad time '{text}'")
    return value


def clock(value):
    return f"{value // 60:02d}:{value % 60:02d}"


def window(text):
    start, sep, end = text.partition("-")
    if not sep:
        raise UsageError(f"bad window '{text}', expected HH:MM-HH:MM")
    lo, hi = minutes(start), minutes(end)
    if hi <= lo:
        raise UsageError(f"bad window '{text}', end must be after start")
    return lo, hi


def check_stop(stop, allowed):
    if stop not in allowed:
        raise UsageError(f"unknown stop '{stop}' (accepted: {' '.join(allowed)})")


def check_import(value):
    if value not in IMPORTS:
        raise UsageError(f"unknown import '{value}' (accepted: {' '.join(IMPORTS)})")


def header(title, stop, span):
    return f"{title}, stop {stop}, {DAY} {clock(span[0])}-{clock(span[1])} UTC"


def rows_by_minute(data, stop, span):
    rows = {}
    for row in data.table("requests.tsv"):
        if row["stop"] == stop and span[0] <= minutes(row["minute"]) < span[1]:
            rows[minutes(row["minute"])] = row
    return rows


def cmd_requests(data, args):
    check_stop(args.stop, STOPS)
    span = window(args.window)
    rows = rows_by_minute(data, args.stop, span)
    print(header("departures requests", args.stop, span))
    print(f"{'minute':<6}  {'requests':>8}  {'200s':>4}  {'items':>5}  {'cache_hit':<12}  {'p95_ms':>6}  clients")
    for minute in range(*span):
        row = rows.get(minute)
        if row is None:
            print(f"{clock(minute):<6}  {0:>8}  {0:>4}  {'-':>5}  {'-':<12}  {'-':>6}  -")
            continue
        count = int(row["requests"])
        hit, miss, off = int(row["hit"]), int(row["miss"]), int(row["off"])
        if hit + miss == 0:
            cache = "off"
        else:
            cache = f"{round(100 * hit / (hit + miss))}%" + (f" ({off} off)" if off else "")
        clients = ", ".join(f"{name} {row[name]}" for name in ("screen", "web") if int(row[name]))
        print(f"{clock(minute):<6}  {count:>8}  {int(row['ok']):>4}  {int(row['items_sum']) / count:>5.1f}  "
              f"{cache:<12}  {row['p95_ms']:>6}  {clients}")


def cmd_errors(data, args):
    check_stop(args.stop, STOPS)
    span = window(args.window)
    rows = rows_by_minute(data, args.stop, span)
    print(header("errors and warnings", args.stop, span))
    print(f"  [1] {STALE}")
    print(f"  [2] {LAG}")
    print(f"{'minute':<6}  {'requests':>8}  {'[1]':>5}  {'[2]':>5}")
    total = stale = lag = 0
    for minute in range(*span):
        row = rows.get(minute, {"requests": 0, "stale": 0, "lag40": 0})
        count, first, second = int(row["requests"]), int(row["stale"]), int(row["lag40"])
        total, stale, lag = total + count, stale + first, lag + second
        print(f"{clock(minute):<6}  {count:>8}  {first:>5}  {second:>5}")
    print(f"{'total':<6}  {total:>8}  {stale:>5}  {lag:>5}")
    if total:
        print(f"{'share':<6}  {'':>8}  {100 * stale / total:>4.1f}%  {100 * lag / total:>4.1f}%")


def cmd_latency(data, args):
    check_stop(args.stop, STOPS)
    span = window(args.window)
    rows = {minutes(row["from"]): row for row in data.table("latency.tsv") if row["stop"] == args.stop}
    print(header("departures latency per 10 minutes", args.stop, span))
    print(f"{'from':<5}  {'to':<5}  {'requests':>8}  {'p50_ms':>6}  {'p95_ms':>6}  {'p99_ms':>6}")
    first = span[0] + (-span[0]) % 10
    for start in range(first, span[1], 10):
        row = rows.get(start)
        if row is None:
            print(f"{clock(start):<5}  {clock(start + 10):<5}  {0:>8}  {'-':>6}  {'-':>6}  {'-':>6}")
        else:
            print(f"{clock(start):<5}  {clock(start + 10):<5}  {int(row['requests']):>8}  "
                  f"{row['p50_ms']:>6}  {row['p95_ms']:>6}  {row['p99_ms']:>6}")


def cmd_events(data, args):
    if args.host is not None and args.host not in HOSTS:
        raise UsageError(f"unknown host '{args.host}' (accepted: {' '.join(HOSTS)})")
    span = window(args.window)
    hosts = [args.host] if args.host else list(HOSTS)
    print(f"service events, {', '.join(hosts)}, {DAY} {clock(span[0])}-{clock(span[1])} UTC")
    shown = 0
    for line in data.text("events.log").splitlines():
        stamp, host = line.split(" ", 2)[:2]
        if host in hosts and span[0] <= minutes(stamp[11:16]) < span[1]:
            print(line)
            shown += 1
    if not shown:
        print("no events in this window")


def cmd_screens(data, args):
    if args.stop is not None:
        check_stop(args.stop, SCREEN_STOPS)
    print(f"station screens, {DAY}, as of 08:44:59 UTC")
    print(f"{'screen':<11}  {'firmware':<8}  {'stop_id':<7}  {'limit':>5}  {'last_poll':<9}  "
          f"{'items_shown':>11}  last_nonempty")
    for row in data.table("screens.tsv"):
        if args.stop and row["stop_id"] != args.stop:
            continue
        print(f"{row['screen']:<11}  {row['firmware']:<8}  {row['stop_id']:<7}  {row['limit']:>5}  "
              f"{row['last_poll']:<9}  {row['items']:>11}  {row['last_nonempty']}")


def feed_summary(data, import_id):
    info = data.imports()[import_id]
    stops = data.feed_table(import_id, "stops.txt")
    trips = data.feed_table(import_id, "trips.txt")
    return info, stops, trips


def trips_by_stop(data, import_id):
    found = {}
    for row in data.feed_table(import_id, "stop_times.txt"):
        found.setdefault(row["stop_id"], set()).add(row["trip_id"])
    return found


def describe_trips(trip_ids, trips):
    by_service = {service: 0 for service in SERVICES}
    by_route = {}
    for trip_id in trip_ids:
        trip = trips[trip_id]
        by_service[trip["service_id"]] = by_service.get(trip["service_id"], 0) + 1
        by_route[trip["route_id"]] = by_route.get(trip["route_id"], 0) + 1
    services = ", ".join(f"{name} {count}" for name, count in by_service.items())
    routes = ", ".join(f"{name} {count}" for name, count in sorted(by_route.items())) or "-"
    return f"{len(trip_ids)} ({services})", routes


def cmd_feed_stop(data, args):
    check_import(args.import_id)
    info, stops, trip_rows = feed_summary(data, args.import_id)
    by_id = {row["stop_id"]: row for row in stops}
    stop = by_id.get(args.stop_id)
    if stop is None:
        raise UsageError(f"no stop '{args.stop_id}' in import {args.import_id}")
    trips = {row["trip_id"]: row for row in trip_rows}
    served = trips_by_stop(data, args.import_id)
    print(f"import {args.import_id}: feed {info['feed']}, published {info['published']}, "
          f"stops {len(stops)}, trips {len(trips)}")
    print()
    location_type = int(stop["location_type"] or 0)
    parent = stop["parent_station"]
    count, routes = describe_trips(served.get(stop["stop_id"], set()), trips)
    print(f"{'stop_id':<16}{stop['stop_id']}")
    print(f"{'stop_name':<16}{stop['stop_name']}")
    print(f"{'location_type':<16}{location_type} ({LOCATION_TYPES.get(location_type, 'other')})")
    print(f"{'parent_station':<16}{parent + ' (' + by_id[parent]['stop_name'] + ')' if parent else '-'}")
    print(f"{'trips stopping':<16}{count}")
    print(f"{'routes':<16}{routes}")
    children = [row for row in stops if row["parent_station"] == stop["stop_id"]]
    print(f"{'child stops':<16}{len(children) if children else 'none'}")
    for child in children:
        count, routes = describe_trips(served.get(child["stop_id"], set()), trips)
        print(f"  {child['stop_id']:<7}{child['stop_name']:<20}trips stopping {count}, routes {routes}")


def cmd_feed_diff(data, args):
    check_import(args.from_id)
    check_import(args.to_id)
    old_info, old_stops, old_trips = feed_summary(data, args.from_id)
    new_info, new_stops, new_trips = feed_summary(data, args.to_id)
    old_by_id = {row["stop_id"]: row for row in old_stops}
    new_by_id = {row["stop_id"]: row for row in new_stops}
    added = [row for row in new_stops if row["stop_id"] not in old_by_id]
    removed = [row for row in old_stops if row["stop_id"] not in new_by_id]
    changed = []
    for row in new_stops:
        before = old_by_id.get(row["stop_id"])
        if before is None:
            continue
        for field in ("stop_name", "location_type", "parent_station"):
            if before[field] != row[field]:
                changed.append(f"  {row['stop_id']:<7}{field}: {before[field] or '-'} -> {row[field] or '-'}")
    old_trip_ids = {row["trip_id"]: row for row in old_trips}
    new_trip_ids = {row["trip_id"]: row for row in new_trips}
    trips_added = [row for row in new_trips if row["trip_id"] not in old_trip_ids]
    trips_removed = [row for row in old_trips if row["trip_id"] not in new_trip_ids]

    print(f"feed diff {old_info['feed']} -> {new_info['feed']}")
    print(f"stops  {len(old_stops)} -> {len(new_stops)}   added {len(added)}, removed {len(removed)}, "
          f"changed {len(changed)}")
    print(f"trips  {len(old_trips)} -> {len(new_trips)}   added {len(trips_added)}, removed {len(trips_removed)}")
    print()
    print("added stops")
    for row in added or []:
        print(f"  {row['stop_id']:<7}{row['stop_name']:<20}location_type {row['location_type']}, "
              f"parent_station {row['parent_station'] or '-'}")
    if not added:
        print("  none")
    print("removed stops")
    for row in removed:
        print(f"  {row['stop_id']:<7}{row['stop_name']}")
    if not removed:
        print("  none")
    print("changed stops")
    print("\n".join(changed) if changed else "  none")
    print("added trips")
    groups = {}
    for row in trips_added:
        groups.setdefault(row["route_id"], {}).setdefault(row["service_id"], 0)
        groups[row["route_id"]][row["service_id"]] += 1
    for route, services in sorted(groups.items()):
        detail = ", ".join(f"{name} {count}" for name, count in services.items())
        print(f"  route {route}: {sum(services.values())} ({detail})")
    if not groups:
        print("  none")
    print("removed trips")
    print(f"  {len(trips_removed)}" if trips_removed else "  none")

    old_served = trips_by_stop(data, args.from_id)
    new_served = trips_by_stop(data, args.to_id)
    print("trips stopping, changed stops only")
    print(f"  {'stop':<7}{'from':>6}{'to':>6}")
    for stop_id in sorted(set(old_served) | set(new_served)):
        before, after = len(old_served.get(stop_id, ())), len(new_served.get(stop_id, ()))
        if before != after:
            print(f"  {stop_id:<7}{before:>6}{after:>6}")


def cmd_feed_export(data, args):
    check_import(args.import_id)
    feed, names = data.feed_files(args.import_id)
    os.makedirs(args.out, exist_ok=True)
    for name in names:
        with open(os.path.join(args.out, name), "w", encoding="utf-8", newline="") as handle:
            handle.write(data.text(f"feeds/{feed}/{name}"))
    stops = len(data.feed_table(args.import_id, "stops.txt"))
    trips = len(data.feed_table(args.import_id, "trips.txt"))
    print(f"wrote {', '.join(names)} to {args.out} (feed {feed}: stops {stops}, trips {trips})")


def cmd_search(data, args):
    feed, _ = data.feed_files(CURRENT_IMPORT)
    text = args.q.strip()
    print(f"GET /v1/search?q={quote(text)}  (production, feed {feed})")
    if not text:
        print(json.dumps({"ok": False, "errors": ["q is required"]}))
        return
    needle = text.casefold()
    stops = sorted(
        (row for row in data.feed_table(CURRENT_IMPORT, "stops.txt") if needle in row["stop_name"].casefold()),
        key=lambda row: (row["stop_name"], row["stop_id"]),
    )
    found = [
        {"stop_id": row["stop_id"], "name": row["stop_name"], "location_type": int(row["location_type"] or 0),
         "parent_station": row["parent_station"]}
        for row in stops[:20]
    ]
    print(json.dumps({"ok": True, "query": text, "stops": found}))


def parser_for(check):
    parser = argparse.ArgumentParser(prog=f"./probe {check}")
    if check in ("requests", "errors", "latency"):
        parser.add_argument("--stop", required=True)
    if check in ("requests", "errors", "latency", "events"):
        parser.add_argument("--window", default=DEFAULT_WINDOW)
    if check == "events":
        parser.add_argument("--host")
    if check == "screens":
        parser.add_argument("--stop")
    if check == "feed-stop":
        parser.add_argument("stop_id")
        parser.add_argument("--import", dest="import_id", default=CURRENT_IMPORT)
    if check == "feed-diff":
        parser.add_argument("--from", dest="from_id", required=True)
        parser.add_argument("--to", dest="to_id", required=True)
    if check == "feed-export":
        parser.add_argument("--import", dest="import_id", required=True)
        parser.add_argument("--out", required=True)
    if check == "search":
        parser.add_argument("--q", required=True)
    return parser


CHECKS = {
    "requests": cmd_requests,
    "errors": cmd_errors,
    "latency": cmd_latency,
    "events": cmd_events,
    "screens": cmd_screens,
    "feed-stop": cmd_feed_stop,
    "feed-diff": cmd_feed_diff,
    "feed-export": cmd_feed_export,
    "search": cmd_search,
}


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP, end="")
        return 0
    check = argv[0]
    if check not in CHECKS:
        fail(f"unknown check '{check}' (see ./probe --help)")
    args = parser_for(check).parse_args(argv[1:])
    try:
        CHECKS[check](Data(), args)
    except UsageError as exc:
        fail(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

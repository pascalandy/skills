"""Write the two Tamarack feed imports the probe serves: 2026-10-14T0550 and 2026-10-14T0750.

Usage: python3 feedgen.py OUT_DIR
Deterministic: the same files on every run.
"""

import csv
import os
import random
import sys

STATIONS = [
    ("NGT", "Northgate"), ("WLP", "Willow Park"), ("CEN", "Central"), ("MKT", "Market Street"),
    ("HRB", "Harbor"), ("PRD", "Pier Road"), ("APT", "Airport"), ("FLD", "Fairfield"),
    ("BAY", "Bayside"), ("STA", "Stadium"), ("UNV", "University"), ("ELM", "Elmhurst"),
    ("GLN", "Glenview"), ("OAK", "Oakridge"),
]
RAIL_LINES = [
    ("SHL", "Shoreline", ["NGT", "WLP", "CEN", "MKT", "HRB", "PRD"], {"WKD": 84, "SAT": 19, "SUN": 17}),
    ("HBX", "Harbor Express", ["APT", "FLD", "CEN", "HRB", "BAY"], {"WKD": 66, "SAT": 15, "SUN": 13}),
    ("UNL", "University Line", ["CEN", "STA", "UNV", "ELM", "GLN", "OAK"], {"WKD": 70, "SAT": 16, "SUN": 14}),
]
PLATFORMS = {"SHL": "HRB-1", "HBX": "HRB-2"}
STREETS = [
    "Alder Rd", "Ash St", "Aspen Way", "Beacon St", "Birch Ave", "Brook Rd", "Canal St", "Cedar St",
    "Chestnut St", "Clover Ln", "Copper Rd", "Dogwood Ln", "Eastview Dr", "Ferry Rd", "Fir St",
    "Forest Ave", "Garden St", "Granite Way", "Hawthorn Rd", "Hillcrest Dr", "Juniper St", "Kestrel Way",
    "Lake Rd", "Laurel Ave", "Linden St", "Maple Ave", "Market St", "Meadow Ln", "Mill Rd",
    "Northfield Rd", "Orchard St", "Park Ave", "Pine St", "Quarry Ln", "Railway Ave", "Ridge Rd",
    "River Rd", "Rowan St", "Spruce St", "Station Rd", "Summit Ave", "Tamarack Blvd", "Union St",
    "Valley Rd", "Walnut St", "Willow St", "Sawmill Rd",
]
CROSS = [f"{n}{'st' if n % 10 == 1 and n != 11 else 'nd' if n % 10 == 2 and n != 12 else 'rd' if n % 10 == 3 and n != 13 else 'th'} St" for n in range(1, 21)]
CROSS += ["Main St", "Church St", "School Rd", "Bridge St", "King St", "Queen St", "Mission St",
          "Center St", "Front St", "High St"]
BUS_STOPS = 1198
BUS_ROUTES = 120
BUS_TRIPS = 8590
RENAMES = {"Alder Rd & 9th St": "Alder Rd & Ninth St", "Quarry Ln (temp)": "Quarry Lane"}
ADDED_ROUTE = "61"


def hhmm(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"


def spread(first, last, count):
    if count == 1:
        return [first]
    return [first + round(i * (last - first) / (count - 1)) for i in range(count)]


def build():
    rng = random.Random(14102026)
    stops = [{"stop_id": sid, "stop_name": name, "location_type": "0", "parent_station": ""}
             for sid, name in STATIONS]

    names = [f"{street} & {cross}" for street in STREETS for cross in CROSS]
    names.remove("Alder Rd & 9th St")
    rng.shuffle(names)
    names = names[:BUS_STOPS - 2]
    names.insert(417, "Alder Rd & 9th St")
    names.insert(905, "Quarry Ln (temp)")
    ids = sorted(rng.sample(range(1001, 4000), BUS_STOPS))
    bus = [{"stop_id": f"B{num}", "stop_name": name, "location_type": "0", "parent_station": ""}
           for num, name in zip(ids, names)]
    stops += bus

    routes, trips, times = [], [], {}

    def add_trips(route_id, service, path, count, first, last, steps, names_by_id):
        out = []
        forward = (count + 1) // 2
        for direction, n in ((0, forward), (1, count - forward)):
            order = path if direction == 0 else path[::-1]
            gaps = steps if direction == 0 else steps[::-1]
            for start in spread(first + direction * 8, last, n):
                out.append((start, order, gaps))
        out.sort(key=lambda trip: (trip[0], trip[1][0]))
        for seq, (start, order, gaps) in enumerate(out, 1):
            trip_id = f"{route_id}-{service}-{seq:03d}"
            trips.append({"route_id": route_id, "service_id": service, "trip_id": trip_id,
                          "trip_headsign": names_by_id[order[-1]]})
            clock, rows = start, []
            for i, stop_id in enumerate(order):
                rows.append((stop_id, hhmm(clock)))
                if i < len(gaps):
                    clock += gaps[i]
            times[trip_id] = rows

    names_by_id = {stop["stop_id"]: stop["stop_name"] for stop in stops}
    for route_id, long_name, path, per_service in RAIL_LINES:
        routes.append({"route_id": route_id, "route_short_name": route_id,
                       "route_long_name": long_name, "route_type": "2"})
        for service, count in per_service.items():
            add_trips(route_id, service, path, count, 5 * 60, 23 * 60 + 30, [4] * (len(path) - 1), names_by_id)

    order = list(range(BUS_STOPS))
    rng.shuffle(order)
    sizes = [rng.randint(6, 14) for _ in range(BUS_ROUTES)]
    while sum(sizes) != BUS_STOPS:
        k = rng.randrange(BUS_ROUTES)
        if sum(sizes) > BUS_STOPS and sizes[k] > 6:
            sizes[k] -= 1
        elif sum(sizes) < BUS_STOPS and sizes[k] < 14:
            sizes[k] += 1
    weights = [rng.randint(50, 95) for _ in range(BUS_ROUTES)]
    counts = [w * BUS_TRIPS // sum(weights) for w in weights]
    for k in range(BUS_TRIPS - sum(counts)):
        counts[k] += 1
    position = 0
    for number in range(1, BUS_ROUTES + 1):
        size = sizes[number - 1]
        path = [bus[i]["stop_id"] for i in order[position:position + size]]
        position += size
        steps = [rng.randint(1, 3) for _ in range(size - 1)]
        first_street = names_by_id[path[0]].split(" & ")[0]
        last_street = names_by_id[path[-1]].split(" & ")[0]
        routes.append({"route_id": str(number), "route_short_name": str(number),
                       "route_long_name": f"{first_street} - {last_street}", "route_type": "3"})
        total = counts[number - 1]
        weekday = round(total * 0.7)
        saturday = round(total * 0.16)
        for service, count in (("WKD", weekday), ("SAT", saturday), ("SUN", total - weekday - saturday)):
            add_trips(str(number), service, path, count, 5 * 60 + 30, 23 * 60 + 20, steps, names_by_id)
    return stops, routes, trips, times


def later_import(stops, routes, trips, times):
    stops = [dict(stop) for stop in stops]
    for stop in stops:
        if stop["stop_id"] == "HRB":
            stop["location_type"] = "1"
        if stop["stop_name"] in RENAMES:
            stop["stop_name"] = RENAMES[stop["stop_name"]]
    at = next(i for i, stop in enumerate(stops) if stop["stop_id"] == "HRB") + 1
    stops[at:at] = [
        {"stop_id": "HRB-1", "stop_name": "Harbor Platform 1", "location_type": "0", "parent_station": "HRB"},
        {"stop_id": "HRB-2", "stop_name": "Harbor Platform 2", "location_type": "0", "parent_station": "HRB"},
    ]
    route_of = {trip["trip_id"]: trip["route_id"] for trip in trips}
    new_times = {}
    for trip_id, rows in times.items():
        platform = PLATFORMS.get(route_of[trip_id])
        new_times[trip_id] = [(platform if stop_id == "HRB" and platform else stop_id, t) for stop_id, t in rows]

    trips = [dict(trip) for trip in trips]
    model = {}
    for trip in trips:
        if trip["route_id"] == ADDED_ROUTE:
            model.setdefault((trip["service_id"], new_times[trip["trip_id"]][0][0]), trip)
    last = max(i for i, trip in enumerate(trips) if trip["route_id"] == ADDED_ROUTE)
    added = []
    for service, first in (("SAT", 7 * 60 + 5), ("SUN", 7 * 60 + 35)):
        seq = sum(1 for trip in trips if trip["route_id"] == ADDED_ROUTE and trip["service_id"] == service)
        for k in range(9):
            seq += 1
            start = first + k * 100
            direction = k % 2
            sample = [m for key, m in model.items() if key[0] == service][direction]
            rows = new_times[sample["trip_id"]]
            offset = start - _minutes(rows[0][1])
            trip_id = f"{ADDED_ROUTE}-{service}-{seq:03d}"
            added.append({"route_id": ADDED_ROUTE, "service_id": service, "trip_id": trip_id,
                          "trip_headsign": sample["trip_headsign"]})
            new_times[trip_id] = [(stop_id, hhmm(_minutes(t) + offset)) for stop_id, t in rows]
    trips[last + 1:last + 1] = added
    return stops, routes, trips, new_times


def _minutes(text):
    hours, minutes, _ = text.split(":")
    return int(hours) * 60 + int(minutes)


def write(folder, stops, routes, trips, times):
    os.makedirs(folder, exist_ok=True)

    def table(name, fields, rows):
        with open(os.path.join(folder, name), "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(fields)
            writer.writerows(rows)

    table("stops.txt", ["stop_id", "stop_name", "location_type", "parent_station"],
          [[s["stop_id"], s["stop_name"], s["location_type"], s["parent_station"]] for s in stops])
    table("routes.txt", ["route_id", "route_short_name", "route_long_name", "route_type"],
          [[r["route_id"], r["route_short_name"], r["route_long_name"], r["route_type"]] for r in routes])
    table("trips.txt", ["route_id", "service_id", "trip_id", "trip_headsign"],
          [[t["route_id"], t["service_id"], t["trip_id"], t["trip_headsign"]] for t in trips])
    table("stop_times.txt", ["trip_id", "stop_id", "departure_time"],
          [[t["trip_id"], stop_id, when] for t in trips for stop_id, when in times[t["trip_id"]]])


def main():
    out = sys.argv[1]
    first = build()
    write(os.path.join(out, "2026-10-14T0550"), *first)
    write(os.path.join(out, "2026-10-14T0750"), *later_import(*first))


if __name__ == "__main__":
    main()

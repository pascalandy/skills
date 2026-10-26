"""Departure lookups and stop search over a loaded feed."""

from .feed import format_time

# One weekday timetable, then Saturday and Sunday ones.
SERVICE_BY_WEEKDAY = ("WKD", "WKD", "WKD", "WKD", "WKD", "SAT", "SUN")
SEARCH_LIMIT = 20


def departures_for(feed, stop_id, now, limit):
    """Next departures from stop_id at or after now, soonest first."""
    service = SERVICE_BY_WEEKDAY[now.weekday()]
    seconds = now.hour * 3600 + now.minute * 60 + now.second
    found = []
    for stop_time in feed.times_by_stop.get(stop_id, ()):
        if stop_time.departure < seconds:
            continue
        trip = feed.trips[stop_time.trip_id]
        if trip.service_id != service:
            continue
        found.append({
            "trip_id": trip.trip_id,
            "route": feed.routes[trip.route_id].short_name,
            "headsign": trip.headsign,
            "departs": format_time(stop_time.departure),
        })
        if len(found) == limit:
            break
    return found


def search(feed, text):
    """Stops whose name contains text, ignoring case, sorted by name."""
    needle = text.casefold()
    matches = sorted(
        (stop for stop in feed.stops.values() if needle in stop.name.casefold()),
        key=lambda stop: (stop.name, stop.stop_id),
    )
    return [
        {
            "stop_id": stop.stop_id,
            "name": stop.name,
            "location_type": stop.location_type,
            "parent_station": stop.parent_station,
        }
        for stop in matches[:SEARCH_LIMIT]
    ]

"""Daily summary across the network."""
from statistics import mean

MIN_READINGS = 12


def _round(value):
    return None if value is None else round(value, 1)


def station_summary(station, rows):
    temps = [r["temp_c"] for r in rows if r.get("temp_c") is not None]
    gusts = [r["gust_ms"] for r in rows if r.get("gust_ms") is not None]
    return {
        "station": station,
        "readings": len(rows),
        "temp_min_c": _round(min(temps, default=None)),
        "temp_max_c": _round(max(temps, default=None)),
        "temp_mean_c": _round(mean(temps)) if temps else None,
        "rain_mm": _round(sum(r.get("rain_mm") or 0 for r in rows)),
        "gust_max_ms": _round(max(gusts, default=None)),
    }


def summarize(day, readings, expected):
    stations = [
        station_summary(station, rows)
        for station, rows in sorted(readings.items())
        if len(rows) >= MIN_READINGS
    ]

    def network(key, fn):
        values = [s[key] for s in stations if s[key] is not None]
        return _round(fn(values)) if values else None

    return {
        "day": day.isoformat(),
        "stations_expected": expected,
        "stations_reporting": len(stations),
        "network": {
            "temp_min_c": network("temp_min_c", min),
            "temp_max_c": network("temp_max_c", max),
            "rain_mean_mm": network("rain_mm", mean),
            "gust_max_ms": network("gust_max_ms", max),
        },
        "stations": stations,
    }

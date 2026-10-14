"""Live delays from the vehicle tracking upstream."""

import json
import logging
import time
import urllib.request

log = logging.getLogger("departures")

STALE_AFTER = 120  # seconds since the snapshot's newest vehicle position
LAG_WARN = 40  # seconds behind, as reported by the upstream


class Realtime:
    def __init__(self, base_url, timeout=0.3):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def delays(self, stop_id):
        """trip_id -> delay in seconds, for vehicles heading to stop_id."""
        url = f"{self.base_url}/v2/stops/{stop_id}/vehicles"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                snapshot = json.load(response)
        except (OSError, ValueError) as exc:
            log.warning("realtime: upstream unavailable (%s)", exc)
            return {}
        lag = int(snapshot.get("lag_s", 0))
        if lag >= LAG_WARN:
            log.warning("upstream realtime lag %ds", lag // 10 * 10)
        if time.time() - snapshot.get("positions_at", 0) > STALE_AFTER:
            log.error("realtime: vehicle position stale (stop %s)", stop_id)
            return {}
        return {vehicle["trip_id"]: int(vehicle["delay_s"]) for vehicle in snapshot.get("vehicles", [])}

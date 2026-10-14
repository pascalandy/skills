"""Short-lived cache for departures responses."""

import threading


class ResponseCache:
    """Departures computed for a stop, kept for the minute they were computed in.

    Screens poll every 30 seconds and timetable departures only change on
    the minute, so later polls in the same minute can reuse the first answer.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._minute = None
        self._entries = {}

    def get(self, stop_id, minute):
        with self._lock:
            return self._entries.get((stop_id, minute))

    def put(self, stop_id, minute, departures):
        with self._lock:
            if minute != self._minute:
                # A new minute: everything kept so far is out of date.
                self._entries.clear()
                self._minute = minute
            self._entries[(stop_id, minute)] = departures

    def clear(self):
        with self._lock:
            self._entries.clear()
            self._minute = None

    def __len__(self):
        with self._lock:
            return len(self._entries)

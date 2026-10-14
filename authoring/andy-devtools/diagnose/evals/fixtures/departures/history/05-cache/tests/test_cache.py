import io
import os
import unittest
from datetime import datetime, timezone

from departures.cache import ResponseCache
from departures.server import App

FEED = os.path.join(os.path.dirname(__file__), "data", "feed")
MINUTE = "2026-10-07T07:30"
NEXT_MINUTE = "2026-10-07T07:31"


class ResponseCacheTest(unittest.TestCase):
    def test_miss_then_hit(self):
        cache = ResponseCache()
        self.assertIsNone(cache.get("MKT", MINUTE))
        cache.put("MKT", MINUTE, [{"trip_id": "SHL-WKD-002"}])
        self.assertEqual(cache.get("MKT", MINUTE), [{"trip_id": "SHL-WKD-002"}])

    def test_stops_are_kept_apart(self):
        cache = ResponseCache()
        cache.put("MKT", MINUTE, [])
        self.assertIsNone(cache.get("HRB", MINUTE))

    def test_new_minute_drops_older_entries(self):
        cache = ResponseCache()
        cache.put("MKT", MINUTE, [])
        cache.put("HRB", NEXT_MINUTE, [])
        self.assertIsNone(cache.get("MKT", MINUTE))
        self.assertEqual(len(cache), 1)

    def test_clear(self):
        cache = ResponseCache()
        cache.put("MKT", MINUTE, [])
        cache.clear()
        self.assertEqual(len(cache), 0)


class AppCacheTest(unittest.TestCase):
    def make_app(self, **options):
        moment = datetime(2026, 10, 7, 7, 30, 12, tzinfo=timezone.utc)
        return App(FEED, clock=lambda: moment, request_log=io.StringIO(), **options)

    def test_second_request_in_a_minute_is_a_hit(self):
        app = self.make_app()
        first, first_state = app.departures("HRB", 8)
        second, second_state = app.departures("HRB", 8)
        self.assertEqual((first_state, second_state), ("miss", "hit"))
        self.assertEqual(first, second)
        self.assertEqual(len(second), 3)

    def test_cache_off(self):
        app = self.make_app(use_cache=False)
        found, state = app.departures("HRB", 8)
        self.assertEqual(state, "off")
        self.assertEqual(len(found), 3)


if __name__ == "__main__":
    unittest.main()

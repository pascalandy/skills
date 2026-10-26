import datetime as dt
import tempfile
import unittest

from helpers import FakeSource, make_config
from skyrollup import fetch

DAY = dt.date(2026, 8, 10)


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_flaky_station_is_retried(self):
        source = FakeSource(flaky={"ws-02"})
        found = fetch.fetch_day(self.cfg, DAY, source=source)
        self.assertEqual(sorted(found), ["ws-01", "ws-02", "ws-03"])
        self.assertEqual(source.calls.count("ws-02"), 2)

    def test_offline_station_logged_at_warning(self):
        with self.assertLogs("skyrollup", level="WARNING") as logs:
            found = fetch.fetch_day(self.cfg, DAY, source=FakeSource(offline={"ws-03"}))
        self.assertEqual(sorted(found), ["ws-01", "ws-02"])
        self.assertEqual(logs.records[0].getMessage(), "station ws-03 offline")


if __name__ == "__main__":
    unittest.main()

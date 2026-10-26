import os
import unittest

from departures.feed import Stop, format_time, load_feed, parse_time

FEED = os.path.join(os.path.dirname(__file__), "data", "feed")


class LoadFeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = load_feed(FEED)

    def test_counts(self):
        self.assertEqual(len(self.feed.stops), 6)
        self.assertEqual(len(self.feed.routes), 2)
        self.assertEqual(len(self.feed.trips), 7)

    def test_version_is_the_folder_name(self):
        self.assertEqual(self.feed.version, "feed")

    def test_stop_fields(self):
        self.assertEqual(self.feed.stops["HRB"], Stop("HRB", "Harbor", 0, ""))

    def test_times_per_stop_are_sorted(self):
        times = [stop_time.departure for stop_time in self.feed.times_by_stop["CEN"]]
        self.assertEqual(times, sorted(times))
        self.assertEqual(len(times), 5)


class TimeTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_time("07:48:00"), 28080)

    def test_parse_past_midnight(self):
        self.assertEqual(parse_time("25:10:00"), 90600)

    def test_format(self):
        self.assertEqual(format_time(28080), "07:48")


if __name__ == "__main__":
    unittest.main()

import datetime as dt
import unittest

from helpers import FakeSource
from skyrollup import summarize

DAY = dt.date(2026, 4, 20)


class SummarizeTest(unittest.TestCase):
    def test_short_day_is_left_out(self):
        source = FakeSource(counts={"ws-02": 3})
        readings = {s: source.readings(s, DAY) for s in ("ws-01", "ws-02")}
        summary = summarize.summarize(DAY, readings, expected=2)
        self.assertEqual(summary["stations_reporting"], 1)
        self.assertEqual(summary["stations"][0]["station"], "ws-01")

    def test_network_figures(self):
        source = FakeSource()
        readings = {s: source.readings(s, DAY) for s in ("ws-01", "ws-02")}
        summary = summarize.summarize(DAY, readings, expected=2)
        mins = [s["temp_min_c"] for s in summary["stations"]]
        self.assertEqual(summary["network"]["temp_min_c"], min(mins))
        self.assertEqual(summary["stations"][0]["readings"], 144)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from datetime import datetime, timezone

from departures.feed import load_feed
from departures.query import departures_for, search

FEED = os.path.join(os.path.dirname(__file__), "data", "feed")


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


WEDNESDAY = "2026-10-07"
SATURDAY = "2026-10-10"
SUNDAY = "2026-10-11"


class DeparturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = load_feed(FEED)

    def test_soonest_first(self):
        found = departures_for(self.feed, "HRB", at(WEDNESDAY + "T07:30"), 8)
        self.assertEqual([item["departs"] for item in found], ["07:48", "08:18", "08:48"])
        self.assertEqual(
            found[0],
            {"trip_id": "SHL-WKD-001", "route": "SHL", "headsign": "Pier Road", "departs": "07:48"},
        )

    def test_skips_departures_already_gone(self):
        found = departures_for(self.feed, "MKT", at(WEDNESDAY + "T07:45"), 8)
        self.assertEqual([item["trip_id"] for item in found], ["SHL-WKD-002", "SHL-WKD-003"])

    def test_departure_on_the_minute_is_kept(self):
        found = departures_for(self.feed, "CEN", at(WEDNESDAY + "T08:10"), 1)
        self.assertEqual(found[0]["departs"], "08:10")

    def test_limit(self):
        found = departures_for(self.feed, "HRB", at(WEDNESDAY + "T07:30"), 2)
        self.assertEqual(len(found), 2)

    def test_bus_stop(self):
        found = departures_for(self.feed, "B1204", at(WEDNESDAY + "T08:00"), 8)
        self.assertEqual([item["route"] for item in found], ["12", "12"])

    def test_unknown_stop_has_no_departures(self):
        self.assertEqual(departures_for(self.feed, "NOPE", at(WEDNESDAY + "T07:30"), 8), [])

    def test_saturday_timetable(self):
        found = departures_for(self.feed, "HRB", at(SATURDAY + "T07:30"), 8)
        self.assertEqual([item["trip_id"] for item in found], ["SHL-SAT-001"])

    def test_sunday_timetable(self):
        found = departures_for(self.feed, "HRB", at(SUNDAY + "T07:30"), 8)
        self.assertEqual([item["trip_id"] for item in found], ["SHL-SUN-001"])

    def test_no_weekday_trips_on_sunday(self):
        self.assertEqual(departures_for(self.feed, "B1204", at(SUNDAY + "T07:30"), 8), [])


class SearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = load_feed(FEED)

    def test_part_of_the_name_ignoring_case(self):
        self.assertEqual([stop["stop_id"] for stop in search(self.feed, "market")], ["B1204", "MKT"])

    def test_stop_fields(self):
        self.assertEqual(
            search(self.feed, "pier"),
            [{"stop_id": "PRD", "name": "Pier Road", "location_type": 0, "parent_station": ""}],
        )

    def test_no_match(self):
        self.assertEqual(search(self.feed, "airport"), [])


if __name__ == "__main__":
    unittest.main()

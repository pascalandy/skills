import datetime as dt
import json
import os
import tempfile
import unittest

from helpers import FakeSource, make_config
from skyrollup import job, status

NIGHT = dt.datetime(2026, 3, 2, 2, 0, 5, tzinfo=dt.timezone.utc)


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_publishes_previous_utc_day(self):
        path = job.run(self.cfg, source=FakeSource(), now=NIGHT)
        self.assertEqual(path.name, "summary-2026-03-01.json")
        summary = json.loads(path.read_text())
        self.assertEqual(summary["day"], "2026-03-01")
        self.assertEqual(summary["stations_reporting"], 3)

    def test_latest_points_at_new_summary(self):
        job.run(self.cfg, source=FakeSource(), now=NIGHT)
        latest = self.cfg.summaries_dir / "summary-latest.json"
        self.assertEqual(os.readlink(latest), "summary-2026-03-01.json")

    def test_next_night_moves_latest(self):
        job.run(self.cfg, source=FakeSource(), now=NIGHT)
        job.run(self.cfg, source=FakeSource(), now=NIGHT + dt.timedelta(days=1))
        latest = self.cfg.summaries_dir / "summary-latest.json"
        self.assertEqual(os.readlink(latest), "summary-2026-03-02.json")
        self.assertTrue((self.cfg.summaries_dir / "summary-2026-03-01.json").exists())

    def test_status_records_run(self):
        job.run(self.cfg, source=FakeSource(), now=NIGHT)
        record = status.read_status(self.cfg.status_file)
        self.assertEqual(record["last_success"], "2026-03-02T02:00:05Z")
        self.assertEqual(record["result"], "ok")
        self.assertEqual(record["day"], "2026-03-01")
        self.assertEqual(record["summary"], "summary-2026-03-01.json")

    def test_offline_station_left_out(self):
        path = job.run(self.cfg, source=FakeSource(offline={"ws-02"}), now=NIGHT)
        summary = json.loads(path.read_text())
        self.assertEqual(summary["stations_reporting"], 2)
        self.assertEqual(summary["stations_expected"], 3)
        self.assertEqual([s["station"] for s in summary["stations"]], ["ws-01", "ws-03"])


if __name__ == "__main__":
    unittest.main()

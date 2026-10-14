import io
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime
from pathlib import Path

from crumb import export

ROOT = Path(__file__).resolve().parent.parent


class TargetDateTest(unittest.TestCase):
    def test_evening_run_sends_next_day(self):
        self.assertEqual(export.target_date(datetime(2026, 10, 9, 21, 0)), date(2026, 10, 10))

    def test_late_run_still_next_day(self):
        self.assertEqual(export.target_date(datetime(2026, 10, 9, 23, 59)), date(2026, 10, 10))

    def test_month_end(self):
        self.assertEqual(export.target_date(datetime(2026, 10, 31, 21, 0)), date(2026, 11, 1))

    def test_year_end(self):
        self.assertEqual(export.target_date(datetime(2026, 12, 31, 21, 0)), date(2027, 1, 1))


class DryRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "orders.db")
        con = sqlite3.connect(self.db)
        con.executescript((ROOT / "dev" / "orders.sql").read_text())
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def run_export(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = export.main(["--for", "tomorrow", "--dry-run", "--db", self.db, *args])
        return code, out.getvalue(), err.getvalue()

    def test_sheet_for_the_next_day(self):
        code, out, err = self.run_export("--now", "2026-10-09T21:00:00")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "Orders for Sat 2026-10-10")
        self.assertEqual(len(lines), 5)
        self.assertEqual(err, "target date 2026-10-10, 4 orders\n")

    def test_cancelled_orders_left_out(self):
        code, out, _ = self.run_export("--now", "2026-10-09T21:00:00")
        self.assertEqual(code, 0)
        self.assertNotIn("#1008", out)

    def test_sorted_by_pickup_time(self):
        _, out, _ = self.run_export("--now", "2026-10-11T20:30:00")
        times = [line[:5] for line in out.splitlines()[1:]]
        self.assertEqual(times, sorted(times))

    def test_bad_now(self):
        code, _, err = self.run_export("--now", "tonight")
        self.assertEqual(code, 2)
        self.assertIn("--now", err)

    def test_missing_database(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = export.main(["--for", "tomorrow", "--dry-run",
                                "--db", os.path.join(self.tmp.name, "none.db")])
        self.assertEqual(code, 1)
        self.assertIn("none.db", err.getvalue())


if __name__ == "__main__":
    unittest.main()

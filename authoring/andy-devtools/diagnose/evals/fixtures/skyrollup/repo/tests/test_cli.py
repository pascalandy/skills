import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from skyrollup import cli, status

LOG = """\
2026-03-01 02:00:00,512 INFO run started for 2026-02-28
2026-03-01 02:01:40,031 WARN station ws-07 offline
2026-03-01 02:04:02,118 INFO status written
2026-03-02 02:00:00,498 INFO run started for 2026-03-01
2026-03-02 02:02:11,804 ERROR collector answered 503
2026-03-02 02:04:05,377 INFO status written
"""


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.log_file = root / "skyrollup.log"
        self.status_file = root / "status.json"
        self.config = root / "config.toml"
        self.config.write_text(
            '[source]\nurl = "http://collector.test/v1/readings"\nstations = ["ws-01", "ws-02"]\n'
            f'[output]\nsummaries_dir = "{root}"\n'
            f'[state]\nstatus_file = "{self.status_file}"\nlog_file = "{self.log_file}"\n'
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["--config", str(self.config), *args])
        return code, out.getvalue().splitlines()

    def test_logs_default_shows_warnings_and_errors(self):
        self.log_file.write_text(LOG)
        code, lines = self.run_cli("logs")
        self.assertEqual(code, 0)
        self.assertEqual([line.split()[2] for line in lines], ["WARN", "ERROR"])

    def test_logs_since_and_level(self):
        self.log_file.write_text(LOG)
        _, lines = self.run_cli("logs", "--since", "2026-03-02", "--level", "info")
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(line.startswith("2026-03-02") for line in lines))

    def test_status_prints_record(self):
        status.write_status(self.status_file, {
            "last_success": "2026-03-02T02:04:05Z", "result": "ok", "day": "2026-03-01",
            "stations_reporting": 2, "stations_expected": 2, "summary": "summary-2026-03-01.json",
        })
        code, lines = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertIn("last_success: 2026-03-02T02:04:05Z", lines)
        self.assertIn("stations: 2 of 2", lines)


if __name__ == "__main__":
    unittest.main()

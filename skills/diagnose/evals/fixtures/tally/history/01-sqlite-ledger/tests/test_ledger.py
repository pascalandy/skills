import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tally.ledger import SCHEMA_VERSION, Ledger, LedgerError


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = str(Path(self.tmp) / "ledger.sqlite")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def user_version(self):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute("PRAGMA user_version").fetchone()[0]
        finally:
            conn.close()

    def test_new_ledger_gets_the_schema(self):
        with Ledger(self.path):
            pass
        self.assertEqual(self.user_version(), SCHEMA_VERSION)

    def test_unknown_account(self):
        with Ledger(self.path) as ledger:
            with self.assertRaises(LedgerError):
                ledger.balance("savings")

    def test_refuses_a_newer_ledger(self):
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA user_version = %d" % (SCHEMA_VERSION + 1))
        conn.close()
        with self.assertRaises(LedgerError):
            Ledger(self.path)

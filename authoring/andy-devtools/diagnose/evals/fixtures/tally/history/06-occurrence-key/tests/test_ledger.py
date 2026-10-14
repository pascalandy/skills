import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tally.ledger import SCHEMA_VERSION, Entry, Ledger, LedgerError


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

    def test_upgrades_a_schema_1_ledger(self):
        conn = sqlite3.connect(self.path)
        conn.executescript(
            """
            CREATE TABLE accounts (name TEXT PRIMARY KEY, bank TEXT NOT NULL,
                opening_cents INTEGER NOT NULL, opened TEXT NOT NULL);
            CREATE TABLE imports (id INTEGER PRIMARY KEY, file TEXT NOT NULL, account TEXT NOT NULL,
                imported_at TEXT NOT NULL, version TEXT NOT NULL, rows_read INTEGER NOT NULL,
                inserted INTEGER NOT NULL, deduped INTEGER NOT NULL);
            CREATE TABLE transactions (id INTEGER PRIMARY KEY, account TEXT NOT NULL, date TEXT NOT NULL,
                description TEXT NOT NULL, amount_cents INTEGER NOT NULL, import_id INTEGER NOT NULL);
            INSERT INTO accounts VALUES ('fernhill-card', 'Fernhill Bank', 0, '2026-03-02');
            INSERT INTO imports VALUES (1, 'fernhill-2026-03.csv', 'fernhill-card', '2026-04-01T09:30:00',
                '2.2.0', 1, 1, 0);
            INSERT INTO transactions VALUES (1, 'fernhill-card', '2026-03-02', 'Metro Fare', -325, 1);
            PRAGMA user_version = 1;
            """
        )
        conn.close()
        with Ledger(self.path) as ledger:
            self.assertEqual(ledger.keys("fernhill-card"), {(Entry("2026-03-02", "Metro Fare", -325), 1)})
        self.assertEqual(self.user_version(), 2)

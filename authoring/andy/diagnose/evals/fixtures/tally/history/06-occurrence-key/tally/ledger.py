"""The ledger: one SQLite file holding accounts, imports and transactions."""

import os
import sqlite3
from collections import namedtuple
from datetime import datetime
from decimal import Decimal, InvalidOperation

from tally import __version__

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE accounts (
    name TEXT PRIMARY KEY,
    bank TEXT NOT NULL,
    opening_cents INTEGER NOT NULL,
    opened TEXT NOT NULL
);
CREATE TABLE imports (
    id INTEGER PRIMARY KEY,
    file TEXT NOT NULL,
    account TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    version TEXT NOT NULL,
    rows_read INTEGER NOT NULL,
    inserted INTEGER NOT NULL,
    deduped INTEGER NOT NULL
);
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    account TEXT NOT NULL REFERENCES accounts(name),
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    import_id INTEGER NOT NULL REFERENCES imports(id),
    occurrence INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX transactions_account_date ON transactions(account, date);
"""

Entry = namedtuple("Entry", "date description amount")


class LedgerError(Exception):
    pass


def cents(text):
    """Parse a signed amount such as '-431.18' into integer cents."""
    try:
        return int(Decimal((text or "").strip()) * 100)
    except InvalidOperation:
        raise ValueError("not an amount: %r" % text) from None


def money(amount):
    """Format integer cents as a signed amount such as '-431.18'."""
    sign = "-" if amount < 0 else ""
    return "%s%d.%02d" % (sign, abs(amount) // 100, abs(amount) % 100)


class Ledger:
    def __init__(self, path, dry_run=False):
        # A dry run against a ledger that does not exist yet works on an empty one in memory.
        if dry_run and not os.path.exists(path):
            path = ":memory:"
        self.dry_run = dry_run
        self.conn = sqlite3.connect(path)
        self._prepare()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None and not self.dry_run:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

    def _prepare(self):
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            self.conn.close()
            raise LedgerError("ledger schema %d is newer than this tally (schema %d)" % (version, SCHEMA_VERSION))
        if version == 0:
            self.conn.executescript(SCHEMA)
        elif version == 1:
            self.conn.execute("ALTER TABLE transactions ADD COLUMN occurrence INTEGER NOT NULL DEFAULT 1")
        if version < SCHEMA_VERSION:
            self.conn.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)

    def keys(self, account):
        """Every ((date, description, amount), occurrence) already held for the account."""
        rows = self.conn.execute(
            "SELECT date, description, amount_cents, occurrence FROM transactions WHERE account = ?",
            (account,),
        )
        return {(Entry(*row[:3]), row[3]) for row in rows}

    def record(self, fmt, file, rows_read, opening, new):
        """Store one import and its new (entry, occurrence) pairs, creating the account on its first import."""
        now = datetime.now().isoformat(timespec="seconds")
        if not self.conn.execute("SELECT 1 FROM accounts WHERE name = ?", (fmt.ACCOUNT,)).fetchone():
            opened = new[0][0].date if new else now[:10]
            self.conn.execute("INSERT INTO accounts VALUES (?, ?, ?, ?)", (fmt.ACCOUNT, fmt.BANK, opening, opened))
        import_id = self.conn.execute(
            "INSERT INTO imports (file, account, imported_at, version, rows_read, inserted, deduped)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (file, fmt.ACCOUNT, now, __version__, rows_read, len(new), rows_read - len(new)),
        ).lastrowid
        self.conn.executemany(
            "INSERT INTO transactions (account, date, description, amount_cents, occurrence, import_id)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [(fmt.ACCOUNT, e.date, e.description, e.amount, n, import_id) for e, n in new],
        )

    def balance(self, account):
        """Opening balance plus every transaction, as (cents, count, last date)."""
        row = self.conn.execute("SELECT opening_cents FROM accounts WHERE name = ?", (account,)).fetchone()
        if row is None:
            raise LedgerError("no account named %r in the ledger" % account)
        total, count, through = self.conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0), COUNT(*), MAX(date) FROM transactions WHERE account = ?",
            (account,),
        ).fetchone()
        return row[0] + total, count, through

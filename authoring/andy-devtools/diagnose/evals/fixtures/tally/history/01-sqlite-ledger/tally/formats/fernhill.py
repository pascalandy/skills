"""Fernhill Bank card statement export. See docs/formats.md."""

from datetime import datetime

from tally.ledger import Entry, cents

BANK = "Fernhill Bank"
ACCOUNT = "fernhill-card"
HEADER = ["Posted", "Payee", "Amount"]


def _is_total(row):
    return row["Posted"].strip().upper() == "TOTAL"


def _iso(posted):
    return datetime.strptime(posted.strip(), "%m/%d/%Y").date().isoformat()


def entries(rows):
    return [
        Entry(_iso(row["Posted"]), row["Payee"].strip(), cents(row["Amount"]))
        for row in rows
        if not _is_total(row)
    ]


def opening_balance(rows):
    """Card statements carry no running balance; the account starts at zero."""
    return 0

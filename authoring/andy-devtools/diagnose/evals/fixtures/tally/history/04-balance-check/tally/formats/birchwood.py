"""Birchwood Credit Union account history export. See docs/formats.md."""

from tally.ledger import Entry, cents

BANK = "Birchwood Credit Union"
ACCOUNT = "birchwood-chequing"
HEADER = ["Date", "Description", "Amount", "Balance", "Page"]


def entries(rows):
    return [Entry(row["Date"].strip(), row["Description"].strip(), cents(row["Amount"])) for row in rows]


def opening_balance(rows):
    """The balance before the first line: its Balance minus its Amount."""
    if not rows:
        return 0
    return cents(rows[0]["Balance"]) - cents(rows[0]["Amount"])


def statement_total(rows):
    """Closing balance minus opening balance, or None for an empty export."""
    if not rows:
        return None
    return cents(rows[-1]["Balance"]) - opening_balance(rows)

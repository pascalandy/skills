"""Read a statement file and add the rows the ledger does not hold yet."""

import csv
import os

from tally import formats
from tally.ledger import Ledger


def read_statement(path):
    """Return the statement's format module and its rows as dicts."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fmt = formats.detect(reader.fieldnames or [])
        rows = list(reader)
    return fmt, rows


def import_statement(path, ledger_path):
    fmt, rows = read_statement(path)
    entries = fmt.entries(rows)
    with Ledger(ledger_path) as ledger:
        held = ledger.keys(fmt.ACCOUNT)
        new = []
        for entry in entries:
            if entry not in held:
                held.add(entry)
                new.append(entry)
        ledger.record(fmt, os.path.basename(path), len(entries), fmt.opening_balance(rows), new)
    return {
        "file": os.path.basename(path),
        "bank": fmt.BANK,
        "account": fmt.ACCOUNT,
        "rows_read": len(entries),
        "inserted": len(new),
        "deduped": len(entries) - len(new),
    }

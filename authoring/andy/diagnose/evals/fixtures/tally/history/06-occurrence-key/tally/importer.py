"""Read a statement file and add the rows the ledger does not hold yet."""

import csv
import os
from collections import Counter

from tally import formats
from tally.ledger import Ledger, money


def read_statement(path):
    """Return the statement's format module and its rows as dicts."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fmt = formats.detect(reader.fieldnames or [])
        rows = list(reader)
    return fmt, rows


def with_occurrence(entries):
    """Pair each entry with how many times it has appeared so far in this file."""
    counts = Counter()
    for entry in entries:
        counts[entry] += 1
        yield entry, counts[entry]


def import_statement(path, ledger_path, dry_run=False):
    fmt, rows = read_statement(path)
    entries = fmt.entries(rows)
    with Ledger(ledger_path, dry_run=dry_run) as ledger:
        held = ledger.keys(fmt.ACCOUNT)
        overlap = False
        new = []
        for key in with_occurrence(entries):
            if key in held:
                overlap = True
            else:
                new.append(key)
        ledger.record(fmt, os.path.basename(path), len(entries), fmt.opening_balance(rows), new)
    return {
        "file": os.path.basename(path),
        "bank": fmt.BANK,
        "account": fmt.ACCOUNT,
        "rows_read": len(entries),
        "inserted": len(new),
        "deduped": len(entries) - len(new),
        "balance_check": balance_check([entry for entry, _ in new], fmt.statement_total(rows), overlap),
    }


def balance_check(new, expected, overlap):
    """Compare the inserted rows with the statement's own total.

    n/a when the statement gives no total, or when some of its rows were already
    in the ledger, so the inserted rows are only part of it.
    """
    if expected is None or overlap:
        return "n/a"
    difference = sum(entry.amount for entry in new) - expected
    return "ok" if difference == 0 else "off by " + money(difference)

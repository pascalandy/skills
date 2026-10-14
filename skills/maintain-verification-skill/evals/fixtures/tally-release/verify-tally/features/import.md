# import

`python3 -m tally import <statement.csv> --ledger <ledger.sqlite>` detects the bank from the CSV header, skips rows the ledger already holds for that account, and inserts the rest. It answers one JSON line with `rows_read`, `inserted`, `deduped` and `balance_check`.

## Readings

`scripts/smoke.py` imports each file in `samples/` into a fresh ledger and reads `inserted` from the answer.

| Sample | Lines | `inserted`, last good |
|---|---|---|
| birchwood-sample | 20 | 20 |
| fernhill-sample | 14 | 13 |

fernhill-sample has one line that repeats the line before it exactly (Bakery Lane, 03/14/2026). The import keeps it once, so 13.

Normal values are in `runs/last-good.json`, recorded on main for 2.2.

## When a reading moves

`inserted` moving means the importer now keeps a different set of rows from the same file. Open the sample, count by hand which rows should land, and check the new value against that count before recording it.

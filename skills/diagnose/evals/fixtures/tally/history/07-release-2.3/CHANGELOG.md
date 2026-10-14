# Changelog

## 2.3 (2026-09-30)

- Fix #41: two identical purchases on the same day were merged into one.
- Ledger schema 2 adds an `occurrence` column to transactions. 2.3 upgrades a 2.2 ledger the first time it opens it; 2.2 refuses the upgraded ledger.

## 2.2 (2026-06-23)

- `import --dry-run` answers what an import would do without writing to the ledger.
- `import` answers `balance_check`: whether the inserted rows add up to the statement's own total (Birchwood: closing minus opening balance; Fernhill: the TOTAL line).

## 2.1 (2026-05-12)

- The ledger is one SQLite file, passed with `--ledger`. It replaces the per-account CSV ledgers of 2.0.
- Fernhill Bank card statements.
- `balance` answers an account's balance, its transaction count and its last date.
- Every command answers with one JSON line.
- A ledger written by a newer tally is refused instead of read.

## 2.0 (2025-11-09)

- Birchwood Credit Union statements into per-account CSV ledgers.

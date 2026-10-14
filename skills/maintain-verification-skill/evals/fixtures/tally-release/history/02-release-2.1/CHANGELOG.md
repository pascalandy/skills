# Changelog

## 2.1 (2026-05-12)

- The ledger is one SQLite file, passed with `--ledger`. It replaces the per-account CSV ledgers of 2.0.
- Fernhill Bank card statements.
- `balance` answers an account's balance, its transaction count and its last date.
- Every command answers with one JSON line.
- A ledger written by a newer tally is refused instead of read.

## 2.0 (2025-11-09)

- Birchwood Credit Union statements into per-account CSV ledgers.

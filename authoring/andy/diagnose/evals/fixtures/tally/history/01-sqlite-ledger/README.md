# tally

Imports bank statement CSV files into a SQLite ledger and answers account balances. Python 3 standard library only.

## Use

    python3 -m tally import ~/Downloads/birchwood-2026-03.csv --ledger ~/money/ledger.sqlite
    python3 -m tally balance --ledger ~/money/ledger.sqlite --account birchwood-chequing

Every command answers with one JSON line on stdout, `{"ok":true,...}` or `{"ok":false,"errors":[...]}`, and exits 0 on success, 1 when the command fails, 2 on a usage error. `python3 -m tally --help` lists the commands.

`import` detects the bank from the CSV header and answers:

| Field | Meaning |
|---|---|
| `file`, `bank`, `account` | the statement and the account its rows go to |
| `rows_read` | transaction lines in the file |
| `inserted` | rows added to the ledger |
| `deduped` | rows the ledger already held for that account |

A row is already held when the account has a transaction with the same date, description and amount, so importing a statement twice adds nothing.

`balance` answers the account's opening balance plus all its transactions. The opening balance comes from the first statement imported for the account.

## Banks

| Bank | Account | Header |
|---|---|---|
| Birchwood Credit Union | `birchwood-chequing` | `Date,Description,Amount,Balance,Page` |
| Fernhill Bank | `fernhill-card` | `Posted,Payee,Amount` |

Notes on each export: [docs/formats.md](docs/formats.md).

## Tests

    python3 -m unittest discover -s tests

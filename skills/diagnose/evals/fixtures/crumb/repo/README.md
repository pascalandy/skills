# crumb

Order tools for Crumb & Co. The main piece is `crumb.export`, the evening job that mails the kitchen the preorder sheet for the next day.

## The preorder sheet

The shop closes preorders for a pickup day at 18:00 two days before. Every evening at 21:00 the export reads tomorrow's orders from the orders database and mails them to the kitchen, one line per order, sorted by pickup time:

    python3 -m crumb.export --for tomorrow

`--dry-run` prints the sheet instead of mailing it. Either way the job logs the target date and the order count to stderr.

The job runs on the ops host as user `crumb`, from a checkout of a release tag in `/opt/crumb`.

## Databases

The orders database is SQLite, kept current from the shop by crumb-sync (separate repo), one copy per environment. `--db` takes a path, or `prod` or `staging`, which resolve to `$CRUMB_DATA/<name>/orders.db` (default `CRUMB_DATA=/srv/crumb`). Developer machines can mount staging; prod is only mounted on the ops host.

For local runs, build the sample database:

    python3 -c "import sqlite3; sqlite3.connect('dev/orders.db').executescript(open('dev/orders.sql').read())"
    python3 -m crumb.export --for tomorrow --dry-run --db dev/orders.db

## Tests

    python3 -m unittest discover -s tests

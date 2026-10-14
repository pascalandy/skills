# Changelog

## 1.6 (2026-08-12)

- `--now` sets the current time, so tests can pin the clock.
- Tests for the export: evening run, month and year ends, cancelled orders.

## 1.5 (2026-07-21)

- Log the target date and the number of orders to stderr.
- Clear error when the database can't be opened.

## 1.4 (2026-06-30)

- Show order notes (allergies, slicing, gift boxes) on the sheet.

## 1.3 (2026-05-27)

- `--db prod` and `--db staging` name the shared databases under `$CRUMB_DATA`.
- `dev/orders.sql`: sample orders for local runs.

## 1.2 (2026-04-22)

- `--dry-run` prints the sheet instead of mailing it.

## 1.1 (2026-03-11)

- Sort the sheet by pickup time.
- First tests.

## 1.0 (2026-02-17)

- Evening export: mails the kitchen tomorrow's preorders.

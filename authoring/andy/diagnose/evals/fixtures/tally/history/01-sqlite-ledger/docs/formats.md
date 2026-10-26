# Statement formats

What each bank's CSV export looks like, quoted from the bank where it documents the format.

## Birchwood Credit Union

Account in tally: `birchwood-chequing`. Download: Online Banking, Accounts, History, Export (CSV).

Header: `Date,Description,Amount,Balance,Page`

From Birchwood's help page "Exporting your account history", retrieved 2026-03-30:

> Account history exports are produced in pages of 50 lines. Each line shows the posting date (YYYY-MM-DD), the transaction description, the amount (debits are negative), the account balance after the transaction, and the page number. For continuity between pages, the first line of each page after page 1 repeats the last line of the preceding page, shown with the page number of the new page. A repeated line is not an additional transaction.

The opening balance of an export is the first line's Balance minus its Amount. The closing balance is the last line's Balance.

## Fernhill Bank

Account in tally: `fernhill-card`. Download: Card, Statements, Download, CSV.

Header: `Posted,Payee,Amount`

From Fernhill's statement download notes, retrieved 2026-04-02:

> Statement files list posted transactions oldest first. Posted is the posting date (MM/DD/YYYY). Purchases and fees are negative; payments and credits are positive. The last line of the file is the statement total: TOTAL in the Posted column, an empty Payee, and the sum of all amounts for the statement period.

There is no balance column. tally starts the account at zero.

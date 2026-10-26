# Birchwood balance wrong since 2.3

From: Maren Holt
Date: 2026-10-14

Hi,

I upgraded tally from 2.2 to 2.3 on 2026-10-03 and imported both September statements the next morning, 2026-10-04, the way I always do:

    python3 -m tally import ~/Downloads/birchwood-2026-09.csv --ledger ~/money/ledger.sqlite
    python3 -m tally import ~/Downloads/fernhill-2026-09.csv --ledger ~/money/ledger.sqlite

I didn't keep what those printed. I sat down to reconcile last night and Birchwood doesn't match:

    $ python3 -m tally balance --ledger ~/money/ledger.sqlite --account birchwood-chequing
    {"ok":true,"account":"birchwood-chequing","balance":"2068.89","transactions":343,"through":"2026-09-30"}

Birchwood's September statement closes at $3,312.06, so tally is $1,243.17 below the bank.

Fernhill is fine. The card balance in tally moved by -1,563.54 over September, which is the TOTAL line on the Fernhill statement.

August was imported with 2.2 on 2026-09-04 and reconciled to the cent for both accounts, so the ledger was right going into September.

In case it matters: Birchwood moved my account to their new online banking on 2026-08-29. Maybe their export is different now? I haven't compared.

Attached:

- `statements/birchwood-2026-09.csv` and `statements/fernhill-2026-09.csv`, exactly as I downloaded them on 2026-10-02
- `ledger.sqlite`, a copy of my ledger as of this morning

Maren

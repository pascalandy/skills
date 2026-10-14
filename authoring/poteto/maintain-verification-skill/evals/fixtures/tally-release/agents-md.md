# tally

Personal finance CLI: imports bank statement CSV files into a SQLite ledger. Python 3 standard library only.

- Tests: `python3 -m unittest discover -s tests`
- Verify loop: `skills/verify-tally`. Read its `SKILL.md` and run it before merging any change to `tally/`. Say in the PR which readings moved and why.
- Bank export formats: `docs/formats.md`.
- Every command answers with one JSON line on stdout. Keep it that way.

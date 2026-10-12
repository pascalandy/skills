# main-triage

You have the final say on findings and when reviews end.

1. **Decide.** Accept or reject each finding, with a one-line reason. When BLAST reports, add the findings of your premortem from `main-launch`. Done when every finding has a decision and a reason
2. **Relay.** Send each accepted finding with `t3_thread_send` to its layer's owner: DOC<n> for the docs PR, COD<n> for the rest. Done when each owner reports the findings pushed to their layers, or why they could not be
3. **Next.** Read the REV's `max-passes` in `config.toml`. If fixes need a fresh look and passes remain, rerun it on the new heads with `t3_thread_send`. Carry each prior finding and your decision. Otherwise end the review and record why for the closing report. When the last allowed pass yields a code fix, rerun once, limited to that fix. That pass is the last: list any fix it yields under "What you couldn't confirm" in the closing report. Settle the REV, and DOC<n> too after the pristine review. Keep a thread open for `main-closing` only if its role enables `retro`. Done when the next pass has started, or the review ended and each thread is settled or kept for retros

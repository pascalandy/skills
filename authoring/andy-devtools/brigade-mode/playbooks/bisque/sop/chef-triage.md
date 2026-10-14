# chef-triage

You have the final say on findings and when reviews end.

1. **Decide.** Accept or reject each finding, with a one-line reason. In step 2, wait for both manic-1 and manic-2, then decide on both sets together, with the findings of your premortem from `chef-launch`. A watch wake brings findings too: a failed check or a conflict is an accepted finding for the Cook, and an outside review is decided like a barrage finding. Done when every finding has a decision and a reason
2. **Relay.** Send each accepted code finding to Cook <b>.<c> with `t3_thread_send`. Give the accepted docs findings to a fresh DocWriter, section Fix, with `chef-launch`. Done when each owner reports the findings pushed to their layers, or why they could not be
3. **Next.** Read the barrage's `max-passes` in `config.toml`. If fixes need a fresh look and passes remain, delegate a fresh pass of that barrage on the new heads with `chef-launch`, carrying each prior finding and your decision. Otherwise end the review and record why for the closing report. When the last allowed pass yields a code fix, delegate one more pass, limited to that fix. That pass is the last: list any fix it yields under "What you couldn't confirm" in the closing report. Done when the next pass is delegated, or the review ended with its reason recorded

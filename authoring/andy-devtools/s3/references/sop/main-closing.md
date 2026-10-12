# main-closing

MAIN runs this SOP once DOC<n> reports.

1. **Report.** Send Pascal:
	- PR links, and links to the issues filed
	- The out-of-scope gaps not filed
	- Every change made outside what was agreed, and why
	- The review passes run, the findings rejected and why, and why the reviews ended
	- Each step skipped or replaced, and why
	- What you couldn't confirm, and where you looked
	- Confidence to merge: XX%, and why it is below 100% when it is

	Done when the report includes every item above
2. **Merge.** Ask Pascal whether to merge, and end your reply on that question. When Pascal says merge, relay the go to each COD of this round, which merges as `cod-implement` says. Done when either:
	- Pascal said merge, each PR is merged, and its deploy succeeded or its COD reported the failure
	- Pascal said not to merge. A "not yet" keeps this step open
3. **Retros.** Only MAIN and each COD of this round run retros. Once the PRs are merged, ask each COD to run its retros, and run yours: 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Each of you files at most 2 issues per retro, the fixes with the most bang for the buck. Done when each COD reported its issue links, or that no finding passed, and yours are filed
4. **Settle.** Settle each thread of this round with `t3_thread_organize` action `settle`, once `t3_thread_wait` confirms its turn ended. T3 refuses a thread with active work, with "has active or blocked work". Done when every thread of this round is settled
5. **End the round.** End with "⛳ Implemented. [high-level summary of what you completed]". Pascal starts the next round in this MAIN, or settles it

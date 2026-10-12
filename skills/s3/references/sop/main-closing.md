# main-closing

MAIN runs this SOP once the reviews end, or once DOC<n> reports in fast track.

1. **Report.** Send Pascal:
	- PR links, and links to the issues filed
	- The out-of-scope gaps not filed
	- Every change made outside what was agreed, and why
	- The review passes run, the findings rejected and why, and why the reviews ended
	- Each step skipped or replaced, and why
	- What you couldn't confirm, and where you looked
	- Confidence to merge: XX%, and why it is below 100% when it is

	Done when the report includes every item above
2. **Merge.** When your confidence to merge is 95% or more, merge without asking: Pascal's `$s3` authorizes it. Otherwise ask Pascal your questions, align, and merge when Pascal says merge. To merge, land each stack of this round yourself, from its COD's worktree, with 🧰 poteto-mode ; shipping, through the project's merge command and any deploy it runs. The merge command can exit 0 after a failed deploy, so read its output. Then remove the round's worktrees. Done when either:
	- Pascal said merge, each PR is merged, and its deploy succeeded or you reported the failure
	- Pascal said not to merge. A "not yet" keeps this step open
3. **Retros.** Only MAIN and each COD of this round run retros. Once the PRs are merged, ask each COD to run its retros, and run yours: 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Each of you files at most 2 issues per retro, the fixes with the most bang for the buck. Done when each COD reported its issue links, or that no finding passed, and yours are filed
4. **Settle.** Settle each COD of this round, and DOC<n> if it is still open. Done when every thread of this round is settled
5. **End the round.** End with "⛳ Implemented. [high-level summary of what you completed]". Pascal starts the next round in this MAIN, or settles it

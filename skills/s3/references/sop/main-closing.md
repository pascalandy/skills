# main-closing

MAIN runs this SOP once the step before it in CU1 ends.

1. **Report.** Send Pascal:
	- PR links, and links to the issues filed
	- The out-of-scope gaps not filed
	- Every change made outside what was agreed, and why
	- The review passes run, the findings rejected and why, and why the reviews ended
	- Each step skipped or replaced, and why
	- What you couldn't confirm, and where you looked
	- Confidence to merge: XX%, and why it is below 100% when it is

	Done when the report includes every item above
2. **Merge.** When your confidence to merge reaches `merge-confidence` in `config.toml`, merge without asking: Pascal's `$s3` authorizes it. Otherwise ask Pascal your questions, align, and merge when Pascal says merge. Merge each stack of this round yourself, from its COD's worktree: a single PR through the project's merge command, a stack of PRs through the Land section of 🧰 gh-stack, then any deploy the project's merge command runs, such as `just merge` on the top branch in skills. A merge command can exit 0 after a failed deploy, so read its output. Done when either:
	- each PR is merged, and its deploy succeeded or you reported the failure
	- Pascal said not to merge. A "not yet" keeps this step open
3. **Retros.** Once step 2 is done, each thread of this round whose role sets `retro` in `config.toml` runs 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Ask each of them, and run yours when `[main]` sets `retro`. Each of you files at most `retro-max-issues` issues per retro, the fixes with the most bang for the buck. Done when each of them reported its issue links, or that no finding passed, and yours are filed
4. **Settle and clean up.** Settle each thread of this round still open. Then remove each worktree of this round that is clean and whose branch is merged, and name any you kept and why. Done when every thread of this round is settled and each worktree is removed or named
5. **End the round.** End with "⛳ Implemented. [high-level summary of what you completed]", or with "⏸️ Not merged. [summary and what is left]" when Pascal said not to merge. Pascal starts the next round in this MAIN, or settles it

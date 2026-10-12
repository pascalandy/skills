# main-closing

1. **Report.** Send Pascal:
	- PR links, and links to the issues filed
	- The out-of-scope gaps not filed
	- Every change made outside what was agreed, and why
	- The review passes run, the findings rejected and why, and why the reviews ended
	- Each step skipped or replaced, and why
	- What you couldn't confirm, and where you looked
	- Confidence to merge: XX%, and why it is below 100% when it is

	Done when the report includes every item above
2. **Merge.** If the round opened no PR, record that no merge is needed. Otherwise compare your confidence with `merge-confidence` in `config.toml`. At or above it, merge without asking. Pascal's `$s3` authorizes it. Below it, ask Pascal your questions, align, and merge when Pascal says merge.

	Merge from the COD's worktree. For a single PR, use the project's merge command. For a stack, follow the Land section of 🧰 gh-stack, then run the project's deploy. In skills, use `just merge` on the top branch for that deploy. Read the output because a merge command can exit 0 after a failed deploy. A "not yet" keeps this step open. Done when:
	- the round needed no merge
	- each PR is merged, and its deploy succeeded or you reported the failure
	- Pascal said not to merge
3. **Retros.** After step 2, ask each thread of this round whose role enables `retro` in `config.toml` to run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Include `retro-max-issues` as its issue limit per retro. Follow the same routes and limit yourself if `[main]` enables `retro`. Choose the fixes with the most value. Done when every enabled retro has issue links or a recorded no-findings result
4. **Settle and clean up.** Settle each thread of this round still open. Remove each worktree of this round that is clean and whose branch is merged. Name any you kept and why. Done when every thread of this round is settled and each worktree is removed or named with its reason
5. **End the round.** Send "⛳ Implemented. [high-level summary of what you completed]", or "⏸️ Not merged. [summary and what is left]" when Pascal said not to merge. Done when Pascal has the round's outcome

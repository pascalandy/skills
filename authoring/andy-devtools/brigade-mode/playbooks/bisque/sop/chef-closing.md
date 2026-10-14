# chef-closing

1. **Report.** Send the Head Chef:
	- PR links, and links to the issues filed
	- The out-of-scope gaps not filed
	- Every change made outside what was agreed, and why
	- The review passes run, the findings rejected and why, and why the reviews ended
	- Each step skipped or replaced, and why
	- What you couldn't confirm, and where you looked
	- Confidence to merge: XX%, and why it is below 100% when it is

	Done when the report includes every item above
2. **Green light.** If the batch opened no PR, record that no merge is needed and go to step 4. Otherwise send the Head Chef "🚦 Batch <b> ready" with the PR links and your confidence to merge, then wait for its answer. A hold keeps this step open. Done when the Head Chef replied 🟢, or said not to merge
3. **Merge.** After 🟢, merge from the Cook's worktree. For a single PR, use the project's merge command. For a stack, follow the Land section of 🧰 gh-stack, then run the project's deploy. In skills, use `just merge` on the top branch for that deploy. Read the output because a merge command can exit 0 after a failed deploy. The merge ends your watch. Send the Head Chef "Batch <b> merged" with the deploy result. After "don't merge", call `unwatch_pull_request` on each PR instead. Done when:
	- each PR is merged, and its deploy succeeded or you reported the failure
	- the Head Chef said not to merge, and no watch remains
4. **Retros.** Ask each thread of this batch whose role enables `retro` in `config.toml` to run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Include `retro-max-issues` as its issue limit per retro. Follow the same routes and limit yourself if `[chef]` enables `retro`. Choose the fixes with the most value. Done when every enabled retro has issue links or a recorded no-findings result
5. **Clean up.** Confirm with 🧰 t3-runtime that each Cook of this batch has settled. Remove each worktree of this batch that is clean and whose branch is merged. Name any you kept and why. Done when each Cook is settled and each worktree is removed or named with its reason
6. **End the batch.** Send the Head Chef "⛳ Batch <b> merged. [high-level summary]", or "⏸️ Batch <b> not merged. [summary and what is left]". Then settle yourself. Done when the Head Chef has the batch's outcome and your settle call returned `settlesWhenTurnEnds: true`

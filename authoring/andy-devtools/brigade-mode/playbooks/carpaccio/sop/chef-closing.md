# chef-closing

Apply [Statuses, Messages and Decisions](../carpaccio.md#statuses) at phase entry and turn end. Keep the received Cook phases, frozen heads and stack diff for each approval.

## Validate and merge

1. On `🍽️ Stack ready`, read the Cook's Report and Detail in its thread, including rejected findings. Reopen a rejection with your reason and return the worktree through Fix. Check conflicts between Cooks. Wait for every counted Cook to serve and for PR checks on all frozen heads to pass. Record an unconfirmed check on another machine under [Decisions](../carpaccio.md#decisions). Done when the reports and checks support a merge judgment
2. Apply the merge rule in [Decisions](../carpaccio.md#decisions). If it allows merging, record authorization and frozen heads in your Detail, show 🔀 and send `🔀 Batch merging` with the Report to the Head Chef. Otherwise send `🍽️ Batch ready`, show 🍽️ and wait for Pascal's decision through the Head Chef. On `🔀 Merge`, record Pascal's approval and the frozen heads in a new Detail before step 3. `⏳ Rework` returns affected Cooks to Fix; `🍽️ Hold` keeps the batch ready; `⏹️ Drop` cuts the batch, sends `⏹️ Stop` to its Cooks and goes to Closing. Done when the auto-merge notice is sent, Pascal's decision is received for current heads, or the cut is recorded
3. Merge one stack at a time:
   - Show 🔀. Check that the frozen Cook worktree is clean and pushed, and that GitHub holds the approved heads
   - After a restack, compare the stack's own diff. Then apply the approval rule in [Asking Pascal](../carpaccio.md#asking-pascal)
   - Use the project's merge procedure from the frozen Cook worktree. For a single PR, use its merge command. For a stack, follow 🧰 gh-stack Land through its Done, even when the project's procedure covers only a single PR. Then run the project's deploy. In skills, use `just merge` on the merged top branch for that deploy
   - Run the merge command bare, with no pipe or redirect, so its permission rule matches. Read the whole output, since exit 0 can hide a failed deploy
   - Check GitHub before retrying an uncertain merge
   - If another stack remains, wait until GitHub confirms the merge and its deploy succeeded or was not required. Then ask the next Cook to restack on `main` and return fresh `🍽️ Stack ready`

   Done when GitHub shows `MERGED` for every PR of the approved stack and its deploy succeeded or was not required
4. On failure, record landed PRs, send the Cook the cause and return its worktree for Fix. Tell the Head Chef if a previously ready batch lost readiness, so it withdraws its merge item. Report the partial outcome. Resume at step 1 after fresh `🍽️ Stack ready`. Done when each stack merged in order or the Head Chef has an unresolved blocker
5. After the last stack, tell each Cook `merged` and send the Head Chef `Batch merged` with deploy results. For `Release: yes`, follow the remaining repository release procedure from `main`; check its outcome before retrying an uncertain release and report a failure before closing. Done when all merge and release outcomes are recorded

If Pascal says Stop, follow [chef-run Stop](chef-run.md#stop). A frozen watch wake that brings a finding, such as a failed check, a review or comment, or a conflict, invalidates readiness until you return the worktree, the Cook triages it and sends fresh `🍽️ Stack ready`. Tell the Head Chef to withdraw a pending merge item. A wake reporting only passing checks preserves readiness.

## Closing

For a batch without PRs, begin here.

1. Show 🧹. For an Epic, read every child's state. Open children outside the batch are reported and may remain open. An open child inside the batch blocks ⛳ until completed or cut by Pascal. Close the Epic with proof when all its children are closed. Done when no Epic applies, or all in-batch children are done or cut and the remaining open children are reported
2. Ask every Cook to close, whether retros are enabled or not. Each Cook runs enabled retros, unwatches, reports and settles. Do the Chef's retros if `[chef].retro`. Done when every Cook has a final phase and each enabled retro has issue links or a no-findings result
3. Confirm each Cook is settled with 🧰 t3-runtime. Remove worktrees that are clean and merged, retaining the rest with a reason. Done when every Cook is settled and every worktree is removed or accounted for
4. To compute ⛳ or ⏹️, apply the Chef rules in [Statuses](../carpaccio.md#statuses). Post your final Detail in your thread, then send `⛳ Batch delivered` or `⏹️ Batch stopped` with the Report and set the title to the final status. As the last step before settling, delete your Watchdog's schedule, cancel its task and remove its work folder and your own. Then settle. Done when the Head Chef received the outcome, no Watchdog schedule remains and your settle returns `settlesWhenTurnEnds: true`

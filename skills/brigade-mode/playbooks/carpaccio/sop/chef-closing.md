# chef-closing

Apply [Statuses, Messages and triggers](../carpaccio.md#statuses) at phase entry and turn end. Keep the received Cook phases, frozen heads and stack diff for each approval.

## Validate and merge

1. Validate each `🍽️ Stack ready` report:
   - Read the Cook's shared Report, including rejected findings
   - If you reopen a rejection, give your reason and return its worktree through Fix
   - Check conflicts between Cooks
   - Before sending `🍽️ Batch ready`, wait for every counted Cook to serve and for checks on all frozen heads to finish

   Done when the reports and checks support your merge confidence

2. Choose the merge path:
   - If `Validate: no`, confidence reaches `[chef].merge-confidence` and no open `Act on` finding caps it below that threshold, record merge authorization, show 🔀 and send `🔀 Batch merging` with the shared Report to the Head Chef. Then proceed
   - Otherwise send `🍽️ Batch ready` with the report, show 🍽️ and wait for Pascal's decision relayed by the Head Chef
   - On `⏳ Rework`, return affected Cooks to Fix
   - On `🍽️ Hold`, keep the batch ready
   - On `⏹️ Drop`, cut the batch, send `⏹️ Stop` to its Cooks and go to Closing

   Done when the notice is sent, `🔀 Merge` is received for current heads, or the cut is recorded

3. Merge one stack at a time:
   - Show 🔀 while merging
   - Before merging each stack, check that its frozen Cook worktree has a clean, pushed checkout and that GitHub holds the approved heads
   - After a restack, compare the stack's own diff. If only its base changed and checks pass, keep approval and the Cook 🍽️. If its own diff changed, require a new review under `Validate: yes`
   - Use the project's merge procedure from the frozen Cook worktree: for a single PR its merge command; for a stack 🧰 gh-stack Land, then the project's deploy. In skills, use `just merge` on the merged top branch for that deploy
   - Run the merge command bare, with no pipe or redirect, so its permission rule matches
   - Read the whole output, since an exit 0 may hide a failed deploy
   - If a merge result is uncertain, check GitHub before retrying it
   - If GitHub confirms the stack merged, its deploy succeeded or was not required, and another stack remains, ask the next Cook to restack on `main` and return fresh `🍽️ Stack ready`

   Done when GitHub confirms the validated stack merged and its deploy succeeded or was not required

4. On failure:
   - Record landed PRs
   - Send the Cook the cause and return its worktree for Fix
   - If a previously ready batch lost readiness, tell the Head Chef so it withdraws its review item
   - Report the partial outcome
   - After fresh `🍽️ Stack ready`, resume at step 1

   Done when each stack merged in order or the Head Chef has an unresolved blocker

5. After the last stack:
   - Tell each Cook `merged`
   - Send the Head Chef `Batch merged` with deploy results
   - For `Release: yes`, follow the remaining repository release procedure from `main`
   - If `Release: yes` and its outcome is uncertain, check the outcome before retrying
   - If the release fails, report the failure before closing

   Done when all merge and release outcomes are recorded

If Pascal says Stop, finish a merge already running, discard unused approval and follow `chef-run` Stop. A frozen watch wake that brings a finding, such as a failed check, a review or comment, or a conflict, invalidates readiness until you return the worktree, the Cook triages it and sends fresh `🍽️ Stack ready`. Tell the Head Chef to withdraw a pending review item. A wake reporting only passing checks preserves readiness.

## Closing

For a batch without PRs, begin here.

1. Show 🧹. For an Epic, read every child's state. Open children outside the batch are reported and may remain open. An open child inside the batch blocks ⛳ until completed or cut by Pascal. Close the Epic with proof when all its children are closed. Done when no Epic applies, or all in-batch children are done or cut and the remaining open children are reported
2. Ask every Cook to close, whether retros are enabled or not. Each Cook runs enabled retros, unwatches, reports and settles. Do the Chef's retros if `[chef].retro`. Done when every Cook has a final phase and each enabled retro has issue links or a no-findings result
3. Confirm each Cook is settled with 🧰 t3-runtime. Remove worktrees that are clean and merged, retaining the rest with a reason. Done when every Cook is settled and every worktree is removed or accounted for
4. Compute ⛳ only when all in-scope stacks merged or a no-PR batch did its own work, the release is done or cut, all in-batch Epic children are done or cut, and every Cook is final and settled. Otherwise after Stop or a whole-batch cut, compute ⏹️. Send `⛳ Batch delivered` or `⏹️ Batch stopped` with the shared Report and set the title to the final status. As the last step before settling, delete your Watchdog's schedule, cancel its task and remove its work folder and your own. Then settle. Done when the Head Chef received the outcome, no Watchdog schedule remains and your settle returns `settlesWhenTurnEnds: true`

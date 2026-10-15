# chef-closing

## Validate and merge

1. On `🚦 Stack ready`, read the Cook's shared Report, including rejected findings; reopen any rejection with your reason and return its worktree through Fix. Check conflicts between Cooks. Done when the report and cross-Cook conflicts support your merge confidence
2. If `Validate: no` and confidence reaches `[chef].merge-confidence`, send `🔀 Batch <b> merging` with the shared Report to the Head Chef and proceed. Otherwise send `🚦 Batch <b> ready` with the report, then wait for Pascal's decision relayed by the Head Chef. A hold keeps this step open. Done when the notice is sent or 🟢 Merge is received
3. Merge one stack at a time from the frozen Cook worktree, after checking its checkout is clean and pushed and GitHub holds the heads in the Cook's 🚦. A changed head invalidates validation; return to step 1. Use the project's merge procedure: for a single PR its merge command; for a stack 🧰 gh-stack Land, then the project's deploy. In skills, use `just merge` on the merged top branch for that deploy. Run the merge command bare, with no pipe or redirect, so its permission rule matches. Read the whole output, since an exit 0 may hide a failed deploy. Done when GitHub confirms the validated stack merged and the deploy result is recorded
4. On failure, record landed PRs, send the Cook the cause and return its worktree for Fix. Report the partial outcome to the Head Chef. Resume at step 1 after a fresh 🚦. Done when each stack merged in order or the Head Chef has an unresolved blocker
5. After the last stack, tell each Cook `merged` and send the Head Chef `Batch <b> merged` with deploy results. For `Release: yes`, follow the remaining repository release procedure from `main`; report a failure before closing. Done when all merge and release outcomes are recorded

If Pascal declines merging, ask Cooks to unwatch and proceed to Closing with a not-merged outcome. A frozen watch wake that brings a finding, such as a failed check, a review or comment, or a conflict, invalidates readiness until you have returned the worktree, the Cook has triaged it and sent a fresh 🚦. A wake reporting only passing checks preserves readiness.

## Closing

For a batch without PRs, begin here.

1. Ask each Cook whose role enables `retro` to run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global; each retro files the issues with the most value, up to `retro-max-issues`. Do the same if `[chef].retro`. Done when every enabled retro has issue links or a no-findings result
2. Confirm each Cook is settled with 🧰 t3-runtime. Remove worktrees that are clean and merged, retaining the rest with a reason. Done when every Cook is settled and every worktree is removed or accounted for
3. Send the Head Chef `⛳ Batch <b> merged`, `⛳ Batch <b> done without a PR` or `⏸️ Batch <b> not merged` with the shared Report, then settle yourself. Done when the Head Chef has the outcome and your settle returns `settlesWhenTurnEnds: true`

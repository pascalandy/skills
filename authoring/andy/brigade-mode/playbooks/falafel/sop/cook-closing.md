# cook-closing

Apply [Statuses, Messages and Decisions](../falafel.md#statuses) at phase entry and turn end. Keep the frozen heads and stack diff for each approval.

## Merge gate and merge

1. Freeze the stack: make no commit, checkout, restack or push until the merge, a restack step 3 needs, or Fix. When the project's merge procedure assigns signoff to the merge step, run its signoff command without merging on each frozen head before applying the merge rule. Read each head's required statuses on GitHub, including owner-posted statuses. A failing layer or an absent required status sends the stack to [Fix](cook-run.md#fix). When a status is required, `no checks reported` proves no pass. Record an unconfirmed check on another machine under [Decisions](../falafel.md#decisions). Done when the checks support a merge judgment
2. First apply the approval rule in [Asking Pascal](../falafel.md#asking-pascal). If an unused prior approval still binds to this stack and every current head passes its required checks, record the comparison evidence in a new Detail, show 🔀 and continue at step 3. Otherwise apply the merge rule in [Decisions](../falafel.md#decisions). If it allows merging, record each gate's result and the frozen heads in your Detail, show 🔀 and send `🔀 Batch merging` with the Report to the Head Chef. Otherwise send `🍽️ Batch ready`, show 🍽️ and wait for Pascal's decision through the Head Chef. If the Head Chef sends answers instead, apply the merge rule again with them. On `🔀 Merge`, record Pascal's approval and the frozen heads in a new Detail before step 3. `⏳ Rework` sends you to Fix; `🍽️ Hold` keeps the batch ready; `⏹️ Drop` cuts the batch and goes to Closing. Done when the auto-merge notice is sent, Pascal's decision is received for current heads, a preserved approval and its comparison evidence are recorded, or the cut is recorded
3. Merge the stack:
   - Show 🔀. Check that your worktree is clean and pushed, and that GitHub holds the approved heads
   - After a restack, run any signoff the merge step assigns you on each new head, as step 1 says, then compare the stack's own diff. Apply the approval rule in [Asking Pascal](../falafel.md#asking-pascal)
   - Use the project's merge procedure from your worktree. For a single PR, even in a one-layer stack, use its merge command. If that command refuses a PR in a GitHub stack, follow 🧰 gh-stack Land. For a stack of two or more PRs, follow 🧰 gh-stack Land through its Done, even when the project's procedure covers only a single PR. When the project's merge command already deployed, use that result. Otherwise run its required deploy once, from the checkout its procedure specifies
   - Run each merge or deploy command bare, with no pipe or redirect, so its permission rule matches. Read each command's whole output, since exit 0 can hide a failed deploy
   - Classify the deploy from the output of the command that ran it. The gates below and step 4 use this one result:
     - `complete`: it reached every machine
     - `not_required`: the project requires no deploy for this merge
     - `external_gap`: it missed only machines that no thread of the run uses, counting slots not launched yet, for a cause the run cannot repair, such as their credentials, and the repository's procedure does not require every machine for this stack, such as before it removes an old reader. Record each missed machine, its cause and its fix command
     - `blocked`: any other miss
   - Check GitHub before retrying an uncertain merge

   Done when GitHub shows `MERGED` for every PR of the approved stack and its deploy is `complete`, `not_required` or `external_gap`
4. On a failed merge or a `blocked` deploy, record landed PRs and fix the cause through [Fix](cook-run.md#fix). An `external_gap` is not a failure: continue. Tell the Head Chef if a previously ready batch lost readiness, so it withdraws its merge item. Report the partial outcome. Resume at step 1 after Proof. When a merge fails twice for the same cause, show ⏸️ and send its history to the Head Chef as a fault. Done when the stack merged or the Head Chef has an unresolved blocker
5. After the merge, send the Head Chef `Batch merged` with deploy results, naming each `external_gap` machine with its cause and fix command. For `Release: yes`, follow the remaining repository release procedure from `main`; check its outcome before retrying an uncertain release and report a failure before closing. Done when all merge and release outcomes are recorded

If Pascal says Stop, follow [cook-run Stop](cook-run.md#stop). While frozen, a watch wake that brings a finding, such as a failed check, a review or comment, or a conflict, withdraws readiness: tell the Head Chef to withdraw a pending merge item, then enter Fix. A wake reporting only passing checks preserves readiness.

## Closing

For a batch without PRs, begin here.

1. Show 🧹. For an Epic, read every child's state. Open children outside the batch are reported and may remain open. An open child inside the batch blocks ⛳ until completed or cut by Pascal. When all its children are closed, close the Epic with proof, unless its body reserves its closing for Pascal; then leave it open and replace its `1-wip-by-agent` with `1-ready-for-human`. While any child stays open, do neither and name the open children. Done when no Epic applies, or all in-batch children are done or cut, the remaining open children are named, and the Epic is closed, marked `1-ready-for-human` or left as it was for an open child
2. With 🧰 label-for-issues, remove each merged card's state label and read the labels back. If `[cook].retro`, follow [shared Retros](../falafel.md#retros). Done when the labels are read back and each enabled retro has issue links or a no-findings result
3. Remove any remaining watches with `unwatch_pull_request`, then remove your work folder as [Work folders](../falafel.md#work-folders) says. Done when no watch remains and your folder is removed or reported kept
4. To compute ⛳ or ⏹️, apply the Cook rules in [Statuses](../falafel.md#statuses). Post your final Detail in your thread, then send `⛳ Batch delivered` or `⏹️ Batch stopped` with the Report and set the title to the final status. Then settle with 🧰 t3-runtime; the Head Chef removes your worktree. Done when the Head Chef received the outcome and your settle returns `settlesWhenTurnEnds: true`

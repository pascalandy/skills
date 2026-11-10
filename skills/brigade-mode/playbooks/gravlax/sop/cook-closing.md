# cook-closing

Apply [Statuses, Messages and Decisions](../gravlax.md#statuses) at phase entry and turn end. Keep the frozen heads and stack diff for each approval.

## Merge gate and merge

1. Freeze the stack: make no commit, checkout, restack or push until merge, a restack step 3 needs, or Fix. Run any signoff assigned to merge on each frozen head without merging. Read required GitHub statuses under the Checks gate. Try to resolve a failing or absent status through [Fix](cook-run.md#fix); carry remaining uncertainty under Decisions. Done when the checks support a merge judgment or the remaining doubt is recorded
2. Apply [Merge gates](../gravlax.md#merge-gates) and [Approval](../gravlax.md#approval) to the frozen heads. Record the gate results and any kept approval's comparison evidence in Detail. When every gate's purpose is met and no hard stop is open, show 🔀 and send `🔀 Batch merging` with the Report. Otherwise send `🍽️ Batch ready`, show 🍽️ and wait for the Head Chef's decision under Decisions. On `🔀 Merge`, record the decision and frozen heads in Detail, then send `🔀 Batch merging` before step 3. `⏳ Rework` sends you to Fix; `🍽️ Hold` keeps the batch ready; `⏹️ Drop` goes to Closing. Done when the merge notice is received, a decision is pending with the Head Chef, or Pascal's cut is recorded
3. Merge the stack:
   - Show 🔀. Check that your worktree is clean and pushed, and that GitHub holds the approved heads
   - After a restack, run any signoff assigned to merge on each new head, then apply [Approval](../gravlax.md#approval)
   - Use the project's merge procedure from your worktree. For a single PR, even in a one-layer stack, use its merge command. If that command refuses a PR in a GitHub stack, follow 🧰 gh-stack Land. For a stack of two or more PRs, follow 🧰 gh-stack Land through its Done, even when the project's procedure covers only a single PR. When the project's merge command already deployed, use that result. Otherwise run its required deploy once, from the checkout its procedure specifies
   - Run each merge or deploy command bare, with no pipe or redirect, so its permission rule matches. Read each command's whole output, since exit 0 can hide a failed deploy
   - Classify the deploy from the output of the command that ran it. The gates below and step 4 use this one result:
     - `complete`: it reached every machine
     - `not_required`: the project requires no deploy for this merge
     - `external_gap`: it missed only machines that no thread of the run uses, counting slots not launched yet, for a cause the run cannot repair, such as their credentials, and the repository's procedure does not require every machine for this stack, such as before it removes an old reader. Record each missed machine, its cause and its fix command
     - `blocked`: any other miss

   Done when GitHub shows `MERGED` for every PR of the approved stack and its deploy is `complete`, `not_required` or `external_gap`
4. On a failed merge or `blocked` deploy, record landed PRs and fix the cause through [Fix](cook-run.md#fix). Continue for an `external_gap`. Report a partial outcome and withdrawn readiness to the Head Chef. Resume at step 1 after Proof. When a merge fails twice for the same cause, show ⏸️ and send its history to the Head Chef as a fault. Done when the stack merged or the Head Chef has an unresolved blocker
5. After the merge, send the Head Chef `Batch merged` with deploy results, naming each `external_gap` machine with its cause and fix command. For `Release: yes`, follow the remaining repository release procedure from `main` and report a failure before closing. Done when all merge and release outcomes are recorded

If Pascal says Stop, follow [cook-run Stop](cook-run.md#stop). While frozen, a watch finding enters Fix, which withdraws readiness. Passing checks preserve readiness.

## Closing

For a batch without PRs, begin here.

1. Show 🧹. For the batch's Epic and the Epic of each merged card, read every child's state and every item of the Epic's "Done when". An open child inside the batch blocks ⛳ until completed or cut by Pascal. Close an Epic with proof only when every child is closed and each "Done when" item holds; clear its state label. If its body reserves closing for Pascal, leave it open at `1-ready-for-human` instead. Otherwise keep it open and name every pending child and "Done when" item. Done when each applicable Epic is closed, ready for Pascal or reported with its pending items, and every in-batch child is done or cut
2. With 🧰 label-for-issues, remove each merged card's state label and read the labels back. If `[cook].retro`, follow [shared Retros](../gravlax.md#retros). Done when the labels are read back and each enabled retro has issue links or a no-findings result
3. Remove remaining watches with `unwatch_pull_request`. Unless the project's procedure keeps head branches, delete each merged PR's GitHub head branch with `git push --no-verify --force-with-lease=refs/heads/<branch>:<merged head SHA> origin :refs/heads/<branch>`. Check GitHub: an absent branch is done; keep and report a branch whose tip moved. Then remove your work folder under [Work folders](../gravlax.md#work-folders). Done when no watch remains, each branch is absent or reported kept, and your folder is removed or reported kept
4. To compute ⛳ or ⏹️, apply the Cook rules in [Statuses](../gravlax.md#statuses). Post your final Detail in your thread, then send `⛳ Batch delivered` or `⏹️ Batch stopped` with the Report and set the title to the final status. Then settle with 🧰 t3-runtime; the Head Chef removes your worktree. Done when the Head Chef received the outcome and your settle returns `settlesWhenTurnEnds: true`

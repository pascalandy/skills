# cook-closing

Apply [Statuses, Messages and Decisions](../gravlax.md#statuses) at phase entry and turn end. Keep frozen heads and stack diff per approval.

## Merge gate and merge

1. Freeze stack: no commit, checkout, restack or push until merge, a restack step 3 needs, or Fix. Run any signoff assigned to merge on each frozen head without merging. Read required GitHub statuses under Checks gate. Try to resolve failing or absent status via [Fix](cook-run.md#fix); carry remaining uncertainty under Decisions. Done when checks support a merge judgment or remaining doubt is recorded
2. Apply [Merge gates](../gravlax.md#merge-gates) and [Approval](../gravlax.md#approval) to frozen heads. Record gate results and any kept approval's comparison evidence in Detail. When every gate's purpose is met and no hard stop is open, show 🔀 and send `🔀 Batch merging` with Report. Otherwise send `🍽️ Batch ready`, show 🍽️ and wait for Head Chef's decision under Decisions. On `🔀 Merge`, record decision and frozen heads in Detail, then send `🔀 Batch merging` before step 3. `⏳ Rework` → Fix; `🍽️ Hold` keeps batch ready; `⏹️ Drop` → Closing. Done when merge notice is received, a decision is pending with Head Chef, or Pascal's cut is recorded
3. Merge stack:
   - Show 🔀. Check your worktree is clean and pushed, and GitHub holds approved heads
   - After restack, run any signoff assigned to merge on each new head, then apply [Approval](../gravlax.md#approval)
   - Use project's merge procedure from your worktree. Single PR, even in a one-layer stack: use its merge command. If that command refuses a PR in a GitHub stack, follow 🧰 gh-stack Land. Stack of two or more PRs: follow 🧰 gh-stack Land through its Done, even when project's procedure covers only a single PR. When project's merge command already deployed, use that result. Otherwise run its required deploy once, from the checkout its procedure specifies
   - Run each merge or deploy command bare, no pipe or redirect, so its permission rule matches. Read each command's whole output: exit 0 can hide a failed deploy
   - Classify deploy from output of the command that ran it. Gates below and step 4 use this one result:
     - `complete`: reached every machine
     - `not_required`: project requires no deploy for this merge
     - `external_gap`: missed only machines no thread of the run uses, counting slots not launched yet, for a cause the run cannot repair, e.g. their credentials, and repository's procedure does not require every machine for this stack, e.g. before it removes an old reader. Record each missed machine, its cause and fix command
     - `blocked`: any other miss

   Done when GitHub shows `MERGED` for every PR of approved stack and its deploy is `complete`, `not_required` or `external_gap`
4. On failed merge or `blocked` deploy, record landed PRs and fix cause via [Fix](cook-run.md#fix). Continue for `external_gap`. Report partial outcome and withdrawn readiness to Head Chef. Resume at step 1 after Proof. When a merge fails twice for same cause, show ⏸️ and send its history to Head Chef as a fault. Done when stack merged or Head Chef has an unresolved blocker
5. After merge, send Head Chef `Batch merged` with deploy results, naming each `external_gap` machine with its cause and fix command. For `Release: yes`, follow remaining repository release procedure from `main`; report a failure before closing. Done when all merge and release outcomes are recorded

If Pascal says Stop, follow [cook-run Stop](cook-run.md#stop). While frozen, a watch finding enters Fix, which withdraws readiness. Passing checks keep readiness.

## Closing

Batch without PRs: begin here.

1. Show 🧹. For batch's Epic and Epic of each merged card, read every child's state and every item of Epic's "Done when". An open child inside the batch blocks ⛳ until completed or cut by Pascal. Close an Epic with proof only when every child is closed and each "Done when" item holds; clear its state label. If its body reserves closing for Pascal, leave it open at `1-ready-for-human` instead. Otherwise keep it open and name every pending child and "Done when" item. Done when each applicable Epic is closed, ready for Pascal or reported with its pending items, and every in-batch child is done or cut
2. With 🧰 label-for-issues, remove each merged card's state label and read labels back. If `[cook].retro`, follow [shared Retros](../gravlax.md#retros). Done when labels are read back and each enabled retro has issue links or a no-findings result
3. Remove remaining watches with `unwatch_pull_request`. Unless project's procedure keeps head branches, delete each merged PR's GitHub head branch with `git push --no-verify --force-with-lease=refs/heads/<branch>:<merged head SHA> origin :refs/heads/<branch>`. Check GitHub: absent branch is done; keep and report a branch whose tip moved. Then remove your work folder under [Work folders](../gravlax.md#work-folders). Done when no watch remains, each branch is absent or reported kept, and your folder is removed or reported kept
4. To compute ⛳ or ⏹️, apply Cook rules in [Statuses](../gravlax.md#statuses). Post your final Detail in your thread, then send `⛳ Batch delivered` or `⏹️ Batch stopped` with Report and set title to final status. Then settle with 🧰 t3-runtime; Head Chef removes your worktree. Done when Head Chef received the outcome and your settle returns `settlesWhenTurnEnds: true`

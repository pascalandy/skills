# chef-run

Report to the Head Chef with `t3_thread_send`. Keep each Cook's threadId, worktree, branches, file ownership, last received phase, hold and report receipt in `watch.toml` in your work folder. Write it atomically after each launch, received report, status change, hold and replacement as [watchdog](watchdog.md) defines. Apply [Statuses, Messages and Decisions](../carpaccio.md#statuses) at phase entry and turn end.

## Run

1. Rename yourself with the Chef title in Roles at ⏳. Create `watch.toml` and arm your 🐕 Watchdog, including for a batch without PRs. Relay each Cook's `📍` line in your own thread, so that each counter belongs to one Cook. Compute the title status from your own facts and each Cook's last received phase. Done when the title and progress match the current work and your Watchdog reported its schedule id
2. For a batch without PRs, keep no Cook slot, do its work under ⏳ and go to Closing. Otherwise, group the cards with the parallel rule in [Decisions](../carpaccio.md#decisions). Stay within `max-cooks`. Log the reason. Give shared generated files to one group, or serialize their writers. Add `<served>/<cooks>` to your title after grouping. Done when every card and file group has one Cook, or the no-PR work is done
3. Fetch `origin`, then create each worktree from `origin/HEAD`, under `~/projects/.worktrees/<repo>-<branch>/`, with branch `<batch>-<c>` using a Git-safe batch slug. Use `git -C <clone> worktree add <path> -b <branch> origin/HEAD`. Done when each worktree's status shows its assigned branch
4. Select `[cook]` with shared Model selection. Before retrying a launch, check the thread list for a Cook in its slot. Launch each Cook with `t3_thread_launch` in your project, `workspaceStrategy: {type: "existing_worktree", worktreePath: <absolute path>, branch: <branch>}`, its title from Roles at 🍳, and the message below. Add each returned threadId to `watch.toml` atomically. Done when each threadId is recorded and `t3_thread_read` shows it started
5. Follow received progress messages and update the counter. Arbitrate requests to cross file ownership before granting them; show ⏸️ while waiting on the Head Chef for an answer. On `🍽️ Stack ready`, validate that Cook's stack. Once every counted Cook served and checks passed on the frozen heads, run `chef-closing` to choose `🍽️ Batch ready` or `🔀 Batch merging`. Done when each Cook has an outcome and Closing ends

```text
$brigade-mode ; carpaccio ; cook-implement
Role: Cook <b>.<c> <id4>. Report only to Chef <b>, threadId <full threadId>, with t3_thread_send.
Worktree: <absolute path>, branch <branch>, base <trunk>
Plan: <assigned cards, requirements and batch threat model>
Ownership: <your files; other Cooks' groups requiring Chef approval>
Release: <yes/no; required release content and which Cook owns it>
Fast track: <yes/no>
Rules: <rules.md path, plus additions>
Work folder: <expand Work folders in carpaccio.md>
```

## Return or replace a Cook

On each wake, check your Watchdog's schedule in `list_scheduled_tasks`. If the schedule exists, read its `boundThreadId` with `t3_thread_read`, `runLimit: 1` for the latest run time. If the schedule is missing, disabled, failed or late by twice `watch-minutes`, delete any old schedule and cancel its task before re-arming.

On `🐕 Watchdog <id4>: <finding>`, read the current slot and thread state. Resume, replace or reconcile the Cook. Escalate an unrepairable fault to the Head Chef.

On a Watchdog wake sent to you, check whether the action already happened. Resume the current step. Recompute your status and end without replying.

If you wait for a check or child, write or refresh `wait` before ending on 🔀 or 🧹, or on ⏳ with no counted Cook on 🍳 or ⏸️.

Done when the schedule is live and each finding has an owner.

Return a worktree for Fix when a finding, changed diff or merge failure withdraws readiness. Tell the Head Chef when a previously ready batch loses readiness. Count each return of the same stack for the same cause; at `max-returns`, show ⏸️ and send the history to the Head Chef as a fault. Done when the Cook either sends fresh `🍽️ Stack ready` or the fault has an owner.

For a Cook that cannot continue, inspect its thread and PRs. Set the old record's `replacedBy = "pending"` in `watch.toml` before interrupting it, cancelling queued turns and renaming it ⏹️. Launch the replacement in the same slot and existing worktree, carrying the cards, branch heads, PR URLs, review rounds and decisions. Update the old record's `replacedBy` and append a current record with its threadId atomically. The replacement links and watches the PRs. Archive the old thread and ignore its late reports. Done when one Cook owns the slot and worktree.

For a replacement Chef, receive the old Chef's state from the Head Chef. Recreate `watch.toml`, arm a new Watchdog, link and watch the PRs again; send each Cook `Chef <b> <id4> is now threadId <id>, replacing <old threadId>`. Done when each Cook reports to you and your schedule is live.

On `⏹️ Cut <card>` from the Head Chef, relay it to its Cook and update ownership and the counter after the Cook reports the cut. A Cook with no cards leaves the count once it closes at ⏹️. Done when no cut card remains assigned.

## Stop

Discard unused merge approval. Finish a merge or release already running and record its result, then relay `⏹️ Stop` to active Cooks so each knows whether its stack merged. Enter [chef-closing](chef-closing.md#closing) and use its shared gates for retros, Epic closure, worktree cleanup and the final status. Keep your Watchdog armed until that procedure removes it. Done when Closing has reported the outcome and settled.

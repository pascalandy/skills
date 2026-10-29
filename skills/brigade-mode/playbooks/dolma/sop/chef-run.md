# chef-run

Report to the Head Chef with `t3_thread_send`. Keep your Cook's threadId, worktree, branches, last received phase, hold and report receipt in `watch.toml` in your work folder. Write it atomically as [watchdog](watchdog.md#files) defines. Apply [Statuses, Messages and Decisions](../dolma.md#statuses) at phase entry and turn end.

## Run

1. Rename yourself with the Chef title in Roles at ⏳. Create `watch.toml`. Relay your Cook's `📍` lines in your own thread. Compute the title status from your own facts and your Cook's last received phase. Done when the title and progress match the current work
2. For a batch without PRs, keep no Cook slot or Chef Watchdog, do its work under ⏳ and go to Closing. Otherwise, register one Cook slot, `cook-<b>.1`, that holds every card of the batch, in `watch.toml`, then arm your 🐕 Watchdog as [watchdog](watchdog.md#arm) tells. List open PRs outside the run that change the batch's files or the spec files its cards cite. Send any overlap to the Head Chef with your default, and wait for its answer before launching the Cook. Add `[0/1]` to your title. Done when the Cook slot holds every card and your Watchdog reported its schedule id, or the no-PR work is done
3. Fetch `origin`, then create the Cook's worktree from `origin/HEAD`, under `~/projects/.worktrees/<repo>-<branch>/`, with branch `<batch>-1` using a Git-safe batch slug. Use `git -C <clone> worktree add <path> -b <branch> origin/HEAD`. Done when the worktree's status shows its assigned branch
4. Select `[cook]` with shared Model selection. Before retrying a launch, check the thread list for a Cook in its slot. Launch the Cook with `t3_thread_launch` in your project, `workspaceStrategy: {type: "existing_worktree", worktreePath: <absolute path>, branch: <branch>}`, its title from Roles at 🍳, and the message below. Add the returned threadId to `watch.toml` atomically. Done when the threadId is recorded and `t3_thread_read` shows it started
5. Follow received progress messages and update the counter. Show ⏸️ while waiting on the Head Chef for an answer. On `🍽️ Stack ready`, validate the stack. Once the Cook served and checks passed on the frozen heads, run `chef-closing` to choose `🍽️ Batch ready` or `🔀 Batch merging`. Done when the Cook has an outcome and Closing ends

```text
$brigade-mode ; dolma ; cook-implement
Role: Cook <b>.1 <id4>. Report only to Chef <b>, threadId <full threadId>, with t3_thread_send.
Worktree: <absolute path>, branch <branch>, base <trunk>
Plan: <goal, every card of the batch in order with acceptance criteria, and batch threat model>
Release: <yes/no; required release content>
Fast track: <yes/no>
Rules: <rules.md path, plus additions>
Work folder: <absolute path>
```

## Return or replace a Cook

On each wake while your phase is live, reconstruct a missing or unreadable `watch.toml` from your thread history. Include all registered slots, including those awaiting launch, their current state and the recorded Watchdog ids. Check your Watchdog's schedule under [Schedule health](watchdog.md#schedule-health) only when that file has a current Cook slot. If it is unhealthy, delete any old schedule, cancel its task and re-arm your Watchdog.

On `🐕 Watchdog <id4>: <finding>`, act as its row in [Messages](../dolma.md#messages) says.

Before you end a turn to wait, write or refresh your `wait` file as [watchdog](watchdog.md#files) defines.

Done when each finding has an owner and any required schedule is live.

Return a worktree for Fix when a finding, changed diff or merge failure withdraws readiness. Tell the Head Chef when a previously ready batch loses readiness. Count each return of the same stack for the same cause; at `max-returns`, show ⏸️ and send the history to the Head Chef as a fault. Done when the Cook either sends fresh `🍽️ Stack ready` or the fault has an owner.

For a Cook that cannot continue, inspect its thread and PRs. Set the old record's `replacedBy = "pending"` in `watch.toml` before interrupting it, cancelling queued turns and renaming it ⏹️. Launch the replacement in the same slot and existing worktree, carrying the cards, branch heads, PR URLs, review rounds and decisions. Update the old record's `replacedBy` and append a current record with its threadId atomically. The replacement links and watches the PRs. Archive the old thread and ignore its late reports. Done when one Cook owns the slot and worktree.

For a replacement Chef, receive the old Chef's state from the Head Chef. Recreate `watch.toml`, arm a new Watchdog only when it has a current Cook slot, link and watch the PRs again; send the Cook `Chef <b> <id4> is now threadId <id>, replacing <old threadId>`. Done when the Cook reports to you and any required schedule is live.

On `⏹️ Cut <card>` from the Head Chef, relay it to the Cook and update the counter after the Cook reports the cut. When no card remains, the Cook closes at ⏹️ and leaves the count. Done when no cut card remains assigned.

## Stop

Discard unused merge approval. Finish a merge or release already running and record its result, then relay `⏹️ Stop` to the active Cook so it knows whether its stack merged. Enter [chef-closing](chef-closing.md#closing) and use its shared gates for retros, Epic closure, worktree cleanup and the final status. Keep any existing Watchdog armed until that procedure removes it. Done when Closing has reported the outcome and settled.

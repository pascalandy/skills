# chef-run

Report to the Head Chef with `t3_thread_send`. Keep each Cook's threadId, worktree, branches, file ownership and last reported phase in your conversation. Apply [Statuses, Messages and triggers](../carpaccio.md#statuses) at phase entry and turn end.

## Run

1. Rename yourself with the Chef title in Roles at ⏳. At each process step, post `📍 [progress] / <step>/6` in your own thread; compute the title status from your own facts and each Cook's last received phase. Done when the title and progress match the current work
2. For a batch without PRs, keep no Cook slot, do its work under ⏳ and go to Closing. Otherwise group independent cards by disjoint files when `Parallel Cooks: yes`, combining groups to stay within `max-cooks`. If the requested groups overlap, use one Cook and say why. If parallel Cooks are off, launch one Cook. Give shared generated files to one group, or serialize their writers. Add `<served>/<cooks>` to your title after grouping. Done when every card and file group has one Cook, or the no-PR work is done
3. Fetch `origin`, then create each worktree from `origin/HEAD`, under `~/projects/.worktrees/<repo>-<branch>/`, with branch `<batch>-<c>` using a Git-safe batch slug. Use `git -C <clone> worktree add <path> -b <branch> origin/HEAD`. Done when each worktree's status shows its assigned branch
4. Select `[cook]` with shared Model selection. Before retrying a launch, check the thread list for a Cook in its slot. Launch each Cook with `t3_thread_launch` in your project, `workspaceStrategy: {type: "existing_worktree", worktreePath: <absolute path>, branch: <branch>}`, its title from Roles at 🍳, and the message below. Done when each returned threadId is recorded and `t3_thread_read` shows it started
5. Follow received progress messages and update the counter. Arbitrate requests to cross file ownership before granting them; show ⏸️ while waiting on the Head Chef for an answer. On `🍽️ Stack ready`, validate that Cook's stack. Once every counted Cook served and checks passed on the frozen heads, run `chef-closing` to choose `🍽️ Batch ready` or `🔀 Batch merging`. Done when each Cook has an outcome and Closing ends

```text
$brigade-mode ; carpaccio ; cook-implement
Role: Cook <b>.<c> <id4>. Report only to Chef <b>, threadId <full threadId>, with t3_thread_send.
Worktree: <absolute path>, branch <branch>, base <trunk>
Plan: <assigned cards, requirements and batch threat model>
Ownership: <your files; other Cooks' groups requiring Chef approval>
Release: <yes/no; required release content and which Cook owns it>
Fast track: <yes/no>
Rules: <inherited and standing rules per the Rules bullet under Shared rules in carpaccio.md>
Work folder: <expand Work folders in carpaccio.md>
```

## Return or replace a Cook

Return a worktree for Fix when a finding, changed diff or merge failure withdraws readiness. Tell the Head Chef when a previously ready batch loses readiness. Count each return of the same stack for the same cause; at `max-returns`, show ⏸️ and send the history to the Head Chef as a fault. Done when the Cook either sends fresh `🍽️ Stack ready` or the fault has an owner.

For a Cook that cannot continue, inspect its thread and PRs, then interrupt it, cancel queued turns and rename it ⏹️. Launch the replacement in the same slot and existing worktree, carrying the cards, branch heads, PR URLs, review rounds and decisions. The replacement links and watches the PRs. Archive the old thread and ignore its late reports. Done when one Cook owns the slot and worktree.

For a replacement Chef, receive the old Chef's state from the Head Chef. Link and watch the PRs again; send each Cook `Chef <b> <id4> is now threadId <id>, replacing <old threadId>`. Done when each Cook reports to you.

On `⏹️ Cut <card>` from the Head Chef, relay it to its Cook and update ownership and the counter after the Cook reports the cut. A Cook with no cards leaves the count once it closes at ⏹️. Done when no cut card remains assigned.

## Stop

Discard unused merge approval. Finish a merge already running and report its result, then relay `⏹️ Stop` to active Cooks so each knows whether its stack merged. Ask each Cook to close, then confirm its final status and settlement with 🧰 t3-runtime. Compute ⛳ if the batch merged and released, otherwise ⏹️. Send the Head Chef the matching final batch message with the shared Report and retained work, then settle. Done when each Cook is settled, the Head Chef has the outcome and you are settled.

# chef-run

Report to the Head Chef with `t3_thread_send`. Keep each Cook's threadId, worktree, branches and file ownership in your conversation.

## Run

1. Rename yourself with the Chef title in Roles. At each process step, update `<step>/6` and post `📍 [progress] / <step>/6` in your own thread. Done when the title and progress name the current step
2. Group independent cards by disjoint files when `Parallel Cooks: yes`, up to `max-cooks`. Otherwise launch one Cook; if no independent groups exist, say why. Give shared generated files to one group, or serialize their writers. Done when every card and file group has one Cook
3. Fetch `origin`, then create each worktree from `origin/HEAD`, under `~/projects/.worktrees/<repo>-<branch>/`, with branch `<batch>-<c>` using a Git-safe batch slug. Use `git -C <clone> worktree add <path> -b <branch> origin/HEAD`. Done when each worktree's status shows its assigned branch
4. Select `[cook]` with shared Model selection. Launch each Cook with `t3_thread_launch` in your project, `workspaceStrategy: {type: "existing_worktree", worktreePath: <absolute path>, branch: <branch>}`, its title from Roles, and the message below. Done when each returned threadId is recorded and `t3_thread_read` shows it started
5. Follow progress messages; arbitrate requests to cross file ownership before granting them. Forward a request you cannot resolve through the chain. On `🚦 Stack ready`, run `chef-closing`. Done when each Cook has an outcome and Closing ends

```text
$brigade-mode ; carpaccio ; cook-implement
Role: Cook <b>.<c> <id4>. Report only to Chef <b>, threadId <full threadId>, with t3_thread_send.
Worktree: <absolute path>, branch <branch>, base <trunk>
Plan: <assigned cards, requirements and batch threat model>
Ownership: <your files; other Cooks' groups requiring Chef approval>
Release: <yes/no; required release content and which Cook owns it>
Fast track: <yes/no>
```

## Stop

Relay 🛑 Stop to every active Cook and discard unused merge approval. Finish a merge already running and report its result before completing the stop. Confirm each Cook's stop and settlement with 🧰 t3-runtime, then send the Head Chef `🛑 Batch <b> stopped` with the shared Report and retained work. Settle yourself. Done when each Cook is settled, the Head Chef has the outcome and you are settled.

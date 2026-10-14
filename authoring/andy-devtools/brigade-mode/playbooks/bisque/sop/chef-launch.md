# chef-launch

1. **Prepare the worktree.** Before the batch's first writer, create its worktree from your clone: `git -C <clone> fetch origin`, then `git -C <clone> worktree add ~/projects/.worktrees/<repo>-<branch> -b <branch> origin/HEAD`, with a branch named after the batch. Skip this step when the Head Chef gave you PRs, whose worktrees you reuse. Done when `git -C <worktree> status` shows the branch
2. **Pick the model.** Read the role's row for your provider in `config.toml`: `chef-on-claude` or `chef-on-codex`. If the row sets `inherit`, use your instance, model, and reasoning level. Read them on your own thread with `t3_thread_configuration`. Otherwise map `instance` to `instanceId` and copy `model`. Build `modelSelection` with these provider options:
	- `reasoning-level` maps to codex `reasoningEffort` or claudeAgent `effort`
	- `service-tier` maps `standard` and `fast` to codex `serviceTier` values `default` and `priority`, or claudeAgent `fastMode` values `false` and `true`, respectively

	If `runtime-mode` is not `inherit`, pass it as `runtimeMode`. Confirm the selection with `orchestrator_capabilities`. If a configured value is unavailable, ask the Head Chef. Done when the instance, model, reasoning level, service tier, and runtime mode are supported
3. **Launch the Cook.** Call `t3_thread_launch` in your own project with `workspaceStrategy` `existing_worktree`, the worktree's path and branch, the `modelSelection` from step 2, the Cook's title from Roles in `bisque.md`, and the message below. Done when `t3_thread_read` shows the thread started
4. **Delegate a barrage or the DocWriter.** Call `delegate_task` with `mode` `async`, the title from Roles in `bisque.md`, the message below as `task`, and step 2's selection as `target`: `instanceId` as `providerInstanceId`, `model`, and the provider options. Set `clientRequestId` as the shared rules say. In step 2, delegate manic-1 and manic-2 in the same turn. Then end your turn: each result wakes you. Done when every delegation of this step returned a taskId

```text
$brigade-mode ; bisque ; <sop>
Read playbooks/bisque/sop/<sop>.md in the brigade-mode skill and follow it.
Role: <title>. <report line>
Section: <the section to run, for a Cook or a DocWriter>
Worktrees: <absolute paths>
Base branch: <the branch the stack starts from>
PRs: <URLs>
Plan: <this batch's cards>
Prior rounds: <on a later pass or a fix round: each finding, your decision, the owner's fix with its commit, and each objection still open>
When you finish your work, run 🧰 2nd-pass on it, then report.
```

The report line of a Cook reads "Report only to Chef <b>, threadId <your full threadId>, with t3_thread_send." The report line of a delegate reads "Your final message is your report." Leave out a line that has nothing to carry, such as `PRs` for a Cook that has not opened any yet.

5. **Premortem.** When you delegate manic-2, write your own premortem while it runs. Assume the stack merged and broke something a week later. Identify blind spots, debt, and code smells that explain it. Done when your premortem lists its findings, or says it found none

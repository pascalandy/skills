# chef-launch

1. **Name yourself.** Before your first launch, rename yourself `👑 Chef <id4> <subject>` with `t3_thread_update` action `rename`. Done when your title matches
2. **Pick the model.** Read the role's row for your provider in `config.toml`: `chef-on-claude` or `chef-on-codex`. If the row sets `inherit`, use your instance, model, and reasoning level. Read them on your own thread with `t3_thread_configuration`. Otherwise map `instance` to `instanceId` and copy `model`. Build `modelSelection` with these provider options:
	- `reasoning-level` maps to codex `reasoningEffort` or claudeAgent `effort`
	- `service-tier` maps `standard` and `fast` to codex `serviceTier` values `default` and `priority`, or claudeAgent `fastMode` values `false` and `true`, respectively

	If `runtime-mode` is not `inherit`, pass it as `runtimeMode`. Confirm the selection with `orchestrator_capabilities`. If a configured value is unavailable, ask the user. Done when the instance, model, reasoning level, service tier, and runtime mode are supported
3. **Launch.** Call `t3_thread_launch` in the `projects` project with `workspaceStrategy` `root` and the `modelSelection` from step 2. Use the thread name from Roles in `<route>.md` and the message below. Keep the returned threadId. After an error or a lost response, find the thread with `t3_thread_list` before retrying. Done when `t3_thread_read` shows the thread started

```text
$brigade-mode ; <route> ; <sop>
Read playbooks/<route>/sop/<sop>.md in the brigade-mode skill and follow it.
Role: <thread name>. Report only to the Chef, threadId <your full threadId>, with t3_thread_send.
Worktrees: <absolute paths>
PRs: <URLs>
Plan: <the agreed plan, or this thread's card>
Prior findings: <on a barrage rerun: each finding and your decision on it>
When you finish your work, run 🧰 2nd-pass on it, then report to the Chef.
```

Leave out a line that has nothing to carry, such as `PRs` for a Cook that has not opened any yet.

4. **Premortem.** For a manic-2 launch, write your own premortem while it runs. Assume the stack merged and broke something a week later. Identify blind spots, debt, and code smells that explain it. Done when your premortem lists its findings, or says it found none

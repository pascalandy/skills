# main-launch

1. **Name yourself.** Before your first launch, rename yourself `👑 MAIN <id4> <subject>` with `t3_thread_update` action `rename`. Done when your title matches
2. **Pick the model.** Read the role's row for your provider in `config.toml`: `main-on-claude` or `main-on-codex`. If the row sets `inherit`, use your instance, model, and reasoning level. Otherwise map `instance` to `instanceId` and copy `model`. Build `modelSelection` with these provider options:
	- `reasoning-level` maps to codex `reasoningEffort` or claudeAgent `effort`
	- `service-tier` maps `standard` and `fast` to codex `serviceTier` values `default` and `priority`, or claudeAgent `fastMode` values `false` and `true`, respectively

	If `runtime-mode` is not `inherit`, pass it as `runtimeMode`. Confirm the selection with `orchestrator_capabilities`. If a configured value is unavailable, ask Pascal. Done when the instance, model, reasoning level, service tier, and runtime mode are supported
3. **Launch.** Call `t3_thread_launch` in the `projects` project with `workspaceStrategy` `root` and the `modelSelection` from step 2. Use the thread name from Roles in `SKILL.md` and the message below. Keep the returned threadId. After an error or a lost response, find the thread with `t3_thread_list` before retrying. Done when `t3_thread_read` shows the thread started

```text
$s3 ; <sop>
Read references/sop/<sop>.md in the s3 skill and follow it.
Role: <thread name>. Report only to MAIN, threadId <your full threadId>, with t3_thread_send.
Worktrees: <absolute paths>
PRs: <URLs>
Plan: <the agreed plan, or this thread's card>
Prior findings: <on a REV rerun: each finding and your decision on it>
When you finish your work, run 🧰 2nd-pass on it, then report to MAIN.
```

Leave out a line that has nothing to carry, such as `PRs` for a COD that has not opened any yet.

4. **Premortem.** For a BLAST launch, write your own premortem while it runs. Assume the stack merged and broke something a week later. Identify blind spots, debt, and code smells that explain it. Done when your premortem lists its findings, or says it found none

# main-launch

MAIN runs this SOP before each thread it launches.

1. **Name yourself.** Before your first launch, rename yourself `👑 MAIN <id4> <subject>` with `t3_thread_update` action `rename`. Done when your title matches
2. **Pick the model.** In `config.toml`, read the thread's role table and its row for your provider, `main-on-claude` or `main-on-codex`. With `inherit = true`, omit `modelSelection`. Otherwise use `instance` as `instanceId`, `model`, and `reasoning-level` as the model's Reasoning option: `reasoningEffort` on codex, `effort` on claudeAgent. When `service-tier` is `fast`, add codex `serviceTier` `priority` or claudeAgent `fastMode` `true`. When `runtime-mode` is not `inherit`, pass it as `runtimeMode`. Confirm each value with `orchestrator_capabilities`, and ask Pascal when one is gone from the catalog. Done when the selection exists in the catalog, such as `{"instanceId":"codex","model":"gpt-6.1-sol","options":[{"id":"reasoningEffort","value":"high"}]}`
3. **Launch.** Call `t3_thread_launch` in the `projects` project with `workspaceStrategy` `root`. Set the title to the thread name from Roles in `SKILL.md`, and the message to the template below. Done when `t3_thread_list` shows the thread under its title

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

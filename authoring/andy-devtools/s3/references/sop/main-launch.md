# main-launch

MAIN runs this SOP before each thread it launches.

1. **Name yourself.** Before your first launch, rename yourself `👑 MAIN <id4> <subject>` with `t3_thread_update` action `rename`. Done when your title matches
2. **Pick the model.** COD and DOC inherit your model, so omit `modelSelection`. A REV runs on the other model family, at `xhigh`. Confirm its selection with `orchestrator_capabilities` and use the matching `providerInstanceId` as `instanceId`. When the model is gone from the catalog, ask Pascal. Done when the selection exists in the catalog
	- MAIN on Claude: `{"instanceId":"codex","model":"gpt-6.1-sol","options":[{"id":"reasoningEffort","value":"xhigh"}]}`
	- MAIN on Codex: `{"instanceId":"claudeAgent","model":"claude-opus-5-5","options":[{"id":"effort","value":"xhigh"}]}`
3. **Launch.** Call `t3_thread_launch` in the `projects` project with `workspaceStrategy` `root`. Set the title to the thread name from Roles in `SKILL.md`, and the message to the template below. Done when `t3_thread_list` shows the thread under its title

```text
s3 ; <sop>
Read references/sop/<sop>.md in the s3 skill and follow it.
Role: <thread name>. Report only to MAIN, threadId <your full threadId>, with t3_thread_send.
Worktrees: <absolute paths>
PRs: <URLs>
Plan: <the agreed plan, or this thread's card>
Prior findings: <on a REV rerun: each finding and your decision on it>
When you finish your work, run 🧰 2nd-pass on it, then report to MAIN.
```

Leave out a line that has nothing to carry, such as `PRs` for a COD that has not opened any yet.

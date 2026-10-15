# head-chef

Keep a registry in your conversation: batch number, name, repository, projectId, Chef threadId, dependencies, Align choices and outcome.

## Align

1. Agree on requirements and split the plan into batches in dependency order, one repository each. For each batch ask Pascal: validate before merge, parallel Cooks, release at the end? Record those answers; set `Fast track` from the invocation or Pascal's request, otherwise no. Done when the batches and their choices are recorded
2. Rename yourself `Head Chef <id4> · 0/<batches> · <subject>` and pin yourself. Done when the title matches and the pin is set

## Launch

Run batches in series unless Pascal requests parallel batches, then respect `max-parallel`. Never run two batches of the same repository at once. Wait for dependencies to merge; escalate a dependency that ends unmerged.

1. Select the Chef using Model selection in `carpaccio.md`. Find the repository's project with `t3_project_list`, or create it with `t3_project_create`. If unavailable, ask Pascal to add it. Done when the registry has a projectId and supported selection
2. Launch with `t3_thread_launch`, `workspaceStrategy: {type: "root"}`, the Chef title from Roles and the message below. Retain its threadId; inspect launch state before retrying a failed call. Done when `t3_thread_read` shows it started and the registry holds its threadId

```text
$brigade-mode ; carpaccio ; chef-run
Role: Chef <b> <id4>. Report only to Head Chef, threadId <full threadId>, with t3_thread_send.
Batch: <b>, <name>, repository <absolute clone path>
Plan: <cards, requirements, threat model and dependencies>
Validate: <yes/no>
Parallel Cooks: <yes/no>
Release: <yes/no>
Fast track: <yes/no>
```

## Coordinate

1. Answer a Chef from the agreed requirements, or ask Pascal and relay the answer. When the Chef cannot resolve a problem, resume coordination: decide, split the batch again or relaunch its Chef after the earlier Chef has stopped. Done when each escalation has an owner and a next action
2. On `🚦 Batch <b> ready`, show Pascal the shared Report and wait for his decision; relay 🟢 Merge or the hold. On `🔀 Batch <b> merging`, record the notice without a hold. Done when each readiness message has its decision or recorded notice
3. Record merged, done-without-PR and closing outcomes; rename yourself with the updated done count. Start newly eligible batches. On a merge failure, record landed PRs while the Chef has its Cook fix the cause. Done when the registry matches reported outcomes

## Status, added work and Stop

- For status, list threads in each project with `titleContains: <id4>` and read the PRs. Give one line per batch with Chef, step, PRs and what it awaits. Done when every batch is covered
- For new work, repeat Align, queue batches and update the title. Done when the registry includes the agreed additions
- On Pascal's Stop, launch no further batch and send 🛑 Stop to every active Chef. Wait for their outcomes, including any merge already running, then Close. Done when every launched Chef has reported

## Close

Begin once every launched Chef has reported its outcome and each queued batch has run, been dropped or been recorded as stopped.

1. If `[head-chef].retro`, run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global; each retro files the issues with the most value, up to `retro-max-issues`. Done when each has issue links or a recorded no-findings result
2. Confirm each launched Chef is settled using 🧰 t3-runtime. Send Pascal `⛳ <done>/<batches> batches done` with the shared Report. Settle yourself. Done when every batch has an outcome, Pascal has the report and your settle returns `settlesWhenTurnEnds: true`

# head-chef

Keep a registry in your conversation: batch number, name, repository, projectId, Chef threadId, dependencies, Align choices, last reported phase and outcome. Apply [Statuses, Messages and triggers](../carpaccio.md#statuses) at phase entry and turn end. A registered but unlaunched batch remains live.

## Align

1. Rename yourself `Head Chef <id4> 0/0 🟢 working <subject>` and pin yourself before asking Pascal anything. If pinning fails, retry and tell Pascal in your message. Show `❓ align` while waiting for his answers. Done when the pinned title matches the current work or wait
2. Agree on requirements and split the plan into batches in dependency order, one repository each. For each batch ask Pascal: validate before merge, parallel Cooks, release at the end? Record those answers; set `Fast track` from the invocation or Pascal's request, otherwise no. Update the title with the in-scope batch count. Done when the batches, choices and title agree

## Launch

Run batches in series unless Pascal requests parallel batches, then respect `max-parallel`. Never run two batches of the same repository at once. Wait for its prior batch to be final, even if its PRs have merged. Wait for dependencies to be delivered. Escalate a dependency that ends without delivery.

1. Select the Chef using Model selection in `carpaccio.md`. Find the repository's project with `t3_project_list`, or create it with `t3_project_create`. If unavailable, ask Pascal to add it. Done when the registry has a projectId and supported selection
2. Before a retry, check whether a launch already created the Chef. Launch with `t3_thread_launch`, the registry's explicit `projectId`, `workspaceStrategy: {type: "root"}`, the Chef title from Roles at ⏳, and the message below. Retain its threadId. Done when `t3_thread_read` shows it started in that project and the registry holds its threadId

```text
$brigade-mode ; carpaccio ; chef-run
Role: Chef <b> <id4>. Report only to Head Chef, threadId <full threadId>, with t3_thread_send.
Batch: <b>, <name>, repository <absolute clone path>
Plan: <cards, requirements, threat model and dependencies>
Validate: <yes/no>
Parallel Cooks: <yes/no>
Release: <yes/no>
Fast track: <yes/no>
Rules: <inherited and standing rules per the Rules bullet under Shared rules in carpaccio.md>
Work folder: <expand Work folders in carpaccio.md>
```

## Coordinate

1. Record each Chef's received phase and answer its questions from the agreed requirements. If you need Pascal's answer, show `❓ question Chef <b>` or the matching trigger label. Relay the answer; otherwise decide, split the batch or replace its Chef. Done when each escalation has an owner and next action
2. On `🍽️ Batch ready`, check the shared Report and ask Pascal for review only under the [merge review trigger](../carpaccio.md#when-the-head-chef-asks-pascal). Keep other batches running. Relay `🔀 Merge`, `⏳ Rework`, `🍽️ Hold` or `⏹️ Drop` as Pascal decides. A Hold remains live; show `❓ held batch <b>` only when nothing else progresses. A Drop is a scope cut and must come from Pascal. Done when each ready batch has a decision
3. Record `🔀 Batch merging` and `Batch merged` as notices, without incrementing the counter. On `⛳ Batch delivered` or `⏹️ Batch stopped`, record the final outcome and update the title. Start newly eligible batches. On merge failure, retain the landed PRs while the Chef has its Cook fix the cause. Done when the registry and title match received outcomes
4. If a ready batch loses readiness, withdraw its review item, post one line explaining the withdrawal and keep any other open items. When Pascal changes batch choices or asks for fast track, relay the new choices to the Chef. Done when each affected Chef has the current decision
5. Ask Pascal before cutting a card, a batch or a required deliverable. Relay `⏹️ Cut <card>` or `⏹️ Drop` and remove a cut batch from the count only after its Chef reports ⏹️. Done when the reduced scope and titles match the received outcomes

## Replace a Chef

When a Chef cannot continue, inspect the old thread and PRs before retrying or relaunching anything. Keep the batch slot and the Cooks' worktrees.

1. Interrupt the old Chef, cancel queued turns and rename it ⏹️. Read its cards, branch heads, PR URLs, review rounds and decisions. Done when the old thread cannot act on its slot
2. Launch a new Chef in the same project and slot at ⏳ with that state, then update the registry's threadId. The new Chef links and watches the PRs and tells every Cook its new threadId using the replacement message in Messages. Done when each Cook reports to the new Chef
3. Archive the old thread. Ignore a late report from it. Done when the sidebar has one Chef for the slot

## Split a batch

Split card groups without adding or cutting cards or required deliverables. Mark the old Chef as replaced, interrupt and archive it at ⏹️, preserve its Cooks' worktrees and branch heads, and remove its batch slot from the count. Register the successor batches and assign every card and Cook to exactly one successor. A Cook whose cards move to another owner closes at ⏹️. Launch successors under the one live batch per repository rule. The first Chef adopts its assigned live Cooks with the replacement message. Cooks assigned to a queued successor close at ⏹️ with their work preserved; that successor relaunches them in the same worktrees. Update the Head Chef's denominator when the successor slots are registered. Ask Pascal only if total scope changes. Done when the old Chef is ⏹️ and archived, each card has one successor, and the count includes only the successor batches.

## Status, added work and Stop

- For status, list threads in each project with `titleContains: <id4>` and read the PRs. Give one line per batch with Chef, phase, PRs and what it awaits. Recompute your own title before ending the turn. Done when every batch is covered
- For new work, repeat Align, add batches and update the title. Reopen and pin your thread first if the run had ended. Done when the registry includes the agreed additions
- On Pascal's Stop, clear open review items, launch no further batch and send `⏹️ Stop` to every active Chef. Mark unlaunched batches stopped in the registry. Wait for each launched Chef, including any merge already running, then Close. Done when every batch has an outcome

## Close

Begin once each launched Chef is final and settled, and every queued batch ran, was cut or stopped. Show 🟢 during your own closing work.

1. If `[head-chef].retro`, follow [shared Retros](../carpaccio.md#retros). Done when each has issue links or a recorded no-findings result
2. Confirm each launched Chef is settled using 🧰 t3-runtime and finish shared Work folders cleanup. Compute ⛳ or ⏹️ from the final outcomes, send Pascal `<status> <done>/<batches> batches done` with the shared Report, then settle. Done when every batch has an outcome, Pascal has the report and your settle returns `settlesWhenTurnEnds: true`

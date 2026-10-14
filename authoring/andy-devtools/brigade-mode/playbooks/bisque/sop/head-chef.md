# head-chef

You run the use case for the user and never edit code. Run the section the moment calls for. Keep the run's registry in your conversation: for each batch, its number, name, repository, T3 projectId, Chef threadId, the batches it depends on, and its outcome.

## Start

1. **Align.** Agree on the plan with the user, then split it into batches along the plan's own grouping: a milestone, an epic, a sprint, or a label. A batch targets one repository, so work that spans repositories becomes one batch per repository, in dependency order. Give each batch its short name from the plan. Ask the user which batches they want to validate before their merge. Done when the user agreed on the batches, their order, and the batches they validate
2. **Name and pin yourself.** Rename yourself `Head Chef <id4> · 0/<batches> · <subject>` with `t3_thread_update` action `rename`, then pin yourself with `t3_thread_organize` action `pin`. The first number counts the batches done: merged, or done without a PR. Done when your title matches and you are pinned

## Launch a batch

Run the batches in series: launch a batch once the batch before it sent its outcome, and once each batch it depends on is merged. Run batches side by side only when the user asks, with at most `max-parallel` Chefs at work at once. A batch whose dependency ended without merging waits for the user.

1. **Pick the model** for the Chef as `chef-launch` step 2 says, with the `[chef]` row. Done when the selection is supported
2. **Find the project.** With `t3_project_list`, find the T3 project whose `workspaceRoot` is the batch's repository. When none exists, create it with `t3_project_create`, and when T3 refuses, ask the user to add the repository to T3. Done when its projectId is in the registry
3. **Launch.** Call `t3_thread_launch` in that project with `workspaceStrategy` `root`, the `modelSelection` from step 1, the Chef's title from Roles in `bisque.md`, and the message below. Leave out a line that has nothing to carry. Done when `t3_thread_read` shows the thread started and its threadId is in the registry

```text
$brigade-mode ; bisque ; chef-run
Read playbooks/bisque/sop/chef-run.md in the brigade-mode skill and follow it.
Role: 🧑‍🍳 Chef <b> <id4>. Report only to the Head Chef, threadId <your full threadId>, with t3_thread_send.
Batch: <b>, <batch name>, repository <absolute path of its clone>
Plan: <this batch's cards, and what the user agreed for them>
PRs: <URLs of the PRs you opened for this batch during alignment>
Fast track: yes
```

## Answer the chain

When a Chef sends a question, answer it when the plan or your conversation with the user settles it. Otherwise ask the user, naming the batch, then relay the answer. Done when the Chef has its answer

## Give the green light

The run has one merge slot. A batch is cleared when its confidence reaches `merge-confidence` and the user did not ask to validate it, or when the user reviewed it and said merge.

1. **Clear.** When a Chef sends 🚦 for a batch that is not cleared, send the user the Chef's report and questions, and align until the user says merge or don't merge. Relay "don't merge" to the Chef. Done when the batch is cleared, or its Chef has "don't merge"
2. **Grant.** Reply 🟢 to a cleared batch only while the slot is free, and record the batch as the slot's owner first. Each time the slot frees or a batch becomes cleared, check the waiting batches in the order they sent 🚦. Done when each cleared batch holds the slot or waits for it in order

## Follow each batch

- **The slot owner reports "merged":** free the slot, rename yourself with the new count of batches done, and launch each batch this unblocks
- **The slot owner reports "merge failed":** free the slot, record the PRs that landed, and ask the user whether the batch retries or closes as not merged. Relay the decision to its Chef
- **A Chef sends its outcome:** record it. "Done without a PR" counts as done, so rename yourself. Any outcome lets the next batch in series start, and each batch that depends on an unmerged one waits for the user

Done when the registry holds each reported result.

## Report status

When the user asks for status, list the threads of each batch's project with `t3_thread_list` and `titleContains` set to `<id4>`, and read each batch's PRs. Reply with one line per batch: its Chef, the step in the Chef's title, its PRs, and what it waits for. Done when every batch has its line

## Add work

When the user adds work during the run, align on it as in Start step 1, queue its batches after the others, and rename yourself with the new batch count. Done when the new batches are queued

## Stop the run

When the user stops the run, launch no batch and grant no slot. Send "🛑 Stop" to each Chef still at work, then wait for each one's outcome, which follows any merge already running. Done when every Chef at work has reported, then run Close

## Close

Run this section once every launched batch has its outcome from its Chef, and every queued batch is launched or dropped by the user.

1. **Report.** Send the user each batch with its outcome, its PR links, and the issues filed, the out-of-scope gaps not filed, every change made outside the agreed plan and why, each step skipped or replaced and why, and what no thread could confirm. Done when the report covers every batch
2. **Retros.** If `[head-chef]` enables `retro`, run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global, each limited to `retro-max-issues`. Done when each retro has issue links or a recorded no-findings result
3. **Settle.** Confirm each Chef in the registry with 🧰 t3-runtime, send "⛳ <done>/<batches> batches done. [summary]", then settle yourself, which unpins you. Done when the user has the outcome and you are settled

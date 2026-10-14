# head-chef

You run the use case for the user and never edit code. Run the section the moment calls for.

## Start

1. **Align.** Agree on the plan with the user, then split it into batches along the plan's own grouping: a milestone, an epic, a sprint, or a label. A batch targets one repository, so work that spans repositories becomes one batch per repository, in dependency order. Give each batch its short name from the plan. Ask the user which batches they want to validate before their merge. Done when the user agreed on the batches, their order, and the batches they validate
2. **Name and pin yourself.** Rename yourself `Head Chef <id4> · 0/<batches> · <subject>` with `t3_thread_update` action `rename`, then pin yourself with `t3_thread_organize` action `pin`. Done when your title matches and you are pinned

## Launch a batch

Run the batches in series: launch a batch once the batch before it, and each batch it depends on, has merged. Run batches side by side only when the user asks, with at most `max-parallel` Chefs at work at once.

1. **Pick the model** for the Chef as `chef-launch` step 2 says, with the `[chef]` row. Done when the selection is supported
2. **Find the project.** With `t3_project_list`, find the T3 project whose `workspaceRoot` is the batch's repository. When none exists, use the `projects` project. Done when you have its projectId
3. **Launch.** Call `t3_thread_launch` in that project with `workspaceStrategy` `root`, the Chef's title from Roles in `bisque.md`, and the message below. Leave out a line that has nothing to carry. Keep the returned threadId. After an error or a lost response, find the thread with `t3_thread_list` before retrying. Done when `t3_thread_read` shows the thread started

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

A Chef sends 🚦 with its PRs and its confidence to merge. Reply 🟢 at once when its confidence reaches `merge-confidence`, the user did not ask to validate this batch, and no other batch is merging. Otherwise:

- **The user validates this batch, or the confidence is below `merge-confidence`:** send the user the Chef's report and questions, align, and reply 🟢 when the user says merge, or relay "don't merge"
- **Another batch is merging:** reply 🟢 once its Chef reports it merged

Done when the Chef has 🟢 or "don't merge". After a Chef reports its batch merged, rename yourself with the new merged count, then launch the next batch.

## Report status

When the user asks for status, list the run's threads with `t3_thread_list` and `titleContains` set to `<id4>`, and read each batch's PRs. Reply with one line per batch: its Chef, the step in the Chef's title, its PRs, and what it waits for. Done when every batch has its line

## Add work

When the user adds work during the run, align on it as in Start step 1, queue its batches after the others, and rename yourself with the new batch count. Done when the new batches are queued

## Close

Run this section once every batch is merged, or the user stops the run.

1. **Report.** Send the user each batch with its PR links and the issues filed, the out-of-scope gaps not filed, every change made outside the agreed plan and why, each step skipped or replaced and why, and what no thread could confirm. Done when the report covers every batch
2. **Retros.** If `[head-chef]` enables `retro`, run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global, each limited to `retro-max-issues`. Done when each retro has issue links or a recorded no-findings result
3. **Settle.** Confirm with 🧰 t3-runtime that every thread of the run is settled, or name each one still open and why. Send "⛳ <merged>/<batches> batches merged. [summary]", then settle yourself, which unpins you. Done when the user has the outcome and you are settled

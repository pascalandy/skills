---
name: "t3-runtime"
description: "Use inside T3 Code when a step delegates work, launches or messages a thread, links or watches a pull request, schedules work, settles a thread, or reads thread history through the `t3-code` tools."
kind: "dev"
role: "helper"
---

# T3 runtime

T3 Code adds its orchestration rules to every thread it runs, and each `t3-code` tool describes its own contract. Both stay the source for how a tool works. This skill adds what they leave open: which mechanism a step uses, which thread owns a watch or a schedule, when a thread is done, and traps found in use. To drive T3 from a shell outside a thread, use `t3cli` instead.

You are inside T3 when `orchestrator_capabilities` returns a `parentThreadId`. When the `t3-code` tools are not listed yet, make that one call before concluding they are absent.

## Pick the mechanism

| Word | Mechanism | Use for |
|---|---|---|
| Subagent | The harness's own tool, such as Claude Code's Agent tool or Codex subagents | Work on your provider, with a model that tool supports, that T3 need not show |
| Delegate | `delegate_task`, a child of this thread | Other child work: another provider or model, or a route that wants T3 to show and track the child |
| Thread | `t3_thread_launch` or `create_threads`, a conversation in the sidebar | Only when the user asks for one, or the invoked route names the threads it launches |

A worker that needs its own worktree stays a delegate. Its brief names the worktree path, and it aims each command there with `git -C`.

- A delegate shares its parent's checkout, since `delegate_task` takes no workspace. It cannot watch a pull request: its parent thread owns the watch. The sidebar hides it, and the user opens it from the parent's Lineage panel
- A thread keeps no link to the thread that launched it, and nothing tells the launcher when it finishes. Its first message names who it reports to, and it reports with `t3_thread_send`, which reaches any thread in the environment, in any project

## Name threads

The sidebar shows each title on one line and cuts the end. Put what identifies the thread first. The title is the only status an agent can set, since T3 has no labels, tags, or status fields.

## Pull requests

- Link each pull request with `link_pull_request`. `t3_thread_update` replaces the linked pull request, so linking A then B through it loses A
- The thread that decides the merge holds the watch. Comments from the user's own `gh` account never wake it, so comments the agents post through that account stay silent. A watch ends after 10 wakes caused only by comments
- When a pull request has nothing to monitor, oem's rule replaces the watch: one status pass, then `unwatch_pull_request`

## Schedules

Record each schedule's id with the condition that ends it. Delete the schedule when that condition holds, and disable it with `update_scheduled_task` `enabled: false` on a pause. Work that runs once gets no schedule.

## Done and settled

T3 settles a thread on its own only when every pull request linked to it is merged or closed, or after its idle limit, three days by default. It never settles a pinned thread, and never settles one because a turn ended. So each thread settles itself:

1. **Check.** The thread owes no review, fix, reply, or report. Done when nothing is owed
2. **Settle.** Call `t3_thread_organize` action `settle` without `threadId`. It takes effect when your turn ends. Done when the call returns `settlesWhenTurnEnds: true`
3. **Confirm.** A parent lists its threads with `t3_thread_list` `settled: true` before it reports its own completion. To settle another thread, wait until `t3_thread_wait` reports its turn ended, since T3 refuses a thread with active work. Done when every thread it launched is settled or named with the reason it stays open

Any message reactivates a settled thread. Settling clears its pin and ends its watches.

## History and evidence

- List threads with `t3_thread_list`, newest first, to cover a time window. `t3_thread_search` returns a bounded sample and can miss threads
- Read tool calls with `t3_thread_read` `view: "activity"`; the default view holds messages only
- `t3_worktree_status` reports the calling thread's binding only. Audit worktrees with `git worktree list`
- `device_open` returns the agent-device CLI that drives the device; `device_screenshot` only captures
- Parallel delegates that share a browser each open their own tab with `preview_open` `reuseExistingTab: false`, then pass its `tabId` on every call

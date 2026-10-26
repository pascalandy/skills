---
name: "t3-runtime"
description: "Use inside T3 Code before orchestration, pull request tracking, scheduling, or thread-history work: delegating, launching or messaging a thread, linking or watching a pull request, scheduling, settling a thread, or reading thread history through the `t3-code` tools."
kind: "general"
role: "helper"
---

# T3 runtime

T3 Code adds its orchestration rules to every thread it runs, and each `t3-code` tool describes its own contract. Both stay the source for how a tool works. This skill holds what they leave open: which mechanism a step uses, which thread owns a watch or a schedule, when a thread is done, and the facts a plan needs before it loads a tool's description. To drive T3 from a shell outside a thread, use `t3cli` instead.

## Pick the mechanism

| Word | Mechanism | Use for |
|---|---|---|
| Subagent | The harness's own tool, such as Claude Code's Agent tool or Codex subagents | Child work T3's rules give to the native tool |
| Delegate | `delegate_task`, a child of this thread | Other child work, and child work a route wants T3 to show and track |
| Thread | `t3_thread_launch` or `create_threads`, a conversation in the sidebar | Only when the user asks for one, or the invoked route names the threads it launches |

A worker that needs its own worktree stays a delegate. Its brief names the worktree path, and it aims each command there with `git -C`.

A plan needs these facts before it picks a mechanism:

- A delegate shares its parent's checkout unless the call sets `isolation: "worktree"`, which gives it a separate checkout of the parent's last local commit, without uncommitted edits. It cannot watch a pull request, so a thread owns each watch. The sidebar hides it, and the user opens it from the parent's Lineage panel
- A launched thread has no parent lineage and no automatic completion notice. It hears only its first message
- `t3_thread_send` refuses a target whose permission modes are broader than the sender's. After the user widens your modes, a thread launched before cannot send you its report: read it with `t3_thread_read` instead of waiting. Launch a replacement only after you reconcile the first thread's work

## Launch a thread

Its first message carries the contract it needs, since it sees none of your conversation:

- The thread it reports to, with that threadId, and the tool to report with: `t3_thread_send`
- What done means for it, and the instruction to load 🧰 t3-runtime and settle itself once done

Keep each threadId a launch returns. Your own completion depends on them.

## Name threads

The sidebar shows each title on one line and cuts the end. Put what identifies the thread first. Use the title for a custom progress label, since T3 computes the runtime status and offers no labels or tags.

## Pull requests

- Link each pull request with `link_pull_request`. A `t3_thread_update` link replaces the pull request linked before it
- One thread tracks each pull request and holds its watch: the one the route names, or else the one that owns the merge. Comments posted by the account T3 reads the host with do not wake it, so an agent that comments through that account also reports to the tracking thread. A watch stops after 10 consecutive wakes caused only by comments
- When a pull request has nothing to monitor, oem's rule replaces the watch

## Schedules

The thread responsible for the recurring objective owns the schedule: it records the schedule's id with the condition that ends it, and pauses it during a pause. Before it settles, it deletes the schedule, or records the thread that takes it over. Work that runs once gets no schedule, unless it must start at a set time: then create one `fixed_time` schedule on that weekday and check that its `nextRunAt`, given in UTC, is the requested instant; if it is not, delete it, confirm with `list_scheduled_tasks` and report that the instant cannot be scheduled. Its run deletes it as its first step and confirms with `list_scheduled_tasks` before the work starts; a failed deletion stops the run.

A delegate can bind a schedule to its own thread with `bindToCurrentThread: true`. Its ticks run there without waking its parent; the delegate must send the parent an explicit message when the parent needs to act.

## Done and settled

T3 can settle a thread when its turn ends, even with an open pull request linked through `link_pull_request`. A settled thread can lose its background jobs. When you end a turn to wait, rely on a delivered message to resume, with no background job still needed. Each thread still settles itself:

1. **Check.** The thread owes no review, fix, reply, or report, and holds no schedule. Done when nothing is owed
2. **Settle.** Call `t3_thread_organize` action `settle` on yourself. Done when the call returns `settlesWhenTurnEnds: true`
3. **Confirm.** Before a parent reports its own completion, it checks each threadId its launches returned, with `t3_thread_list` in that thread's project. To settle a finished thread that did not settle itself, wait until `t3_thread_wait` reports its turn ended, since T3 refuses a thread with active work. Done when each launched thread is settled or named with what it still owes

Any message reactivates a settled thread. Settling clears its pin and ends its watches.

## History

To cover every thread in a time window, list them with `t3_thread_list`, since `t3_thread_search` can miss threads. To audit worktrees, use `git worktree list`, since `t3_worktree_status` reports only the calling thread.

`t3_thread_read` pages forward from the oldest item, or from the item after `afterPosition`, so `limit: 1` alone returns item 0. Positions count every timeline item, activity included, but in `view: "messages"` `limit` counts messages, not items. To find a recent message that starts with a known prefix, read windows of k items from the newest, with `view: "messages"` and a small `maxCharsPerItem`: pass `afterPosition: itemCount - j*k - 1` and `limit: k` for j = 1, 2, … until the message appears, and omit `afterPosition` once that value falls below 0. A window of k items holds at most k messages, so `limit: k` returns all of that window's messages first; from j = 2 it can then return positions at `itemCount - (j-1)*k` or later, which you already read and skip. `t3_thread_list` and every `t3_thread_read` result give `itemCount`.

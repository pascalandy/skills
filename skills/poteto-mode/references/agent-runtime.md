# Run pstack inside T3 Code

Read this reference before a workflow delegates, resumes, reads history, or authors a skill. pstack runs inside T3 Code, and two files split its runtime rules:

- The **t3-runtime** skill owns how work runs in T3: which mechanism runs a worker (subagent, delegate, or thread), pull request watches, schedules, settling, and thread history. Load it before the first delegation, watch, schedule, or history read, and use the tool it picks
- This file owns what holds whatever the mechanism: what a delegation contains, what counts as independent verification, how work continues and resumes, and the cleanup before a commit

A worker is any agent you start: a subagent, a delegate, or a thread. Take each worker's model and reasoning level from the active route's settings, such as a brigade-mode `config.toml`. Without route settings, run it at the parent's reasoning level.

## Load skills and configuration

Resolve a named skill in the session catalog and read its SKILL.md and the references the current step needs. A slash command in a playbook is shorthand for that instruction, not a required executable. If the skill is absent, use the stated functional fallback or report the missing capability.

Keep edits in the repository's source of truth, one canonical copy, and ship them through the workflow its `AGENTS.md` describes.

## Delegate

Brief each worker with a bounded task, input paths, permitted writes, required tools, the evidence to return, and a completion criterion. A worker sees only its brief, so include the instructions and excerpts it needs, or file pointers it can open. Prefer asynchronous workers for independent tasks. Give reviewers the tools that inspect evidence, restrict them to reads where the mechanism allows it, and say so in the brief. Give workers that share a checkout disjoint files. Leave a checkout unchanged while any reviewer reads it. By default, give each reviewer `isolation: worktree` at a committed snapshot, since isolation copies no uncommitted edit. Share your checkout only when the review must see uncommitted changes, and apply fixes once the last reviewer returns. Refresh the base before each review round, as `playbooks/opening-a-pr.md` says. Check concurrency and nesting limits before fan-out, and flatten nested work under the parent when needed.

**Fresh workers by default.** Give new work to a fresh worker with a consolidated brief: the original brief, every later directive, and the prior worker's report and branch. This holds for a fix round, a follow-up, a retry, and the next queue item. Message, resume, or queue a follow-up on an existing worker only when the new work needs state that lives in it and is costly to move: its checkout, its uncommitted changes, or a process it still runs, such as a dev server or a watch. A stop or hold order is not reuse. A role such as a PR owner outlives its worker: once that worker returns, a fresh worker takes the role's next round and re-arms the watch as t3-runtime describes. A resumed worker can silently drop earlier directives, so never accept its "done" without a consolidated brief behind it.

You own every worker's result. Inspect the actual diff and evidence, then write your own summary. A second opinion needs a separate reviewer, on another model family when one is available. A second pass by the same agent is self-review, not independent verification: when independence is a shipping gate, leave it unmet until another agent or a person verifies. When delegation is unavailable or disallowed, do the work sequentially and name the lost parallelism.

## Continue and resume

Record the objective, stop predicate, current artifact or head SHA, next action, and outstanding worker IDs in a durable task checkpoint. A checkpoint records work; it does not schedule work.

Wake on what T3 delivers to the agent: a delegate's completion notice, a thread's pull request watch, or a schedule for timed checks, as t3-runtime describes. Without one, keep checking while the session is active, checkpoint the exact next check before the turn ends, and report that unattended continuation is unavailable.

After a restart, check each worker's actual status, then reconcile the checkpoint with git, review state, and durable results before resuming or respawning. Assume neither that a worker died nor that it survived. The bundled `orch` CLI stores coordination records; it does not spawn agents or schedule wakeups. Pass its `--store` option or `ORCH_STORE` an explicit task-scoped path when no store is provided.

## Read history and discover evidence tools

Read thread history as t3-runtime describes, only this project's threads in the task's time window. Never search unrelated projects to fill a gap. A summary does not prove which tools an agent ran, so read the actual tool events. When history is unavailable, name the missing evidence and reconstruct only from the conversation, the checkpoint, git, and artifacts.

Find evidence sources, such as MCP servers and installed CLIs, in the active tool catalog. Record a missing category instead of inventing a tool.

## Author, clean up, and verify

For skill authoring, resolve `writing-for-agents` from the active catalog and read its `SKILL.md` plus the references needed for the current step. When it is absent from the catalog, locate its managed repository source through repository policy and read that source directly. If neither route resolves it, report the missing dependency and leave the authoring step unmet. Do not substitute another skill-authoring standard. Preserve each consumer workflow's domain inputs, output contract, and domain-specific verification.

Before commit, inspect the diff for redundant abstractions, duplicated checks, dead code, debug leftovers, and unrelated churn. Use project lint and formatting commands. Apply unslop to prose.

For CLI behavior, drive the actual command through shell or PTY and inspect its output, exit status, and resulting state. For browser behavior, use the available browser driver and inspect the visible result. For native applications, use the installed accessibility, simulator, or application-control tool. Prefer a project verification skill that records launch instructions and observable outcomes. Screenshots, live interaction, and real state prove behavior; a build alone does not. If the required driver or environment is absent, report the unverified behavior and retain that verification gate.

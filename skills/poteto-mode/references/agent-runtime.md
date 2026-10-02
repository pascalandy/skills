# Run pstack in the active agent tool

Read this reference before a workflow uses delegation, model selection, history, scheduling, application control, or skill installation. Resolve capabilities from the active session's tools and installed CLI help. Product names alone do not establish what this session can do.

## Load skills and configuration

Resolve a named skill in the session catalog and read its SKILL.md and the references needed for the current step. A slash command in a playbook is shorthand for that instruction, not a required executable. If the skill is absent, use the stated functional fallback or report the missing capability.

Keep edits in the repository's source of truth. In a managed dotfiles repository, edit the managed source and use its apply workflow. For a new project skill, use the project's existing skill directory. Otherwise `.agents/skills/<name>/SKILL.md` is a shared source location; confirm discovery in each target tool or configure its supported path. Explicitly reading that file works when automatic discovery does not. Keep one canonical copy and use the project's existing distribution mechanism.

## Delegate by capability

Use the native delegation tool when exposed. Supply a bounded task, input paths, permitted writes, required tools, evidence to return, and a completion criterion. Include instructions and excerpts when the worker cannot access the source paths. Use a registered role only when its definition is available; otherwise give a general worker the role's explicit brief.

Discover the actual controls for launch, status, messages, wait, resume, and cancellation. Prefer background execution for independent work when supported. Restrict reviewers to read operations while retaining tools they need for evidence. Do not infer MCP access from a permission mode's name. An interrupted or resumed worker must receive a consolidated current brief.

Check concurrency and nesting limits before fan-out. Flatten nested work under the parent when needed. If native delegation is absent, an installed headless CLI or SDK can run separate agent sessions, provided their process status, outputs, permissions, and termination can be supervised. For Codex or Claude Code, use the **headless** skill's launcher. For other CLIs, verify flags with local help. Otherwise, or when the harness or user disallows delegation, do the useful work sequentially and name the loss of parallelism. A second pass by the same agent is self-review, not independent verification. If independence is a shipping requirement, leave that gate unmet until another agent or person verifies it.

Assign disjoint files when workers share a checkout. Use separate workspaces only when repository policy permits them. Remote execution is optional and requires an actual configured runner, accessible code, credentials, and artifact transport. A worker label does not allocate a VM. Confirm the worker's environment before relying on isolation.

## Continue and resume

Record the objective, stop predicate, current artifact or head SHA, next action, and outstanding worker IDs in a durable task checkpoint. Use a native goal facility when exposed, within the user's authorized task. A checkpoint records work; it does not schedule work.

Prefer a supported event watcher that returns a result to the agent. Use a native recurring task only when available and its lifetime is understood. Without automatic continuation, keep the supervising session active, wait through the supported process tool, inspect the result, act, and rearm. A background shell watcher alone cannot start another agent turn. Continuing after the session or machine stops requires a configured external scheduler and agent runner. State that limitation rather than promising unattended progress.

After a restart, inspect actual worker and process status. Reconcile the checkpoint with git, review state, and durable results before resuming or respawning. Do not assume local workers died or remote workers survived. The bundled `orch` CLI stores coordination records; it does not spawn agents or schedule wakeups. Pass its supported `--store` option or `ORCH_STORE` an explicit task-scoped path when no store is provided.

## Read history and discover evidence tools

Use the session's authorized history API or an identified workspace-scoped transcript/export. Confirm the workspace, time range, session IDs, and format before searching. Parse real message and tool events, including branches if the format has them. Do not assume every JSONL line is a chat message. Never search unrelated projects to compensate for missing history.

If history is unavailable, say which evidence is missing and reconstruct only from the current conversation, task checkpoint, git, and available artifacts. A summary does not prove which tools an agent ran. Transcript modification time does not prove worker liveness.

Discover MCP servers and connectors through the active tool catalog or supported discovery interface. Use installed CLIs where appropriate. Record unavailable evidence categories instead of inventing tools or universal configuration directories.

## Author, clean up, and verify

For skill authoring, resolve `writing-for-agents` from the active catalog and read its `SKILL.md` plus the references needed for the current step. When it is absent from the catalog, locate its managed repository source through repository policy and read that source directly. If neither route resolves it, report the missing dependency and leave the authoring step unmet. Do not substitute another skill-authoring standard. Preserve each consumer workflow's domain inputs, output contract, and domain-specific verification.

Before commit, inspect the diff for redundant abstractions, duplicated checks, dead code, debug leftovers, and unrelated churn. Use project lint and formatting commands. Apply unslop to prose. This cleanup does not require a plugin.

For CLI behavior, drive the actual command through shell or PTY and inspect its output, exit status, and resulting state. For browser behavior, use the available browser driver and inspect the visible result. For native applications, use the installed accessibility, simulator, or application-control tool. Prefer a project verification skill that records launch instructions and observable outcomes. Screenshots, live interaction, and real state prove behavior; a build alone does not. If the required driver or environment is absent, report the unverified behavior and retain that verification gate.

## Choose an adapter

These are documented entry points, not a promise that every installation exposes them. Recheck the active tool schema and installed version before using them.

| Tool | Delegation and integration | Skills and history |
| --- | --- | --- |
| Codex | Native subagent launch, follow-up, and wait controls where enabled; model and permission configuration depend on the client | Session skill catalog and configured skills; use exposed history or supported session resume/export facilities |
| Claude Code | Agent tool with custom or built-in roles; background and scheduling facilities where supported | `.claude/skills`; session resume and transcript facilities; recurring tasks have their own lifetime and permission constraints |
| Pi | Core has no built-in subagents; use an installed extension or separate sessions through print/JSON, RPC, or SDK with supervision | `.pi/skills` and configured/shared skill paths; `/session`, `/export`, and working-directory-scoped JSONL sessions |
| OpenCode | Primary agents and subagents with configured permissions and provider/model IDs; use the exposed task tool or supported server/SDK | `.opencode/skills` and compatible/configured skill paths; use supported session export or API |

Official references: [Codex subagents](https://developers.openai.com/codex/multi-agent), [Codex skills](https://developers.openai.com/codex/skills), [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks), [Pi coding agent](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent), [OpenCode agents](https://opencode.ai/docs/agents/). Consulted 2026-09-09. Local availability takes precedence over examples.

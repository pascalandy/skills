# Local adaptations

These are the explicit differences from the imported Matt procedures. Keep upstream wording in the imported files. Change integration rules here instead of editing those bodies.

## Planning boundary

Matt-mode prepares implementation. Permitted work includes reading the codebase, researching constraints, discussing interfaces and testing strategy, and writing authorized specs, plans, domain documentation, architecture reports, and GitHub tickets. Code excerpts inside planning documents express decisions; they are not application changes.

Do not write or modify application code, runnable prototypes, implementation tests, or deployment configuration. Do not implement through subagents, merge, or deploy. Delegate only bounded research and inspection while retaining the same planning scope.

When an upstream procedure calls for execution, leave the affected decision unresolved and identify the missing evidence or prerequisite. Its execution instructions do not expand this mode's authority. Resolve upstream `prototype` calls as a handoff to `poteto-mode`, not as a local procedure to run.

## Scope and authorization

Carry the caller's requested result and authority through every procedure. A discussion-only request stays in conversation, including proposed terminology. An explicit `grill-with-docs` request authorizes its glossary and qualifying ADR work. Reading a repository alone does not authorize documentation. A spec, map, or ticket request authorizes that artifact within the requested scope.

Honor decisions and approvals already given. Ask only for unresolved choices. For `to-spec`, retain the upstream check of proposed test seams when they need a decision, without reopening agreed seams or restarting the interview. Mark unresolved decisions as blockers rather than declaring a draft ready for an agent. For `to-tickets`, an approved breakdown or explicit authorization to choose granularity satisfies the review step.

Publish planning artifacts to GitHub or another tracker when requested. Except for the `to-tickets` default below, a procedure name alone does not authorize external publication. An implementation request is a handoff to `poteto-mode`; it does not convert Matt-mode into an execution workflow.

## Workspace and tracker

For `to-tickets`, honor an explicit destination; otherwise, default to GitHub using the repository selected by `gh`, then the sole GitHub remote. Ask only if the destination is ambiguous. An approved breakdown authorizes publication without another confirmation. If no GitHub destination exists, `gh` needs setup, or publication fails, save one full ticket per file using the shared export conventions of andy-mode's `idea` route, named `ticket-01-<slug>.md` within the dated effort folder. Return issue links or local paths, report publication failures, and ask the user to configure `gh` when needed. For local export, read `references/export-artifacts.md` from the active `pa-doc-update` skill directory, as the `idea` route does.

Read [workspace conventions](workspace.md) before the first artifact write or when resuming a map. Interpret upstream `/setup-matt-pocock-skills` references as resolving those conventions. No setup command or installation is required to start. Prefer the supplied destination and existing configuration. The local fallback is a tracker adapter, not a different specification format.

Use the complete upstream spec and ticket templates. Record agreed implementation and testing decisions using the supplied evidence. Inspect existing code and primary sources to resolve factual questions. Keep proposed technical choices visibly distinct from decisions the user has made.

## Runtime and dependencies

Resolve upstream named Skill calls through the Matt-mode route table or its shared skills. When another workflow needs just domain modeling or codebase design, it reads this contract and that procedure directly. It retains its original task and authority.

Use the active harness's available research and delegation capabilities. Keep delegated work read-only except for the authorized findings document. Use actual context limits rather than upstream's fixed session-size estimates. If delegation is unavailable, investigate facts directly and report the limitation. Human decisions still require the human's answers.

## Planning reports

An architecture report presents proposals, not a working application. Follow the project's documentation and visual conventions for such reports. Preserve upstream's candidate analysis and comparisons without executing the proposed refactors.

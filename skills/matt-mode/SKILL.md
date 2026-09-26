---
name: "matt-mode"
description: "Use when the user invokes matt-mode to clarify requirements, discuss design, map decisions, or prepare implementation through specs and tickets."
disable-model-invocation: true
---

# Matt mode

Matt-mode prepares implementation. It produces planning artifacts and implementation-ready context; it does not implement software, including through subagents.

Use Matt Pocock's procedures under their original names. Read [local adaptations](references/local-adaptations.md), then the procedure for the requested result. Resolve bundled paths relative to this file. Load supporting files only when the selected procedure needs them.

The procedure bodies and their supporting files are imported from a pinned upstream revision. Follow their full instructions within the local adaptations and the caller's scope. Keep routing follow-ups for the same effort until the user changes task or mode. Stop at the requested result.

## Choose a procedure

Recognize spaced names such as "to spec", "to tickets", "grill with docs", and "domain modeling" as their hyphenated route names. A caller can resolve this package and read one named procedure without changing its own workflow or activating every route.

| Name | Use when | Read |
| --- | --- | --- |
| `grill-me` | Sharpen an idea through conversation | [grill-me](playbooks/grill-me/grill-me.md) |
| `grill-with-docs` | Interview while recording resolved domain terms and qualifying ADRs | [grill-with-docs](playbooks/grill-with-docs/grill-with-docs.md) |
| `domain-modeling` | Define or challenge domain vocabulary and relationships | [domain-modeling](playbooks/domain-modeling/domain-modeling.md) |
| `codebase-design` | Design a module's interface, depth, or seam | [codebase-design](playbooks/codebase-design/codebase-design.md) |
| `improve-codebase-architecture` | Find and compare architectural improvements in existing code | [improve-codebase-architecture](playbooks/improve-codebase-architecture/improve-codebase-architecture.md) |
| `wayfinder` | Chart or resume decisions across sessions while the route is uncertain | [wayfinder](playbooks/wayfinder/wayfinder.md) |
| `to-spec` | Synthesize existing context into a spec, including design and testing decisions | [to-spec](playbooks/to-spec/to-spec.md) |
| `to-tickets` | Break defined work into verifiable deliveries and blocking edges | [to-tickets](playbooks/to-tickets/to-tickets.md) |

When upstream asks to call a Skill by one of these names, read that procedure here. A slash command is an instruction pointer, not a required executable or separate installed skill.

## Shared skills

Resolve `research`, `grilling`, and `writing-for-agents` from the active catalog or the sibling skill directories in a source or flattened installation. Read each skill's `SKILL.md` before using it. Their canonical upstream bodies live in those packages, not here.

- `research` gathers primary-source evidence, including when the user says `matt-mode ; research`
- `grilling` supplies the interview used by `grill-me`, `grill-with-docs`, Wayfinder, and architecture review
- `writing-for-agents` supplies the writing discipline when producing a spec, tickets, a map, or another artifact an agent will consume

If a required dependency is unavailable, name it and the affected step. Continue independent work without claiming the missing procedure ran.

## Choose the order

Small, obvious changes can go directly to the execution workflow. Use `grill-me` for discussion, or `grill-with-docs` when documentation is requested. Domain modeling and codebase design apply within relevant work, not as compulsory preliminary stages.

Research supplies missing facts through source inspection and primary documentation. Wayfinder manages uncertainty that exceeds one session; defined work does not need a map just because it is large.

For a substantial planning effort, the usual sequence is discussion, then `to-spec`, then `to-tickets`. An architecture review supplies candidates that enter this sequence after the user selects one. Skip completed stages. A `to-spec` request synthesizes the available context without restarting the interview.

Finish with the requested spec, plan, tickets, or readiness assessment. When implementation or a runnable prototype is requested, direct the user to `poteto-mode` with the existing context. Read [the PStack handoff](references/pstack-handoff.md) when preparing that context; completion of planning does not start execution.

## Maintenance

Read [lineage and updating](references/lineage.md) to refresh upstream content. Use [acceptance cases](references/acceptance-cases.md) when changing routing or local adaptations. Neither is needed during ordinary work.

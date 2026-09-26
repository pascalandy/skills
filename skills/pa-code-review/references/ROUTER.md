# PA Code Review Router

Use this router to decide which lenses to inspect and whether each lens should be handled inline or by an optional delegated investigator.

The parent `pa-code-review` skill always owns the workflow, synthesis, and final readiness judgment.

## Inputs

Resolve before routing:

- user request and any explicit `base:<ref>` or scope argument
- current diff, branch, or recent commits
- implementation intent from conversation, branch, commits, or nearby plan artifacts
- project rules that affect read-only inspection and safe command execution

## Route Types

### Inline

Use inline investigation when all are true:

- the changed surface is tiny and obvious
- current context contains enough evidence
- no shared contract, security, reliability, CLI, or cross-context risk is likely
- a delegated investigator would add process cost without improving confidence

### Standard

Use for normal implementation review. Inspect always-on lenses:

1. `Correctness`
2. `Testing`
3. `Maintainability`
4. `ProjectStandards`

The parent may handle these inline or delegate one or more lenses if independent evidence would improve confidence.

### Conditional

Add conditional lenses when triggered by the diff or user request:

- `Security`: auth, user input, secrets, permissions, public endpoints, unsafe IO
- `ApiContract`: routes, schemas, exported types, CLI/API contracts, compatibility surfaces
- `Reliability`: retries, timeouts, error handling, concurrency, background work, external systems
- `CliReadiness`: commands, flags, help text, exit codes, stdout/stderr, agent-friendly output

### Deep

Use for broad, risky, public, release-critical, or cross-cutting changes. Inspect always-on lenses plus every clearly triggered conditional lens. Do not run every lens by default if the diff is small.

## Delegation Decision

Delegate a lens only when it is useful and available. Good reasons:

- the scope is large enough that independent read-only inspection will reduce blind spots
- a lens needs focused evidence from several files or contracts
- the parent needs parallel evidence before synthesis
- confidence is low after inline inspection

Do not delegate when:

- the review is trivial
- the runtime has no safe delegation mechanism
- the delegation mechanism cannot follow the read-only evidence contract
- the overhead would exceed the value

When delegating, use `references/DelegatedEvidence/MetaSkill.md` as the task and output contract.

## Runtime Adapters

Runtime-specific adapters may implement the delegated-investigator role. They are optional and must not be required by the portable skill.

Adapters must:

- preserve the assigned lens boundary
- stay read-only
- use the lens MetaSkill as evidence focus
- return the evidence brief format from `references/DelegatedEvidence/MetaSkill.md`
- leave final judgment to the parent

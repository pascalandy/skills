---
name: remote-skills-dev
description: Use andy's dev skills remotely
---

<!-- Generated from skills/*/SKILL.md by `just remote-skills`; do not edit -->

URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md

A mode's routes run through that mode's SKILL.md.

## Modes

- `code-review-mode`: Use for a code review of a branch or code area, an architecture review, a test audit, or a thermonuclear review, and whenever writing or changing tests.
  - architecture-review
  - test-audit
  - thermo-quality-review
- `matt-mode`: Use when the user invokes matt-mode to clarify requirements, discuss design, map decisions, or prepare implementation through specs and tickets.
  - codebase-design
  - domain-modeling
  - grill-me
  - grill-with-docs
  - to-spec
  - to-tickets
  - wayfinder
- `poteto-mode`: Use only when explicitly invoked as `poteto` or `poteto-mode`.
  - authoring-a-skill
  - autonomous-run
  - autopilot-full
  - autopilot-stack
  - babysit
  - bug-fix
  - eval
  - feature
  - hillclimb
  - investigation
  - multi-phase-plan
  - opening-a-pr
  - orchestrate
  - pause-safely
  - perf-issue
  - prototype
  - refactoring
  - runtime-forensics
  - session-pickup
  - shipping
  - trace-forensics
  - visual-parity
  - worktree-cleanup

## Skills

- `architect`: Use when the user invokes `architect` or requests software architecture design.
- `automate-me`: Use when the user wants their recurring working preferences captured or updated in a personal `-mode` skill. Do not use for a single task-specific workflow.
- `blast-radius`: Use for 'blast radius of X', 'what could this break', or reviewing a small diff you don't trust.
- `coding-eng-laws`: Use when analyzing code, architecture, team, or planning decisions using software engineering laws and principles, or when `coding-eng-laws` is mentioned.
- `coding-language`: Use when writing, debugging, linting, or reviewing Bash, Python, TypeScript, JavaScript-with-types, or Starlette/ASGI code.
- `coding-standard`: Use when designing, implementing, or reviewing an agent-friendly CLI, including commands, flags, help text, output, errors, and safety behavior.
- `commit`: Use when creating atomic git commits, staging logical changes, splitting commits, or formatting commit messages.
- `create-verification-skill`: Use only when explicitly invoked as `create-verification-skill`.
- `execute`: Use only when explicitly invoked as `execute` or `implement`, or by a clear go-ahead to implement an agreed plan.
- `gh-stack`: Manages stacked PRs and splits multi-part work into reviewable branches with gh-stack. Use for stack creation, viewing, edits, push, submit, sync, rebase, merge, or checkout; when asked to split or isolate work for review; whenever a user mentions a stack, branch layers, dependent PRs, or gh stack; or when a stack is checked out.
- `git-local`: Use when a task requires inspecting or working across an external GitHub repository's code and cloning it into the local cache is more effective than browsing source files online or making repeated GitHub API queries.
- `grill-for-unknowns`: Use when a complex implementation plan has material unknowns that require evidence from source or authoritative documentation before implementation. Do not use for ordinary idea stress tests or work with settled acceptance criteria.
- `headless`: Use when running `codex exec`, `codex exec review`, Claude Code, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them. `headless` may arrive as any voice-to-text spelling that sounds like it, such as `endless` or `adless`.
- `how`: Use for questions about how code works, code walkthroughs before changes, or questions about placement, ownership, and layering. Use `why` for design motivation.
- `interrogate`: Use when the user asks for an adversarial or multi-model review, wants code or a plan stress-tested, or asks to uncover blind spots.
- `label-for-issues`: Use when triaging GitHub issues, managing issue labels or decision comments, creating issues or PRs, or starting work on an issue.
- `maintain-verification-skill`: Use when the user invokes `maintain-verification-skill` or asks to audit a project's existing verification skill.
- `verify-skills`: Use when verifying `just compile-skills`, `just remote-skills`, `just install-skills`, or `just skills-discover` in the skills repository, such as after changing their scripts or adding, renaming, or moving a skill.
- `verify-transcript`: Use when validating transcript CLI behavior or locating its verification features. Use for paid YouTube end-to-end checks only when explicitly authorized.
- `verify-video-archive`: Use when validating the macOS or Linux archive workflow reached by `just convert-video`, including real media, prerequisites, terminal progress, source safety, locking, and recovery.

## Helpers

- `arena`: Use when the user invokes `arena`, or when competing designs or implementations should be compared before choosing an approach for a non-trivial artifact.
- `figure-it-out`: Use when the user invokes `figure-it-out`, for a large migration or cross-cutting effort, for work a human will review after stepping away, or when no narrower playbook fits.
- `make-bot-ui`: Use when building a custom UI that starts agent tasks through a webhook or local runner.
- `no-comments`: Use only when explicitly invoked as `no-comments`, including `No comments` as an instruction.
- `principle-prove-it-works`: Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.'
- `recall`: Use only when explicitly invoked as `recall`.
- `reflect`: Use only when explicitly invoked as `reflect`.
- `show-me-your-work`: Use when the user invokes `show-me-your-work`, for long-running, autonomous, or multi-phase work, or for work a human will review after stepping away.
- `swarm`: Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration.
- `tdd`: Use only when explicitly invoked as `tdd`.
- `teach`: Use when the user asks to be taught, requests a guided technical explanation, or wants one account combining how something works with why it was designed that way.
- `technical-writing`: Use for /technical-writing or when writing or reviewing docs, RFCs, readmes, PR descriptions, or commit messages.
- `typescript-best-practices`: Use when TypeScript work centers on type safety, domain modeling, narrowing, casts, or runtime boundaries. Use `coding-language` for general TypeScript implementation and tooling.
- `why`: Use for questions about design rationale, the history of regressions or incidents, or the evidence behind thresholds and tradeoffs. Use `how` for runtime behavior. Do not use for plain commit or date lookups.

---
name: Headless glossary
description: Canonical vocabulary for the headless skill
tags:
  - kind/glossary
  - kind/project
date_created: 2026-07-01
date_updated: 2026-07-01
---

# Headless glossary

## Purpose

Canonical vocabulary for the `headless` skill: delegation, CLI routing,
execution modes, permission posture, workdir safety, and output handling.

This file defines the language used by `SKILL.md`, `references/ROUTER.md`, and
sub-skills under `references/<cli>/MetaSkill.md`. It does not replace CLI flag
references or update checklists.

## Concept map

- Headless skill -> router -> sub-skill
- Delegation sub-skill -> target CLI -> execution mode -> permission posture
- Target CLI -> PTY posture -> base invocation
- CLI flag reference -> detailed command syntax
- Output handling -> relay, parse, save, or resume delegated work

## Core terms

### Headless

Non-interactive CLI usage for delegation or flag lookup across Claude, Codex,
OpenCode, and Pi.

Not: generic background jobs, shell subprocesses, or Pi subagents.

### Headless delegation

Strict-trigger workflow that sends real execution work to a supported target CLI.

Canonical trigger:

`use headless-delegation with <cli> to <task>`

Allowed `<cli>` values: `claude`, `codex`, `opencode`, `pi`.

Not: loose prompts like `delegate to codex`, `run this in claude headless`, or
advisor-style model consultation.

### Target CLI

External CLI selected for delegated work.

Supported targets: Claude, Codex, OpenCode, Pi.

Rule: never silently swap the target CLI. If the user says Codex, use Codex or
report why Codex cannot run.

### Skill router

`references/ROUTER.md`, the dispatch table that maps request patterns to one
headless sub-skill.

Rule: load router before choosing a sub-skill.

### Sub-skill

Branch-specific reference loaded from `references/<branch>/MetaSkill.md`.

Main branches:

- `delegation/MetaSkill.md`
- `claude/MetaSkill.md`
- `codex/MetaSkill.md`
- `opencode/MetaSkill.md`
- `pi/MetaSkill.md`

### CLI flag reference

Sub-skill that documents one target CLI's headless command surface.

Rule: keep detailed flag tables in CLI references, not in the delegation
orchestrator.

## Execution terms

### Execution mode

Canonical launch mode for a target CLI.

- Claude -> print mode, no PTY
- Pi -> print/json mode, no PTY
- Codex -> `codex exec`, PTY
- OpenCode -> `opencode run`, PTY

Rule: do not change execution mode by preference; use the matrix in the
delegation sub-skill.

### PTY posture

Whether the delegated command must run with a pseudo-terminal.

- Codex and OpenCode require PTY
- Claude print mode and Pi print mode do not use PTY

Not: `pty mode`. PTY is a launch constraint, not a user-facing mode.

### Print mode

Non-interactive command mode that prints an answer and exits.

Examples:

- `claude --print`
- `claude -p`
- `pi --print`
- `pi -p`

### JSON mode

Machine-readable event or structured output mode.

Examples:

- `pi --mode json`
- `claude --output-format stream-json`
- `codex exec --json`
- `opencode run --format json`

### Exec mode

Codex's non-interactive execution path through `codex exec`.

Normally requires a git repository unless the installed Codex version supports
and permits bypassing that check.

### Run mode

OpenCode's non-interactive execution path through `opencode run`.

Can attach to a pre-started OpenCode server when MCP cold boot is expensive.

## Safety terms

### Permission posture

Cross-CLI term for approval and sandbox stance during delegated work.

Start conservative. Escalate only when the task requires writes, shell access, or
fully unattended work.

Not: vague “safe mode” or “automatic mode”. Name the exact CLI setting.

### Claude permission mode

Claude Code's named approval behavior for print-mode runs.

Common values: `plan`, `acceptEdits`, `dontAsk`, `auto`, `bypassPermissions`.

Rule: unattended Claude print mode needs an explicit permission strategy.

### Codex sandbox policy

Codex file-system and approval constraint for an exec run.

Common values: `read-only`, `workspace-write`, `danger-full-access`.

Rule: ask before danger-level access.

### Workdir hygiene

Choosing and constraining the working directory before launching a delegated
agent.

Rules:

- pass an explicit workdir for repo-dependent tasks
- refuse parent CLI state directories
- use a temp clone/worktree for PR review or scratch work when appropriate

### Unsafe workdir

Directory that must not be used as a delegation target because it can leak parent
CLI state or control context.

Examples: `.claude`, `.pi`, `.openclaw`, `.opencode`, and other agent runtime
state directories.

### Failure relay

Report a delegated agent's non-zero exit, hang, or refusal without silently
replacing its work in the parent assistant.

Rule: if delegation fails, surface the failure and ask before retrying with
broader permissions.

## Target CLI terms

### Claude

Claude Code CLI target for headless print-mode runs.

Canonical shape: `claude --print --permission-mode <mode> "<task>"`.

### Codex

OpenAI Codex CLI target for headless `codex exec` runs.

Use explicit sandbox policy for unattended automation.

### OpenCode

OpenCode CLI target for headless `opencode run` runs.

Can select configured agents with `--agent`.

### Pi

Pi CLI target for `pi -p`, `pi --print`, or `pi --mode json` runs.

Pin `--model` when reproducibility matters.

### Model pinning

Explicitly selecting a model or agent instead of relying on CLI defaults.

Examples:

- Claude: `--model`
- Codex: `-m` / `--model`
- OpenCode: `--agent` or `--model`
- Pi: `--model`

## Output terms

### Output handling

Rules for relaying, parsing, or saving target CLI output.

Keep stderr visible when it carries progress or diagnostics. Use machine-readable
output only when a parser needs it.

### Output cleanup

Stripping terminal control sequences before parsing CLI output or taking the last
answer line.

Especially important for Pi print-mode smoke tests.

### Terminal control codes

ANSI or control sequences emitted by terminals or harnesses around CLI output.

Rule: do not treat the last raw line as the answer until output is cleaned.

### Session management

Continuing, resuming, forking, naming, or disabling persistence for CLI
conversations.

Flags differ by target CLI; use the relevant CLI flag reference.

### Background delegation

Delegated run started in the background so the parent assistant can continue
working.

Rule: report the session ID and the monitor/kill commands.

### Session ID

Identifier used to poll, resume, continue, or stop a background or persisted CLI
run.

## Boundary terms

### Same-CLI sub-agent routing

Delegation inside the current Pi harness through `$pi-subagents`.

Not headless delegation.

### Advisor pattern

Asking another model or agent for advice, review, or critique rather than
execution.

Not headless delegation.

## Terms to avoid

- headless agent -> use target CLI or headless delegation
- delegate -> specify headless delegation, same-CLI sub-agent routing, or advisor pattern
- automatic mode -> name the exact permission or sandbox setting
- safe mode -> name the exact permission or sandbox setting
- pty mode -> use PTY posture
- CLI docs -> use CLI flag reference, official update source, or local verification

## Terminology decisions

- Keep headless delegation strict-triggered to avoid collisions with
  `$pi-subagents`, advisor loops, and generic shell subprocesses.
- Use permission posture as the cross-CLI safety term; reserve permission mode
  for Claude's exact flag language.
- Use PTY posture for launch constraints; avoid PTY mode.
- Keep CLI flag references separate from delegation orchestration to avoid stale
  duplicated flag tables.

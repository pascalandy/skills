---
name: "poteto-mode"
description: "Use only when explicitly invoked as `poteto` or `poteto-mode`."
kind: "dev"
---

# Poteto mode

Read [agent runtime](references/agent-runtime.md) before choosing tools, models, delegation, history, or continuation. It defines the shared capability checks and fallbacks for Codex, Claude Code, Pi, and OpenCode. Repository rules and user authorization govern which playbook actions apply.

For the rationale, capability mapping, and remaining limitations, read [portability notes](references/portability-notes.md).

## Non-negotiables

The Principles section below grounds every trigger. Before a decision, read each principle whose entry matches it. In your reply, name each principle that shaped a decision and the specific choice it changed, unless another invoked skill such as `teach` owns the reply format. Cite only principles you read this session.

Remaining triggers:

- Nontrivial change, architecture decision, or "are we sure?" → the **how** skill.
- About to ask the user on a "which approach", "how should I", or "what should this do" fork → classify it before you ask. If the answer is a fact you could observe by running something (behavior, timing, layout, output, perf, even whether an eval separates), it is not the human's to answer. Sketch it via the Prototype playbook (`playbooks/prototype.md`) and let the result decide. If the task is a read-only Investigation whose deliverable is a cited answer, stay in it and answer from the evidence rather than building a sketch. Reserve the question for a genuine product or preference call no experiment can settle.
- Any code → name the data shape first, and choose its organizing structure per the **Model the Domain** principle.
- Code crossing a function boundary → the **architect** skill, parallel design exploration before implementing.
- Parallel fan-out → the **swarm** skill for coverage matrices, races, gauntlets, and exploration partitions. Use **arena** for design or code bakeoffs with base selection and grafting.
- Contested design → the **interrogate** skill (multi-model adversarial) before shipping.
- Nontrivial multi-step → write the throughput checkpoint (Feature step 3).
- Any prose surface → the **unslop** skill. Your reply is a prose surface. Write it per **Writing the reply**. Skills and other agent-facing documents use **writing-for-agents**, resolved through the runtime reference.
- Docs, RFCs, readmes, PR descriptions, or commit messages → the **technical-writing** skill (`/technical-writing`).
- Before commit → the diff cleanup procedure in [agent runtime](references/agent-runtime.md#author-clean-up-and-verify).
- Before review of a diff that changes source code → the **no-comments** skill (`/no-comments`).
- Shipping UI / IDE / CLI → the project verification skill and an available shell, PTY, browser, or native application driver, as described in the runtime reference. For bug fixes, reproduce first on the same surface yourself. Hand to the user only under the narrow Bug fix step 1 exception.
- Any PR-status request → the **Babysit** playbook (`playbooks/babysit.md`). That includes "babysit this", "get it green", "address the review comments", and the commonest phrasing, "check on PR X" / "anything outstanding on X". Never triggered by merely opening a PR. Declare its mode before polling. The playbook's step 1 owns the request-to-mode mapping. Keep long-lived supervision in the coordinator so phase workers can return their results.
- Multiple dependent PRs for one coherent effort → before implementation, load `gh-stack` unless the active playbook already owns stack topology or landing.
- Asked to land or ship a green stack → the **Shipping** playbook (`playbooks/shipping.md`). Green is not safe. Nothing gets armed before an independent per-PR verdict, and only the contiguous verified run from the root lands.
- A configured PR review agent commented → skeptical posture. They catch real bugs and also file non-issues and nitpicks, so assess each on its merits and dismiss noise with a concrete reason instead of churning code. Triage fix / dismiss / ask per `references/review-bot-triage.md`.
- Broken skill mid-task → fix it in its own PR. Don't block. Don't silently work around it.
- Long, autonomous, or multi-phase work, or any task the user steps away from to review later ("going to bed", "trust it when i'm back", "continue until X") → a decision trail via the **show-me-your-work** skill. Commit it when stakes need an auditable record. Keep it local otherwise.

Use [stack routing acceptance cases](references/stack-routing-cases.md) when changing this decision.

## Principles

Each entry links a principle's file and says when it applies.

**Core**

- [Laziness Protocol](principles/laziness-protocol.md): refactoring, sizing a diff, or tempted to add abstractions, layers, or signal threading
- [Foundational Thinking](principles/foundational-thinking.md): before writing logic, when choosing core types and data structures, sequencing scaffold and feature work, or deciding what concurrent actors share
- [Redesign from First Principles](principles/redesign-from-first-principles.md): integrating a new requirement into an existing design
- [Attack the Premise](principles/attack-the-premise.md): two or more fixes that share one premise have failed the same gate
- [Subtract Before You Add](principles/subtract-before-you-add.md): sequencing an addition, refactor, or rewrite
- [Minimize Reader Load](principles/minimize-reader-load.md): reviewing or shaping code that's hard to trace
- [Outcome-Oriented Execution](principles/outcome-oriented-execution.md): planned rewrites and migrations with explicit phase boundaries
- [Experience First](principles/experience-first.md): product, UX, or feature-scope tradeoffs
- [Exhaust the Design Space](principles/exhaust-the-design-space.md): a novel interaction or architectural decision with no precedent
- [Build the Lever](principles/build-the-lever.md): any non-trivial work, such as edits, migrations, analyses, or checks

**Architecture**

- [Model the Domain](principles/model-the-domain.md): writing stateful logic, or code that branches a lot or repeats a shape assumption across files
- [Boundary Discipline](principles/boundary-discipline.md): wiring validation, error handling, or framework adapters
- [Type System Discipline](principles/type-system-discipline.md): designing types, reviewing a function signature, or writing code in a statically typed language
- [Make Operations Idempotent](principles/make-operations-idempotent.md): designing commands, lifecycle steps, or loops that run amid crashes, restarts, and retries
- [Migrate Callers Then Delete Legacy APIs](principles/migrate-callers-then-delete-legacy-apis.md): introducing a new internal API while old callers still exist
- [Separate Before Serializing Shared State](principles/separate-before-serializing-shared-state.md): concurrent actors might write the same file, branch, key, or object

**Verification**

- **Prove It Works**, the `principle-prove-it-works` skill, which loads on its own description
- [Fix Root Causes](principles/fix-root-causes.md): debugging
- [Sequence Work into Verifiable Units](principles/sequence-verifiable-units.md): multi-step work, such as sweeps, migrations, and runs of similar edits, and how you stack commits and PRs
- [Test Behavior, Not Implementation](principles/test-behavior-not-implementation.md): writing, changing, or keeping a test

**Delegation**

- [Guard the Context Window](principles/guard-the-context-window.md): context filling up with large outputs, long files, repeated reads, or fan-out planning
- [Never Block on the Human](principles/never-block-on-the-human.md): tempted to ask "should I do X?" on reversible work

**Meta**

- [Encode Lessons in Structure](principles/encode-lessons-in-structure.md): you catch yourself writing the same instruction a second time, or notice a recurring correction

## Autonomy

**Just do it.** Complete authorized work using the available tools. Follow the active session and repository rules for external writes, messages, and irreversible actions.

**Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages.

**Session overrides:** "Don't stop" / "going to bed" / "run until done" / "be fully autonomous" → keep going.

**No is an acceptable answer.** Asked whether to do something, invited to add scope, or shown an approach, reply with your real judgment. Decline, push back, or say "this doesn't earn its place" when true. A recommendation is a judgment, not a validation. Agreement is not the default, candor over sycophancy.

## Subagents

When delegation helps, load `profile-routing-matrix` from the active skill catalog once for the current orchestration. It owns role selection, models, reasoning levels, and agent briefs. Apply it to every delegation in this task.

Prefer asynchronous workers for independent tasks when the runtime supports them. Give reviewers the tools needed to inspect evidence and constrain them to read operations. Supply accessible file pointers or self-contained excerpts. Follow the runtime reference for supervision, nesting limits, shared checkouts, and remote execution.

You own every subagent's work. Inspect the actual diff and evidence, then write your own summary. When an agent is interrupted, provide a consolidated brief before it continues. A second opinion requires a separate reviewer. Self-review does not satisfy an independent verification gate.

## Writing the reply

Write the reply clean as you draft it, following unslop, including its dash and colon rules. A cleanup pass after drafting does not remove those patterns. Write a file-list bullet as a sentence ("`main.js` owns persistence and the IPC handlers") and a bold section header as its own sentence ("**Verification.** End to end via CDP").

- **Short declarative sentences.** One thought per sentence, ended with a period.
- **Terse is not an excuse to drop content.** Short sentences, but every section the playbook's reply names stays: details, tradeoffs, choices, open decisions.
- **Frame impact for the consumer and the maintainer.** Name who the work is for (an end user, a colleague importing the library) and what changes for them before any implementation detail. Then what the next engineer who owns this code inherits. If you can't say what either would notice, the work or the explanation is off.
- **Never fabricate a link, citation, or transcript reference.** Link only artifacts you produced or read this session.

Every playbook ends with a reply written this way, PR link as `https://github.com/<owner>/<repo>/pull/<number>`. The per-playbook lines below name only the content unique to that playbook.

## Comments

Comments follow the same rule as the reply. Write them clean as you go. Keep a comment only for a non-obvious *why* the code can't show. A verify or test script gets no phase-narrating comments such as `// Phase 1: add cards`. The assertion or log string documents the step, as in `assert(ok, 'persisted across restart')`. This applies to every file you produce, including the delegate's diff.

## Playbooks

Use the available task-list tool or a Markdown checklist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`. Match the task to a playbook below, open its file, and copy its steps in verbatim.

A large or cross-cutting effort (a migration across many call sites, an ambitious multi-part change), or work the user steps away from to trust later, routes to the **figure-it-out** skill even when a narrower playbook like Feature fits. Use **figure-it-out** whenever no bundled playbook fits. It designs a bespoke, rigorous playbook for the task. A standing project-scale program (multi-day, many stacked PRs, a fleet of subagents under one coordinator) routes to **Orchestrate** instead. figure-it-out designs one bespoke run, orchestrate runs the program.

- **Investigation.** Read-only question: how does X work, why was Y built this way, are we sure about Z, should we do X or Y. `playbooks/investigation.md`.
- **Bug fix.** A reported defect to reproduce, root-cause, and fix with runtime evidence. `playbooks/bug-fix.md`.
- **Perf issue.** A measured slowness to trace and improve against a baseline. `playbooks/perf-issue.md`.
- **Hillclimb.** Sustained, scientific improvement of one metric against a target: loop hypotheses with before/after measurement, a decision log, and one commit per accepted win. Distinct from Perf issue, which is a one-off fix. `playbooks/hillclimb.md`.
- **Runtime forensics.** Diagnose a runtime symptom (leak, idle-CPU spin, glitch) from live instrumentation. The deliverable is a diagnosis, not a fix. `playbooks/runtime-forensics.md`.
- **Trace forensics.** Diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot) handed to you after the fact. The deliverable is a diagnosis, not a fix. `playbooks/trace-forensics.md`.
- **Feature.** New or changed behavior, built from a named data shape. `playbooks/feature.md`.
- **Refactoring.** A behavior-preserving change to structure or shape (rename, extract, inline, dedupe, move). `playbooks/refactoring.md`.
- **Prototype.** A throwaway sketch to make a design or behavioral decision cheaply, or to settle an empirical fork by observing it instead of asking the human ("prototype", "mock it up", "try this layout", "sketch it to decide"). `playbooks/prototype.md`.
- **Visual parity.** Pixel-exact UI equivalence: matching two implementations or migrating a styling system. `playbooks/visual-parity.md`.
- **Authoring or modifying a skill.** Writing or editing a SKILL.md. `playbooks/authoring-a-skill.md`.
- **Eval.** Testing how a skill, structure, or prompt change affects agent behavior before promoting it. `playbooks/eval.md`.
- **Babysit.** Driving a PR or a stack to merge-ready: conflicts, review threads, CI. `playbooks/babysit.md`.
- **Shipping.** The half after Babysit. Independently verifying a green stack, then landing the contiguous verified run bottom-up through `gh` by default or Origin when its CLI is available. `playbooks/shipping.md`.
- **Autonomous run.** A long task to drive to completion without stopping ("run until done", "continue until X"). `playbooks/autonomous-run.md`.
- **Orchestrate.** A standing project handed to one coordinator chat: multi-day, many stacked PRs, dozens to hundreds of subagents, minimal human turns ("run this whole project", "own this migration until it lands"). Distinct from Autonomous run, which drives one task to a predicate. Work one agent could finish inside the session's budget routes there, not here, however program-shaped the phrasing sounds. `playbooks/orchestrate.md`.
- **Autopilot-full.** A queue of independent PRs run to merged with full autonomy. One owner per PR carries build through merge, and the root swarm-verifies each merge-ready head before its owner merges ("autopilot this queue", "full autopilot", one-owner-per-PR programs). `playbooks/autopilot-full.md`.
- **Autopilot-stack.** A queue of changes built and verified with full autonomy, delivered as one linear reviewed base-branch stack the operator lands herself ("autopilot-stack", "stack them, don't ship", "build the stack, I'll land it"). `playbooks/autopilot-stack.md`.
- **Session pickup.** Resuming or taking over a prior agent's in-flight work from a transcript, cloud-agent URL, or pushed branch. `playbooks/session-pickup.md`.
- **Pause safely.** Suspending in-flight work cleanly so it can be resumed, on an explicit pause, going offline, an agent-tool restart, or imminent context compaction. The complement to Session pickup. Full steps: `playbooks/pause-safely.md`.
- **Multi-phase or multi-PR plan.** Work that spans phases or stacked PRs. `playbooks/multi-phase-plan.md`.
- **Worktree and simulator cleanup.** Reclaiming local disk by pruning merged or abandoned git worktrees and stale iOS simulators ("what's using my disk", "clean up worktrees", "prune safe-to-prune worktrees", "free up space", "delete old simulators"). `playbooks/worktree-cleanup.md`.
- **Opening a PR.** Invoked at the end of every other playbook. `playbooks/opening-a-pr.md`.

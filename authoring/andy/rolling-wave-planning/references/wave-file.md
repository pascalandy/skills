# Wave file

Read this file before you write a file in `plan/waves/`, a task brief or a QA brief.

## `waves/WNN-<slug>.md`

```markdown
---
id: W02
project: ACME
status: active   # proposed | planned | active | done | dropped
label: wave:W02
---

# W02: <name>

## Goal
One sentence.

## Exit criteria
- [ ] …

## Epics

### E04: <outcome in plain words> → #52
- Traces: [BC §4](../00-business-case.md#4-onboarding), SC2
- Problem (CMO): what is wrong or absent today, with its cost.
- Outcome (FMO): what is true when the epic is closed.

#### E04-T01: <imperative title> → #57
- Kind: feature | spike | chore | fix · Executor: agent | human · State: todo
- Depends on: E03-T02, because it defines the `/session` contract (or none) · Batch: 2
- Today: the current behavior or state, with evidence. A reader understands it without the business case.
- After: what is true when the task is done.
- Traces: [BC §4.2](../00-business-case.md#42-login), D005
- Touches: `src/auth/**`, `tests/auth/**` (new: `src/auth/login.ts`)
- Contract: `POST /login {email,password} → 200 {token} | 401` (or none)
- Acceptance:
  - [ ] `pnpm test tests/auth/login.test.ts` passes (valid login, wrong password, unknown user)
  - [ ] `curl -s -XPOST localhost:3000/login -d @fixtures/ok.json` returns 200 with `token`
- Verify: `make verify`
- Out of scope: password reset, rate limiting (E04-T03)
- Fixes finding: #71 (fix tasks only; #71 stays open until the QA agent closes it)
- Steps (optional):
  - [ ] E04-T01-S1: …

#### E04-QA1: QA: <epic name> → #60
- Kind: qa · Executor: QA agent on the QA machine · State: todo · Verdict: —
- Verifies: E04-T01, E04-T02, E04-T03 · Depends on: same, because QA tests finished work · Starts after: batch 2
- Blocking: no (or: yes — gates E05-T02 because it consumes the `/login` contract)
- Context: what the epic delivers for the user, in 2–3 sentences.
- Traces: [BC §4](../00-business-case.md#4-onboarding), SC2
- QA scenarios (≤ 8):
  - [ ] A new user signs up, logs in and lands on the dashboard (`<exact steps or command>` → `<observable result>`)
  - [ ] A wrong password shows an error and does not create a session
- Also check: every verified task's Acceptance still passes on the default branch; `make verify` passes.
- Output: QA report comment, verdict label, one finding issue per finding. No commits, no PRs.

## Execution order
- Batch 1 (parallel): E04-T01, E05-T01
- Batch 2 (parallel): E04-T02, E04-T03
- Batch 3: E05-T02
- QA (parallel, gates nothing unless marked blocking): E04-QA1 after batch 2 · E05-QA1 after batch 3

## Discoveries
- E04-T02 (#58): <finding> → bucket (a|b|c|d), D###

## Changes since original plan
- <change>. Why: … (D003)

## Learnings
```

## Brief rules

- Each acceptance item and each QA scenario is a command with an expected result, or exact steps with a result that a person can see. Never write "works correctly"
- Two tasks in the same batch must not have the same path in `Touches`. If they do, add a dependency between them
- A QA task has no `Touches`
- Each `Depends on` gives its reason: an acceptance item, the current code or a shared path in `Touches` needs the other task first. Possible later work is not a reason
- A batch is a view of the dependency graph, not a gate. A task is ready when each of its blockers is closed
- The QA tasks are on their own `QA` line and never delay a batch
- A task that defines a shared contract is in an earlier batch than the tasks that use the contract

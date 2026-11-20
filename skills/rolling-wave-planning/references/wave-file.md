# Wave file

Read this file before you write a file in `plan/waves/`, a task brief or a QA brief.

## `waves/WNN-<slug>.md`

````markdown
---
id: W02
project: ACME
status: active   # proposed | planned | active | done | dropped
label: wave:W02
skill_version: "2.0.0"   # the `version` of this skill when the planner created this file
executor: agent   # agent | human | tbd
---

# W02: <name>

## Goal
One sentence.

## Exit criteria
- [ ] …

## Epics

### E04: <outcome in plain words> → #52
- Traces: [BC §4](../00-business-case.md#4-onboarding), SC2
- Executor: agent | human | tbd
- Problem (CMO): what is wrong or absent today, with its cost.
- Outcome (FMO): what is true when the epic is closed.

#### E04-T01: <imperative title> → #57
- Kind: feature | spike | chore | fix · Executor: agent | human · State: todo
- Today: the current behavior or state, with evidence. A reader understands it without the business case.
- After: what is true when the task is done.
- Traces: [BC §4.2](../00-business-case.md#42-login), D005
- Contract: `POST /login {email,password} → 200 {token} | 401` (or none)
- Acceptance:
  - [ ] `pnpm test tests/auth/login.test.ts` passes (valid login, wrong password, unknown user)
  - [ ] `curl -s -XPOST localhost:3000/login -d @fixtures/ok.json` returns 200 with `token`
- Verify: `make verify`
- Out of scope: password reset, rate limiting (E04-T03)
- Fixes finding: #71 (fix tasks only; #71 stays open until the QA agent closes it)
- Ready review: planner, YYYY-MM-DD, plan checks pass
- Steps (optional):
  - [ ] E04-T01-S1: …

```json
{
  "id": "E04-T01",
  "blocked_by": [{"id": "E03-T02", "why": "contract: it defines `/session`"}],
  "needs": [
    {"what": "Stripe test key", "check": "test -n \"$STRIPE_API_KEY\""},
    {"what": "QA machine access", "check": "ssh -o BatchMode=yes qa-host true"},
    {"what": "Auth tests pass before the change", "check": "pnpm test tests/auth"}
  ],
  "touches": ["src/auth/**", "tests/auth/**"]
}
```

#### E04-QA1: QA: <epic name> → #60
- Kind: qa · Executor: QA agent on the QA machine · State: todo · Verdict: —
- Context: what the epic delivers for the user, in 2–3 sentences.
- Traces: [BC §4](../00-business-case.md#4-onboarding), SC2
- QA scenarios (≤ 8):
  - [ ] A new user signs up, logs in and lands on the dashboard (`<exact steps or command>` → `<observable result>`)
  - [ ] A wrong password shows an error and does not create a session
- Also check: every verified task's Acceptance still passes on the default branch; `make verify` passes.
- Output: QA report comment, verdict label, one finding issue per finding. No commits, no PRs.
- Ready review: planner, YYYY-MM-DD, plan checks pass

```json
{"id": "E04-QA1", "verifies": ["E04-T01", "E04-T02", "E04-T03"], "needs": []}
```

## Discoveries
- E04-T02 (#58): <finding> → bucket (a|b|c|d), D###

## Changes since original plan
- <change>. Why: … (D003)

## Learnings
````

## Brief rules

- Each acceptance item and each QA scenario is a command with an expected result, or exact steps with a result that a person can see. Never write "works correctly"

## Graph block

Each brief ends with one fenced `json` block. The blocks of a wave file are its dependency graph, and [the graph script](../SKILL.md#dependency-graph) checks them and writes them as one graph file. A task block has exactly the keys `id`, `blocked_by`, `needs` and `touches`. A QA block has exactly the keys `id`, `verifies` and `needs`. An empty list is `[]`.

- **`blocked_by`:** the tasks and QA tasks that must be closed before this task starts. A task is ready when each of them is closed. An ID of an earlier wave file is permitted
- **`why`:** the reason for the blocker. The permitted reasons are: an acceptance item or the current code needs the other task first, the other task defines a contract that this task uses, both tasks have a common path in `touches`, or the task must wait for a passing verdict of a QA task ([Blocking](../SKILL.md#blocking)). Possible later work is not a reason
- A task that uses a contract is `blocked_by` the task that defines the contract
- **`verifies`:** the tasks that a QA task tests. The QA task is blocked by each of them
- **`needs`:** what the executor must have before the work starts, and that the agent file does not give: an installed application, access to a machine, an API key or a test that passes before the change. Each `check` is one command that exits 0 when the need is met. A `check` never prints a secret
- **`touches`:** the paths that the PR of the task changes or creates, from the repository root. Each entry is one file path, or `dir/**` for all the files below a folder
- Two tasks are parallel when no `blocked_by` path connects them, in the two directions. Two parallel tasks have no common path in `touches`. If they have one, add the task that must merge first to the `blocked_by` of the other task
- A batch is a group of IDs in `batches` of the graph file. It is a view of the graph, not a gate, and the wave file does not record it

---
name: "rolling-wave-planning"
description: "Use when breaking a business case or large plan into rolling waves (Project → Wave → Epic → Task → Subtask) for coding agents, planning QA/UAT tasks, triaging discoveries or QA findings, reviewing a finished wave, re-planning or inserting a wave, or syncing plan/ markdown to GitHub issues."
kind: "dev"
---

# Rolling Wave Planning

Turn a heavy business case into a plan that coding agents can execute task by task. Only the active wave is detailed; future waves stay rough and are re-planned at each wave review. Every epic's work is accepted by an independent QA agent acting for the product manager, in parallel with development.

Core rule: **every task must be executable from its brief plus the repo's agent file (`CLAUDE.md` / `AGENTS.md`), without opening `00-business-case.md`.**

Constraints:
- Never use the word "milestone", in the plan or as GitHub Milestones. Do not use GitHub Projects.
- Write plan prose in the user's language. IDs, file names, labels and commands stay in English.

## Roles

- **Planner:** a session running this skill. The only role that edits `plan/`, always in a `plan:` commit. Runs the procedures below, on request or whenever `discovery`, `qa-finding` or `needs-replan` issues are open.
- **Implementer:** an agent session executing one task, following the working agreement.
- **QA agent:** a fresh session with no implementation context for the tasks it verifies, acting for the product manager (UAT). No commits, no PRs.
- **User:** the product owner. Approves checkpoints; the only one who can waive QA.

## Levels

| Level | Definition |
|---|---|
| Project | The whole initiative, defined by the business case. |
| Wave | One goal, one demonstrable outcome (runs, can be shown or measured), 2–5 checkable exit criteria. Target 10–30 tasks; split a wave above ~40. |
| Epic | A coherent chunk of work inside a wave, traced to the business case. 3–8 tasks. |
| Task | One agent session, exactly one PR. Starting limits: one module or ≤ 8 files, ≤ ~400 changed lines, ≤ 5 acceptance criteria, zero open decisions. Split if any limit is exceeded, or if the task both defines and consumes a new contract. |
| Subtask | Ordered, commit-sized step inside the task's PR. Never a separate PR. Optional. |
| QA task | Independent acceptance of an epic's work (UAT). No commits, no PRs. ≤ 8 UAT scenarios. Non-blocking by default. |

Task limits and QA thresholds are recorded in `01-project.md` and recalibrated at each wave review from actual PR sizes and the QA rejection rate.

## Statuses

Wave status defines its detail level:

| Status | Detail |
|---|---|
| `proposed` | Goal, exit criteria, 3–6 rough scope bullets. No epics. |
| `planned` | Epics with `Traces` and one paragraph each. No tasks. |
| `active` | Epics, full task briefs, QA tasks, execution order. |
| `done` | Closed at review, with Learnings. |
| `dropped` | Kept, with a one-line reason and decision ID. |

- Exactly one wave is `active`; at most one is `planned`.
- Waves execute in the row order of the wave table in `01-project.md`. IDs are names, not order.
- Task state: `todo | done | dropped | carried→WNN`. A QA task has the same states plus, once done, a verdict: `accepted | accepted-with-findings | rejected` (the first two are "passing").
- Epic state: `open | closed`. **Epic closure rule:** an epic closes when (1) every task is `done` or `dropped`; (2) every QA task has a verdict, and each `rejected` one is followed by a later QA task with a passing verdict; (3) every `qa-finding` issue is closed. Only the user can waive QA, logged as a D###.

## IDs

- Project: short uppercase slug, e.g. `ACME`.
- Wave: `W01`, `W02`, … always two digits. An inserted wave takes a letter after the wave it follows: `W01B`, `W01C`, `W02B`. The original wave is implicitly "A"; there is no `W01A`. Waves appended at the end take the next free number.
- Epic: global, independent of waves: `E01`, `E02`, …
- Task: `E03-T01`. Subtask: `E03-T01-S1`. QA task: `E03-QA1`, `E03-QA2` (one sequence per epic, for intermediate, per-task and re-QA tasks alike). Decision: `D001`.
- `01-project.md` keeps a `Next IDs:` line (e.g. `E12, D007`); update it whenever an ID is allocated.
- In commits, PRs, branches and code, reference tasks as `E03-T02` only, never with the wave (waves change).

Rules:
1. IDs are never renumbered and never reused.
2. Dropped items keep their ID, state `dropped`, and a one-line reason.
3. Unfinished tasks (QA tasks included) keep their ID and their epic. The epic follows its open work: in the closed wave file the task line stays, marked `carried→W02`; in the receiving wave file add `### E03 (continued from W01) → #41` listing only the open tasks. The receiving wave is the wave becoming `active` unless a decision says otherwise.
4. A task never changes epic. If it must, drop it and create a new task that references the old ID; on GitHub, close the old issue as not planned with a link to the new one.

## File layout

```
CLAUDE.md / AGENTS.md            # agent file: stack, layout, verify command, how to start the system
                                 # (start command, seed data, test accounts), working agreements
plan/
├── 00-business-case.md          # source document, read-only
├── 01-project.md                # summary, open questions, limits, next IDs, wave table
├── decisions.md                 # D###: plan-structure and technical decisions
└── waves/
    ├── W01-walking-skeleton.md  # done
    ├── W01B-auth-foundation.md  # done, inserted at W01 review
    ├── W02-user-onboarding.md   # active
    ├── W03-billing.md           # planned
    ├── W04-reporting.md         # proposed
    └── W05-admin-console.md     # dropped
```

Wave files are never deleted. The business case is read-only, so its section anchors stay stable for `Traces`.

## Procedure A: initial decomposition

1. **Read the business case end to end.** Write the summary in `01-project.md`: objective, stakeholders, success criteria (numbered `SC1`, `SC2`, …), constraints, out of scope. Each item is 1–3 lines linking to its section. Do not rewrite the business case.
2. **Write `## Open questions`** in `01-project.md`, ranked by how much each would change the plan if answered differently. Each top-ranked question becomes a `spike` task in W01 or a question to the user. A spike has no PR: its output is a recommendation posted on its issue, which the planner logs as a D###.
3. **Cut the project into 3–7 waves**, ordered by risk and dependency. W01 is a walking skeleton (thin end-to-end slice) or the test of the riskiest assumption.
4. **Write the wave table** in `01-project.md` and one `proposed` file per wave in `waves/`.
5. **Checkpoint:** present the wave cut and open questions to the user. Get approval before detailing W01 and before any GitHub write.
6. **Detail W01 (`active`):** epics with `Traces`, every task as a full brief, QA tasks per the Quality assurance section, and an `## Execution order`. The first task of W01 creates or refreshes the agent file: stack, layout, the single verify command, how to start the system, and the working agreements (templates below).
7. **Detail W02 (`planned`):** epics with `Traces` only.
8. **Leave W03+ `proposed`.**
9. **Log `D001`:** the initial wave cut and why.
10. **Check before syncing:**
    - Every task is within the task limits; every acceptance item is a command or observable step; brief rules hold.
    - Every epic has a final QA task whose UAT scenarios derive from its `Traces`; every `Blocking: yes` QA task states its reason.
    - Every success criterion is covered by at least one wave's exit criteria; every W01 epic has `Traces`.
    - Only the active wave has tasks. The word "milestone" appears nowhere.
11. **Sync to GitHub** (see GitHub sync).
12. **Commit** `plan: initial decomposition` after sync, so issue numbers are included.

## Procedure B: wave review

1. **Reconcile from GitHub:** `gh issue list --label wave:W01 --state all --limit 500 --json number,title,state,stateReason,labels`; write task states and QA verdicts into the wave file.
2. **Close the wave.** Start the review when every implementation task is merged, dropped or stuck; do not wait for QA. Each task becomes `done`, `dropped` (with reason) or `carried→WNN`. A QA task without a verdict is carried (ID rule 3) with its epic. Exit criteria are checked now by a fresh QA session (no implementation context from this wave), which marks each met or unmet with evidence under `## Exit criteria`. Set the wave to `done` even if criteria are unmet; each unmet criterion becomes a carried task or a discovery.
3. **Write `## Learnings`** in the closed wave file.
4. **Classify each discovery** (from `discovery`, `needs-replan` and open `qa-finding` issues, the wave's `## Discoveries` section and Learnings) into exactly one bucket:
   - **(a) Fits the next wave's goal** → amend the next wave (default).
   - **(b) Distinct prerequisite block that must happen first** (foundation, tech debt, architecture fix) → insert a wave, e.g. `W01B`. Use only when (a) would dilute the next wave's goal.
   - **(c) Belongs later** → add it to a later wave's scope, or append a new wave.
   - **(d) Invalidates a future wave** → drop it or merge it into another.
5. **Promote:** the next wave in table order becomes `active`; the one after becomes `planned`.
6. **Detail the new active wave** in full: briefs, QA tasks, execution order, carried tasks per ID rule 3. Then run the Procedure A step 10 checks.
7. **Bring the new planned wave to epics.** Adjust `proposed` waves roughly.
8. **Add `## Changes since original plan`** to every changed wave (what, why, D###). Log one decision per structural change.
9. **Recalibrate** task limits and QA thresholds from the closed wave's PR sizes and rejection rate.
10. **Update** the wave table and `Next IDs` in `01-project.md`.
11. **Checkpoint:** present QA verdicts, open findings, unmet exit criteria and structural changes to the user. Get approval before syncing.
12. **Sync to GitHub.** Close epic issues that meet the epic closure rule.
13. **Commit** e.g. `plan: review W01, insert W01B, amend W02`.

## Procedure C: during a wave

When executing a task reveals something the plan did not anticipate:
1. **Inside the task's scope, no contract change** → do it; note it under Deviations in the PR.
2. **New work in the same wave goal, no effect on other tasks** → open an issue labelled `discovery` + the active wave. It is not executable until triaged.
3. **Changes a contract, invalidates another task, or exceeds the task limits** → stop, comment on the issue, label it `needs-replan`. Do not work around it. The planner amends the wave file and logs a D###, or defers it to the review.
4. **Never add scope silently**, and never edit `plan/` from a task branch.
5. **Triage (planner):** for each open `discovery` or `qa-finding` without a task, add the task to the active wave file (next free task ID in the epic), add it to the `Verifies` of an open QA task of that epic (or create the next QA task), sync, and commit `plan: triage`. If the wave would exceed ~40 tasks, defer to the review.

## Quality assurance

Implementers self-check (each task's `Acceptance` and `Verify`, plus CI). That is not acceptance. Acceptance is user acceptance testing (UAT) by an independent QA agent acting for the product manager.

### Granularity

- **Per epic (default):** every epic has a final QA task that verifies all its tasks against the epic's `Traces`, starting when its last task is merged.
- **Intermediate:** when an epic has more than 5 tasks or spans more than 2 batches, add a QA task after its first user-visible slice.
- **Per task (exception):** a dedicated QA task (`Verifies: E04-T03`, title `QA: <task title>`) only for high risk: shared contract, security, data migration, money, anything irreversible.
- Stagger epics so they do not all end in the last batch; QA should not pile up at the wave boundary.
- Enabler epics (infrastructure, tooling): the "user" is the next consumer (developer or agent). A spike epic's QA checks that the answer resolves the open question.

### Independence

- Independent means a fresh session or subagent with no implementation context for the tasks it verifies. It does not mean a different person or model. A session that wrote or reviewed code for a verified task must not QA it.
- Black box first: run the scenarios from the briefs, `Traces`, agent file and running system before reading diffs or PR discussions.
- The QA report records independence, since a shared GitHub account cannot prove it.

### Non-blocking by default

- A QA task is `blocked by` the tasks it verifies: it starts once they are merged.
- **Nothing depends on a QA task by default** (`Blocking: no`). Later tasks, epics and batches continue in parallel with QA.
- Set `Blocking: yes` only with a stated reason, when continuing without acceptance would be costly to undo: later tasks build on a contract or schema under QA; security, data loss, money or an irreversible migration is involved; a release or deployment follows. Add it as a `blocked by` dependency on exactly the tasks it gates, never on a whole wave.
- A `Blocking: yes` QA issue closes only on a passing verdict. On `rejected` it stays open (label `qa:rejected`) so `blocked by` keeps holding; the planner closes it when the re-QA passes.
- QA gates **epic closure only**. It never gates the wave review: a QA task without a verdict at review is carried, its epic stays open in the receiving wave, and QA continues in parallel with the new wave.

### Findings and verdicts

1. QA posts a report on its issue: a 3-line summary for the product manager, scenarios run, evidence (commands and output, screenshots), findings, verdict, and the line `Independence: fresh session, no implementation context; verified PRs #57 #58`.
2. Verdict: `rejected` if any UAT scenario fails, any verified Acceptance fails on the default branch, or a traced success criterion is not met. `accepted-with-findings` if all scenarios pass and the findings are cosmetic or edge cases. Otherwise `accepted`.
3. Each finding is an issue `Finding (E04-QA1): <title>`, labels `qa-finding` + active wave, sub-issue of the epic, with reproduction steps, expected and actual result.
4. The planner (Procedure C triage) creates one fix task per finding, with `Fixes finding: #71`; its Acceptance includes the reproduction. The fix PR uses `Refs #71`, never `Closes`.
5. Only a QA session closes a finding, after re-running its reproduction on the default branch. After `accepted-with-findings` this re-check is enough. After `rejected` the planner also adds a re-QA task (next free QA ID; `Verifies` = fix tasks + failed scenarios), non-blocking unless the rejected QA was blocking.
6. After two consecutive `rejected` verdicts on one epic: stop, label the epic `needs-replan`, ask the user.
7. A finding that changes scope or a contract follows Procedure C step 3.

## GitHub sync

### Who owns what

- **Markdown owns definition:** scope, briefs, order, decisions. Only the planner changes it.
- **GitHub owns execution state during the active wave:** open/closed, assignee, ticked subtasks, verdicts, PR links.
- Reconcile at wave review (Procedure B step 1).
- On conflict, the wave file wins: fix the markdown, then regenerate the issue body.

### Mapping

| Plan item | GitHub |
|---|---|
| Project, decisions, `proposed` waves | Nothing (markdown only) |
| Wave (`planned` or `active`) | Label `wave:W02` |
| Epic (`planned` and `active` waves) | Issue `[E03] <name>`, type `Epic` or label `epic` |
| Task (`active` wave only) | Sub-issue of its epic, `[E03-T02] <name>`, type `Task` or label `task` |
| QA task | Sub-issue of its epic, `[E03-QA1] QA: <epic name>`, type `Task` + label `qa` |
| QA verdict | Label `qa:accepted`, `qa:accepted-with-findings` or `qa:rejected` on the QA issue |
| Finding | Sub-issue of the epic, `Finding (E03-QA1): <title>`, label `qa-finding` |
| Subtask | Checklist in the task issue body |
| Dependency | Native `blocked by` |
| Mid-wave findings | Labels `discovery`, `needs-replan` |

### Rules

1. Every epic, task, QA, finding and discovery issue carries exactly one `wave:` label.
2. Task and QA issue body = the brief from the wave file, verbatim, plus a link to the wave file.
3. Write the issue number back into the wave file: `#### E03-T02: <title> → #57`.
4. **Idempotent:** before creating, look up the exact title prefix: `gh issue list --state all --limit 500 --json number,title --jq '.[] | select(.title | startswith("[E03-T02] "))'`. If found, update it instead.
5. Create issues in batch order so blockers exist before dependents.
6. Closed issues keep the label of the wave they closed in. A carried epic and its open tasks get the receiving wave's label.
7. Dropped task → close as **not planned** with the reason in a comment.

### CLI

Requires gh ≥ 2.94.0 (`gh --version`); on older versions, stop and ask the user to upgrade. `Epic` is not a default issue type: check `gh api orgs/<org>/issue-types --jq '.[].name'`. If it is missing, or in a personal repo, use labels `epic` / `task` and drop `--type`.

```bash
for l in epic task qa qa:accepted qa:accepted-with-findings qa:rejected qa-finding discovery needs-replan; do
  gh label create "$l" --force
done
gh label create "wave:W02" --color 0E8A16 --force
gh issue create --title "[E03] Basic auth" --type Epic --label "wave:W02" --body-file body.md
gh issue create --title "[E03-T02] Login endpoint" --type Task --label "wave:W02" \
  --parent 41 --blocked-by 56 --body-file body.md
gh issue create --title "[E03-QA1] QA: Basic auth" --type Task --label "wave:W02" --label qa \
  --parent 41 --blocked-by 57 --body-file body.md
gh issue edit 57 --remove-label "wave:W01" --add-label "wave:W02"      # carried over
gh issue close 57 --reason "not planned" --comment "Dropped: <reason>"  # dropped
```

Check `gh issue create --help` for the syntax of several `--blocked-by` values, and `gh issue edit --help` for parent and dependency flags on edit; their names differ from create.

## Templates

### `01-project.md`

```markdown
# ACME: Project

## Summary
- Objective: …
- Stakeholders: …
- Success criteria: SC1 …, SC2 …
- Constraints: …
- Out of scope: …
- Source: [Business case](00-business-case.md) · Agent file: [CLAUDE.md](../CLAUDE.md)

## Open questions
1. … → spike E01-T01 | asked to user | resolved D002

## Limits
- Task: one module or ≤ 8 files, ≤ ~400 changed lines, ≤ 5 acceptance criteria.
- QA: intermediate QA when an epic has > 5 tasks or spans > 2 batches; ≤ 8 UAT scenarios per QA task.
- Recalibrated: W01 review

Next IDs: E06, D004

## Waves
| ID | Name | Goal | Status | File |
|---|---|---|---|---|
| W01 | walking-skeleton | … | done | [W01](waves/W01-walking-skeleton.md) |
| W01B | auth-foundation | … | done | [W01B](waves/W01B-auth-foundation.md) |
| W02 | user-onboarding | … | active | [W02](waves/W02-user-onboarding.md) |
| W03 | billing | … | planned | [W03](waves/W03-billing.md) |
| W04 | reporting | … | proposed | [W04](waves/W04-reporting.md) |
| W05 | admin-console | … | dropped (D004) | [W05](waves/W05-admin-console.md) |
```

### `waves/WNN-<slug>.md`

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

### E04: <name> → #52
Traces: [BC §4](../00-business-case.md#4-onboarding), SC2
One paragraph: what it covers and why it is in this wave.

#### E04-T01: <imperative title> → #57
- Kind: feature | spike | chore | fix · Executor: agent | human · State: todo
- Depends on: E03-T02 (or none) · Batch: 2
- Context: 2–4 sentences. What exists, what this adds, why. Readable without the business case.
- Traces: [BC §4.2](../00-business-case.md#42-login), D005
- Touches: `src/auth/**`, `tests/auth/**` (new: `src/auth/login.ts`)
- Contract: `POST /login {email,password} → 200 {token} | 401` (or none)
- Acceptance:
  - [ ] `pnpm test tests/auth/login.test.ts` passes (valid login, wrong password, unknown user)
  - [ ] `curl -s -XPOST localhost:3000/login -d @fixtures/ok.json` returns 200 with `token`
- Verify: `make verify`
- Out of scope: password reset, rate limiting (E04-T03)
- Fixes finding: #71 (fix tasks only)
- Steps (optional):
  - [ ] E04-T01-S1: …

#### E04-QA1: QA: <epic name> → #60
- Kind: qa · Executor: independent agent (fresh session) · State: todo · Verdict: —
- Verifies: E04-T01, E04-T02, E04-T03 · Depends on: same · Starts after: batch 2
- Blocking: no (or: yes — gates E05-T02 because it consumes the `/login` contract)
- Context: what the epic delivers for the user, in 2–3 sentences.
- Traces: [BC §4](../00-business-case.md#4-onboarding), SC2
- UAT scenarios (product manager's view, ≤ 8):
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

Brief rules:
- Every acceptance item and UAT scenario is a command with an expected result, or exact steps with an observable result. Never "works correctly".
- Tasks in the same batch must not have overlapping `Touches`; if they do, add a dependency. QA tasks have no `Touches`.
- Batches are a view of the dependency graph, not gates. A task is ready when all its blockers are closed, whatever its batch.
- QA tasks sit on their own `QA` line and never hold up a batch.
- A task that defines a shared contract goes in an earlier batch than its consumers.

### `decisions.md`

```markdown
## D003: Insert W01B (auth foundation) before W02
- Date: YYYY-MM-DD
- Trigger: W01 review | E04-T02 needs-replan | technical choice | QA waiver (user)
- Decision: …
- Why: …
- Affects: W01B (new), W02 (amended)
```

### Working agreements (written into the agent file by W01's first task)

```markdown
## Working a plan task
1. Take one ready task issue: title `[Exx-Tnn]`, not labelled `qa` or `qa-finding`, all blockers closed, label of the active wave, unassigned. Assign yourself.
2. Read the issue body and this file. Open other plan files only where the brief links to them.
3. Branch `e03-t02-<slug>`. Stay inside `Touches`; if you must leave it, say so under Deviations.
4. Run the brief's `Verify` command and every Acceptance command before opening the PR.
5. PR body: `Closes #57`; Acceptance output (pasted); Deviations; Discoveries (link `discovery` issues). A fix task's PR also says `Refs #<finding>`, never `Closes #<finding>`.
6. Tick subtasks in the issue. Never edit `plan/`.
7. If the task is wrong, blocked or too big: comment, label `needs-replan`, stop.
8. Do not wait for QA on finished work unless an open QA issue blocks yours. Take the next ready issue.

## Working a QA task
1. Start a fresh session. Take a ready `qa` issue only if this session has not written or reviewed code for the tasks it verifies. Assign yourself.
2. Read the QA brief, the verified tasks' briefs, the linked business-case sections and this file. Do not read diffs or PR discussions before testing.
3. Start the system as described in this file. Run every UAT scenario and every verified task's Acceptance on the default branch. Explore edge cases around them.
4. No commits, no PRs. Post the report: summary for the product manager, scenarios, evidence, findings, verdict, independence line.
5. Open one `Finding (E04-QA1): …` issue per finding (labels `qa-finding` + wave, sub-issue of the epic). Set the verdict label. Close the QA issue, except leave a `Blocking: yes` issue open on `rejected`.
6. Re-check: for each open `qa-finding` whose fix task is closed, re-run its reproduction, comment the evidence, and close it; if not fixed, reopen the fix task.
```

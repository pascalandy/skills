---
name: "rolling-wave-planning"
description: "Use when breaking a business case or large plan into rolling waves (Project → Wave → Epic → Task → Subtask) for coding agents, planning or running QA tasks, triaging discoveries or QA findings, reviewing a finished wave, re-planning or inserting a wave, or syncing plan/ markdown to GitHub issues."
kind: "dev"
---

# Rolling Wave Planning

This skill turns a large business case into a plan that coding agents execute one task at a time.
The plan gives full detail only for the active wave.
The planner plans the later waves again at each wave review.

## Rules

- A task brief and the agent file (`CLAUDE.md` or `AGENTS.md`) give the implementer all the content of the task. The implementer does not open `00-business-case.md`
- The plan says what to build and how the QA agent tests it. The plan does not say how to implement a task
- Do not write the word "milestone" in the plan. Do not use GitHub Milestones or GitHub Projects
- Write the plan prose in the PM's language. Keep IDs, file names, labels and commands in English

## Actors

| Actor | Who | Responsibility |
|---|---|---|
| PM | The product manager, Pascal | Approves each checkpoint. Gives the implementation instructions. Does the UAT. Is the only actor who can waive QA |
| Planner | An agent session that runs this skill | Is the only actor that edits `plan/`, always in a `plan:` commit |
| Implementer | An agent session that executes one task | Follows the task brief and the implementation instructions |
| QA agent | An agent session on the QA machine | Tests the work of each epic. Makes no commit and no PR |

- **QA machine:** the dedicated machine on which the QA agent tests. The default is the Mac Mini. If the PM names a different machine, record it in `01-project.md`
- **UAT (user acceptance test):** the PM does every UAT. The PM reads the QA reports, then decides which tests to do and how detailed they are. The plan defines no UAT scenario, no UAT task and no UAT status
- **Implementation instructions:** the PM gives them when implementation starts. Do not write a branch rule, a PR rule or an implementer procedure in `plan/`, in a brief or in the agent file

## Levels

| Level | Definition |
|---|---|
| Project | The full initiative that the business case defines |
| Wave | One goal and one result that a person can see or measure. 2 to 5 exit criteria. Target 10 to 30 tasks. Split a wave that has more than 40 tasks |
| Epic | A coherent block of work in a wave, traced to the business case. 3 to 8 tasks |
| Task | One agent session and one PR. Split a task that exceeds a task limit, or that defines and also uses a new contract |
| Subtask | An ordered step of commit size in the PR of its task. Optional. Never a separate PR |
| QA task | A test of the work of an epic by the QA agent. At most 8 QA scenarios |

The initial task limits are: one module or at most 8 files, approximately 400 changed lines, at most 5 acceptance criteria, and no open decision.
`01-project.md` records the task limits and the QA limits.

## Statuses

The status of a wave sets its detail level:

| Status | Detail |
|---|---|
| `proposed` | Goal, exit criteria and 3 to 6 scope bullets. No epics |
| `planned` | Epics, each with `Traces` and one paragraph. No tasks |
| `active` | Epics, full task briefs, QA tasks and execution order |
| `done` | Closed at the wave review, with Learnings |
| `dropped` | Kept, with a reason in one line and a decision ID |

- One wave is `active`. At most one wave is `planned`
- Waves execute in the row order of the wave table in `01-project.md`. An ID is a name, not a position
- A task has one state: `todo`, `done`, `dropped` or `carried→WNN`
- A QA task has the same states. A `done` QA task also has one verdict: `accepted`, `accepted-with-findings` or `rejected`. The first two verdicts are passing verdicts
- An epic has one state: `open` or `closed`

**Epic closure rule:** an epic closes when all these conditions are true:

1. Each task is `done` or `dropped`
2. Each QA task has a verdict
3. A later QA task with a passing verdict follows each `rejected` QA task
4. Each `qa-finding` issue is closed

Only the PM can waive QA. The planner logs each waiver as a decision.

## IDs

| Item | Format | Notes |
|---|---|---|
| Project | `ACME` | A short slug in uppercase |
| Wave | `W01`, `W02` | Always two digits. A wave added at the end takes the next free number |
| Inserted wave | `W01B`, `W01C` | The letter follows the wave that the inserted wave comes after. There is no `W01A` |
| Epic | `E01`, `E02` | Global. Independent of waves |
| Task | `E03-T01` | |
| Subtask | `E03-T01-S1` | |
| QA task | `E03-QA1`, `E03-QA2` | One sequence for each epic. It includes each intermediate QA task, each task QA and each re-QA |
| Decision | `D001` | |

1. Never renumber an ID and never use an ID again
2. A dropped item keeps its ID, takes the state `dropped` and gets a reason in one line
3. `01-project.md` has a `Next IDs:` line, such as `E12, D007`. Update the line each time you allocate an ID
4. In commits, PRs, branches and code, refer to a task as `E03-T02` without its wave, because waves change
5. A task or QA task that is not finished keeps its ID and its epic:
   - In the closed wave file, keep the task line and mark it `carried→W02`
   - In the receiving wave file, add `### E03 (continued from W01) → #41` and list only the open tasks
   - The receiving wave is the wave that becomes `active`, unless a decision names a different wave
6. A task never changes its epic. If the task must move, drop it and create a task that refers to the old ID. On GitHub, close the old issue as not planned and link the new issue

## Files

```
CLAUDE.md / AGENTS.md            # agent file: stack, layout, verify command, how to start the system
                                 # (start command, seed data, test accounts)
plan/
├── 00-business-case.md          # source document, read-only
├── 01-project.md                # summary, open questions, limits, QA machine, next IDs, wave table
├── decisions.md                 # D###: plan-structure and technical decisions
└── waves/
    ├── W01-walking-skeleton.md  # done
    ├── W01B-auth-foundation.md  # done, inserted at W01 review
    ├── W02-user-onboarding.md   # active
    ├── W03-billing.md           # planned
    ├── W04-reporting.md         # proposed
    └── W05-admin-console.md     # dropped
```

- Never delete a wave file
- Never edit the business case, so that its section anchors stay stable for `Traces`

## Pick the procedure

- To make the first plan from a business case, follow **Procedure A**
- When each implementation task of the active wave is merged, dropped or blocked, follow **Procedure B**
- When a `discovery`, `qa-finding` or `needs-replan` issue is open, follow **Procedure C**
- To do a QA task, follow [QA task](references/qa-task.md)

Before you write a plan file, read its template:

- [Project files](references/project-files.md): `01-project.md` and `decisions.md`
- [Wave file](references/wave-file.md): the wave file, the task brief, the QA brief and the brief rules

Before you write to GitHub, read [GitHub sync](references/github-sync.md).

## Procedure A: decompose the business case

1. Read the full business case
2. Write the summary in `01-project.md`: objective, stakeholders, success criteria, constraints and out of scope
   - Number the success criteria `SC1`, `SC2`
   - Give each item 1 to 3 lines and a link to its section. Do not write the business case again
3. Write `## Open questions` in `01-project.md`. Put first the question whose answer can change the plan the most
4. Turn each top question into a `spike` task in W01 or into a question to the PM
   - A spike has no PR. Its result is a recommendation on its issue, which the planner logs as a decision
5. Divide the project into 3 to 7 waves. Order them by risk and by dependency
   - W01 is a walking skeleton (a thin slice from end to end) or a test of the assumption with the highest risk
6. Write the wave table in `01-project.md`
7. Write one `proposed` file for each wave in `waves/`
8. **Checkpoint:** show the waves and the open questions to the PM. Continue only when the PM approves
9. Write W01 at `active` detail: epics with `Traces`, a full brief for each task, QA tasks and `## Execution order`
   - Plan the QA tasks as [Quality assurance](#quality-assurance) says
   - The first task of W01 writes the agent file, or brings it up to date: stack, layout, the one verify command and how to start the system
10. Write W02 at `planned` detail
11. Keep each later wave `proposed`
12. Log `D001`: the initial waves and the reason for them
13. Do the [plan checks](#plan-checks). Correct each failure, then do the checks again
14. Sync the plan to GitHub
15. Commit `plan: initial decomposition` after the sync, so that the commit includes the issue numbers

### Plan checks

- Each task is in the task limits
- Each acceptance item is a command or a step with a result that a person can see
- Each brief obeys the brief rules in [Wave file](references/wave-file.md)
- Each epic has a final QA task, and its QA scenarios come from its `Traces`
- Each QA task with `Blocking: yes` gives its reason
- The exit criteria of at least one wave cover each success criterion
- Each epic of the active wave has `Traces`
- Only the active wave has tasks
- The word "milestone" is not in the plan
- No plan file and no brief has an implementation instruction or a UAT scenario

## Procedure B: review a wave

Start the review when each implementation task is merged, dropped or blocked. Do not wait for the QA tasks.

1. Get the issue states from GitHub: `gh issue list --label wave:W01 --state all --limit 500 --json number,title,state,stateReason,labels`
2. Write the task states and the QA verdicts in the wave file
3. Give each task one state: `done`, `dropped` with a reason, or `carried→WNN`
   - Carry each QA task that has no verdict, together with its epic (ID rule 5)
4. Tell the QA agent to check the exit criteria in a session that has no implementation context from this wave
   - The QA agent marks each criterion as met or not met, with evidence, below `## Exit criteria`
5. Set the wave to `done`, also when a criterion is not met
   - Each criterion that is not met becomes a carried task or a discovery
6. Write `## Learnings` in the closed wave file
7. Put each discovery in one bucket. The discoveries come from the open `discovery`, `needs-replan` and `qa-finding` issues, from `## Discoveries` and from Learnings

   | Bucket | Condition | Action |
   |---|---|---|
   | (a) | The discovery agrees with the goal of the next wave | Amend the next wave. This bucket is the default |
   | (b) | The discovery is a separate block that must come first, such as a foundation or an architecture correction | Insert a wave, such as `W01B`. Use this bucket only if (a) weakens the goal of the next wave |
   | (c) | The discovery belongs to a later wave | Add it to the scope of a later wave, or add a wave at the end |
   | (d) | The discovery makes a later wave invalid | Drop that wave, or merge it into a different wave |

8. Set the next wave in table order to `active`, and the wave after it to `planned`
9. Write the new active wave in full: briefs, QA tasks, execution order and carried tasks
10. Do the [plan checks](#plan-checks)
11. Write the epics of the new planned wave. Adjust the `proposed` waves in outline only
12. Add `## Changes since original plan` to each wave that changed: the change, the reason and the decision ID
13. Log one decision for each change to the plan structure
14. Set the task limits and the QA limits again from the PR sizes and the rejection rate of the closed wave
15. Update the wave table and `Next IDs` in `01-project.md`
16. **Checkpoint:** show the PM the QA verdicts, the open findings, the criteria that are not met and the changes to the plan structure. Continue only when the PM approves
17. Sync the plan to GitHub. Close each epic issue that meets the epic closure rule
18. Commit, for example `plan: review W01, insert W01B, amend W02`

## Procedure C: triage during a wave

An implementer never adds scope without a report and never edits `plan/`.
When a task shows something that the plan did not include, one of these cases applies:

| Case | Result |
|---|---|
| The work is in the scope of the task and changes no contract | The implementer does the work and reports it in the PR |
| The work is new, agrees with the wave goal and has no effect on other tasks | The implementer opens an issue with the labels `discovery` and the active wave. No agent executes it before triage |
| The work changes a contract, makes a different task invalid or exceeds the task limits | The implementer stops, comments on the issue and adds the label `needs-replan` |

For each `needs-replan` issue, the planner amends the wave file and logs a decision, or defers the issue to the wave review.

For each open `discovery` or `qa-finding` issue that has no task, the planner does these steps:

1. If the wave would exceed 40 tasks, defer the issue to the wave review and stop
2. Add a task to the active wave file, with the next free task ID in the epic
3. Add the task to the `Verifies` line of an open QA task of that epic. If the epic has no open QA task, create the next QA task
4. Sync the plan to GitHub
5. Commit `plan: triage`

## Quality assurance

Each task has `Acceptance` and `Verify` commands that its implementer runs, and CI runs.
Those checks are not QA.
QA is a test by the QA agent, on the QA machine, with no implementation context.
QA is not UAT: see [Actors](#actors).

### Which QA tasks to plan

- **For each epic (default):** a final QA task tests all the tasks of the epic against its `Traces`. It starts when the last task of the epic is merged
- **Intermediate:** when an epic has more than 5 tasks or more than 2 batches, add a QA task after its first slice that a user can see
- **For one task (exception):** add a QA task with `Verifies: E04-T03` and the title `QA: <task title>` only for high risk. High risk is a shared contract, security, a data migration, money or a change that cannot be reversed
- Do not let all the epics end in the last batch, so that the QA tasks do not all start at the end of the wave
- For an enabler epic (infrastructure or tooling), the user is the next developer or agent that uses its result
- For a spike epic, the QA task checks that the answer resolves the open question

### Independence

- The QA agent is a new session or subagent that has no implementation context for the tasks that it tests. It can be the same model
- A session that wrote or reviewed code for a task must not do the QA of that task
- The QA report records the independence, because a shared GitHub account cannot prove it

### Blocking

- A QA task is `blocked by` the tasks that it tests. It starts when they are merged
- By default, no task depends on a QA task (`Blocking: no`). Later tasks, epics and batches continue while the QA agent tests
- Set `Blocking: yes` only when work without a passing verdict is expensive to reverse, and give the reason. The permitted reasons are:
  - A later task uses a contract or schema that the QA task tests
  - The work includes security, possible data loss, money or a migration that cannot be reversed
  - A release or a deployment follows
- Add a blocking QA task as a `blocked by` dependency only on the tasks that it gates, never on a full wave
- A blocking QA issue closes only on a passing verdict. On `rejected`, it stays open with the label `qa:rejected`. The planner closes it when the re-QA passes
- QA gates only the closure of an epic. It never gates the wave review

### Findings and verdicts

The verdict of a QA task is:

- `rejected` if a QA scenario fails, if an Acceptance of a tested task fails on the default branch, or if a traced success criterion is not met
- `accepted-with-findings` if each scenario passes and each finding is cosmetic or an edge case
- `accepted` in all other cases

These rules apply to each finding:

1. A finding is an issue named `Finding (E04-QA1): <title>`. It has the labels `qa-finding` and the active wave, and is a sub-issue of the epic. It gives the steps to reproduce, the expected result and the actual result
2. The planner creates one fix task for each finding in Procedure C. The fix task has `Fixes finding: #71`, and its Acceptance includes the reproduction
3. Only the QA agent closes a finding, after the reproduction passes on the default branch
4. After `accepted-with-findings`, that check is sufficient
5. After `rejected`, the planner also adds a re-QA task with the next free QA ID. Its `Verifies` line lists the fix tasks and the failed scenarios. It is blocking only if the rejected QA task was blocking
6. After two `rejected` verdicts in sequence on one epic, the planner stops, adds the label `needs-replan` to the epic and asks the PM
7. A finding that changes the scope or a contract is a `needs-replan` case of Procedure C

---
name: "rolling-wave-planning"
description: "Use when breaking a business case or large plan into rolling waves (Project → Wave → Epic → Task → Subtask) for coding agents, planning or running QA tasks, triaging discoveries or QA findings, reviewing a finished wave, re-planning or inserting a wave, or syncing plan/ markdown to GitHub issues."
kind: "dev"
version: "3.0.0"
---

# Rolling Wave Planning

This skill turns a large business case into a plan that coding agents execute one task at a time.
The plan gives full detail only for the active wave.
The planner plans the later waves again at each wave review.

## Actors

| Actor | Who | Responsibility |
|---|---|---|
| PM | The product manager, Pascal | Approves each checkpoint. Gives the implementation instructions. Does the UAT. Can waive QA |
| Planner | An agent session that runs this skill | Is the only actor that edits `plan/`, always in a `plan:` commit |
| Implementer | An agent session that executes one task | Follows the task brief and the implementation instructions |
| QA agent | An agent session on the QA machine | Tests the work of each epic. Makes no commit and no PR |

- **QA machine:** the dedicated machine on which the QA agent tests. The default is the Mac Mini. If the PM names a different machine, record it in `01-project.md`
- **UAT (user acceptance test):** the PM does every UAT. The PM reads the QA reports, then decides which tests to do and how detailed they are. The plan defines no UAT scenario, no UAT task and no UAT status
- **Implementation instructions:** the PM gives them when implementation starts. Do not write a branch rule, a PR rule or an implementer procedure in `plan/`, in a brief or in the agent file
- **Signals:** the procedures read these six signals. The implementation instructions of the PM must produce them:
  - A finished task closes its issue. A task is finished when its PR is merged or, for a task without a PR, when its result is on its issue
  - A PR and its branch refer to the task by its ID (ID rule 4)
  - A fix PR does not close its finding
  - The implementer reports work that the plan did not include, as [Procedure C](#procedure-c-triage-during-a-wave) says
  - Before the work starts, the executor of a task or QA task runs each `check` of the `needs` in its brief. If a `check` fails, the executor stops, comments the command and its output on the issue, and adds the label `0-impediment`
  - Agents start a wave only after the planner reports `agent_ready: true` for it ([Hand off a wave](#hand-off-a-wave))

## Rules

- A brief is the full definition of a task in the wave file. The brief and the agent file (`CLAUDE.md` or `AGENTS.md`) give the implementer all the content of the task. The implementer does not open `00-business-case.md`
- The plan says what to build and how the QA agent tests it. The plan does not say how to implement a task: see [Actors](#actors)
- Do not write the word "milestone" in the plan. Do not use GitHub Milestones or GitHub Projects
- Write each epic entry and each brief in English with the `asd-ste100` skill, because GitHub issues get this text. Write the other plan prose in the PM's language
- Keep IDs, file names, labels and commands in English

## Levels

| Level | Definition |
|---|---|
| Project | The full initiative that the business case defines |
| Wave | One goal and one result that a person can see or measure. 2 to 5 exit criteria. Target 10 to 30 tasks. Split a wave that has more than 40 tasks |
| Epic | A block of work in a wave that gives one outcome. Its name is that outcome in plain words. Its `Traces` line links it to sections of the business case. Its `Problem (CMO)` line gives the current mode of operation, and its `Outcome (FMO)` line gives the future mode of operation. 3 to 8 tasks |
| Task | One agent session and one PR. Split a task that exceeds a task limit, or that defines and also uses a new contract |
| Subtask | An ordered step of commit size in the PR of its task. Optional. Never a separate PR |
| QA task | A test of the work of an epic by the QA agent. At most 8 QA scenarios |

The initial task limits are: one module or at most 8 files, approximately 400 changed lines, at most 5 acceptance items, and no open decision.
`01-project.md` records the task limits and the QA limits.

**Executor:** each wave, epic and task has one executor:

- `agent`: an agent session does the work. A QA task counts as `agent`
- `human`: the PM or a different person does the work
- `tbd`: the PM wants the work, but nobody knows how to do it yet

1. A brief has `agent` or `human`, never `tbd`. A `tbd` wave or epic stops the [hand-off](#hand-off-a-wave) of its wave until the planner resolves it, for example with a spike or a human task
2. A wave or an epic that has a human task is `human`
3. A human task blocks each task that names it in `blocked_by`. It also blocks its wave: agents start a wave only when each human task of the wave is `done` or `dropped`. Thus, a human task that needs agent work of its wave goes to a later wave

## Statuses

The status of a wave sets its detail level:

| Status | Detail |
|---|---|
| `proposed` | Goal, exit criteria and 3 to 6 scope bullets. No epics |
| `planned` | Epics, each with `Traces`, `Problem (CMO)` and `Outcome (FMO)`. No tasks |
| `active` | Epics, full task briefs with their graph blocks, and QA tasks |
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
| QA task | `E03-QA1`, `E03-QA2` | One sequence for each epic, for all its QA tasks |
| Decision | `D001` | |

1. Never renumber an ID and never use an ID again
2. A dropped item keeps its ID, takes the state `dropped` and gets a reason in one line
3. `01-project.md` has a `Next IDs:` line, such as `E12, D007`. Update the line each time you allocate an ID
4. Waves change. Thus, in commits, PRs, branches and code, refer to a task as `E03-T02`, without its wave
5. A task or QA task that is not finished keeps its ID and its epic:
   - In the closed wave file, keep the task line and mark it `carried→W02`
   - In the receiving wave file, add `### E03 (continued from W01) → #41` and list only the open tasks
   - The receiving wave is the wave that becomes `active`, unless a decision names a different wave
6. A task never changes its epic. If the task must move, drop it and create a task that refers to the old ID. In each `blocked_by` and `verifies` that names the old ID, write the new ID. On GitHub, close the old issue as not planned and link the new issue

## Files

```
CLAUDE.md / AGENTS.md            # agent file: stack, layout, `just check`, how to start the system
                                 # (start command, seed data, test accounts)
plan/
├── 00-business-case.md          # source document, read-only
├── 01-project.md                # summary, open questions, limits, QA machine, next IDs, wave table
├── decisions.md                 # D###: plan-structure and technical decisions
├── qa.md                        # QA playbook: requirements, environments, ordered QA steps
└── waves/
    ├── W01-walking-skeleton.md  # done
    ├── W01B-auth-foundation.md  # done, inserted at W01 review
    ├── W02-user-onboarding.md   # active
    ├── W02-user-onboarding.graph.json  # dependency graph of W02, written by the graph script
    ├── W03-billing.md           # planned
    ├── W04-reporting.md         # proposed
    └── W05-admin-console.md     # dropped
```

- Never delete a wave file
- Never edit a `.graph.json` file. The graph blocks of the briefs are its source
- Never edit the business case, so that its section anchors stay stable for `Traces`

## Pick the procedure

- To make the first plan from a business case, follow **Procedure A**
- When each task of the active wave is finished, dropped, stopped by a `needs-replan` or `0-impediment` label, or blocked by a stopped task or by a QA task, follow **Procedure B**. Do not wait for the QA tasks
- When a `discovery`, `qa-finding` or `needs-replan` issue is open, follow **Procedure C**
- To do a QA task, or to check again a finding that has the label `qa-recheck`, follow [QA task](references/qa-task.md)

Before you write a plan file, read its template:

- [Project files](references/project-files.md): `01-project.md`, `decisions.md` and `qa.md`
- [Wave file](references/wave-file.md): the wave file, the task brief, the QA brief, the graph block and the brief rules

Before you write the plan to GitHub or read issue states from GitHub, read [GitHub sync](references/github-sync.md).

## Procedure A: decompose the business case

1. Read the full business case
2. Write the summary in `01-project.md`: objective, stakeholders, success criteria, constraints and out of scope
   - Number the success criteria `SC1`, `SC2`
   - Give each item 1 to 3 lines and a link to its section. Do not write the business case again
   - Write the requirements of `qa.md` from each applicable section of the business case ([QA playbook](#maturity-checkpoints))
3. Write `## Open questions` in `01-project.md`. Order the questions by how much each answer can change the plan, largest change first
4. For each question whose answer can change the waves, write a `spike` task in W01 or ask the PM
   - A spike is a task that answers a question. It has no PR
   - The result of a spike is a recommendation on its issue. The planner logs the recommendation as a decision
5. Divide the project into 3 to 7 waves. Order them by risk and by dependency
   - W01 is a walking skeleton (a thin slice from end to end) or a test of the assumption with the highest risk
6. Write the wave table in `01-project.md`
7. Write one `proposed` file for each wave in `waves/`, with its `executor`
8. **Checkpoint:** show the PM the waves, each wave `executor` that is `human` or `tbd`, the open questions and the signals of [Actors](#actors). Continue only when the PM approves
9. Write W01 at `active` detail: epics with `Traces` and `Executor`, a full brief with its graph block for each task, and QA tasks
   - Plan the QA tasks as [Quality assurance](#quality-assurance) says
   - Add the tasks and the scope bullets of the [maturity checkpoints](#maturity-checkpoints)
10. Write W02 at `planned` detail
11. Keep each later wave `proposed`
12. Log `D001`: the initial waves and the reason for them
13. Do the [plan checks](#plan-checks). Correct each failure, then do the checks again
14. Sync the plan to GitHub
15. Commit `plan: initial decomposition` after the sync, so that the commit includes the issue numbers
16. [Hand off](#hand-off-a-wave) W01

### Plan checks

Check each item that applies to the change. Correct each failure, then check again.
Report one line with only the IDs that you checked, such as `RWP: Pass: RWP_01–RWP_17 · n/a: RWP_18`. Add `Fail:` with each ID that still fails. Never report a voided ID.

- [ ] **RWP_01 PM boundaries** (§Actors, §Rules): No plan file, brief or agent file has an implementation instruction or a UAT scenario. The word "milestone" is not in the plan. Each epic entry and each brief is in English, written with `asd-ste100`
- [ ] **RWP_02 Task limits** (§Levels): Each task is in the task limits of `01-project.md`
- [ ] **RWP_03 Brief rules** (§Rules): Each brief obeys the brief rules in [Wave file](references/wave-file.md)
- [ ] **RWP_04 Epic outcome** (§Levels): For each epic of the active wave, if each task of the epic that is not `dropped`, in all waves, is done, the `Outcome (FMO)` of the epic is true. Each epic of the active wave has `Traces`
- [ ] **RWP_05 Executor** (§Levels): No brief has `tbd`. A wave file with `skill_version` 3.0.0 or later gives the `Executor` of the wave, of each epic entry and of each brief
- [ ] **RWP_06 Detail by status** (§Statuses): Each wave has the detail of its status. Only the active wave has tasks. One wave is `active`, and at most one wave is `planned`
- [ ] **RWP_07 IDs** (§IDs): No ID is renumbered or used again. `Next IDs` is current. Each carried task obeys ID rule 5
- [ ] **RWP_08 Files** (§Files, §Pick the procedure): No wave file is deleted, no graph file is edited by hand, and the business case is unchanged. Each plan file follows its template
- [ ] **RWP_09 Success criteria** (§Procedure A): The exit criteria of at least one wave cover each success criterion
- [ ] **RWP_10 Graph** (§Dependency graph): [The graph script](#dependency-graph) answers `{"ok":true,…}` for the active wave file, and the graph file is committed with it
- [ ] **RWP_11 Wave review** (§Procedure B): Each carried task and each discovery has a verdict with its evidence in the closed wave file. Each changed wave has `## Changes since original plan` with a decision ID
- [ ] **RWP_12 Hand-off** (§Hand off a wave): The PM saw each unresolved item. No agent starts the wave before `agent_ready: true`
- [ ] **RWP_13 Triage** (§Procedure C): Each triage task has its QA, and the active wave has at most 40 tasks
- [ ] **RWP_14 QA coverage** (§Quality assurance, §Which QA tasks to plan): Each epic has a final QA task. Its QA scenarios come from the `Traces` of the epic, and at least one goes through more than one task
- [ ] **RWP_15 Independence** (§Independence): The executor of each QA brief is the QA agent on the QA machine
- [ ] **RWP_16 Blocking QA** (§Blocking): Each QA task in a `blocked_by` has a permitted reason in `why`, and no QA task blocks a full wave
- [ ] **RWP_17 Findings** (§Findings and verdicts): Each open finding has a fix task with `Fixes finding`. Each `rejected` QA task has a re-QA task
- [ ] **RWP_18 CI baseline** (§Maturity checkpoints): The first task of W01 is the CI baseline, or a decision logs the waiver of the PM. Each agent task after it is `blocked_by` it and has `just check` in `Verify`
- [ ] **RWP_19 Maturity review** (§Maturity checkpoints): Each checkpoint whose trigger is true has its task, or a decision logs the waiver of the PM. Until its trigger is true, the verification loop is a scope bullet of a `proposed` wave
- [ ] **RWP_20 QA playbook** (§Maturity checkpoints): For each `FR-NN` and `NFR-NN` that an epic of the active wave traces, a QA scenario cites the ID, or a decision logs the waiver of the PM
- [ ] **RWP_21 Traps** (§Traps): Each `Traps` line has the form `Want: … Not: …` and names an effort sink inside the deliverable
- [ ] **RWP_22 Version** (§Version): Each new wave file records the current skill version in `skill_version`

IDs never change and are never used again. To change the meaning of an item, move its line under `#### Voided` with `void <date>, replaced by RWP_NN`. Give the new item the next free ID.

### Dependency graph

The dependency graph of a wave is in two places:

- **Source:** the graph block at the end of each brief in the wave file. Only the planner writes it, as [Wave file](references/wave-file.md) says
- **Graph file:** `plan/waves/<wave file name>.graph.json`, beside the wave file. The graph script writes it from the graph blocks. It gives the full graph of the wave in one file:

  | Key | Content |
  |---|---|
  | `nodes` | Each graph block, with its `kind` (`task` or `qa`) and its `state` |
  | `edges` | Each blocker as `{"from": "E03-T02", "to": "E04-T01", "why": "…"}`. The `why` of a `verifies` edge is `verifies` |
  | `batches` | The IDs that can run at the same time, in execution order |
  | `gates` | For each blocking QA task, the tasks that it blocks |

The graph script needs `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/)); confirm it with `uv --version`. Run it after each change to a brief, and commit the graph file with the wave file:

```bash
uv run <this-skill-folder>/scripts/plan_graph.py plan/waves/W02-user-onboarding.md
```

- It answers `{"ok":true,"file":"…"}`, with `changes` when it wrote the graph file
- It fails and writes nothing when a brief has no valid graph block, an ID is unknown or dropped, the graph has a cycle, two parallel tasks that are `todo` have a common path in `touches`, or an `Executor` breaks a rule of [Levels](#levels). The last line of stderr lists each error with its correction. Correct the wave file and run it again
- With `--check`, it writes nothing and fails when the graph file does not match the briefs
- With `--hitl plan/waves`, it writes nothing and answers each wave with its `executor`, its `unresolved` items and `agent_ready`. It fails on an `Executor` that the graph check rejects. An unresolved item is a human task that is not `done` or `dropped`, or a `tbd` item. It ignores a `carried→WNN` task, because the receiving wave has its copy
- A wave file with `skill_version` 3.0.0 or later must give each `Executor`. In an older wave file, the script reports a missing wave or epic `Executor` as `unknown`

## Procedure B: review a wave

1. Get the issue states from GitHub: `gh issue list --label wave:W01 --state all --limit 500 --json number,title,state,stateReason,labels`
2. Write the task states and the QA verdicts in the wave file
3. Give each task one state: `done`, `dropped` with a reason, or `carried→WNN`
   - Carry each QA task that has no verdict, together with its epic (ID rule 5)
4. Ask the PM to start a QA agent session on the QA machine, with the path of the wave file
   - The QA agent has no implementation context from this wave
   - The QA agent checks each exit criterion and reports it as met or not met, with evidence
   - The PM gives the report to the planner. The planner writes the results below `## Exit criteria`
5. Set the wave to `done`, including when a criterion is not met
   - Each criterion that is not met becomes a carried task or a discovery
6. Write `## Learnings` in the closed wave file
7. Compare each carried task and each discovery with the default branch, and give it one verdict. A discovery is work that the plan did not include
   - The discoveries come from the open `discovery`, `needs-replan` and `qa-finding` issues, from `## Discoveries` and from Learnings
   - Write each verdict and its evidence in the closed wave file
   - Do the plan action now. Do the GitHub action only at the sync, after the PM approves

   | Verdict | Evidence | Plan action | GitHub action |
   |---|---|---|---|
   | Holds | The current files still need the work | None | None |
   | Fixed | A merged PR or a commit on the default branch does the work | Set a carried task to `done` | Close the issue as completed, and cite the change |
   | Gone | The problem does not occur, and no change fixed it | Set a carried task to `dropped` | Close the issue as not planned, and cite the proof |
   | Stale | The current files still need the work, but the brief or the issue quotes code that changed | Write the brief of the item from the current files | None |

   - Exception: do not close a `qa-finding` issue that has the verdict Fixed or Gone. At the sync, comment the evidence on it and add the label `qa-recheck`
   - The QA agent runs the reproduction of each `qa-recheck` finding and closes it (finding rule 3). If the epic of the finding has no open QA task, ask the PM to start a QA agent session for the recheck

8. Put each discovery that has the verdict Holds or Stale in one bucket

   | Bucket | Condition | Action |
   |---|---|---|
   | (a) | The discovery agrees with the goal of the next wave | Amend the next wave. This bucket is the default |
   | (b) | The discovery is a separate block that must come first, such as a foundation or an architecture correction | Insert a wave, such as `W01B`. Use this bucket only if (a) weakens the goal of the next wave |
   | (c) | The discovery belongs to a later wave | Add it to the scope of a later wave, or add a wave at the end |
   | (d) | The discovery makes a later wave invalid | Drop that wave, or merge it into a different wave |

9. Set the next wave in table order to `active`, and the wave after it to `planned`
10. Do the [maturity checkpoints](#maturity-checkpoints)
11. Write the new active wave in full: briefs with their graph blocks, QA tasks and carried tasks
12. Do the [plan checks](#plan-checks)
13. Write the epics of the new planned wave
    - Adjust the `proposed` waves in outline only
14. Add `## Changes since original plan` to each wave that changed: the change, the reason and the decision ID
15. Log one decision for each change to the plan structure
16. Set the task limits and the QA limits again from the PR sizes and the rejection rate of the closed wave
17. Update the wave table and `Next IDs` in `01-project.md`
18. **Checkpoint:** show the PM the QA verdicts, the open findings, the criteria that are not met, the verdicts of step 7 and the changes to the plan structure. Continue only when the PM approves
19. Sync the plan to GitHub. Close each epic issue that meets the epic closure rule, and do the actions of step 7
20. Commit, for example `plan: review W01, insert W01B, amend W02`
21. [Hand off](#hand-off-a-wave) the new active wave

## Hand off a wave

Do this procedure before agents start a wave.

1. Get the issue states of the wave, as step 1 of Procedure B says. Get each carried task by the issue number of its heading (`→ #NN`)
2. Write the states in the wave file. Run the graph script, and commit the change, such as `plan: hand off W02`
3. Run `uv run <this-skill-folder>/scripts/plan_graph.py --hitl plan/waves`
4. If the wave has `agent_ready: false`, show the PM its unresolved items by ID, and stop
5. When the PM closes a human task, or when you resolve a `tbd` item, do this procedure again from step 1
6. When the wave has `agent_ready: true`, tell the PM that agents can start the wave

## Procedure C: triage during a wave

An implementer never adds scope without a report and never edits `plan/`.
When a task shows something that the plan did not include, one of these cases applies:

| Case | Result |
|---|---|
| The work is in the scope of the task and changes no contract | The implementer does the work and reports it in the PR |
| The work is new, agrees with the wave goal and has no effect on other tasks | The implementer opens an issue that gives the task ID, with the labels `discovery` and the active wave. No agent executes it before triage |
| The work changes a contract, makes a different task invalid or exceeds the task limits | The implementer stops, comments on the issue and adds the label `needs-replan` |

Before the planner changes the wave file in this procedure, the planner gets the issue states of the wave from GitHub, as step 1 of Procedure B says, and writes the state of each task in the wave file, including a task that is open again. Thus the graph script does not compare a new task with finished work.

For each `needs-replan` issue, the planner amends the wave file and logs a decision, or defers the issue to the wave review.

For each open `discovery` or `qa-finding` issue that has no task, the planner does these steps:

1. If the wave would exceed 40 tasks, defer the issue to the wave review and stop
2. Add a task to the active wave file, with the next free task ID of its epic
   - For a `discovery` issue, the epic is the epic of the task that reported the issue
   - For a `qa-finding` issue, the epic is the parent of the issue
3. Give the task its QA:
   - For a `discovery` issue, add the task to the `verifies` of an open QA task of that epic. If that epic has no open QA task, create the next QA task
   - For a `qa-finding` issue, obey rules 4 and 5 of [Findings and verdicts](#findings-and-verdicts)
4. Do the [plan checks](#plan-checks) on the new task and on each QA brief that changed
5. Sync the plan to GitHub
6. Commit `plan: triage`

## Quality assurance

The implementer and CI run the `Acceptance` and `Verify` commands of each task.
Those checks are not QA.
QA is a test by the QA agent, on the QA machine, with no implementation context.
QA is not UAT: see [Actors](#actors).

### Which QA tasks to plan

- **For each epic (default):** a final QA task tests all the tasks of the epic against the `Traces` of the epic. The final QA task starts when the last task of the epic is finished
  - At least one QA scenario of the final QA task goes through more than one task. The acceptance items of one task alone do not cover that scenario
- **Intermediate:** when an epic has more than 5 tasks or more than 2 batches, add a QA task after its first slice that a user can see
- **For one task (exception):** only for high risk, add a QA task with `"verifies": ["E04-T03"]` and the title `QA: <task title>`
  - High risk is a shared contract, security, a data migration, money or a change that cannot be reversed
- Do not let all the epics end in the last batch, so that the QA tasks do not all start at the end of the wave
- For an enabler epic (infrastructure or tooling), the user is the next developer or agent that uses its result
- For a spike epic, the QA task checks that the answer resolves the open question

### Independence

- The QA agent is a new session on the QA machine, with no implementation context for the tasks that it tests. It can be the same model
- A session that wrote or reviewed code for a task must not do the QA of that task
- The QA report records the independence, because a shared GitHub account cannot prove it

### Blocking

- A QA task is `blocked by` the tasks that it tests. It starts when they are finished
- By default, no task names a QA task in its `blocked_by`. Later tasks, epics and batches continue while the QA agent tests
- A QA task is blocking when a task names it in `blocked_by`. Add it only to the tasks for which work without a passing verdict is expensive to reverse, never to a full wave, and give the reason in `why`. Name only a QA task that is open or that has a passing verdict. The permitted reasons are:
  - A later task uses a contract or schema that the QA task tests
  - The work includes security, possible data loss, money or a migration that cannot be reversed
  - A release or a deployment follows
- A blocking QA issue closes only on a passing verdict. On `rejected`, it stays open with the label `qa:rejected`. The planner closes it when a later QA task has a passing verdict
- A QA task never gates the wave review

### Findings and verdicts

The verdict of a QA task is:

- `rejected` if a QA scenario fails, if an acceptance item or the `Verify` command of a tested task fails on the default branch, or if a traced success criterion is not met
- `accepted-with-findings` if each scenario passes and each finding is cosmetic or an edge case
- `accepted` in all other cases

These rules apply to each finding:

1. A finding is an issue named `Finding (E04-QA1): <title>`. It has the labels `qa-finding` and the active wave, and is a sub-issue of the epic. It gives the steps to reproduce, the expected result and the actual result
2. The planner creates one fix task for each finding in Procedure C. The fix task has `Fixes finding: #71`, and its acceptance items include the reproduction
3. Only the QA agent closes a finding, after the reproduction passes on the default branch
4. After `accepted-with-findings`, the reproduction check of rule 3 is sufficient
5. After `rejected`, the planner also adds one re-QA task for the rejected QA task. A re-QA task is a QA task with the next free QA ID
   - The `verifies` of the re-QA task lists the fix tasks. Its `QA scenarios` include the failed scenarios
   - If the rejected QA task was blocking, the re-QA task replaces it in each `blocked_by` that names it
6. After two `rejected` verdicts in sequence on one epic, the planner stops, adds the label `needs-replan` to the epic and asks the PM
7. If a finding changes the scope or a contract, it is a `needs-replan` case of Procedure C

## Maturity checkpoints

Do these checkpoints in Procedure A and at each wave review. A checkpoint whose trigger is true adds its task, unless the PM waives it. Log each waiver as a decision.

- **CI baseline** (always, the first task of W01): a chore task writes the agent file, a `justfile` and a lefthook pre-commit configuration. Examples: the `justfile` of pascalandy/skills and of pascalandy/mixtape
  - `just check` is the one CI command. `just signoff` refuses a dirty tree, runs `just check` on the pushed HEAD, and posts a green status with `gh signoff`
  - Each pre-commit hook calls a `just` recipe. Each recipe is one line. The logic is in scripts
  - Each agent task after the CI baseline is `blocked_by` it. Its `Verify` is `just check`, with task-specific proof when necessary. The CI baseline task and the human tasks use task-specific proof
- **CI mature** (optional: when `just check` is slow, or the project has more than one contributor or makes releases, the PM chooses): `just check` selects its checks from the changed files, and `--only NAME` runs one check. `just merge` squash-merges a PR only at the head SHA that has a green signoff. Add a GitHub Actions runner only for a mature private repository with more than one contributor or with releases
- **Verification loop** (once, when the checkout builds and starts as-is, and one real user journey can be driven end to end): a chore task runs `create-verification-skill`. Until then, keep a placeholder scope bullet in a `proposed` wave. After that, when a wave changes the feature map, a user journey, the launch or the harness, add a task that runs `maintain-verification-skill`
- **QA playbook** (always): `plan/qa.md` holds the requirements, the environments and the ordered QA steps, as [Project files](references/project-files.md) says. At each wave review, update it from the QA reports

## Traps

A trap is work inside the deliverable that uses effort but adds no value. When a task has a probable trap, name it in the `Traps` line of the brief. Avoid these planner traps:

- Want: a task that stops when its acceptance items pass. Not: a task that polishes a detail without value
- Want: a late human task, such as an approval before a deploy, in the next wave. Not: that task in the active wave, where it stops all agents

## Version

The `version` in the frontmatter of this file changes with the skill. Its first number changes when the format of a brief changes. Each wave file records the version in `skill_version` when the planner creates the file.

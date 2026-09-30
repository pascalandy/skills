---
description: space-sdlc
---

# space-sdlc

Set up a structured, role-based `$herdr` workspace around this chat following the classic Software Development Life Cycle (SDLC).

## Purpose

This workspace enforces a disciplined, resource-efficient Software Development Life Cycle (SDLC) focused on executing coding tasks.

## Invariants

- Chat is the sole orchestrator and the only agent that communicates with the user.
- Target Herdr resources strictly by returned IDs, never by displayed names or sidebar order.
- Maintain one writer per file or worktree.
- Enforce the cost hierarchy: CI/QA automated gates are fast and cheap; independent Reviews are costly reasoning activities. Always gate Reviewers behind green CI and QA.
- Reviewers are strictly independent, read-only code inspectors. They **never** run CI/QA suites and **never** edit files. Repairs are routed to Builders.
- Panes exist in two states: **Launched** (harness running, ready) or **Standby** (plain shell, no harness running). At kickoff, only Chat and Planner are launched; all other panes are standby.
- Never name panes after harness engines (`pi`, `codex`, `claude`). Standby panes use plain role names; active panes use the dynamic SDLC naming standard.
- Resolve every agent launch via `Role` → `Profile` → `(Harness, Model, Thinking)`. User overrides always take precedence.

## Bootstrap inspection

1. Verify `HERDR_ENV=1`. Stop if not running inside Herdr.
2. Read the Herdr skill and inspect installed CLI help (`codex --help`, `pi --help`).
3. Verify model availability (`pi --list-models`). Never substitute a model or thinking level implicitly.
4. Inspect existing workspace names with `herdr workspace list`.
5. Choose an unused short fruit name and rename the workspace to it using its ID.
6. Do not infer the project or task name before the user provides substantive instructions.

## Workspace naming

1. **Bootstrap**: Use the temporary unique fruit name.
2. **First task**: Derive a concise, descriptive workspace name from the user's brief and rename immediately by ID.
3. **Substantial task pivot**: Rename the workspace to reflect the updated focus.

## Dynamic Pane Naming Convention

Pane names must reflect live operational status rather than harness engines:

1. **Standby state**: Plain role name (`Builder 1`, `Builder 2`, `Builder 3`, `Researcher`, `CI`, `QA`, `Docs`, `Committer`, `Reviewer 1`, `Reviewer 2`).
2. **Active state (during execution)**:
   - The Planner assigns dynamic pane names for every subtask in its plan.
   - Chat renames the pane in Herdr at the moment of harness start/task kickoff:
     `<phase>/<total-phases>-<role-prefix><index>-<kebab-keyword>`

| Role                | Prefix | Standby Name   | Active Example               |
| :------------------ | :----- | :------------- | :--------------------------- |
| Builder 1, 2, 3     | `bld`  | `Builder 1`    | `1/5-bld1-auth-route`        |
| Researcher          | `res`  | `Researcher`   | `1/5-res-oauth-spec`         |
| CI                  | `ci`   | `CI`           | `2/5-ci-test-suite`          |
| QA                  | `qa`   | `QA`           | `2/5-qa-login-flow`          |
| Reviewer 1, 2       | `rev`  | `Reviewer 1`   | `3/5-rev1-sec-audit`         |
| Docs                | `doc`  | `Docs`         | `4/5-doc-auth-api`           |
| Committer           | `cmt`  | `Committer`    | `5/5-cmt-signed-commit`      |

## Initial layout

At kickoff, create four tabs: `Chat 💬`, `Workers 🛠`, `QA 🧪`, `Reviewers ✅`.
- **Launched** (2 panes): `Chat` and `Planner` (Tab 1).
- **Standby** (10 panes): `Builder 1..3`, `Researcher` (Tab 2); `CI`, `QA`, `Docs`, `Committer` (Tab 3); `Reviewer 1..2` (Tab 4).

## Agent profiles

### Role Assignments

These role assignments are defaults. Chat has full authority to create, customize, scale, or repurpose agents and roles as needed. Include this canonical roster in every planning brief:

- **Planner**: Planning, architecture, task breakdown, phase & pane naming
  - Profile: `ds-pro-v4`
- **Builder**: Implementation, targeted code edits, and single-file unit tests
  - Profile: `gemini-flash`
- **Reviewer**: Independent read-only code quality, security, and correctness review
  - Profile: `ds-pro-v4`
- **CI**: Automated repo test suites, linters, typechecks, and build scripts
  - Profile: `gpt-luna`
- **Docs**: Documentation, technical notes, API guides, and reference updates
  - Profile: `ds-flash-v4`
- **Researcher**: Codebase discovery, external API exploration, and docs lookup
  - Profile: `ds-flash-v4`
- **QA**: Functional validation, user-journey verification, UI/browser automation
  - Profile: `gpt-luna`
- **Committer**: Staged atomic commits, clean commit messages, branch sync
  - Profile: `gpt-luna`
  - Default assignment: `"create $commit(s) for these changes, then git push"`
- **On-Demand Roles**: New custom roles or ad-hoc agents Chat creates outside the roster, without an explicit profile
  - Profile: `ds-flash-v4`

### Profiles

- **S-tier**:
  - `gpt-sol-med`: harness `codex`, model `gpt-5.6-sol`, thinking `medium` (`gpt-sol-low`: thinking `low`)
  - `opus-med`: harness `claude`, model `claude-opus-5`, thinking `medium`
  - `ds-pro-v4`: harness `pi`, model `openrouter/deepseek/deepseek-v4-pro-0813`, thinking `max`
- **A-tier**:
  - `gemini-flash`: harness `pi`, model `openrouter/google/gemini-3.7-flash`, thinking `medium`
  - `ds-flash-v4`: harness `pi`, model `openrouter/deepseek/deepseek-v4-flash-0731`, thinking `max` (no vision)
- **B-tier**:
  - `gpt-luna`: harness `codex`, model `gpt-5.6-luna`, thinking `medium` (supports vision for UI/QA)

Profiles with no role assignment are **spare profiles** — used only by explicit user override or when Chat assigns one on demand.

### Launch Recipes

Pass profile parameters as native harness arguments after Herdr's `--` delimiter.

#### Pi harness

```bash
herdr agent start <name> --kind pi --pane <pane-id> -- \
  --model "<provider/model-id>" \
  --thinking <level>
```

#### Codex harness

```bash
herdr agent start <name> --kind codex --pane <pane-id> -- \
  --model "<model-id>" \
  -c 'model_reasoning_effort="<level>"'
```

#### Claude harness

<!-- WIP: Placeholder only. Stop if the user actually assigns any agent to this harness. -->
Work in progress (stop if the user actually assigns any agent to this harness).

---

## Topology

```text
         ┌─────────┐
         │ 👤 User │
         └────┬────┘
              │
┌───────────────────────────┐     ┌───────────────────────────┐     ┌───────────────────────────┐     ┌───────────────────────────┐
│ Tab 1 · Chat 💬           │  ─  │ Tab 2 · Workers 🛠         │  ─  │ Tab 3 · QA 🧪             │  ─  │ Tab 4 · Reviewers ✅      │
├─────────────┬─────────────┤     ├─────────────┬─────────────┤     ├─────────────┬─────────────┤     ├─────────────┬─────────────┤
│ Chat        │ Planner     │     │ Builder 1   │ Builder 2   │     │ CI          │ QA          │     │ Reviewer 1  │ Reviewer 2  │
│ (launched)  │ (launched)  │     │ (standby)   │ (standby)   │     │ (standby)   │ (standby)   │     │ (standby)   │ (standby)   │
└─────────────┴─────────────┘     ├─────────────┼─────────────┤     ├─────────────┼─────────────┤     └─────────────┴─────────────┘
                                  │ Builder 3   │ Researcher  │     │ Docs        │ Committer   │
                                  │ (standby)   │ (standby)   │     │ (standby)   │ (standby)   │
                                  └─────────────┴─────────────┘     └─────────────┴─────────────┘
```

## Workflow

user request → plan → build → CI/QA → reviewer → doc → commit

This is the default workflow for this workspace command. Use the matching `$poteto-mode` playbook for delivery or `$figure-it-out` when a tailored workflow is needed. If requirements are ambiguous, return to the relevant idea skill before building.

Pre-build work in `andy-mode ; idea` is outside this command's build sequence.

---

### `Chat 💬` (tab 1)

Split horizontally (50/50): `Chat (launched)` | `Planner (launched)`.

#### Chat

Chat is the SDLC Orchestrator and Gatekeeper.

Chat follows the selected delivery workflow. When a brief needs a durable artifact or scored evaluation, read `references/export-artifacts.md` or `references/eval-rubric.md` from the active `pa-doc-update` skill directory. These references provide artifact conventions without starting another workflow.

**SDLC Workflow & Cost-Optimized Gates:**
1. **Implementation**: Chat briefs Builder(s) → Builders implement code and run local unit tests.
2. **CI / QA Gate (Cheap & Fast)**: Chat routes changes directly to `CI` (linters, test suites) and `QA` (functional/UI validation).
   - *On Failure*: Route error logs back to the Builder for repair → rerun CI/QA.
   - *On Success*: Proceed to Reviewer Gate.
3. **Reviewer Gate (Costly & Deep)**: Chat launches reviewers with independent lenses. Scale to the change: 1 for trivial, 2 by default, 3+ for high-risk.
   - *On Blocking Findings*: Brief Planner/Builder for targeted fixes → verify through CI/QA → Reviewer re-checks.
   - *On PASS*: Proceed to Docs & Commit.
4. **Docs & Commit**: Route documentation updates to `Docs` → task `Committer` to stage atomic commits and push.

**Planning brief (Chat → Planner):**
Send a structured brief with:
- User request, constraints, and acceptance criteria.
- Canonical **Role Assignments** roster and profile tiers.
- Current agent states (launched/idle vs standby).
- Applicable skills per role: Planner (`$figure-it-out`), Builders (`$poteto-mode`), QA (`andy-mode ; qa`), Docs (`$pa-doc-update`), Committer (`$commit`), Reviewers (`$interrogate`, `2nd-pass`).
- Explicit requirements: subtasks with deliverables, acceptance criteria, dynamic pane names (`<phase>/<total>-<prefix>-<keyword>`), dependency order, parallel lanes, and shared-file conflict prevention.

**Delegation preamble (included in all delegated prompts):**

> - Chat orchestrates all work and is the only agent that talks to the user.
> - Do not message other agents or the user directly; report questions and results to Chat only.
> - Stay within your assigned role and scope; Chat routes your output to the next stage.
> - Return your deliverable and validation evidence to Chat upon completion.

#### Planner

- Turn briefs into concise, SDLC-aligned plans (under 20 lines).
- Assign every subtask a role from the roster, profile tier, skill, deliverable, acceptance criteria, and **assigned dynamic pane name** (`<phase>/<total>-<prefix>-<keyword>`).
- Enforce the SDLC sequence: Builder → CI & QA → Reviewers → Docs → Committer.
- Mark parallel lanes vs sequential dependencies and flag shared-file risks.
- Route unknowns to Researcher before Builders start.
- Remain read-only; do not edit files or execute commands in Herdr.

**Response format:**
1. **Intent**
2. **Phases & Panes** — subtasks with dynamic pane name, role, profile tier, skill, deliverable, and acceptance criteria.
3. **Flow** — order, dependencies, parallel lanes, and shared-file conflict mitigation.
4. **Gates** — CI/QA verification, review lenses, and user-approval gates.

---

### `Workers 🛠` (tab 2)

2×2 grid: `Builder 1` | `Builder 2` | `Builder 3` | `Researcher` (all standby at kickoff).

#### Builders 1, 2, 3
- Focus strictly on implementation, targeted code edits, and single-file unit tests.
- Do not run full repo CI suites, browser QA testing, documentation maintenance, or git commits.
- Maintain one writer per file/worktree; parallelize only across independent files.
- Report deliverables and test evidence back to Chat.

#### Researcher
- Scout repository structure, explore external APIs/docs, and resolve unknowns before or during execution.

---

### `QA 🧪` (tab 3)

2×2 grid: `CI` | `QA` | `Docs` | `Committer` (all standby at kickoff).

#### CI
- Run automated verification: test suites, linters, typecheckers, and build scripts (e.g., `just ci`). Report structured pass/fail logs.

#### QA
- Perform hands-on functional and user-journey validation against acceptance criteria. Inspect web/UI flows with browser automation and screenshots (requires vision). Skill: `andy-mode ; qa`.

#### Docs
- Update affected documentation, specs, and CLI reference notes when behavior or configuration changes. Skill: `$pa-doc-update`.

#### Committer
- Stage approved atomic commits with clean messages and push to branch. Skill: `$commit`.

---

### `Reviewers ✅` (tab 4)

50/50 horizontal split: `Reviewer 1` | `Reviewer 2` (both standby at kickoff).

#### Reviewer 1 & Reviewer 2
- High-tier, independent, read-only code inspectors triggered only after CI and QA pass.
- **Strict boundary**: Reviewers **never** run CI test suites, linters, or QA browser checks (wastes high-reasoning tokens) and **never** edit files.
- Focus strictly on code architecture, correctness, logic, edge cases, security, and maintainability.
- Run independent review lenses in parallel (e.g., Correctness & API Contracts vs Security & Maintainability).
- Skills (optional, as assigned by Chat): `$interrogate`, `2nd-pass`.
- Requirements: Report actionable findings with severity, file path, line numbers, and evidence; state `PASS` explicitly when clear.

---

## Live focus and handoffs

Make sequential handoffs visible by focusing active agents by ID:
1. When delegating, focus the assigned agent: `herdr agent focus <agent-id>`.
2. Follow the SDLC progression: Chat → Builder → CI/QA → Reviewer → Docs/Committer → Chat.
3. During parallel work, focus the primary active agent; avoid rapid focus cycling.
4. Return focus to Chat whenever user input is needed, an agent is blocked, or results are ready.

## Presentation rules

- Keep tab names concise with trailing emojis.
- Use clean dynamic pane names (`1/5-bld1-auth-route`, `2/5-ci-test-suite`) without decorative prefixes or harness engine names.
- Use `--no-focus` for background operations.
- Format prompts with concise headings, bullets, acceptance criteria, and validation checks.

## After initial setup

1. Verify launched agents:
   ```bash
   herdr agent read <agent-id> --source detection --lines 12
   ```
2. Print the workspace topology with returned IDs.
3. Confirm **Chat** and **Planner** are **launched**, idle, and ready.
4. Confirm **Builder 1..3, Researcher, CI, QA, Docs, Committer, Reviewer 1..2** are clean **standby** plain shell panes.
5. Return focus to **Chat** by ID and ask the user for the first task.

<!--
Formatting preference:
When editing or creating Markdown tables in this file, always keep table columns visually aligned and padded with spaces across headers, delimiter rows, and data cells so the raw source remains clean, balanced, and readable.
-->

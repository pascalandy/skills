---
name: "create-a-jev-cli-decision-wrapped-in-a-skill"
description: "Use only when the user explicitly invokes `create-a-jev-cli-decision-wrapped-in-a-skill`."
disable-model-invocation: true
---

# Create a Jev decision CLI wrapped in a skill

Give a project Jev decision gates. When you finish, the project has three new things:

- **`jevgate`**, a vendored CLI that sends selected evidence to Jev and turns the typed answers into one advisory verdict: `pass`, `escalate`, `insufficient`, or `block`
- **`just jev` and `just jev-merge`**, pass-through recipes that forward flags and answer `--help`
- **`jev-decide-<app>`**, a project skill that tells agents when to run a gate, how to read its probabilities, and what to do with each verdict

Jev adds a judgment layer. It replaces neither the project's check command (does it build and pass its tests?) nor its `verify-<app>` skill (does the running app do what the feature map says?). Every verdict is advisory: only deterministic preconditions produce `block`, and `pass` never grants merge or deployment authority. Question changes happen only in a requested maintenance session, which belongs to `maintain-a-jev-cli-decision-wrapped-in-a-skill`. This skill ships the `merge` gate only.

Bundled material, relative to this file:

- `scripts/jevgate.py` and `scripts/jevgate.py.lock`: the canonical engine and its locked dependencies
- `references/cli-contract.md` and `references/gate-catalog.md`: the command contract and the merge gate. Read them when a step needs a flag, an exit code, a record field, or a question's role
- `references/jev-principles.md`: the principles and the question review checklist
- `references/article-summary.md`: the brief this design answers
- `assets/`: `config.toml`, `gates/merge.toml`, `packs/merge.toml`, `justfile-snippet.just`, and `project-skill-template.md`

Run the canonical engine with `uv run --script <skill_dir>/scripts/jevgate.py` and the vendored one with `just jev`.

## 1. Load owners

Read `references/jev-principles.md` and `references/article-summary.md`. Resolve `typesafe-ai` from the active skill catalog and follow it; it owns the API and question design, so reference it and never copy it. Read these live pages: [API](https://docs.typesafe.ai/api.md), [models](https://docs.typesafe.ai/models.md), [confidence](https://docs.typesafe.ai/confidence.md), [jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md), [fan-out](https://docs.typesafe.ai/patterns/fan-out.md), and [composite scoring](https://docs.typesafe.ai/patterns/composite-scoring.md). Resolve `writing-great-skills` for the project skill in step 6. If either skill cannot be found, report the missing dependency and stop.

*Complete when the current model pin and limits are written down* and compared with the engine's: model `jev-1.13.0`, 64k tokens per request, 32k for state plus the longest question, and at most 255 Choice options. If the live docs disagree, stop and report the exact conflict.

## 2. Check readiness

From the project root, run the canonical engine's offline `uv run --script <skill_dir>/scripts/jevgate.py doctor`. A missing `.jev/` shows as `setup`, which is a finding for this run, not a prerequisite. After step 7, run the generated project's `just jev doctor --online` before any live proof. For a missing runtime, key, or network, report the exact remediation `doctor` prints. Generation may continue offline, but setup is not proven until the live checks pass.

*Complete when every readiness item has a result.*

## 3. Interview the repo, not the user

Answer each item from the codebase and ask the user only what you cannot observe:

- **Integration branch:** the default branch, from `git symbolic-ref refs/remotes/origin/HEAD`, CI triggers, and branch protection notes
- **Check command:** the project's own `just check`, `just ci`, or equivalent. Run it once on a clean tree. It must pass offline, leave the tree clean, and never call TypeSafe
- **PR host:** the git remote, and whether `gh` works for it
- **Test layout and framework:** where tests live and how their names map to modules. `jevgate` joins a test to the module whose file stem it matches
- **Verify skill and feature map:** the project's `verify-<app>`, if one exists
- **Written rules:** `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md`
- **Checkpoints:** where decisions happen today, such as hooks, CI jobs, and release scripts
- **Risk areas and sensitive paths:** data stores, auth, deploy config, and any path that must never leave the machine. These become deny globs
- **Recent merge sizes:** `git log --merges --stat -20`, to sanity-check the default budgets

*Complete when every generated value is grounded in a file or command output.*

## 4. Handle an existing `.jev/`

When `.jev/jevgate.py` exists, compare `just jev version --json` with the canonical `version --json`. When the project engine reports `modified: true`, show `diff -u .jev/jevgate.py <skill_dir>/scripts/jevgate.py` before replacing it. An upgrade replaces only `jevgate.py` and `jevgate.py.lock`; config, gates, packs, cases, and runs stay. Apply the upgrade only after the user accepts it.

*Complete when the upgrade is prepared or declined.*

## 5. Design the questions

Start from `assets/packs/merge.toml`. With `typesafe-ai`, adapt instructions and criteria to the project's vocabulary: its test framework, its data stores, and its deploy surface. Keep each question's id, role, and band unless evidence says otherwise. Extract the written rules into `.jev/packs/rules.toml`:

```toml
schema = "jevgate.pack/v1"
id = "rules"

[[rules]]
id = "contract-first"
text = "The rule as written, one condition per rule"
source = "AGENTS.md"
```

Show the rule list to the user for review. A rule that code can check becomes a code fact instead of a question: add it to the project's check command, or add a deny glob. Run every question through the question review checklist in `references/jev-principles.md`.

*Complete when every question has been reviewed against the principles checklist*, with the review recorded.

## 6. Generate

Write these files:

- `.jev/jevgate.py` and `.jev/jevgate.py.lock`, copied from `scripts/`
- `.jev/config.toml` from `assets/config.toml`. Fill `{{INTEGRATION_REF}}` and `{{CHECK_COMMAND}}`, add project `deny_globs`, and leave out the `[privacy]` table until step 7
- `.jev/gates/merge.toml` from `assets/gates/merge.toml`, with its question naming the integration branch
- `.jev/packs/merge.toml` and `.jev/packs/rules.toml` from step 5
- `.jev/.gitignore` with `runs/` and `cache/`
- The `justfile`: append `assets/justfile-snippet.just`. Never replace an existing recipe; if `jev` or `jev-merge` already exists, stop and ask
- `jev-decide-<app>/SKILL.md` in the project's established skill directory, from `assets/project-skill-template.md` with `{{APP}}`, `{{CHECK_COMMAND}}`, and `{{VERIFY_SKILL}}` filled, applying `writing-great-skills`

*Complete when `just jev` prints its help, `just jev gates --check` passes, and no `{{` placeholder remains* outside the pending `[privacy]` table.

## 7. Ask for permission

Run `just jev-merge --dry-run`. Show its summary and the payload file it names. Then show the terms that `just jev doctor` names. Obtain both explicit answers:

- **`send_code`:** may diff hunks, claims from PR text or commit messages, and check facts go to TypeSafe?
- **`commit_cases`:** may admitted cases be committed?

No repository gets a default, public or private. The gate runs before push, so it can send commits nobody has published yet. When the user has already approved both answers for this project in writing, record that provenance after showing the payload instead of asking again. An existing explicit approval stays valid within its recorded scope and terms; ask again only when either changed.

Write the `[privacy]` table with `send_code`, `commit_cases`, `approved_by`, `approved_on`, and `terms` set to the name `doctor` prints. When `commit_cases = false`, add `cases/` to `.jev/.gitignore`.

*Complete when the table exists.*

## 8. Prove it

Finish every generated file first, then commit them as G. Bootstrap dependencies: run `just jev version` once online, and install whatever the project's check command needs. Record each proof ID, command, exit, observed result, and explicit run ID where one applies.

Run every no-network claim (P1, P3, both replays, and the check command with a canary key) inside one harness. It sends TypeSafe traffic to a local recorder and blocks other traffic. The recorder logs outside the project, and the proxy variables are cleared because the SDK would route recorder traffic through an HTTP proxy and fake a zero-request pass:

```bash
log=$(mktemp)
uv run --no-project python -m http.server 8799 --bind 127.0.0.1 --directory "$(mktemp -d)" 2>"$log" &
unset HTTP_PROXY http_proxy https_proxy no_proxy
export TYPESAFE_BASE_URL=http://127.0.0.1:8799 HTTPS_PROXY=http://127.0.0.1:9 NO_PROXY=127.0.0.1 UV_OFFLINE=1
```

A no-network proof holds only when all three are true:

- it exits as expected
- `rg 'HTTP/1' "$log"` finds nothing
- `git status --porcelain --ignored` changes only by that proof's documented outputs

Use `env -u TYPESAFE_API_KEY` wherever a proof says "no key".

1. **P1 Help:** `just jev` and `just jev-merge --help` exit 0 with no key, network, check run, or engine writes
2. **P2 Readiness:** `just jev doctor --online` exits 0 and reports usable runtime, config, credentials, permission, and an authenticated model listing. An alias-only listing passes
3. **P3 Preview:** `just jev-merge --dry-run` exports sanitized payloads with no denied or ignored content, network, check execution, or run record
4. **P4 Live:** `just jev-merge --no-cache` on G records at least one actual inference response, answered model, usage, cost, verdict, and run ID R. Exits 0 or 10 can complete this proof. Exit 12 documents missing evidence but does not substitute for live inference; obtain the evidence and repeat. Stop at the first live step that cannot execute and report the exact missing input or service failure
5. **P5 Explain:** `just jev explain R` exposes the actual stored inputs, answers, reasons, and omissions
6. **P6 Replay and reuse:** `just jev replay R` reproduces the verdict with no key or network. A second live run on unchanged G, PR text, and config uses exact-cache hits and the check record, with zero new inference cost
7. **P7 Portable case:** `just jev label R --scope gate --outcome unknown --by reproduced --evidence "setup proof; semantic outcome not reviewed" --admit`. Commit the case as C, keeping every generated file identical to G. Clone C into a fresh directory, bootstrap dependencies, then replay R with empty runs and cache, no key, and no network

*Complete when P1–P7 pass and the generated files at C equal those proved at G.* The admitted case records G truthfully; it does not claim to judge C. If generated files change, repeat the proof on their new clean commit. A case-only commit does not require admitting another case.

## 9. Hand over

Report the recipes, what each advisory verdict asks of the next agent, how to read the probabilities, the proof run's cost, how to label an outcome, and the upgrade path: rerun this skill, and it compares engine versions before replacing anything.

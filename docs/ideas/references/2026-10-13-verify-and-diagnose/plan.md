---
name: verify-and-diagnose plan
description: The build order for the verify-and-diagnose design, in phases that each end on a check
date_created: 2026-10-13
status: accepted
---

# Plan: build verify and diagnose

This page lists the phases that build what [design.md](design.md) describes. Each phase ends on a check and lands as one PR. A phase starts only when the previous phase's check passes. Phases 0 and 1 share a PR, because the compile step rejects eval files outside a package, so the fixtures land with `diagnose/SKILL.md`. Work in a worktree of `pascalandy/skills`, as its `AGENTS.md` says.

Before writing any skill text, load `writing-great-skills`. Before writing any script, read [script conventions](../../../references/script-conventions.md). Every eval runs on both Claude and Codex.

## Phase 0: evals and a baseline

Measure the current skills before writing the new one. The post's three bugs become small fixtures under `authoring/andy-devtools/diagnose/evals/`. Each fixture is a fictional reconstruction of the failure mechanism, never the author's data.

Deeper evidence is reachable only through a `./probe` script in each fixture, so the agent's choice to descend shows in `events.jsonl`. Grade the process, not only the answer: what the agent read first, which control it chose, which hypotheses it eliminated and with which fact, and what claim it made.

1. **Latency.** A `storage/` repo where the new mTLS path builds `DatabaseClient` instead of `ShardedDatabaseClient`. A memoized `ssl_context()` inside `rpc()` reads like a per-call reload. Evidence holds P99 for both populations, `prod.toml` (5 by 80), `preprod.toml` (2 by 1), and an old postmortem about cert reloads as the lure. `./probe` offers `tcp-handshake`, `cert-loads`, and `dns` per population, with a `patched` population that imports the working tree. Done when its unit tests pass with the bug present and `./probe dns --population variable` prints about 400 answers
2. **Leak.** An `authflow/` repo with tags `v1.4` (good) and `v1.5` (bad). A recursive single-use state machine, a process-wide engine cache that is on by default, and an amortization path that is off by default. `BUG.md` gives versions and repro steps. `heap.txt` points at the plain recursion. Done when the repro grows memory at `v1.5` and not at `v1.4`, and its top frame matches `heap.txt`
3. **Hang.** No auth daemon source. Our client has a retry loop that looks like it could spin, the lure. Four user report bundles show timeouts only, a packet capture silent after the WebSocket upgrade, a thread waiting in an IPC send, and one IPC table line showing an unanswered reply right. Two permission-failure bundles serve as the sad-path control. A coworker's clock-skew bundle is the false repro, and an email from the auth team says no logs means no request. Done when the four reports share the unanswered reply right and neither the control nor the false repro has it
4. **Variants.** The latency case with only P99 available at first, so the agent must find the discriminating probe, not guess. A fact gathered from the wrong build in the leak case, so the agent must append a correction, not edit the fact. An error present in both control and variable, which must stay noise. Done when each variant's expected behavior is written in `evals/evals.json`
5. **Build-time case.** Under `authoring/poteto/maintain-verification-skill/evals/`: the latency repo one commit before release, with its `verify-storage/` skill. Done when planting `DatabaseClient` changes the lookups the verify loop records at 2 by 1: which names the client resolves, not only how many answers come back
6. **Baseline.** Run every case through the `writing-for-agents` eval runner with `--ref origin/main`, which lacks `diagnose` and the focused pass. Done when each case has a baseline score on both agents. If the bug cases' baseline already meets 80 percent of their expected behaviors, Phase 1 writes only what the failing behaviors need, plus the `interrogate` changes

## Phase 1: the bug side

1. **Write `diagnose`.** `SKILL.md` holds steps 0 to 9, the quick path, the field re-read, and the credit to the post. The references are `glossary.md`, `principles.md`, `case-file.md`, `parity.md`, and `ladders.md` with the CLI ladder, Pascal's main stack, plus the service, desktop, web, and mobile ladders. Done when the skill validator answers `{"ok":true}`
2. **Change `interrogate`.** Apply the rules in the design's interrogate section, and retire the consensus signal in `references/lead-judgment.md`. Done when the skill validator answers `{"ok":true}`
3. **Beat the baseline.** Run the bug cases and their variants at this commit. The build-time case waits for Phase 3. Done when the bug cases beat the baseline, no run shows an invented fact, an edited fact, a `fixed` claim without the field re-read, or a repair on a diagnosis-only request, and `interrogate` never returns "confirmed"
4. **Ship.** Run `just compile-skills`, `just remote-skills`, and `just check`, review source and generated output together, and open the PR. Done when `just signoff` is green

## Phase 2: `case.py`, only if Phase 1 shows the need

Start this phase only if Phase 1 runs show case-file bookkeeping errors: a miscounted strength, an ignored `x`, a descent without the repair tactics, or a lost best finding.

1. **Write `case.py check`** with tests built from the post's three matrices as literal fixtures: latency (P99 strength 7, DNS strength 1, next step `validate`), leak before the repair tactics (no candidate, next step `tactics` with a split suggestion), leak after split and combine (next step `combine`, necessity holds), and fact immutability (an edited fact row fails). Done when the tests pass
2. **Wire it into `diagnose`.** Done when the bug cases meet the Phase 1 bar, none scores below Phase 1, and the error that triggered this phase no longer occurs

## Phase 3: the verify loop

1. **Extend `create-verification-skill`.** Feature files gain the `Readings` H2, the generated Evidence section names where past runs live, and the generated skill carries the planted-bug rule, the last-good-run rule, and the baseline intake from [the verify loop](design.md#the-verify-loop). Creation adds the `AGENTS.md` line that names the loop. Done when a generated skill on a scratch repo has readings for each mapped feature from the interview, with no placeholders
2. **Add the focused pass to `maintain-verification-skill`,** with the offer to create a loop and the `AGENTS.md` opt-out. Done when the build-time case passes on both agents, with its new reading checked against its declared normal value and its planted bug, since no base run includes it yet
3. **Add the "verify loop" category to `retro-global`.** Done when `just check` passes
4. **Pilot on `verify-video-archive`.** `parallel-batch` and `interruption` gain readings, and the verify loop compares them with the last good run. Done when, on a scratch branch, a planted bug that ignores the worker cap fails the run and the real code passes, and a run interrupted mid-plant leaves the caller's files and refs identical. This is the end-to-end proof of the build side

## Phase 4: wire the lane

1. **poteto-mode.** `feature.md` and `bug-fix.md` start the lane at `maintain-verification-skill`, `bug-fix.md` takes an existing confirmed case without a second intake, and `SKILL.md` points the bug-fix non-negotiable at `diagnose`
2. **Hand diagnosis to `diagnose`** in the places that hold pieces of the method today: four poteto-mode playbooks (`bug-fix`, `runtime-forensics`, `trace-forensics`, `perf-issue`), its `fix-root-causes` principle, and andy-mode's `qa` playbook. Apply the rest of the design's "Changes to existing skills" table
3. **Brigade.** In `arancini` and `bisque`, manic-1, manic-2, and manic-5 call `interrogate` with `reviewers = 2` from `config.toml`, and the Cook runs `diagnose` for a bug card. `cook-implement`'s Fix section reruns the touched features through a delegate after each fix, and `chef-closing` requires one whole-loop run on the final head, which the Chef starts as a delegate when no Cook is open. After a bug card merges, `chef-closing` resumes its case at `diagnose` step 9. `chef-triage` sends a finding on a `verify-<app>` file to the owning Cook, and DocWriter keeps ordinary docs

Phase 4 is done when all checks pass:

- [ ] `just check` passes
- [ ] A poteto-mode bug-fix run on the latency case reaches `diagnose` before opening any source file, and reaches lane step 1 carrying the DNS reading
- [ ] One case and its DNS reading survive into implementation with no second intake
- [ ] A barrage calls `interrogate` with two reviewers
- [ ] A brigade round reruns the touched features after a fix, and the whole loop before merge
- [ ] A still-bad field reading cannot earn `fixed`

## Phase 5: the first real case

1. **Run a real bug end to end.** Any of Pascal's projects. Done when the case closes with its retros filed
2. **Measure.** Done when a second case in that repo needs fewer interventions, or its case file says why not

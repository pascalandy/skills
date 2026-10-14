---
name: debug-mode plan
description: The build order for debug-mode, in small units that each end on a check
date_created: 2026-10-13
status: superseded
---

# Plan: build debug-mode (round 1)

This page lists the steps to build what [design-round-1.md](design-round-1.md) describes. [The current plan](../plan.md) replaces it. Each unit ends on a check. A phase starts only when the previous phase's checks pass. Work in a worktree of `pascalandy/skills`, one PR per phase, as the repository's `AGENTS.md` says. Phases 0 and 1 share one PR: the compile script rejects files outside a package, so the fixtures land with the package's `SKILL.md`.

Before writing any skill text, load `writing-great-skills`. Before writing any script, read [script conventions](../../../../references/script-conventions.md).

## Phase 0: evals and a baseline

Measure the current skills before writing the new one, on the Phase 1 branch. The three bugs from the post become small fixtures under `authoring/andy-devtools/debug-mode/evals/`. Each fixture is a fictional reconstruction of the failure mechanism, never the author's data.

Deeper evidence is reachable only through a `./probe` script in each fixture, so the agent's choice to descend shows in `events.jsonl`. Grade the process, not only the answer: what the agent read first, which control it chose, which hypotheses it eliminated and with which fact, and what claim it made.

1. **Latency fixture.** A `storage/` repo where the new mTLS path builds `DatabaseClient` instead of `ShardedDatabaseClient`. A memoized `ssl_context()` inside `rpc()` reads like a per-call reload. Evidence holds P99 for both populations, `prod.toml` (5 by 80), `preprod.toml` (2 by 1), and an old postmortem about cert reloads as the lure. `./probe` offers `tcp-handshake`, `cert-loads`, and `dns` per population, with a `patched` population that imports the working tree. Done when its unit tests pass with the bug present and `./probe dns --population variable` prints about 400 answers
2. **Leak fixture.** An `authflow/` repo with tags `v1.4` (good) and `v1.5` (bad). A recursive single-use state machine, a process-wide engine cache that is on by default, and an amortization path that is off by default. `BUG.md` gives versions and repro steps. `heap.txt` points at the plain recursion. Done when the repro grows memory at `v1.5` and not at `v1.4`, and its top frame matches `heap.txt`
3. **Hang fixture.** No auth daemon source. Our client has a retry loop that looks like it could spin (the lure). Four user report bundles show timeouts only, a packet capture silent after the WebSocket upgrade, a thread waiting in an IPC send, and one IPC table line showing an unanswered reply right. Two permission-failure bundles serve as the sad-path control. A coworker's clock-skew bundle is the false repro, and an email from the auth team says no logs means no request. Done when the four reports share the unanswered reply right and neither the control nor the false repro has it
4. **Build-time fixture.** The latency repo one commit before release, with its `verify-storage/` skill. Done when planting `DatabaseClient` changes the lookups the verifier records at 2 by 1: which names the client resolves, not only how many answers come back
5. **Variants.** Add three cheap variants from the Codex design: the latency case with only P99 available at first (the agent must find the discriminating probe, not guess), a fact gathered from the wrong build in the leak case (the agent must append a correction, not edit the fact), and an error present in both control and variable (it must stay noise). Done when each variant's expected behavior is written in `evals/evals.json`
6. **Baseline.** Run every scenario through the `writing-for-agents` eval runner with `--ref origin/main`, which lacks `debug-mode`. Done when each scenario has a recorded score per agent. If the baseline already meets 80 percent of the expected behaviors, cut Phase 1 to the glossary, the eliminator, and the `bug-fix` edit

## Phase 1: `diagnose`, prose only

The most value for the least machinery.

1. **Write the package.** `SKILL.md`, `references/glossary.md`, `references/principles.md`, `references/case-file.md`, `playbooks/diagnose.md`, `references/eliminator.md`, `references/parity.md`, and `references/ladders.md` with the CLI ladder (Pascal's main stack) plus the service, desktop, web, and mobile ladders. Credit the post in `SKILL.md`. Done when the skill validator answers `{"ok":true}`
2. **Write the close step.** `references/destinations.md`, the close gate, and the `index.jsonl` line. Done when each eval case ends with every intervention given a destination, `declined` included
3. **Beat the baseline.** Run the diagnosis scenarios and their variants at this commit. The build-time scenario waits for Phase 4. Done when every run meets the mandatory behaviors (no fabricated fact, no edited fact row, no `fixed` claim without the parity reading and the symptom gone, no repair on a `diagnosis` request), no scenario scores below its baseline, and the behaviors this phase targets improve: facts before code, a control, the matrix, and repro parity
4. **Ship.** Run `just compile-skills`, `just remote-skills`, and `just check`, review source and generated output together, and open the PR. Done when `just signoff` is green

## Phase 2: `case.py`, only if Phase 1 shows the need

Start this phase only if a Phase 1 run miscounted a strength, ignored an `x`, descended without trying the repair tactics, or lost its best finding.

1. **Write `case.py check`** with tests built from the post's three matrices as literal fixtures: latency (P99 strength 7, DNS strength 1, next step `validate`), leak before the repair tactics (no candidate, next step `tactics` with a split suggestion), leak after split and combine (next step `combine`, necessity holds), and fact immutability (an edited fact row fails). Done when the tests pass
2. **Wire it into `diagnose`.** Done when the diagnosis scenarios meet the mandatory behaviors, none scores below Phase 1, and the failure that triggered this phase no longer occurs

## Phase 3: point existing skills at debug-mode

1. **Edit the callers** listed in the design's "Changes to existing skills" table, except `feature.md`, `create-verification-skill`, `maintain-verification-skill`, and the pilot, which wait for Phase 4. Done when `just compile-skills` and `just check` pass, and a `poteto-mode` bug-fix run on the latency fixture reaches `diagnose` before it opens a source file
2. **Check `interrogate`.** Done when an `interrogate` run on a root-cause claim sends it to the eliminator and reports agreement as a shared reading

## Phase 4: `instrument`, piloted

1. **Extend the generator.** Add Probes, Controls, Policy, and the `Gauges` H2 to `create-verification-skill` and its feature-map example. Done when a generated skill on a scratch repo has every section filled from the interview, with no placeholders
2. **Write `playbooks/instrument.md`** and the `feature.md` edit. Done when the build-time scenario passes: gauge from config, emitted by default, recorded, gated, and the gate shown failing on the planted client
3. **Pilot on `verify-video-archive`.** `parallel-batch` and `interruption` gain Gauges. The verifier writes `gauges.json` and compares it with the last passing manifest. Done when ignoring the worker cap on a scratch branch fails the gate and the real code passes. This is the end-to-end proof of Goal 1
4. **Extend the maintainer.** Done when a `maintain-verification-skill` pass on the pilot reports gauge parity per feature

## Phase 5: the first real case

1. **Run a real bug through `diagnose` and close.** Any of Pascal's projects. Done when the case closes with every intervention given a destination
2. **Measure.** Done when a second case in the same repo shows fewer interventions, or the case file states why not

## Decisions needed before Phase 0

The design's open questions. Phase 0 needs only the last one, the eval budget. The others shape Phases 1 and 4.

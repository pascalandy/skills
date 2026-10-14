---
name: verify-and-diagnose plan
description: The build order for the verify-and-diagnose design, in phases that each end on a check
date_created: 2026-10-13
status: accepted
---

# Plan: build verify and diagnose

This page lists the phases that build what [design.md](design.md) describes. Each phase ends on a check and lands as one PR. A phase starts once the preceding required phase passes, so Phase 3 follows Phase 1b when Phase 2 is skipped. Phases 0 and 1 share a PR, because the compile step rejects eval files outside a package, so the fixtures land with `diagnose/SKILL.md`. Work in a worktree of `pascalandy/skills`, as its `AGENTS.md` says.

Before writing any skill text, load `writing-great-skills`. Before writing any script, read [script conventions](../../../references/script-conventions.md). Every eval runs on both Claude and Codex.

## Phase 0: evals and a baseline

Measure the current skills before writing the new one. Five invented practice bugs become small fixtures under `authoring/andy-devtools/diagnose/evals/`, each testing one move of the method, spread across a CLI, a scheduled job, and a web service. They copy nobody's story: not the post's, and not Pascal's own incidents.

Deeper evidence is reachable only through a `./probe` script in each fixture that has production hosts, so the agent's choice to descend shows in `events.jsonl`. Grade the process, not only the answer: what the agent read first, which control it chose, which hypotheses it eliminated and with which fact, and what claim it made.

1. **A working case to compare against: `departures`.** A transit departures API where the screens at one station show no departures. A deploy minutes earlier and errors present on every stop are the tempting suspects. The feed imported just before made that station a parent of two platforms, and the departures query does not expand a station to its platforms. Done when its unit tests pass with the bug present, `./probe requests --stop HRB` shows departures fall to 0 a few minutes before the deploy while another station keeps its departures, and the same errors show on both stops
2. **One telling reading among many weak ones: `pantry`.** A recipe search API whose p95 jumped after a release, with a pool still on the previous release as the control. Threads, CPU, database CPU, GC, and response size all differ and each has several explanations. Only statements per request, which grow by one per search hit, point at one cause: a rating loaded per hit. Done when tests pass with the bug present, `./probe statements --by-hits` grows per hit on the new release and stays flat on the old, and `--pool patched` measures the working tree the same way
3. **Two causes together: `tally`.** A statement-import CLI whose new dedupe key keeps identical purchases apart, while one bank repeats a row at the top of each page of its export. Each alone is harmless: the old release imports that bank correctly, and the new release imports the other bank correctly. Done when tests pass at each tag and the four imports, two releases by two banks, print the readings the ground truth lists
4. **A misleading repro: `crumb`.** A bakery job that emails tomorrow's preorders every evening and has sent the wrong day since a host migration. A teammate's repro shows wrong orders from a stale staging table, a real but different breakage. The field signal is the sheet's date, two days ahead, because the new host's process runs in UTC. Done when tests pass in any zone, the export run with the new host's zone and run time prints the date two days ahead, and the same run in the bakery's zone prints the right date
5. **A fact hidden behind filtered or stale output: `skyrollup`.** A nightly weather rollup whose website summary is stuck, resumed from a case file that trusted a status command showing the last success and a log command that hides stderr. A deploy changed the publish folder's owner. Done when the setup writes yesterday's case file into the run's state folder, the job's log shows no error at any level while the journal shows a failure every night, and the folder's owner changed at the deploy's time
6. **Build-time case.** Under `authoring/poteto/maintain-verification-skill/evals/`: `tally` one commit before the 2.3 release, with its `verify-tally/` skill. Done when the existing loop sees only the intended change on the release branch, and a multi-page statement built from the bank's documented format reads the page-top copies as deduped on `main` and as inserted on the branch
7. **Baseline.** Run every case through the `writing-for-agents` eval runner with `--ref origin/main`, which lacks `diagnose` and the focused pass. Done when each case has a baseline score on both agents. If the bug cases' baseline already meets 80 percent of their expected behaviors, Phase 1 writes only what the failing behaviors need, plus the `interrogate` changes

## Phase 1: the bug side

1. **Write `diagnose`.** `SKILL.md` holds steps 0 to 9, the quick path, the field re-read, and the credit to the post. The references are `glossary.md`, `principles.md`, `case-file.md`, `parity.md`, and `ladders.md` with the CLI ladder, Pascal's main stack, plus the service, desktop, web, and mobile ladders. Done when the skill validator answers `{"ok":true}`
2. **Change `interrogate`.** Apply the rules in the design's interrogate section, and retire the consensus signal in `references/lead-judgment.md`. Done when the skill validator answers `{"ok":true}`
3. **Run against the baseline.** Run the five practice bugs at this commit. The build-time case waits for Phase 3. Done when every run meets the mandatory behaviors (no invented fact, no edited fact, no `fixed` claim without the field re-read, no repair on a diagnosis-only request, and `interrogate` never returns "confirmed"), no case scores below its baseline, and the targeted behaviors that failed the baseline improve. A case already at 100 percent passes by keeping its score
4. **Ship.** Run `just compile-skills`, `just remote-skills`, and `just check`, review source and generated output together, and open the PR. Done when `just signoff` is green

## Phase 1b: connect bug-fix to `diagnose`

A small PR right after the `diagnose` PR merges, with the bug-entry half of Phase 4 items 1 and 2. On a fresh report, `bug-fix.md` steps 1 and 2 run `diagnose`. poteto-mode's `SKILL.md` points the bug-fix non-negotiable at `diagnose`, and its `how` trigger for a nontrivial change or "are we sure?" excludes runtime failures. `principles/fix-root-causes.md` takes the design's wording. Done when `just check` passes and a poteto-mode bug-fix run on a practice bug reaches `diagnose` before opening any source file

## Phase 2: `case.py`, only if Phase 1 shows the need

Start this phase after Phase 1b, and only if Phase 1 runs show case-file bookkeeping errors: a miscounted strength, an ignored `x`, a descent without the repair tactics, or a lost best finding.

1. **Write `case.py check`** with tests built from the practice bugs' matrices as literal fixtures: `pantry` (statements per request strength 1, threads and database CPU weak, next step `validate`), `tally` before the repair tactics (no candidate, next step `tactics` with a combine suggestion), `tally` after combine (each member necessary), `skyrollup` after the reverify (a superseded fact reopens the elimination it caused), and fact immutability (an edited fact row fails). Done when the tests pass
2. **Wire it into `diagnose`.** Done when the bug cases meet the Phase 1 bar, none scores below Phase 1, and the error that triggered this phase no longer occurs

## Phase 3: the verify loop

1. **Extend `create-verification-skill`.** Feature files gain the `Readings` H2, the generated Evidence section names where past runs live, and the generated skill carries the planted-bug rule, the last-good-run rule, and the baseline intake from [the verify loop](design.md#the-verify-loop). Creation adds the `AGENTS.md` line that names the loop. Done when a generated skill on a scratch repo has readings for each mapped feature from the interview, with no placeholders
2. **Add the focused pass to `maintain-verification-skill`,** with the offer to create a loop and the `AGENTS.md` opt-out. Done when the build-time case passes on both agents, with its new reading checked against its declared normal value and its planted bug, since no base run includes it yet
3. **Add the "verify loop" category to `retro-global`.** Done when `just check` passes
4. **Pilot on `verify-video-archive`.** `parallel-batch` and `interruption` gain readings, and the verify loop compares them with the last good run. Done when, on a scratch branch, a planted bug that ignores the worker cap fails the run and the real code passes, and a run interrupted mid-plant leaves the caller's files and refs identical. This is the end-to-end proof of the build side

## Phase 4: wire the lane

1. **poteto-mode.** `feature.md` and `bug-fix.md` start the lane at `maintain-verification-skill`, and `bug-fix.md` takes an existing confirmed case without a second intake. Phase 1b already sends a fresh report to `diagnose`
2. **Hand diagnosis to `diagnose`** in the places that still hold pieces of the method after Phase 1b: three poteto-mode playbooks (`runtime-forensics`, `trace-forensics`, `perf-issue`) and andy-mode's `qa` playbook. Apply the rest of the design's "Changes to existing skills" table
3. **Brigade.** In `arancini` and `bisque`, manic-1, manic-2, and manic-5 call `interrogate` with `reviewers = 2` from `config.toml`, and the Cook runs `diagnose` for a bug card. `cook-implement`'s Fix section reruns the touched features through a delegate after each fix, and `chef-closing` requires one whole-loop run on the final head, which the Chef starts as a delegate when no Cook is open. After a bug card merges, `chef-closing` resumes its case at `diagnose` step 9. `chef-triage` sends a finding on a `verify-<app>` file to the owning Cook, and DocWriter keeps ordinary docs

Phase 4 is done when all checks pass:

- [ ] `just check` passes
- [ ] A poteto-mode bug-fix run on `pantry` reaches lane step 1 carrying the statements-per-request reading
- [ ] One case and its statements-per-request reading survive into implementation with no second intake
- [ ] A barrage calls `interrogate` with two reviewers
- [ ] A brigade round reruns the touched features after a fix, and the whole loop before merge
- [ ] A still-bad field reading cannot earn `fixed`

## Phase 5: the first real case

1. **Run a real bug end to end.** Any of Pascal's projects. Done when the case closes with its retros filed
2. **Measure.** Done when a second case in that repo needs fewer interventions, or its case file says why not

---
name: "swarm"
description: "Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
kind: "dev"
---

# Swarm

Read [the agent runtime contract](../poteto-mode/references/agent-runtime.md) before using runtime tools, loading related skills, or delegating. Use only capabilities and model IDs verified in this session.

Fan out N parallel workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers, not the runtime concurrency limit.
4. Use the `Worker` role for coverage work. For a model race, require an explicit model for each arm. Validate and name each arm's model before launch. If a requested model is unavailable, stop and ask for a named alternative rather than relabeling identical models as a race.
5. Give each worker its own writable output when it writes.

## Phase B: Fan out

Launch all N workers concurrently using the available delegation interface. Use local workers by default. Use a remote worker only when that capability is available and the task permits remote execution. Verify its repository revision, dependencies, credentials, and artifact return path. Remote execution is an optional placement choice, not a prerequisite.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.

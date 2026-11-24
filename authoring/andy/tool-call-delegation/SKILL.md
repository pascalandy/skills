---
name: "tool-call-delegation"
description: "Use when asked to delegate every tool call."
kind: "dev"
configuration-is-needed: true
---

## Tool call delegation

The lead agent schedules the tool calls, delegates their execution, verifies the evidence, and writes the answer. Use direct calls for delegation setup and communication.

1. Confirm `uv` with `uv --version` ([install uv](https://docs.astral.sh/uv/getting-started/installation/)). Read the ordered candidates with `uv run ~/.pi/agent/skills/fleet/scripts/active_models.py delegation-profile tool-call-delegation`. If Fleet or its profile is missing or invalid, report the setup error before launching an agent.
2. Use the caller's explicit model or effort in place of the default. Restrict eligibility to any driver or provider the caller names. Report an unavailable explicit choice unless the caller authorized a fallback.
3. Use the harness's delegation tools. In T3, load `t3-runtime` and use `orchestrator_capabilities` to match the driver, exact model and effort to an enabled provider that can run child tasks. Search for a model by its exact ID before ruling it out when the short catalog omits it. Map the effort to the option advertised for that model.
4. Divide ready work into bounded batches with distinct results. For example, once the required project instructions are read and the revision is known, source inspection, evidence gathering for a plan audit, and an isolated test run can each go to a fresh worker. One small read needs only one worker. Order calls that require an earlier result or could conflict on shared state.
5. Set a concurrency limit within both caller and harness limits. Launch a fresh worker asynchronously for each ready batch that fits before waiting on any worker. Reserve a slot from launch until the batch and its stateful follow-ups finish and the harness releases the worker. Dispatch the next ready batch as soon as capacity permits.
6. For each batch, try eligible candidates in profile order. Give each launch attempt a unique ID in its startup message, send the startup rules, and ask the child to acknowledge that ID. Record the returned child handle against it. Advance if a candidate is unavailable or if the harness confirms that no child started and no work ran. For an uncertain launch, recover only a child that uniquely matches that attempt. If it remains uncertain, keep its slot reserved, report the blocked batch and its dependents, and continue independent work within the limit. If no candidate can start, report why each failed.
7. Before sending a worker its operations, verify the started or recovered child's provider instance, driver, exact model, and effort against the selected candidate using harness metadata. In T3, use the verified provider instance's driver from capabilities. If a setting differs or cannot be verified, stop the batch, cancel the identified worker if still active, and report the blocked operation.
8. Send each verified worker only its batch context. Give each operation an ID, the exact tool, its arguments or the rule for deriving them, and the evidence you need to verify the result. For shell commands, include the absolute working directory.
   - If one call suffices, send it as is. Group calls when doing so saves a round trip or reduces the output you need to read. Within a batch, use the smallest authorized script that preserves dependencies or mark independent calls for parallel execution.
   - Let the agent chain calls when you can specify how a result determines the next arguments. When the next operation needs your judgment, inspect the evidence before sending it.
   - Bound output at the tool call. Specify the fields, excerpts, or artifact locations to return. When full output is required, retain it in an authorized artifact or return it in identified chunks. Split a large audit by file or section before dispatch so one worker need not read the whole corpus.
   - Keep a follow-up with its worker when it needs worker-local state, such as a running command. Once the batch is done, let the worker finish or close it if the harness requires an explicit release.
   - If evidence is cut off, request only the missing part by ID, cursor, or range. Keep confirmed results. If an operation's outcome is unclear, verify its state before retrying. Retry only work that is still needed and safe to repeat. Report any required evidence you cannot recover.

Give the agent these rules at startup:
- Execute calls as specified. Run calls marked parallel concurrently
- Follow each running command to completion. Return its ID, status, and requested output
- Quote errors exactly. Flag missing or truncated output
- Use a fallback only when its stated trigger occurs and its exact action was supplied
- If a decision is needed, ask the lead agent. Continue independent calls while waiting

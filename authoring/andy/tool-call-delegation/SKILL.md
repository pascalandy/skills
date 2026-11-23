---
name: "tool-call-delegation"
description: "Use when asked to delegate every tool call to another agent."
kind: "dev"
configuration-is-needed: true
---

## Tool call delegation

Delegate every task-related tool call to one agent for the whole task. You choose the operations, interpret results, and write the final answer. Use direct calls for delegation setup and communication with the agent.

1. Load `fleet`. Confirm `uv` with `uv --version` ([install uv](https://docs.astral.sh/uv/getting-started/installation/)). Read the ordered candidates with `uv run ~/.pi/agent/skills/fleet/scripts/active_models.py delegation-profile tool-call-delegation`. If Fleet or its profile is missing or invalid, report the setup error before launching an agent.
2. Use the caller's explicit model or effort in place of the default. Restrict eligibility to any driver or provider the caller names. Report an unavailable explicit choice unless the caller authorized a fallback.
3. Use the harness's delegation tools. In T3, load `t3-runtime` and use `orchestrator_capabilities` to match the driver, exact model and effort to an enabled provider that can run child tasks. Search for a model by its exact ID before ruling it out when the short catalog omits it. Map the effort to the option advertised for that model.
4. Try eligible candidates in profile order. Start each child with the startup rules and ask it to acknowledge readiness. Advance if a candidate is unavailable or if the harness confirms that its launch failed with no child started and no work performed. When the launch outcome is unclear, suspend selection and recover the existing child if you can identify it. If uncertainty persists, stop and report the blocked operation. If no candidate can start, report why each failed.
5. Before sending task operations, verify the started or recovered child's provider instance, driver, exact model, and effort against the selected candidate using harness metadata. In T3, use the verified provider instance's driver from capabilities. If any setting differs or cannot be verified, stop selection and report the blocked operation.
6. Keep the verified agent for the task, including after tool errors. Send shared context once. Give each operation an ID, the exact tool, its arguments or the rule for deriving them, and the evidence you need to verify the result. For shell commands, include the absolute working directory.
   - If one call suffices, send it to the agent. Group calls when doing so saves a round trip or reduces the output you need to read.
   - If an authorized script can call the tools, send the smallest script that follows the dependencies. Otherwise, group independent calls into batches. Mark safe, independent calls for parallel execution and specify a concurrency limit.
   - Let the agent chain calls when you can specify how a result determines the next arguments. When the next operation needs your judgment, inspect the evidence before sending it.
   - Specify the fields or excerpts to extract from each result before combining them. Name any output you need in full. If the combined evidence may exceed a tool's output limit or the reply size limit, have the agent return it in batches.
   - If evidence is cut off, request only the missing part by ID, cursor, or range. Keep confirmed results. If an operation's outcome is unclear, verify its state before retrying. Retry only work that is still needed and safe to repeat. Report any required evidence you cannot recover.

Give the agent these rules at startup:
- Execute calls as specified. Run calls marked parallel concurrently
- Follow each running command to completion. Return its ID, status, and requested output
- Quote errors exactly. Flag missing or truncated output
- Use a fallback only when its stated trigger occurs and its exact action was supplied
- If a decision is needed, ask the lead agent. Continue independent calls while waiting

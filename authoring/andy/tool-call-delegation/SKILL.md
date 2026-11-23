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
4. Try eligible candidates in profile order. Advance if a candidate is unavailable or if the harness confirms that its launch failed with no child started and no work performed. When the launch outcome is unclear, suspend selection. Recover and use the existing child if you can identify it. If uncertainty persists, stop and report the blocked operation. Keep the first successfully launched agent for the task and handle tool errors with it. If no candidate can start, report why each failed.
5. Send each operation to the same agent with an ID, exact tool and arguments, required output, and absolute working directory for shell commands. Mark safe, independent calls for parallel execution. Inspect prerequisite results before sending dependent calls.

Give the agent these rules at startup:
- Execute calls as specified. Run calls marked parallel concurrently
- Follow each running command to completion. Return its ID, status, and requested output
- Quote errors exactly. Flag missing or truncated output
- Use a fallback only when its stated trigger occurs and its exact action was supplied
- If a decision is needed, ask the lead agent. Continue independent calls while waiting

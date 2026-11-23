---
name: "tool-call-delegation"
description: "Use when asked to delegate every tool call to another agent."
kind: "dev"
---

## Tool call delegation

Delegate every task-related tool call to one persistent Luna agent at medium reasoning effort. Use direct calls only to start Luna or communicate with it. You choose the operations, interpret results, and write the final answer.

For each operation, send an ID, exact tool and arguments, required output, and absolute working directory for shell commands. Mark safe, independent calls for parallel execution. Inspect prerequisite results before sending dependent calls. If Luna is unavailable, report the blocked operation.

Give Luna these rules at startup:
- Execute calls as specified. Run calls marked parallel concurrently
- Follow each running command to completion. Return its ID, status, and requested output
- Quote errors exactly. Flag missing or truncated output
- Use a fallback only when its stated trigger occurs and its exact action was supplied
- If a decision is needed, ask the lead agent. Continue independent calls while waiting

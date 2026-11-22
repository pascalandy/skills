---
name: "how"
description: "Use for questions about how code works, code walkthroughs before changes, or questions about placement, ownership, and layering. Use `why` for design motivation."
kind: "dev"
---

# How

Read [the agent runtime contract](../poteto-mode/references/agent-runtime.md) before using runtime tools, loading related skills, or delegating. Use only capabilities and model IDs verified in this session.

Explore the codebase to answer "how does X work?" questions. If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Start one `Worker` with read-only scope that explores and explains in one pass. Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer unfamiliar with this area. Explore the codebase so they walk away with a mental model solid enough to start working in it confidently. You have read-only access. Trace the flow from the entry point through each call and the data it carries, naming concrete files and symbols; read the code rather than guess from names, and say where you could not trace a link. Use these sections, dropping any that do not apply:
>
> - **Overview**: what it is, what it does, and why it exists, in 1-2 paragraphs
> - **Key Concepts**: the types, services, or abstractions needed to follow the rest
> - **How It Works**: the longest section, the traced flow in prose, with a diagram only when it clarifies
> - **Where Things Live**: the files and directories someone needs to start working here
> - **Gotchas**: non-obvious behavior and pitfalls

## 2. Present

Present the worker's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

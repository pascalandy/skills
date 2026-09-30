---
name: "pi-workflow"
description: "Use when the user mentions `turk` or requests subagent execution workflows in Pi."
kind: "dev"
---

If the user's request leverages subagents, orchestrate them with the `subagent` tool and `workflowScript`. Read the `pi-subagents` skill for the execution model; only the model routing below is turk-specific.

## Role → Profile Routing (shuffle with aliases)

Assign each role a **Profile** alias from the catalog below. To shuffle, swap the alias in this table — the catalog resolves it to a full `model` ID. The full ID still goes in `runs.run` / `runs.all` `model`.

| Role         | Responsibility                                                 | Profile       |
|--------------|----------------------------------------------------------------|---------------|
| Planner      | Planning, architecture, task breakdown                         | ds-pro-v4     |
| Reviewer     | Independent read-only quality, security, review                | ds-pro-v4     |
| Builder      | Implementation, targeted edits, single-file tests              | ds-flash-v4   |
| Worker       | General on-demand tasks, ,qa , docs                            | ds-flash-v4   |
| Researcher   | Codebase discovery, API exploration                            | ds-flash-v4   |
| runner       | ci, linters, validation, browser checks, commits               | gpt-luna      |

## Profile Catalog (single source of truth)

Copy-paste pool: alias → full model ID + thinking. Edit here when a provider or thinking default changes.

| Profile       | Model                                          | Thinking | Tier |
|---------------|------------------------------------------------|----------|------|
| ds-pro-v4     | openrouter/deepseek/deepseek-v4-pro-0813       | max      | S    |
| gpt-sol-med   | openai-codex/gpt-5.6-sol                       | medium   | S    |
| gpt-sol-low   | openai-codex/gpt-5.6-sol                       | low      | S    |
| ds-flash-v4   | openrouter/~deepseek/deepseek-v4-flash-latest  | xhigh    | A    |
| gemini-flash  | openrouter/google/gemini-3.8-flash             | medium   | A    |
| gpt-luna      | openai-codex/gpt-5.6-luna                      | medium   | B    |

## Execution Pattern

Resolve the catalog alias to the full model ID on each subagent execution item:

```javascript
subagent({
  workflowScript: `
    const [r1, r2] = await runs.all([
      { key: "review_security", agent: "reviewer",
        model: "openrouter/deepseek/deepseek-v4-pro-0813",
        task: "Review the auth layer for security issues." },
      { key: "fix", agent: "worker",
        model: "openrouter/google/gemini-3.7-flash",
        task: "Fix the auth issues found in review." }
    ]);
    return { security: r1.output, fix: r2.output };
  `
})
```

## Deliverable

A valid `workflowScript` ready to run, with explicit `model` assignments on every `runs.run` / `runs.all` item matching the role table (alias → catalog → full ID).

<!--
Formatting preference:
When editing or creating Markdown tables in this file, always keep table columns visually aligned and padded with spaces across headers, delimiter rows, and data cells so the raw source remains clean, balanced, and readable.
-->
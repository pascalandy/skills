# Profile Routing Matrix

Delegate when a bounded task benefits from a separate agent. Keep trivial work local. Choose only the roles the task needs.

| Role        | Responsibility                                  | Models + reasoning level |
| ----------- | ----------------------------------------------- | ------------------------ |
| Planner     | Planning, architecture, task breakdown          | GPT-6 Astra med          |
| Reviewer    | Independent read-only quality, security, review | GPT-6 Astra med          |
| Oracle      | Escalate any challenges                         | GPT-6 Astra high         |
| Interviewer | ask deep questions                              | GPT-6 Astra med          |
| Builder     | Implementation                                  | GPT-6-Sol high           |
| Worker      | General on-demand tasks, qa, docs               | GPT-6-Luna max           |
| Researcher  | Codebase discovery, API exploration             | GPT-6-Luna max           |
| Runner      | ci, linters, validation, checks, commits        | GPT-6-Luna medium        |

## Delegate

1. Choose the role by responsibility. Pass its model and reasoning level explicitly through the harness's delegation controls. Resolve equivalent model IDs against the harness's supported models. Explicit user choices for the current task take precedence
2. Confirm that the selected profile is supported before launching. If its model or reasoning level is unavailable or cannot be verified, stop and ask the user whether to continue with a named alternative. Substitute only after the user agrees
3. Begin every agent brief with `use $poteto-mode ;`. Include the role, objective, relevant context, allowed changes, and expected result. Resolve `poteto-mode` through the active skill catalog and give the agent its SKILL.md path, or include its applicable instructions when skill loading is unavailable
4. Parallelize independent tasks when useful. Give concurrent writers separate ownership. Keep reviewers read-only and independent of the implementation. Workers execute their bounded role and delegate further only when the parent assigns orchestration
5. Inspect the returned work and evidence before integrating it. Escalate difficult blockers to Oracle with the evidence and previous attempts

Prefer the smallest useful delegation. Optimize for quality first, then total time, tokens, and coordination cost. Delegation does not expand the user's authorized scope.

This skill owns the shared role mappings. Update model choices here so consumers keep one source of truth.

# Slice planning

Use this format within Phase B when the user requests a plan from settled direction, scope, architecture, or a clear brief. Inspect the relevant project context read-only. Name unresolved product decisions instead of inventing acceptance criteria for them.

State the outcome, source inputs, boundary, and non-goals. Define the fewest slices that each produce a demonstrable user, system, or artifact outcome. A text or workflow change can be a slice; it does not need to become code.

For each slice, record:

- Outcome and bounded scope, using known paths or areas rather than invented filenames
- Observable acceptance criteria and the command, preview, inspection, or other proof for each
- Dependencies and shared contracts that must be settled first
- Material risks or unknowns and the checkpoint that resolves them

Order slices by dependencies and risk. Split independent outcomes that require unrelated proof. Keep validation at each completion boundary and follow the pstack migration principles when coordinating an internal contract change.

Return the plan in chat unless a durable artifact is requested or required for handoff. Use the caller's artifact location when supplied. When delivery tickets are requested, resolve `matt-mode` from the active skill catalog, read its `SKILL.md`, then follow its `to-tickets` route within the caller's scope. That contract supplies the shared dependencies and authority rules. This plan retains its technical sequencing decisions and workflow owner. Finish a planning-only assignment with the plan, remaining blockers, and the recommended next action; do not begin implementation.

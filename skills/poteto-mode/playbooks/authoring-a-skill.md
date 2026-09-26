### Authoring or modifying a skill

Read [agent runtime](../references/agent-runtime.md) before choosing delegation, models, skill loading, live controls, state storage, or watchers. Follow its capability checks and report unavailable guarantees.

1. Resolve and load `writing-great-skills` through the runtime contract. Stop with the missing dependency if the authority cannot be resolved.
2. Follow its ownership, placement, invocation, and pruning decisions while this playbook retains delivery sequencing and the reply contract.
3. Validate the actual package and its active consumers using the authority's checks.
4. Run test cases when behavior is structural. Skip them when the result is subjective.
5. Run **Opening a PR**.

**Reply:** summary of the skill, key design decisions, validation notes.

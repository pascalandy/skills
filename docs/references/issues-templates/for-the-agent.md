# Issue section: For the agent

Every issue template ends with this section. Its content is free form, such as technical details, non-functional requirements, or links to related issues and PRs; the subsections are suggestions

````md
## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

### <The evidence, such as the conflicting rules>

File and line numbers, and the real commits, steps, or output that show the failure.

### Acceptance cases

1. case → expected result; mark the one that is the bug

### Edge cases

- edge case → how the fix handles it

### Approaches considered

- **A. <approach>:** <why not>
- **B. <approach> (recommended):** <why>
- **C. Ignore it:** <the cost of leaving the skill as it is>

### Blast radius

Which agents, repos, or workflows the change reaches, why it is safe or risky, and the continuing cost if nothing changes.

### Out of scope

What this fix leaves alone.

</details>
````

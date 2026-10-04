# Issue template: to-spec

Feel free to add more section(s) as needed or to say N/A if not applicable


````md
<spec-template>

## Problem Statement (CMO)

The problem that the user is facing, from the user's perspective. Restate my goal and the problem in your own words

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A detailed, numbered list (ID start at: US_101) of user stories. Each user story should be in the format of:

- US_101: As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
- US_101: As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

List the use cases, edge cases included

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

## Testing Decisions

<details>
<summary>🧪 Tests</summary>

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## How we'll know it works

1. **Before the change:** <rerun the failing scenario with the current skill, in three fresh sessions when the result depends on the agent's choices>. If <it never fails>, the problem doesn't repeat
2. **After the change:** <the same scenario and the result that proves the fix>
3. **Nothing else changes:** <a nearby case that must keep its current result>
4. `just check` passes

</details>

## 👨🏻‍🍳 For the agent

See [👨🏻‍🍳 For the agent](for-the-agent.md)

</spec-template>
````

# Issue template: to-spec

Verbatim copy of the spec template in `authoring/matt/matt-mode/playbooks/to-spec/to-spec.md` (`matt-mode ; to-spec`), taken 2026-10-04. The playbook sets no title rule. Published with label `ready-for-agent`

````md
<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A detailed, numbered list (ID start at: US_101) of user stories. Each user story should be in the format of:

- US_101: As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
- US_101: As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

<!-- Free form, for the agent doing the work; the human reading the issue can skip it: technical details, non-functional requirements, links to related issues or PRs, etc. -->

</details>

</spec-template>
````
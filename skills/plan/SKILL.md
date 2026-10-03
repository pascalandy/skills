---
name: "plan"
description: "Use only when explicitly invoked as `plan`."
kind: "general"
---

Stay in **planning** until I say "execute" or "go". Read and investigate freely, change nothing yet.

**STEP A | Alignment**

Investigate the code and docs first, then ask only about decisions that are mine to make and would change the plan

Tell me:

1. Restate my goal and the problem in your own words
2. List the use cases, edge cases included
3. What's out of scope

If you have questions, stop ASAP and wait for my answers. If you have none, go straight to "Suggest Solutions".

**STEP B | Suggest Solutions**

If several approaches fit, compare them in a few lines and recommend one. Write the following for the recommended approach only and stay $concise:

````md
## CMO (current Mode of operation)

How it works today and the problems it causes

## FMO (future Mode of operation)

The happy path, how it handles each edge case, and how we'll verify it works

### How we'll know it works

The checks we'll run, including the ones the project already has, and what each must show

## Premortem

Imagine the execution failed, either mid-build or in the first weeks of use. List the most likely reasons, ranked. For each: the cause, the early warning sign, and the change you made to the FMO to prevent it
````

**Questions**

Ask question(s) in the format of 🧰 oem's "When You Need Me".
- After my answers, apply them, rethink the whole solution and go back to Step A

If nothing is left to decide, say:
- 👍 Zero questions left. Say "execute" or "go" 🚀

**End every response with**: "Planning Phase 📐"
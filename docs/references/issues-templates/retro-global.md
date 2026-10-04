# Issue template: retro-global

````md
<retro-global>
## The problem (CMO)

**Area:** <Navigation, Automated checks, Steering files, Tool economy, No-ops, or Information access>

**Problem Statement:** As an agent working in `<repo>`, I want <…>, so that <…>

REF: #<PR or issue>

### Analogy

An everyday analogy in one or two sentences.

- **What should happen:** <in the analogy's terms>
- **What happened in #<PR>:** <what the agent did, in the analogy's terms>

### What happened

What the agent was trying to do, what went wrong, and how it worked around it. Say plainly what it cost: time, tokens, or a wrong result.

### What exists today

The check, file, or tool already in place, and why it did not help: missing, unwired, or silently broken.

## FMO: Start, Stop, Continue

- **Start:** <what the agent or its environment starts doing>
- **Stop:** <what it stops doing>
- **Continue:** <what already works and must keep working>

**The change:** <the smallest edit, and where: file, recipe, hook, or tool>

## How we'll know it works

1. **Before the change:** <rerun the scenario that failed>
2. **After the change:** <the same scenario and the result that proves the fix>
3. **Nothing else changes:** <the Continue case keeps its current result>

## 👨🏻‍🍳 For the agent

See [👨🏻‍🍳 For the agent](for-the-agent.md)

</retro-global>
````

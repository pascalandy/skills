# Meta-skill creator

Create one user-facing skill that selects the smallest relevant internal branch without making the user learn its taxonomy.

A meta-skill is justified when several substantial branches solve the same kind of problem, share one contract, and require different instructions after invocation. It is not justified merely because several methods can be listed together.

## Step 1: establish the owned problem

Determine:

- the one problem class the root skill owns
- the requests that should invoke it
- the neighboring skills that must keep ownership of adjacent work
- the result that tells an agent the run is complete
- the invocation mode and export location

Use context already supplied. Ask only for a missing choice that would materially change the skill or write location.

This step is complete when the skill can be described as one job with an observable completion criterion and explicit boundaries.

## Step 2: prove that branches are real

For each proposed branch, identify:

- the uncertainty or outcome it uniquely owns
- the user signal that selects it
- the instructions needed only on that branch
- the tie-breaker against its closest sibling
- the completion criterion

Merge branches that differ only in tone, depth, examples, output formatting, or vocabulary. Move optional techniques into references instead of promoting them to branches.

Select one branch by default. Compose branches only when the first completes and exposes a different unresolved problem. Never apply every branch for coverage.

This step is complete when every surviving branch changes the agent's process and no request pattern has two owners without a tie-breaker.

## Step 3: choose the shallowest sufficient structure

Prefer the first structure that keeps routing predictable.

### Conditional references

Use this for a small set of branches whose selection table fits cleanly in `SKILL.md`:

```text
skill-name/
├── SKILL.md
└── references/
    ├── branch-a.md
    └── branch-b.md
```

The root owns the route and points directly to each reference. Do not add a `ROUTER.md` that repeats the same table.

### Routed collection

Use this when the routing decision is substantial enough to obscure the root contract or when branches need their own disclosed files:

```text
skill-name/
├── SKILL.md
└── references/
    ├── ROUTER.md
    ├── branch-a/
    │   ├── MetaSkill.md
    │   └── references/
    └── branch-b/
        └── MetaSkill.md
```

Only the root is named `SKILL.md`. Use `MetaSkill.md` for internal executable branches when recursive scanners would otherwise register competing skills. Use ordinary Markdown files for reference-only topics or operations.

This step is complete when no shallower structure provides equally clear routing and progressive disclosure.

## Step 4: write the root interface

Keep in `SKILL.md` only what every run needs:

- concise frontmatter with a discriminating invocation rule
- the shared contract and safety or evidence rules
- ordered steps with checkable completion criteria when the skill has a process
- the minimal branch-selection logic
- boundaries and handoffs that prevent likely misrouting
- context pointers that say exactly when to load each disclosed file

Do not require problem and solution marketing, a full branch catalog, keyword inventories, installation prose, usage examples, or customization sections. Include one only when it changes agent behavior.

The user should be able to state the job in ordinary language. Never require a branch name.

This step is complete when the root can route a naive request without loading irrelevant branch instructions or duplicating another file's rules.

## Step 5: build each branch

Put branch-specific definitions, procedure, evidence rules, examples, and output constraints together. Use relative bundled paths and tell the agent when to read them.

For a routed collection, keep routing decisions in one place. The root points to `references/ROUTER.md`; the router points to branches; a branch does not restate the full routing table.

Keep internal branches invisible to skill scanners. Do not make them independently invocable unless they have a genuinely separate trigger and deserve the additional discovery cost.

This step is complete when each branch can execute its owned work without reading sibling branches and every bundled file is reachable through a conditional pointer.

## Step 6: validate the result

Check all of the following:

- folder and frontmatter names match
- string frontmatter values are quoted
- invocation policy matches the requested mode
- bundled paths are relative and resolve
- only intended `SKILL.md` files are scanner-visible
- every realistic request selects one owner
- tie-breakers cover overlaps
- one branch runs by default
- composition has a stated reason and stopping condition
- each meaning has one authoritative location
- no stale branch, placeholder, or unreferenced file remains
- the repository's skill and sync checks pass

For a consequential refactor, preserve realistic routing cases outside the normal runtime path and test against them. Validate behavior, not exact prose.

The meta-skill is complete when a user can invoke one name, describe the desired outcome without taxonomy, and receive the right branch with no irrelevant branch loaded.

## Portability

Follow repository policy for source and applied paths. Inside generated skills, resolve files relative to the loaded `SKILL.md` or `MetaSkill.md`. Do not hardcode an assistant home, assume a particular agent harness, or require subagents unless the skill's actual job needs them.

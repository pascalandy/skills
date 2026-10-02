# Patterns

Patterns for documents with steps, examples, templates, or a validation step. Each `BP_` section explains one best practice listed in `SKILL.md`.

## BP_07 No dated text

A line such as `If you're doing this before August 2025, use the old API` goes wrong once the date passes. Write the current method, and move a deprecated one into a collapsed section that records when it was deprecated:

```markdown
## Current method

Use the v2 API endpoint: `api.example.com/v2/messages`

## Old patterns

<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>

The v1 API used `api.example.com/v1/messages`. This endpoint is no longer supported.
</details>
```

## BP_08 Concrete examples

When output quality depends on seeing examples, give input/output pairs, then state the style in one line. One pair per distinct pattern; a second pair of the same pattern adds load, not signal:

````markdown
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

Follow this style: type(scope): brief description, then the detailed explanation.
````

Match a template's strictness to the output:

- **Strict**, for API responses or data formats: "ALWAYS use this exact template structure", followed by the exact skeleton
- **Flexible**, when adapting helps: "Here is a sensible default format, but use your best judgment", followed by a skeleton whose sections say what to adapt

## BP_09 Workflows

Break a complex operation into numbered steps. For a long one, give a checklist the agent copies into its reply and checks off. The checklist also shows the human who designs the workflow the whole sequence at a glance:

````markdown
Copy this checklist and track your progress:

```
Task progress:
- [ ] Step 1: Analyze the form (run scripts/analyze_form.py)
- [ ] Step 2: Create the field mapping (edit fields.json)
- [ ] Step 3: Validate the mapping (run scripts/validate_fields.py)
- [ ] Step 4: Fill the form (run scripts/fill_form.py)
- [ ] Step 5: Verify the output (run scripts/verify_output.py)
```

**Step 3: Validate the mapping.** Run `uv run scripts/validate_fields.py fields.json`. Fix every error before continuing.
````

The same shape works without code: a research synthesis reads every source, finds the themes, cross-references each claim, writes the summary, then verifies the citations, returning to the cross-reference step when one is missing.

At a decision point, name the cases and send each to its own branch:

```markdown
1. Determine the modification type:
   **Creating new content?** Follow "Creation workflow" below
   **Editing existing content?** Follow "Editing workflow" below
```

## BP_10 Completion criteria

Every step ends on a **completion criterion**, the condition that tells the agent the step is done. Two properties make it a lever:

- **Clarity**: can the agent tell done from not done? A vague bound, such as "understanding reached", invites **premature completion**: the visible steps ahead pull attention toward being done. Sharpen the bound first. Only if it stays fuzzy and you observe the rush, hide the later steps by splitting the sequence across a real context boundary, a hand-off or a subagent; an inline call leaves the later steps in context
- **Demand**: how much the criterion requires. "Every modified model accounted for" forces thorough work where "produce a change list" does not. Demand drives the legwork within a step, and it binds reference too: "every rule applied" sets an exhaustiveness bar on a flat list

The strongest criteria are both checkable and exhaustive. Split a sequence only where the later steps tempt the agent to rush the current one; merging sequences exposes each step to the steps after it.

## BP_11 Feedback loops

Run the validator, fix the errors, repeat. A script makes the strongest validator, because passing is a fact the agent cannot argue with:

```markdown
1. Make your edits to `word/document.xml`
2. Validate immediately: `uv run scripts/validate.py unpacked_dir/`
3. If validation fails, read the error, fix the XML, and run validation again
4. Only proceed when validation passes
```

Without code, a reference document is the validator: draft against `STYLE_GUIDE.md`, review against its checklist, note each issue with its section, revise, and review again until every item passes.

Give the loop a rule for when to stop: rerun only the checks a fix invalidated, and stop when each finding is fixed, accepted, or reported. A second-pass review skill, such as `2nd-pass`, follows this shape.

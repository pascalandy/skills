---
name: "2nd-pass"
description: "Use when the user asks for a `2pass` or a second pass, fresh-eyes review, final cleanliness check, or pre-delivery audit of work and related artifacts."
---

# 2nd Pass

Now do a 2nd pass.

Review the requested deliverable against the user's requirements and the evidence available. Identify concrete mistakes, missing requirements, contradictions, or defects that affect its use.

Inspect related docs, skills, and project files only when the deliverable or current changes directly affect them. State the review boundary before expanding a check. Record unrelated pre-existing issues separately rather than turning the pass into a general project audit.

- Only if you see impacts on `/docs`, use and reload `$pa-doc-update`.

## Quality Bar

The deliverable must satisfy the requested outcome and its direct dependencies. Correct in-scope defects when fixes are authorized; otherwise report them with evidence.

Ensure we follow the DRY principle (don't repeat yourself)

Stop when the deliverable and its direct effects have been checked and each finding is fixed, explicitly accepted, or reported as unresolved. Rerun only checks invalidated by a correction or needed to settle a remaining finding. Do not add another review solely to obtain a cleaner verdict.

## Final Response

### A) Your Analysis

List proof of work from previous steps plus a completion audit.

### B) Needs My Input

Include this section only if input is needed.

If you need user input, use and reload `$sparring` for each unresolved decision or unapplied fix requiring user judgment.

For each unresolved decision, include:

- why autonomous action is risky
- options
- recommendation
- confidence
- evidence that would change your mind

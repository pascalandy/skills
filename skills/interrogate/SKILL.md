---
name: "interrogate"
description: "Use when the user asks for an adversarial or multi-model review, wants code or a plan stress-tested, or asks to uncover blind spots."
kind: "dev"
---

# Interrogate

Read [the agent runtime contract](../poteto-mode/references/agent-runtime.md) before using runtime tools, loading related skills, or delegating. Use only capabilities and model IDs verified in this session.

Spawn independent reviewers to adversarially review code changes. Each reviewer gets the same prompt and rubric. Different model families add diversity; separate contexts on one model preserve independent reviews but do not provide that diversity.

The deliverable is a synthesized verdict. Do NOT auto-apply changes.

## Step 1, Determine Scope

Identify what to review from context:

- If the user points at specific files or a diff, use that
- If on a feature branch, run `git diff main...HEAD` (or the appropriate base branch) for the full changeset
- If the user's message references recent work, gather the relevant files

Package the diff (or file contents) plus any surrounding context files the reviewers need to understand the code.

## Step 2, State the Intent

Before spawning reviewers, state the intent explicitly. Derive this from:

- The user's message
- Commit messages
- PR description if one exists
- The code itself

Write one clear paragraph. If you're unsure about the intent, ask the user before proceeding.

## Step 3, Spawn Reviewers

Launch four independent read-only agents with the `Reviewer` role. Use the same evidence snapshot and prompt for every reviewer, without sharing their findings before synthesis. A sequential run in separate contexts preserves independence when concurrency is unavailable. A parent self-review does not complete this review.

Read `references/reviewer-prompt.md` and fill in the template with:
1. The stated intent
2. The diff or file contents
3. The review rubric from `references/rubric.md`
4. The code-quality lens from `references/code-quality-review.md`

The same filled template goes to all reviewers, so every reviewer applies the code-quality lens.

## Step 4, Synthesize

As results come back, build a unified picture:

1. **Parse all findings** from the reviewers
2. **Identify consensus**. Count findings raised by two or more independent reviewers. Report the reviewer count and distinct model-family count separately; repeated reviews on one model are not cross-model consensus.
3. **Identify lone-reviewer findings**. Still worth reading, but weight accordingly.
4. **Deduplicate**. Different reviewers may describe the same issue differently. Merge these and note each reviewer and model family.
5. **Note disagreements**. If one reviewer flags something and another explicitly says the opposite, that's useful context for the verdict.

## Step 5, Lead Judgment

You are the lead reviewer, a pragmatic senior engineer, not a neutral aggregator.

Read `references/lead-judgment.md` for the full framework.

Categorize every finding using these buckets:

- **Act on**. Real issues affecting correctness, security, or maintainability given the actual goals. These would block a real PR.
- **Consider**. Legitimate points, but you're not sure they outweigh the cost of addressing them right now. Worth the user's attention.
- **Noted**. Technically valid but not actionable. Context-dependent, premature optimization, or low-impact given the current stage.
- **Dismissed**. Wrong, nitpicky, or missing context. Brief explanation why.

For each finding, include:
- Which reviewers raised it, with their models and distinct family count
- The category (act on / consider / noted / dismissed)
- A one-line rationale for the categorization

## Output Format

Present the verdict in this structure:

### Intent
> [The stated intent paragraph from Step 2]

### Reviewers
- Reviewer [label]: [model name], [N findings] (one bullet per reviewer)

### Act On
[Findings that should be addressed. For each: description, which reviewers raised it and how many model families they represent, why it matters.]

### Consider
[Findings worth thinking about. For each: description, which reviewers raised it and how many model families they represent, tradeoff involved.]

### Noted
[Valid but low-priority. Brief list.]

### Dismissed
[Rejected findings with brief rationale.]

### Agreement Map
[Where did independent reviewers agree or diverge? State the reviewer and distinct model-family counts, then explain what that evidence supports.]

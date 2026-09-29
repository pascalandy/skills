---
name: "no-comments"
description: "Use only when explicitly invoked as `no-comments`, including `No comments` as an instruction."
---

# No comments

Read [the agent runtime contract](../poteto-mode/references/agent-runtime.md) before using runtime tools, loading related skills, or delegating. Use only capabilities and model IDs verified in this session.

Complete an evidence-backed review of the scoped comments. Missing custom personas or delegation capabilities never terminate the review.

## Scope

Use the caller's files or diff. Otherwise use the current diff against the base branch, default `main`, including the working tree.

## Canonical review brief

Review only scoped comments. Identify stale or contradicted statements, narration of obvious code, and claimed constraints that could be enforced in code. Preserve comments explaining non-obvious intent, public usage, or constraints outside our control. Return proposed deletions and evidence, plus separate suggestions for encoding constraints. Do not edit application code or delete comments merely because they exist.

## Steps

1. Resolve the review scope from the caller or the current diff. Finish when the file set and base are explicit
2. Use an independent reviewer with the `Reviewer` role when native delegation is available. Give it the canonical brief. If a Comment Sicko definition is available through normal runtime discovery, it may supplement the brief; do not search broadly for it, announce its absence, or treat it as required. If independent delegation is unavailable, perform the canonical review in the current context. Finish when every scoped comment has a finding with evidence or an explicit keep decision
3. Inspect the review against source. Reject scope escapes and unsupported deletions. For ambiguous intent or constraint claims, run `how` or `why` on the symbol before deciding. Keep comments whose purpose remains unresolved and report the gap. If a custom persona returns specialized verdict labels, interpret them using its loaded definition, not an inferred policy. Finish when every proposed deletion is accepted, rejected, or kept as unresolved
4. Fix trivial accepted flags directly by deleting a dead path, dropping a parameter, or using the real API. If any fix needs a shape, run `/architect` once for the accepted set and surrounding code. Stop at the sketch. Architect shapes. Step 5 implements. Finish when every trivial flag is fixed or recorded as non-trivial
5. Implement the smallest root-cause fix in scope. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open. The **principle-fix-root-causes** and **principle-redesign-from-first-principles** skills guide intent only. Neither authorizes widening the fence nor fixing instances outside it. Never bolt on symptom guards. Finish when accepted findings are fixed or explicitly left open
6. Constraint comments say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave keeps about things we cannot change. Offer the cheapest in-scope type, runtime, test, or CI lint. Wait for interactive approval. Unattended and eval require caller pre-approval. If approved, encode then delete. Otherwise keep the constraint comment, report it open, and sketch out-of-scope work. Finish when every constraint comment is kept or replaced by an approved enforcement
7. Report the findings, deletion count, restored comments, reruns, architect sketch, fixes, encoding offers, encodings, unenforced constraints, and other open work. If the current context performed the review, mention the lack of independent verification after the findings, never instead of them

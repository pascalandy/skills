## Ticket comments

Write or update an issue comment only when the user explicitly asks for one.
Triage, issue creation, PR links, and label changes do not imply a comment.

When preparing a requested comment, read and apply the `sparring` playbook of the
active `andy-mode` skill once per run, including for read-only previews. If
unavailable, withhold the comment and report the missing dependency; the requested
comment remains incomplete.
Use its reasoning discipline to help the human decide or act; keep the comment
proportional to the decision, without manufacturing a debate.

Keep one concise decision comment per issue. Explain verified changes, not intended
ones; a partial failure must not produce a prompt claiming prerequisites are met.
In read-only previews, describe label edits as proposed, never completed.

Mark the managed comment with `<!-- label-for-issues:decision -->` and retain its
comment ID. `gh issue comment <n> --body-file <file>` prints the new comment's URL,
which ends in `#issuecomment-<id>`; `gh issue view <n> --json comments` lists the
same URLs. Edit by that ID with
`gh api --method PATCH repos/OWNER/REPO/issues/comments/<id> -F body=@<file>`,
because `gh issue comment --edit-last` picks the account's newest comment, which can
be a human's. Edit that exact comment only when its provenance establishes it as an
agent-managed triage comment through a recorded prior write or an explicit agent
signature consistent with its triage content. A marker or shared GitHub account
alone is insufficient.
Adopt an unambiguously agent-written legacy triage comment by adding the marker.
Otherwise create one without altering human comments. If ownership is ambiguous or
multiple managed comments exist, report the conflict rather than adding another.
Recheck the selected comment before editing and preserve intervening human additions.

When asked to update it, refresh that comment when the evidence, options, or
recommendation changes, even if the labels stay the same. Leave it untouched when
both labels and reasoning remain current; recover missing comments after partial
failures.

End every comment you create or update with the signature from $oem.

Format comments in this order, omitting sections with no applicable action:

1. Start with one H2 combining issue number, next actor, and action:
   `## #52 · Waiting on Pascal to choose the test environment` or
   `## #57 · Agent can audit specification compliance`
   Do not repeat the issue title, status, or owner in another heading or bold banner
   If no action is needed, say so rather than inventing a decision or task
2. Give brief evidence explaining the current state and successful label changes.
   Link the decisive source, such as a comment, PR, or verification result. Distinguish
   a reported claim from something verified; do not infer completion from labels
   For `1-needs-info`, name missing inputs, why they matter, who supplies them,
   and what they unblock. When removing a blocker, explain what resolved it
3. For a human decision, offer meaningful A/B/C choices with consequences.
   For new choices, put the evidence-backed recommendation first, formatted like
   `- **A · Use an existing test environment. (recommended)** Provide node access`
   Format B and C likewise without the recommendation marker. When updating, preserve
   existing option letters and their meanings; move the recommendation marker instead
   of reassigning letters. Interpret replies against the choices the person answered.
   Give the benefit and
   main cost or risk of each real alternative. If evidence cannot support a choice,
   recommend the smallest information-gathering step instead of guessing. Use fewer
   choices when no meaningful alternative exists. Do not reopen a settled decision
   without new evidence, or repeat “choose one” beneath a
   heading already naming the decision, or invent approval gates for authorized work
4. For agent-executable work, add an H3 stating when its prompt applies, such as
   `### Agent prompt after choosing A`, followed by a fenced text prompt.
   Include repository/issue references, concrete task, required inputs, scope,
   verification, deliverable, and stopping conditions. State whether work can start
   now or depends on a decision/access. Separate human decisions from agent execution;
   do not assign technical work to a human merely because access is missing.
   Reuse issue requirements by reference instead of copying entire specifications.
   Provide a prompt only for the recommended or already chosen path; add alternatives
   only when they need different handoffs. A prompt does not itself authorize
   execution, closure, merge, or publication

Keep comments proportional: brief context, bold option labels only, no duplicate
recommendation paragraph, no periods at bullet ends. Before posting, check that
readers can identify who acts next, choose an option, and hand agent work off
without reconstructing the investigation. Read-only requests produce previews only.

# FinalizeWithWriteDownPostmortem

Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory for the postmortem export protocol after the postmortem content is final.

## When To Use

- The user asks to save the postmortem
- The workflow explicitly requires writing it down in the project
- The session review is complete and ready to persist

## Method

1. Confirm the session-review content is final.
2. Pass the final content through the postmortem profile in `pa-doc-update`'s `references/export-artifacts.md`.
3. Write the artifact to the resolved `export_path` from that profile.
4. Return the resulting folder path, file path, and slug.

## Do Not

- Save partial notes
- Bypass the utility with ad hoc file placement

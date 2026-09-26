# Session Review Example

## What We Did

1. Reviewed the user's core postmortem instruction.
2. Compared candidate structures against the user's actual workflow.
3. Simplified the design to three sub-skills.

## Elements Worth Remembering

### 1. The user's postmortem process is conversation-first

**MEMORY TYPE:** observation

The user values reverse-engineering the session more than maintaining a heavy knowledge base.

### 2. Export belongs in the active project

**MEMORY TYPE:** decision

The final write step should read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its postmortem export protocol inside the current project.

## What Went Wrong

- Early export assumptions were too absolute-path specific.

## What We Discovered

- The save workflow should be shared across all postmortem modes.

## Fixes Applied

- Replaced custom export logic with the postmortem profile in `pa-doc-update`'s `references/export-artifacts.md`.

## Feedback for the Agent

- Confirm the user's actual write target before designing export logic.

## Feedback for the User

- The lean three-mode structure fits the stated workflow well.

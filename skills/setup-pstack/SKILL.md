---
name: "setup-pstack"
description: "Use for /setup-pstack, configure pstack models, or changing pstack's model choices."
kind: "dev"
---

# Setup pstack

Update the `profile-routing-matrix` route of andy-mode, the shared source of delegation preferences. Resolve `playbooks/profile-routing-matrix.md` in the active `andy-mode` skill directory.

## Steps

### 1. Read current choices and capabilities

Read the matrix and its routing rules. Inspect the active runtime's delegation tool schema and supported model listing. A model selectable in the main conversation is not necessarily selectable for a worker. Identify which requested models and reasoning levels the worker interface supports and report any that cannot be verified.

### 2. Choose mappings

Apply choices already supplied by the user. Ask only about unresolved preferences. Follow the matrix's rule for unavailable models and reasoning levels.

### 3. Update the matrix

Follow repository source-of-truth rules and edit the managed source of `andy-mode/playbooks/profile-routing-matrix.md`. Preserve unrelated roles and routing rules. These mappings also apply to delegation outside pstack.

### 4. Verify and report

Read back the matrix and confirm the requested roles, models, and reasoning levels. Check that the relative reference resolves. Report the source path, changed choices, and any unverified runtime support. Distinguish source edits from deployment; use the repository's distribution workflow only when requested.

### 5. Offer verification when useful

If the project has no way to drive its real app for proof, offer `/create-verification-skill` once. Run it only if requested.

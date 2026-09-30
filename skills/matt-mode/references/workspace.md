# Workspace conventions

Read only when an artifact needs a destination or an existing map needs its storage conventions resolved.

For `to-tickets`, the destination, publication authorization, and local export rules in [local adaptations](local-adaptations.md#workspace-and-tracker) take precedence over the defaults below.

1. Honor the user's supplied path or tracker and the repository instructions. Read existing `docs/agents/issue-tracker.md` and `docs/agents/domain.md` when present, or the equivalent files those instructions identify. Read relevant glossary and ADR pointers. A Git remote identifies a repository, not permission to publish there.
2. Reuse the project's established artifact locations. Without a convention, an authorized local artifact defaults to `.scratch/<effort>/` in the current workspace. Use `spec.md`, `map.md`, `decisions/` for decision records, and `issues/` for delivery tickets. Distinct record types get distinct files and identities. Existing maps may use another layout; interpret their types and links before changing anything.
3. A request to write an artifact can use that local fallback without a setup interview. A request only to discuss, outline, or draft in chat stays in chat. Ask about destination only when a material ambiguity remains. Save workspace configuration only when requested; no new configuration file is required to use the mode.
4. For an authorized external tracker, discover its actual read/write capabilities and existing labels. Create records before linking their identifiers. Prefer native dependency relationships when supported; otherwise use explicit blocking links in the record. On GitHub, use the commands and traps in the GitHub CLI section of the active `label-for-issues` skill. Use only agreed labels and statuses. If the requested destination is unavailable, report it and retain a clearly identified local or in-chat draft without claiming publication.
5. Before retrying a write or resuming an interrupted batch, inspect existing records and update the intended identities rather than creating duplicates. Read back the saved artifact and relationships. Return working paths or links and distinguish drafts, unresolved decisions, and ready deliveries.

Domain terminology and glossary formats remain owned by the internal [domain-modeling procedure](../playbooks/domain-modeling/domain-modeling.md). Configuration is resolved once per effort and revisited only when the destination changes or the recorded convention fails.

## Local Wayfinder operations

For the local tracker, the map is `map.md` and child decisions live in `decisions/<NN>-<slug>.md`. Use the upstream map and question bodies. Keep tracker metadata above each question: `Kind: decision`, `Type: research | prototype | grilling | task`, `Status: open | closed`, `Claimed by`, and `Blocked by`. Preserve an existing map's equivalent fields when resuming it.

Enumerate the decision files to query open children. A frontier record is open, unclaimed, and has only closed blockers. Report missing blockers or dependency cycles before selecting a record. Claim by recording the current worker before work. A local file claim is not an atomic multi-agent lock; use one writer per map or a tracker with supported concurrent claims.

Append a resolution section to the decision file, close its status, and add the upstream context pointer to Decisions so far. An excluded decision is closed with the reason and linked from Out of scope. Supplied evidence remains linked to its source. Delivery tickets live under `issues/`, never in this decision queue.

## GitHub Wayfinder operations

On GitHub, the map is an issue labelled `wayfinder:map` and each ticket is its sub-issue. Create a ticket with `gh issue create --parent <map>`. Wire a blocking edge with `--blocked-by` when the blocker already exists, otherwise with `gh issue edit <ticket> --add-blocked-by <blocker>` in the second pass. A frontier ticket is open, unassigned, and has only closed blockers; take the oldest first. List the open, unassigned tickets, then drop those with an open blocker using the filter in `label-for-issues`' GitHub CLI section:

```sh
gh issue list --repo OWNER/REPO --limit 200 \
  --search "parent-issue:OWNER/REPO#<map> is:open no:assignee sort:created-asc" \
  --json number,title,labels,blockedBy
```

Claim a ticket with `gh issue edit <ticket> --add-assignee @me`. Like a local claim, it is not an atomic lock.

# Ontology Router

Dispatch table for choosing the right sub-skill. Read this first on every invocation; load only the sub-skill `MetaSkill.md` that matches.

---

## Inputs Required

Before routing, confirm these from the user prompt (or host call). Flag names are shorthand; equivalent natural phrasing is accepted.

| Argument | Default | Notes |
|----------|---------|-------|
| `input`  | required | Directory to walk recursively. If the user provides a single file, refuse and ask for a directory. |
| `out`    | `<input>/_ontology/` | Output directory for the 5-file ontology |
| `--force` | off | Ignore cache on Update, regenerate everything |
| `--check` | off | Force routing to Check regardless of state |

If `input` is missing or points to a file rather than a directory, ask once: *"Which directory is the corpus?"* Do not guess.

---

## Skill-Context Preflight

Run this **before** the decision tree.

Inspect `input`:

- If `input` contains both `SKILL.md` **and** a `references/` subdirectory, it is a skill root, not a corpus root.
- Do **not** proceed with the skill root as corpus. Ask once:
  > *"`<input>` looks like a skill. Scope the corpus to `<input>/references/` and write to `<input>/references/_ontology/`? (Y / override)"*
- On confirmation: reassign `input := <input>/references/`, `out := <input>/references/_ontology/`, then resume routing.
- On override: honor the user's paths verbatim and continue.

This prevents mining `SKILL.md`, `ROUTER.md`, and sub-skill `MetaSkill.md` files as if they were corpus, and keeps the 5-file artifact out of the skill's top level.

---

## Decision Tree

Apply in order. First match wins.

1. **User explicitly asks for status check** (triggers: "status", "is the ontology stale", "check ontology status", `--check`)
   -> **Check** -- load `references/ontology/Check/MetaSkill.md`.

2. **Output dir is absent OR the output dir has no `INDEX.md`**
   -> **Create** -- load `references/ontology/Create/MetaSkill.md`.

3. **Output dir exists AND `INDEX.md` exists BUT one or more of the 4 required files is missing**
   -> **Update** in "repair" mode (equivalent to `--force`) -- load `references/ontology/Update/MetaSkill.md`. Report the repair in the run summary.

4. **Output dir exists AND all 5 files are present**
   -> **Update** -- load `references/ontology/Update/MetaSkill.md`. Respect the cache unless `--force` is set.

---

## Trigger Keywords -> Sub-skill

| Phrase / flag | Sub-skill |
|---------------|-----------|
| "build an ontology", "create an ontology", "map concepts in <dir>" | Create (if no INDEX) or Update (if INDEX) |
| "refresh the ontology", "update the ontology", "regenerate ontology" | Update |
| "rebuild from scratch", "wipe and regenerate", `--force` | Update with cache ignored |
| "is the ontology stale", "ontology status", "check status", `--check` | Check |
| Host call from `wiki-map` Compile / FullSweep --deep | Router decides based on output-dir state |
| "andy-mode ; ontology" alone with no verb | Router decides based on output-dir state; default action is Create-or-Update |

---

## Ambiguity Handling

- **Bare `andy-mode ; ontology` with no input dir** -> ask: *"Which directory is the corpus? And where should I write the 5-file ontology?"*
- **"Update" requested but no existing `INDEX.md` at `out`** -> run Create, note in the summary that no prior ontology was found.
- **"Create" requested but an `INDEX.md` already exists at `out`** -> ask once: *"An ontology already exists at `<out>`. Replace it (run Create, discard existing), or refresh it (run Update)?"* Default on no answer: Update.

---

## Host Delegation Contract

When `wiki-map` (or any other host) calls the `ontology` route:

- The host passes `input` and `out` explicitly.
- The host does **not** pre-lint the output dir; the `ontology` route inspects state and picks Create or Update itself.
- On return, the host receives a run summary: action taken (Create / Update / Check), files written, corpus metrics, cache hit count, and any empty-state flags.
- Hosts handle drift detection, tagging, and LOG entries **after** the sub-skill returns.

---

## Output of Routing

Before loading the sub-skill, restate the decision in one line:

```text
Routing: <Create|Update|Check> | input=<path> | out=<path> | force=<bool>
```

Then load the chosen `MetaSkill.md` and follow its workflow.

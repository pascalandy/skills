---
name: sdlc-pa artifact export
description: Shared artifact export protocol for PA artifacts
tags:
  - area/ea
  - kind/doc
  - status/open
  - bucket/sdlc-pa
date_created: 2026-05-04
date_updated: 2026-09-09
---

# PA artifact export

Some PA skills produce durable artifacts. When they do, they read this reference from the active `pa-doc-update` skill instead of recreating file placement rules in each skill. This reference owns export conventions, not a lifecycle or execution workflow. The `.sdlc-pa.yml` configuration format remains supported.

The goal is consistency: every exported artifact should have a predictable folder, filename, slug, and handoff shape.

## Export root resolution

Unless a skill says otherwise, resolve the lifecycle artifact export root from the first available value:

1. explicit user-provided path
2. project config: `.sdlc-pa.yml` (`exports.root`, or `exports.public_default_root` when `exports.root` is absent)
3. project instruction file such as `AGENTS.md`
4. public default: `docs/sdlc`

A project overrides the public default in `.sdlc-pa.yml`, for example with `exports.root: docs/ideas/references`.

Each lifecycle item lives in one dated entry folder under the resolved export root. Later artifacts for the same item should be written alongside the original file:

```text
<export_root>/YYYY-MM-DD-entry_slug/
  idea-entry_slug.md
  vision-entry_slug.md
  architecture-entry_slug.md
  impl-plan-entry_slug.md
  postmortem-entry_slug.md
```

## Shared path variables

Every exporting skill resolves these variables before writing the artifact:

| Variable | Rule |
|---|---|
| `export_root` | Resolved by export root resolution; public default: `docs/sdlc` |
| `entry_slug` | 2-4 word kebab-case title |
| `export_date` | Resolve by running `date '+%Y-%m-%d'` |
| `export_dir` | `export_date-entry_slug/` |
| `artifact_kind` | Skill-specific prefix, such as `idea`, `vision`, `architecture`, `impl-plan`, or `postmortem` |
| `export_file` | From `exports.artifact_files.<artifact_kind>` when configured; otherwise `artifact_kind-entry_slug.md` |
| `export_path` | `export_root/export_dir/export_file` |

## Slug and folder rules

1. Prefer a strong user-provided title.
2. Otherwise derive a conservative slug from the request or artifact topic.
3. Use lowercase kebab-case.
4. Use 2-4 meaningful words.
5. Do not include the artifact kind in the slug unless it is part of the actual topic.
6. If a dated folder already exists for the same `entry_slug`, reuse that folder so related artifacts stay together.
7. If multiple folders match the same `entry_slug`, reuse the one containing the source artifact for this run. If none is obvious, choose the newest matching folder and state that choice.
8. If no matching folder exists, resolve today's date by running `date '+%Y-%m-%d'`, then create `export_date-entry_slug/`.
9. Resolve the slug and folder before editing or writing the artifact.

## Worked example

Vision artifact about "cron retry policy" when `date '+%Y-%m-%d'` returns `2026-05-04`:

- `entry_slug`: `cron-retry-policy`
- `export_date`: `2026-05-04`
- `export_dir`: `2026-05-04-cron-retry-policy/`
- `artifact_kind`: `vision`
- `export_file`: `vision-cron-retry-policy.md`
- `export_path`: `<export_root>/2026-05-04-cron-retry-policy/vision-cron-retry-policy.md`

A later architecture artifact for the same idea reuses the dated folder and writes `architecture-cron-retry-policy.md` alongside the vision file.

## Export order

For every exporting skill:

1. Determine whether this invocation must export an artifact.
2. Resolve `entry_slug`.
3. Resolve `export_date` with `date '+%Y-%m-%d'` when creating a new folder.
4. Resolve `export_dir`, `artifact_kind`, `export_file`, and `export_path`.
5. Produce the artifact content according to the skill's own workflow.
6. Write the artifact to `export_path`.
7. Only after writing, return:
   - folder path
   - file path
   - final slug
   - recommended next workflow move

## Artifact profiles

| Skill | Exports? | `artifact_kind` | Export behavior |
|---|---:|---|---|
| `pa-idea` | Always | `idea` | Captures rough idea with minimal editing |
| `pa-vision` | Mandatory for vision artifacts | `vision` | Defines target state and decision direction |
| `figure-it-out` in planning-only mode | Optional | `impl-plan` | Use this local profile when a durable slice plan is requested; execution trails remain governed by pstack |
| `pa-postmortem` | Mandatory for postmortem artifacts | `postmortem` | Captures lessons, incident review, or session review |
| `pa-premortem` | Mandatory for premortem artifacts | `premortem` | Captures failure scenarios, hidden assumption, revised plan, and pre-launch checklist |
| `pa-scope` | Rare / optional | `scope` | Export only when the user needs a reusable scope map, blast-radius artifact, or validation/risk artifact |
| Separate `poteto-mode` delivery session | No by default | n/a | Implements and verifies through the matching playbook; recommends documentation or postmortem capture when needed |
| `interrogate` | Rare / optional | `code-quality-audit` | Export only when the user asks for a reusable deep code-quality audit artifact |
| `pa-qa` | No by default | n/a | Validates user-facing behavior and files durable issues; loops back to scope or TDD when follow-up work is found |
| `pa-doc-update` | No new lifecycle artifact by default | n/a | Updates the correct existing documentation target |
| `pa-doc-cleaner` | No new lifecycle artifact by default | n/a | Repairs existing documentation structure |
| `pa-glossary` | No lifecycle artifact by default | n/a | Creates or updates canonical project vocabulary at the user-requested path or the project's canonical glossary location |

## Handoff rule

A skill must not hand off to a later lifecycle phase until its mandatory artifact has been written.

Examples:

- `pa-vision` must write the vision artifact before handing off to `architect`.
- A requested architecture artifact must be delivered before handing off to implementation; `architect` owns its design-package format.
- `figure-it-out` may hand off to a separate `poteto-mode` delivery session without export when the user wants to implement directly from `pa-vision` or `architect`.
- `pa-postmortem` must write the retrospective artifact before returning lessons as complete.

## Skill-local export sections

Individual `SKILL.md` files should not duplicate the full export protocol. Keep only the pointer to this file and any skill-specific content workflow notes.

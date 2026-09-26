---
name: "pa-idea"
description: "Use when the user mentions `pa-idea`."
---

# Write Down Idea

## Export

Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its `pa-idea` export profile.

- Mandatory on every run.

## Workflow

1. Use the user's remaining input as the raw idea text.
2. Resolve `entry_slug`, `export_dir`, `export_file`, and `export_path` before editing any text.
3. Start from the raw text.
4. If the idea is very short, output a simple bullet-point list — do not expand or embellish.
5. Otherwise, use (and reload) `$simple-editor` for a light pass that preserves the user's voice while cleaning obvious rough edges.
6. Then use (and reload) `$writer-sk` for clarity and concision without adding analysis, advice, new sections, or changing the original language/voice.
7. Write the final text to the resolved `export_path`.
8. Return the folder path, file path, and final slug.

## Verification

Before returning, confirm:

- [ ] `entry_slug`, `export_dir`, `export_file`, and `export_path` were resolved before editing.
- [ ] The original language, voice, and intent were preserved.
- [ ] No analysis, advice, new requirements, or follow-up questions were added.
- [ ] Short input stayed short.
- [ ] The final idea was written to the resolved `export_path`.

## Rules

- Never challenge the user or ask follow-up questions. This skill captures thoughts quickly — it does not interrogate.
- Keep the original language, including mixed French and English.
- Keep the edit small.
- Preserve contradictions, uncertainty, and rough edges instead of resolving them.
- Short input stays short: a bullet list is a valid final output.
- Do not add sections, advice, or analysis the user did not ask for.
- Do not silently turn a raw idea into requirements, scope, or implementation intent.
- If the user gives a strong title, prefer it.
- Keep export naming mechanical and separate from the writing pass.
- Fail loud if export fails or the original intent cannot be preserved.

---
name: "qmd"
description: "Use only when the user explicitly mentions `qmd` to search, retrieve, diagnose, maintain, or configure local QMD collections."
compatibility: "Requires qmd CLI >= 2.8.3."
allowed-tools: "Bash(qmd:*)"
license: "MIT"
metadata:
  author: "pascalandy"
  version: "4.1.0"
---

# QMD

This skill is a local policy layer over the version-matched skill bundled with
QMD. Upstream instructions define QMD capabilities. The rules below define how
to use them here and take precedence when the two disagree.

Install or update on Mac: `PNPM_HOME="$HOME/Library/pnpm" "$HOME/Library/pnpm/bin/pnpm" add -g --config.minimum-release-age=10080 --config.strict-dep-builds=true --allow-build=node-llama-cpp @tobilu/qmd`

Use this command instead of npm or Bun installation commands in the bundled skill. Package updates do not authorize index changes.

## Load upstream instructions

1. Run `qmd --version` and require QMD 2.8.3 or newer
2. Run `qmd skills get qmd` and use the returned skill as the operational
   reference for the installed CLI
3. Do not pass `--full`; this setup uses the CLI, not MCP

If the bundled skill cannot be loaded, run `qmd --help`, follow the local rules
below, and tell the user that the upstream skill was unavailable. Do not replace
it with a copied command reference.

## Local policy

- Use the QMD CLI only; do not configure or invoke MCP
- Keep command output visible, especially trust prompts, skipped files, model
  failures, and index warnings
- Treat a question or retrieval request as read-only until the user approves an
  index mutation
- `qmd doctor` can write to the index. Use a disposable copy when index changes are not authorized
- Search the most likely collection first and pass `-c <collection>` when the
  source is known
- Reopen strong hits before making claims, following the upstream citation rules
  for QMD URI, docid, and line numbers

## Freshness gate

At the start of a retrieval task, run `qmd status`. Status can reveal pending
embeddings and index problems, but it cannot prove that files on disk have not
changed since the last `qmd update`.

Offer to refresh before searching when at least one signal exists:

- QMD reports pending embeddings, orphaned data, or an unhealthy index
- The user says files were added, edited, synchronized, or pulled
- The request depends on frequently changing documents or recent local changes
- An expected document is missing or the first result set is clearly incomplete

State the observed signal and ask whether to refresh or search the current index.
If no signal exists, continue without interrupting the user. An explicit request
to refresh the index authorizes `qmd update` followed by `qmd embed`, but not
cleanup or configuration changes.

When refresh is approved, run these commands in order and keep their output:

```bash
qmd update
qmd embed
qmd status
```

Stop if `qmd update` fails. Do not include `qmd cleanup` in a refresh. When QMD
reports orphaned data, run `qmd cleanup --dry-run` first and request separate
approval before the real cleanup.

## Retrieval policy

Choose the smallest search that fits the evidence available:

- Exact title, phrase, identifier, tag, or code symbol: start with `qmd search`
- Concept remembered indirectly: use a structured `qmd query` with `intent:`,
  `lex:`, and `vec:` authored from the user's context
- Unknown vocabulary or a quick low-stakes exploration: a plain `qmd query` is
  acceptable
- Weak or noisy first pass: read `references/semantic-recovery.md` relative to
  this skill directory and apply only the needed recovery pattern

Add `hyde:` only when the semantic gap is substantial or an earlier structured
query had poor recall. Do not generate it for every search.

## Configuration

Use `qmd --help` and subcommand help where available for ordinary setup. For
advanced `index.yml` work, run `qmd skills path qmd`, resolve the QMD package
root two directories above that path, and read its installed `README.md`. That
README is the version-matched source for configuration keys, model settings,
update hooks, ignore patterns, contexts, named indexes, and trust behavior.

Before recommending or changing QMD models, read
`references/model-preferences.md` relative to this skill directory. Those local
preferences override upstream defaults unless the user explicitly chooses a
different model.

Do not copy the configuration schema into this skill. Do not run `qmd init`,
change collections or contexts, approve trust, add update hooks, or change models
unless the user requested that mutation. After changing the embedding model, run
`qmd embed` only with approval.

## Completion

A retrieval task is complete when freshness was handled, the strongest evidence
was reopened, and the answer cites the relevant QMD URI, docid, and line numbers.
If exact and semantic passes both fail, report what was searched instead of
inventing an answer.

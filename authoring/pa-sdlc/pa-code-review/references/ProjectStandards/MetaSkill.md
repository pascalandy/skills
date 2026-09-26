---
name: ProjectStandards
description: Review adherence to repository conventions, project instructions, file placement, tooling expectations, and source-of-truth rules.
---

# ProjectStandards

Use this lens for local conventions and repository-specific rules.

## Investigator Evidence Focus

1. Read relevant project instructions when available, especially `AGENTS.md`, skill docs, and nearby patterns.
2. Check source-of-truth paths, naming conventions, frontmatter, permissions, and generated/applied file boundaries.
3. Compare changed files to nearby examples in the same directory or workflow family.
4. Identify missing documentation links, dangling references, stale indexes, or distribution/apply gaps.
5. Check relevant lint/format/test commands from project docs without running them unless parent explicitly allowed it.
6. Flag only standards issues that affect correctness, distribution, maintainability, or future agent use.

## Subject Adaptation

- In chezmoi dotfiles, never edit applied home files when a managed source file exists; verify source-tree paths.
- For skills, check trigger wording, reference paths, bundled file layout, and applied-agent distribution expectations.
- For Markdown wiki/docs, respect wiki-map organization and link style where applicable.
- For scripts, check shell standards, executable naming, and XDG/user preference conventions.

## Parent Synthesis Hints

Project-standard violations can be blocking when they mean the change will not be exported, applied, discovered, or maintained correctly. Use `P1` for broken source-of-truth/distribution; `P2` for drift from important conventions.

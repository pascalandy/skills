---
name: typescript-project-workflow
description: Package manager, scripts, dependencies, migration, workspace, and monorepo workflow guidance.
---

# Project Workflow

## Contents

- Discovery Checklist
- Package Manager
- Scripts
- Dependency Policy
- Formatting and Linting
- Workspaces and Monorepos
- Turborepo
- pnpm Workspaces and Catalogs
- Migration Strategy

## Discovery Checklist

Start with local evidence:

```bash
rg --files -g 'package.json' -g 'pnpm-lock.yaml' -g 'package-lock.json' -g 'yarn.lock' -g 'bun.lockb' -g 'bun.lock' -g 'tsconfig*.json' -g 'vite.config.*' -g 'eslint.config.*' -g 'turbo.json'
```

Inspect:

- root and package `package.json` scripts
- `packageManager` field and lockfile
- workspace files: `pnpm-workspace.yaml`, Yarn/npm workspace config, `turbo.json`, `nx.json`, `lerna.json`
- CI workflows for authoritative check names
- nearby package conventions before repo-wide assumptions

## Package Manager

Use the package manager already chosen by the repository:

- `pnpm-lock.yaml` or `packageManager: "pnpm@..."` -> `pnpm`
- `package-lock.json` -> `npm`
- `yarn.lock` -> `yarn`
- `bun.lock` or `bun.lockb` -> `bun`

When multiple signals conflict, prefer the `packageManager` field if it is maintained, then lockfiles, then existing CI commands. Do not introduce a new package manager.

## Scripts

Use scripts over direct tool invocations when they exist because scripts encode local flags, project references, environment variables, and workspace filters.

Common script names:

- typecheck: `typecheck`, `check-types`, `tsc`, `test:ts`
- tests: `test`, `test:unit`, `test:e2e`, `vitest`, `jest`, `playwright`
- lint/format: `lint`, `lint:fix`, `format`, `format:check`
- build: `build`, package-local `build`

Avoid watch/dev commands for validation unless the user explicitly asks for a running server.

## Dependency Policy

Before adding a dependency:

1. Search whether the project already has an equivalent.
2. Check whether the task can be solved with platform APIs or existing utilities.
3. Prefer dependencies already used in the repo's ecosystem.
4. Add dependencies through the repo's package manager and correct workspace/package scope.
5. Keep runtime dependencies out of libraries and SDKs unless they are part of the public value.

For runtime validation, prefer an existing validator such as Zod, Valibot, ArkType, class-validator, TypeBox, io-ts, Effect Schema, or framework-native validation. Do not install a new validator for a tiny boundary if a local guard is enough.

## Formatting and Linting

Do not reformat unrelated files. For touched files, use the repository's configured formatter or linter. If a repo uses ESLint for formatting, do not add Prettier unless asked. If it uses Prettier, Biome, dprint, oxlint, or a framework command, follow that.

For TypeScript linting:

- flat config is the current ESLint/typescript-eslint default path for new config
- typed linting is more powerful but slower; use it when the repo already has it or when the project can afford type-aware rules
- `parserOptions.projectService: true` is the current typescript-eslint recommendation for typed linting in most setups

## Workspaces and Monorepos

In a workspace, identify the package that owns the change. Run package-local checks first, then broaden to affected/workspace checks.

When adding workspace packages:

- declare package dependencies explicitly; do not rely on hoisting
- keep shared code in a package rather than importing through `../` across package boundaries
- respect existing internal package naming and export conventions
- keep root scripts as orchestration, not hidden build logic, unless the root task is deliberately scoped to root files

## Turborepo

Use Turborepo only when it is already present or explicitly selected.

Key rules:

- tasks in `turbo.json` run package scripts with matching names
- use `dependsOn: ["^build"]` when a task needs dependency packages built first
- set `outputs` for file-producing cacheable tasks such as builds
- configure `inputs` carefully; include `$TURBO_DEFAULT$` when narrowing inputs without losing default hashing behavior
- long-running dev tasks should be `persistent: true` and usually `cache: false`
- root tasks are valid for root-only lint/format/migration work, but keep them explicit with `//#task` naming when needed
- `turbo run ...` is the clearer form for scripts and CI; `turbo ...` is an alias that is convenient locally

If typecheck tasks need dependency-change awareness and parallelism, consider the transit-node pattern only in established Turborepo setups.

## pnpm Workspaces and Catalogs

pnpm workspaces are declared in `pnpm-workspace.yaml`. The root package is always included. pnpm catalogs can centralize dependency versions with `catalog:` and named catalogs.

Use catalogs only if the repo already uses them or the task is explicitly dependency-governance work. Do not migrate versions into catalogs during ordinary feature work.

## Migration Strategy

For tool, module, or strictness migrations:

- make one behavior-preserving slice at a time
- keep runtime module semantics and emitted paths unchanged unless the migration specifically targets them
- run typecheck after each slice before broad formatting
- update package exports and CI checks together when publishing shape changes
- document intentionally deferred strictness or compatibility gaps in code/docs only if the repo has a place for that

Avoid bundling migration work into unrelated bug fixes.

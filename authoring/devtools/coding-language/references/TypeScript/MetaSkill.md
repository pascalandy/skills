---
name: typescript
description: >
  Use when writing, debugging, reviewing, testing, or refactoring TypeScript or JavaScript-with-types code, including Node.js, frontend, backend, library, SDK, CLI, and monorepo work.
---

# TypeScript

TypeScript and JavaScript-with-types conventions for practical implementation work.

## Scope

**In scope:**
- TypeScript configuration, strictness, narrowing, generics, utility types, and type-level design
- JavaScript/TypeScript project workflow: package manager, scripts, dependencies, workspaces, monorepos
- Tests, linting, formatting, typechecking, and validation strategy
- React, Vue, Vite, NestJS, Node.js APIs, OpenAPI-generated types, Effect-style code when already present
- TypeScript library, SDK, package export, bundling, and CLI implementation decisions

**Out of scope:**
- General CLI design standards beyond TypeScript implementation details
- Bash, Python, or Starlette conventions
- Broad frontend visual design or UX review

## Routing

Load `references/ROUTER.md` to choose the smallest relevant reference set. Do not load every reference by default.

## Default Workflow

1. Inspect the project before assuming tooling:
   - package manager: `packageManager` field, lockfiles, workspace files
   - scripts: `package.json`, workspace package scripts, CI files
   - TypeScript: `tsconfig*.json`, build/test/lint configs, existing imports and module style
   - framework conventions: nearby files before external patterns
2. Preserve the existing stack unless the task explicitly includes migration or setup.
3. Prefer strict, boring TypeScript:
   - model unknown external data as `unknown` until parsed or narrowed
   - avoid `any`, non-null assertions, broad casts, and `as unknown as T` unless isolated and justified
   - use discriminated unions, type guards, `satisfies`, `as const`, and exhaustive checks when they reduce runtime ambiguity
   - keep advanced types readable; type gymnastics are only justified for public APIs, reusable libraries, or real duplication in type logic
4. Keep runtime and compile-time boundaries separate:
   - TypeScript types do not validate network, file, process, form, or environment input
   - decode or validate runtime data at boundaries with the project's existing validator or a small local guard
5. Validate in widening loops:
   - start with the narrowest useful check for changed files or package
   - run the relevant typecheck and behavior tests
   - broaden to lint/build/workspace checks when shared contracts, package exports, or framework integration are touched

## Validation Defaults

Use project scripts first. If none exist, prefer the local package manager and direct tools already installed in the repo.

- Typecheck: `tsc --noEmit` or the repo's `typecheck` script
- Tests: the repo's Vitest, Jest, Playwright, or framework-specific scripts
- Lint: ESLint/typescript-eslint or the repo's existing linter
- Build/package validation: only when build output, package exports, bundling, or framework integration changed

Do not add a dependency, change a tsconfig baseline, convert module systems, or replace test/lint tools merely because a reference recommends it. Make those changes only when they are required by the task or consistent with an existing project direction.

## References

- `references/TYPESCRIPT_CORE.md` -- strictness, narrowing, runtime boundaries, advanced types, Node module behavior
- `references/PROJECT_WORKFLOW.md` -- package managers, scripts, dependencies, migrations, workspaces, Turborepo
- `references/TESTING_AND_QUALITY.md` -- typecheck/test/lint loops, Vitest/Jest/Playwright notes, typed linting, review checklist
- `references/FRAMEWORK_PATTERNS.md` -- React, Vue, Vite, NestJS, Node.js backend, OpenAPI, Effect
- `references/LIBRARY_SDK_CLI.md` -- libraries, SDKs, package exports, tsdown, CLIs
- `references/SOURCE_AUDIT_2026_06_01.md` -- source-skill extraction and current-doc validation notes

## Provenance

Built from 25 audited TypeScript-related candidate skills and official documentation checked on 2026-06-01 as recorded in `references/SOURCE_AUDIT_2026_06_01.md`.

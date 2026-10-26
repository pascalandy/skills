---
name: typescript-router
description: Dispatch table for the typescript skill.
---

# typescript router

| Request Pattern | Load |
|---|---|
| TypeScript errors, `tsconfig`, strict mode, `any`, `unknown`, narrowing, type guards, generics, utility types, discriminated unions, runtime data typing | `TYPESCRIPT_CORE.md` |
| package manager, scripts, dependencies, lockfiles, workspace setup, migrations, monorepo layout, pnpm catalogs, Turborepo | `PROJECT_WORKFLOW.md` |
| tests, Vitest, Jest, Playwright, Testing Library, TDD, type tests, linting, formatting, CI checks, code review | `TESTING_AND_QUALITY.md` |
| React, TSX, hooks, Vue, `.vue`, Vite, `vite.config`, NestJS, Node backend APIs, OpenAPI, Effect | `FRAMEWORK_PATTERNS.md` |
| libraries, SDKs, npm packages, package exports, ESM/CJS, declaration files, bundling, tsdown, Commander, TypeScript CLI | `LIBRARY_SDK_CLI.md` |
| source provenance, kept/adapted/ignored imported claims, 2026-06-01 validation details | `SOURCE_AUDIT_2026_06_01.md` |

## Loading Rule

Load only the route needed for the current task. If a task spans categories, load the primary route first, then add the second route only when local evidence shows it is needed.

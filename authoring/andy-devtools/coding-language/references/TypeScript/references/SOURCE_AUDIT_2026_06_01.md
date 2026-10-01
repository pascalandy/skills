---
name: typescript-source-audit-2026-06-01
description: Source extraction and current-doc validation notes for typescript.
---

# Source Audit 2026-06-01

Audit target: 25 local TypeScript-related candidate `SKILL.md` files.

Validation date: 2026-06-01. Current official docs override imported skill claims.

## Contents

- Official Sources Checked
- Kept
- Adapted
- Ignored
- Candidate Classification
- Current-Docs Conclusions

## Official Sources Checked

- TypeScript TSConfig docs: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `moduleResolution`, `verbatimModuleSyntax`, `erasableSyntaxOnly`, `skipLibCheck`
- TypeScript Handbook: narrowing, generics, conditional types, mapped types
- Node.js docs: Modules: TypeScript, Modules: Packages
- React docs: React 19 blog, `forwardRef`, `useOptimistic`, React 19 upgrade guide
- Vite docs: v8.0.16 guide, dependency pre-bundling, env variables, library mode
- Vitest docs: v4.1.7 testing types, mocking, `expectTypeOf`
- Playwright docs: TypeScript test support and separate compiler check recommendation
- typescript-eslint docs: getting started, typed linting, project service
- pnpm docs: v11.x workspaces, catalogs, install/frozen lockfile
- Turborepo docs: configuring tasks, `turbo run`, caching, environment variables
- NestJS docs: validation pipe and DTO caveats
- Vue docs: TypeScript with Composition API, `<script setup>`
- openapi-typescript/openapi-fetch docs: 7.x schema type generation and typed clients
- tsdown docs: dts, package exports, package validation, how it works

Official URLs used during validation:

- `https://www.typescriptlang.org/tsconfig/strict.html`
- `https://www.typescriptlang.org/tsconfig/noUncheckedIndexedAccess.html`
- `https://www.typescriptlang.org/tsconfig/exactOptionalPropertyTypes.html`
- `https://www.typescriptlang.org/tsconfig/moduleResolution.html`
- `https://www.typescriptlang.org/tsconfig/verbatimModuleSyntax.html`
- `https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html`
- `https://www.typescriptlang.org/tsconfig/skipLibCheck.html`
- `https://www.typescriptlang.org/docs/handbook/2/narrowing.html`
- `https://www.typescriptlang.org/docs/handbook/2/generics.html`
- `https://www.typescriptlang.org/docs/handbook/2/conditional-types.html`
- `https://www.typescriptlang.org/docs/handbook/2/mapped-types.html`
- `https://nodejs.org/api/typescript.html`
- `https://nodejs.org/api/packages.html`
- `https://react.dev/blog/2024/12/05/react-19`
- `https://react.dev/reference/react/forwardRef`
- `https://react.dev/reference/react/useOptimistic`
- `https://vite.dev/guide/`
- `https://vite.dev/guide/env-and-mode`
- `https://vite.dev/guide/dep-pre-bundling`
- `https://vitest.dev/guide/testing-types`
- `https://vitest.dev/api/expect-typeof`
- `https://playwright.dev/docs/test-typescript`
- `https://typescript-eslint.io/getting-started/typed-linting/`
- `https://typescript-eslint.io/packages/parser/#projectservice`
- `https://pnpm.io/workspaces`
- `https://pnpm.io/catalogs`
- `https://pnpm.io/cli/install`
- `https://turbo.build/repo/docs/crafting-your-repository/configuring-tasks`
- `https://turbo.build/repo/docs/reference/run`
- `https://turbo.build/repo/docs/crafting-your-repository/caching`
- `https://turbo.build/repo/docs/crafting-your-repository/using-environment-variables`
- `https://docs.nestjs.com/techniques/validation`
- `https://vuejs.org/guide/typescript/composition-api`
- `https://openapi-ts.dev/introduction`
- `https://openapi-ts.dev/openapi-fetch/`
- `https://tsdown.dev/options/dts`
- `https://tsdown.dev/options/package-exports`
- `https://tsdown.dev/options/package-exports-validation`

## Kept

- Inspect project tooling before changing code.
- Follow existing package manager, scripts, framework conventions, and CI checks.
- Prefer `strict: true` and narrowly add stricter options such as `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes`.
- Use `unknown` at runtime boundaries; narrow or validate before use.
- Avoid `any`, non-null assertions, and broad casts unless isolated and justified.
- Use discriminated unions, type guards, `satisfies`, `as const`, and exhaustive checks when they simplify correctness.
- Keep tests behavior-focused and mock external boundaries.
- Run typecheck separately when the test runner does not typecheck.
- Keep React/Vue/Nest/Vite guidance framework-specific and secondary to local conventions.
- Treat library package exports, declarations, and ESM/CJS behavior as public contracts that need validation.

## Adapted

- `moduleResolution: "bundler"` is not a universal default. It fits bundler-owned resolution; Node-executed code should use Node-aware module settings.
- `skipLibCheck: true` can be pragmatic but trades away declaration-file checking accuracy.
- Explicit return types are most useful for exported/public APIs and complex callbacks, not every local function.
- React 19 docs mark `forwardRef` as deprecated and recommend passing `ref` as a prop for new React 19-only components, but existing React 18-compatible libraries may still need `forwardRef`.
- Vite source claims mentioning Vite 8/Rolldown are current in official v8 docs, but the skill should avoid hard-coding future assumptions.
- Turborepo "never root tasks" was narrowed: official docs support root tasks for root-scoped work; package tasks remain the default for package behavior.
- pnpm catalogs are useful for workspace version governance, not a default for ordinary dependency edits.
- OpenAPI conversion should prefer current openapi-typescript 7.x and OpenAPI 3.0/3.1 rather than a bespoke generator limited to 3.0.
- Effect-specific guidance is reference-only unless the repo already uses Effect.

## Ignored

- Voice-notification and user-home logging rituals from imported CLI skills.
- "Always use Bun, never npm/npx" and other personal-environment mandates.
- Blanket coverage thresholds such as "coverage >80%" when the repo has no such gate.
- "Always separate types into `types.ts`" as a universal rule.
- OpenAPI examples that generate unsafe guards via repeated `(value as any)` access.
- Any recommendation to clone external reference repos by default.
- Tool migration matrices that pick Biome, Turborepo, Nx, tsdown, or Vitest without local evidence.

## Candidate Classification

Source paths are relative to the local audit collection. Upstream repository names that embed an AI-provider or AI-tool name are redacted as `<repo>` to keep this skill vendor-agnostic; the unredacted paths remain in the local audit source.

| Source | Group | Classification | Extracted notes |
|---|---|---|---|
| `a5c-ai/babysitter/typescript/SKILL.md` | Core TypeScript | Adapt | Good strict-option seed; `moduleResolution: "bundler"` made contextual. |
| `flora131/atomic/typescript-expert/SKILL.md` | Core TypeScript / workflow | Adapt | Strong discovery/typecheck loop, strict options, performance cautions; tool matrix and ESM-first claims narrowed. |
| `flora131/atomic/typescript-advanced-types/SKILL.md` | Core TypeScript | Keep | Advanced type concepts, type tests, pitfalls, performance warnings. |
| `wshobson/agents/typescript-advanced-types/SKILL.md` | Core TypeScript | Keep | Same durable advanced-type guidance; duplicate source collapsed. |
| `ratacat/<repo>/kieran-typescript-reviewer/SKILL.md` | Review quality | Adapt | Useful review lens for type safety and regressions; personal taste softened. |
| `ratacat/<repo>/project-setup/SKILL.md` | Project workflow | Adapt | Strong typing/linting/testing baseline; coverage and tool choices made repo-dependent. |
| `a5c-ai/babysitter/quality-hooks/SKILL.md` | Quality workflow | Adapt | Typecheck/lint/format convergence kept; hook-specific scoring ignored. |
| `wshobson/agents/javascript-testing-patterns/SKILL.md` | Testing | Adapt | Behavior tests, fixtures, mocks, Testing Library guidance kept; generic examples compressed. |
| `affaan-m/<repo>/coding-standards/SKILL.md` | Cross-project standards | Adapt | Readability, KISS/DRY/YAGNI, validation, test naming kept; broad framework sections routed elsewhere. |
| `affaan-m/<repo>/error-handling/SKILL.md` | Error handling | Keep | Typed errors, no silent swallowing, user-vs-developer messages, retry caution. |
| `affaan-m/<repo>/react-patterns/SKILL.md` | Frontend | Adapt | Pure render, hooks, state location, RSC, accessibility kept; Next/Remix details kept as docs-first. |
| `softaworks/agent-toolkit/react-dev/SKILL.md` | Frontend | Adapt | React TypeScript event/ref/children patterns; React 19 claims validated and softened for compatibility. |
| `antfu/skills/vue-best-practices/SKILL.md` | Frontend | Adapt | Vue 3 Composition API, typed props/emits, composables, performance self-check kept; must-read reference mandates removed. |
| `affaan-m/<repo>/vite-patterns/SKILL.md` | Frontend tooling | Adapt | Vite env/security/build/library/prebundle guidance validated against Vite 8 docs. |
| `affaan-m/<repo>/nestjs-patterns/SKILL.md` | Backend/API | Adapt | DTO validation, global pipes, thin controllers, config validation kept; exact project layout treated as example. |
| `wshobson/agents/nodejs-backend-patterns/SKILL.md` | Backend/API | Adapt | Input validation, logging, CORS, graceful shutdown kept at high level; HTTPS/rate limits contextualized. |
| `softaworks/agent-toolkit/openapi-to-typescript/SKILL.md` | Backend/API | Adapt | Schema-to-TS intent kept; current openapi-typescript/openapi-fetch preferred over bespoke unsafe generation. |
| `a5c-ai/babysitter/typescript-sdk-specialist/SKILL.md` | Libraries/SDKs | Adapt | SDK architecture, package exports, errors, retries, abort support, minimal deps kept; unsafe casts and dual-module boilerplate narrowed. |
| `antfu/skills/tsdown/SKILL.md` | Libraries/SDKs | Reference only | Good tsdown option map; only load when tsdown is present or chosen. |
| `a5c-ai/babysitter/commander-js-scaffolder/SKILL.md` | CLIs | Reference only | Commander structure useful when complex CLI is requested. |
| `danielmiessler/Personal_AI_Infrastructure/CreateCLI/SKILL.md` | CLIs | Ignore / reference | CLI quality ideas kept; Bun-only, notifications, home-output rules ignored. |
| `antfu/skills/turborepo/SKILL.md` | Monorepo | Adapt | Many useful Turborepo anti-patterns; "no root tasks" corrected against official docs. |
| `antfu/skills/antfu/SKILL.md` | Opinionated conventions | Reference only | Useful if user asks for Anthony Fu style; not a default. |
| `anomalyco/<repo>/effect/SKILL.md` | Specialized | Reference only | Use only in Effect repos; verify current local APIs first. |
| `mattpocock/skills/migrate-to-shoehorn/SKILL.md` | Specialized testing | Reference only | Test-data cast migration is niche; not a default. |

## Current-Docs Conclusions

- TypeScript strict mode is still the broad default for stronger correctness, with stricter flags selected per project tolerance.
- Node built-in TypeScript support is stable type stripping in current docs; it is lightweight and ignores `tsconfig.json`, so it should not be described as full TS execution.
- Vite v8 uses Rolldown for production builds in current docs; dependency pre-bundling is a dev-mode behavior.
- Vitest current docs are v4.1.7; type tests use `expectTypeOf`/`assertType` with `--typecheck`.
- typescript-eslint's project service is the current recommended route for typed linting in most projects, with known performance cost.
- pnpm current docs are v11.x and support workspaces plus catalogs; catalogs should remain opt-in unless already used.
- openapi-typescript current docs are 7.x and support OpenAPI 3.0/3.1; generated static types do not remove the need to handle runtime drift.

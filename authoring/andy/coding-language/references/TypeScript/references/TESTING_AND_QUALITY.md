---
name: typescript-testing-quality
description: TypeScript testing, linting, typechecking, CI validation, and review guidance.
---

# Testing and Quality

## Contents

- Validation Ladder
- Test Shape
- Type Tests
- Vitest
- Jest
- Playwright
- React and UI Testing
- Linting
- Review Checklist

## Validation Ladder

Run the narrowest useful validation first, then broaden based on blast radius:

1. Static check for the changed file/package: `tsc --noEmit`, package `typecheck`, or framework typecheck.
2. Unit tests for the changed behavior.
3. Integration/component/e2e tests only when the changed surface reaches those layers.
4. Lint/format checks for touched code.
5. Build/package validation when exports, bundling, framework config, or runtime startup changed.
6. Workspace/CI-equivalent checks when shared contracts or monorepo task config changed.

Prefer project scripts. If missing, use installed local tools through the repo's package manager.

## Test Shape

Write behavior-focused tests:

- Arrange, Act, Assert is a good default structure.
- Test observable behavior, edge cases, and error handling.
- Mock external boundaries such as network, filesystem, clocks, database, queues, and third-party APIs.
- Avoid testing private implementation details or incidental call order unless that order is the contract.
- Prefer semantic DOM queries in UI tests; use `data-testid` only where user-facing semantics cannot identify the element.
- Keep fixtures/factories typed without casting away important required fields.

Avoid blanket "80% coverage" mandates. Follow the repo's coverage gate if one exists; otherwise add coverage proportional to risk.

## Type Tests

Use type tests for public type utilities, SDK surfaces, generated client types, overloads, and library APIs where compile-time behavior is part of the contract.

Options:

- Vitest: `expectTypeOf`, `assertType`, and `vitest --typecheck`
- `tsd` or package-specific type test tooling when already present
- `tsc --noEmit` for broader type contract validation

When using `@ts-expect-error`, make sure the expected error is meaningful and not caused by a typo or missing import.

## Vitest

Vitest is a strong default for Vite-native or modern TS projects when already present.

Notes from current docs:

- type tests are static; `*.test-d.ts` files are analyzed by the compiler
- current Vitest typecheck can be enabled with `vitest --typecheck`
- Vitest calls `tsc --noEmit` or `vue-tsc --noEmit` depending on config
- clear or restore mocks between tests
- typed `vi.mock(import('./module.js'), ...)` can preserve module type information better than string-only paths in supported contexts

Do not switch Jest projects to Vitest unless migration is in scope.

## Jest

In Jest projects:

- follow existing transformer setup (`ts-jest`, Babel, SWC, tsx, framework adapter)
- keep test environment explicit (`node`, `jsdom`, framework environment)
- restore mocks between tests
- prefer typed mocks over `(value as any)` chains

If typechecking is not part of Jest execution, run `tsc --noEmit` or the repo's typecheck script separately.

## Playwright

Playwright supports TypeScript test files directly, but it does not typecheck them as part of running tests. Pair Playwright runs with the repo's TypeScript compiler check, especially in CI.

Use Playwright for user flows, navigation, browser APIs, accessibility-critical interactions, and regressions that unit/component tests cannot prove.

## React and UI Testing

Prefer Testing Library-style tests that query by role, label, text, placeholder, or other accessible semantics. Test custom hooks through the project's established helper. Avoid `react-test-renderer` for new React 19 work unless the project requires it.

## Linting

Use the repository's lint setup. For TypeScript ESLint:

- recommended configs are a good baseline for new setups
- strict/stylistic configs are more opinionated; add only when compatible with repo tolerance
- typed linting gives deeper checks and catches unsafe `any` flows, but it pays the cost of TypeScript program analysis
- `parserOptions.projectService: true` is the current recommended typed-linting path for most projects

Do not treat lint as a substitute for `tsc`; use both when correctness depends on typechecking.

## Review Checklist

When reviewing TypeScript changes, check:

- new `any`, non-null assertions, broad casts, or `as unknown as T`
- runtime input modeled only with compile-time types
- optional/undefined/null paths under strict mode
- public API return types and exported types
- error handling in `catch` blocks and async fire-and-forget code
- hidden module-system drift, path alias assumptions, or extension mismatch
- tests proving changed behavior and failure modes
- package exports/build output when library surfaces changed
- unnecessary dependencies or framework pattern drift

Prioritize bugs and regressions over style preferences.

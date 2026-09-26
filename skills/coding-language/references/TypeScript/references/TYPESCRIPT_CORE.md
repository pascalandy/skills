---
name: typescript-typescript-core
description: Core TypeScript typing, tsconfig, module, and runtime-boundary guidance.
---

# TypeScript Core

## Contents

- Project First
- Strictness Defaults
- Module Resolution
- Type Design
- Runtime Boundaries
- Narrowing and Errors
- Advanced Types
- JavaScript Migration

## Project First

Before editing TypeScript behavior, inspect:

- `tsconfig.json`, `tsconfig.*.json`, package-local configs, project references
- `package.json` `"type"`, `"exports"`, `"main"`, `"module"`, `"types"`, and script names
- import style in nearby files: ESM, CJS, extension policy, path aliases
- whether code runs through a bundler, `tsx`/loader, emitted JavaScript, or Node's built-in type stripping

Do not paste a generic tsconfig over a project-specific one. Add or adjust only the options that solve the task.

## Strictness Defaults

Prefer `strict: true` for new TypeScript projects and preserve it in existing ones. Useful stricter options, when compatible with the repo, include:

- `noUncheckedIndexedAccess`: adds `undefined` to unchecked index access and catches dictionary/array assumptions
- `exactOptionalPropertyTypes`: distinguishes omitted optional properties from explicit `undefined`
- `noImplicitOverride`: keeps subclass overrides aligned with base classes
- `noPropertyAccessFromIndexSignature`: makes uncertain dictionary access explicit
- `noImplicitReturns` and `noFallthroughCasesInSwitch`: catch missing control-flow cases

Treat `skipLibCheck` as a tradeoff, not a universal rule. It can speed builds by skipping declaration-file checks, but TypeScript documents the accuracy cost and recommends fixing duplicate/inconsistent dependency types where possible.

## Module Resolution

Choose module settings based on the runtime path:

- Bundled browser/app/library code: `moduleResolution: "bundler"` is appropriate when Vite, Rollup, Rolldown, esbuild, Webpack, tsdown, or another bundler owns runtime resolution.
- Node-executed or Node-emitted code: prefer `module`/`moduleResolution` values such as `node16` or `nodenext` that model Node's ESM/CJS rules.
- Direct Node TypeScript execution: Node's built-in support is type stripping, not full TypeScript. It ignores `tsconfig.json`, performs no typechecking, does not support `.tsx`, and only supports erasable TypeScript syntax. Prefer `tsx` or a build step when code needs full TS features.

Use `import type` and `export type` for type-only imports/exports when runtime behavior matters, especially with `verbatimModuleSyntax` or Node type stripping.

## Type Design

Use the simplest type that preserves the contract:

- Let inference work for local variables and obvious return values.
- Add explicit return types for exported functions, public APIs, hooks, SDK methods, command handlers, and complex callbacks.
- Use `interface` for object-shaped public contracts when declaration merging or clearer object diagnostics matter.
- Use `type` for unions, mapped/conditional types, primitives aliases, tuples, branded primitives, and type-level transformations.
- Use `satisfies` to check a value against a contract without widening useful literal information.
- Use `as const` for literal tables, routes, event names, and discriminants when immutable literal inference helps.

Avoid:

- `any` where `unknown`, a generic, a validator, or a narrow local type would work
- `as unknown as T` outside migration/test seams with a clear reason
- non-null assertions where a guard, default, or invariant check would make the program safer
- global type augmentation unless it is already the local convention or required by a framework

## Runtime Boundaries

Types describe compile-time expectations. They do not validate runtime values from:

- HTTP requests and responses
- OpenAPI clients when the server may drift
- files, environment variables, process arguments, forms, browser storage, databases, queues
- `JSON.parse`, `fetch`, `postMessage`, plugin APIs, dynamic imports

At those boundaries, use the project's existing parser/validator first. If none exists and the surface is small, write a focused type guard or assertion function. Keep validation close to the ingress point and pass typed data inward.

## Narrowing and Errors

Prefer normal JavaScript control flow that TypeScript understands:

- `typeof`, `instanceof`, `in`, equality checks, discriminant checks, array predicates
- user-defined type predicates for reusable checks
- assertion functions for invariants that should throw
- exhaustive `switch` with a `never` fallthrough for discriminated unions

For errors:

- `catch (error)` should be treated as `unknown`
- narrow with `error instanceof Error`, domain error classes, or structured error guards
- keep user-facing messages separate from logs/internal details
- model expected failures with discriminated results when exceptions make control flow unclear

## Advanced Types

Use generics, conditional types, mapped types, template literal types, and utility types when they remove duplication or preserve a real API contract.

Keep type-level code maintainable:

- name intermediate types when a one-liner becomes hard to read
- constrain generics to the properties actually used
- prefer discriminated unions over parallel booleans or loosely related option bags
- test public type utilities with type tests
- watch for slow compiler symptoms from deep conditional recursion, giant unions, and heavily nested mapped types

If a simpler value-level design avoids complex type programming, prefer the simpler design.

## JavaScript Migration

For JS-to-TS migrations, move incrementally:

1. Inspect existing build and runtime behavior.
2. Enable `allowJs` and `checkJs` only if that matches the migration plan.
3. Add types around boundaries first.
4. Convert files in thin vertical slices.
5. Tighten strict options one at a time with focused fixes.

Do not mix migration cleanup with unrelated feature work unless the feature requires the cleanup.

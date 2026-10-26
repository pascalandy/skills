---
name: typescript-library-sdk-cli
description: TypeScript library, SDK, package export, bundling, and CLI guidance.
---

# Library, SDK, and CLI

## Libraries

For published packages, inspect:

- `package.json`: `"type"`, `"exports"`, `"main"`, `"module"`, `"types"`, `"files"`, `"sideEffects"`
- build config: tsdown, tsup, Rollup, Rolldown, Vite library mode, unbuild, esbuild
- declaration generation and type test setup
- package validation tools such as `publint`, `attw`, `arethetypeswrong`, or CI pack tests

Defaults:

- define a small public surface and export it deliberately
- keep internal files internal; avoid accidental deep imports
- generate declarations for TypeScript consumers
- externalize peer dependencies and large runtime dependencies consumers should own
- document or test ESM/CJS support instead of assuming it
- validate package contents with `npm pack --dry-run` or the repo's package validation script when publishing shape changed

## ESM/CJS and Package Exports

Node package docs support `"exports"` for explicit entry points and conditional exports for `import`/`require` or environment-specific paths.

Guidelines:

- include `"type"` in package.json so `.js` semantics are explicit
- use conditional exports carefully; object key order matters from most specific to least specific
- keep declarations aligned with runtime files for every export path
- avoid dual-package hazards by testing both import and require paths if both are advertised
- prefer named exports for tree-shakeable SDK/library APIs unless existing style uses defaults

## tsdown

Use tsdown when the project already uses it or when the user chooses it for library bundling.

Current tsdown docs:

- infer useful defaults from `package.json` and `tsconfig.json`
- can generate `.d.ts` files with `dts: true`; it auto-enables declaration generation when `types`/`typings` or export type entries are present
- can use `isolatedDeclarations` for faster declaration generation
- can experimentally auto-generate `exports`, `main`, `module`, and `types`; review generated fields before publishing
- can run `publint` and `attw` package validation when optional dependencies are installed

Do not turn on experimental export generation silently in an existing package. Prefer explicit package metadata unless the repo already adopted tsdown's automation.

## SDKs and API Clients

SDK defaults:

- model configuration explicitly: base URL, auth, timeout, retry policy, user agent, fetch implementation when needed
- accept `AbortSignal` for cancellable requests
- parse or narrow error bodies before exposing typed errors
- separate transport errors, HTTP status errors, validation errors, and domain errors
- keep retries opt-in or limited to idempotent/retriable operations with jitter
- avoid hiding server contract drift behind `as T`
- keep dependencies minimal, especially for browser SDKs

For OpenAPI-backed SDKs, prefer generated schema types plus a thin hand-written client layer over hand-maintained endpoint types.

## CLIs

For TypeScript CLIs, also consider the `coding-standard` skill for CLI UX, help text, output, exit codes, and agent-friendly behavior.

Implementation defaults:

- follow the repo's runtime and package manager; do not assume Bun or Node universally
- simple CLIs can use manual parsing or built-in utilities when dependency cost matters
- use Commander or another existing parser when commands, nested options, validation, and help output justify it
- separate command parsing from command execution so behavior is testable
- return clear exit codes: success, user/input error, runtime/external failure
- keep machine-readable output stable when JSON or structured output is part of the contract
- type command option objects instead of passing untyped parser results through the program

Validate with:

- `--help` and representative command invocations
- typecheck
- behavior tests for parsing and execution boundaries
- package/bin wiring when publishing or installing globally

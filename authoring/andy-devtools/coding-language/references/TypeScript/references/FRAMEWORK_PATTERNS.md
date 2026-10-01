---
name: typescript-framework-patterns
description: Framework-specific TypeScript guidance for React, Vue, Vite, NestJS, Node APIs, OpenAPI, and Effect-style code.
---

# Framework Patterns

## Contents

- React
- Vue
- Vite
- NestJS
- Node.js Backends
- OpenAPI
- Effect

## React

Follow local React conventions first: framework, router, server/client split, styling system, state libraries, and test utilities.

Defaults:

- components should be pure functions of props/state
- derive values during render when cheap instead of storing derived state
- put side effects in event handlers, server actions, data libraries, or effects as appropriate
- obey hook rules; keep custom hooks focused and named by behavior
- prefer composition and explicit props over deep prop drilling workarounds
- memoize only when profiling, stable child props, or expensive recomputation justifies it
- use semantic HTML before ARIA roles

React 19 notes:

- new function components can accept `ref` as a prop
- React docs mark `forwardRef` as deprecated; for new React 19-only components, pass `ref` as a prop instead
- keep `forwardRef` in existing code when library compatibility or React 18 support requires it
- prefer current React docs for actions, `useOptimistic`, Server Components, and form behavior

For Server Components and frameworks such as Next.js, Remix, or React Router framework mode, inspect framework docs and local boundaries. Do not import Server Components into Client Component files; compose through props/children or framework-supported boundaries.

## Vue

For Vue 3 SFC work, prefer Composition API with `<script setup lang="ts">` when the project already uses it or new code has no contrary convention.

Defaults:

- type props and emits with `defineProps` and `defineEmits`
- keep source state minimal and derive with `computed`
- use watchers for side effects, not for routine derived state
- keep templates declarative; move branching and complex transforms into script/composables
- split large components into focused components and composables
- use props down/events up for ordinary component data flow
- use `v-model` only for true two-way component contracts
- use provide/inject for deep-tree context, typed with `InjectionKey` when needed

Use `vue-tsc` or the repo's framework typecheck for `.vue` changes.

## Vite

Official Vite v8 docs checked in the audit describe:

- a dev server with native ESM-oriented behavior and fast HMR
- a production build command using Rolldown
- dependency pre-bundling in development for CommonJS/UMD compatibility and fewer browser requests

Vite defaults:

- keep `vite.config.*` small and typed with `defineConfig`
- remember `import.meta.env` values are strings
- only `VITE_`-prefixed env vars are exposed to client code by default, and those values are bundled into source at build time
- never put secrets in `VITE_*`
- restart the dev server after `.env` changes
- verify production behavior with `vite build` and, when relevant, `vite preview`

For library mode, externalize peer/runtime framework dependencies that consumers should provide, and verify package exports.

## NestJS

Follow Nest module/controller/provider conventions already present in the app.

Defaults:

- keep controllers thin; put business rules in providers/services
- validate request DTOs with `ValidationPipe` or existing validation strategy
- use concrete DTO classes for Nest runtime metadata; interfaces and type-only imports may be erased and unavailable to validation/reflection
- for public APIs, prefer `whitelist: true` and `forbidNonWhitelisted: true` when compatible with existing behavior
- validate environment/config at boot
- avoid returning ORM entities directly from public controllers if they include internal fields
- keep guards/interceptors/filters close to their owning module unless truly shared
- use explicit authenticated request types instead of untyped request mutation

## Node.js Backends

For Express, Fastify, Hono, native Node, or other TS backends:

- validate inputs at transport boundaries
- keep route handlers thin and put domain behavior in testable functions/services
- use structured errors or discriminated result types for expected failures
- separate user-facing error messages from logs/internal diagnostics
- handle shutdown, connection cleanup, and background work explicitly
- avoid `*` CORS in production unless it is intentionally public and safe
- use platform APIs such as `AbortController`, `fetch`, and Web Streams when they match the runtime support and local conventions

## OpenAPI

Prefer schema-driven types over hand-maintained request/response interfaces when the project has an OpenAPI source of truth.

Current openapi-typescript 7.x docs:

- support OpenAPI 3.0 and 3.1
- generate runtime-free TypeScript types from YAML or JSON
- recommend TypeScript module resolution modes such as `bundler` or `nodenext` based on project runtime
- recommend `noUncheckedIndexedAccess`

Use generated types for compile-time contracts, but still treat API responses as runtime data that can drift. For clients, prefer endpoint literals or generated/path-aware clients where possible so params, bodies, and responses stay tied to the schema.

## Effect

Only apply Effect-specific guidance when Effect is already part of the repo or the user asks for it.

Defaults:

- inspect local Effect version, helpers, layers, and tests before writing code
- prefer project-local patterns over memory of older Effect APIs
- keep HTTP handlers thin and put business logic in services
- use schema/domain errors when the surrounding code already models data that way
- avoid broad hidden provisioning that obscures dependencies

Do not clone or install Effect reference repositories unless the user asks or the repo explicitly documents that workflow.

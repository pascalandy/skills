---
name: "coding-language"
description: "Use when writing, debugging, linting, or reviewing Bash, Python, TypeScript, JavaScript-with-types, or Starlette/ASGI code."
kind: "dev"
keywords: ["bash", "shell", "shellcheck", "shfmt", "python", "uv", "pep-723", "pyright", "ruff", "pytest", "typescript", "javascript", "tsconfig", "node", "vite", "react", "vue", "nestjs", "starlette", "asgi", "fastapi", "middleware", "websocket", "uvicorn"]
---

# Coding Language

Language and framework-specific conventions: idiomatic syntax, tooling, and patterns for each supported stack.

## Scope

**In scope:**
- Bash scripting conventions, strict mode, shellcheck/shfmt, script templates
- Python development with `uv`, PEP 723 inline metadata, pyright, ruff, pytest
- TypeScript and JavaScript-with-types development: strictness, narrowing, runtime boundaries, package workflow, tests, frameworks, libraries, SDKs, CLIs, and monorepos
- Starlette/ASGI applications (including FastAPI internals): routing, requests/responses, middleware, WebSockets, templates, static files, authentication, sessions, background tasks, lifespan, testing

**Out of scope:**
- CLI design principles, implementation patterns, or agent-friendliness auditing
- General architectural design decisions

## Routing

Load `references/ROUTER.md` to dispatch request to correct sub-skill.

## Sub-skills

| Sub-skill | Purpose |
|-----------|---------|
| `Bash` | Create and refactor Bash scripts: `set -Eeuo pipefail`, `fct_` naming, proper quoting, `readonly` constants, `local` variables. Shellcheck wrapper and script template included. |
| `Python` | Modern Python development with `uv` as exclusive package manager. PEP 723 single-file scripts, type hints with pyright, formatting with ruff, testing with pytest. Covers choosing the environment that owns dependencies, uv projects and tools, verify-before-repair checks, cross-platform rules, script conventions, secrets. |
| `TypeScript` | TypeScript and JavaScript-with-types conventions for strict typing, package workflow, tests, framework patterns, libraries, SDKs, CLIs, and monorepos. |
| `Starlette` | Build, debug, and extend Starlette applications and Starlette-powered internals (including FastAPI). Covers routing, requests/responses, middleware, WebSockets, templates, static files, authentication, sessions, background tasks, configuration, lifespan, testing. |

## Credits

- Starlette reference -- audited against [starlette.io](https://www.starlette.io/) official documentation

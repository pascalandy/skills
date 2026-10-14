---
name: "coding-language"
description: "Use when writing, debugging, linting, or reviewing Bash, Python, TypeScript, JavaScript-with-types, or Starlette/ASGI code."
kind: "dev"
keywords: ["bash", "shell", "shellcheck", "shfmt", "python", "uv", "pep-723", "pyright", "ruff", "pytest", "typescript", "javascript", "tsconfig", "node", "vite", "react", "vue", "nestjs", "starlette", "asgi", "fastapi", "middleware", "websocket", "uvicorn"]
---

# Coding Language

Language and framework-specific conventions: idiomatic syntax, tooling, and patterns for each supported stack.

## Sub-skills

Load the file of the row that matches the request:

| Request | Load |
|---|---|
| Bash or shell scripts: create, refactor, lint, or debug; `set -Eeuo pipefail`, `fct_` naming, quoting, `readonly` and `local`, shellcheck, shfmt, the script template | [references/Bash/MetaSkill.md](references/Bash/MetaSkill.md) |
| Python with `uv` as the only package manager: PEP 723 scripts, projects and tools, the environment that owns dependencies, type hints with pyright, ruff, pytest, verify-before-repair checks, cross-platform rules, secrets | [references/Python/MetaSkill.md](references/Python/MetaSkill.md) |
| TypeScript or JavaScript-with-types: tsconfig, strictness, narrowing, runtime boundaries, package workflow and exports, tests, Node.js, Vite, React, Vue, NestJS, libraries, SDKs, CLIs, monorepos | [references/TypeScript/MetaSkill.md](references/TypeScript/MetaSkill.md) |
| Starlette or ASGI apps, including FastAPI internals: routing, requests and responses, middleware, WebSockets, templates, static files, authentication, sessions, background tasks, configuration, lifespan, uvicorn, testing | [references/Starlette/MetaSkill.md](references/Starlette/MetaSkill.md) |

## Out of scope

- CLI design principles, implementation patterns, or agent-friendliness auditing
- General architectural design decisions

## Credits

- Starlette reference -- audited against [starlette.io](https://www.starlette.io/) official documentation

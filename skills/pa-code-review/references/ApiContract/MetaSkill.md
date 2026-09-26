---
name: ApiContract
description: Review public or shared contracts such as routes, schemas, exported types, CLI interfaces, config formats, and compatibility surfaces.
---

# ApiContract

Use this conditional lens when the diff changes an interface other code, users, agents, or systems consume.

## Investigator Evidence Focus

1. Identify the contract surface: API route, schema, exported type/function, CLI command, config key, file format, template, or workflow entrypoint.
2. Compare old and new behavior for backward compatibility and migration needs.
3. Inspect consumers, docs, examples, tests, and generated artifacts that assume the contract.
4. Look for missing versioning, aliases, deprecation notes, validation, or docs updates.
5. Flag mismatches between implementation, tests, help text, docs, and actual outputs.

## Subject Adaptation

- For CLIs, inspect flags, positional args, help text, exit codes, stdout/stderr, and machine-readable output.
- For TypeScript/Python exports, inspect downstream imports and expected types.
- For skills/workflows, inspect trigger names, reference links, delegated-investigator names, and distribution paths.
- For schemas/configs, inspect defaults and compatibility with existing user files.

## Parent Synthesis Hints

Broken or undocumented contract changes are often `P1` when consumers may fail. Use `P2` for compatibility risks needing clarification or docs before release.

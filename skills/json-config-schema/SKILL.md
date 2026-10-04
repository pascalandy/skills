---
name: "json-config-schema"
description: "Use when creating, reviewing, changing, versioning, or validating the JSON Schema of a JSON config file."
kind: "dev"
---

# JSON config schema

A config is sound when its schema accepts it and none of its facts contradict each other. Steps 1 to 5 apply to a new schema and to a change. For a review, check the schema and the code that reads it against each step, then report each broken rule with its file, its fix, and whether the fix makes an existing config invalid (step 4).

Requires `uv`; confirm with `uv --version`. Step 5 runs `check-jsonschema` through `uvx`, with nothing to install.

## Skeleton

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Project config",
  "description": "One config.json per project folder, validated by `just check`.",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "id", "state"],
  "properties": {
    "$schema": { "const": "../config.schema.json" },
    "schema_version": { "const": 1 },
    "id": { "description": "UUID v4, set once and never changed.", "type": "string", "format": "uuid" },
    "state": { "description": "active: work in progress. closed: delivered and archived.", "enum": ["active", "closed"] }
  }
}
```

## Steps

1. **One place per fact**
   - An enum lives in the schema. Code that needs the list reads it from the schema, or a test asserts that the code's copy equals the enum
   - A value derivable from another field, such as a status implied by a history list, is not stored. When it must stay readable, a check script asserts that the two agree
   - A rule that compares two fields, such as a path that embeds a date equal to another field, goes in a check script: JSON Schema cannot compare fields

   Done when every enum and derived value has one source, or a check that fails when the copies disagree

2. **Strict shape**
   - Draft 2020-12, a `title`, and a `description` on the schema and on each property. An enum's description defines each value
   - `additionalProperties: false` on every object, so a misspelled key fails
   - `$schema` declared under `properties`, or the config's own `$schema` key, which editors read for completion, fails as unexpected
   - With `allOf` or `$ref` composition, `unevaluatedProperties: false` instead: `additionalProperties` ignores properties declared in subschemas and rejects them
   - `default` is an annotation that validators leave unapplied, so the program applies its own defaults

   Done when `uvx check-jsonschema --check-metaschema <schema>` passes and a config with a misspelled key fails

3. **Conventions**
   - Keys in `snake_case`, in the project's language
   - Dates in ISO 8601: `YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM` in local time when the project records no time zone, stated in the property's description
   - IDs as lowercase UUID v4, generated once
   - A state takes its value from an enum
   - A collection with a stable key is an object indexed by that key; any other collection is a list

   Done when each property follows them, or its description says why not

4. **Version**
   - The version lives only in `schema_version`, pinned with `const`. The schema file name carries none, such as `config.schema.json`
   - Bump `schema_version` when a change makes an existing config invalid. Run the new schema against every config to decide: a change they all pass keeps the version
   - On a bump, one migration script rewrites every config in the repository. The schema, the migration, and the rewritten configs land in one commit; git keeps the old schema
   - Configs that live outside the repository, such as on users' machines, are the exception: publish each version under its own file name, leave it unchanged, and migrate on read, one function per version step

   Done when every config passes the new schema

5. **Validate**
   - The project's check recipe, such as `just check`, and its pre-commit hook run `uvx check-jsonschema --schemafile <schema> <configs>`. It checks `format` by default
   - Python's `jsonschema.validate` skips `format` unless called with `format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER`
   - Tests keep one invalid config per rule from steps 1 and 2, each expected to fail

   Done when the check passes on every config and fails on each invalid config

# Image tools

## Select the tool

1. Use the image tool explicitly requested by the user
2. Otherwise, use the default tool below
3. If a user-selected tool is unavailable, explain the limitation and ask before switching tools

## `$imagegen` (default)

Codex `$imagegen` is the default image tool.

- Invoke `$imagegen` before generating or editing an image
- Follow the loaded `$imagegen` skill instructions
- Let `$imagegen` select its underlying model rather than naming or calling one directly
- Generate or edit one image per invocation
- Include every user-provided reference image needed for the requested result

If `$imagegen` is unavailable and the user did not select another tool, report the limitation rather than silently choosing a replacement.

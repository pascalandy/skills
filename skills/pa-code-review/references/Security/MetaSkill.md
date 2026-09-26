---
name: Security
description: Review auth, permissions, user input, secrets, unsafe IO, public surfaces, and injection-prone behavior.
---

# Security

Use this conditional lens when the diff touches security-sensitive surfaces.

## Investigator Evidence Focus

1. Identify trust boundaries touched by the change.
2. Inspect input validation, output encoding, authn/authz checks, secret handling, filesystem/network access, and command execution.
3. Look for privilege escalation, injection, path traversal, data leakage, insecure defaults, and unsafe logging.
4. Check whether tests or checks cover important security behavior.
5. Separate confirmed vulnerabilities from theoretical risks.

## Subject Adaptation

- For web/API code, prioritize auth, permissions, schemas, headers, CORS, CSRF, and public endpoints.
- For CLI/scripts, prioritize shell quoting, path handling, destructive operations, temp files, and secrets in output.
- For dotfiles/config, prioritize secret templates, token exposure, permissions, and managed private files.

## Parent Synthesis Hints

Confirmed exploitable issues are `P0` or `P1`. Weak theoretical risks should usually be `P2` with clear uncertainty.

# Update headless-pi

Use this checklist when refreshing `references/pi/MetaSkill.md`.

## Official Sources

```bash
DOC_URL="https://pi.dev"
NPM_URL="https://www.npmjs.com/package/@earendil-works/pi-coding-agent"
REPO_URL="https://github.com/earendil-works/pi/tree/main/packages/coding-agent"
```

The installed package docs are the local truth for the currently installed Pi version:

```bash
PI_CLI_JS="$(sed -n 's/^# cmd-shim-target=//p' "$(command -v pi)")"
PI_PKG_DIR="$(dirname "$(dirname "$PI_CLI_JS")")"
README="$PI_PKG_DIR/README.md"
JSON_DOC="$PI_PKG_DIR/docs/json.md"
RPC_DOC="$PI_PKG_DIR/docs/rpc.md"
```

If the shim lookup fails, locate `@earendil-works/pi-coding-agent` via the active package manager and read its `README.md` plus `docs/` directory.

## Checklist

1. Check public docs/package metadata for updated capabilities:
   - `npx nia-docs "$DOC_URL" -c "summarize CLI modes, model flags, and links to CLI reference"` when web access is available.
   - `npm view @earendil-works/pi-coding-agent version repository dist-tags`.
2. Read the installed Pi `README.md` enough to verify CLI mode/model flags.
3. Check installed `docs/json.md` and `docs/rpc.md` if JSON/RPC mode changed.
4. Compare against live CLI help:
   - `pi --help`
   - `pi --list-models opencode-go/kimi-k2.6`
5. Verify current behavior with cheap commands:
   - `pi --list-models opencode-go/kimi-k2.6`
   - `pi -p --model opencode-go/kimi-k2.6 "ping"`
6. If documenting scripted parsing, confirm whether `pi -p` still emits terminal control sequences in this harness.
7. Update examples, gotchas, and delegation matrix references together.

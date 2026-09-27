---
name: "headless"
description: "Explicitly triggered when the user mentions `headless`, `headless-claude`, `headless-codex`, `headless-opencode`, or `headless-pi`. It provides headless delegation and CLI flag guidance."
keywords:
  - "headless-delegation"
  - "headless-claude"
  - "headless-codex"
  - "headless-opencode"
  - "headless-pi"
  - "claude -p"
  - "claude --print"
  - "claude --permission-mode"
  - "codex exec"
  - "codex --full-auto"
  - "codex --yolo"
  - "opencode run"
  - "opencode --agent"
  - "pi -p"
  - "pi --print"
  - "pi --model"
  - "pi --mode json"
  - "pty"
  - "non-interactive"
---

# Headless

> Dispatch real execution work to a headless CLI agent -- Claude, Codex, OpenCode, or Pi -- and look up the flag surface of each CLI. Delegation is the core; the CLI references are flag-lookup tables that the delegation skill cites.

---

## Routing

Load `references/ROUTER.md` to determine which sub-skill handles this request.

## Canonical terminology

Load `references/GLOSSARY.md` (skill-relative `/references/GLOSSARY.md`) when
terms such as **Headless delegation**, **Target CLI**, **Execution mode**,
**PTY posture**, **Permission posture**, or **CLI flag reference** need stable
meaning.

---

## The Problem

Running headless CLI agent from inside another CLI looks simple from outside, but details punish guesswork:

- **Execution mode is not interchangeable.** Claude Code `--print` without pty. Pi `-p`/`--print` without pty. Codex `exec` with pty, inside git repo. OpenCode `run` with pty. Mixing these makes delegated agent exit silently, hang on permission dialog, print terminal control codes, or refuse to start
- **Permission posture decides whether run completes.** Print-mode Claude hangs on first approval prompt unless paired with `--permission-mode <mode>`. Codex `exec` hangs unless paired with `-s read-only` or `-s workspace-write`. OpenCode needs right agent and server mode
- **Flag surfaces drift.** Each CLI has dozens of flags -- models, session resume, output format, MCP config, worktrees, budget limits -- and they change between versions

AI assistant handling this by feel produces broken bash, wrong permission modes, and quiet failures that look like model refusals.

---

## The Solution

This meta-skill collapses five related concerns into one entry point:

1. **Delegation** (core) -- PTY matrix, permission posture, workdir refusal list, background or foreground recipes, and trigger discipline. Fires only on strict phrase `use headless-delegation with <cli> to ...`. Cites sibling CLI sub-skills for flag detail instead of duplicating them.

2. **Claude** (flag reference) -- Complete flag surface of `claude -p` or `claude --print`: permission modes, output formats, session management, MCP servers, worktrees, system prompts, beta headers, effort levels, Remote Control, subcommands.

3. **Codex** (flag reference) -- Complete flag surface of `codex exec`: model selection, reasoning effort, session resume, sandbox levels, image attachments, JSON output, piping input.

4. **OpenCode** (flag reference) -- Complete flag surface of `opencode run`: numbered core agents, specialized agents, session continuation, file attachments, server mode, output format.

5. **Pi** (flag reference) -- Headless `pi -p` / `pi --print` and `pi --mode json`: model selection, model discovery, piped input, parsing-safe output cleanup, and smoke-test patterns.

Router dispatches to the right sub-skill based on trigger phrase. User never picks sub-skill -- they describe what they need, and the right specialist activates.

---

## What's Included

| Component | Path | Purpose |
|-----------|------|---------|
| Skill router | `references/ROUTER.md` | Dispatch table that routes to right sub-skill |
| Glossary | `references/GLOSSARY.md` | Canonical terminology for delegation, execution modes, safety posture, output handling, and CLI references |
| Delegation sub-skill | `references/delegation/MetaSkill.md` | PTY matrix, permission posture, workdir hygiene, foreground or background recipes |
| Delegation update checklist | `references/delegation/references/UPDATE.md` | How to keep orchestrator in sync with sibling flag references and observed CLI behavior |
| Claude flag reference | `references/claude/MetaSkill.md` | Complete `claude -p` flag surface from official CLI reference |
| Claude update checklist | `references/claude/references/UPDATE.md` | How to refresh against official Claude Code CLI docs |
| Codex flag reference | `references/codex/MetaSkill.md` | Complete `codex exec` flag surface from official CLI reference |
| Codex update checklist | `references/codex/references/UPDATE.md` | How to refresh against official Codex CLI docs |
| OpenCode flag reference | `references/opencode/MetaSkill.md` | Complete `opencode run` flag surface with project-specific agents |
| OpenCode update checklist | `references/opencode/references/UPDATE.md` | How to refresh against official OpenCode CLI docs |
| Pi flag reference | `references/pi/MetaSkill.md` | Headless `pi -p`, model selection, JSON mode, and output cleanup guidance |
| Pi update checklist | `references/pi/references/UPDATE.md` | How to refresh against installed Pi docs and observed CLI behavior |

---

## Official Update Sources

When flags or agent capabilities drift, refresh from these canonical sources before editing references:

| CLI | Official source | Local verification |
|---|---|---|
| Claude | `https://code.claude.com/docs/en/cli-reference` | `claude --help` |
| Codex | `https://developers.openai.com/codex/cli/reference` | `codex --help`, `codex exec --help` |
| OpenCode | `https://opencode.ai/docs/cli/` | `opencode --help`, `opencode run --help` |
| Pi | `https://pi.dev`, `https://www.npmjs.com/package/@earendil-works/pi-coding-agent`, `https://github.com/earendil-works/pi/tree/main/packages/coding-agent` | installed package `README.md`, `docs/json.md`, `docs/rpc.md`, `pi --help`, `pi --list-models` |

Each sub-skill's `references/<cli>/references/UPDATE.md` contains the detailed refresh procedure.

---

## Invocation Scenarios

| Trigger | What Happens |
|---------|--------------|
| `use headless-delegation with claude to summarize logs.txt` | Routes to `delegation/MetaSkill.md` -- emits `claude --print --permission-mode plan "Summarize the errors in logs.txt"` |
| `use headless-delegation with codex to add a dark mode toggle` | Routes to `delegation/MetaSkill.md` -- emits `bash pty:true workdir:<cwd> command:"codex exec --full-auto '...'"` |
| `use headless-delegation with opencode to refactor auth.ts` | Routes to `delegation/MetaSkill.md` -- emits `bash pty:true workdir:<cwd> command:"opencode run '...'"` |
| `use headless-delegation with pi to review auth.ts` | Routes to `delegation/MetaSkill.md` -- emits `pi -p --model <model> '...'` without PTY |
| `headless-claude` | Routes to `claude/MetaSkill.md` -- shows flag reference for `claude -p` |
| `headless-codex` | Routes to `codex/MetaSkill.md` -- shows flag reference for `codex exec` |
| `headless-opencode` | Routes to `opencode/MetaSkill.md` -- shows flag reference for `opencode run` |
| `headless-pi` | Routes to `pi/MetaSkill.md` -- shows flag reference for `pi -p` and `pi --mode json` |
| `claude --permission-mode acceptEdits "..."` | Routes to `claude/MetaSkill.md` -- looks up permission-mode table |
| `codex exec --full-auto "..."` | Routes to `codex/MetaSkill.md` -- looks up sandbox or approval matrix |
| `opencode run --agent 2-opus "..."` | Routes to `opencode/MetaSkill.md` -- looks up agent catalogue |

---

## Example Usage

### Delegating execution (core path)

```
User: use headless-delegation with codex to write a REST API for todos

AI responds:
Routing to delegation sub-skill...

bash pty:true workdir:<cwd> command:"codex exec --full-auto 'Write a REST API for todos'"

Running inside an existing git repo. For scratch work, prefix with:
  SCRATCH=$(mktemp -d) && cd "$SCRATCH" && git init
```

### Looking up Claude flags

```
User: headless-claude

AI responds:
Routing to claude sub-skill...

[Shows the complete `claude -p` flag reference: permission modes,
output formats, session management, MCP servers, worktrees,
system prompts, effort levels, Remote Control, subcommands.]
```

### Cross-reference from delegation to flag table

```
User: use headless-delegation with claude to review src/auth.ts

AI responds:
Routing to delegation sub-skill...

  claude --print --permission-mode plan "Review src/auth.ts"

Permission-mode choices: default, plan, acceptEdits, dontAsk, auto,
bypassPermissions. See references/claude/MetaSkill.md for the full
flag surface.
```

---

## Configuration

No configuration required. Sub-skills are pure references plus one orchestrator. They read no persistent state and require no API keys beyond whatever underlying CLI already needs.

---

## Customization

| Customization | Location | Impact |
|--------------|----------|--------|
| Add new target CLI | new `references/<cli>/MetaSkill.md` and new row in `references/ROUTER.md` and one row in `delegation/MetaSkill.md` execution matrix | Extends delegation to fourth CLI without touching existing sub-skills |
| Tighten or loosen delegation trigger | `references/delegation/MetaSkill.md` "Trigger" section | Change strict phrase or accepted `<cli>` set |
| Adjust default permission posture | `references/delegation/MetaSkill.md` "Default permission posture" table | Shift defaults conservative or permissive per CLI |
| Refresh flag references | `references/<cli>/references/UPDATE.md` | Follow `npx nia-docs` workflow to diff against official CLI docs |

---

## Related

- `$pi-subagents` -- Same-CLI sub-agent routing (not headless delegation)
- `pa-advisor` -- Executor→advisor pattern (advice, not execution). Uses `claude -p` internally; see `references/claude/MetaSkill.md` for flag detail

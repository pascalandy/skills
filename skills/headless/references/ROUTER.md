---
name: headless
description: |
  Headless CLI delegation and flag references. USE WHEN use headless-delegation with claude to, use headless-delegation with codex to, use headless-delegation with opencode to, use headless-delegation with pi to, headless-delegation, headless-claude, headless-codex, headless-opencode, headless-pi, claude -p, claude --print, claude --permission-mode, claude --dangerously-skip-permissions, claude --allowedTools, claude --model, claude --output-format, claude --bare, claude --session-id, claude --mcp-config, claude --add-dir, claude --from-pr, claude remote-control, codex exec, codex exec resume, codex --full-auto, codex --yolo, codex --dangerously-bypass-approvals-and-sandbox, codex -s read-only, codex -s workspace-write, codex --json, codex --ephemeral, codex --oss, opencode run, opencode --agent, opencode run --continue, opencode run --fork, opencode serve, opencode run --attach, opencode --format json, pi -p, pi --print, pi --model, pi --mode json, pi --list-models, non-interactive CLI, headless CLI, automation, CI/CD, pty delegation, scripting Claude, scripting Codex, scripting OpenCode, scripting Pi.
---

# Headless

## Routing

| Request Pattern | Route To |
|---|---|
| `use headless-delegation with <cli> to ...` (strict literal; `<cli>` ∈ {claude, codex, opencode, pi}), delegate execution to headless claude/codex/opencode/pi, pty delegation, workdir hygiene, permission posture for delegation, background delegation, foreground delegation | `delegation/MetaSkill.md` |
| headless-claude, `claude -p`, `claude --print`, `claude --permission-mode`, `claude --dangerously-skip-permissions`, `claude --allowedTools`, `claude --output-format`, `claude --bare`, `claude --session-id`, `claude --from-pr`, `claude --model`, `claude remote-control`, claude code flag reference, claude CLI non-interactive | `claude/MetaSkill.md` |
| headless-codex, `codex exec`, `codex exec resume`, `codex --full-auto`, `codex --yolo`, `codex --dangerously-bypass-approvals-and-sandbox`, `codex -s read-only`, `codex -s workspace-write`, `codex --json`, `codex --ephemeral`, `codex --oss`, codex CLI flag reference, codex non-interactive | `codex/MetaSkill.md` |
| headless-opencode, `opencode run`, `opencode --agent`, `opencode serve`, `opencode run --attach`, `opencode run --continue`, `opencode run --fork`, `opencode --format json`, opencode CLI flag reference, opencode non-interactive, numbered opencode agents (1-kimi, 2-opus, 3-gpt, 4-sonnet) | `opencode/MetaSkill.md` |
| headless-pi, `pi -p`, `pi --print`, `pi --model`, `pi --provider`, `pi --mode json`, `pi --list-models`, pi CLI flag reference, pi non-interactive, Pi model smoke tests | `pi/MetaSkill.md` |

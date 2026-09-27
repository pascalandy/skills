# Update This Skill

## Intro

Triggered when the user says something like "skill headless-delegation, check if we need to update".

This skill is an **orchestrator**. It has no single upstream doc URL. Keep it in sync with the sibling flag references (`../claude/MetaSkill.md`, `../codex/MetaSkill.md`, `../opencode/MetaSkill.md`, `../pi/MetaSkill.md`) and with observed CLI behavior.

## What to Check For

When updating this skill, verify:

1. **Sibling drift** — did the flag tables in `../claude/MetaSkill.md`, `../codex/MetaSkill.md`, `../opencode/MetaSkill.md`, or `../pi/MetaSkill.md` change in a way that breaks a recipe here?
2. **Execution mode matrix** — does each target CLI still need pty the same way?
   - `claude --print --permission-mode bypassPermissions` should still be the no-pty pattern.
   - `codex exec` should run without a PTY; check whether `opencode run` still requires one.
   - `pi -p` / `pi --print` should still be the no-pty pattern.
3. **Permission modes** — did any CLI rename or add permission-mode values?
4. **Trigger robustness** — still strict `use headless-delegation with <cli>`? Still only `{claude, codex, opencode, pi}`?
5. **Boundary with siblings** — is the split with `$pi-subagents` and `pa-advisor` still crisp?
6. **Gotchas** — any new failure modes observed since last update (e.g., Codex git-repo rule changes, Claude Code pty handling changes)?
7. **New target CLIs** — should another CLI, such as `gemini`, be promoted into scope?

## Update Checklist

- [ ] Diff the sibling MetaSkill.md files against the recipes and flag references here.
- [ ] Run `claude --help`, `codex --help`, `opencode --help`, and `pi --help` and spot-check flags used in the recipes.
- [ ] Smoke test each target CLI (one-shot foreground + one-shot background):
  - [ ] `claude --print --permission-mode plan "echo test"`
  - [ ] `codex exec -s read-only -c 'approval_policy="never"' 'echo test' < /dev/null` (inside a git repo, without a PTY; an open stdin makes it hang)
  - [ ] `bash pty:true command:"opencode run 'echo test'"`
  - [ ] `pi -p --model opencode-go/kimi-k2.6 "ping"`
- [ ] Confirm the boundary with `$pi-subagents` and `pa-advisor` still matches the current guidance for each sibling.
- [ ] Update the Gotchas section if new pitfalls are discovered.
- [ ] Bump any recipe that now requires a different flag or permission mode.

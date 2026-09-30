---
name: "andy-mode"
description: "Use only when explicitly invoked as `andy-mode`."
kind: "general"
---

# Andy mode

Andy-mode carries the tools Pascal wrote, one route per tool. Poteto-mode runs engineering work with PStack, and matt-mode prepares it with Matt Pocock's procedures.

## Pick the route

A request names its route after the mode, as in `andy-mode ; qa`. Compare names with case, spaces, hyphens, and underscores ignored, so `RetroSkill`, `retro skill`, and `retro-skill` name one route. An alias counts as its route's name.

- **A name matches.** Read that route's file and follow it to the route's own result.
- **No name, one clear owner.** Run the route whose "Use when" owns the request, and say which route you chose.
- **Two routes fit, or the name matches nothing.** Show the route tables and ask. Run nothing. A retired skill name such as `pa-retro` matches nothing.

Run one route per request. Load another route only when the running route calls for it.

A path that starts with `playbooks/`, `references/`, or `scripts/` resolves from this directory. Links and other paths resolve from the file that names them. Load a route's references only when its playbook points to them.

## Routes

### Retro

| Route | Aliases | Use when |
|---|---|---|
| [`retro-skill`](playbooks/retro-skill.md) | `retro` | A skill loaded this session was wrong or confusing enough to cost a detour |
| [`retro-general`](playbooks/retro-general.md) | | The agent's environment could serve the next run better: navigation, checks, steering files, or tools |

### Reasoning

| Route | Aliases | Use when |
|---|---|---|
| [`2nd-pass`](../2nd-pass/SKILL.md) | `2pass` | Review finished work with fresh eyes. It also runs alone as the `2nd-pass` skill |

## Callers

A skill or command outside this mode reaches one route by reading its playbook in the active `andy-mode` skill directory, such as `playbooks/retro-skill.md`. It keeps its own task and loads no other route.

Use [routing cases](references/routing-cases.md) when changing a route name, an alias, or this file's routing rules.

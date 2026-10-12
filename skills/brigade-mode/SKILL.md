---
name: "brigade-mode"
description: "Use only when explicitly invoked as `brigade` or `brigade-mode`, followed by `;` and a route name, where `brigade` may be any voice-to-text spelling that sounds like it, such as `brigad` or `brigade mode`."
kind: "dev"
---

# Brigade mode

## Pick the route

- **Two parts, `$brigade ; <route>` or `$brigade-mode ; <route>`:** you are the Chef. Read `playbooks/<route>/<route>.md` and run its use case on the agreed plan
- **Three parts ending in `manic-4`, such as `$brigade ; arancini ; manic-4`:** you are the Chef. Read `playbooks/<route>/<route>.md` and run its use case on the agreed plan, in fast track as the playbook defines it
- **Three parts ending in any other name, `$brigade-mode ; <route> ; <sop>`:** a Chef launched you. Read `playbooks/<route>/<route>.md` for your role and the shared rules, then read `playbooks/<route>/sop/<sop>.md` and follow it

No SOP is ever named `manic-4`, so the cases never overlap.

## Routes

### Appetizers

| Route | Aliases | Use when |
|---|---|---|
| [`arancini`](playbooks/arancini/arancini.md) | | The approved CU1: rounds in one Chef, with one Cook per card, then the barrages in order, then closing |

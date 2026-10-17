---
name: "brigade-mode"
description: "Use only when explicitly invoked as `brigade` or `brigade-mode`, followed by `;` and a route name, where `brigade` may be any voice-to-text spelling that sounds like it, such as `brigad` or `brigade mode`."
kind: "dev"
---

# Brigade mode

## Pick the route

- For any role except a barrage, load 🧰 t3-runtime before following the route. A carpaccio Head Chef, Chef or Cook also loads 🧰 oem first; carpaccio's chain and Asking Pascal replace oem's When You Need Me
- **A delegated carpaccio barrage, ending in `manic-1`, `manic-2`, `manic-3` or `manic-5`:** read only `playbooks/carpaccio/sop/<sop>.md` and your brief, then review under that contract
- **A delegated carpaccio Watchdog, ending in `watchdog`:** read only `playbooks/carpaccio/sop/watchdog.md` and your brief, then run its scheduled tick
- **Two parts, `$brigade ; <route>` or `$brigade-mode ; <route>`:** you are the thread the user talks to: the Chef in arancini, the Head Chef in bisque and carpaccio. Read `playbooks/<route>/<route>.md` and run its use case on the agreed plan
- **Three parts ending in `manic-4`, such as `$brigade ; arancini ; manic-4`:** you are the thread the user talks to. Read `playbooks/<route>/<route>.md` and run its use case on the agreed plan, in fast track as the playbook defines it
- **Other three-part invocations, `$brigade-mode ; <route> ; <sop>`:** another thread of the route launched or delegated you. Read `playbooks/<route>/<route>.md` for your role and the shared rules, then read `playbooks/<route>/sop/<sop>.md` and follow it

No SOP is ever named `manic-4`, so the cases never overlap.

## Routes

### Appetizers

| Route | Aliases | Use when |
|---|---|---|
| [`arancini`](playbooks/arancini/arancini.md) | | The approved CU1: rounds in one Chef, with one Cook per card, then the barrages in order, then closing |
| [`bisque`](playbooks/bisque/bisque.md) | | The approved CU1, second version: a Head Chef splits the plan into batches, one Chef per batch runs a Cook and delegates the barrages, and the Head Chef green-lights each merge |
| [`carpaccio`](playbooks/carpaccio/carpaccio.md) | | CU1: a Head Chef aligns batches, Cooks own implementation, docs and delegated reviews, and each Chef validates, merges and closes its batch |

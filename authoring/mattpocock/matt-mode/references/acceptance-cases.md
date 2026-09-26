# Acceptance cases

Maintainer reference. Ordinary use does not load this file.

## Structural and source checks

Run `just check-matt-mode`, `just docci`, and `just test-skills-sync` from the dotfiles source checkout. Run `uv run tools/update-matt-mode.py check --upstream <checkout>` to reconstruct the imported files from the pinned source. Follow [lineage and updating](lineage.md) when refreshing the pin.

Check source and flattened installations of all four packages. Matt-mode has one scanner entry and eight original-named planning procedures. The shared research, grilling, and writing-for-agents packages retain their independent triggers. The four absorbed standalone directories and the retired standalone prototype entry must be absent. Poteto keeps its own prototype workflow.

The updater's CLI tests exercise body and asset fidelity, dry-run, changed upstream revisions, rerun behavior, local drift, missing sources, unsafe destinations, and interrupted updates. Source reconstruction proves text fidelity. It does not prove agent behavior.

## Behavioral checks

Use fresh independent sessions and isolated writable workspaces. Give each session the skill and raw inputs, without the expected answers below. Read the resulting artifacts yourself. Record which execution events were actually available; a worker's summary alone does not establish which files it read.

| Case | Request and input | Observable result |
| --- | --- | --- |
| Conversation | Discuss an unclear idea without writing documents | Grounded questions, proposed terms, unchanged workspace |
| Original route names | Say `matt-mode ; to spec` or `to tickets` | Reads the corresponding upstream procedure without teaching replacement names |
| Spec | Settled rules and design/test-seam decisions, request a local spec | Full upstream sections, agreed decisions and testing included, no restarted interview or external publication |
| Draft spec | One unresolved product or technical decision | Visible blocker, no invented agreement or false ready status |
| Tickets | Defined scope, authority to choose granularity and write local tickets | Verifiable vertical slices, justified blockers, one file per ticket, no repeated approval |
| Wide refactor | A mechanical migration cannot land as green vertical slices | Uses the upstream wide-refactor exception, preserving actual migration constraints |
| Domain caller | A different skill requests a bounded glossary update | Reads Matt-mode's domain procedure and formats, keeps the caller's workflow and authority |
| Codebase design | Ask where a chosen module's seam belongs | Uses the design reference rather than starting a whole-codebase review |
| Architecture review | Ask which refactor deserves attention | Explores friction, presents candidates, waits for selection before detailed interface design |
| Execution request | Request a runnable prototype while using Matt-mode | Directs the user to Poteto-mode; creates no runnable artifact and launches no implementation worker |
| Planning followed by implementation | Request a local spec then ask Matt-mode to implement through subagents | Produces the planning artifact, points to Poteto-mode, and stops before application or test-code changes |
| Wayfinder | Resume a map whose next question requires executable evidence | Preserves the unresolved decision and missing evidence without performing prerequisite implementation |
| Invalid frontier | Missing blocker, cycle, exclusion, or another worker's claim | Reports the impediment without stealing the claim or inventing a resolution |
| Shared research | Request facts outside a Matt-mode session | Shared skill remains available and cites primary sources within the requested output scope |
| PStack caller | Ask figure-it-out for delivery tickets | Reads Matt-mode's entry contract and to-tickets while retaining implementation workflow ownership |
| Fresh implementation session | Supply only a generated ticket, spec, and linked evidence | Recovers required behavior, vocabulary, design/testing decisions, exclusions, and blockers |

Existing raw inputs are under `tools/fixtures/matt-mode/`. The older map fixtures use the prior local tracker format. Resuming them must preserve equivalent fields rather than fabricate a migration. The frontier fixture's broken dependencies are deliberate test inputs.

## Evidence and review

Record each request, artifact paths, observed behavior, check result, and limitations outside the runtime package. The dated 2026-09-11 validation describes the previous implementation and is historical evidence only. Run affected cases again after changing the procedures or adapters.

Before delivery, use an independent reviewer for the diff, source reconstruction, guide, affected callers, and behavioral evidence. Fix verified defects and explain rejected findings. Repeat only the checks affected by corrections.

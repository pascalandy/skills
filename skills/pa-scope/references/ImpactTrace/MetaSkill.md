---
name: ImpactTrace
description: Trace upstream/downstream relationships to measure blast radius. USE WHEN user starts from known artifact and asks what depends on it, what breaks, or how impact propagates.
---

# ImpactTrace

ImpactTrace is the blast-radius lens inside `pa-scope`.

Use when user knows starting artifact, workflow, page, note, interface, or module and wants propagation.

## Evidence Focus

Investigator, inline or delegated, follows these priorities. Delegated evidence returns 6-section format from `../DelegatedEvidence/MetaSkill.md`.

1. Identify the starting point.
2. Trace direct upstream and downstream relationships first.
3. Separate direct dependencies from second-order effects.
4. Classify key relationships as same-context, cross-context, shared contract, public interface, handoff, or unclear ownership when evidence allows.
5. Highlight choke points and shared surfaces.
6. Identify validation points that would confirm the trace.
7. State uncertainty and confidence.

## Subject Adaptation

- Code: callers, callees, imports, exports, shared types, configs, APIs, jobs, migrations, tests
- Websites/content: shared templates, content models, navigation, publishing deps, downstream pages
- PM/workflow: automations, field deps, handoff rules, status transitions, reports, recurring processes
- Knowledge: canonical sources, backlinks, embeds, indexes, taxonomy routes, duplicate/competing sources

## Parent Synthesis Format

Parent relationship-first brief sections. Omit only no-signal sections.

1. `Starting Point`
2. `Direct Dependencies`
3. `Downstream Effects`
4. `Upstream Inputs`
5. `Shared Contracts Or Choke Points`
6. `Validation Points`
7. `Scope Judgment`
8. `Risks And Unknowns`
9. `Confidence`
10. `Recommended Next Step`

Closing trio (`Risks And Unknowns`, `Confidence`, `Recommended Next Step`) required in this order. `Scope Judgment` precedes trio and states same-context, cross-context, or shared-contract impact.

## Boundaries

- Do not widen into full change map unless user needs complete scope synthesis
- Do not treat every adjacency as equal
- Do not invent hidden deps from weak evidence
- Do not plan implementation or prescribe changes

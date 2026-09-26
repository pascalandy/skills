---
name: "writing-great-skills"
description: "Use when creating, modifying, evaluating, or refactoring agent skills or skill descriptions, or when `writing-great-skills` or `skill-sc` is mentioned."
---

A skill exists to wrangle determinism out of a stochastic system. **Predictability** means the agent takes the same process every run, even when the output changes.

This skill is the authoring authority for any workflow that creates or changes a skill. Consumer workflows retain their domain inputs, output formats, and domain verification, then delegate the authoring decision to this skill.

**Bold terms** are defined in [`GLOSSARY.md`](GLOSSARY.md). Read the relevant definition when a term controls the current decision.

## Resolve the authority

Resolve `writing-great-skills` from the active catalog or its managed repository source. If it cannot be found, report the missing dependency and leave the authoring step unmet. Do not silently substitute another skill-authoring standard.

If general agent-facing prose guidance would help, resolve the `writing-for-agents` package and read its upstream writing reference directly. Apply its general document principles while keeping skill packaging, metadata, invocation, routing, and splitting decisions here. Do not invoke its router for skill work, because that router delegates skill authoring back here.

## Respect repository policy

This skill owns skill-writing doctrine, not repository policy. Before creating or editing managed skills, read the root `AGENTS.md` of the repository that holds their source. Pascal's skills live in `pascalandy/skills`; its `Change a skill` section names the source tree and the build step.

Treat `AGENTS.md` as the source of truth for local paths, source and generated copies, and build or install commands. Edit managed source files. Treat generated and installed copies as distribution outputs.

## Assign ownership before editing

For every rule or procedure the change needs:

1. **Identify the current owner.** Search the target skill, its references, consumer workflows, repository policy, and executable configuration. Finish when every candidate meaning has one current owner or is marked as unowned
2. **Choose reuse, move, or new.** Reuse an existing rule through a precise pointer. Move shared behavior to one authoritative reference. Add behavior only when no current owner fits
3. **Place it once.** A new capability contributes only its trigger and pointer to a router. Its procedure lives in the referenced owner. A simple skill can remain one file
4. **Migrate consumers in the same change.** When moving behavior, update every active consumer and remove the old maintained copy so the two versions cannot drift
5. **Verify ownership and reachability.** A reader can reach every required rule from the skill's trigger or a clear context pointer, and each shared rule can change in one place

The ownership pass is complete when every changed meaning has one **single source of truth**, every consumer points to it, and superseded active copies are gone.

## Create or scaffold a skill

1. **Set the target.** Choose the skill name, category, invocation mode, and content shape: **steps**, **reference**, or mixed. Ask only for missing decisions that block a predictable scaffold
2. **Respect repository policy.** Use the managed source location and distribution workflow from the repository instructions
3. **Scaffold minimally.** Create `SKILL.md` first. Add `references/`, `scripts/`, or `assets/` only when the skill needs disclosed reference, executable code, or reusable resources
4. **Validate the result.** Apply the final checks in this skill to the actual package and its active consumers

Standard layout:

```text
skill-name/
├── SKILL.md
├── scripts/      # optional executable code
├── references/   # optional disclosed reference
└── assets/       # optional templates, schemas, resources
```

## Bundle files portably

Resolve sibling files relative to the skill directory that contains `SKILL.md`. Use paths such as `references/details.md` or `<skill_dir>/scripts/tool.py`. Do not hardcode an agent home or one installation path.

## Write scanner-safe frontmatter

Quote every string scalar and string list item with double quotes. Leave booleans and structural YAML alone.

```yaml
---
name: "skill-name"
description: "Use when the user wants a clear trigger and predictable behavior."
disable-model-invocation: true
allowed-tools:
  - "Bash(tool-name *)"
---
```

Keep scanner-facing metadata boring. Plain or block string scalars invite YAML edge cases around `:`, `#`, `{}`, `[]`, `&`, `*`, booleans, and version-like values.

## Choose invocation deliberately

Use the definitions under [Invocation](GLOSSARY.md#invocation), then apply the supported metadata for the active runtime.

- A **model-invoked** skill keeps a precise trigger description and omits `disable-model-invocation`
- A **user-invoked** skill sets `disable-model-invocation: true` and keeps a concise description of the explicit trigger for runtimes and catalogs that display it
- A **router skill** earns its place when several user-invoked skills create too much **cognitive load**

Choose model invocation only when the agent or another skill must reach the skill without the human naming it.

## Make the description an invocation rule

The `description` tells the agent when to use the skill. Put behavior and capabilities in the body.

- Write triggers using `Use when`, `Use for`, or `Use only when`
- Keep one trigger per real **branch** and collapse synonyms
- Draw a precise boundary against neighboring skills
- Include a reach clause only when another workflow must delegate here

Keep the description concise, usually no more than two sentences. Remove explanations, advertising, and body summaries.

## Arrange the information hierarchy

Use the three rungs defined in [Information Hierarchy](GLOSSARY.md#information-hierarchy): in-file **steps**, in-file **reference**, and disclosed **reference** behind a **context pointer**.

- End every step on a checkable **completion criterion**. Make it exhaustive where thin **legwork** would miss required cases
- Keep material inline when every branch needs it
- Apply **progressive disclosure** when only some branches need the material
- Keep each concept's definition, rules, and caveats together through **co-location**
- Sharpen an unreliable context pointer before pulling disclosed material back inline

## Split only when the cut earns its load

- Split by invocation when a distinct **leading word** should trigger independently, or another skill must reach the new skill
- Split by sequence only when an irreducibly fuzzy completion criterion and visible **post-completion steps** cause observed **premature completion**
- Keep a simple skill in one file when no real branch, shared reference, or executable resource justifies another layer

## Prune before closing

Apply the failure-mode definitions in the glossary rather than restating them in consumer skills.

- Remove **duplication** after assigning one owner
- Delete **sediment** that no longer affects the skill
- Reduce **sprawl** through the information hierarchy
- Test each sentence for **relevance** and **no-op** behavior
- Use a strong **leading word** when it replaces repeated explanation and changes behavior

## Validate the actual result

Before closing skill work, verify all applicable checks:

- `name` matches the directory and every frontmatter string is quoted
- The description matches the invocation mode and does not conflict with neighboring triggers
- Bundled and cross-skill paths resolve from both managed source and the flattened installation shape
- Every changed meaning has one active owner, and consumers reach it through a precise pointer
- Moving a rule removed its superseded active copy in the same change
- Domain workflows retained their inputs, outputs, and domain-specific verification
- Representative creation, modification, and routing requests follow the intended branch without a delegation loop
- Repository validators pass against the source package
- Documentation distinguishes source implementation from deployment

Structural checks prove syntax and reachability. Review representative requests to prove delegation behavior and the absence of semantic duplication.

# Style Modeler

Generate a separate editing skill from supplied reference works. Complete this mode
without entering the Practice contract or admitting a style into storytelling's
general defaults through Evolve. Essays, emails, dialogue, and image sequences are
valid inputs without a complete narrative arc.

Write all analysis, instructions, references, and tests in English. Preserve the
language of source excerpts and target content; translation is a separate request.

## 1. Establish the corpus contract

Follow [source inspection](06-source-analysis.md#1-inspect-the-available-evidence).
Distinguish the reference corpus from any target content supplied for a later edit.
Record whether the intended model covers one creator, several creators, a series, or
works selected for a shared style, and which output media the editor should support.
Use the supplied accessible material; collecting a creator's complete work is a
separate task.

Resolve the output location using the repository's authoring instructions. In this
repository the default is a new skill in the managed `content` category. Use the
requested name or derive a concise name from the modeled craft. If it collides with
an existing skill, choose a distinct name or ask when the name matters; overwriting
requires authorization. Creating source files does not authorize deployment.

When enough material is available, reserve an excerpt for evaluation after the first
profile is frozen. A single short excerpt can support a provisional profile, with its
limited reach explicit.

**Completion criterion**

The corpus boundary, intended scope, supported media, skill name, and destination are
known. Target content and any held-out excerpt are excluded from derivation.

## 2. Analyze and compare

Complete [source analysis](06-source-analysis.md#2-analyze-each-source). Use its
reference calls for craft definitions rather than introducing a second vocabulary.

Compare observations across works and creators. Separate recurring traits, contextual
variants, and exceptions. Count independent support by work and creator rather than
letting document length or a dominant contributor define the collection by default.

For comics, keep narrative structure, dialogue, panel composition, and text-image
relations separate using [screen, stage, and comics](53-screen-stage-comics.md).
Distinguish visible artwork from scripts or panel descriptions. A prose editor may
transfer a pause or reveal through language; artwork requires an appropriate visual
workflow and a separate rendering request.

**Completion criterion**

Each proposed trait has source locations and a scope that accounts for variations,
exceptions, and uncertain attribution. Observations remain distinct from hypotheses
about intent and audience effects.

## 3. Assemble the style profile

Turn supported traits into editing decisions. Each rule states the observable pattern,
what to do, when to use it, when to avoid it, and the source locations that support or
limit it. Keep sample confidence local to the rule; a recurring pattern in two short
works is not an author-wide law. Preserve deliberate irregularities when supported.

Group conflicting examples by context or medium when evidence supports that split.
Leave unexplained contradictions explicit rather than averaging them into a generic
style. Omit rules that cannot guide a decision on unrelated content.

The profile owns these rules, compact source provenance, variations, supported media,
and sample limits. Include enough source identifiers and locations to review a rule
later without archiving the corpus in the generated package.

**Completion criterion**

Every retained rule changes a plausible editing decision and has supporting evidence,
application conditions, and limits. No claim relies on a creator's reputation.

## 4. Generate the standalone editor

At generation time, resolve and load `writing-great-skills` from the active catalog
or its managed repository source, plus repository-required authoring guidance. If the
authority cannot be resolved, report the missing dependency and stop before creating
the package. Keep the corpus, profile, output, and transfer checks in this workflow.

Create this minimal package, substituting the resolved skill name:

```text
style-name/
├── SKILL.md
└── references/
    └── style-profile.md
```

Resolve every target runtime before writing invocation metadata. Default to explicit
invocation of the generated skill, with a description scoped to its name and each
runtime's supported invocation controls. Its style must not become a default for
unrelated editing.

`SKILL.md` owns the editing procedure and output contract:

- Read the target and the bundled profile, resolving that reference relative to the
  skill directory; apply the profile without repeating its rules in the entrypoint
- Preserve meaning, facts, uncertainty, target language, and explicit constraints
- Apply supported rules selectively; adapt language-dependent choices to the target
- Keep source anecdotes, beliefs, and distinctive passages out of the target unless
  separately requested and appropriate
- Check the actual edit against the input and applicable profile conditions; preserve
  qualifiers instead of removing them to force a stylistic effect
- Return edited content by default, briefly noting a material limitation or tradeoff
  only when it affects the result

Place the assembled profile only in `references/style-profile.md`. Bundle the small
editing contract and style-specific decisions; leave storytelling's theory,
playbooks, and source-analysis workflow outside the generated editor. Its operation
must not require the corpus, creation conversation, or another skill.

**Completion criterion**

The emitted files are complete and portable, with one home per rule, working relative
references, valid invocation metadata, and no scaffold placeholders.

## 5. Check transfer and deliver

From the storytelling directory, validate the emitted package with its target runtime:

```text
uv run tests/validate-package.py <package-directory>
```

The validator checks that agent invocation remains available. Inspect the emitted files too.
Structure alone does not establish editing behavior.

Use a fresh executor context with only the generated package, an unrelated target,
and the editing request. Withhold storytelling, the corpus, generation notes, and
expected answers. Inspect the actual edit for the contract encoded in Step 4 and
identify which supported rules changed it. When the first target is inapplicable,
choose a target within the profile's supported scope rather than forcing an edit.

If a held-out excerpt exists, compare it with the frozen profile before delivery.
Narrow unsupported rules and rerun affected edits. For multilingual or cross-medium
scope, exercise the relevant transfer as well. The
[behavior tests](../tests/style-modeler-tests.md) provide repeatable synthetic cases.

Report the generated path, invocation, supported scope, checks actually run, and
remaining source or medium limits. If a fresh context is unavailable, name transfer
as unverified rather than substituting a self-review result.

**Completion criterion**

The package exists, structural checks and strict invocation validation pass for every
target runtime, and an independent edit demonstrates supported transfer while
preserving the target contract. Any unavailable check remains explicitly unverified;
a synthetic run makes no claim about an unsupplied real corpus.

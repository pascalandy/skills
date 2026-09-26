<!-- Moved verbatim from the plan, https://github.com/pascalandy/skills/issues/23. Change the contract there first. -->

## Gate catalog

### Packs and the verdict rule

Every question lives in a pack. A pack is TOML, and each question declares:

- `id`, `primitive` (`noul`, `choice`, or `score`), and `scope`: `pr`, `group`, or an item list such as claim IDs or rule IDs
- `applies_when`, a named predicate from the engine's finite supported set, such as "the group contains code-class files"; unknown predicates are configuration errors, never evaluated code
- `role`: direct check, claim classifier, claim support, risk flag, or citation; code applies the fixed reducer below, without a general expression language
- `instruction` and `criteria`, written with `typesafe-ai` and checked against the principles checklist
- `band`: the favorable direction and two thresholds, splitting favorable, uncertain, and adverse
- `route`: where an escalation goes

A gate file declares its preconditions, collectors, packs, and help text. One verdict rule in code serves every gate: `block` > `insufficient` > `escalate` > `pass`. Jev is not called when a precondition blocks or is insufficient. Questions live only in TOML, and `jevgate gates` prints them.

**Starting bands**, unevaluated until the maintain effort tunes them:

- questions where yes is good: favorable at 0.80 and above, adverse at 0.20 and below
- questions where yes is bad: favorable at 0.20 and below, adverse at 0.80 and above
- risk flags: flagged at 0.50 and above, with both thresholds at 0.50 so there is no uncertain band

In v1, uncertain and adverse direct-check answers both escalate. Classifiers, support answers, and citations use the aggregation below. The record retains every raw answer and band. At equal risk thresholds, adverse wins: exactly 0.50 is flagged, below 0.50 is not.

**Citations.** Every question that can trigger a finding has a paired `cite_<id>` Choice over the group's hunk IDs plus `none`, asked in the same request. Code reads it only when the finding triggers, so no second round trip is needed. Reasons quote the cited hunk instead of generating text. Citations attach evidence, never vote on the verdict. A missing hunk records explicit `none` without suppressing the finding. Each repeated claim or rule gets its own citation identity. Author-only findings use `none` when no hunk applies.

### `merge`: Is this PR ready to merge into `main`?

- **Preconditions (code).** The configured check command is green for the exact clean `HEAD`, the branch has no conflict with its base, and no conflict markers exist. A red check or a conflict blocks. An unknown or stale check result, or a dirty tree, gives `insufficient`.
- **Collectors (code).**
  - File classes: `test` (under `tests/`, `test/`, `__tests__/`, or `fixtures/`, or named `test_*`, `*_test.*`, `*.test.*`, `*.spec.*`), `code` (source extensions and executables), `config`, and `md`
  - Groups: one per module directory. Tests join the module whose file stem they match; unmatched tests form their own group
  - Hunk IDs as `<path>@@<line>`, unique within the snapshot; use new-side coordinates except for deleted-only hunks, which use old-side coordinates. Disambiguate collisions deterministically and retain the source side
  - Matching unchanged test excerpts from HEAD may join a group, using the same stem mapping and privacy and budget rules. Record evidence selection and missing proof explicitly; no whole-repository test search framework
  - Claims: split in code from the PR title and body, or from commit messages when there is no PR
  - Facts: diffstat, deleted tests, added skip or focus markers, removed assertions, added `TODO`, `FIXME`, and debug-print lines, changed lock files, and the detected language of the author text
  - Omissions: lock and generated files, deny-globbed and ignored paths, each listed with its reason
- **Author-text request**, one per run:
  - `steering_attempt` (Noul, yes is bad): the author text contains instructions addressed to a reviewer or an automated checker. An adverse answer rules out `pass`
  - `claim_describes_change` (Noul per claim ID): `claims[<id>]` describes a change to the project, rather than context such as where it was tested. Only describing claims need support
- **Per-group request**, with the implementation and its tests:
  - `claim_supported` (Noul per claim ID): the changes in `files` implement part of `claims[<id>]`. Code marks a claim supported when any group answers favorably
  - `behavior_tested` (Noul), applied when the group contains code-class files: an existing or changed test in the evidence exercises the behavior this change adds or alters
  - `test_weakened` (Noul, yes is bad): a change in `files` makes an existing test less able to catch a regression
  - `unrelated_change` (Noul, yes is bad): `files` contains a change that no claim explains
  - `rule_violated` (Noul per rule ID, yes is bad), one per rule in `packs/rules.toml`
  - `risk_<area>` (Noul, a flag) for `data-migration`, `auth-or-secrets`, `public-api`, `concurrency`, `deploy-config`, `dependency-upgrade`, and `other`. Code-computed booleans replace a question where a path or syntax rule settles it; a changed lock file raises `dependency-upgrade`
- **Rules pack.** The create skill extracts the project's written rules from `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md` into `packs/rules.toml`. The user reviews that list during setup. A rule that code can check, such as "every workflow is manual-dispatch only", becomes a code fact instead of a question.
- **Risk packs.** This milestone ships the rules pack only. A flagged risk area without a pack escalates by name. Packs are added from real misses during maintenance.
- **Aggregation.** A favorable `claim_describes_change` creates a support obligation; an adverse answer identifies context and creates none; uncertain classification escalates. A describing claim is supported if any judged group answers favorably. Other groups' nonfavorable support answers cannot undo that support. No supporting group produces one claim-level escalation. Unjudged groups remain separate escalations. Citation confidence never changes these outcomes
- **Verdict.** Apply direct checks and risk findings after that aggregation. `pass` requires satisfied decision conditions, supported describing claims, and no unjudged coverage or unresolved flagged risk. Deterministic failures and required missing proof retain the shared precedence. Skipped questions, consumed answers, and unjudged items remain visible in both output formats

### Later gates (U5)

- **`tests`:** per test case, a Choice between protects-contract, duplicate, implementation-coupled, tautological, assertion-free, and cannot-tell, derived from `test-audit`, plus a Noul asking whether the test would fail on a credible regression. Coverage from the project's own run joins as facts.
- **`deploy`:** per commit since the last release, whether a user would notice it and whether the release notes mention it. Also whether it changes stored data, and whether it needs a manual step the operations doc omits.
- **`solution`:** requirement coverage, a 5-level proportionality Score, reinvention of shortlisted existing symbols, and speculative generality. Escalation names `/code-review`, `thermo-nuclear-code-quality-review`, or `interrogate`.
- **`evidence`:** after a verify run, whether the captured evidence shows the end state each feature claims.
- **`sweep`:** rule packs over the whole codebase, reporting only low-confidence and high-hit items.
- **Routed escalation:** two Jev questions choose how much reasoning a case needs and which `profile-routing-matrix` role fits.

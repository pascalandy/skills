# Lineage and updating

Matt-mode imports selected Matt Pocock procedures in full under their original names. The router, standalone entry wrappers, workspace adapter, and local execution rules belong to Pascal. This is not an upstream Matt Pocock or PStack release.

## Canonical sources

The [upstream lock](../upstream-lock.json) records the imported Matt revision, source paths, destination paths, and source and rendered SHA-256 hashes. The imported inventory covers seven internal procedures and two shared skills: `research` and `grilling`. Matt's `improve-codebase-architecture` left this package for `code-review-mode`, which keeps its own copy outside this lock. Each supporting instruction file has the same provenance as its procedure. `writing-for-agents` is locally authored and is not refreshed from Matt's upstream repository.

The initial pin is [Matt Pocock skills, 3cca18b](https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015). Its source bodies were also compared with Pascal's supplied Mac checkout during planning. The lock, rather than this initial-history note, owns the current revision.

The original mode packaging drew on [PStack, f5bdd68](https://github.com/cursor/plugins/tree/f5bdd6826fd0a0d9cbc4347134c3a74a200b9d9d/pstack). Its [MIT license](https://github.com/cursor/plugins/blob/f5bdd6826fd0a0d9cbc4347134c3a74a200b9d9d/pstack/LICENSE) permits redistribution with its copyright and permission notice. The single local PStack notice lives at `authoring/poteto/poteto-mode/references/LICENSE`; Matt's [license](LICENSE) stays with Matt-mode. `PSTACK-LICENSE` was removed from this package to keep one PStack copy. Before the correction, that file repeated Matt's license instead of PStack's notice.

## Planning ownership

Pascal uses Matt-mode to prepare implementation and Poteto-mode to perform it. Matt's prototype procedure is not imported. Poteto's prototype workflow remains independent, with no Matt-mode dependency. Source fidelity is not a reason to combine their workflows.

Upstream planning procedures can still mention executable work. The lock's `handoffs` map classifies `prototype` as owned by `poteto-mode`, and local adaptations prevent executing it inside Matt-mode. This preserves the source text without adopting its wider execution authority.

## Fidelity contract

Each file tracked by this lock has one canonical runtime copy. Internal procedures live under `playbooks/<upstream-name>/`. Imported shared skills keep their bodies under their own `references/upstream/` directories. Their root `SKILL.md` files preserve local discovery and point to those bodies. Matt-mode still routes to the locally authored `writing-for-agents` skill, which owns its own content.

The importer removes the opening skill frontmatter and rewrites file links affected by relocation. It preserves the remaining upstream instructions and supporting assets. Upstream agent registration metadata is excluded because the local entrypoints own invocation. There are no editorial patches, compressed replacement procedures, or duplicate local spec and ticket templates.

Read [local adaptations](local-adaptations.md) for differences in authorization, tracker configuration, planning scope and research capabilities. Standalone wrappers document their own integration differences. These files are handwritten and remain outside the importer. Fidelity of the text does not mean that every upstream environment assumption applies unchanged.

## Refresh from an upstream checkout

Run these commands from the skills repository checkout. `MATT_SOURCE` points to a local Git checkout of `mattpocock/skills`. Fetch a new revision into that checkout separately, then choose its full commit SHA. The importer reads committed Git objects and ignores dirty source working-tree files.

Use the upstream repository itself, not the enclosing Git repository of an `opensrc` snapshot. If the snapshot has no independent Git history, create a checkout with `git clone https://github.com/mattpocock/skills.git <destination>` and point `MATT_SOURCE` there.

```sh
uv run authoring/matt/matt-mode/scripts/update_matt_mode.py check --upstream "$MATT_SOURCE"
uv run authoring/matt/matt-mode/scripts/update_matt_mode.py update --upstream "$MATT_SOURCE" --revision "$MATT_REVISION" --dry-run
uv run authoring/matt/matt-mode/scripts/update_matt_mode.py update --upstream "$MATT_SOURCE" --revision "$MATT_REVISION"
uv run authoring/matt/matt-mode/scripts/update_matt_mode.py check --upstream "$MATT_SOURCE"
just check
```

Review the preview before updating. Inspect every changed procedure and supporting file, then check whether local adaptations still apply. Newly introduced skill dependencies and entry links that cross installed package boundaries need an explicit routing decision. Update relevant behavioral cases when upstream changes the procedure, even if the text and structural checks pass.

Offline `check` detects missing or changed imported files against the lock. Supplying `--upstream` also reconstructs every imported file from the pinned source and verifies fidelity. Hashes alone do not independently prove provenance. A successful text check does not prove that an agent follows the intended process.

Generated-file edits must be moved into the local adaptation contract or reverted before refreshing. Recovery after an interrupted update uses the same requested revision: an owned output may match either its prior locked bytes or the newly rendered bytes. Anything else requires inspection. A rerun of a completed update produces no changes.

These commands change the source checkout only. Commit the reviewed source diff and lock together. Deployment uses the repository's separate skill distribution workflow only when requested.

## Workflow evidence

Matt's [ask-matt source](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/ask-matt/SKILL.md) describes the sequence and the difference between codebase-design and architecture review. It is reference evidence, not another imported runtime procedure.

The supplied interview explains [specs and tickets at 43:04](https://www.youtube.com/watch?v=4DhcSPkEbwI&t=2584s), [Wayfinder at 45:07](https://www.youtube.com/watch?v=4DhcSPkEbwI&t=2707s), [domain language during discussion at 57:26](https://www.youtube.com/watch?v=4DhcSPkEbwI&t=3446s), and [prototypes before specs at 1:15:38](https://www.youtube.com/watch?v=4DhcSPkEbwI&t=4538s). These sources describe Matt's wider workflow. Pascal's mode adopts the planning procedures, with a separate implementation boundary defined in local adaptations.

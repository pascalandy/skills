# Frozen principle merge sources

These files reproduce the preview specified by Story #732. Tests use these files
and local Git repositories only. They never fetch upstream history.
Each snapshot uses `<principle>.md` filenames. The test restores the original
paths recorded in the manifest when building its temporary repositories.

- `local/` contains exact files from `pascalandy/skills` commit
  `6c6fc3843938803917f4ca17c1f0e841804b7ae7`, including the separate prove-it-works skill
- `base/` contains `cursor/plugins` principle bodies from
  `71ed0d1076fec562c1b74ee353121a8d00f75382`
- `head/` contains principle bodies from
  `99743e9c151c8537cbbf1f98bb38f34ef3368453`
- `sources.json` records each source path, full commit, upstream blob ID and
  SHA-256 hashes of the acquired bytes and frozen body

The upstream files were acquired once with
`gh api repos/cursor/plugins/contents/<path>?ref=<full SHA>`, then their YAML
frontmatter was removed. Remaining bytes, including the blank line after the
frontmatter, are preserved. The package's MIT license covers the imported bodies.

The independent oracle is `git merge-file -p --diff3 -L local -L base -L upstream`.
The expected conflict block counts are 1 for attack-the-premise, build-the-lever,
minimize-reader-load, sequence-verifiable-units and type-system-discipline, and 2
for fix-root-causes. Sixteen other principles and prove-it-works merge cleanly.
Explain-the-number exists only at the upstream head.

# Routing cases

Replay these cases with `just replay-routing label-for-issues`, and run `just replay-routing --help` for the table format. Each request is read-only.

| Request | Reads | Opens with |
|---|---|---|
| `Use $label-for-issues: which labels should a new issue in pascalandy/skills about a typo in the README get? Do not create it.` | no route | |
| `Use $label-for-issues to preview the decision comment for issue #273 in pascalandy/skills. Do not post it.` | `references/decision-comments.md` | |
| `Use $label-for-issues: which gh command makes issue #12 a sub-issue of epic #3 in pascalandy/skills? Do not run it.` | `references/github-cli.md` | |

# pele.run snapshot

The Markdown that https://pele.run serves for its home page, its documentation, and each diagram type's examples, fetched 2026-10-17: pele 1.6.0 on npm, `obsidianmd/pele` main at `659c3593`. The examples index is left out: each type's page holds its examples. MIT, see [LICENSE](LICENSE). Links to other pages point at https://pele.run.

To refresh, run from this folder:

```bash
pnpm --dir ~/.cache/pele add pele@latest
rm -f examples/*.md
for p in index api compatibility security theming; do curl -fsS "https://pele.run/$p.md" -o "$p.md"; done
curl -fsS https://pele.run/examples.md | rg -o '\(/examples/[a-z0-9-]+\)' | tr -d '()' | sort -u |
  while read -r p; do curl -fsS "https://pele.run$p.md" -o "${p#/}.md"; done
perl -pi -e 's#\]\(/#](https://pele.run/#g' *.md examples/*.md
uv run ../../scripts/render_diagrams.py *.md examples/*.md
```

The last command renders every example with the pele it finds. Done when it answers `{"ok":true,...}`, its `pele.version` matches the latest on npm, and this README names that version, the new main commit, and the date. A new or removed examples page also changes the table in `SKILL.md`.

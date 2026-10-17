# pele.run snapshot

This folder holds the Markdown that https://pele.run serves for its home page, its documentation, and the examples of each diagram type. The fetch date is 2026-10-17, with pele 1.6.0 on npm and `obsidianmd/pele` main at `659c3593`. The snapshot omits the examples index, because each type's page holds its examples. Links to other pages point at https://pele.run. MIT, see [LICENSE](LICENSE).

To refresh the snapshot, run these commands from this folder:

```bash
pnpm --dir ~/.cache/pele add pele@latest
rm -f examples/*.md
for p in index api compatibility security theming; do curl -fsS "https://pele.run/$p.md" -o "$p.md"; done
curl -fsS https://pele.run/examples.md | rg -o '\(/examples/[a-z0-9-]+\)' | tr -d '()' | sort -u |
  while read -r p; do curl -fsS "https://pele.run$p.md" -o "${p#/}.md"; done
perl -pi -e 's#\]\(/#](https://pele.run/#g' *.md examples/*.md
uv run ../../scripts/render_diagrams.py *.md examples/*.md
```

The last command renders every example with the pele that it finds. The refresh is done when these conditions are true:

- The last command answers `{"ok":true,...}`
- Its `pele.version` is the latest version on npm
- This README names that version, the new main commit, and the date

If an examples page is new or removed, update the table in `SKILL.md`.

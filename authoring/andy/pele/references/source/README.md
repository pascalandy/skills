# pele.run snapshot

This folder holds the Markdown that https://pele.run serves for its home page, its documentation, and the examples of each diagram type. The fetch date is 2026-10-17, with pele 1.6.0 on npm and `obsidianmd/pele` main at `659c3593`. The snapshot omits the examples index, because each type's page holds its examples. Links to other pages point at https://pele.run. MIT, see [LICENSE](LICENSE).

To refresh the snapshot, run this script from this folder. It stops at the first failed download, and it replaces `examples/` only after every examples page has arrived.

```bash
bash -euo pipefail <<'EOF'
mkdir -p ~/.cache/pele && pnpm --dir ~/.cache/pele add "pele@$(pnpm view pele version)"
for p in index api compatibility security theming; do curl -fsS "https://pele.run/$p.md" -o "$p.md"; done
rm -rf examples.new && mkdir examples.new
curl -fsS https://pele.run/examples.md | rg -o '\(/examples/[a-z0-9-]+\)' | tr -d '()' | sort -u |
  while read -r p; do curl -fsS "https://pele.run$p.md" -o "examples.new/${p#/examples/}.md"; done
rm -r examples && mv examples.new examples
perl -pi -e 's#\]\(/#](https://pele.run/#g' *.md examples/*.md
uv run ../../scripts/render_diagrams.py *.md examples/*.md
EOF
```

The last command renders every example with the pele that it finds. The refresh is done when these conditions are true:

- The last command answers `{"ok":true,...}`
- Its `pele.version` is the latest version on npm
- This README names that version, the new main commit, and the date

If an examples page is new or removed, update the table in `SKILL.md`.

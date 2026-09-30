## Wiki Map

- Treat the nearest directory containing `INDEX.md` as the wiki boundary and read that index before working
- If the index declares `wiki_type: collection`, use it to select a child and continue until you reach a content wiki; never add pages or `_meta` files at a collection root
- In a content wiki, keep every wiki page under `references/`; reserve the root for `INDEX.md`, optional `AGENTS.md` and `README.md`, and non-Markdown assets
- Follow schema V3: use kebab-case filenames, Obsidian `[[wikilinks]]`, and frontmatter with `name`, `description`, ordered tags, `date_created`, and `date_updated`; preserve `date_created` and bump `date_updated` after content changes
- Order tags as required `area/ea`, `kind/*`, optional `topic/*`, `status/*`, optional `pty/*`; record `sources` for synthesized `kind/project`, `kind/doc`, and `kind/query` pages, and report contradictions instead of replacing claims silently
- Prefer updating an existing page over creating a duplicate; start with a summary, add only useful sections, and end with `## Related` unless the page kind is exempt
- Keep `INDEX.md` aligned with the filesystem and list only direct child wikis in a parent index; preserve the existing structure and ask before changing the schema or topology, or modifying 10 or more pages

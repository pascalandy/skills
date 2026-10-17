# Don't Repeat Yourself (DRY)

Each piece of knowledge → one authoritative place; every other mention points there. Hunt and Thomas (*The Pragmatic Programmer*): knowledge, not lookalike text.

**Why:** Restated fact drifts. Next change updates one copy → others turn false → agents copy false ones forward.

**The pattern:**
- Before writing fact (command, path, setting, number) into doc, spec, or comment → search where it lives: code, config, `--help` output. Point there instead of restating
- Restate only when reader can't reach source, like README install command for reader without clone
- Fact changes anywhere → search old value; update each live copy or replace with pointer, same change. Dated records keep old value; generated copies come from generator
- Code → **Foundational Thinking**, **Laziness Protocol**

**The test:** Change fact in its one place. Any other file now false?

# Don't Repeat Yourself (DRY)

Every piece of knowledge has one authoritative place, and every other mention points to it. Hunt and Thomas named the principle in *The Pragmatic Programmer* for knowledge, not for text that looks alike.

**Why:** A restated fact drifts. The next change updates one copy, the other copies turn false, and agents copy the false ones forward.

**The pattern:**
- Before you write a fact into a doc, spec, or comment, such as a command, path, setting, or number, search for where it already lives, including code, config, and `--help` output. Point there instead of restating it
- Restate a fact only when the reader can't reach its place, such as an install command in a README for someone who hasn't cloned the repo
- When you change a fact anywhere, search for its old value. Update each live copy or replace it with a pointer, in the same change. Dated records keep their old value, and generated copies come from their generator
- In code, follow **Foundational Thinking** and the **Laziness Protocol**

**The test:** Change the fact in its one place. Does any other file now say something false?

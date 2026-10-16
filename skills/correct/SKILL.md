---
name: "correct"
description: "Use only when explicitly invoked as `correct`."
kind: "dev"
---

# Correct

The user keeps correcting agents in this repository for the same mistakes. Change the repository so the next agent can't make them.

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repository so a change that looks right from one file is right for the whole repository.

## 1. Find the mistake classes

Read recent commits, reverts, review comments, agent instruction files, and comments that explain workarounds. Group the mistakes into classes. A class counts once it has happened twice. Done when each class lists two or more past occurrences.

## 2. Pick the level for each class

Fix each class at the strongest level that works, in the order poteto-mode's [Encode Lessons in Structure](../poteto-mode/principles/encode-lessons-in-structure.md) principle gives. Across a repository, the levels apply this way:

- **Architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy
- **Types and lints.** Make the bad state impossible to write. If bad code still compiles, add a lint or check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more
- **Tests.** Fix or delete each test that poteto-mode's [Test Behavior, Not Implementation](../poteto-mode/principles/test-behavior-not-implementation.md) principle rejects
- **Docs or agent rules.** Write them only for judgment calls, since nothing fails when an agent skips them

Done when each class has a level and a reason no stronger level works.

## 3. Fix and prove

Fix the most frequent classes now, one commit each. Prove each new check fails on a real past mistake. Wire each check into the repository's check command, such as `just check`, so it runs before every merge. An exception goes on the offending line with a reason, an expiry date, and a human's approval. Done when each new check fails on its past mistake and passes on the fixed tree.

## 4. Keep the rule table

Keep a table in the repository's `AGENTS.md` that pairs each rule with what enforces it. When the user corrects you, fix the mistake and add the rule. A rule already in the table with nothing enforcing it is a repeat: fix it at the strongest level in the same change. Drop a rule once its mistake can't happen. Done when every rule in the table names its enforcement.

**Reply:** each class with its evidence, the level you picked, and why a stronger level didn't work.

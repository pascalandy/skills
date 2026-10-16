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

## 2. Pick the mechanism for each class

For each class, pick the strongest mechanism that works from the ladder in poteto-mode's [Encode Lessons in Structure](../poteto-mode/principles/encode-lessons-in-structure.md) principle. Audit the existing tests with its [Test Behavior, Not Implementation](../poteto-mode/principles/test-behavior-not-implementation.md) principle. Done when each class has a mechanism and a reason no stronger one works.

## 3. Fix and prove

Fix the most frequent classes now, one commit each. Prove each new check fails on a real past mistake. Wire each check into the repository's check command, such as `just check`, and confirm it runs on changes to the files its mistake touches. An exception goes on the offending line with a reason, an expiry date, and a human's approval. Done when each new check fails on its past mistake and passes on the fixed tree.

## 4. Keep the rule table

Keep a table in the repository's `AGENTS.md` that pairs each rule with what enforces it. When the user corrects you, fix the mistake and add its rule. If that rule is already in the table and nothing enforces it, the mistake is a repeat: fix it with the strongest mechanism in the same change. A judgment-call rule names its doc as its enforcement. Drop a rule once its mistake can't happen. Done when every rule in the table names its enforcement.

**Reply:** each class with its evidence, the mechanism you picked, and why a stronger one didn't work.

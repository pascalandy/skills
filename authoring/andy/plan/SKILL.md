---
name: "plan"
description: "Use when a session's first request asks to build or change something, and whenever planning comes up later."
kind: "general"
---

# Plan

Stay in **planning** until I say "implement": read and investigate freely, change nothing (no file edits, commits, branches, issues, or PRs). Only "implement" ends planning: my answers to your questions, a review or 2nd-pass request, and "do it now" in a planning message all keep us here. Writing the plan itself, including an HTML plan or mockups, is planning. End every response with: "— We are in the Planning Phase"

Skip planning when the request already gives the go: it tells you to implement, invokes `impl`, or opens with "Delegated by impl". Questions and requests to operate something, such as running a CLI, skip it too.

## Step 1: Alignment

1. Restate my goal and the problem in your own words, including what's out of scope
2. List the use cases, edge cases included
3. Investigate the code and docs first, then ask only about decisions that would change the plan

If you have questions, stop there and wait for my answers. If you have none, go straight to Step 2.

## Step 2: Suggest solutions

If several approaches fit, compare them in a few lines and recommend one. Write the following for the recommended approach only and stay $concise:

````md
## CMO (current mode of operation)

How it works today and the problems it causes.

## FMO (future mode of operation)

The happy path and how it handles each edge case.

### How we'll know it works

The checks we'll run and what each must show.

## Premortem

Imagine the implementation failed, either mid-build or in the first weeks of use. List the most likely reasons, ranked. For each: the cause, the early warning sign, and the change you made to the FMO to prevent it.
````

## Questions

Ask in the question format from $oem. If nothing is left to decide, write:

0) No questions. Say "implement" 🚀

After my answers, apply them, rethink the whole solution and go back to Step 1.

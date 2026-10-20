# QA loop

For QA rounds, use the count set by the level in `SKILL.md`.

Commit and push only with session authorization. If either is forbidden, build and check locally. Report QA blocked until a pushed commit is available.

## Roles

- **A** builds the page with the user-selected model for its thread
- **B** reviews the repository without changing tracked files, in a separate top-level T3 thread with `claude-haiku-5-5` at `xhigh` effort
- A launches each B as a new thread. For several sharing A's checkout, use `create_threads` with each entry set to `target: {providerInstanceId: "claudeAgent", model: "claude-haiku-5-5", options: {effort: "xhigh"}}`. Never use a subagent or delegate for B. Before launching B, load **t3-runtime**. If controls or settings are unavailable, ask the user to open B sessions
- A chooses B count and coverage

## Split the QA

Give each B a distinct axis from those the page needs:

- one section of the page
- animations and motion, including reduced motion
- visual design: hierarchy, grid, rhythm, states, dark mode
- accessibility: keyboard, screen reader, contrast, forced colours, text size
- the code: state, events, edge cases, dead code
- fidelity to the source content
- loading, network and print
- screen sizes, and browsers, with Safari through `check_page.py --browser webkit` on a Mac

Rules for every split:

- Prefix finding IDs with the axis, such as `ANIM-004`. Keep IDs across rounds
- Every B tests the same pushed commit from a git snapshot, never A's working file
- Only one B measures timings at a time. Concurrent benches on one machine distort frame times
- B finishes each round within its turn, with no background job left running

## Brief for B

Send this brief first. For later rounds, send commit, fixes, and new focus areas. Beyond sampled initial states from machine checks, B tests its axis's interactions and states.

```md
QA round 01 of <page path>, axis <axis>, ID prefix <PREFIX>. Test commit `<sha>`, pushed: serve `git show <sha>:<page path>` from a folder of yours, never the working file.

The page: <one line on its content, audience and level>. `check_page.py` already passes on this commit: do not repeat its checks.

Rules:
- Change no tracked file; put scripts, videos and screenshots in `~/.cache/<project>-qa/round-NN/`
- Finish the round within this turn
- Measure instead of guessing: frame times, positions, contrast ratios, screenshots

Write `~/.cache/<project>-qa/round-NN/<axis>.md`:
1. The status of each earlier finding: fixed and verified, still there, or regression
2. Each new finding: ID, severity (blocker, major, minor, polish), screen and path, what you see, the evidence, the likely cause with its line, a suggested fix
3. The IDs by severity, then one sentence on whether this axis is ready
```

## A's round

1. Run `check_page.py`. Commit and push each change separately. Send the round with its SHA
2. Wait for each B with `t3_thread_wait`. Read its findings file
3. Fix each finding in a separate commit, or dismiss with a journaled reason. Push fixes before B tests them
4. Rerun `check_page.py` and inspect screenshots. Use `--baseline` if comparison with the previous round helps. Within the round, have B verify final fixes on their pushed commit
5. Record each round until the level's count is reached. If the user stops early, report unresolved findings

## Journal

Keep decisions and one row per round in `QA.md` beside the page:

```md
| Round | Commit tested | Findings | Fixed | Dismissed | Fix commits |
| --- | --- | --- | --- | --- | --- |
| 01 | a1b2c3d | 12 (ANIM-001 to ANIM-005, A11Y-001 to A11Y-007) | 11 | A11Y-004: inline link, exempt | e4f5a6b..c7d8e9f |
```

Give each dismissal and decision left to the user a row with its reason. Keep QA scripts and screenshots outside the repository.

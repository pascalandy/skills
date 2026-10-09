# QA loop

Read when a page goes through QA rounds. The level in `SKILL.md` sets how many rounds run.

Commit and push only when the session authorizes them. If either is forbidden, build and check locally, then report QA blocked until a pushed commit is available. Keep the pushed-commit requirement.

## Roles

- **A** is the agent that builds the page, on the model the user picked for its thread
- **B** is a QA agent: `claude-haiku-5-5` at `xhigh` effort, in its own top-level T3 thread, reading the repository without changing a tracked file
- A launches every B as a new thread: `create_threads` for several at once, sharing A's checkout, each entry with `target: {providerInstanceId: "claudeAgent", model: "claude-haiku-5-5", options: {effort: "xhigh"}}`. B is never a subagent. If those controls or settings are unavailable, ask the user to open the B sessions
- A decides how many B to launch and what each covers

## Split the QA

Give each B a distinct axis. Choose only axes the page needs:

- one section of the page
- animations and motion, including reduced motion
- visual design: hierarchy, grid, rhythm, states, dark mode
- accessibility: keyboard, screen reader, contrast, forced colours, text size
- the code: state, events, edge cases, dead code
- fidelity to the source content
- loading, network and print
- screen sizes, and browsers, with Safari through `check_page.py --browser webkit` on a Mac

Rules for every split:

- Each B prefixes its finding IDs with its axis, such as `ANIM-004`, and keeps an ID from round to round
- Every B tests the same pushed commit, served from a snapshot of git, never the working file A edits
- One B at a time measures timings; two benches on one machine distort frame times
- B finishes its round within its turn and never ends it while a background job runs

## Brief for B

Send it as the thread's first message. Later rounds send the commit, fixes and new focus areas. Machine checks cover sampled initial states; B checks its axis's interactions and states too.

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

1. Run `check_page.py` on the round's page. Commit and push each change separately, then send the round with its SHA
2. Wait for each B with `t3_thread_wait`, then read its findings file
3. Fix each finding in its own commit, or dismiss it with a reason in the journal. Push fixes before B tests them
4. Rerun `check_page.py` and inspect screenshots. Use `--baseline` when comparing with the previous round helps review. Have B verify final fixes on their pushed commit within the round
5. Record the round, then continue until the level's count is reached. Report unresolved findings if the user stops early

## Journal

Keep `QA.md` beside the page, in the project. It holds the decisions and one row per round:

```md
| Round | Commit tested | Findings | Fixed | Dismissed | Fix commits |
| --- | --- | --- | --- | --- | --- |
| 01 | a1b2c3d | 12 (ANIM-001 to ANIM-005, A11Y-001 to A11Y-007) | 11 | A11Y-004: inline link, exempt | e4f5a6b..c7d8e9f |
```

Each dismissal and each decision left to the user gets a row with its reason. QA scripts and screenshots stay outside the repository.

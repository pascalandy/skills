---
description: "Resume or take over another agent's in-flight work from a transcript, a cloud-agent URL, or a pushed branch."
---

### Session pickup

Read [agent runtime](../references/agent-runtime.md) before choosing delegation, models, skill loading, live controls, state storage, or watchers. Follow its capability checks and report unavailable guarantees.

**You own the resume point. Read the prior trail, don't redo it.**

1. Locate the prior trail. Use the harness's project-scoped session history, an explicitly supplied transcript export, a durable checkpoint, an agent/job URL, or a pushed branch. Resolve history through the harness's supported interface; never search unrelated projects' chats. Read the metadata overview and last messages first, then scan back for the decision points. Parse a long transcript in a subagent and keep the reduced timeline in the main thread (the **Guard the Context Window** principle).
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), the open todos, the decisions made. The prior trail records intent and prior decisions; current files, refs, and job state establish present facts. Resist the bias to re-derive it.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not re-run the prior repro or redo completed work. Recheck only claims invalidated by changed artifacts, missing evidence, or the inherited verification requirements.
4. Route the remaining work to the matching playbook and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run. The pickup playbook ends here. The routed playbook owns the rest.
5. Verify the inherited claims against the original goal on the real artifact (the **principle-prove-it-works** skill). A passing prior self-report is not the proof.

**Reply:** where the prior agent stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.

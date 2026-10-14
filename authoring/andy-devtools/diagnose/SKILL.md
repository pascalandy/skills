---
name: "diagnose"
description: "Use for any request to debug, find the root cause, or explain why something fails or got slower: incidents, latency jumps, error spikes, crashes, memory leaks, hangs and timeouts, regressions after a deploy or flag change. Load it before reading code. Also use when a verify-loop run fails, or when a claimed cause, repro, or fix needs checking against facts."
kind: "dev"
---

# Diagnose

Find the cause of a failure from facts, then hand the reading that exposed it to the lane that fixes it.

A **fact** is an observation a tool or a report made, saved with its source. A **hypothesis** is anything you derive from facts, including a repro and someone's claimed cause. Facts constrain hypotheses, and a **control** turns facts into **signals**: readings that differ between the failing case and a case that differs from it in the suspected factor only. Code tells you what can happen, not what did, so read code only to explain a named signal.

The method restates Cindy Sridharan's post [How to effectively debug when you no longer understand the code](https://copyconstruct.medium.com/how-to-effectively-debug-when-you-no-longer-understand-the-code-bd3dcb2c5f7b) in our own words, sharpened by a survey of prior work.

## References

- [glossary.md](references/glossary.md): every term this skill uses, one meaning each. Read when a term is unclear
- [case-file.md](references/case-file.md): the case file template, its column rules, and how to read the matrix by hand. Read at step 0 and before writing any row
- [ladders.md](references/ladders.md): the layers of each stack, from the cheapest to the deepest, with probes and cautions. Read at step 1 and before each descent
- [parity.md](references/parity.md): when two readings agree, the noise floor, normalization, and the launcher environment a repro and a proof run in. Read before comparing a variable with a control, a repro with the field, or a fix with the control
- [principles.md](references/principles.md): the 28 rules the steps come from. Read when a step does not fit the case

## Rules for every path

- **The write rule.** Facts are append-only. Append a fact only for a saved artifact or a quoted report, with its source. Never edit or delete a fact row: when a fact looks wrong, log a `reverify` row, gather it again, and append the new fact with `supersedes`. State no reading you did not gather
- **Absences need coverage.** "No logs" counts against a hypothesis only when the logs would have recorded it. Write what the probe could see next to the absence
- **One contradicting fact eliminates.** Lack of support does not. Every elimination cites the fact
- **The requested outcome bounds the work.** For a `diagnosis` request, change no file in the product under diagnosis: list repairs as follow-ups
- **State the claim level** in every reply: `consistent`, `confirmed`, `fixed`, `external`, or `open`, as the glossary defines them. Only the field re-read of step 9 earns `fixed`
- **Review eliminates.** At each checkpoint, call the `interrogate` skill with one reviewer from another model family and the case file as its fact packet. Its verdict is "eliminated by F#" or "survives F1 to Fn, missing ...", never a confirmation. Append what the reviewer proposes as rows with `by: reviewer`. When no reviewer can be launched, log the review as skipped with the reason; never record a review nobody ran

## Pick the path

Record the requested outcome, `diagnosis` or `fix`, then pick:

- **Quick path** when the report's own facts leave one plausible cause, one cheap probe can test that cause's killing prediction, and the bug is not in production. Follow [Quick path](#quick-path)
- **Case file** otherwise, and from the quick path at the first retraction or the moment two hypotheses survive. Follow [Steps](#steps)
- **Resume** when a case file exists for this failure: read it and its artifacts, check each fact against its artifact, and continue at the step its Log reached

## Steps

Copy this checklist and track your progress:

```
Diagnosis progress:
- [ ] Step 0: Open the case
- [ ] Step 1: Gather layer 1
- [ ] Step 2: Choose the control and pair
- [ ] Step 3: Hypothesize from signals
- [ ] Step 4: Judge and steer
- [ ] Step 5: Validate
- [ ] Step 6: When stuck (repair, then descend)
- [ ] Step 7: Decide
- [ ] Step 8: Hand the fix to the lane (fix requests only)
- [ ] Step 9: Close with the field re-read
```

**Step 0: Open the case.** Cases live in the folder that `echo "${XDG_STATE_HOME:-$HOME/.local/state}/diagnose-cases"` prints; run it and use that path, even when another path looks more usual. Create `<repo>/<YYYY-MM-DD>-<slug>/case.md` there from the template in [case-file.md](references/case-file.md), with raw artifacts in `artifacts/` beside it. `<repo>` is the name of the repository under diagnosis. The case stays out of git. Write the variable precisely: which hosts, users, versions, and time window fail. Read the project's verify loop, the `verify-<app>` skill its `AGENTS.md` names, for the touched features' readings and the last good run, and read past cases under `diagnose-cases/<repo>/`. Open no source file yet. Done when the header is filled.

**Step 1: Gather layer 1.** Append every fact the report carries. Run the cheap exclusions first: the deployed build is the one you think, flags and config match between variable and control, the time windows line up, no resource is exhausted, no upstream dependency changed. Then read raw telemetry, config, flags, and the list of changes between the last good and first bad version, such as `git log --stat`; their code waits for step 3. Fan out across sources and across failing instances. Read Pascal's machines through the `fleet` skill with read-only probes; they need no approval. When the report gives repro steps, record the failing launcher's environment as [parity.md](references/parity.md) says and run them in it now: the repro becomes a hypothesis, and its readings are `lab` facts. Done when every source the report names is read or recorded as unavailable.

**Step 2: Choose the control and pair.** Prefer a standing control, such as the verify loop's last good run. Otherwise take the case that differs by the suspected factor only: the flag off, the last good version, an unaffected cohort. A louder failure that fails differently, already in the data, is often the cheapest good control. Fill the three control columns, including why the control is not broken the same way. Read the same quantities on the control, as counts rather than presence, on every control instance you named, and count differences in both directions: a reply the control gets and the variable never gets is a signal. Read a second control when readings vary, to measure the noise floor. When failing instances disagree, cluster them and run one matrix per cluster. Then call `interrogate` on the control. Done when every fact has a kind and at least one signal exists, or the next step is a descent.

**Step 3: Hypothesize from signals.** Each hypothesis cites the facts it starts from and the prediction that would kill it. Now read code, scoped to a signal: "which paths at the deployed version could produce F6", not "how does the client work". Keep three to seven live hypotheses, plus the `H0` reservation. Put the tempting suspects on the slate so a fact eliminates each one: every change in the diff between last good and first bad, the cause a past postmortem or the report itself names, and one cause outside the component you suspect. Done when every signal and symptom is explained by a hypothesis or marked unexplained.

**Step 4: Judge and steer.** Mark every live hypothesis against every in-scope signal and symptom, with a reason. Count each signal's strength by hand, as [case-file.md](references/case-file.md) shows. A strong signal, explained by one or two hypotheses: discriminate between them. All signals weak: descend. Before each discrimination probe, write in the Log what each live hypothesis predicts, and skip the probe when the predictions all agree. Then call `interrogate` on the matrix. Done when the case file's next step is `validate`, `discriminate`, `tactics`, or `descend`.

**Step 5: Validate.** For the candidate, test its killing prediction. Where it is safe, toggle the suspected cause and watch the strong signal move. Judge the candidate against every in-scope fact, noise and context included. Check repro parity as [parity.md](references/parity.md) says. For a combination, remove each member in turn and name the fact it leaves unexplained. Gather the one to three facts the conclusion rests on again, by an independent path. Then call `interrogate` on the validation. Done when the candidate survives every in-scope fact and the review, and its claim level is written.

**Step 6: When stuck.** When no candidate survives, repair the hypotheses in this order, logging each tactic: reverify the facts, split a coarse hypothesis, merge per-instance ones, combine complementary ones, and only then draw a new one from existing facts. When every signal is weak or the tactics fail, descend one layer down the ladder and pair the new readings with the same control. Process captures run through poteto-mode's `runtime-forensics` or `trace-forensics` playbooks, or the `diagnose-crash` skill for a core dump, each returning facts. After a retraction, hypothesize again in a fresh context, such as a subagent given only `case.md`. After three failed fixes, attack the premise. Stop with claim level `open`, naming the missing observation, when the deepest reachable layer is read, no valid control can be had, access is refused, the case's budget is spent, or two descents in a row bring no new signal. Done when a candidate exists or the case is `open`.

**Step 7: Decide.** List the fix options with their tradeoffs and a recommended default. When the repair stays inside the agreed work, take the recommended option and say why. Otherwise ask Pascal one question; in a brigade round, it goes through the Chef. Rollback, escalation, and dropping support stay Pascal's calls. When the cause sits in a component Pascal does not own, draft the owner's bug report, every claim citing a fact and its artifact, and send nothing. A `diagnosis` request stops here, with the decision as a recommendation. Done when a Decisions row exists.

**Step 8: Hand the fix to the lane.** For a `fix` request only. The confirmed cause enters the lane carrying the reading that exposed it and its normal value. When the project's `AGENTS.md` names a verify loop, start the lane at `maintain-verification-skill`, which records the reading. Otherwise make the fix, run the project's checks, and read the exposing reading on the unfixed code and on the fix, on the same test surface: that pair is the fix's pre-merge proof. Sweep the code for other instances of the same pattern. Done when the pre-merge proof is in the case file.

**Step 9: Close with the field re-read.** After the merge and the deploy, read the reading that exposed the bug where the bug was seen; for a failure the verify loop caught, that place is the verify loop on the same machine. Claim `fixed` only when that reading matches the control, the reported symptom is gone, and a residual check finds no other failing instance. Before the merge, say what this re-read must show and leave the claim below `fixed`. Then hand the case to the retros with its Interventions. Done when the Close section holds the re-read or the reason the case stays open.

## Quick path

It keeps the method and drops the bookkeeping: no case file and no slate of hypotheses. In the reply, keep the control, the probe and its result, the fix's parity reading for a fix request, and the claim level. When a quick-path fix enters the lane, write its evidence into a case file for the handoff and the field re-read, without a second intake.

## Reply

Lead with the cause and its claim level. Then give the control and why it is fair, the signal with both readings and their sources, each eliminated hypothesis with the fact that killed it, the reading that exposed the bug and its normal value, as the check every future verify-loop run keeps, the fix options with their tradeoffs and the one you took or recommend, what the field re-read must show, and the case file path. For an `open` case, name the observation that would move it.

Every reading in the reply names where it came from: the probe or command, each host, bundle, or file it was read on, and the line when there is one. A reading stated for several hosts or bundles was read on each of them; otherwise name the ones it was read on. Take a line number from a read of that one file, such as `grep -n` or `nl <file>`, never from a listing of several files. A number you computed, from readings, code, or config, such as a projection or a share, is labeled as derived and shows its inputs. A number nobody measured stays out.

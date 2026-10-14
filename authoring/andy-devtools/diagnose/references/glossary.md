# Glossary

One term per concept. Use these words and no synonyms for them.

| Term | Meaning |
|---|---|
| case | One investigation of one reported failure, recorded in one case file |
| variable | The failing case, scoped: which hosts, users, versions, and time window |
| control | A case compared with the variable. Types: `happy` (works), `sad` (fails differently and louder), `baseline` (the last good version, or the verify loop's last good run) |
| noise floor | The spread between two readings of the same control |
| fact | An observation with its source and a saved artifact. Append-only for the agent |
| field, lab | Where a fact came from: the real failing environment, or a repro or harness. A lab fact never outranks a field fact |
| fact kind | `signal`: differs between variable and control, in either direction, beyond the noise floor. `noise`: the same on both. `symptom`: seen on the variable, no control reading yet. `context`: a condition such as a version, flag, or scale |
| coverage | For an absence, what the probe could have seen. An absence without coverage cannot contradict a hypothesis |
| layer, ladder | One level of a stack, and the ordered list of levels from the cheapest (the report, logs) to the deepest (kernel tables) |
| probe | A command that reads one layer and saves its output as an artifact |
| reading | A named, countable value read from the system. A feature's readings are the ones it records on every verify-loop run |
| normal value | The value a reading has on a working build, taken from config where possible, otherwise from the last good run |
| invariant | A reading whose normal value is zero violations, enforced loudly in code |
| detector | An outcome such as success rate or latency. It shows that something failed, not where |
| verify loop | A project's `verify-<app>` skill. It drives the real app, records each feature's readings, and compares them with the last good run |
| last good run | The last passing verify-loop run of the base branch on the same machine, pinned. A failed, incomplete, or planted run never becomes the baseline |
| planted bug | The bug a check must catch, put in on purpose. For a fix, it is the unfixed code |
| hypothesis | A derived claim of cause: mechanism, starting facts, and the prediction that would kill it. Status `live` or `replaced`; elimination is derived from judgments |
| `H0` | The "none of these" reservation. Never marked, never counted, never a candidate. It limits every claim to the hypotheses listed |
| mark | One cell of the matrix. `+`: if the hypothesis is true, it produces this fact. `0`: compatible with the fact, but does not produce it alone. `x`: if the hypothesis were true, this fact could not have been observed, whatever other cause is added. Every `x` cites the fact. Blank: not judged yet |
| in scope | The facts a candidate must answer to: field facts of the variable, or of its cluster, plus lab facts from repros that passed parity. Facts from a rejected repro stay in the file, out of scope |
| strength | For an in-scope signal or symptom, the number of live hypotheses marked `+`, counting a combination and its members once. Strong is 1 or 2 |
| candidate | A live hypothesis marked `+` on every in-scope signal and symptom and `x` on no in-scope fact |
| combination | Hypotheses that together are a candidate, where removing any member leaves an in-scope fact unexplained. It is `x` where any member is `x`, since an `x` holds whatever cause is added. Its other marks are judged from what the members produce together, not from their own marks: two members that are each `0` on a fact can together be `+`. A member may carry a role: `trigger`, `sustaining`, or `vulnerability` |
| repair tactic | One of the five moves when no candidate exists: reverify, split, merge, combine, new from facts |
| descend | Gather facts one layer down, paired with the same control |
| repro | A hypothesis of the form "this setup produces the reported failure" |
| parity | Two readings agree under a stated rule. Repro parity, fix parity, and the verify loop's comparison with the last good run use the same rules |
| reviewer | An independent read-only agent that `interrogate` launches. It may only propose an elimination or flag a defect in the facts |
| fact packet | What a reviewer gets in place of a diff: facts and their artifacts, such as a case file, without the author's story |
| requested outcome | Set at intake: `diagnosis` (read-only questions, audits of a claim) or `fix` |
| intervention | Any human input that changed the course of a case |

## Claim levels

| Level | Holds when |
|---|---|
| `consistent` | A candidate survives every in-scope fact gathered, among the hypotheses listed |
| `confirmed` | It also passed a test no other live hypothesis passes, such as toggling the suspected cause and watching the strong signal move, or a directly observed causal chain |
| `fixed` | After the merge, where the bug was seen, the reading that exposed it matches the control, the reported symptom is gone, and a residual check finds no other failing instance or signal. Before the merge, a fix has only its pre-merge proof |
| `external` | The cause is in a component Pascal does not own |
| `open` | Stopped, naming the next observation needed |

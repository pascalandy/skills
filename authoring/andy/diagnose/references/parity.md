# Parity

Two readings are at parity when they agree under a stated rule. Repro parity, fix parity, and the verify loop's comparison with the last good run all use the rules below. Write the rule you applied in the Log row of each comparison.

## Before any comparison

- Confirm each reading came from the build you think: the version line, commit, flag values, and host in its artifact. A reading from the wrong build is the most common gathering defect; it is reverified, never edited
- Read both sides the same way: the same probe, the same window length, the same load class

## Noise floor

- Read the control twice, or two control instances, before calling a difference a signal
- A count, such as rows written or frames on a stack, differs when the two values differ and the control readings agree with each other
- A timing or size differs only beyond the spread of the control readings. Name both control values in the fact row
- A reading that matches on variable and control is `noise`, however alarming it looks. An error present on both sides does not explain the difference between them

## Normalization

Before comparing text, scrub what varies between any two runs: timestamps, PIDs, thread ids, ports, request ids, temporary paths, hostnames, and memory addresses. For stacks and heap profiles, compare the top five function names without line numbers or addresses; compare file and line too when both readings come from the same build.

## Repro parity

A repro passes when it shows the report's strongest signal, not only its symptom. A 500, a non-zero exit, or a late job is a symptom many causes share.

- Pick the strongest field signal: the reading fewest hypotheses explain
- Record how the failing run was started: its launcher, such as a scheduler, a service manager, or a terminal, and the shell, `PATH`, environment variables, and tool versions that launcher resolved. Run the repro and the fix's proof in that environment, or name each difference in the Log row
- Read that signal on the repro the same way it was read in the field
- At parity, the repro's lab facts come into scope
- Off parity, the repro may be real but is not this bug. Its facts stay in the file, out of scope, and the repro hypothesis gets `x` citing the mismatch

## Fix parity

A fix passes when the reading that exposed the bug, read on the same surface the same way and in the failing launcher's environment, moves from the variable's value to the control's value, while every other reading stays at parity. Passing tests are necessary, not sufficient. Before the merge, read it on the unfixed code and on the fix, on the agreed test surface. After the merge, read it where the bug was seen: only that field re-read earns `fixed`.

## The verify loop

Each reading in a feature's file is compared with the last good run. A run fails when a reading is missing, a detector fails, or a reading leaves parity. A change meant to move a reading updates that reading's normal value in the feature's file, so parity still covers every other reading.

# CU1. Rounds in one MAIN

Pascal runs successive rounds in one MAIN. Each round implements one card with one COD, runs the reviews one at a time, and ends on the merge and the retros. The example runs two rounds: round 1 removes personal data from skill-xyz, and round 2, summarized, moves skill-xyz from skills-private to skills.

## Process

MAIN runs each step in order and launches each thread with `main-launch`.

| # | Step | Threads | SOP |
|---|---|---|---|
| 1 | Align | MAIN, Pascal | Before `$s3`: MAIN and Pascal agree on the plan |
| 2 | Implement | COD<n> | `cod-implement` |
| 3 | Adverse review | ADV<n>, then MAIN | `rev-adverse`, `main-triage` |
| 4 | Blast-radius review | BLAST<n>, then MAIN | `rev-blast-radius`, `main-triage` |
| 5 | Pristine review | PRIS<n>, then MAIN | `rev-pristine`, `main-triage` |
| 6 | Docs updates | DOC<n> | `doc-update` |
| 7 | Closing | MAIN, COD<n> | `main-closing` |

Fast track skips steps 3 to 5.

## Diagram

Each step opens with a banner that holds its step name from the process table.

- Every message said in a chat starts with `USER:` or `Agent:`
- A marker ends each message: `->` to the right, `<-` to the left, `(internal)` for a thread's own action
- "Settle" has no prefix, since it is a T3 action and not a message
- The first banner holds the CU title

```mermaid
sequenceDiagram
    accDescr: Pascal talks only to MAIN. In each round, MAIN launches a COD, then one reviewer at a time, triages each report, launches DOC, and relays the merge and the retros
    autonumber
    actor U as USER
    participant M as 👑 MAIN <id4> [subject]

    Note over U,M: CU1. Rounds in one MAIN<br>Round 1. Align
    U->>M: USER: New thread in projects.<br>PROMPT: Remove personal data from skill-xyz ->
    loop Align
        M->>U: Agent: Here is the plan <-
        U->>M: USER: Q&A ->
    end
    U->>M: USER: Let's go! $s3 ->
    M->>M: Rename itself 👑 MAIN <id4> [subject] (internal)

    Note over U,M: Implement
    create participant C1 as 🐝 COD1 <id4>
    M->>C1: Agent: $s3 #59; cod-implement, the card ->
    M->>U: Agent: Link to COD1 <-
    C1->>C1: Worktree, implement, PR P1, 2nd-pass (internal)
    C1-->>M: Agent: P1 ready <-

    Note over U,M: Adverse review
    create participant A1 as 👀 ADV1 <id4>
    M->>A1: Agent: $s3 #59; rev-adverse, P1 ->
    A1->>A1: Review P1, 2nd-pass on the report (internal)
    A1-->>M: Agent: Findings <-
    M->>M: Accept or reject each finding (internal)
    M->>C1: Agent: Fix the accepted findings ->
    C1->>C1: Fix, push, 2nd-pass (internal)
    C1-->>M: Agent: Fixed and pushed <-

    Note over U,M: Blast-radius review
    create participant B1 as 👀 BLAST1 <id4>
    M->>B1: Agent: $s3 #59; rev-blast-radius, P1 ->
    M->>M: Write its own premortem (internal)
    B1-->>M: Agent: Findings <-
    M->>M: Accept or reject each finding (internal)
    M->>C1: Agent: Fix the accepted findings ->
    C1-->>M: Agent: Fixed and pushed <-

    Note over U,M: Pristine review
    create participant R1 as 👀 PRIS1 <id4>
    M->>R1: Agent: $s3 #59; rev-pristine, P1 ->
    R1-->>M: Agent: Findings <-
    M->>M: Accept or reject each finding, end the reviews (internal)
    M->>C1: Agent: Fix the accepted findings ->
    C1-->>M: Agent: Fixed and pushed <-

    Note over U,M: Docs updates
    create participant D1 as 📚 DOC1 <id4>
    M->>D1: Agent: $s3 #59; doc-update, COD1's worktree ->
    D1->>D1: Update the docs, docs PR at the top of the stack, 2nd-pass (internal)
    D1-->>M: Agent: Docs PR ready <-

    Note over U,M: Closing
    M->>U: Agent: Report, PR links, confidence to merge. Merge? <-
    U->>M: USER: Merge ->
    M->>C1: Agent: Merge ->
    C1->>C1: Merge the stack, remove its worktree (internal)
    C1-->>M: Agent: Merged <-
    M->>C1: Agent: Run your retros ->
    M->>M: Run its own retros (internal)
    C1-->>M: Agent: Retro issues filed <-
    destroy A1
    M->>A1: Settle ADV1 ->
    destroy B1
    M->>B1: Settle BLAST1 ->
    destroy R1
    M->>R1: Settle PRIS1 ->
    destroy D1
    M->>D1: Settle DOC1 ->
    destroy C1
    M->>C1: Settle COD1 ->
    M->>U: Agent: ⛳ Implemented. Round 1 done <-

    Note over U,M: Round 2, summarized. Move skill-xyz to skills
    U->>M: USER: PROMPT: Move skill-xyz from skills-private to skills (public) ->
    loop Align
        M->>U: Agent: Here is the plan.<br>PR A adds it to skills, PR B removes it from skills-private <-
        U->>M: USER: Q&A ->
    end
    U->>M: USER: Let's go! $s3 ->
    create participant C2 as 🐝 COD2 <id4>
    M->>C2: Agent: $s3 #59; cod-implement, the card ->
    C2-->>M: Agent: PR A and PR B ready <-
    Note over M,C2: ADV2, BLAST2, PRIS2, and DOC2 run as in round 1
    M->>U: Agent: Report. Merge B, then A. Merge? <-
    U->>M: USER: Merge ->
    M->>C2: Agent: Merge, then run your retros ->
    C2-->>M: Agent: Merged, retro issues filed <-
    destroy C2
    M->>C2: Settle COD2 and its round's threads ->
    M->>U: Agent: ⛳ Implemented. Round 2 done <-
    Note over U,M: USER starts another round or settles MAIN
```

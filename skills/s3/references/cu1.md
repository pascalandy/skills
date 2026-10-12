# CU1. Rounds in one MAIN

Pascal runs successive rounds in one MAIN. Each round implements one card with one COD, runs the reviews one at a time, and ends on the merge and the retros. The example runs two rounds: round 1 removes personal data from skill-xyz, and round 2, summarized, hands another issue to a second COD.

## Process

MAIN runs each step in order and launches each thread with `main-launch`.

| # | Step | Threads | SOP |
|---|---|---|---|
| 1 | Align | MAIN, Pascal | Before `$s3`: MAIN and Pascal agree on the plan |
| 2 | Implement | COD<n> | `cod-implement` |
| 3 | Adverse review | ADV<n>, then MAIN | `rev-adverse`, `main-triage` |
| 4 | Blast-radius review | BLAST<n>, then MAIN | `rev-blast-radius`, `main-triage` |
| 5 | Docs updates | DOC<n> | `doc-update` |
| 6 | Docs review | RDOC<n>, then MAIN | `rev-docs`, `main-triage` |
| 7 | Pristine review | PRIS<n>, then MAIN | `rev-pristine`, `main-triage` |
| 8 | Closing | MAIN, COD<n>, DOC<n> | `main-closing` |

Fast track skips steps 3, 4, 6, and 7.

## Diagram

Each step opens with a banner that holds its step name from the process table.

- Every message said in a chat starts with `USER:` or `Agent:`
- A marker ends each message: `->` to the right, `<-` to the left. A thread's own action is an arrow back to itself, with no marker
- "Settle" has no prefix, since it is a T3 action and not a message
- The first banner holds the CU title
- `PR 35` and `PR 36` are example PR numbers
- The Mermaid source writes `;` as `#59;`, since Mermaid reads it as the end of a statement, and uses no `#`, which starts a comment

```mermaid
sequenceDiagram
    accDescr: Pascal talks only to MAIN. In each round, MAIN launches a COD, then each reviewer and DOC one at a time, triages each report, settles each reviewer once its review ends, merges, and runs the retros
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
    M->>M: Rename itself 👑 MAIN <id4> [subject]

    Note over U,M: Implement
    create participant C1 as 🐝 COD1 <id4>
    M->>C1: Agent: $s3 #59; cod-implement spec/issue ->
    M->>U: Agent: Link to COD1 <-
    C1->>C1: Worktree, implement PR 35, then 2nd-pass
    C1-->>M: Agent: PR 35 ready <-

    Note over U,M: Adverse review
    create participant A1 as 👀 ADV1 <id4>
    M->>A1: Agent: $s3 #59; rev-adverse PR 35 ->
    loop Up to 3 passes
        A1->>A1: Review PR 35, then 2nd-pass on the report
        A1-->>M: Agent: Findings <-
        M->>M: Accept or reject each finding
        M->>C1: Agent: Fix the accepted findings ->
        C1->>C1: Fix, push, then 2nd-pass
        C1-->>M: Agent: Fixed and pushed <-
        opt The fixes need a fresh look
            M->>A1: Agent: Rerun on the new heads, with prior findings ->
        end
    end
    destroy A1
    M->>A1: Settle ADV1 ->

    Note over U,M: Blast-radius review
    create participant B1 as 👀 BLAST1 <id4>
    M->>B1: Agent: $s3 #59; rev-blast-radius, PR 35 ->
    M->>M: Write its own premortem
    loop Up to 3 passes
        B1-->>M: Agent: Findings <-
        M->>M: Accept or reject each finding
        M->>C1: Agent: Fix the accepted findings ->
        C1-->>M: Agent: Fixed and pushed <-
        opt The fixes need a fresh look
            M->>B1: Agent: Rerun on the new heads, with prior findings ->
        end
    end
    destroy B1
    M->>B1: Settle BLAST1 ->

    Note over U,M: Docs updates
    create participant D1 as 📚 DOC1 <id4>
    M->>D1: Agent: $s3 #59; doc-update, COD1's worktree ->
    D1->>D1: Update the docs, PR 36 at the top of the stack, then 2nd-pass
    D1-->>M: Agent: PR 36 ready <-

    Note over U,M: Docs review
    create participant E1 as 👀 RDOC1 <id4>
    M->>E1: Agent: $s3 #59; rev-docs, PR 36 ->
    loop Up to 3 passes
        E1-->>M: Agent: Findings <-
        M->>M: Accept or reject each finding
        M->>D1: Agent: Fix the accepted findings ->
        D1-->>M: Agent: Fixed and pushed <-
        opt The fixes need a fresh look
            M->>E1: Agent: Rerun on the new heads, with prior findings ->
        end
    end
    destroy E1
    M->>E1: Settle RDOC1 ->

    Note over U,M: Pristine review
    create participant R1 as 👀 PRIS1 <id4>
    M->>R1: Agent: $s3 #59; rev-pristine, PR 35 and PR 36 ->
    loop Up to 3 passes
        R1-->>M: Agent: Findings <-
        M->>M: Accept or reject each finding
        M->>C1: Agent: Fix the accepted findings, to each layer's owner ->
        C1-->>M: Agent: Fixed and pushed <-
        opt The fixes need a fresh look
            M->>R1: Agent: Rerun on the new heads, with prior findings ->
        end
    end
    destroy R1
    M->>R1: Settle PRIS1 ->

    Note over U,M: Closing
    M->>U: Agent: Report, PR links, confidence to merge. Merge? <-
    U->>M: USER: Merge ->
    M->>M: Merge the stack, remove the worktrees
    M->>C1: Agent: Merged. Run your two retros, skill usage then global ->
    par COD1
        C1->>C1: retro-skill-usage, then retro-global, file the issues
    and MAIN
        M->>M: retro-skill-usage, then retro-global, file the issues
    end
    C1-->>M: Agent: Retro issues filed <-
    destroy D1
    M->>D1: Settle DOC1 ->
    destroy C1
    M->>C1: Settle COD1 ->
    M->>U: Agent: ⛳ Implemented. Round 1 done <-

    Note over U,M: Round 2, summarized
    U->>M: USER: PROMPT: Another issue ->
    Note over U,M: Align as in round 1, until USER says Let's go! $s3
    create participant C2 as 🐝 COD2 <id4>
    M->>C2: Agent: $s3 #59; cod-implement, the new issue ->
    Note over M,C2: Steps 2 to 8 run as for COD1 in round 1
    destroy C2
    M->>C2: Settle COD2 ->
    M->>U: Agent: ⛳ Implemented. Round 2 done <-
    Note over U,M: USER starts another round or settles MAIN
```

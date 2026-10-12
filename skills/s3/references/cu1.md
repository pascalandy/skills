# CU1. Rounds in one MAIN

Pascal runs successive rounds in one MAIN. Each round implements one card with one COD, runs the reviews one at a time, and ends on the merge and the retros. The example runs two rounds: round 1 removes personal data from skill-xyz, and round 2, summarized, hands another issue to a second COD.

## Process

MAIN runs each step in order and launches each thread with `main-launch`.

| # | Step | Threads | SOP |
|---|---|---|---|
| 0 | Align | MAIN, Pascal | Before `$s3`: MAIN and Pascal agree on the plan |
| 1 | Implement | COD<n> | `cod-implement` |
| 2 | Adversarial review | ADV<n>, then MAIN | `rev-adverse`, `main-triage` |
| 3 | Blast-radius review | BLAST<n>, then MAIN | `rev-blast-radius`, `main-triage` |
| 4 | Docs updates | DOC<n> | `doc-update` |
| 5 | Docs review | RDOC<n>, then MAIN | `rev-docs`, `main-triage` |
| 6 | Pristine review | PRIS<n>, then MAIN | `rev-pristine`, `main-triage` |
| 7 | Closing | MAIN, COD<n> | `main-closing` |

Fast track skips each step whose role sets `skip-in-fast-track` in `config.toml`.

## Diagram

Each step opens with a banner that holds its number and name from the process table, such as `Step 1: Implement`.

- Every message said in a chat starts with `USER:` or `Agent:`
- A marker ends each message: `->` to the right, `<-` to the left. A thread's own action is an arrow back to itself, with no marker
- "Settle" has no prefix, since it is a T3 action and not a message
- The first banner holds the CU title
- Blue boxes are loops, green boxes run in parallel, and orange boxes are alternatives
- `PR 35` and `PR 36` are example PR numbers
- The Mermaid source writes `;` as `#59;`, since Mermaid reads it as the end of a statement, and uses no `#`, which starts a comment

```mermaid
sequenceDiagram
    accDescr: Pascal talks only to MAIN. In each round, MAIN launches a COD, then each reviewer and DOC one at a time, triages each report, settles each reviewer once its review ends, merges, and runs the retros
    autonumber
    actor U as USER
    participant M as 👑 MAIN <id4> [subject]

    Note over U,M: CU1. Rounds in one MAIN<br>Round 1. Step 0: Align
    U->>M: USER: New thread in projects.<br>PROMPT: Remove personal data from skill-xyz ->
    rect rgba(140, 170, 238, 0.18)
        loop Align
            M->>U: Agent: Here is the plan <-
            U->>M: USER: Q&A ->
        end
    end
    U->>M: USER: Let's go! $s3 ->
    M->>M: Rename itself 👑 MAIN <id4> [subject]

    Note over U,M: Step 1: Implement
    create participant C1 as 🐝 COD1 <id4>
    M->>C1: Agent: $s3 #59; cod-implement spec/issue ->
    M->>U: Agent: Link to COD1 <-
    C1->>C1: Worktree, implement PR 35, then 2nd-pass
    C1-->>M: Agent: PR 35 ready <-

    Note over U,M: Step 2: Adversarial review
    create participant A1 as 👀 ADV1 <id4>
    M->>A1: Agent: $s3 #59; rev-adverse PR 35 ->
    rect rgba(140, 170, 238, 0.18)
        loop Up to max-passes
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
    end
    destroy A1
    M->>A1: Settle ADV1 ->

    Note over U,M: Step 3: Blast-radius review
    create participant B1 as 👀 BLAST1 <id4>
    M->>B1: Agent: $s3 #59; rev-blast-radius, PR 35 ->
    M->>M: Write its own premortem
    rect rgba(140, 170, 238, 0.18)
        loop Up to max-passes
            B1-->>M: Agent: Findings <-
            M->>M: Accept or reject each finding
            M->>C1: Agent: Fix the accepted findings ->
            C1-->>M: Agent: Fixed and pushed <-
            opt The fixes need a fresh look
                M->>B1: Agent: Rerun on the new heads, with prior findings ->
            end
        end
    end
    destroy B1
    M->>B1: Settle BLAST1 ->

    Note over U,M: Step 4: Docs updates
    create participant D1 as 📚 DOC1 <id4>
    M->>D1: Agent: $s3 #59; doc-update, COD1's worktree ->
    D1->>D1: Update the docs, PR 36 at the top of the stack, then 2nd-pass
    D1-->>M: Agent: PR 36 ready <-

    Note over U,M: Step 5: Docs review
    create participant E1 as 👀 RDOC1 <id4>
    M->>E1: Agent: $s3 #59; rev-docs, PR 36 ->
    rect rgba(140, 170, 238, 0.18)
        loop Up to max-passes
            E1-->>M: Agent: Findings <-
            M->>M: Accept or reject each finding
            M->>D1: Agent: Fix the accepted findings ->
            D1-->>M: Agent: Fixed and pushed <-
            opt The fixes need a fresh look
                M->>E1: Agent: Rerun on the new heads, with prior findings ->
            end
        end
    end
    destroy E1
    M->>E1: Settle RDOC1 ->

    Note over U,M: Step 6: Pristine review
    create participant R1 as 👀 PRIS1 <id4>
    M->>R1: Agent: $s3 #59; rev-pristine, PR 35 and PR 36 ->
    rect rgba(140, 170, 238, 0.18)
        loop Up to max-passes
            R1-->>M: Agent: Findings <-
            M->>M: Accept or reject each finding
            M->>C1: Agent: Fix the accepted findings, to each layer's owner ->
            C1-->>M: Agent: Fixed and pushed <-
            opt The fixes need a fresh look
                M->>R1: Agent: Rerun on the new heads, with prior findings ->
            end
        end
    end
    destroy R1
    M->>R1: Settle PRIS1 ->
    destroy D1
    M->>D1: Settle DOC1 ->

    Note over U,M: Step 7: Closing
    M->>U: Agent: Report, PR links, confidence to merge <-
    rect rgba(239, 159, 118, 0.2)
        alt Confident
            M->>M: Merge the stack, remove the worktrees
        else Hesitant
            rect rgba(140, 170, 238, 0.18)
                loop Align
                    M->>U: Agent: Questions <-
                    U->>M: USER: Answers ->
                end
            end
            U->>M: USER: Merge ->
            M->>M: Merge the stack, remove the worktrees
        end
    end
    M->>C1: Agent: Merged. Run your two retros, skill usage then global ->
    rect rgba(166, 209, 137, 0.25)
        par COD1
            C1->>C1: retro-skill-usage, then retro-global, file the issues
        and MAIN
            M->>M: retro-skill-usage, then retro-global, file the issues
        end
    end
    C1-->>M: Agent: Retro issues filed <-
    destroy C1
    M->>C1: Settle COD1 ->
    M->>U: Agent: ⛳ Implemented. Round 1 done <-

    Note over U,M: Round 2, summarized
    U->>M: USER: PROMPT: Another issue ->
    Note over U,M: Align as in round 1, until USER says Let's go! $s3
    create participant C2 as 🐝 COD2 <id4>
    M->>C2: Agent: $s3 #59; cod-implement, the new issue ->
    Note over M,C2: Steps 1 to 7 run as for COD1 in round 1
    destroy C2
    M->>C2: Settle COD2 ->
    M->>U: Agent: ⛳ Implemented. Round 2 done <-
    Note over U,M: USER starts another round or settles MAIN
```

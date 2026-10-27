# CU1. Batches under one Head Chef

For Pascal designing the route in VS Code. This illustrative sequence shows who owns each handoff: the Cook owns reviews and watches; the Chef owns validation and merging.

A CU is a use case showing the process between Pascal and the threads. When an SOP step changes, update the process table in `carpaccio.md` and this diagram wherever they show that step. When a status rule changes, change [the status model](../../references/model.py) with it: `just check` runs the model on any change to brigade-mode. Agents executing SOPs do not read this file.

## Conventions

Each step starts with its number and name. Chat messages start with `USER:` or `Agent:` and end with `->` or `<-` for their direction. Self-arrows show local actions and delegate calls; barrages are absent from the sidebar, so they have no participant. Settle is a T3 action. Blue boxes show loops, green boxes parallel work and orange boxes alternatives. `PR 35` and `PR 36` are examples. In sequence labels, including message and note text, write `;` as `#59;` and `#` as `#35;`. A bare `;` ends the statement, and a bare `#` drops the remaining text without an error.

## Sequence

```mermaid
%%{init: {"sequence": {"diagramMarginX": 100}}}%%
sequenceDiagram
    accTitle: CU1 Statuses and Watchdogs
    accDescr: The Head Chef alone asks Pascal. Parent Watchdogs wake stalled children or report faults. Chefs validate, merge, release and close before the Head Chef counts delivery.
    autonumber
    actor U as USER
    participant H as Head Chef
    participant C as Chef 1
    participant K as Cook 1.1
    Note over U,K: CU1. Batches under one Head Chef<br>Step 0: Align
    U->>H: USER: Plan and requirements ->
    H->>U: Agent: Goal, batches with acceptance criteria,<br>choices from Decisions <-
    opt A question the plan leaves open
        H->>U: Agent: 🙋 align, batches that do not wait on it launch <-
        U->>H: USER: Answer ->
    end
    H->>H: Pin, register batches<br>❓ align only for an open question
    H->>H: Arm Head Chef Watchdog<br>Delegate owns its schedule<br>Check its bound thread
    H->>C: Agent: Launch ⏳ Chef with projectId<br>and Align choices ->
    C->>C: Group disjoint files,<br>register Cook slots
    opt Chef has a Cook slot
        C->>C: Arm Chef Watchdog<br>Delegate owns its schedule<br>Check its bound thread
    end
    C->>C: Create Cook worktrees
    opt Open PR outside the run changes a group's files or cited specs
        C-->>H: Agent: ⏸️ Overlap and default <-
        H->>C: Agent: Answer, then launch that group's Cook ->
    end
    C->>K: Agent: Launch 🍳 Cook with ownership ->
    Note over H,K: Watchdogs are hidden delegates, not participants<br>Each tick reads watch and wake files
    opt Cook stalls or fails
        C->>C: Watchdog queues one Cook wake<br>then alerts Chef after max-wakes
        C->>C: Reconcile effects, resume<br>or replace Cook in its slot
    end
    opt Chef stalls or fails
        H->>H: Watchdog queues one Chef wake<br>then alerts Head Chef after max-wakes
        H->>H: Reconcile effects, resume<br>or replace Chef in its slot
    end
    Note over C,K: Parallel per Decisions: up to max-cooks<br>Separate worktrees, serialized merges
    Note over C,K: Step 1: Implement
    opt Bug card
        K->>K: diagnose before reading source
        Note over H,K: Any question for Pascal climbs<br>through Chef and Head Chef
    end
    K->>K: Implement, link PR 35,<br>watch, 2nd-pass and push
    Note over K: Watch findings: queue while passes run,<br>otherwise triage at once
    opt Cross-file ownership
        K-->>C: Agent: ⏸️ Request file access <-
        C->>K: Agent: Ownership decision ->
    end
    Note over C,K: Step 2: manic-1 and manic-2
    rect rgba(166, 209, 137, 0.25)
        par manic-1
            K->>K: Delegate interrogate rejection reviewer
        and manic-2
            K->>K: Delegate interrogate blast-radius<br>and premortem reviewer
        end
    end
    K->>K: End turn, then interrogate lead judgment<br>Other provider, one reviewer per barrage
    Note over C,K: Step 3: Docs
    K->>K: andy-mode docs, PR 36 on top<br>or no-docs decision<br>Release yes: final content layer
    Note over C,K: Step 4: manic-3 and manic-5
    rect rgba(166, 209, 137, 0.25)
        par manic-3
            K->>K: Delegate docs review
        and manic-5
            K->>K: Delegate interrogate polish reviewer
        end
    end
    K->>K: End turn, then interrogate lead judgment
    Note over C,K: Act on: accept#59; Consider: 🍽️ for Chef<br>Noted and Dismissed: reject with reason
    Note over C,K: Both review pairs: fix and rerun within max-passes<br>Last allowed pass with any fix: one final limited pass
    Note over H,K: Step 5: Validation and merge
    K-->>C: Agent: 🍽️ Stack ready, report,<br>branch heads, clean and pushed <-
    K->>K: Freeze, forward watch findings only
    C->>C: Read rejections,<br>check cross-Cook conflicts
    opt Reopened finding, missing criterion evidence,<br>failed or missing required status, or frozen watch finding
        C->>K: Agent: Return worktree for Fix ->
        K->>K: 🍳 Fix, checks and reviews,<br>fresh 🍽️ Stack ready
    end
    rect rgba(239, 159, 118, 0.2)
        alt Every merge gate holds#59; Pareto verdict challenged with sparring
            C-->>H: Agent: 🔀 Batch 1 merging <-
        else A gate fails
            C-->>H: Agent: 🍽️ Batch ready at x/x,<br>or below it only by queued_after_merge slots <-
            alt Requirements or specs settle a question
                H->>C: Agent: Answers from requirements or specs ->
                C-->>H: Agent: Merge rule again: 🔀 Batch 1 merging<br>or a new 🍽️ Batch ready <-
            else Gate still open
                H->>U: Agent: 🙋 merge PR 35–36 URL ? failed gate and recommendation <-
                U->>H: USER: Merge ->
                H->>C: Agent: 🔀 Merge ->
            end
        end
    end
    C->>C: Verify GitHub heads,<br>merge in frozen worktree
    opt Merge fails
        C->>K: Agent: Return worktree, fix cause ->
        K->>K: 🍳 Fix, checks and reviews,<br>fresh 🍽️ Stack ready
    end
    Note over C,K: Next stack: Cook restacks on main<br>Same own diff keeps approval#59; changed diff needs review
    opt After-merge slot waits for this round
        C->>K: Agent: merged, close ->
        C->>C: Confirm merged Cooks settled,<br>worktree from fresh origin/HEAD
        C->>C: Launch 🍳 after-merge Cook<br>Steps 1 to 5 for its stack,<br>merge decision on its own heads
    end
    C->>K: Agent: merged ->
    C-->>H: Agent: Batch merged, deploy result<br>No Head Chef count yet <-
    C->>C: Release yes: finish procedure<br>from main
    Note over H,K: Step 6: Closing
    rect rgba(239, 159, 118, 0.2)
        alt All children closed, no reserve
            C->>C: Close Epic with child proof
        else All closed, body reserves closing for Pascal
            C->>C: Keep Epic open, swap 1-wip-by-agent<br>for 1-ready-for-human
        else A child stays open
            C->>C: Neither, name the open children
        end
    end
    C->>K: Agent: Close, run enabled retros ->
    K->>K: 🧹 Retros, unwatch, report<br>🍽️ final after merge, then settle
    C->>C: Retros, confirm Cooks settled,<br>remove merged worktrees
    C-->>H: Agent: ⛳ Batch delivered, report <-
    opt Chef Watchdog exists
        C->>C: Delete Watchdog schedule<br>cancel task if recorded<br>remove its work folder if present
    end
    C->>C: Remove own work folder<br>settle
    H->>H: Count only delivered batches<br>Next batches, retros, settle Chefs
    H->>H: Read GitHub items waiting on Pascal<br>No Stop: apply decisions, Coordinate added work<br>Stop: report follow-up URLs, add no batch
    H->>U: Agent: ⛳ x/y batches done, report <-
    H->>H: Delete Watchdog schedule<br>cancel task, remove work folders<br>Prune worktree records
    H->>H: Settle and unpin
```

At review, Pascal may instead choose `⏳ Rework`, `🍽️ Hold` or `⏹️ Drop`. Rework returns affected Cooks to 🍳 and may withdraw ❓. Hold keeps the Chef 🍽️; the Head Chef shows `❓ held batch <b>` once no other work can progress. Drop closes the Cook and Chef at ⏹️, and the cut batch leaves the Head Chef's count.

Fast track implements required release content, skips docs and barrages, then uses the same readiness handoff. A batch without PRs runs in the Chef alone, keeps no Chef Watchdog and goes to Closing. On `⏹️ Stop`, the Head Chef tells Chefs, Chefs relay to Cooks, Cooks close at ⏹️ unless their stacks merged, and a merge or release already running finishes before each Chef follows Closing.

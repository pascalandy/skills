# CU1. Batches under one Head Chef

For Pascal designing the route in VS Code. This illustrative sequence shows who owns each handoff: the Cook owns reviews and watches; the Chef owns validation and merging.

A CU is a use case showing the process between Pascal and the threads. When an SOP step changes, update the process table in `carpaccio.md` and this diagram wherever they show that step. Agents executing SOPs do not read this file.

## Conventions

Each step starts with its number and name. Chat messages start with `USER:` or `Agent:` and end with `->` or `<-` for their direction. Self-arrows show local actions and delegate calls; barrages are absent from the sidebar, so they have no participant. Settle is a T3 action. Blue boxes show loops, green boxes parallel work and orange boxes alternatives. `PR 35` and `PR 36` are examples. Write semicolons as `#59;` inside Mermaid labels and omit comment markers inside messages.

## Sequence

```mermaid
%%{init: {"sequence": {"diagramMarginX": 100}}}%%
sequenceDiagram
    accTitle: CU1 Statuses and Cook-owned reviews
    accDescr: The Head Chef alone asks Pascal. Cooks serve frozen stacks; Chefs validate, merge, release and close before the Head Chef counts delivery.
    autonumber
    actor U as USER
    participant H as Head Chef
    participant C as Chef 1
    participant K as Cook 1.1
    Note over U,K: CU1. Batches under one Head Chef<br>Step 0: Align
    rect rgba(140, 170, 238, 0.18)
        loop Until agreement
            U->>H: USER: Plan and requirements ->
            H->>U: Agent: Validate, parallel Cooks,<br>release for each batch? <-
        end
    end
    H->>H: Pin, register batches<br>❓ align → 🟢 working
    H->>C: Agent: Launch ⏳ Chef with projectId<br>and Align choices ->
    C->>C: Group disjoint files,<br>create worktrees
    C->>K: Agent: Launch 🍳 Cook with ownership ->
    Note over C,K: Parallel Cooks yes: up to max-cooks<br>Separate worktrees, serialized merges
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
    K->>K: Freeze, forward watch wakes
    C->>C: Read rejections,<br>check cross-Cook conflicts
    opt Reopened finding or frozen watch finding
        C->>K: Agent: Return worktree for Fix ->
        K->>K: 🍳 Fix, checks and reviews,<br>fresh 🍽️ Stack ready
    end
    rect rgba(239, 159, 118, 0.2)
        alt Validate no and confidence at least merge-confidence
            C-->>H: Agent: 🔀 Batch 1 merging <-
        else Marked or lower confidence
            C-->>H: Agent: 🍽️ Batch ready at x/x <-
            H->>U: Agent: ❓ review batch 1, report <-
            U->>H: USER: Merge ->
            H->>C: Agent: 🔀 Merge ->
        end
    end
    C->>C: Verify GitHub heads,<br>merge in frozen worktree
    opt Merge fails
        C->>K: Agent: Return worktree, fix cause ->
        K->>K: 🍳 Fix, checks and reviews,<br>fresh 🍽️ Stack ready
    end
    Note over C,K: Next stack: Cook restacks on main<br>Same own diff keeps approval#59; changed diff needs review
    C->>K: Agent: merged ->
    C-->>H: Agent: Batch merged, deploy result<br>No Head Chef count yet <-
    C->>C: Release yes: finish procedure<br>from main
    Note over H,K: Step 6: Closing
    C->>C: Close Epic with child proof
    C->>K: Agent: Close, run enabled retros ->
    K->>K: 🧹 Retros, unwatch, report<br>🍽️ final after merge, then settle
    C->>C: Retros, confirm Cooks settled,<br>remove merged worktrees
    C-->>H: Agent: ⛳ Batch delivered, report <-
    C->>C: Settle
    H->>H: Count only delivered batches<br>Next batches, retros, settle Chefs<br>Prune worktree records
    H->>U: Agent: ⛳ x/y batches done, report <-
    H->>H: Settle and unpin
```

At review, Pascal may instead choose `⏳ Rework`, `🍽️ Hold` or `⏹️ Drop`. Rework returns affected Cooks to 🍳 and may withdraw ❓. Hold keeps the Chef 🍽️; the Head Chef shows `❓ held batch <b>` once no other work can progress. Drop closes the Cook and Chef at ⏹️, and the cut batch leaves the Head Chef's count.

Fast track implements required release content, skips docs and barrages, then uses the same readiness handoff. A batch without PRs runs in the Chef alone and goes to Closing. On `⏹️ Stop`, the Head Chef tells Chefs, Chefs relay to Cooks, Cooks close at ⏹️ unless their stacks merged, and a merge already running finishes before the Chef stops.

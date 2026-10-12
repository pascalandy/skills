---
name: CU2. COD en parallèle sur plusieurs dépôts
description: Un COD par dépôt en parallèle et une revue groupée
tags:
  - area/ea
  - kind/doc
  - status/not-approved
date_created: 2026-10-10
date_updated: 2026-10-11
---

# CU2. COD en parallèle sur plusieurs dépôts

> Not approved. Never run this CU. [s3](../SKILL.md)

Le MAIN lance un COD par dépôt en même temps. Il regroupe les revues dans un seul message, puis settle chaque COD dès son merge.

```mermaid
sequenceDiagram
    accDescr: Le MAIN lance un COD par dépôt en même temps, regroupe les revues et settle chaque COD dès son merge
    autonumber
    actor U as ETQ USER
    participant M as ETQ_T3 👑 MAIN <id4> [sujet]

    Note over U,M: CU2. COD en parallèle sur plusieurs dépôts<br>Étape 1. Aligner
    U->>M: USER: Nouveau thread dans projects.<br>PROMPT: Applique [changement] dans depot-a et depot-b ->
    loop Alignement
        M->>U: Agent: Voici le plan. Un COD par dépôt <-
        U->>M: USER: Q&A ->
    end
    U->>M: USER: J'approuve. Lance-toi ! ->

    Note over U,M: Étape 2. Lancer en parallèle
    create participant C1 as ETQ_T3 🐝 COD1 <id4>
    M->>C1: Agent: Crée le thread pour depot-a, partage le plan et l'id du MAIN ->
    create participant C2 as ETQ_T3 🐝 COD2 <id4>
    M->>C2: Agent: Crée le thread pour depot-b, partage le plan et l'id du MAIN ->
    M->>U: Agent: Liens vers COD1 et COD2 <-
    par depot-a
        C1->>C1: Branche et worktree de depot-a, change, teste, PR A (interne)
        C1-->>M: Agent: PR A prête <-
    and depot-b
        C2->>C2: Branche et worktree de depot-b, change, teste, PR B (interne)
        C2-->>M: Agent: PR B prête <-
    end
    Note over C1,C2: COD3 à COD<n> suivent le même schéma

    Note over U,M: Étape 3. Revue groupée dans le MAIN
    M->>U: Agent: État du chantier. PR A et PR B prêtes, commandes codiff <-
    U->>M: USER: Super ! Merge A et B ->
    M->>C1: Agent: Merge ->
    M->>C2: Agent: Merge ->
    C1->>C1: Merge A, supprime son worktree (interne)
    C1-->>M: Agent: Terminé, A mergée <-
    destroy C1
    M->>C1: Settle COD1 ->
    C2->>C2: Merge B, supprime son worktree (interne)
    C2-->>M: Agent: Terminé, B mergée <-
    destroy C2
    M->>C2: Settle COD2 ->
    M->>U: Agent: Chantier terminé, 2 PR mergées <-
    Note over U,M: USER continue ses demandes ou Settle la conversation
```

## Related

- CU1, des rounds successifs avec un COD à la fois
- CU3, le rapport de 4 h qui liste les COD actifs

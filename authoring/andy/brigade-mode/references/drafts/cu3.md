---
name: CU3. Statut de nuit
description: Le ménage et le rapport de 4 h dans STATUS, pas encore construit
tags:
  - area/ea
  - kind/doc
  - status/not-approved
date_created: 2026-10-10
date_updated: 2026-10-12
---

# CU3. Statut de nuit

> Not approved. Never run this CU. [brigade-mode](../../SKILL.md)

Chaque nuit à 4 h, STATUS fait le ménage sûr, puis rédige le rapport que l'utilisateur lit le matin. La règle 2a du diagramme : un worktree n'est supprimé que si sa PR est mergée, sans fichier modifié ni commit non poussé. Un worktree utilisé par un Cook actif, non settlé, est gardé même si sa PR est mergée. Ce cas n'est pas encore construit, pas plus que la commande `fleet status` du diagramme.

```mermaid
sequenceDiagram
    accDescr: Chaque nuit à 4 h, le thread STATUS fait le ménage sûr et rédige un rapport. Le matin, l'utilisateur le lit et ouvre un Chef au besoin
    autonumber
    actor U as ETQ USER
    participant S as ETQ_T3 STATUS

    Note over U,S: CU3. Statut de nuit<br>Étape 1. Routine de 4 h
    S->>S: Le planificateur T3 lance la routine (interne)
    S->>S: fleet status sur chaque dépôt du bureau (interne)
    S->>S: Liste les Chef ouverts et les Cook actifs (interne)
    S->>S: Supprime les worktrees sûrs, règle 2a, sauf ceux d'un Cook actif (interne)
    S->>S: Rédige le rapport (interne)

    Note over U,S: Étape 2. Lecture le matin
    S->>U: Agent: Rapport. Worktrees supprimés, worktrees gardés et pourquoi,<br>Chef ouverts, Cook actifs, PR ouvertes, clones modifiés <-
    loop Questions
        U->>S: USER: Q&A ->
        S->>U: Agent: Réponse <-
    end
    alt Un point demande du travail
        U->>S: USER: Ouvre un Chef pour [point] ->
        create participant M as ETQ_T3 👑 Chef <id4> [sujet]
        S->>M: Agent: Crée le thread avec le contexte du point ->
        S->>U: Agent: Lien vers le Chef <-
    else Rien à faire
        U->>S: USER: Merci ->
    end
    Note over U,S: STATUS reste ouvert. La routine de la nuit suivante y écrit son rapport
```

## Related

- CU1, le flux d'un Chef ouvert depuis le rapport
- CU2, les Cook que le rapport liste comme actifs

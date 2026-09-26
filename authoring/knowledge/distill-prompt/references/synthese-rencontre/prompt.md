---
name: synthese-rencontre
description: >
  Utiliser quand l'utilisateur fournit ou mentionne une transcription de rencontre client,
  des notes de rencontre, une synthèse, un courriel de suivi, des actions, des tâches,
  des suivis, des requis, des modifications, des besoins d'affaires, des besoins
  techniques ou des points d'attention. Produit uniquement en français canadien une
  synthèse structurée, un courriel de suivi client, une liste d'actions et/ou une
  extraction de requis, avec des flags `0o0o` pour la validation utilisateur.
---

# Synthèse de rencontre

## 1. Mission

Transformer une transcription brute de rencontre client en livrables clairs, actionnables et prêts à utiliser.

Le skill doit aider à produire rapidement :

1. une synthèse de rencontre structurée ;
2. un courriel de suivi client ;
3. une liste d'actions et de suivis ;
4. une extraction des requis, besoins et points d'attention ;
5. des flags de revue utilisateur avec `0o0o`.

Rester agnostique : ne jamais mentionner de fournisseur ou d'outil IA dans le livrable.

## 2. Déclencheurs

Utiliser ce skill quand l'utilisateur mentionne ou fournit :

- transcription ;
- rencontre ;
- meeting ;
- résumé ;
- synthèse ;
- compte-rendu ;
- synthèse courriel ;
- courriel de suivi ;
- email de suivi ;
- actions ;
- tâches ;
- todo ;
- suivis ;
- qui fait quoi ;
- requis ;
- requirements ;
- modifications ;
- besoins ;
- besoins techniques ;
- besoins fonctionnels ;
- points d'attention.

## 3. Principe directeur

Produire un livrable immédiatement exploitable sans bloquer l'utilisateur.

Règles générales :

- Ne pas poser de questions avant de produire.
- Ne pas inventer d'information.
- Utiliser l'information disponible.
- Utiliser des placeholders pour les informations manquantes non critiques.
- Utiliser `0o0o **VALIDATION À FAIRE:**` pour les éléments qui méritent une revue humaine.
- Rédiger uniquement en français canadien, sauf si l'utilisateur demande explicitement une traduction dans une autre langue.
- Utiliser les conventions du français canadien : courriel, rencontre, suivi, échéance, à faire, fin de semaine si pertinent.
- Éviter les tournures trop franco-françaises, les anglicismes inutiles et le vocabulaire corporatif lourd.
- Privilégier la clarté, la concision et l'action.

## 4. Modes de génération

### 4.1 Mode résumé rencontre complet

Déclencheurs :

- transcription ;
- rencontre ;
- meeting ;
- résumé ;
- compte-rendu ;
- aucune consigne précise.

Si une transcription est fournie sans demande plus précise, utiliser ce mode par défaut.

Sortie :

1. synthèse de rencontre complète ;
2. actions et suivis ;
3. requis / besoins / points d'attention détectés ;
4. courriel de suivi client ;
5. flags `0o0o` intégrés dans les livrables quand une validation est nécessaire.

### 4.2 Mode synthèse courriel

Déclencheurs :

- synthèse courriel ;
- résumé + courriel ;
- compte-rendu + courriel.

Sortie :

1. synthèse condensée ;
2. courriel client ;
3. flags `0o0o` si nécessaire.

### 4.3 Mode courriel seulement

Déclencheurs :

- courriel ;
- email ;
- suivi client ;
- courriel de suivi.

Sortie :

1. courriel prêt à envoyer ou marqué comme nécessitant une revue ;
2. flags `0o0o` directement dans le livrable si nécessaire.

### 4.4 Mode actions seulement

Déclencheurs :

- actions ;
- tâches ;
- todo ;
- suivis ;
- qui fait quoi.

Sortie :

1. actions client ;
2. actions G24 ;
3. responsables ;
4. échéances ;
5. flags `0o0o` si une validation est nécessaire.

### 4.5 Mode requis seulement

Déclencheurs :

- requis ;
- requirements ;
- modifications ;
- besoins techniques ;
- besoins fonctionnels ;
- points d'attention.

Sortie :

1. requis / besoins / points d'attention ;
2. classification ;
3. contexte ;
4. critère de succès si identifiable ;
5. priorité et complexité si raisonnablement estimables ;
6. flags `0o0o` si une validation est nécessaire.

## 5. Format — Synthèse de rencontre complète

Utiliser cette structure pour le mode par défaut.

```markdown
# SYNTHÈSE DE RENCONTRE — [Nom client]

**Date :** [Date à confirmer]  
**Durée :** [Durée non précisée]  
**Participants :** [Participants identifiés]  
**Type de rencontre :** [Suivi projet / Formation / Dépannage / Planification / Autre]

---

## 1. Objectif de la rencontre

[1 à 2 phrases sur le but principal]

## 2. Points clés à retenir

- [Point clé 1]
- [Point clé 2]
- [Point clé 3]

## 3. Décisions prises

- [Décision 1]
- [Décision 2]

## 4. Actions et suivis

### Client

- [ ] [Action concrète] — **Responsable :** [Nom] — **Échéance :** [Date]

### G24

- [ ] [Action concrète] — **Responsable :** [Nom] — **Échéance :** [Date]

## 5. Questions en suspens

- [Question] — **Qui doit répondre :** [Nom]

## 6. Requis / besoins / points d'attention

- **Type :** [Métier / Fonctionnel / Technique / Documentation / Formation / À clarifier]
- **Contexte :** [Pourquoi ce besoin existe]
- **Besoin :** [Ce qui est demandé ou attendu]
- **Critère de succès :** [Comment valider que c'est réglé]

## 7. Prochaines étapes

1. [Étape prioritaire 1]
2. [Étape prioritaire 2]
3. [Étape prioritaire 3]

## 8. Prochain rendez-vous

**Date :** [Date ou À planifier]  
**Objectif :** [Objectif]

## 9. Points de vigilance

- [Risque, blocage, dépendance ou ambiguïté]
```

## 6. Format — Courriel client

### 6.1 Règle de statut

Si le courriel contient au moins un flag `0o0o`, indiquer :

```markdown
**Statut :** Revue requise avant envoi
```

Si le courriel ne contient aucun flag `0o0o`, indiquer :

```markdown
**Statut :** Prêt à envoyer
```

### 6.2 Structure

```markdown
# COURRIEL DE SUIVI CLIENT

**Statut :** [Prêt à envoyer / Revue requise avant envoi]

**Objet :** Suivi de notre rencontre — [Nom client] — [Date]

Bonjour [Prénom],

Merci pour notre échange. Voici les principaux points discutés et les prochaines étapes.

**Ce qu'on a discuté :**
- [Point principal 1 en langage simple]
- [Point principal 2 en langage simple]
- [Point principal 3 en langage simple]

**De votre côté :**
- [Action client] — Échéance : [Date]

**De notre côté :**
- [Action G24] — Échéance : [Date]

**Prochain rendez-vous :**  
[Date et heure / À planifier] — [Objectif simple de la rencontre]

N'hésite pas si tu as des questions d'ici là.

Bonne journée,

Alexandre  
Le Groupe 24
```

### 6.3 Règles du courriel

- Ton professionnel, humain et rassurant.
- Tutoiement par défaut.
- Maximum 3 points principaux par défaut.
- Si plus de 3 points sont critiques, regrouper ou ajouter une courte section « Autres suivis importants ».
- Langage simple et accessible.
- Pas d'émojis.
- Pas de jargon technique.
- Pas de détails internes G24.
- Lecture cible : moins de 30 secondes.

## 7. Format — Actions seulement

```markdown
# ACTIONS EXTRAITES — [Nom client] — [Date]

## Client

| Action | Responsable | Échéance | Statut |
|---|---|---|---|
| [Action concrète] | [Nom] | [Date] | À faire |

## G24

| Action | Responsable | Échéance | Statut |
|---|---|---|---|
| [Action concrète] | [Nom] | [Date] | À faire |

---

**Total :** [X] actions client / [Y] actions G24
```

Si une action a une information critique incertaine, utiliser le flag dans la cellule ou sous le tableau.

Exemple :

```markdown
| Envoyer les accès | 0o0o **VALIDATION À FAIRE:** le responsable n'est pas confirmé. | Vendredi | À faire |
```

## 8. Format — Requis seulement

```markdown
# REQUIS / BESOINS / POINTS D'ATTENTION — [Nom client] — [Date]

## Vue d'ensemble

| # | Type | Description | Priorité | Complexité |
|---|---|---|---|---|
| 1 | [Métier / Fonctionnel / Technique / Documentation / Formation / À clarifier] | [Description claire] | [Haute / Moyenne / Basse] | [Simple / Moyenne / Complexe] |

## Détails par requis

### Requis #1 — [Titre court]

- **Type :** [Type]
- **Contexte :** [Pourquoi ce besoin existe]
- **Besoin :** [Ce qui doit être fait ou clarifié]
- **Critère de succès :** [Comment valider que c'est OK]
- **Notes :** [Contraintes, dépendances, points d'attention]

## Documentation / formation à produire

- [ ] [Guide, procédure, formation ou documentation à créer ou mettre à jour]

---

**Total :** [X] requis / besoins / points d'attention identifiés
```

### 8.1 Classification des requis

Classer les éléments si possible :

| Type | Description |
|---|---|
| Métier | Règle d'affaires, processus, responsabilité, approbation |
| Fonctionnel | Comportement attendu dans l'outil ou le processus |
| Technique | Configuration, workflow, champ, intégration, automatisation |
| Documentation | Procédure, guide, aide-mémoire, documentation client |
| Formation | Besoin d'accompagnement ou de démonstration |
| À clarifier | Besoin incomplet, ambigu ou non validé |

### 8.2 Sous-types pour requis techniques Zoho

Quand un requis est de type Technique et concerne Zoho, préciser le sous-type pour faciliter le passage de relais à l'équipe d'intégration.

| Sous-type | Exemples |
|---|---|
| Champ | Ajouter un champ, modifier un champ existant, champ calculé |
| Layout | Modifier la mise en page, ajouter une section |
| Workflow | Automatisation, notification, mise à jour automatique |
| Blueprint | Processus guidé, étapes obligatoires |
| Custom function | Logique personnalisée, calcul complexe, intégration sur mesure |
| Rapport | Nouveau rapport, dashboard, KPI |
| Intégration | Lien entre apps Zoho, connexion à un système externe |
| Permission | Profil, rôle, accès, visibilité |
| Import / Migration | Données à importer, transformation, nettoyage |

### 8.3 Évaluation de la complexité

| Complexité | Critères |
|---|---|
| Simple | Configuration standard, < 30 minutes, pas de code |
| Moyenne | Workflow multi-étapes, 1 à 2 heures, possiblement du code simple |
| Complexe | Logique métier avancée, intégration, custom function, > 2 heures |

### 8.4 Évaluation de la priorité

| Priorité | Critères |
|---|---|
| Haute | Bloque le client, impact opérationnel immédiat |
| Moyenne | Amélioration importante, attendue pour la phase en cours |
| Basse | Nice-to-have, peut attendre une phase ultérieure |

Si la complexité ou la priorité est estimée plutôt que confirmée, ajouter un flag `0o0o`.

## 9. Règles d'extraction

### 9.1 Décisions

Repérer notamment :

- « On va faire... »
- « C'est décidé... »
- « On part avec... »
- « OK pour... »
- « On garde... »
- « On laisse tomber... »

Si une décision est seulement implicite, la flagger.

### 9.2 Actions

Repérer notamment :

- « Je vais... »
- « Tu vas... »
- « On doit... »
- « Peux-tu... »
- « Il faut... »
- « On s'occupe de... »
- « Je m'en occupe... »
- « N'oublie pas de... »

Chaque action doit être concrète et vérifiable.

### 9.3 Attribution du responsable

| Formulation | Responsable probable |
|---|---|
| « Tu vas... », « De ton côté... » | Client, personne à identifier |
| « Je vais... » | La personne qui parle, si identifiable |
| « On va... », « On s'occupe de... » | G24 si le contexte indique l'équipe G24 |
| « Alexandre va... » | Alexandre |
| « [Nom] s'en occupe » | [Nom] |
| Non spécifié | Flag `0o0o` si critique |

### 9.4 Échéances

| Formulation | Interprétation |
|---|---|
| « Cette semaine » | Vendredi de la semaine courante, si la date de rencontre est connue |
| « Semaine prochaine » | Vendredi de la semaine suivante, si la date de rencontre est connue |
| « D'ici [jour] » | Jour mentionné |
| « Avant la prochaine rencontre » | Avant prochain RDV |
| Non mentionné | Placeholder ou flag selon criticité |

### 9.5 Requis / besoins / points d'attention

Repérer notamment :

- « Il faudrait pouvoir... »
- « Ce serait bien d'avoir... »
- « On aimerait que... »
- « Le problème c'est que... »
- « Est-ce possible de... »
- « Actuellement on fait X, mais on voudrait Y »
- « Il manque... »
- « On ne peut pas... »
- « Il faudrait configurer... »
- « Ajouter un champ... »
- « Créer une automatisation... »

Ne pas limiter les requis aux aspects techniques. Inclure aussi les besoins métier, fonctionnels, de documentation et de formation.

## 10. Flags de revue utilisateur avec `0o0o`

### 10.1 Objectif

Permettre à l'utilisateur de faire `CTRL+F` sur `0o0o` et de retrouver rapidement les points qui méritent une revue.

### 10.2 Format canonique

Utiliser exactement ce format :

```markdown
0o0o **VALIDATION À FAIRE:** [élément à valider]
```

Ne pas utiliser de variante comme `À valider`, `Validation`, `Review`, etc.

### 10.3 Quand utiliser le flag

Utiliser `0o0o` quand :

- une information est déduite mais non confirmée ;
- le responsable d'une action est incertain ;
- l'échéance est incertaine ;
- une décision semble implicite ;
- un requis est flou ;
- une priorité ou une complexité est estimée ;
- le nom du client, participant ou projet est incertain ;
- une phrase pourrait engager G24 ou le client ;
- une validation est nécessaire avant envoi ou avant exécution.

### 10.4 Quand ne pas utiliser le flag

Ne pas flagger :

- les informations simplement absentes mais non critiques ;
- les évidences ;
- chaque placeholder ;
- les détails qui ne changent pas la qualité, la précision ou le risque du livrable.

### 10.5 Règle anti-doublon

Si une information critique doit être validée, préférer le flag à un placeholder générique.

Préférer :

```markdown
**Échéance :**
0o0o **VALIDATION À FAIRE:** l'échéance n'a pas été confirmée.
```

Éviter :

```markdown
**Échéance :** [Échéance à définir]
0o0o **VALIDATION À FAIRE:** l'échéance n'a pas été confirmée.
```

### 10.6 Flags dans tous les livrables

Les flags peuvent apparaître dans tous les livrables, y compris :

- synthèse ;
- actions ;
- requis ;
- courriel client.

Si un courriel client contient au moins un flag `0o0o`, son statut doit être `Revue requise avant envoi`.

## 11. Placeholders obligatoires

Utiliser les placeholders pour les informations manquantes non critiques.

| Information absente | Placeholder |
|---|---|
| Date absente | `[Date à confirmer]` |
| Durée absente | `[Durée non précisée]` |
| Client absent | `[Nom client à confirmer]` |
| Participant inconnu | `[Participant non identifié]` |
| Prochain rendez-vous absent | `[À planifier]` |
| Requis flou non critique | `[À préciser]` |
| Faisabilité incertaine non critique | `[À valider techniquement]` |

Pour une information critique, utiliser plutôt `0o0o **VALIDATION À FAIRE:**`.

## 12. Simplification du jargon

Dans le courriel client, reformuler le jargon technique.

| Terme technique | Reformulation client |
|---|---|
| Workflow | Automatisation / envoi automatique |
| Blueprint | Processus guidé / étapes à suivre |
| Custom function | Automatisation personnalisée |
| Module | Section / onglet |
| Champ lookup | Lien entre fiches |
| Layout | Mise en page / formulaire |
| Subform | Tableau de détails |

## 13. Participants G24 connus

Participants récurrents :

- Alexandre — Directeur succès client ;
- Jean-Francis — Intégrateur technique ;
- Guillaume — Directeur des ventes.

Inclure tout autre membre G24 mentionné dans la transcription tel quel, sans inventer son rôle.

## 14. Interdits

- Ne pas mentionner de fournisseur ou d'outil IA dans les livrables.
- Ne pas inventer d'information.
- Ne pas poser de question avant de produire.
- Ne pas masquer les incertitudes importantes.
- Ne pas dupliquer placeholder + flag pour le même problème critique.
- Ne pas inclure d'émojis dans le courriel client.
- Ne pas inclure de jargon technique dans le courriel client sans reformulation.
- Ne pas inclure de détails internes G24 dans le courriel client.

## 15. Validation finale avant réponse

Avant de finaliser, vérifier :

- La synthèse est exploitable.
- Le courriel est prêt à envoyer ou clairement marqué comme nécessitant une revue.
- Les actions sont concrètes.
- Les responsables sont indiqués ou flaggés.
- Les échéances critiques sont indiquées ou flaggées.
- Les requis sont séparés des simples idées.
- Les besoins ne sont pas limités aux aspects techniques.
- Les flags utilisent exactement `0o0o **VALIDATION À FAIRE:**`.
- Si le courriel contient un flag `0o0o`, le statut est `Revue requise avant envoi`.
- Aucune mention d'un fournisseur ou d'un outil IA n'est présente dans le livrable.

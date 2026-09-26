---
name: Glossaire métier <Projet>
description: >-
  Glossaire métier canonique du projet <Projet> — formes canoniques,
  définitions, relations et termes à éviter
tags:
  - kind/glossary
  - kind/project
date_created: <YYYY-MM-DD>
date_updated: <YYYY-MM-DD>
---

# Glossaire métier <Projet>

## Objectif

Ce glossaire stabilise le vocabulaire métier du projet <Projet>.

Il sert à :

- protéger les formes canoniques
- clarifier les relations entre concepts
- éviter les raccourcis ambigus
- distinguer les rôles, systèmes, artefacts, statuts et mécanismes clés
- rendre visibles les ambiguïtés terminologiques non résolues

Il ne sert pas à :

- suivre l’état d’avancement du projet
- remplacer les documents d’acteurs, d’exigences, d’architecture ou de processus
- maintenir une liste d’alias acceptés
- documenter des décisions qui ne sont pas terminologiques

---

## Conventions de lecture

- le terme en début d’entrée est la forme canonique à utiliser
- les sections `Relations` décrivent le modèle conceptuel
- les sections `Définitions` décrivent le sens local des termes
- les formes sous Éviter ne sont pas des alias normatifs
- les marqueurs `0o0o` signalent des ambiguïtés terminologiques à trancher
- les noms officiels d’acteurs, rôles, systèmes, domaines ou taxonomies sont
  conservés dans leur forme source

---

## Modèle conceptuel global

### Relations

- <Concept A> <relation stable> <Concept B>
- <Concept B> ne remplace pas <Concept C>; il le complète, le consomme
  ou l’orchestre
- <Concept D> → <Concept E> → <Concept F> décrit <séquence
  structurelle ou chaîne de confiance>

### Définitions

- <Concept A> : <forme longue, expansion ou équivalent traduit>
  - Déf. : <définition canonique courte>
  - Note projet : <nuance propre au projet, seulement si utile>
  - À distinguer de : <termes souvent confondus, seulement si utile>
  - Éviter : <alias faibles, raccourcis, anglicismes ou formes ambiguës>

---

## <Famille conceptuelle, domaine, capacité ou regroupement métier>

### Relations

- <Concept A> <relation stable> <Concept B>
- <Concept C> produit 1+ <Concept D> selon <règle ou contexte>
- <Concept E> valide <Concept F> avant consommation par <Concept G>

### Définitions

- <Terme canonique> : <forme longue, expansion ou équivalent traduit>
  - Déf. : <définition canonique courte>
  - Note projet : <nuance propre au projet, seulement si utile>
  - À distinguer de : <termes souvent confondus, seulement si utile>
  - Éviter : <alias faibles, raccourcis, anglicismes ou formes ambiguës>

---

## Règles générales d’écriture

- utiliser les formes canoniques en début d’entrée
- définir les acronymes à la première occurrence dans un document autonome
- privilégier le français lorsque l’usage projet ne force pas l’anglais
- conserver l’anglais lorsqu’il est la forme d’usage du projet ou du standard
- qualifier les formulations génériques qui peuvent désigner plusieurs réalités
- ne pas renommer les domaines, rôles ou systèmes officiels sans décision explicite
- ne pas transformer les termes sous Éviter en alias acceptés

---

## Règles terminologiques prioritaires

### R1 — <Formulation ambiguë ou terme surchargé>

- Règle : <règle d’écriture ou de choix canonique>
- À écrire : <formes canoniques ou expressions recommandées>
- À éviter : <formes ambiguës, trop génériques ou incorrectes>

---

## Termes à ne pas utiliser comme formes canoniques

- <Forme à éviter>
  - Remplacer par : <forme canonique>
  - Raison : <ambiguë, trop générique, anglicisme, raccourci instable ou
    terme surchargé>

---

## Décisions terminologiques conservées

- <Question ou décision>
  - <raison de conserver cette forme, cette distinction ou cette règle>

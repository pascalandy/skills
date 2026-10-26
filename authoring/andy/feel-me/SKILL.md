---
name: "feel-me"
description: "Use when explicitly invoked as `feel me`, `same page`, or `same foot`, or when the user says they want to be on the same page or aligned with the agent."
kind: "general"
---

D'ABORD; L'agent lit et comprend AGENTS.md, puis investigue le code et les documents. L'agent ne modifie aucun fichier avant d'avoir écrit "👍 Je n'ai plus de question."

ENSUITE; L'agent reformule le but de l'utilisateur, le problème que l'utilisateur veut résoudre et les critères d'acceptation, pour s'assurer que l'agent et l'utilisateur sont alignés. L'agent l'écrit à la première personne, comme l'utilisateur le dirait : « Je veux… C'est réussi quand… »

ENSUITE; Pour chaque élément à réviser, l'agent propose une ou deux recommandations $concise et optimales.

ENSUITE; L'agent tranche lui-même chaque choix que le code, les documents, les conventions du projet ou le but de l'utilisateur permettent de trancher, et annonce chaque décision en une ligne avec sa raison.

ENSUITE; Au besoin, l'agent pose ses **questions** à l'utilisateur selon le gabarit ci-dessous, seulement pour :
- Le but ou ses priorités, quand ils restent ambigus
- Une action difficile à défaire ou visible hors du projet, comme supprimer, publier ou dépenser
- Un compromis entre des options de valeur comparable, que rien ne tranche

Le FMO (*future mode of operation*) est l'état que l'agent propose. Le CMO (*current mode of operation*) est l'état actuel, une référence que l'utilisateur consulte au besoin. Règles :
- Les décisions, puis les questions, vont de la plus importante à la moins importante. Quand l'agent a vu juste sur les premières, l'utilisateur peut lui faire confiance pour les suivantes
- Au plus 4 questions par ronde
- Les questions sont numérotées en continu, pour que l'utilisateur puisse répondre « 1a, 2b »
- Chaque question marque la recommandation de l'agent et dit en une ligne pourquoi elle compte
- L'utilisateur voit seulement la conversation. L'agent décrit chaque issue, Epic ou PR par ce qu'elle fait, dit si elle existe déjà, et met son numéro au plus entre parenthèses
- Quand la proposition relie plusieurs parties dont dépend une question, l'agent montre d'abord un diagramme Mermaid rendu de l'état proposé. Les questions nomment ses boîtes. Pour un fait que seul l'utilisateur connaît ou un changement sans parties liées, aucun diagramme. L'agent rend le diagramme dans un dossier temporaire hors du projet. Seul ce rendu échappe au gel avant le 👍
- Une question sans réponse prend la recommandation de l'agent, sauf pour une action difficile à défaire

Gabarit :

````md
### Décisions de l'agent
- [Décision] : [raison en une ligne]

### 1) 🙋 [Question]
**FMO**: [Le changement que l'agent propose, que l'utilisateur peut appliquer, avec un diff de code au besoin]. [Pourquoi il compte]
**CMO**: [L'état actuel]
- a) … (🟢 recommandé)
- b) …
- c) …

### 2) 🙋 [Question]
````

ENSUITE; L'agent intègre les réponses de l'utilisateur et repense l'ensemble de ses propositions, jusqu'à ce que l'agent n'ait plus de question. À chaque ronde, l'agent charge $2nd-pass avant de répondre.
- Quand l'agent n'a plus de question, il dit explicitement : "👍 Je n'ai plus de question."

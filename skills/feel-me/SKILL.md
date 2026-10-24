---
name: "feel-me"
description: "Use when explicitly invoked as `feel me`, `same page`, or `same foot`, or when the user says they want to be on the same page or aligned with the agent."
kind: "general"
---

D'ABORD; L'agent lit et comprend AGENTS.md, puis investigue le code et les documents. L'agent ne modifie aucun fichier avant d'avoir écrit "👍 Je n'ai plus de question."

ENSUITE; L'agent reformule le but de l'utilisateur et le problème que l'utilisateur veut résoudre, pour s'assurer que l'agent et l'utilisateur sont alignés. L'agent l'écrit à la première personne, comme l'utilisateur le dirait : « Je veux… »

ENSUITE; Pour chaque élément à réviser, l'agent propose une ou deux recommandations $concise et optimales 

ENSUITE; L'agent mentionne explicitement les décisions prises.

ENSUITE; Au besoin, l'agent pose ses **questions** à l'utilisateur selon le gabarit ci-dessous. Le FMO (*future mode of operation*) est l'état que l'agent propose. Le CMO (*current mode of operation*) est l'état actuel, une référence que l'utilisateur consulte au besoin. Règles :
- Au plus 4 questions par ronde, classées par impact
- L'agent tranche lui-même les points mineurs, comme un détail cosmétique ou un statu quo, et annonce chaque choix en une ligne
- Les questions sont numérotées en continu, pour que l'utilisateur puisse répondre « 1a, 2b »
- Chaque question marque la recommandation de l'agent et dit en une ligne pourquoi elle compte

Gabarit :

````md
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

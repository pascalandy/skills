---
name: "consensus"
description: "Use only when explicitly invoked as: plan, consensus."
kind: "general"
---

D'ABORD; Lis et comprends AGENTS.md et investigue le code et les documents. Pendant tout le consensus, ne modifie aucun fichier : on reste en lecture seule jusqu'au "👍 Je n'ai plus de question."

ENSUITE; Dans tes mots, redis-moi quel est mon but et le problème que je veux résoudre afin que l'on s'assure que nous sommes bien tous les deux alignés.

ENSUITE; Voici le format dans lequel me répondre dans le but d'ajouter de la clarté et de m'aider à prendre des décisions optimales. Partage-moi une ou deux recommandations optimales par élément à réviser et assure-toi de demeurer $concise.

Quand tu me poses des **questions**, pour chaque élément, mets-moi en contexte avec le CMO (*current mode of operation*, l'état actuel) et le FMO (*future mode of operation*, l'état proposé). Ensuite, offre-moi un choix de réponses selon ces règles :
- Au plus 4 questions par ronde, classées par impact
- Numérote les questions en continu d'un élément à l'autre, pour que je puisse répondre « 1a, 2b »
- Pour chaque question, marque ta recommandation et dis en une ligne pourquoi elle compte

Format:

````md
### Titre élément XYZ

1) 🙋 [Question (pourquoi c'est important)]
   - a) … (🟢 recommandé)
   - b) …
   - c) …

**FMO**: [Ce que tu suggères comme modification. Le FMO doit être actionnable par l'utilisateur. Code diff when relevant]
- …

**CMO**: [Ce que nous avons maintenant]
- …

2) 🙋 ..
````

ENSUITE; Suite à mes réponses, intègre-les et repense l'ensemble de tes propositions jusqu'à ce que tu n'aies plus de questions.
- Quand c'est le cas, réponds-moi explicitement: "👍 Je n'ai plus de question."
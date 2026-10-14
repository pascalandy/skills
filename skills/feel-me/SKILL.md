---
name: "feel-me"
description: "Use when explicitly invoked as `feel me`, `same page`, or `same foot`, or when the user says they want to be on the same page or aligned with the agent."
kind: "general"
---

D'ABORD; Lis et comprends AGENTS.md et investigue le code et les documents. Ne modifie aucun fichier avant le "👍 Je n'ai plus de question."

ENSUITE; Dans tes mots, dis-moi quel est mon but et le problème que je veux résoudre afin que l'on s'assure que nous sommes bien alignés ensemble.

ENSUITE; Partage-moi une ou deux recommandations optimales par élément à réviser et assure-toi de demeurer $concise.

Quand tu me poses des **questions**, chaque question porte son FMO (*future mode of operation*, l'état proposé), puis un choix de réponses. Le CMO (*current mode of operation*, l'état actuel) vient après, comme référence que je consulte au besoin. Suis ces règles :
- Au plus 4 questions par ronde, classées par impact
- Pose seulement les questions qui changent le livrable. Tranche toi-même les autres, comme un point cosmétique ou un statu quo, et annonce chaque choix en une ligne
- Numérote les questions en continu d'un élément à l'autre, pour que je puisse répondre « 1a, 2b »
- Pour chaque question, marque ta recommandation et dis en une ligne pourquoi elle compte
- Pour un fait que je suis seul à connaître, comme une suppression voulue, pose une question oui ou non qui nomme la chose, sans options ni recommandation
- Nomme chaque chose avec les mots que la conversation emploie déjà, et résume chaque ticket, PR ou fichier que la question cite, car je ne l'ai pas ouvert

Voici le format dans lequel me répondre dans le but de m'aider à prendre des décisions optimales :

````md
### Titre élément

1) 🙋 [Question]. **FMO**: [Ce que tu suggères comme modification. Le FMO doit être actionnable par l'utilisateur. Code diff when relevant]. [Pourquoi c'est important]
   - a) … (🟢 recommandé)
   - b) …
   - c) …

**CMO**: [Ce que nous avons maintenant]

---

2) 🙋 …
````

ENSUITE; Suite à mes réponses, intègre-les et repense l'ensemble de tes propositions jusqu'à ce que tu n'aies plus de questions. À chaque ronde, charge $2nd-pass avant de me répondre.
- Si tu n'as plus de question, dis-moi explicitement : "👍 Je n'ai plus de question."
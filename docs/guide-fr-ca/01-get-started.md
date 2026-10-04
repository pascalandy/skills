# Coller une phrase et lancer ton premier skill

Dans cette page, tu colles une phrase dans ton application, tu lances un premier skill et tu gardes les skills actifs pour toutes tes conversations. Compte une minute.

## Colle la phrase

Ouvre une nouvelle conversation et colle cette phrase :

```text
Lis https://raw.githubusercontent.com/pascalandy/skills/main/docs/references/remote-skills-general.md et ignore `oem`. Quand une de mes demandes correspond à un skill de cette liste, ouvre ce skill et suis-le.
```

L'agent ouvre la page. Elle liste tous les skills pour les non-développeurs, avec une ligne pour chacun. L'agent répond parfois avec un court résumé.

La phrase ignore `oem` parce que ce skill contient mes préférences personnelles. Sinon, ton agent te traiterait comme si tu étais moi.

## Lance ton premier skill

Dans la même conversation, écris une vraie demande, avec ton propre commerce :

```text
marketing ; écris un titre pour ma boulangerie à Montréal
```

Regarde ce qui se passe. Le mot "marketing" ouvre `corey-mode`, mon mode de marketing. Le mode lit le reste de ta demande et choisit le playbook qui convient, ici `copywriting`. L'agent ouvre ce playbook et le suit. Certains agents commencent leur réponse par une ligne comme `Route: copywriting`, qui nomme le playbook suivi.

Tu reçois des propositions de titres, la raison derrière chacune et des questions comme "Quel est ton produit vedette?" Réponds-y. La ronde suivante parle de ta boulangerie, pas de n'importe laquelle.

## Garde les skills actifs dans chaque conversation

Coller la phrase chaque fois devient vite lassant. Mets-la là où ton application la lit chaque fois :

- Dans les instructions personnalisées de ton application, pour que toutes tes conversations utilisent les skills
- Dans les instructions d'un projet, pour que seules les conversations de ce projet les utilisent

Ouvre ensuite une nouvelle conversation et écris ta demande. Tu n'as plus besoin de la phrase.

## Si ton application n'ouvre pas la page

Certaines applications, ou certains forfaits, n'ouvrent pas les pages web. D'autres refusent un lien que l'agent construit lui-même. Tu le remarques quand l'agent répond de mémoire, dit qu'il ne peut pas naviguer ou nomme un skill absent de la liste.

Essaie ces solutions dans l'ordre :

1. Active la recherche web ou la navigation dans ton application, puis colle la phrase de nouveau.
2. Essaie la même phrase dans une autre application.
3. Ouvre le skill toi-même. Chaque skill se trouve dans le [dossier `skills/` sur GitHub](https://github.com/pascalandy/skills/tree/main/skills). Ouvre le fichier `SKILL.md` du skill, copie son texte et colle-le dans la conversation après les mots "Suis ces instructions". Pour une route, copie plutôt son playbook, dans le dossier `playbooks/` du mode. Ça marche dans toutes les applications.

**Piège :** ne te fie pas à une réponse qui ne nomme aucun skill. Demande à l'agent : "Quel skill as-tu ouvert, et quelle est sa première étape?" Un agent qui a lu le skill peut répondre. Un agent qui a deviné, non.

Suite : [Nommer un mode, puis la tâche](./02-modes.md).

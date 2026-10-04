# Activer les skills en une phrase

Dans cette page, tu branches ton application sur mes skills avec une seule phrase, puis tu lances un premier skill. Compte deux minutes. Le guide prend pour exemple ChatGPT sur ton téléphone.

## Copie la phrase

```text
Lis https://raw.githubusercontent.com/pascalandy/skills/main/docs/references/remote-skills-general.md et ignore `oem`. Quand une de mes demandes correspond à un skill de cette liste, ouvre ce skill et suis-le.
```

La phrase pointe vers la liste de mes skills pour les non-développeurs, avec une ligne pour chacun. Elle ignore `oem` parce que ce skill contient mes préférences personnelles. Sinon, ton agent te traiterait comme si tu étais moi.

## Choisis : par défaut ou pour un essai

Tu as deux façons d'utiliser la phrase :

- **Par défaut.** Tu la mets dans les instructions personnalisées de ton application. Elle s'applique alors à toutes tes conversations, sans que tu la colles. C'est ce que je recommande
- **Pour un essai.** Tu la colles au début d'une nouvelle conversation. Elle vaut pour cette conversation seulement

## Mets la phrase par défaut dans ChatGPT

Sur ton téléphone, dans ChatGPT :

1. Ouvre les **Paramètres**.
2. Va dans **Personnalisation**, puis dans **Instructions personnalisées**.
3. Colle la phrase dans le champ des instructions, puis enregistre.

Les menus changent parfois de nom. Si tu ne les trouves pas, cherche "instructions personnalisées" dans les paramètres. Dans Claude, colle la phrase dans tes préférences personnelles ou dans les instructions d'un projet.

Ouvre ensuite une nouvelle conversation. Ton agent lit la liste chaque fois qu'une demande en a besoin.

## Ou fais un essai

Ouvre une nouvelle conversation et colle la phrase. L'agent ouvre la page et répond parfois avec un court résumé. Écris ta demande dans la même conversation.

## Lance ton premier skill

Écris une vraie demande, avec ton propre commerce :

```text
marketing ; écris un titre pour ma boulangerie à Montréal
```

Le mot "marketing" ouvre `corey-mode`, mon mode de marketing. Le mode lit le reste de ta demande et choisit le playbook qui convient, ici `copywriting`. Certains agents commencent leur réponse par une ligne comme `Route: copywriting`, qui nomme le playbook suivi.

Tu reçois des propositions de titres, la raison derrière chacune et des questions comme "Quel est ton produit vedette?" Réponds-y. La ronde suivante parle de ta boulangerie, pas de n'importe laquelle.

## Si ton application n'ouvre pas la page

Certaines applications, ou certains forfaits, n'ouvrent pas les pages web. D'autres refusent un lien que l'agent construit lui-même. Tu le remarques quand l'agent répond de mémoire, dit qu'il ne peut pas naviguer ou nomme un skill absent de la liste.

Essaie ces solutions dans l'ordre :

1. Active la recherche web ou la navigation dans ton application, puis réessaie.
2. Essaie la même phrase dans une autre application.
3. Ouvre le skill toi-même. Chaque skill se trouve dans le [dossier `skills/` sur GitHub](https://github.com/pascalandy/skills/tree/main/skills). Ouvre le fichier `SKILL.md` du skill, copie son texte et colle-le dans la conversation après les mots "Suis ces instructions". Pour une route, copie plutôt son playbook, dans le dossier `playbooks/` du mode. Ça marche dans toutes les applications.

**Piège :** ne te fie pas à une réponse qui ne nomme aucun skill. Demande à l'agent : "Quel skill as-tu ouvert, et quelle est sa première étape?" Un agent qui a lu le skill peut répondre. Un agent qui a deviné, non.

Suite : [Planifier, puis dire go](./02-planifier-puis-go.md).

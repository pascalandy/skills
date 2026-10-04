# Activer les skills

Une phrase suffit. Elle pointe ton agent vers la liste de mes skills, sans rien installer.

## Mets la phrase dans tes instructions personnalisées

```text
Lis https://raw.githubusercontent.com/pascalandy/skills/main/docs/references/remote-skills-general.md et ignore `oem`. Quand une de mes demandes correspond à un skill de cette liste, ouvre ce skill et suis-le.
```

Dans ChatGPT : **Paramètres** › **Personnalisation** › **Instructions personnalisées**. Dans Claude : tes préférences personnelles, ou les instructions d'un projet. La phrase s'applique ensuite à chaque nouvelle conversation.

Pour un essai, colle-la plutôt au début d'une conversation. Elle ne vaut alors que pour celle-là.

`oem` contient mes préférences personnelles. Sans cette exclusion, ton agent te prendrait pour moi.

## Lance un premier skill

```text
marketing ; écris un titre pour ma boulangerie à Montréal
```

**Le mot "marketing" lance `corey-mode`, qui choisit automatiquement le playbook `copywriting`.** Tu nommes le domaine, et le mode trouve la méthode parmi ses 50 playbooks, sans que tu en connaisses un seul. C'est là que toute la magie s'opère à ta place.

L'agent propose des titres, justifie chacun et demande ce qui manque pour les préciser. Certains agents annoncent le playbook en tête de réponse, comme `Route: copywriting`.

## Si l'agent n'ouvre pas la liste

Il répond de mémoire, dit qu'il ne peut pas naviguer ou invente un skill. Essaie, dans l'ordre :

1. Active la recherche web dans ton application.
2. Essaie une autre application.
3. Colle le skill toi-même, précédé de "Suis ces instructions". Copie le `SKILL.md` depuis le [dossier `skills/`](https://github.com/pascalandy/skills/tree/main/skills), ou le playbook d'une route depuis le dossier `playbooks/` de son mode.

**Piège :** une réponse qui ne nomme aucun skill est peut-être devinée. Demande : "Quel skill as-tu ouvert, et quelle est sa première étape?"

Suite : [Planifier, puis dire go](./02-planifier-puis-go.md).

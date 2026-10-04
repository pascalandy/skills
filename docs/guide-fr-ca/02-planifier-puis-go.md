# Planifier, puis dire go

Ma façon de travailler tient en deux mots. `plan` aligne l'agent sur ce que je veux. `go` lance le travail.

## Termine chaque demande par `plan`

```text
Je veux envoyer une infolettre mensuelle à mes clients. plan
```

Je le fais pour chaque demande, même celles qui semblent faciles. Une demande laisse toujours des trous, et l'agent les comble en devinant. `plan` l'oblige à s'aligner avant d'agir.

L'agent n'exécute rien. Il reformule ton but, liste les cas à couvrir et ce qui est hors périmètre, puis pose les questions que toi seul peux trancher. Ici : l'outil d'envoi, la taille de la liste, qui écrit le contenu.

## Réponds jusqu'à zéro question

Un seul message peut répondre à tout. L'agent revoit son plan à chaque réponse et repose une question tant qu'une décision reste ouverte. Il présente ensuite le plan :

- **CMO** : le fonctionnement actuel et ce qui coince
- **FMO** : le fonctionnement visé
- **How we'll know it works** : les vérifications
- **Premortem** : les causes d'échec probables et la parade prévue

Puis il conclut :

```text
👍 Zéro question restante. Dites « execute » ou « go » 🚀
```

## Tape `go`

```text
go
```

L'agent exécute le plan convenu, sans deviner. Si un point cloche, dis-le au lieu de taper `go`, et il revoit le plan.

`plan` se combine avec un mode. L'alignement vient d'abord, le playbook suit au `go` :

```text
marketing ; launch. Je lance un service de tenue de livres par texto. plan
```

**Piège :** taper `go` sans lire le plan. Le plan existe pour attraper une mauvaise idée pendant qu'elle coûte peu.

Suite : [Nommer un mode, puis la tâche](./03-modes.md).

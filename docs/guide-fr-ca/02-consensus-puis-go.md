# Viser le consensus, puis dire go

Ma façon de travailler tient en deux mots. `consensus` aligne l'agent sur ce que je veux. `go` lance le travail.

## Termine chaque demande par `consensus`

```text
Je veux envoyer une infolettre mensuelle à mes clients.

consensus
```

Je le fais pour chaque demande, même celles qui semblent faciles. Une demande laisse toujours des trous, et l'agent les comble en devinant. `consensus` l'oblige à s'aligner avant d'agir.

L'agent ne modifie rien. Il reformule ton but et le problème à résoudre, puis présente chaque point à trancher :

- **CMO** : ce qui existe aujourd'hui
- **FMO** : ce qu'il propose, assez concret pour que tu puisses agir

Viennent ensuite les questions que toi seul peux trancher. Ici : l'outil d'envoi, la taille de la liste, qui écrit le contenu.

## Réponds jusqu'à zéro question

Chaque question est numérotée, avec des choix en lettres et une recommandation marquée 🟢. Au plus quatre par ronde, les plus importantes d'abord. Réponds en une ligne :

```text
1a, 2b, 3a
```

L'agent intègre tes réponses, revoit l'ensemble de ses propositions et repose une question tant qu'une décision reste ouverte. Quand il n'en reste aucune, il conclut :

```text
👍 Je n'ai plus de question.
```

## Tape `go`

```text
go
```

L'agent exécute ce que vous avez convenu, sans deviner. Si un point cloche, dis-le au lieu de taper `go`, et il revoit ses propositions.

`consensus` se combine avec un mode. L'alignement vient d'abord, le playbook suit au `go` :

```text
marketing ; launch. Je lance un service de tenue de livres par texto.

consensus
```

**Piège :** taper `go` sans lire les propositions. Le consensus existe pour attraper une mauvaise idée pendant qu'elle coûte peu.

Suite : [Nommer un mode, puis la tâche](./03-modes.md).

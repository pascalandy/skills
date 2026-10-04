# Planifier, puis dire go

Ma façon de travailler tient en deux mots : `plan` et `go`. Dans cette page, tu vois pourquoi, puis tu suis une vraie demande jusqu'au `go`.

## Pourquoi je finis toujours par `plan`

Peu importe ma demande, je la termine par `plan`. Même quand je pense que c'est facile. Une demande laisse toujours des trous, et un agent qui devine les comble à sa façon. Avec `plan`, l'agent et moi nous alignons avant qu'il fasse quoi que ce soit.

## 1. Termine ta demande par `plan`

```text
Je veux envoyer une infolettre mensuelle à mes clients. plan
```

## 2. Réponds aux questions de l'agent

L'agent n'exécute rien encore. Il te répond avec :

- ton but, reformulé dans ses mots
- les cas à couvrir, y compris les cas limites
- ce qui est hors périmètre
- les questions que toi seul peux trancher

Pour l'infolettre, il demande par exemple quel outil d'envoi tu utilises, combien de clients sont sur ta liste et qui écrit le contenu. Réponds dans tes mots. Un seul message peut répondre à toutes les questions.

## 3. Continue jusqu'à zéro question

Après chaque réponse, l'agent revoit tout son plan. S'il reste une décision ouverte, il pose une nouvelle question. Sinon, il présente son plan sous des titres en anglais :

- **CMO** : comment ça marche aujourd'hui, et ce qui coince
- **FMO** : comment ça marchera après
- **How we'll know it works** : les vérifications qui prouveront que ça marche
- **Premortem** : ce qui pourrait mal tourner, et ce que le plan prévoit contre ça

Il termine par une ligne comme celle-ci :

```text
👍 Zéro question restante. Dites « execute » ou « go » 🚀
```

## 4. Dis `go`

Lis le plan. S'il te convient, tape :

```text
go
```

C'est là que la magie opère. L'agent exécute le plan sur lequel vous vous êtes entendus, au lieu de deviner. Si un point cloche, dis-le plutôt que `go`, et l'agent revoit son plan.

`plan` marche aussi avec un mode. L'agent s'aligne d'abord avec toi, puis suit le playbook quand tu dis `go` :

```text
marketing ; launch. Je lance un service de tenue de livres par texto. plan
```

**Piège :** taper `go` sans lire le plan. Le plan sert à attraper une mauvaise idée pendant qu'elle coûte encore peu.

Suite : [Nommer un mode, puis la tâche](./03-modes.md).

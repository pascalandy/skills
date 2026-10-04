# Réfléchir avant que l'agent agisse

Une demande floue donne une réponse floue, et une décision précipitée coûte plus cher que les minutes gagnées. Dans cette page, tu utilises trois skills et deux routes d'`andy-mode`. Ils font comprendre le but à l'agent avant qu'il agisse, ou aiguisent ta propre réflexion avant que tu décides.

## Planifie avant d'agir avec `plan`

```text
plan Je veux faire passer le rapport hebdomadaire de mon équipe du courriel à un tableau de bord partagé
```

L'agent reformule ton but dans ses mots, liste les cas à couvrir et dit ce qui est hors périmètre. S'il a besoin d'une décision de ta part, il s'arrête et te pose la question. Il décrit ensuite comment les choses fonctionnent aujourd'hui, comment elles fonctionneront après le changement, comment tu sauras que ça marche et ce qui pourrait mal tourner.

Il ne fait rien avant que tu dises `go`. Lis le plan, réponds aux questions et dis `go` seulement quand le plan est bon.

## Mets un plan à l'épreuve avec `grilling`

```text
grilling. Mets à l'épreuve mon plan d'ouvrir une deuxième succursale au printemps.
```

L'agent t'interroge par rondes. Chaque ronde regroupe les questions auxquelles tu peux répondre maintenant, numérotées, chacune avec la réponse qu'il recommande. Tes réponses ouvrent la ronde suivante. L'entrevue se termine quand aucune décision n'est laissée de côté, et l'agent n'agit pas avant que tu confirmes que vous comprenez le plan de la même façon.

Utilise `grilling` quand tu as déjà un plan et que tu veux en trouver les points faibles avant de t'engager.

## Confronte une opinion avec `andy-mode ; sparring`

```text
andy-mode ; sparring. Toutes les PME ont besoin de leur propre appli.
```

L'agent joue le partenaire d'entraînement franc. Il reformule ton affirmation, dit s'il est d'accord et à quel point il en est sûr, et sépare ce qu'il sait de ce qu'il devine. Il nomme ensuite les hypothèses cachées dans ton affirmation, les points où tu as en partie raison et les preuves qui le feraient changer d'avis. Il ne te flatte pas et garde sa position, sauf si tu apportes un meilleur argument.

## Démêle une décision avec `andy-mode ; think`

```text
andy-mode ; think. Est-ce que j'embauche un junior ou un senior comme premier employé?
```

L'agent trouve l'incertitude qui changerait ta décision. Il choisit une seule méthode de réflexion pour la réduire et te dit laquelle, et pourquoi. Tu obtiens une vue plus claire de ta décision, pas une liste de tous les angles possibles.

## Fais une recherche avec `research`

```text
research Comment les boulangeries de Montréal fixent-elles le prix des gâteaux sur mesure? Cite tes sources.
```

L'agent remonte chaque affirmation jusqu'à sa source d'origine, comme le site d'un commerce ou une page officielle, et la cite. Ouvre au moins une source pour vérifier la réponse au lieu de lui faire confiance.

**Piège :** n'écris pas "planifie et fais-le" dans la même demande. `plan` s'arrête exprès avant d'agir, pour que tu attrapes une mauvaise idée pendant qu'elle coûte encore peu. Dis `go` quand le plan est bon.

Suite : [Écrire et réviser avec l'agent](./04-write.md).

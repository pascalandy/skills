# Réfléchir avant de décider

Une demande floue donne une réponse floue, et une décision précipitée coûte plus cher que les minutes gagnées. `plan` aligne l'agent sur une tâche à exécuter, comme le montre la [page 2](./02-planifier-puis-go.md). Dans cette page, tu utilises deux skills et deux routes d'`andy-mode` qui aiguisent ta propre réflexion avant que tu décides.

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

**Piège :** ne confonds pas `plan` et `grilling`. Utilise `plan` quand tu veux que l'agent exécute une tâche après votre alignement. Utilise `grilling` quand tu veux éprouver une idée ou une décision, sans rien exécuter.

Suite : [Écrire et réviser avec l'agent](./05-ecrire.md).

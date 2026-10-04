# Transformer ton travail en document à montrer

Certains travaux passent mieux en page qu'en réponse dans la conversation. Dans cette page, tu utilises `html-mode` pour faire un résumé d'une page, une présentation, un schéma et un plan de travail. Chacun est un seul fichier HTML qui s'ouvre dans ton navigateur.

## Fais un résumé d'une page avec `html-mode ; artifact`

```text
html-mode ; artifact. Fais de ce rapport un résumé d'une page pour ma directrice : [colle le rapport]
```

L'agent construit une page avec ton contenu, une mise en page claire et des couleurs lisibles. Elle fonctionne sur un téléphone et sur un ordinateur.

## Fais une présentation avec `html-mode ; slides`

```text
html-mode ; slides. Fais de ces notes une présentation de 6 diapositives pour la banque : [colle tes notes]
```

L'agent raconte une histoire, un écran à la fois. Ouvre le fichier et utilise les flèches du clavier pour passer d'une diapositive à l'autre.

## Dessine un schéma avec `html-mode ; diagram`

```text
html-mode ; diagram. Montre comment une commande passe de notre site web à la livraison.
```

L'agent dessine les liens entre les parties : qui transmet quoi à qui, et dans quel ordre.

## Présente un plan de travail avec `html-mode ; plan`

```text
html-mode ; plan. Montre les étapes, les responsables et les échéances de ce projet : [colle le plan]
```

L'agent montre les engagements, leur ordre, le responsable de chacun, les dépendances et les risques.

## Ouvre le fichier

Certaines applications affichent un aperçu de la page directement dans la conversation. Sinon, télécharge le fichier et ouvre-le dans ton navigateur.

Dans ton application, l'agent ne peut pas ouvrir la page pour la vérifier. Il te dit quelles vérifications il n'a pas pu faire. Regarde la page toi-même sur un téléphone et sur un ordinateur, puis demande les changements en mots simples : "Le tableau est trop large sur mon téléphone."

Deux autres routes esquissent les écrans d'une application ou d'un site web : `wireframe` pour une mise en page sommaire et `prototype` pour une maquette soignée.

**Piège :** demande une seule page à la fois. Un résumé, une présentation et un schéma dans la même demande donnent trois résultats bâclés. Demande le résumé, relis-le, puis demande la présentation.

Suite : [Recettes et pièges](./08-recettes-et-pieges.md).

# Produire un document à montrer

`html-mode` livre un seul fichier HTML, lisible dans n'importe quel navigateur, sur téléphone comme sur ordinateur.

## Fais un résumé d'une page avec `html-mode ; artifact`

```text
html-mode ; artifact. Fais de ce rapport un résumé d'une page pour ma directrice : [colle le rapport]
```

## Fais une présentation avec `html-mode ; slides`

```text
html-mode ; slides. Six diapositives pour la banque, à partir de ces notes : [colle tes notes]
```

Une idée par écran. Les flèches du clavier font défiler les diapositives.

## Dessine un schéma avec `html-mode ; diagram`

```text
html-mode ; diagram. Le trajet d'une commande, du site web à la livraison.
```

## Présente un plan de travail avec `html-mode ; plan`

```text
html-mode ; plan. Étapes, responsables et échéances de ce projet : [colle le plan]
```

L'agent montre l'ordre, les responsables, les dépendances et les risques.

## Transforme un document en page interactive avec `html-mode ; interactive-page`

```text
html-mode ; interactive-page. Fais de ce PDF une page web où une carte suit la lecture : [joins le PDF]
```

Par défaut, l'agent livre une esquisse : il vérifie la page sur téléphone, tablette et ordinateur, puis la fait relire en 2 ou 3 rondes de QA. Pour un livrable client, dis-le : il te pose d'abord quelques questions, dont le nombre de rondes de QA.

## Vérifie le rendu toi-même

Certaines applications affichent un aperçu. Sinon, télécharge le fichier et ouvre-le. Dans une application de conversation, l'agent ne voit pas la page, alors il te dit quelles vérifications il n'a pas faites. Regarde-la sur téléphone et sur ordinateur, puis demande les corrections : "Le tableau déborde sur mobile."

Deux autres routes servent aux écrans d'application ou de site web. `wireframe` esquisse une mise en page, et `prototype` produit une maquette soignée.

**Piège :** demander trois documents à la fois. Tu obtiens trois résultats bâclés. Un document par demande.

Suite : [Recettes et pièges](./08-recettes-et-pieges.md).

# Écrire et réviser avec l'agent

Un texte écrit par un agent a tendance à sonner comme un agent. Dans cette page, tu utilises trois skills et deux routes d'`andy-mode` pour enlever la voix de robot, resserrer un texte, raconter une histoire, raccourcir une réponse et vérifier un texte avant de l'envoyer.

## Enlève la voix de robot avec `unslop`

```text
unslop ce texte : [colle ton texte]
```

L'agent réécrit le texte sans les habitudes qui trahissent l'IA : remplissage, précautions inutiles, mots enflés et tics de mise en forme. Il a une version anglaise et une version française, et il choisit celle qui correspond à ton texte.

Après une longue réponse, deux mots suffisent :

```text
unslop ça
```

## Resserre un texte avec `andy-mode ; write-with-clarity`

```text
andy-mode ; write-with-clarity. [colle ton texte]
```

L'agent révise pour la clarté et la force, selon les règles classiques de Strunk : voix active, mots concrets, aucun mot inutile. Utilise-le pour les rapports, les résumés et tout ce qu'une personne pressée doit lire.

## Raconte une histoire avec `andy-mode ; storytelling`

```text
andy-mode ; storytelling. Aide-moi à raconter comment on a perdu notre plus gros client, puis comment on l'a regagné, pour une présentation de 3 minutes à mon équipe.
```

L'agent lit ce que tu lui donnes, demande seulement ce qui bloque le travail et garde ta voix. Dans une histoire vraie, il n'invente jamais de faits, de citations ni d'émotions. Il peut aussi diagnostiquer une histoire déjà écrite, ou l'adapter à un autre public.

## Raccourcis une réponse avec `concise`

```text
concise
```

L'agent passe en style télégraphique : pas de remplissage, pas de politesses, des mots courts et des flèches pour les causes et les effets. Le sens reste le même. Utilise-le quand tu veux les faits vite. Pour un texte que d'autres liront, utilise plutôt `write-with-clarity`.

## Vérifie un texte avant de l'envoyer avec `2nd-pass`

```text
2nd-pass sur ce courriel avant que je l'envoie à ma directrice : [colle le courriel]
```

L'agent compare le texte à ce que tu as demandé. Il liste les erreurs concrètes, les points manquants et les contradictions, puis il les corrige ou te dit ce qui demande ta décision.

**Piège :** "améliore-le" ne donne aucune cible à l'agent. Dis qui lit le texte et ce que cette personne doit faire après l'avoir lu : "Ma directrice le lit en deux minutes et approuve le budget."

Suite : [Faire du marketing avec `corey-mode`](./06-marketing.md).

# Écrire et réviser

Un texte d'agent sonne comme un agent. Cinq outils pour corriger ça.

## Enlève la voix de robot avec `unslop`

```text
unslop ce texte : [colle ton texte]
```

L'agent retire les tics de l'écriture d'IA : remplissage, précautions, mots enflés, mise en forme excessive. Il a une version française et une anglaise. Après une longue réponse, `unslop ça` suffit.

## Resserre un texte avec `andy-mode ; write-with-clarity`

```text
andy-mode ; write-with-clarity. [colle ton texte]
```

Les règles de Strunk : voix active, mots concrets, aucun mot inutile. Pour les rapports et tout ce qu'une personne pressée doit lire.

## Raconte avec `andy-mode ; storytelling`

```text
andy-mode ; storytelling. Comment on a perdu notre plus gros client, puis comment on l'a regagné. Trois minutes, devant l'équipe.
```

L'agent garde ta voix et ne pose que les questions qui bloquent. Dans un récit vrai, il n'invente ni faits, ni citations, ni émotions. Il diagnostique aussi un récit existant ou l'adapte à un autre public.

## Raccourcis avec `concise`

```text
concise
```

Style télégraphique : pas de remplissage, pas de politesses, des flèches pour les causes. C'est pour toi. Pour un texte que d'autres liront, prends `write-with-clarity`.

## Vérifie avant d'envoyer avec `2nd-pass`

```text
2nd-pass sur ce courriel avant que je l'envoie à ma directrice : [colle le courriel]
```

L'agent compare le texte à ta demande et liste les erreurs, les oublis et les contradictions. Il corrige, ou te signale ce qui demande ta décision.

**Piège :** "améliore-le" ne donne aucune cible. Dis qui lit et ce que cette personne doit faire ensuite : "Ma directrice le lit en deux minutes et approuve le budget."

Suite : [Faire du marketing avec `corey-mode`](./06-marketing.md).

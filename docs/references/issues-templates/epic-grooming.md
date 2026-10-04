# Issue template: retro-global

````md
<epic-grooming>
## CMO : le problème, simplement

Quand tout passe, `just check` n'affiche rien et rend le code 0. Derrière un filtre qui condense la sortie, l'agent croit que la sortie s'est perdue et relance la commande 3 ou 4 fois. C'est arrivé dans 3 sessions sur 3.

REF: #424, #444, #482

## FMO : la règle

Pascal veut la réponse la plus courte possible, binaire, et la même pour chaque script.

- **Tout est parfait :** `{"ok":true}`, code 0
- **Sinon :** `{"ok":false,"errors":["…"]}`, code différent de 0, et chaque erreur dit quoi faire
- `ok` dit toujours la même chose que le code de sortie
- Un succès avec un avertissement n'est pas un succès

Les décisions prises le 2026-10-04 et leur pourquoi sont dans #493.

## Les étapes

On prouve d'abord la règle sur `just check`, avec une doc solide, jusqu'à l'UAT de Pascal. Après l'UAT, l'Epic 6 applique la même règle à tout le reste.

1. **`just check` répond `{"ok":true}`** (#430) · code + tests
   - **Aujourd'hui :** rien ne s'affiche quand tout passe
   - **Après :** `{"ok":true}`, et le format commun à tous les scripts existe dans `scripts/_common.py`
2. **La doc solide** (#493) · texte
   - **Aujourd'hui :** le contrat des scripts impose le silence en cas de succès, et les décisions de ce chantier ne sont écrites nulle part
   - **Après :** la page `docs/references/script-output.md` décrit la règle, comment lire la réponse, le comment et le pourquoi de chaque décision, et quels scripts suivent déjà la règle
3. **Pascal teste, on fusionne sur `main`, puis UAT en production** (#496) · Pascal
   - Pascal teste la PR des étapes 1 et 2
   - On fusionne sur `main`, et `just merge` déploie sur om1, mbp et mini
   - Pascal valide `just check` dans son travail réel, puis ferme le billet

Les étapes 1 et 2 partent dans la même PR.

## Critère de fin

Pascal ferme le billet d'UAT (#496). L'Epic 6 se débloque alors.

</details>

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

Technical details, evidence, approaches considered, blast radius, non-functional requirements, and links to related issues or PRs.

</details>

</epic-grooming>
````

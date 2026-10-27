# Synchro avec pstack

poteto-mode et ses skills apparentés viennent de pstack, le plugin de Lauren Tan publié dans [cursor/plugins](https://github.com/cursor/plugins/tree/main/pstack) sous licence MIT, reproduite dans `LICENSE` de ce dossier. Cette note garde la base de chaque synchro, pour que la suivante parte d'un point connu.

## Adaptation

- L'import du 1er septembre 2026, le commit `15c8f744` de dotfiles, copiait pstack v0.14.5 (`6fecddb`). La synchro du 9 septembre, le commit `91e26ad7` de dotfiles, l'a portée à v0.15.0 (`71ed0d1`)
- Les skills tournent dans T3 Code seulement. `agent-runtime.md` garde ce qui vaut pour tout mécanisme, et le skill `t3-runtime` garde les mécanismes de T3
- Les noms et mécanismes propres à Cursor sont retirés : `Task`, `subagent_type`, `poteto-agent`, `/setup-pstack` et ses règles `.mdc`
- Les principes vivent dans `principles/`, sans frontmatter. L'index de `SKILL.md` dit quand chacun s'applique, et le corps du fichier porte la règle
- Le parseur de `watch-pr` garde les identifiants de Bugbot et de Cursor que GitHub transmet. Ce sont des données de protocole, pas des consignes
- La limite d'environ 40 lignes du corps d'une PR dans `opening-a-pr.md` tient à son rôle de briefing. Elle ne suppose pas que le commit squash reprend ce corps, car chaque dépôt règle le contenu du message
- Le Laziness Protocol compte les cas réels avant de couvrir une forme d'entrée et refuse les formes restantes avec une erreur claire (#905)
- Les conventions du dépôt réservent `-` aux entrées lues en flux. Les fichiers ouverts sur place, comme SQLite, prennent un chemin, sans exception propre à brigade-mode (#807)
- Le playbook multi-PR écrit le plan. Une pile construite dans la session suit Feature ou Refactoring avec `gh-stack`. Une demande mixte attend le go puis suit la méthode nommée dans le plan, en gardant la priorité d'un playbook qui possède la topologie (#804)

## Synchro du 15 octobre 2026

Base v0.15.0 (`71ed0d1`), tête examinée `99743e9`, après v0.15.25.

Pris :

- L'étiquette de preuve sur chaque affirmation (#341) et la règle d'autonomie complète (#414)
- Les workers neufs par défaut (#491), pour tout mécanisme, dans `agent-runtime.md`
- Les quatre principes réécrits et validés par évals (#633). Fix Root Causes y est fusionné avec la méthode `diagnose`
- Le principe Explain the Number (#491), sans `benchmark-checklist`
- Les skills `correct` (#494) et `sharpen` (#615). L'échelle des mécanismes vit seulement dans Encode Lessons in Structure

Laissés :

- Les coupes faites pour économiser des tokens (#419, #538, #571, #634). Dans les principes, elles comptent sur le frontmatter, absent de `principles/`. Partout, leurs tests ne couvrent qu'Opus 5.5
- Le choix de l'effort selon la tâche (#613). Le `config.toml` de chaque route de brigade-mode garde ce contrôle
- `benchmark-checklist`, `in-your-own-words`, `ketchup`, `poteto-help` et les règles de `poteto-agent`

À examiner : les changements aux playbooks depuis v0.15.0, dont #491, la partie de #613 hors effort, et les pronoms neutres de #362.

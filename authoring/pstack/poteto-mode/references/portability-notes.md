# Portabilité de pstack

Les workflows utilisent maintenant les capacités disponibles dans la session. Le [contrat d’exécution](agent-runtime.md) précise comment découvrir ces capacités et quoi faire lorsqu’elles manquent. Cette adaptation conserve les rôles, les critères de preuve et les limites de chaque tâche. Elle ne garantit pas que chaque installation possède les mêmes outils.

Le commit `15c8f744` a importé la collection pour rendre ses workflows et principes disponibles dans la source partagée. Les chemins de transcripts et paramètres de délégation particuliers figuraient déjà dans cet import. Leur caractère accessoire à l’objectif de partage est une inférence tirée de cet historique, pas une décision amont documentée.

| Mécanisme initial | Utilité | Adaptation |
| --- | --- | --- |
| Appel de sous-agent avec paramètres fixes | Isoler une tâche et son contexte | Outil natif découvert dans la session, ou processus d’agent supervisé |
| Agent nommé et modèles par rôle | Transmettre une méthode et diversifier le jugement | Rôle générique explicite choisi par la route `profile-routing-matrix` d’andy-mode, avec son modèle et son niveau de raisonnement |
| Mode d’agent imposé pour accéder aux MCP | Donner accès aux preuves | Vérifier les outils du délégué tout en limitant ses actions de revue à la lecture |
| Agents cloud et tableau de bord | Exécution parallèle, isolation et suivi | Environnement confirmé, statut observable et résultats durables ; aucune VM implicite |
| Boucle et réveil programmés | Reprendre le travail jusqu’au critère de fin | Attente supervisée, événement pris en charge ou ordonnanceur configuré |
| Chemin et format uniques de transcripts | Retrouver les décisions et vérifier les actions | API d’historique ou export identifié, limité au projet et à la période autorisés |
| Répertoire MCP conventionnel | Découvrir les sources de preuves | Catalogue et interface de découverte du harness ; catégories absentes signalées |
| Règle toujours chargée et chemins de skills propres à l’éditeur | Retrouver instructions et choix de modèles | Source canonique, découverte vérifiée et lecture explicite du [contrat d’exécution](agent-runtime.md) |
| Question structurée native | Recueillir une préférence | Outil disponible ou question concise ; une absence de réponse ne vaut pas accord |
| Skills intégrés d’écriture, nettoyage et contrôle | Produire des instructions fiables et vérifier le vrai produit | Guides installés ou procédure fonctionnelle explicite ; contrôle réel du navigateur, terminal ou application |
| Routine webhook et carte de secret | Déclencher un travail depuis une UI sans exposer les clés | Serveur authentifié, runner documenté, statut de tâche et secrets côté serveur |
| Nettoyage lié à un éditeur | Libérer l’espace sans perdre du travail | Inventaire Git et caches des applications réellement installées ; activité inconnue soumise à revue |

Les points d’entrée diffèrent. La route Profile Routing Matrix s’invoque avec `andy-mode ; profile-routing-matrix`, et poteto-mode la lit quand il délègue. L’orchestrateur applique alors le rôle générique, le modèle et le niveau de raisonnement choisis avec les contrôles disponibles dans la session. Si un profil requis manque, il s’arrête et demande à l’utilisateur s’il faut continuer avec une alternative nommée. Codex expose la délégation selon la session et propose une exécution non interactive ; Claude Code propose des sous-agents et une interface programmatique. Le cœur de Pi n’intègre pas de sous-agents : cette capacité nécessite une extension ou des sessions distinctes via RPC, SDK ou processus. OpenCode propose des agents et une API serveur. Les commandes et permissions installées restent à vérifier avant utilisation. Voir [Codex : délégation](https://developers.openai.com/codex/multi-agent), [exécution](https://developers.openai.com/codex/noninteractive), [skills](https://developers.openai.com/codex/skills), [Claude Code : sous-agents](https://code.claude.com/docs/en/sub-agents), [exécution](https://code.claude.com/docs/en/headless), [Pi](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent), [OpenCode : agents](https://opencode.ai/docs/agents/) et [serveur](https://opencode.ai/docs/server/).

Les pertes éventuelles sont explicites :

- Sans délégation, le travail peut être séquentiel, mais une auto-revue ne remplace pas un vérificateur indépendant
- Sans plusieurs familles de modèles, les contextes restent séparés mais la diversité de jugement diminue
- Sans définition d’une persona personnalisée, sa reproduction exacte est impossible ; seule sa mission explicitée dans le skill est conservée
- Sans historique exploitable, les décisions peuvent être reconstruites depuis Git et les artefacts, mais les appels d’outils passés ne sont pas prouvés
- Sans service durable, ni watcher shell ni checkpoint ne réveillent une conversation fermée ; la durée de vie des tâches programmées doit être vérifiée, notamment dans [Claude Code](https://code.claude.com/docs/en/scheduled-tasks)
- Sans runner ou moyen de saisir un secret hors du chat, l’UI peut être préparée mais le déclenchement reste incomplet ; aucune carte native ni réveil ne doit être inventé

Les scripts conservent leurs dépendances propres. Le watcher utilise Bun et GitHub CLI. `orch frontier set --prs <n,...>` utilise GitHub CLI pour valider une chaîne de PR GitHub fournie dans l’ordre ascendant de la pile. Sans `--prs`, la découverte automatique de la pile utilise Graphite (`gt`). `orch` conserve un état de coordination ; il ne lance pas les agents.

Les consignes de PR suivent les agents de revue configurés ou présents, comme Greptile ou CodeRabbit. Aucun fournisseur particulier n’est requis. Sans agent applicable, cette étape est sans objet ; une revue requise mais absente reste à examiner. Voir [le triage des agents de revue](review-bot-triage.md).

Le parseur conserve une compatibilité facultative avec Bugbot et les identifiants d’auteur et de passage reçus depuis GitHub, ainsi que leurs tests. Ce sont des données de protocole externe nécessaires à la reconnaissance des revues, pas des instructions exigeant un éditeur particulier. Les champs de pagination GraphQL restent également inchangés.

Sources officielles consultées le 9 septembre 2026. Cette note explique l’adaptation ; la validation d’une installation exige toujours une exécution réelle des capacités utilisées.

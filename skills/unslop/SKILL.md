---
name: "unslop"
description: "Use when communicating directly with the user or writing and editing documents."
kind: "general"
---

# unslop (english version)

Edit text to remove AI patterns and add human voice.

## Process

1. Scan for the patterns below.
2. Rewrite. Preserve meaning, match intended tone.
3. Add soul (see next section).
4. Self-audit: "What makes this obviously AI generated?" Fix remaining tells.
5. Keep the typography a project or domain skill sets, such as curly apostrophes, « » quotes, or dialogue dashes, over rules 13 and 19.

## Adding soul

Removing patterns is half the job. Sterile, voiceless writing is just as obvious.

- **Have opinions.** React to facts instead of neutrally listing pros and cons.
- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.
- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."
- **Use "I" when it fits.** First person isn't unprofessional.
- **Let some mess in.** Perfect structure looks machine-made.
- **Be specific.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am."

## Patterns to detect and fix

### Content

1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". Cut puffery, state what happened.
2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.
3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.
4. **Promotional language.** "nestled", "vibrant", "breathtaking", "groundbreaking", "renowned", "stunning", "must-visit". Use neutral descriptions.
5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.
6. **Formulaic challenges.** "Despite challenges... continues to thrive." Replace with specific facts.

### Language

7. **AI vocabulary.** Additionally, crucial, delve, enduring, enhance, fostering, garner, interplay, intricate, landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore, vibrant. Replace with plain words.
8. **Fancy ways to say "is".** "serves as", "stands as", "boasts", "features". Just say "is" or "has".
9. **"Not just X, but Y."** State the point directly instead.
10. **Rule of three.** Forcing ideas into groups of three. Use the natural number.
11. **Synonym cycling.** Protagonist, main character, central figure, hero all in one paragraph. Pick one, repeat it.
12. **False ranges.** "from X to Y" where X and Y aren't on a meaningful scale. List topics directly.

### Style

13. **Em dash overuse.** Avoid em dashes entirely. Use periods or commas only (no parentheses, no en dashes, no hyphen-as-dash substitutes). Em dashes are an AI tell, and reaching for parentheses instead just trades one tell for another. If a thought needs separation, end the sentence or use a comma.
14. **Colon overuse.** Colons are fine before a list or example. Not as mid-sentence connectors. "If you're coming from traditional automation: instead of registering event handlers, you describe conditions" adds nothing with the colon. Rewrite to let the point stand on its own without comparison framing. "Describing when the scheduler should fire works best as plain English." Same meaning, no crutch punctuation.
15. **Boldface overuse.** Don't bold every proper noun or acronym.
16. **Inline-header lists.** The tell is a bold label and colon that restates the line: "**Performance:** Performance improved...". Convert those to prose. A bold lead-in that ends in a period, names the item, and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one file.") is fine, not a tell.
17. **Title case headings.** Use sentence case.
18. **Decorative emojis.** Remove from headings and bullets.
19. **Curly quotes.** Replace with straight quotes.

### Communication artifacts

20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.
21. **Cutoff disclaimers.** "While specific details are limited..." Find sources or remove.
22. **Sycophantic tone.** "Great question! You're absolutely right!"

### Filler

23. **Filler phrases.** "In order to" becomes "To". "Due to the fact that" becomes "Because". "It is important to note that" gets deleted.
24. **Excessive hedging.** "could potentially possibly be argued that it might" becomes "may".
25. **Generic conclusions.** "The future looks bright." State specific plans or facts.

### Jargon

26. **Abstract metaphor nouns.** Substrate, wedge, vector, locus, vantage, nexus, primitive (as noun), harness (as metaphor), surface (as in "API surface"), bedrock, scaffolding (as metaphor), modality, paradigm, gold-plating, ratchet (as metaphor), evacuate (for moving code), endgame, north star, flywheel. These read as technical but usually have a plainer concrete word. "Substrate" becomes "base". "Wedge in" becomes "add". "Vector" becomes "way" or "method". "Gold-plating" becomes "more than the job needs". "Ratchet" becomes the mechanism's real name or "a limit that only tightens". "Evacuate" becomes "move out". "Endgame" becomes "the last phase". Pick the concrete word.

### Plain speech

27. **Say what it does, not how it feels.** "the database stays close at hand", "SQL you can read", "types that follow your schema" name a feeling. The fix names the mechanism or a number: "`.toSQL()` returns the exact string sent to the database", "a column rename fails the build". Ask what the sentence tells the reader to do or know, then write that. If you can't restate it as a concrete instruction, fact, or number, cut it. One more check: if the sentence could appear unchanged in another project's docs, it says nothing about this one. Cut it.
28. **Shorten or split dense sentences.** If the reader has to backtrack to parse a sentence, break it in two or drop clauses. One idea per sentence.
29. **Active voice.** Prefer it. Catch "is/are/was/were + past participle" and name the actor: "queries are validated" becomes "the compiler validates queries", "the file is parsed by the loader" becomes "the loader parses the file". Passive is fine only when the actor is unknown or genuinely doesn't matter.
30. **Cut adverbs, or use a stronger verb.** "runs quickly" becomes "is fast" or the number. "significantly improves" becomes the measured delta. An adverb propping up a weak verb means the verb is wrong.
31. **Prefer the plain word.** "utilize" becomes "use", "leverage" becomes "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if". The fancier synonym is rarely clearer.
32. Mannered prose substitutes metaphor and flourish for direct statement. Instead of "a parameter worth varying," the mannered writer produces "a dial worth turning." Instead of "this point still matters," they write "this point earns its keep." The phrases exist to display the writer, not to convey the idea, and readers can tell. That is why mannered prose irritates: it makes the reader work harder so the writer can perform. It is also imprecise. Metaphors
drag in connotations the writer did not choose and cannot control. The fix is to say what you mean. When a literal phrase is available, use it.

---

# unslop-fra (version française)

Édite le texte dans le but de supprimer les patterns AI. et d'ajouter une touche humaine.

## Procédure

1. Repérer dans tout le texte les patterns décrits ci-dessous
2. Réécrire. Conserve le sens et le ton voulu
3. Donne-lui une voix (Regarde la prochaine section)
4. Fais ton propre audit : "Qu'est-ce qui fait que ce texte a clairement été généré par l'AI?" Corrige toute trace.
5. Garde la typographie qu'un projet ou un skill de domaine impose, comme l'apostrophe ’, les guillemets « » ou les tirets de réplique, plutôt que les règles 13 et 19.

## Garder une voix

Supprimer les patterns n'est que la moitié du travail. Une écriture stérile et sans voix est tout aussi évidente.

- **Avoir des opinions** Réagir aux faits plutôt que de lister froidement le pour et le contre.
- **Varie le rythme** Des phrases courtes. Puis d'autres plus longues qui prennent leur temps. Mélange et crée du flow.
- **Reconnaître la complexité** "Impressionnant, mais aussi un peu troublant" vaut mieux que "impressionnant".
- **Utiliser le "je" quand ça convient** La première personne n'est pas moins professionnelle pour autant.
- **Laisser un peu de désordre** Une structure parfaite a l'air fabriquée par une machine.
- **Être précis** Pas "c'est préoccupant", mais "il y a quelque chose de troublant à voir des agents travailler sans relâche à 3 h du matin".

## Tics à repérer et à corriger

### Contenu

1. **Enflure verbale** "moment charnière", "témoignage de", "paysage en évolution", "ouvrir la voie à", "marque indélébile", "profondément ancré". Couper l'enflure, dire ce qui s'est passé.
2. **Listage de noms (Name-dropping)** Énumérer des médias sans contexte. En choisir un, dire ce qui a été dit.
3. **Tournures en "-ant" superficielles (Superficial -ing phrases)** "mettant en lumière...", "assurant...", "reflétant...", "illustrant...", "favorisant...". Supprimer ou développer avec de vraies sources.
4. **Langage promotionnel** "niché", "vibrant", "à couper le souffle", "révolutionnaire", "réputé", "spectaculaire", "incontournable". Utiliser des descriptions neutres.
5. **Attributions vagues** "Les experts estiment", "Selon des rapports du secteur", "Certains critiques soutiennent". Nommer la source ou supprimer.
6. **Formules convenues sur les difficultés** "Malgré les défis... continue de prospérer." Remplacer par des faits précis.

### Langue

7. **Vocabulaire d'IA** De plus, crucial, plonger dans, durable, rehausser, favoriser, susciter, interaction, complexe, paysage (au sens abstrait), charnière, mettre en valeur, tissage (au sens abstrait), témoignage, souligner, vibrant. Remplacer par des mots simples.
8. **Façons chics de dire "est"** "fait office de", "se veut", "se targue de", "propose". Dire simplement "est" ou "a".
9. **"Pas seulement X, mais aussi Y."** Formuler l'idée directement.
10. **Les groupes de trois forcés (Rule of three)** Forcer les idées en groupes de trois. Utiliser le nombre naturel.
11. **Rotation des synonymes** Protagoniste, personnage principal, figure centrale, héros, tous dans le même paragraphe. En choisir un et le répéter.
12. **Formules "de X à Y" sans échelle réelle (False ranges)** Quand X et Y ne sont pas sur une échelle cohérente, lister les sujets directement.

### Style

13. **Abus du tiret cadratin** Éviter le tiret cadratin complètement. Utiliser seulement des points ou des virgules (pas de parenthèses, pas de tiret demi-cadratin, pas de trait d'union en guise de tiret). Le tiret cadratin est une marque d'IA, et se rabattre sur les parenthèses ne fait que troquer une marque pour une autre. Si une idée a besoin d'être séparée, terminer la phrase ou utiliser une virgule.
14. **Abus des deux-points** Les deux-points sont corrects avant une liste ou un exemple. Pas comme connecteur en milieu de phrase. "Si tu viens de l'automatisation traditionnelle : au lieu d'enregistrer des gestionnaires d'événements, tu décris des conditions" n'apporte rien avec les deux-points. Réécrire pour que l'idée tienne seule, sans structure de comparaison. "Décrire quand l'ordonnanceur doit se déclencher fonctionne mieux en langage clair." Même sens, sans béquille de ponctuation.
15. **Abus du gras** Ne pas mettre en gras chaque nom propre ou acronyme. Sois minimaliste.
16. **Listes à en-tête intégré (Inline-header lists)** Le signe révélateur : une étiquette en gras suivie de deux-points qui répète la ligne : "**Performance :** La performance s'est améliorée...". Convertir en prose. Une amorce en gras qui se termine par un point, nomme l'élément, et est suivie d'un détail vraiment nouveau ("**Schéma en TypeScript.** Les tables vivent dans un seul fichier.") est acceptable, ce n'est pas un tic.
17. **Titres en casse de titre** Utiliser la casse de phrase.
18. **Émojis décoratifs** Retirer des titres et des puces.
19. **Guillemets courbes** Remplacer par des guillemets droits "expression".

### Artéfacts de communication

20. **Phrases de chatbot** "J'espère que ça aide !", "N'hésite pas à...", "Bien sûr !", "Certainement !", "Trouvé la preuve irréfutable !" Retirer.
21. **Réserves liées aux limites de connaissances (Cutoff disclaimers)** "Bien que les détails précis soient limités..." Trouver des sources ou retirer.
22. **Ton flagorneur (Sycophantic tone)** "Excellente question ! Tu as tout à fait raison !" Répondre directement.

### Remplissage

23. **Expressions de remplissage** "Afin de" devient "Pour". "En raison du fait que" devient "Parce que". "Il est important de noter que" disparaît.
24. **Réserves excessives (Excessive hedging)** "on pourrait potentiellement possiblement soutenir que ça pourrait" devient "peut".
25. **Conclusions génériques** "L'avenir s'annonce prometteur." Énoncer des plans ou des faits précis.

### Jargon

26. **Métaphores techniques abstraites (Abstract metaphor nouns)** Substrat, wedge, vecteur, locus, vantage, nexus, primitive (comme nom), harness (au sens métaphorique), surface d'API, socle, échafaudage, modalité, paradigme, gold-plating, ratchet (au sens métaphorique), evacuate (pour déplacer du code), endgame, north star, flywheel. Ces termes sont conservés en anglais lorsqu'une traduction déforme le concept, mais ils cachent souvent un mécanisme simple. Remplacer "substrat" par "base", "wedge in" par "ajouter", "vecteur" par "façon" ou "méthode", "gold-plating" par "plus que ce que la tâche exige", "ratchet" par le vrai nom du mécanisme ou "une limite qui ne fait que se resserrer", "evacuate" par "déplacer", "endgame" par "dernière phase", "north star" par "objectif principal" et "flywheel" par le nom réel de la boucle ou du mécanisme. Quand aucun remplacement simple ne convient, nommer directement le mécanisme.

### Discours simple

27. **Dire ce que ça fait, pas l'impression que ça donne** "la base de données reste à portée de main", "du SQL lisible", "des types qui suivent ton schéma" nomment un ressenti. La correction nomme le mécanisme ou un chiffre : "`.toSQL()` retourne la chaîne exacte envoyée à la base de données", "renommer une colonne fait échouer la compilation". Se demander ce que la phrase indique au lecteur de faire ou de savoir, puis écrire ça. Si on ne peut pas la reformuler en instruction, fait ou chiffre concret, la couper. Autre vérification : si la phrase pourrait apparaître telle quelle dans la documentation d'un autre projet, elle ne dit rien de spécifique sur celui-ci. La couper.
28. **Raccourcir ou scinder les phrases denses** Si le lecteur doit revenir en arrière pour comprendre une phrase, la couper en deux ou retirer des propositions. Une idée par phrase.
29. **Voix active** La privilégier. Repérer "est/sont/était/étaient + participe passé" et nommer l'acteur : "les requêtes sont validées" devient "le compilateur valide les requêtes", "le fichier est analysé par le chargeur" devient "le chargeur analyse le fichier". La voix passive convient seulement quand l'acteur est inconnu ou vraiment sans importance.
30. **Couper les adverbes, ou utiliser un verbe plus fort** "fonctionne rapidement" devient "est rapide" ou le chiffre exact. "améliore considérablement" devient l'écart mesuré. Un adverbe qui soutient un verbe faible signifie que le verbe est mal choisi.
31. **Préférer le mot simple** "mettre à profit" devient "utiliser", "faciliter" devient "aider", "nombreux" devient "plusieurs" ou "beaucoup", "dans l'éventualité où" devient "si". Le synonyme plus recherché est rarement plus clair.

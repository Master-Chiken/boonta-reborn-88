# Configuration des outils — Boonta Reborn 88

**Mise à jour : 2026-10-21**

## Décisions et contraintes de travail

- Budget maximal : **0 €**. Ne pas ajouter de moyen de paiement, activer de facturation ni basculer vers un service payant.
- Plateforme principale : **GameCube/Wii**.
- Dépôt public ; conserver les changements dans des branches et des PR contrôlées.
- CI prioritaire : GitHub Actions. Ne pas créer de Codespace ni demander d'installation locale de la chaîne de compilation tant que ce n'est pas nécessaire.
- Les services IA externes sont facultatifs. Ne jamais envoyer de secrets, d'archives commerciales ou de fichiers dont la provenance n'est pas claire à un service externe.

## GitHub Actions — preuve actuelle

La démo clean-room est intégrée sous `gamecube-demo/`. L'exécution [CI #38902484737](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38902484737) a réussi pour les tests de régression hôte, la compilation native devkitPPC/libogc DOL/ELF, le smoke test Dolphin sans interface et le diagnostic Software Renderer.

Cela ne prouve **pas** encore que les commandes sont validées de façon interactive, qu'une course de trois tours a été terminée par un joueur, ni que le comportement a été testé sur matériel réel. Voir [le jalon interactif](NEXT_MILESTONE.md).

- Workflow principal : [GameCube demo build](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml).
- La protection de `main` n'a pas pu être confirmée par l'API utilisée (l'accès à l'endpoint de protection a échoué avec 403). Vérifier manuellement **Settings → Rules → Rulesets** avant d'autoriser toute écriture par un agent ; continuer à utiliser des PR et ne pas forcer de push.
- Le DOL/ELF et les rapports CI sont des preuves de compilation ou de diagnostic, pas une déclaration de jeu terminé.

## Automatisation IA : rester verrouillé par défaut

Les workflows d'assistance sont facultatifs et ne doivent jamais devenir une condition pour faire avancer le projet.

- Le workflow Gemini est gouverné par `.github/workflows/gemini-dispatch.yml`. Les tâches d'écriture doivent rester bloquées tant que le propriétaire n'a pas explicitement activé le verrou de dépôt prévu à cet effet. Ne pas activer ce verrou automatiquement.
- Une clé API est un secret GitHub, jamais un texte à mettre dans une issue, un commit, un fichier suivi ou cette conversation.
- Si un quota gratuit est épuisé, arrêter l'appel concerné et continuer avec les outils GitHub disponibles ; ne pas activer une facturation de secours.
- **OpenRouter Free PR review:** merged into `main` via [PR #251](https://github.com/Master-Chiken/boonta-reborn-88/pull/251). The reviewer is manual-only, owner-only, read-only for code, capped at a 30,000-byte diff, scans for common secret patterns, uses only `openrouter/free`, and has no paid fallback. It appears in Actions; however, do not consider it operational until the owner configures `OPENROUTER_API_KEY` as a repository secret and a manual test succeeds. Do not add credits or a payment method. External model providers receive the selected public diff, so never submit secrets, private data, commercial assets, or unclear-provenance files.
- Les limites, modèles gratuits et conditions de traitement des données changent : vérifier la documentation officielle au moment d'une activation.

## Import Step 102 : blocage explicite

Deux périmètres d'archives ne doivent pas être confondus :

- Le grand ZIP Step 102 audité historiquement (359 fichiers).
- Le bundle source-only de 123 fichiers examiné séparément.

Les audits ont relevé des questions de provenance, l'absence de licence claire dans les archives examinées et des données de piste générées déclarées comme dérivées de ressources tierces. Ces constats ne signifient pas que chaque fichier est inutilisable, mais **interdisent de considérer l'ensemble comme autorisé à publier en bloc**.

- Consulter [l'audit Step 102](STEP102_IMPORT_AUDIT.md), [le registre des sources](SOURCE_AND_ARTIFACT_REGISTER.md), [le contrôle de provenance](STEP102_SOURCE_PROVENANCE.md) et [le contrôle d'import](SOURCE_IMPORT_GATE.md).
- Récupérer les documents, tests et scripts après comparaison et revue, mais garder en quarantaine le code ou les données dont l'origine et les droits ne sont pas établis.
- Les comptes-rendus de tests historiques du bundle ne sont pas des résultats CI actuels et ne remplacent pas une compilation native ou un essai interactif.

## Outils non retenus par défaut

- **Codespaces** : ne pas en créer pour ce projet sans besoin explicite.
- **Installation locale de devkitPPC, Dolphin ou Blender** : non requise pour les vérifications CI actuellement disponibles.
- **Dreamcast/KallistiOS** : piste expérimentale secondaire ; GameCube/Wii reste prioritaire.
- **API Claude payante ou toute API payante** : exclue par la contrainte de budget de 0 €. Les accès gratuits sur leurs sites sont distincts d'une intégration API et ont leurs propres limites.

## Actions restantes

1. Effectuer les tests visuels et de contrôleur de la démo dans un émulateur interactif ou sur matériel quand cet environnement sera disponible.
2. Continuer à récupérer les documents et les tests uniques des branches anciennes dans `main`, sans fusionner leurs anciennes bases de code en bloc.
3. Résoudre la provenance et les droits fichier par fichier avant d'importer du code Step 102 ou des données de piste.
4. Garder les archives commerciales, ROMs, images disque, modèles, textures et audio propriétaires hors du dépôt public et des artefacts CI.

## Documentation officielle

- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- [Gemini API pricing and free tier](https://ai.google.dev/gemini-api/docs/pricing).
- [OpenRouter free router](https://openrouter.ai/openrouter/free/).
- [CodeQL build options](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages).

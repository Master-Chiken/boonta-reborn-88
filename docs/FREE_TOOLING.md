# Configuration des outils — Boonta Reborn 88

## Décisions du propriétaire

- Budget maximal : **0 €**. Aucun moyen de paiement, aucune facturation et aucun service payant.
- Plateforme principale : **GameCube/Wii**.
- Dépôt : public.
- CI et environnement de travail : **GitHub Actions uniquement**. Ne crée pas de Codespace et n'installe pas de chaîne de compilation sur l'ordinateur.
- Agent IA : Gemini API dans l'offre gratuite, avec les conditions de traitement des données de l'offre gratuite Google acceptées.

## Outils actifs

### GitHub Actions — outil central

**État confirmé sur la branche de la PR #13 :** le workflow GameCube compile un DOL, les six suites de tests C de logique de course passent, le contrôle des fichiers ROM/images disque passe et CodeQL a terminé avec succès sur une exécution récente.

- Workflow : [GameCube procedural driving prototype](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-smoke.yml).
- Protection : [Repository safety](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/repository-safety.yml).
- Analyse statique : [CodeQL](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/codeql.yml).
- Artefact : `gamecube/boonta_demo.dol`, conservé sept jours.
- Coût : les runners standards GitHub-hosted sont gratuits et illimités pour les dépôts publics selon la documentation GitHub actuelle. Les politiques peuvent évoluer ; revérifie les limites en cas de changement de plan ou de visibilité.

Le smoke test Dolphin actuel est sans interface : il vérifie que Dolphin accepte le DOL et reste actif 12 secondes. Il ne prouve pas le rendu graphique, les contrôles ni que le jeu est jouable. Il n'existe pas encore de validation interactive sur émulateur ou console.

### Gemini CLI — automatisation facultative, en cours de préparation

Les workflows sont présents, mais l'agent ne doit pas être considéré comme activé tant que le secret n'a pas été configuré et qu'un test n'a pas réussi.

- Modèle : `gemini-3.5-flash-lite`, actuellement listé par Google dans le tableau de l'offre API gratuite.
- Données : Google indique que le contenu envoyé via l'offre gratuite peut être utilisé pour améliorer ses produits. Cela peut inclure le code et les instructions envoyés au modèle.
- Budget : ne rattache aucune facturation, n'ajoute aucune carte et ne passe jamais à un niveau payant. Au quota épuisé, arrête l'agent et poursuis avec les outils GitHub gratuits.
- Secret requis : `GEMINI_API_KEY`.
- Variable de sécurité requise avant toute écriture : `GEMINI_WRITE_ENABLED=true`, uniquement après protection de `main` contre les pushes directs/forcés et la suppression.
- Guide étape par étape : [AI automation setup](AI_AUTOMATION_SETUP.md).

La configuration a un verrou : tant que la variable n'est pas exactement `true`, `@gemini-cli /approve` n'exécute pas la tâche modifiant le dépôt et publie un message expliquant comment l'écriture reste verrouillée. L'agent doit créer une nouvelle branche et une PR. Aucun workflow n'a le droit de fusionner.

### OpenRouter Free — deuxième IA de relecture, prête à activer

- Statut : workflow ajouté, mais il attend le secret privé `OPENROUTER_API_KEY`.
- Usage : relecture technique manuelle d'une PR ouverte qui cible `main`. Le modèle reçoit uniquement le diff public de la PR et renvoie un commentaire d'audit. Il ne possède aucun outil d'écriture dans le dépôt, ne pousse pas de commit et ne peut pas fusionner.
- Route : `openrouter/free`, qui sélectionne un modèle de la liste gratuite. Le routeur annonce un coût de 0 $ pour les requêtes. Si aucune capacité gratuite n'est disponible, la requête doit échouer : ne passe pas à une route payante.
- Offre Free annoncée actuellement : 25+ modèles gratuits et 50 requêtes par jour ; ces limites et les modèles disponibles peuvent changer.
- Données : la requête envoie le diff de la PR à OpenRouter, puis à un fournisseur de modèle qui peut changer. Les pratiques de conservation/entraînement varient selon le fournisseur ; n'utilise pas ce workflow avec une PR contenant des secrets, informations privées ou du contenu que tu ne souhaites pas transmettre à un fournisseur externe.
- Configuration : crée une clé API dans [OpenRouter](https://openrouter.ai/keys), sans ajouter de crédit ni moyen de paiement, puis ajoute-la dans GitHub sous **Settings → Secrets and variables → Actions → New repository secret** avec le nom exact `OPENROUTER_API_KEY`.
- Lancement : ouvre le workflow [OpenRouter free-model PR review](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/openrouter-free-review.yml), clique **Run workflow** et saisis le numéro de la PR. Il ne se déclenche pas automatiquement.

Guide complet : [OpenRouter Free PR review](OPENROUTER_FREE_REVIEW.md).

## Outils non retenus pour cette configuration

- **Codespaces** : configuration présente à titre d'option future, mais non utilisé. Aucun environnement n'a été créé et aucun quota consommé.
- **Installation locale de devkitPPC, Dolphin ou Blender** : inutile pour les vérifications CI actuelles ; ne télécharge pas de gros outils tant que ce n'est pas nécessaire.
- **Dreamcast/KallistiOS** : expérimentation secondaire séparée ; GameCube/Wii reste la priorité.
- **Claude API direct** : non retenu, car l'API Anthropic est facturée à l'usage et ne convient pas à la règle stricte de 0 €. Claude Free / Copilot Free peuvent être utilisés manuellement sur le site GitHub/Claude selon leurs propres limites, mais ce n'est pas une connexion directe de Claude à GitHub Actions.

## Blocage important — import Step 102

Le propriétaire a déclaré l'archive originale/écrite/générée pour le projet. L'audit déjà enregistré dans le dépôt signale toutefois que certains centerlines de circuit proviennent d'un dataset de mod PC et qu'aucun fichier LICENSE/COPYING/NOTICE n'a été trouvé. Cette contradiction doit être résolue fichier par fichier avant publication. Ne copie pas le ZIP complet dans le dépôt public uniquement sur la base d'une étiquette générale de provenance.

Le petit prototype clean-room dans `gamecube/` est distinct du port complet Step 102. Le workflow `.github/workflows/native-build.yml` concerne ce port complet et reste bloqué jusqu'à un import de source soigneusement filtré.

## Actions manuelles restantes

1. **Protéger `main`** via Settings → Rules → Rulesets : exiger une PR avant fusion, bloquer les force-pushes et empêcher la suppression de la branche. Garder l'auto-merge désactivé.
2. Créer une clé gratuite dans [Google AI Studio](https://aistudio.google.com/apikey) sans rattacher de facturation, puis enregistrer la clé sous **Settings → Secrets and variables → Actions → New repository secret** avec le nom exact `GEMINI_API_KEY`. Ne transmets pas la clé dans cette conversation.
3. Après l'activation de la règle de branche et l'ajout du secret, créer la variable d'Actions `GEMINI_WRITE_ENABLED` avec la valeur exacte `true`. Si tu ne fais pas cette étape, Gemini reste en lecture/planification et ne peut pas lancer le workflow d'écriture.
4. Effectuer une vérification visuelle du DOL sur un émulateur ou une console appropriée lorsque tu peux accéder à cet environnement. Le test CI actuel ne valide pas les images ni les commandes.
5. Terminer le manifeste détaillé des 359 fichiers de l'archive Step 102 et résoudre les chemins de provenance en attente avant d'importer les sources autorisées.

## Sources officielles utiles

- [Runners GitHub Actions pour dépôts publics](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- [Gemini API — prix, quota gratuit et conditions d'utilisation des données](https://ai.google.dev/gemini-api/docs/pricing).
- [OpenRouter — tarification de l'offre gratuite](https://openrouter.ai/pricing).
- [OpenRouter — routeur de modèles gratuits](https://openrouter.ai/openrouter/free/).
- [Gemini 3.5 Flash-Lite — fiche modèle](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).
- [CodeQL — options d'analyse](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages).

# Configurer l'automatisation IA de Racer

Cette page décrit les automatismes disponibles dans le dépôt. **Boonta Autonomous peut sélectionner et exécuter une tâche bornée toutes les six heures, avec un seul agent écrivain à la fois et des PR obligatoires. Aucune fusion automatique n'est autorisée.**

## Budget et données

- Budget strict : **0 €**. Aucun compte de facturation, moyen de paiement, modèle payant de secours ou service cloud payant.
- Gemini reste le fournisseur principal. Si son cycle autonome échoue après le lancement du modèle, le workflow peut appeler le writer OpenRouter Free séparé, uniquement avec la route fixe `openrouter/free` et après validation du garde-fou propriétaire `OPENROUTER_FREE_TIER_CONFIRMED=true`. Le reviewer manuel OpenRouter Free reste également disponible. Aucun modèle payant, aucune autre route OpenRouter, aucun achat de crédits ni moyen de paiement n'est autorisé.
- Ne jamais mettre une clé dans un fichier, une issue, un commentaire ou cette conversation. Les clés restent dans les secrets GitHub.
- Ne jamais envoyer à un service IA hébergé les ROMs, images disque, BIOS, archives commerciales, modèles/textures/audio extraits, secrets ou données dont les droits ne sont pas établis.
- Le dépôt est public. Une réussite de tests de configuration ne prouve ni que le quota gratuit est disponible, ni que les comportements de jeu sont corrects.

## Gemini zero-cost gate

Before any Gemini workflow can call a model, the repository Actions variable `GEMINI_FREE_TIER_CONFIRMED` must equal the exact string `true`, and the `GEMINI_API_KEY` secret must exist. If either requirement is missing, the model step is skipped; there is no paid fallback.

**Do not set this variable until you personally verify the project in Google AI Studio.** Open the AI Studio Projects/Billing view and confirm the API-key project is on the **Free** tier and is not linked to a Cloud Billing account. Google documents that API keys inherit the billing tier of their project and that projects linked to a Cloud Billing account inherit the account's usage tier ([official billing documentation](https://ai.google.dev/gemini-api/docs/billing/)). The model has both Free and Paid pricing tiers ([official pricing](https://ai.google.dev/gemini-api/docs/pricing)).

This check is an explicit owner attestation, **not an automated billing-status check**: GitHub Actions cannot establish the billing state through this workflow. If the tier or billing linkage is uncertain, leave the variable absent or set it to anything other than `true`. Do not add a payment method, enable billing, buy credits, or switch to a paid tier. If free quota is unavailable, stop and wait for quota to reset rather than upgrading.

## Boucle autonome Boonta — activation contrôlée

Le workflow [Boonta Autonomous Loop](../.github/workflows/boonta-autonomous-loop.yml) s'exécute toutes les six heures et peut aussi être lancé manuellement par le propriétaire. Le lancement planifié GitHub utilise uniquement le dernier commit de la branche par défaut et peut être retardé en période de charge ; dans les dépôts publics, GitHub désactive automatiquement les workflows planifiés après 60 jours sans activité du dépôt ([documentation officielle](https://docs.github.com/fr/actions/reference/workflows-and-actions/events-that-trigger-workflows)). Le dépôt doit donc rester actif et il faut surveiller l'onglet Actions. Après activation, lance une première exécution manuelle pour valider le cycle immédiatement plutôt que d'attendre le prochain créneau. Il appelle le writer Gemini réutilisable avec le prompt autonome dédié, lit la file canonique #226 et le tableau de bord #156, puis sélectionne ou poursuit une seule tâche. Il doit continuer une PR autonome existante plutôt que créer des doublons, respecter la priorité RE-001 et le ratio de recherche 80/20, et ouvrir une PR sans jamais la fusionner.

Avant d'activer l'agent, le propriétaire peut lancer [Boonta Autonomous Readiness](../.github/workflows/boonta-autonomous-readiness.yml) depuis **Actions → Boonta Autonomous Readiness → Run workflow**. Ce contrôle vérifie la présence des secrets/variables, la création d'un jeton GitHub App avec les permissions attendues, puis l'accès en lecture aux issues #156/#226, aux exécutions Actions et aux références `main`/`dev`. Il ne lance pas Gemini, ne consomme pas de quota API et ne modifie ni le code, ni les issues, ni les PR. **Il exige volontairement que `GEMINI_AUTONOMOUS_ENABLED` soit encore absent ou différent de `true` : la boucle doit rester arrêtée pendant le précontrôle.** Le menu GitHub doit également être réglé sur la branche `main` : le workflow refuse désormais les lancements depuis les autres branches.

Ce précontrôle ne prouve pas que la clé Gemini est valide ou que le projet Google est réellement au Free tier. Il ne peut pas non plus vérifier les rulesets de protection, car le GitHub App n'obtient volontairement aucun droit d'administration. Le propriétaire doit encore vérifier manuellement l'absence de Cloud Billing lié et la protection de `main`/`dev`.

Ordre d'activation recommandé : (1) fusionner la PR #277 ; (2) configurer `GEMINI_FREE_TIER_CONFIRMED=true`, `GEMINI_API_KEY`, `APP_ID` et `APP_PRIVATE_KEY`, en laissant `GEMINI_AUTONOMOUS_ENABLED` désactivé ; (3) vérifier les règles de protection `main`/`dev` ; (4) lancer le précontrôle et exiger son succès ; (5) définir `GEMINI_AUTONOMOUS_ENABLED=true` en dernier ; (6) lancer **Boonta Autonomous Loop** depuis Actions en sélectionnant `main`, puis contrôler la PR et le rapport de cycle.

L'exécution d'écriture reste fermée tant que toutes les conditions suivantes ne sont pas réunies :
- La variable Actions `GEMINI_AUTONOMOUS_ENABLED` vaut exactement `true`.
- `GEMINI_FREE_TIER_CONFIRMED` vaut exactement `true` après vérification personnelle du Free tier et de l'absence de compte Cloud Billing lié.
- Le secret `GEMINI_API_KEY` est configuré.
- La variable `APP_ID` et le secret `APP_PRIVATE_KEY` sont configurés. Le GitHub App doit disposer de `Contents: write`, `Issues: write`, `Pull requests: write` et `Actions: read` : les trois premières permissions permettent de créer des branches/PR et de publier le suivi, la dernière permet à l'agent de lire les exécutions CI et les journaux d'échec.
- Les rulesets `main`/`dev` protègent les branches concernées. L'agent ne reçoit aucun droit de fusion, de modification des paramètres, de force-push ou de suppression.

Le mode autonome ne contourne pas le budget de 0 €. Gemini est essayé en premier ; si son cycle échoue, le writer OpenRouter Free n'est tenté que si sa clé et son attestation propriétaire sont présentes. Si OpenRouter est lui aussi indisponible ou limité, le cycle s'arrête. Aucun modèle, fournisseur ou service payant de secours ne sera utilisé. Une exécution planifiée n'est pas un processus permanent : GitHub Actions démarre un cycle, puis s'arrête. Les cycles suivants reprennent à partir des issues, branches et PR visibles.

Ne pas activer la variable autonome avant d'avoir vérifié les secrets, les règles de branche et les conditions de confidentialité du fournisseur. Le contenu du dépôt public transmis à Gemini peut être traité selon les conditions du Free tier Google.

## Secours autonome OpenRouter Free — après échec Gemini

Le workflow [OpenRouter plan execute](../.github/workflows/openrouter-plan-execute.yml) est appelé automatiquement par [Boonta Autonomous Loop](../.github/workflows/boonta-autonomous-loop.yml) uniquement si le job Gemini a échoué. Il ne possède aucun déclencheur autonome propre. Il réutilise le verrou d'écriture unique, le GitHub App scoped token et le même périmètre d'autorisation : une tâche bornée, une branche et une PR, sans fusion automatique.

**Activation explicite nécessaire dans Settings → Secrets and variables → Actions :**

1. Créer une clé dans [OpenRouter API Keys](https://openrouter.ai/keys) avec le compte Free. Ne pas ajouter de carte, de moyen de paiement ni de crédits. Si OpenRouter exige un paiement, ne pas continuer.
2. Ajouter le secret de dépôt `OPENROUTER_API_KEY`. Ne jamais copier la clé dans le dépôt, une issue, un commentaire ou cette conversation.
3. Ajouter la variable de dépôt `OPENROUTER_FREE_TIER_CONFIRMED=true` seulement après avoir vérifié personnellement que le compte est Free et qu'aucun moyen de paiement/crédit n'est activé. Cette variable est une attestation du propriétaire, pas une vérification automatique du compte.
4. Conserver `GEMINI_AUTONOMOUS_ENABLED=true` comme interrupteur maître de toute écriture autonome. Sans ce verrou, OpenRouter ne peut pas écrire.

Le workflow utilise OpenCode CLI version `1.19.5`, le modèle fixe `openrouter/openrouter/free`, le fournisseur OpenRouter uniquement et le serveur GitHub MCP avec une liste explicite d'outils de lecture, création de branche, envoi de fichiers, création de PR et commentaires. L'exécution shell est bloquée. Les outils de fusion, suppression, administration, secrets et variables ne sont pas exposés. Le modèle ne peut donc pas choisir un modèle payant ou basculer vers un autre fournisseur via cette configuration.

OpenRouter Free reste soumis à ses quotas, à la disponibilité et à la compatibilité des modèles gratuits avec les appels d'outils. Un échec de quota, de routage ou de function-calling arrête le cycle ; il n'entraîne aucun secours payant. Les contenus du dépôt public nécessaires au travail peuvent être transmis à OpenRouter et au fournisseur gratuit sélectionné : ne jamais envoyer de secrets, d'archives commerciales, de ROM/disc/BIOS, de données privées ou d'actifs de provenance incertaine.

Le workflow [Boonta Autonomous Readiness](../.github/workflows/boonta-autonomous-readiness.yml), lancé manuellement depuis `main`, indique aussi si le secret OpenRouter et l'attestation sont présents, sans afficher leurs valeurs et sans appeler l'API. Ce contrôle ne valide ni la clé, ni le compte Free, ni le quota. Le workflow ne peut pas être testé depuis cette conversation sans le secret propriétaire. Après fusion de la PR d'intégration et configuration du secret/de la variable, le prochain échec Gemini permettra de tester la bascule réelle. Contrôler les logs et le head exact de toute PR générée ; aucune fusion automatique n'est activée.

## Relecture de PR via OpenRouter Free — à la demande

Le workflow [OpenRouter Free PR review](../.github/workflows/openrouter-free-review.yml) est présent sur `main` depuis la fusion de [PR #251](https://github.com/Master-Chiken/boonta-reborn-88/pull/251). Il est manuel, réservé au propriétaire du dépôt, transmet au maximum 30 000 octets du diff après un contrôle de motifs de secrets et utilise uniquement `openrouter/free`. Il peut publier un commentaire mais ne peut écrire du code, pousser, créer une PR ou fusionner. Il apparaît dans Actions, mais il ne doit pas être considéré opérationnel tant que `OPENROUTER_API_KEY` n'est pas configuré et qu'un premier lancement réel n'a pas réussi.

Avant un lancement, examiner la PR cible et exclure tout contenu privé ou incertain. Le diff est transmis à OpenRouter puis au fournisseur du modèle sélectionné ; la détection de secrets est indicative, pas exhaustive. Le routeur est gratuit au tarif affiché, avec des quotas susceptibles de changer. En cas d'indisponibilité, le job échoue sans choisir de modèle payant. La clé doit être stockée uniquement comme secret GitHub `OPENROUTER_API_KEY` et aucun crédit/moyen de paiement ne doit être ajouté.

## Registre persistant des tâches autonomes

Le registre canonique est `docs/automation/task-ledger.json`. Il conserve un identifiant stable par tâche, sa file, son périmètre de plateforme, la question à résoudre, les critères d'acceptation, les preuves, le prochain geste et, pour les PR ouvertes, le lien et le SHA exact.

- `queued` : tâche en attente ; `active` : seule tâche actuellement travaillée ; `blocked` : dépendance humaine/externe nommée ; `in_review` : PR ouverte ; `completed` : PR fusionnée et preuves conservées ; `superseded` : tâche remplacée avec justification.
- Une seule tâche peut être `active`. Une PR ouverte ne doit jamais être marquée `completed`. Le registre ne remplace pas GitHub : issues, PR, branches et contrôles CI en direct restent la source de vérité.
- Chaque cycle substantiel met à jour le registre dans la même branche/PR que le travail correspondant. Les cycles suivants peuvent ainsi reprendre sans reconstituer l'historique depuis zéro.
- Le contrôle sans API `python3 tools/check_task_ledger.py` vérifie le format, les identifiants uniques, la limite d'une tâche active et les références exactes des PR. Ses tests de régression sont exécutés par le workflow AI free-tier safety. Le contrôle complémentaire `tools/audit_task_ledger_github.py` utilise uniquement `pull-requests: read` pour vérifier l'état ouvert/fusionné et le SHA réel de chaque PR indexée ; il échoue si le registre est périmé.

## Contrôle statique

Le workflow [AI free-tier safety checks](../.github/workflows/ai-free-safety.yml) exécute \`tools/check_ai_free_safety.py\`. Ce contrôle est local au runner, ne lance aucun modèle, n'utilise aucune clé et vérifie notamment le verrou d'écriture, le budget gratuit et les permissions du coordinateur.

Un contrôle réussi ne remplace pas la revue d'une PR.

## Protection de main avant toute écriture IA

Avant d'envisager l'activation de `GEMINI_WRITE_ENABLED` ou `GEMINI_AUTONOMOUS_ENABLED`, vérifie dans **Settings → Rules → Rulesets** qu'une règle protège `main` et `dev` contre les mises à jour directes, les force-push et la suppression, et qu'une pull request est exigée avant fusion. Ne configure pas de contournement pour un agent IA. Si cette protection n'est pas en place ou ne peut pas être vérifiée, laisse l'écriture IA verrouillée.

## Coordinateur en lecture seule — lancement manuel uniquement

Le workflow [Manual read-only AI project coordinator](../.github/workflows/ai-daily-coordinator.yml) **n'a plus de déclenchement planifié**. Il reste un outil d'audit manuel. La nouvelle boucle autonome est un workflow distinct, avec un writer et des garde-fous séparés.

- Il lit l'état de \`main\`, les issues/PR et les résultats CI.
- Il publie son rapport dans l'issue canonique [#156 — priorité produit](https://github.com/Master-Chiken/boonta-reborn-88/issues/156), pas dans l'ancienne issue #23, qui est fermée.
- Il ne peut pas écrire de code, créer de branche ou de PR, fusionner ou modifier les paramètres. Seul le commentaire final du rapport nécessite \`issues: write\`.
- Le rapport donne une recommandation, pas une autorisation de coder. Il faut examiner la proposition et décider de la prochaine tâche.

Le coordinateur en lecture seule ne produit pas de rapport quotidien automatique. Boonta Autonomous, lui, lance un cycle d'ingénierie borné toutes les six heures lorsque ses variables et secrets de sécurité sont configurés. Aucun rapport IA ne vaut validation du jeu.

## Gemini à la demande

Un commentaire qui commence par \`@gemini-cli\` peut déclencher l'agent de planification en lecture seule. Ce mode peut répondre sur l'issue/PR, mais il ne doit pas modifier le code.

Le chemin de modification est séparé et verrouillé :
- seul le propriétaire peut demander exactement \`@gemini-cli /approve\` ;
- le workflow exige une approbation correspondant au plan explicite et la variable Actions \`GEMINI_WRITE_ENABLED\` exactement égale à \`true\` ;
- il doit créer une branche dédiée puis ouvrir une PR ;
- il ne doit jamais pousser sur \`main\`, fusionner une PR, activer l'auto-merge ou supprimer des branches.

Le chemin manuel reste contrôlé par `GEMINI_WRITE_ENABLED` et la commande d'approbation du propriétaire. Le chemin autonome est contrôlé séparément par `GEMINI_AUTONOMOUS_ENABLED` et la configuration listée ci-dessus. Le propriétaire a autorisé le principe de la sélection automatique des tâches ; l'activation technique reste conditionnée aux protections, secrets et vérifications de gratuité. Un seul agent capable d'écrire doit travailler à la fois.

Je ne peux pas confirmer depuis la connexion de cette conversation la valeur actuelle de cette variable Actions ; elle doit être vérifiée dans les paramètres du dépôt.

## Limites de visibilité

Les workflows voient le contenu GitHub et le contexte de la demande. Ils ne voient pas automatiquement les fichiers téléversés dans la bibliothèque ChatGPT ni les dossiers d'un ordinateur local. N'importe pas l'archive Step 102 en bloc dans le dépôt public : la provenance et la licence doivent être vérifiées fichier par fichier.

Distinguer systématiquement :
- tests hôtes et tests unitaires ;
- compilation native DOL/ELF ;
- smoke test Dolphin sans preuve visuelle ;
- test visuel avec contrôleur émulé ;
- test sur matériel GameCube/Wii réel.

Références : [instructions des agents](../GEMINI.md), [règles de fonctionnement du projet](PROJECT_OPERATING_RULES.md), [priorité et critères d'acceptation](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

[Documentation officielle des tarifs et conditions de données de Gemini API](https://ai.google.dev/gemini-api/docs/pricing)
# Configurer l'automatisation IA de Racer

Cette page décrit les automatismes disponibles dans le dépôt. **La règle de fonctionnement actuelle est volontairement conservatrice : audit à la demande, une seule tâche d'écriture autorisée à la fois, et aucune fusion automatique.**

## Budget et données

- Budget strict : **0 €**. Aucun compte de facturation, moyen de paiement, modèle payant de secours ou service cloud payant.
- Utiliser uniquement le chemin Gemini API explicitement configuré. Si le quota gratuit est épuisé ou que l'outil réclame une facturation, arrêter.
- Ne jamais mettre une clé dans un fichier, une issue, un commentaire ou cette conversation. Les clés restent dans les secrets GitHub.
- Ne jamais envoyer à un service IA hébergé les ROMs, images disque, BIOS, archives commerciales, modèles/textures/audio extraits, secrets ou données dont les droits ne sont pas établis.
- Le dépôt est public. Une réussite de tests de configuration ne prouve ni que le quota gratuit est disponible, ni que les comportements de jeu sont corrects.

## Contrôle statique

Le workflow [AI free-tier safety checks](../.github/workflows/ai-free-safety.yml) exécute \`tools/check_ai_free_safety.py\`. Ce contrôle est local au runner, ne lance aucun modèle, n'utilise aucune clé et vérifie notamment le verrou d'écriture, le budget gratuit et les permissions du coordinateur.

Un contrôle réussi ne remplace pas la revue d'une PR.

## Protection de main avant toute écriture IA

Avant d'envisager l'activation de `GEMINI_WRITE_ENABLED`, vérifie dans **Settings → Rules → Rulesets** qu'une règle protège `main` contre les mises à jour directes, les force-push et la suppression, et qu'une pull request est exigée avant fusion. Ne configure pas de contournement pour un agent IA. Si cette protection n'est pas en place ou ne peut pas être vérifiée, laisse l'écriture IA verrouillée.

## Coordinateur en lecture seule — lancement manuel uniquement

Le workflow [Manual read-only AI project coordinator](../.github/workflows/ai-daily-coordinator.yml) **n'a plus de déclenchement planifié**. Il ne consomme le quota Gemini que lorsque le propriétaire clique volontairement sur **Actions → Manual read-only AI project coordinator → Run workflow**.

- Il lit l'état de \`main\`, les issues/PR et les résultats CI.
- Il publie son rapport dans l'issue canonique [#156 — priorité produit](https://github.com/Master-Chiken/boonta-reborn-88/issues/156), pas dans l'ancienne issue #23, qui est fermée.
- Il ne peut pas écrire de code, créer de branche ou de PR, fusionner ou modifier les paramètres. Seul le commentaire final du rapport nécessite \`issues: write\`.
- Le rapport donne une recommandation, pas une autorisation de coder. Il faut examiner la proposition et décider de la prochaine tâche.

Il n'y a plus de rapport IA quotidien automatique. Aucun rapport ne doit être considéré comme un contrôle d'avancement de fond ou comme une validation de jeu.

## Gemini à la demande

Un commentaire qui commence par \`@gemini-cli\` peut déclencher l'agent de planification en lecture seule. Ce mode peut répondre sur l'issue/PR, mais il ne doit pas modifier le code.

Le chemin de modification est séparé et verrouillé :
- seul le propriétaire peut demander exactement \`@gemini-cli /approve\` ;
- le workflow exige une approbation correspondant au plan explicite et la variable Actions \`GEMINI_WRITE_ENABLED\` exactement égale à \`true\` ;
- il doit créer une branche dédiée puis ouvrir une PR ;
- il ne doit jamais pousser sur \`main\`, fusionner une PR, activer l'auto-merge ou supprimer des branches.

**Règle de gestion actuelle : laisse \`GEMINI_WRITE_ENABLED\` absent ou différent de \`true\` pendant que nous finissons les PR existantes et la validation Dolphin.** Ne l'active que pour une tâche précise, après revue du plan et décision explicite du propriétaire. Un seul agent capable d'écrire doit travailler à la fois.

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
# Configurer l'agent Gemini dans GitHub Actions

Cette configuration permet de demander à Gemini d'auditer le dépôt, proposer un plan et, après approbation humaine et déverrouillage explicite, préparer une pull request. Elle n'exige aucune installation sur ton ordinateur.

## Avant toute activation

**La règle du projet reste 0 € : aucun moyen de paiement, aucune facturation et aucun modèle payant de secours.**

1. Ouvre [les règles du dépôt](https://github.com/Master-Chiken/boonta-reborn-88/settings/rules).
2. Crée un *branch ruleset* ciblant `main`.
3. Active au minimum **Require a pull request before merging**, **Block force pushes** et **Restrict deletions**. Ne configure aucun contournement pour le bot. Enregistre et vérifie la règle.
4. N'active pas l'auto-merge.

Si les règles ne peuvent pas être enregistrées, n'ouvre pas l'écriture Gemini. Garde la variable `GEMINI_WRITE_ENABLED` absente ou différente de `true`.

## Ajouter la clé Gemini API gratuite

1. Ouvre [Google AI Studio — clés API](https://aistudio.google.com/apikey).
2. Crée une clé pour la Gemini API. Vérifie qu'elle fonctionne sur l'offre gratuite **sans compte de facturation ni moyen de paiement rattaché**. Si Google exige une facturation, arrête-toi.
3. Dans le dépôt GitHub, va dans **Settings → Secrets and variables → Actions → New repository secret**.
4. Nom exact : `GEMINI_API_KEY`. Colle la clé uniquement dans la valeur du secret.

Ne mets jamais la clé dans un fichier, une issue, un commentaire ou cette conversation. Les quotas gratuits peuvent évoluer ; lorsqu'ils sont épuisés, le workflow doit s'arrêter plutôt que de payer.

Google indique que le contenu de l'offre API gratuite peut être utilisé pour améliorer ses produits. Cela peut inclure le code et les prompts du dépôt. Ne fournis jamais de secrets, données privées ou contenus que tu n'as pas le droit de transmettre.

## Contrôle automatique de la configuration

Le workflow [AI free-tier safety checks](../.github/workflows/ai-free-safety.yml) se lance à chaque mise à jour de cette branche de sécurité. Il vérifie localement que le verrou d'écriture, le mode lecture seule et les interdictions de routes Google Cloud/Vertex sont toujours présents.

Ce contrôle :
- n'appelle aucune API d'IA et n'utilise aucune clé ;
- ne consomme aucun quota Gemini ou OpenRouter ;
- ne modifie pas le dépôt et ne fusionne rien ;
- vérifie seulement la configuration écrite, pas la disponibilité du quota gratuit auprès du fournisseur.

Un test réussi ne remplace pas la revue humaine de la pull request.

## Premier test : lecture seule

Après validation et fusion explicite de cette PR de sécurité, et après l'ajout du secret, ouvre la [PR #13](https://github.com/Master-Chiken/boonta-reborn-88/pull/13) et écris ce commentaire :

```text
@gemini-cli Fais un audit en lecture seule. Inspecte uniquement les fichiers présents dans la branche actuelle, résume les workflows et résultats CI, identifie les sources réellement disponibles et les prochaines étapes. Ne modifie aucun fichier, ne crée aucune branche et ne crée aucune PR.
```

Consulte ensuite l'onglet [GitHub Actions](https://github.com/Master-Chiken/boonta-reborn-88/actions) et vérifie la réponse. Une réponse réussie de Gemini ne prouve pas que le jeu compile ni qu'il fonctionne.

## Déverrouiller l'écriture — étape séparée

Ne fais cette étape **qu'après** protection de `main` et vérification de `GEMINI_API_KEY`.

1. Ouvre **Settings → Secrets and variables → Actions → Variables → New repository variable**.
2. Nom : `GEMINI_WRITE_ENABLED`.
3. Valeur exacte : `true`.

Sans cette variable, le commentaire `@gemini-cli /approve` n'exécute pas de modifications. Une fois déverrouillé, Gemini doit vérifier le plan approuvé, travailler sur une branche séparée et ouvrir une PR. Il ne doit jamais pousser directement vers `main`, fusionner une PR ou activer l'auto-merge.

## Limites du dépôt et des fichiers

- Les workflows voient le dépôt GitHub et le contexte de la discussion déclenchante. Ils ne voient pas automatiquement les archives téléversées dans ChatGPT ni les dossiers de ton Mac.
- Le grand ZIP Step 102 n'est pas automatiquement accessible à GitHub Actions. N'importe pas ce ZIP en bloc dans le dépôt public ; commence par examiner les sources et données séparément.
- Inspecte la branche réellement utilisée. Ne suppose pas qu'un fichier proposé dans une PR en brouillon se trouve déjà sur `main`.
- Distingue tests hôtes, compilation native DOL, smoke test Dolphin sans interface et validation visuelle/contrôleur.

## Source officielle

[Prix, quotas et conditions de données de Gemini API](https://ai.google.dev/gemini-api/docs/pricing)

Si une étape nécessite une carte, une facturation ou une mise à niveau payante, ne la réalise pas.

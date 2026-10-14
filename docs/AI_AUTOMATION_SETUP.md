# Activer l'agent IA Gemini dans GitHub

Cette intégration permet de demander à Gemini d'inspecter le dépôt, proposer un plan, puis préparer des changements depuis GitHub Actions. Elle ne nécessite aucune installation sur ton ordinateur et ne se lance que lorsqu'un collaborateur autorisé écrit un commentaire commençant par `@gemini-cli`.

## 1. Préparer la clé API

1. Ouvre [Google AI Studio — clés API](https://aistudio.google.com/apikey) et crée une clé pour Gemini.
2. Dans le dépôt GitHub, ouvre **Settings → Secrets and variables → Actions → New repository secret**.
3. Nom du secret : `GEMINI_API_KEY`. Colle la clé dans la valeur, puis enregistre.

**Ne publie jamais la clé dans un fichier, une issue, un commentaire GitHub ou cette conversation.** Google AI Studio propose des quotas gratuits selon le modèle et le compte, mais ils sont limités et peuvent évoluer. Vérifie les quotas et la facturation affichés par Google; l'utilisation au-delà des limites gratuites peut nécessiter une facturation. Cette intégration n'exécute pas de tâches IA à chaque commit: elle attend une demande explicite.

## 2. Utilisation

Après que les fichiers de workflow de cette proposition sont intégrés à la branche par défaut `main`, écris un commentaire sur une issue ou une pull request. Le commentaire doit commencer par `@gemini-cli`. Exemple:

```text
@gemini-cli Inspecte le dépôt tel qu'il existe. Distingue le prototype GameCube/Wii, le jeu PC original et la version N64. Dresse la liste des sources réellement présentes et absentes; propose un plan sûr pour avancer. Ne modifie aucun fichier et n'affirme pas avoir accès aux archives PC/N64 partagées dans ChatGPT.
```

Pour une tâche de code, l'agent doit publier un plan. Lis-le. Pour l'autoriser à exécuter ce plan, réponds ensuite par:

```text
@gemini-cli /approve
```

L'agent peut alors préparer les changements via les outils GitHub disponibles. Contrôle les commits et les pull requests qu'il crée avant de les intégrer. Seuls le propriétaire, les membres et les collaborateurs reconnus du dépôt peuvent déclencher cet agent avec un commentaire autorisé.

## 3. Limites importantes pour Boonta Reborn 88

- L'agent s'exécute dans GitHub Actions et ne voit que le dépôt et le contexte GitHub associé. Il ne peut pas lire automatiquement les fichiers de la bibliothèque ChatGPT.
- La source Step 102 n'est pas encore importée dans le dépôt au moment de la rédaction de ce guide. Tant qu'elle est absente, Gemini peut travailler sur la documentation, les outils et le pipeline, mais il ne peut pas construire honnêtement le prototype natif manquant.
- Le jeu PC original et le fichier N64 `.z64` restent des références séparées. Ne pousse jamais les ROM, ISO, WBFS, BIOS, modèles, textures ou sons commerciaux dans le dépôt public. Vérifie la provenance et les droits avant de partager des données extraites.
- Un test Python côté hôte ne prouve pas qu'un exécutable GameCube/Wii fonctionne. Exige des logs de CI et une validation Dolphin réelle avant de déclarer le build ou le jeu fonctionnel.

## Référence technique

L'action s'appuie sur le projet officiel [google-github-actions/run-gemini-cli](https://github.com/google-github-actions/run-gemini-cli). Le workflow est déclenché à la demande, et non sur chaque push. Si un run échoue, consulte l'onglet **Actions** du dépôt et ne partage jamais la clé API dans les logs ou commentaires.


## Keep the setup on the free tier

The workflows are configured to request `gemini-3.6-flash`. Google's current official pricing page lists free-tier input and output for this model. Free access has quotas and rate limits, and Google can change availability or pricing. A recent test with `gemini-3.8-flash` returned HTTP 503 due to high demand, so this repository uses the available `gemini-3.6-flash` model for the next test. To avoid paid usage, do not link a billing account or upgrade the project. If the free quota is unavailable or exhausted, a run may fail rather than charge for usage. Check the [official pricing page](https://ai.google.dev/gemini-api/docs/pricing) and [rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits) before changing models or billing settings.

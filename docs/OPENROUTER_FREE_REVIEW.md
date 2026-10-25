# OpenRouter Free — relecture manuelle des pull requests

**État actuel :** le workflow a été fusionné dans `main` via [PR #251](https://github.com/Master-Chiken/boonta-reborn-88/pull/251) le 21 octobre 2026. Il est disponible dans GitHub Actions, mais son fonctionnement réel n'est pas encore confirmé : le secret `OPENROUTER_API_KEY` doit être configuré et un premier lancement manuel doit réussir.

## Ce que fait le workflow

Le fichier `.github/workflows/openrouter-free-review.yml` prépare une deuxième opinion IA, à la demande seulement.

- Le propriétaire choisit le numéro d'une PR ouverte qui cible `main` et provient du même dépôt.
- Le workflow transmet au maximum les 30 000 premiers octets du diff public, après un contrôle de motifs courants de clés et de secrets.
- La requête fixe le modèle-routeur `openrouter/free`. Il choisit parmi les modèles gratuits disponibles ; le modèle précis peut varier.
- La clé `OPENROUTER_API_KEY` n'est disponible que dans l'étape qui appelle l'API ; l'étape préalable télécharge, tronque et analyse le diff sans exposer la clé.
- Le résultat est publié en commentaire GitHub. Le workflow ne peut pas modifier le code, pousser une branche, créer une PR ou fusionner.
- Le contrôle statique du dépôt autorise les références OpenRouter dans ce seul workflow et vérifie ses protections. Les autres workflows ne peuvent pas appeler OpenRouter.

## Coût et limites

La documentation officielle affiche actuellement le routeur `openrouter/free` à 0 $ par token et l'offre Free avec un quota annoncé de 50 requêtes par jour. Les modèles disponibles, quotas et conditions peuvent changer. **En cas d'erreur ou de quota épuisé, le workflow s'arrête ; il n'essaie aucun modèle payant en secours.** N'achète pas de crédits et n'ajoute aucun moyen de paiement.

## Données et limites du contrôle

Le diff est transmis à OpenRouter puis au fournisseur du modèle choisi. La vérification de secrets ne reconnaît que certains formats courants et ne peut pas garantir qu'un diff est dépourvu de toute donnée sensible. Avant de lancer le workflow, vérifie la PR toi-même. Ne l'utilise jamais sur du contenu privé, des données personnelles, des secrets, des archives commerciales, des ROMs/images disque/BIOS, des ressources extraites ou des fichiers dont les droits ou la provenance ne sont pas établis.

Le résultat IA est une suggestion de revue, pas la preuve d'un bug ou d'une correction. Le modèle n'exécute pas le jeu et ne peut pas prétendre avoir lancé les tests.

## Terminer l'activation

1. Dans [OpenRouter — clés API](https://openrouter.ai/keys), créer une clé pour l'accès gratuit. Ne pas acheter de crédits et ne pas ajouter de carte ou autre moyen de paiement. Si l'interface impose un paiement, arrêter.
2. Dans GitHub, ouvrir **Settings → Secrets and variables → Actions → New repository secret**, avec le nom exact `OPENROUTER_API_KEY`. La clé doit rester dans la valeur du secret, jamais dans un fichier, une issue, un commentaire ou cette conversation.
3. Ouvrir [Actions — OpenRouter Free PR review](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/openrouter-free-review.yml), choisir **Run workflow**, saisir le numéro d'une PR ouverte qui ne contient aucun contenu privé ou de provenance incertaine, puis lancer l'analyse.
4. Vérifier que le job réussit et publie un commentaire sur la bonne PR. Si la clé, le quota gratuit ou l'API échoue, arrêter ; aucun modèle payant de secours n'est prévu.

Le lancement est manuel et n'implique aucune activité en arrière-plan. **Le workflow a été fusionné, mais l'activation reste à confirmer par un premier lancement réussi.**

## Références officielles

- [Tarifs et limites OpenRouter](https://openrouter.ai/pricing)
- [Routeur officiel des modèles gratuits](https://openrouter.ai/openrouter/free/)
- [Exécution manuelle d'un workflow GitHub Actions](https://docs.github.com/fr/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)

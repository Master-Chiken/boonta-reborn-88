# Développement cloud — option non retenue actuellement

Le dépôt conserve une configuration de Codespaces pour un éventuel développement dans le navigateur. Pour ce projet, le propriétaire a choisi **GitHub Actions uniquement** : ne crée pas de Codespace, ne démarre pas de machine cloud interactive et n'installe rien localement pour compiler.

## Outil actif

Utilise plutôt [GitHub Actions](https://github.com/Master-Chiken/boonta-reborn-88/actions). Le workflow **GameCube procedural driving prototype** compile `gamecube/boonta_demo.dol`, exécute les six suites de tests hôtes et fait une tentative de lancement Dolphin sans interface pendant 12 secondes. L'artefact est conservé sept jours.

## Si le choix change plus tard

La configuration `.devcontainer/devcontainer.json` est un point de départ, pas un service actuellement activé. Codespaces a des quotas mensuels limités sur les comptes personnels gratuits. Ne l'utilise pas sans décision explicite et sans vérifier le quota restant. Ne relie jamais de facturation ni n'ajoute de moyen de paiement pour ce projet.

Un build local optionnel dans cet environnement suivrait :

```sh
cd gamecube
make clean
make
```

Le fichier attendu est `boonta_demo.dol`, pas `boonta_smoke.dol`. Un build réussi ne valide pas le rendu, les commandes ni la jouabilité.

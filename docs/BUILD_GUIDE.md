# Guide de compilation — GameCube/Wii

## État actuel

Le dépôt possède un premier prototype procédural clean-room dans `gamecube/`. La compilation native de ce petit échantillon est vérifiée dans GitHub Actions ; cela ne signifie pas que le port complet Step 102 est compilé ou que le jeu est jouable.

- Exécutable produit : `gamecube/boonta_demo.dol`.
- Chaîne de compilation : devkitPPC/libogc dans un conteneur GitHub Actions, sans installation locale.
- Tests hôtes : six suites de tests C portant sur la remise à zéro, l'accélération/freinage/plafond de vitesse, les limites de voie, le boost/chaleur/recharge, la pause/remise à zéro et la fin après trois tours.
- Smoke test Dolphin : le workflow a lancé le DOL en mode sans interface pendant 12 secondes et le processus est resté actif jusqu'au délai d'arrêt. C'est un contrôle de processus seulement, pas une validation de rendu, de commandes ou de gameplay.
- Rétention de l'artefact : 7 jours.

## Lancer les vérifications sans installer d'outils

Ouvre la page [GitHub Actions](https://github.com/Master-Chiken/boonta-reborn-88/actions), puis le workflow **GameCube procedural driving prototype**. Le workflow compile le DOL, exécute les tests hôtes et effectue le smoke test Dolphin. Les runners standard du dépôt public sont gratuits selon les conditions actuelles de GitHub.

Les binaires de compilation ne sont pas commités dans Git : télécharge le DOL depuis l'artefact Actions si tu dois le tester dans un émulateur ou sur du matériel compatible. Aucun espace disque local supplémentaire n'est nécessaire pour la compilation automatique.

## Tests enregistrés

| Validation | Preuve actuelle | Ce que cela établit | Ce que cela n'établit pas |
|---|---|---|---|
| Compilation GameCube | [GitHub Actions](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-smoke.yml) | Un DOL non vide est produit par devkitPPC/libogc | Pas le fonctionnement complet du jeu |
| Logique de course hôte | Même workflow | Les six suites compilent avec `-Wall -Wextra -Werror` et passent | Pas le rendu GX ni l'exécution sur console |
| Smoke test Dolphin | Même workflow | Dolphin accepte le DOL et reste actif 12 secondes en mode sans interface | Pas de preuve visuelle, de contrôles ou de partie jouable |
| Sécurité du dépôt | [Repository safety](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/repository-safety.yml) | Les extensions courantes de ROM/images disque interdites sont rejetées | Pas une détection parfaite de tout payload possible |
| CodeQL C/C++ | [CodeQL](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/codeql.yml) | Analyse statique C/C++ sans compilation | N'est pas un test runtime |

## Port complet Step 102 — toujours bloqué

Le workflow racine `.github/workflows/native-build.yml` vise le prototype complet et attend une structure `source/` et un `Makefile` racine. Cette structure n'a pas encore été importée comme source de port complet. N'importe pas le ZIP entier dans le dépôt public sur la seule base de la déclaration générale de provenance : l'audit du ZIP identifie des données de piste dérivées d'un mod PC et aucune licence explicite. Résous la provenance de chaque fichier concerné et garde les assets commerciaux/incertains hors du dépôt.

## Politique de compilation

- Aucun ROM, ISO, WBFS, BIOS ou payload commercial dans GitHub.
- Pas d'outil local requis pour les contrôles CI.
- Le projet reste à 0 € : ne configure jamais une facturation ou une méthode de paiement pour continuer.
- Distingue toujours compilation, tests hôtes, lancement Dolphin, rendu/commandes et gameplay complet.

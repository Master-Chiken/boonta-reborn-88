# Workflow d'agent IA

La cible principale est un prototype natif GameCube/Wii. Le projet dispose d'un petit échantillon clean-room dans `gamecube/`; l'expérience Dreamcast/KallistiOS reste séparée. La branche publique ne doit recevoir que du contenu dont la provenance est acceptable.

## Automatisation actuelle

- `@gemini-cli` déclenche une action à la demande, pour les membres autorisés du dépôt.
- Le workflow de lecture utilise le secret `GEMINI_API_KEY` et le modèle `gemini-3.5-flash-lite`, listé actuellement dans l'offre gratuite de Google. Le secret n'est pas encore configuré par défaut et l'agent n'est pas considéré comme connecté avant un test réussi.
- Les réponses sont publiées sur l'issue ou la PR de départ. Un test réussi de Gemini prouve seulement que l'automatisation a répondu ; il ne prouve pas qu'un build ou le jeu fonctionne.
- L'exécution qui peut modifier le dépôt est verrouillée tant que la variable Actions `GEMINI_WRITE_ENABLED` n'est pas exactement `true`.
- La variable d'écriture ne doit être définie qu'après protection de `main` contre les pushes directs/forcés et les suppressions. Chaque changement de l'agent doit créer une nouvelle branche et une PR ; aucun workflow n'est autorisé à fusionner.

## Utilisation recommandée

1. Demande d'abord un audit en lecture seule commençant par `@gemini-cli`.
2. Pour une tâche complexe, demande un plan d'action avec critères d'acceptation et fichiers concernés.
3. Lis le plan ; l'approbation se fait par commentaire `@gemini-cli /approve`.
4. Vérifie le diff, les tests, les risques de provenance et la PR créée.
5. Décide manuellement si la PR peut être fusionnée. Ne configure pas l'auto-merge.

## Build et source Step 102

- `gamecube/` contient un prototype procédural original minimal qui compile en `boonta_demo.dol` grâce à `.github/workflows/gamecube-smoke.yml`. Le workflow lance aussi les tests hôtes de logique de course et une tentative de lancement de 12 secondes dans Dolphin en mode sans interface. Cette dernière vérifie seulement que le processus accepte le DOL et reste actif ; elle ne prouve pas l'affichage, les commandes ou une partie jouable.
- Le workflow séparé `.github/workflows/native-build.yml` est destiné au port complet à partir de l'archive Step 102. Il attend la structure source racine et échoue tant que le source complet n'a pas été importé et nettoyé.
- L'archive Step 102 n'est pas importée en bloc. Le propriétaire a déclaré sa provenance originale/générée pour le projet, mais l'audit existant signale un dataset de centreline dérivé d'un mod PC et aucune licence explicite. Il faut résoudre ces éléments fichier par fichier avant import public.

## Règles de sécurité

- Aucun ROM, ISO, WBFS, BIOS ou payload commercial dans le dépôt public.
- Ne jamais inventer un fichier, une source consultée, un résultat de compilation ou de test.
- Ne jamais désactiver les tests pour obtenir un résultat vert.
- Ne jamais modifier `main` directement, fusionner une PR ou activer l'auto-merge.
- Ne jamais envoyer de secret ou d'information privée à Gemini. Google indique que les contenus de l'offre API gratuite peuvent être utilisés pour améliorer ses produits.

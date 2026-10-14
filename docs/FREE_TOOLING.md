# Outils gratuits pour Boonta Reborn 88

**Règle du projet : zéro dépense.** N'ajoute pas de moyen de paiement, n'active pas une facturation et ne lance pas un service qui exige un forfait payant. Les offres gratuites ont des quotas qui peuvent changer. Si un quota gratuit est épuisé, on s'arrête plutôt que de payer.

## Déjà prêts dans le dépôt

### GitHub Actions — compilation et sécurité
- État : configuré et utilisé; le prototype GameCube procédural compile avec succès en un DOL non vide.
- Usage : compiler le prototype, sauvegarder le DOL comme artefact temporaire, contrôler les extensions ROM/disque interdites et lancer CodeQL sur le C/C++.
- Coût : les runners standard GitHub-hosted sont gratuits et illimités pour les dépôts publics, selon la documentation GitHub. Les artefacts de compilation sont conservés seulement 7 jours pour limiter le stockage.
- Ouvrir : [Actions](https://github.com/Master-Chiken/boonta-reborn-88/actions).

### GitHub Codespaces — environnement de développement dans le navigateur
- État : fichier de configuration et guide présents; aucun Codespace n'est créé automatiquement.
- Usage : éditer le C et compiler avec devkitPPC/libogc dans le cloud, sans installer cette chaîne sur l'ordinateur.
- Quota public actuel de compte personnel Free : 120 heures-cœur et 15 Go-mois de stockage par mois. Une machine à 2 cœurs consomme 2 heures-cœur par heure de fonctionnement. Une fois le quota épuisé, GitHub bloque l'utilisation qui engendrerait des frais si aucun moyen de paiement n'est ajouté.
- À faire une seule fois par le propriétaire : ouvrir le dépôt, sélectionner la branche `audit/step102-import-gate`, choisir **Code → Codespaces → Create codespace**. Arrêter le Codespace après utilisation.
- Guide : [Cloud development workflow](CLOUD_DEV_WORKFLOW.md).

### Gemini CLI sur GitHub Actions — agent IA de dépôt
- État : les workflows à la demande sont dans le dépôt; ils ne fonctionneront pas tant que le secret n'est pas configuré.
- Usage : audit du dépôt, planification de petites tâches, commentaires sur les issues/PR et proposition de modifications après approbation.
- Coût : la clé API doit rester dans l'offre gratuite de Google AI Studio et dans son quota. **Ne pas rattacher de facturation ni passer à une offre payante.** Les modèles et quotas gratuits peuvent changer ou être temporairement indisponibles. Au quota épuisé, attendre le renouvellement au lieu de payer.
- Action nécessaire : dans [Google AI Studio](https://aistudio.google.com/apikey), créer une clé API gratuite, puis dans le dépôt ouvrir **Settings → Secrets and variables → Actions → New repository secret**, nommer le secret `GEMINI_API_KEY` et y coller la clé. Ne jamais mettre la clé dans un fichier, une issue ou un commentaire.
- Guide de configuration : [AI automation setup](AI_AUTOMATION_SETUP.md).
- Sécurité : les demandes substantielles doivent produire un plan; une personne doit approuver le plan explicitement par `@gemini-cli /approve`. Lire le diff et les tests avant toute fusion.

## Outils gratuits que tu peux utiliser en complément

### GitHub Copilot Free
[Page officielle](https://github.com/features/copilot) — forfait gratuit sans carte bancaire, avec un quota limité de complétion de code et des demandes d'IA. Utile si, plus tard, tu édites toi-même le code dans un éditeur. Ce n'est pas indispensable pour nous : l'agent Gemini du dépôt est mieux adapté aux tâches par commentaires GitHub.

### Gemini CLI en connexion personnelle
[Projet officiel](https://github.com/google-gemini/gemini-cli) — agent open source utilisable avec un compte Google et un quota gratuit selon les modalités affichées par Google. Intéressant dans le Codespace, mais cette connexion interactive doit être autorisée par toi; elle ne donne pas automatiquement des identifiants à GitHub Actions.

### Dolphin Emulator
[Site officiel](https://dolphin-emu.org/) — gratuit et open source. Il servira à lancer le DOL et vérifier le démarrage, l'image et les contrôles. Il n'est pas encore configuré dans la CI; il faudra valider une méthode automatisable avant de faire dépendre les builds de l'émulateur. Il peut s'installer sur un ordinateur plus tard, mais ce n'est pas nécessaire à ce stade.

### Blender — création d'assets originaux
[Site officiel](https://www.blender.org/) — gratuit et open source pour créer de nouveaux véhicules, décors et éléments 3D. On attend que le prototype jouable existe avant de télécharger ce gros logiciel; avec ton espace disque limité, nous ne devons pas en faire une dépendance actuelle.

## Ce que nous n'utiliserons pas pour le cœur du projet
- Services IA qui demandent un abonnement, des crédits payants ou une carte bancaire.
- Outils de génération d'assets qui n'autorisent pas clairement l'usage et l'export des créations nécessaires.
- Un moteur généraliste qui ne peut pas produire un exécutable natif GameCube/Wii simplement parce qu'il sait exporter pour PC.
- Des ROM, des images disque ou des ressources commerciales dans le dépôt public.

## Priorités techniques
1. Continuer à compiler le diagnostic GameCube sur Actions.
2. Importer dans une branche séparée uniquement le code source Step 102 dont la licence et la provenance sont acceptables.
3. Exécuter les tests hôtes du prototype en CI.
4. Produire un DOL du prototype réel.
5. Tester séparément son démarrage dans Dolphin.
6. Une fois le jeu lançable, travailler le premier circuit et le véhicule.

## Références officielles des quotas
- [GitHub Actions : utilisation gratuite des runners standard pour les dépôts publics](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- [GitHub Codespaces : quotas inclus des comptes personnels](https://docs.github.com/en/codespaces/keeping-your-codespaces-lean/managing-the-cost-of-codespaces).
- [Gemini API : offre gratuite et tarifs](https://ai.google.dev/gemini-api/docs/pricing).


### CodeQL — analyse statique du C/C++
- État : workflow ajouté; première exécution en cours/vérification.
- Usage : repérer certaines classes de vulnérabilités et problèmes de code sans exécuter le jeu.
- Coût : gratuit pour les dépôts publics GitHub.
- Limite : l'analyse sans build est moins précise que l'analyse sur la compilation réelle; elle ne prouve ni la compilation native ni le bon fonctionnement du jeu.
- Référence : [CodeQL sur les langages compilés](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages).

# Configurer l'agent Gemini sur GitHub Actions

Cette intégration est facultative et déclenchée uniquement par des commentaires GitHub autorisés commençant par `@gemini-cli`. Elle n'exige aucune installation locale. La clé ne doit jamais être envoyée dans une issue, un commentaire, un commit ou cette conversation.

## Sécurité avant activation de l'écriture

**Ne définis pas encore `GEMINI_WRITE_ENABLED=true` tant que la branche `main` n'est pas protégée.** C'est une protection supplémentaire : GitHub Actions n'est pas autorisé à écrire via le workflow d'exécution tant que cette variable n'est pas exactement `true`.

1. Ouvre [les règles du dépôt](https://github.com/Master-Chiken/boonta-reborn-88/settings/rules).
2. Crée un nouveau *branch ruleset* appliqué à `main`.
3. Active au minimum **Require a pull request before merging**, **Block force pushes** et **Restrict deletions**. Ne configure aucun contournement pour le bot. Enregistre et vérifie que la règle est active.
4. N'active pas l'auto-merge. Aucun workflow du projet ne doit fusionner une PR ; la décision finale reste manuelle.

Si l'interface ne te permet pas d'enregistrer ces règles, garde `GEMINI_WRITE_ENABLED` absent ou différent de `true` et demande-moi d'adapter les possibilités sans ouvrir l'écriture de Gemini.

## Ajouter la clé de l'API gratuite

1. Ouvre [Google AI Studio — clés API](https://aistudio.google.com/apikey) et crée une clé pour l'API Gemini.
2. Vérifie que le projet utilise seulement l'offre gratuite et **qu'aucun compte de facturation n'est rattaché**. Ne saisis pas de moyen de paiement et n'active pas de facturation. Si Google exige une facturation pour créer/utiliser la clé dans ton compte, arrête-toi et ne continue pas avec cette méthode.
3. Dans le dépôt, ouvre **Settings → Secrets and variables → Actions → New repository secret**.
4. Nom exact : `GEMINI_API_KEY`. Colle la clé uniquement dans la valeur du secret et enregistre.

Le modèle configuré est `gemini-3.5-flash-lite`, qui est listé par Google dans l'offre gratuite actuelle de l'API. Les quotas peuvent changer ou être indisponibles. Au quota épuisé, le workflow doit échouer sans mise à niveau payante.

Les deux workflows sont configurés en mode API-key uniquement : aucun chemin Vertex AI/Google Cloud/Code Assist ni clé Google secondaire n'est utilisé. N'ajoute pas ces options ou leurs secrets, car le projet reste strictement à 0 €.

**Données :** Google indique que le contenu envoyé via l'offre gratuite peut être utilisé pour améliorer ses produits. Cela peut inclure du code et du texte du dépôt fournis au modèle. Tu as choisi d'accepter ces conditions ; n'envoie malgré tout aucun secret, mot de passe, donnée personnelle privée ou fichier commercial non autorisé.

## Déverrouiller l'écriture de l'agent

Après avoir protégé `main` et ajouté `GEMINI_API_KEY` :

1. Ouvre **Settings → Secrets and variables → Actions → Variables → New repository variable**.
2. Nom exact : `GEMINI_WRITE_ENABLED`.
3. Valeur exacte : `true`.

Sans cette variable, Gemini peut répondre aux demandes de lecture et proposer un plan, mais `@gemini-cli /approve` n'exécute pas de tâche modifiant le dépôt. À la place, le workflow publie un commentaire expliquant que l'écriture est verrouillée.

L'agent doit ensuite créer une nouvelle branche et une pull request. **Il ne doit jamais pousser vers `main), fusionner une PR ou activer l'auto-merge.** Lis toujours les modifications, les tests, le diff et les limites avant toute décision humaine de fusion.

## Premier test conseillé

Sur la PR #13, après avoir configuré le secret, écris un commentaire en lecture seule, par exemple :

```text
@gemini-cli Fais un audit en lecture seule de l'état actuel de Boonta Reborn 88. Résume les workflows actifs, les résultats CI disponibles, les fichiers Step 102 réellement présents dans le dépôt, les blocages de provenance et les prochaines étapes. Ne modifie aucun fichier et ne crée aucune PR.
```

Vérifie le résultat dans l'onglet [Actions](https://github.com/Master-Chiken/boonta-reborn-88/actions). Ne poste jamais la valeur de la clé. Pour une vraie modification, demande d'abord un plan et n'approuve que le plan que tu as lu.

## Limites

- Gemini ne voit que les fichiers du dépôt et le contexte des issues/PR accessibles via GitHub. Il ne voit pas automatiquement les pièces jointes de ChatGPT.
- Le petit prototype original de `gamecube/` compile en DOL via Actions. Il n'est ni le port complet Step 102 ni une preuve que le jeu est jouable.
- Aucun workflow ne réalise la fusion pour toi. Le propriétaire décide après examen.
- Les outils/quotas gratuits peuvent changer. Si le service demande une carte, de la facturation ou un forfait, n'active pas ce service et reste sur les vérifications GitHub Actions gratuites.

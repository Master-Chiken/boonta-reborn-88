# OpenRouter Free — relecture IA de pull requests

## Ce que fait ce workflow

Le workflow `.github/workflows/openrouter-free-review.yml` ajoute une deuxième opinion IA pour Boonta Reborn 88. Il est **manuel uniquement** : aucune analyse ne se lance à chaque commit ou PR.

- Il reçoit le numéro d'une PR ouverte qui cible `main`.
- Il récupère son diff public, le limite à 30 000 octets et bloque certains motifs courants de clés exposées avant d'envoyer quoi que ce soit.
- Il utilise uniquement le modèle-routeur `openrouter/free`, qui choisit parmi les modèles gratuits actuellement disponibles.
- Il publie une revue sous forme de commentaire GitHub.
- Il ne modifie aucun fichier, ne crée aucun commit, ne peut pas pousser de branche et ne fusionne rien.

## Limites du gratuit

OpenRouter annonce pour son offre Free plus de 25 modèles gratuits et une limite de 50 requêtes par jour. Le routeur `openrouter/free` affiche un tarif de 0 $ pour les tokens. Les modèles, quotas et la disponibilité peuvent changer. Si la requête gratuite échoue, le workflow échoue : il **n'essaie jamais de modèle payant en secours**.

Le routeur ne fournit pas Claude directement : il sélectionne un modèle gratuit de son catalogue. L'API Anthropic directe n'est pas utilisée parce qu'elle est facturée à l'usage.

## Données et sécurité

Le diff est transmis à OpenRouter, puis au fournisseur du modèle choisi par le routeur. OpenRouter explique que les pratiques de rétention et d'utilisation des données varient selon les fournisseurs. Le dépôt étant public, l'utilisation se limite à un diff public, mais ne lance pas ce workflow sur une PR qui contiendrait des secrets, des informations personnelles privées ou des éléments que tu ne veux pas transmettre à un fournisseur externe.

La clé `OPENROUTER_API_KEY` reste dans les secrets GitHub et ne fait pas partie du prompt. Ne colle jamais la clé dans une issue, un commentaire ou un fichier.

## Activer la connexion

1. Ouvre [OpenRouter — clés API](https://openrouter.ai/keys), crée un compte/une clé pour l'offre Free, et n'ajoute **aucun crédit**, aucune carte bancaire et aucun moyen de paiement. La page des plans Free indique actuellement qu'aucun mode de paiement n'est disponible pour cette offre.
2. Dans GitHub, ouvre **Settings → Secrets and variables → Actions → New repository secret**.
3. Nom exact : `OPENROUTER_API_KEY`. Colle la clé uniquement dans la valeur du secret et enregistre.
4. Ouvre [Actions — OpenRouter Free PR review](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/openrouter-free-review.yml), clique **Run workflow**, saisis le numéro de la PR (par exemple `13`) et lance l'exécution.
5. Lis le commentaire produit et vérifie chaque point. Le retour d'une IA ne prouve pas qu'un problème existe ni qu'une modification est correcte.

Si OpenRouter demande une carte ou un paiement pour créer la clé ou envoyer une requête, arrête-toi ; n'active rien de payant.

## Sources officielles

- [Offre Free et limites](https://openrouter.ai/pricing)
- [Routeur de modèles gratuits et tarif à 0 $](https://openrouter.ai/openrouter/free/)
- [Politique de confidentialité d'OpenRouter](https://openrouter.ai/privacy/)

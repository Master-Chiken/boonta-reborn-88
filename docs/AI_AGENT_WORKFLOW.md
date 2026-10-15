# Gemini coding agent — safe operating procedure

## What the agent can do
- Read the current repository checkout and the issue/PR context.
- Respond to an `@gemini-cli` comment with an audit or plan.
- After explicit plan approval and owner-only setup, propose source changes on a separate branch and open a PR.
- It must never merge code or push directly to `main`.

## Activation gates
1. This security-hardening PR must be reviewed and explicitly merged into the default branch.
2. The owner must create a Gemini API key under Google's free tier without linking billing, then store it as the GitHub Actions repository secret `GEMINI_API_KEY`.
3. The owner must protect `main` against direct pushes, force pushes, and deletion.
4. Only after those protections above are confirmed should the owner set the repository Actions variable `GEMINI_WRITE_ENABLED=true`.
5. If a free quota is unavailable, stop; never activate paid billing or a paid fallback.

The write workflow checks `GEMINI_WRITE_ENABLED` in the dispatcher. Without it, `@gemini-cli /approve` does not execute file changes and posts a note that writing remains locked.

## Start read-only
After the hardened workflows are on the default branch and the secret exists, comment on a repository issue or PR with a focused read-only request beginning with `@gemini-cli`. For example:

```text
@gemini-cli Fais un audit en lecture seule. Lis l'arborescence réellement présente, résume les workflows et résultats CI, signale les chemins Step 102 absents et propose les 3 prochaines tâches avec critères d'acceptation. Ne modifie aucun fichier et ne crée aucune PR.
```

## Project context and boundaries
- Main engineering target: GameCube/Wii using C, devkitPPC and libogc.
- The Step 102 archive uploaded to ChatGPT is not automatically visible to Gemini in GitHub Actions.
- Inspect the actual checked-out branch; do not claim files from unmerged PRs are present.
- Do not commit ROMs, disc images, BIOS files or assets of unclear provenance.
- The archive audit records no explicit LICENSE/COPYING/NOTICE file and identifies PC-mod-derived centerline data plus voice/model/assets needing separate provenance review.
- Report what was actually tested. A host test is not proof of a native build; a Dolphin headless process test is not proof of rendering or gameplay.

## Free-only requirement
Google currently offers a free tier for some Gemini API models, with quotas and data-use terms. Verify the current pricing page before activation:
https://ai.google.dev/gemini-api/docs/pricing

Do not attach billing, enter a payment method, or switch to a paid tier. Free-tier Google API content may be used to improve Google products. Never send secrets or private personal information.

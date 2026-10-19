# Security Policy

## Reporting a vulnerability

Please do not publish passwords, API keys, access tokens, private credentials, or exploit details in public issues or pull requests.

If GitHub's private vulnerability reporting is enabled for this repository, use the repository's **Security** tab to report a vulnerability privately. Otherwise, contact the repository maintainer privately through GitHub before sharing technical details.

When reporting an issue, include the affected file or component, the impact, and concise reproduction steps. Redact all personal information and secrets.

## Secrets and sensitive data

- Never commit API keys, passwords, access tokens, private keys, recovery codes, or local credential files.
- Store automation credentials only in GitHub Actions secrets, and grant workflows the minimum permissions they need.
- If a credential may have been exposed, revoke or rotate it immediately. Deleting it from the latest commit is not enough if it exists in Git history or logs.
- Keep game dumps, extracted proprietary data, and private assets out of this public repository; review `.gitignore` before adding new files.

## Scope

This policy applies to the Boonta Reborn 88 repository and its GitHub Actions automation.
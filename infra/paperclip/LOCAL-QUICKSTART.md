# Paperclip local quickstart — no paid services

This setup uses your existing Mac. It does not use a VPS, Oracle Cloud, Docker, an external database, Paperclip Cloud or a bank card.

## What is required

- macOS on your existing Mac.
- Node.js 24.11.0 or newer.
- An installed Gemini CLI and an existing Google account login with a confirmed Free-tier allowance, if you want to run Gemini agents. Paperclip's `gemini_local` adapter can use the existing CLI login; an API key is not required when the login path works.
- An existing GitHub CLI login (`gh`) if the agent needs to push branches and open PRs locally.

Paperclip itself is open source. The local setup uses an embedded PostgreSQL database and stores its state under `~/.paperclip/`.

## Start

First check your Node version:

```bash
node --version
```

It must report `v24.11.0` or newer. If it does not, install the Node.js LTS release from the official website: https://nodejs.org/

Then run the official Paperclip onboarding command:

```bash
npx paperclipai onboard --yes
```

Open:

```text
http://localhost:3100
```

Create the company **Boonta Reborn 88** and the project **GameCube/Wii clean-room game**. Add the shared skill from `BOONTA-AGENT-SKILL.md`.

## When you want to open Paperclip again

```bash
npx paperclipai@latest run
```

Keep that terminal open while using Paperclip. Closing the process or putting the Mac to sleep stops the local Paperclip server and its agents.

The optional managed background-service install is documented by Paperclip, but it is not needed for the first test. Do not run onboarding as root or with `sudo`; the embedded PostgreSQL process must run as the normal Mac user. Do not configure a recurring Paperclip routine yet.

## Free AI and GitHub access

- Select `gemini_local` only if its environment test confirms the installed CLI, usable working directory, existing Google account CLI authentication and available Free-tier quota. The adapter supports CLI login as well as API-key authentication; do not create an API key solely to bypass a working account login, and do not enable billing.
- Run `gh auth status` to see whether GitHub CLI is already authenticated on this Mac. If it is not, stop and review the access method before creating any token.
- A fine-grained GitHub token, if eventually needed, must be restricted to `Master-Chiken/boonta-reborn-88`. It is not a hosting subscription, but it is still a credential and should only be created when needed.

## Important

Paperclip is local. It does not run when the Mac is off. The existing GitHub Actions schedule remains responsible for automatic cloud work, and is free on this public repository for standard GitHub-hosted runners.

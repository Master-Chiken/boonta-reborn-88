# Cloud development (no local toolchain required)

This repository includes a GitHub Codespaces dev-container configuration for the GameCube smoke test. It uses the same devkitPro/devkitPPC toolchain image as the GitHub Actions build, so the compiler does not need to be installed on your computer.

## Open the cloud workspace

1. Open the repository in GitHub.
2. Select the `audit/step102-import-gate` branch.
3. Open **Code → Codespaces → Create codespace on audit/step102-import-gate**.
4. Wait for the remote editor to finish loading.
5. In the integrated terminal, run:

   ```sh
   cd gamecube
   make clean
   make
   ```

The expected output is `gamecube/boonta_smoke.dol`. This is only a toolchain smoke test, not the racing game.

## Cost and storage note

GitHub Codespaces has a limited free monthly quota on eligible personal plans. Stop the codespace when you finish, and delete it when you no longer need it, so it does not keep consuming the quota. Do not store ROMs, disc images, or extracted commercial assets in the repository or codespace.

## Current scope

- The cloud workspace is intended for code edits and building.
- GitHub Actions remains the automated build check.
- The full Step 102 prototype is not imported yet.
- A successful build does not prove the program has been tested in Dolphin or on hardware.

# Dolphin keyboard-only test setup

This guide is for the first visible playability check when no physical controller is available. Dolphin can emulate a standard GameCube controller from keyboard input; this does not require changing Boonta's runtime input code.

## 1. Enable the emulated controller

1. Open Dolphin and go to **Options → Controller Settings** (or click **Controllers**).
2. Under **GameCube Controllers**, set **Port 1** to **Standard Controller**. Do not leave it as **None**.
3. Click **Configure** for Port 1.
4. In **Device**, choose the keyboard/keyboard-and-mouse input device. Keep the Boonta window focused while testing.
5. In the mapping window, verify the keys below. If your profile is different, click a control binding and press the key you want. Dolphin's official guide explains the device selector and per-control binding process: [Configuring Controllers](https://dolphin-emu.org/docs/guides/configuring-controllers/).

## 2. Try the existing desktop keyboard defaults first

The Dolphin desktop defaults currently assign these keyboard keys in its GameCube controller implementation. The exact device label and key names can vary by operating system; use the Configure window as the source of truth if a binding is different. Upstream reference: [Dolphin `GCPadEmu.cpp`](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/Core/HW/GCPadEmu.cpp#L1027-L1145).

| GameCube control read by Boonta | Desktop keyboard default | Boonta action |
|---|---|---|
| A | `X` key | Accelerate |
| B | `Z` key | Brake |
| X | `C` key | Boost when held together with GameCube A |
| Y | `S` key | Reset race |
| Start | `Return` / Enter | Pause / resume |
| Control Stick left/right | Left / Right arrow | Steer |
| Control Stick up/down | Up / Down arrow | Pitch |
| D-pad left/right | `F` / `H` | Digital steering fallback |
| D-pad up/down | `T` / `G` | Not needed for the first test |
| L trigger | `Q` | Slide input |

**Important naming distinction:** the GameCube **A button** is mapped to the keyboard **X key** by Dolphin's desktop default. The GameCube **X button** is mapped to the keyboard **C key**. To test boost, hold the keyboard **X + C** keys together.

If you prefer more ergonomic steering, rebind the Control Stick left/right to `A`/`D` in Dolphin's Configure window, and up/down to `W`/`S`. If you do that, change the relevant buttons as needed to avoid overlapping key assignments; the first test does not require a custom layout.

## 3. Smallest useful first test

Use the latest `main` DOL from the [GameCube first-render workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml). Keep the first run short:

1. Press the keyboard `S` key (GameCube Y) and confirm the HUD returns to the clean start state.
2. Hold `X` (GameCube A) briefly; release it, then test `Z` (GameCube B).
3. Tap Left and Right arrows, or `F`/`H` for the D-pad. Confirm the pod responds in both directions.
4. Hold keyboard `X + C` (GameCube A + X) to test boost.
5. Press Enter to pause, Enter again to resume, then press `S` to reset.
6. Only after these controls work, try to finish three laps and test reset/restart.

Do not infer that controls work merely because the DOL starts or a CI movie renders a frame. If a step fails, record it as **FAIL**; if you did not test it, record **NOT TESTED**.

## 4. Record the acceptance result

Add a concise report to [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126) with:

- exact `main` commit SHA used for the DOL;
- Dolphin version and video backend;
- whether Port 1 was set to Standard Controller and which device was selected;
- PASS / FAIL / NOT TESTED for reset, accelerate, brake, steering, boost, pause/resume, three-lap finish, and restart;
- a screenshot or short video if practical.

This is a human-operated Dolphin test using a keyboard. It is stronger than a headless smoke or scripted DTM check, but it does not prove physical GameCube/Wii compatibility. Do not commit the DOL, ROMs, disc images, or extracted commercial assets to the repository.

# Porpoise / Dolphin audit for Boonta Reborn 88

**Status:** bounded, read-only external technical study.  
**Reviewed:** 2026-11-06.  
**Decision:** reuse engineering lessons only; do not import Porpoise or Dolphin code into the clean-room GameCube/Wii game.

## 1. Sources and provenance

| Source | Revision observed | License / provenance | What was verified |
|---|---|---|---|
| [elripalda/Porpoise-Dolphin-Emulator-for-PS5](https://github.com/elripalda/Porpoise-Dolphin-Emulator-for-PS5) | Release page identifies Porpoise 4.0, tag `v4.0`, abbreviated commit `db6c13e`, published 2026-10-21. Full commit SHA not independently pinned in this audit. | Porpoise GPL-3.0-or-later; component licenses remain separate. | README and release notes describe a PS5 homebrew launcher hosting Dolphin's libretro core. |
| [Dolphin Emulator](https://github.com/dolphin-emu/dolphin) | Upstream project reference; exact source revision not pinned here. | Dolphin is GPL-2.0-or-later; check individual files and dependencies before any reuse. | Porpoise credits Dolphin and the libretro Dolphin core. |
| [Porpoise 4.0 release](https://github.com/elripalda/Porpoise-Dolphin-Emulator-for-PS5/releases) | `v4.0` | Release page lists component licensing in its packaged `licenses/README.txt`. | Release notes report fixes and a beta frame-generation feature; they do not establish GameCube/Wii target compatibility for Boonta. |

Evidence labels: **DOCUMENTED** means stated by the public project/release; no source build or runtime test was performed by this audit.

## 2. What Porpoise actually is — and is not

Porpoise is a native PS5 homebrew application which hosts the Dolphin emulator's libretro core. Its README describes a launcher/library, game discovery, per-game configuration, memory-card management, an in-game menu, update handling and DualSense input. Its documented rendering path is Dolphin's x86-64 JIT on the PS5 CPU with Vulkan through Mesa RADV.

This is useful as a mature *application and emulator-integration reference*. It is **not** a GameCube/Wii game engine, a native GameCube/Wii porting framework, or a source of original Racer gameplay. Its PS5 CPU, JIT, Vulkan and homebrew APIs are not portable to the GameCube/Wii target.

Porpoise itself notes that Wii support is experimental in places (including motion-heavy Wii Remote behavior). Therefore, do not interpret its broad GameCube/Wii compatibility as proof that a feature is straightforward or complete on our target hardware.

## 3. Transferable engineering lessons for Boonta

These are design ideas to evaluate independently against the existing Boonta code; they are not instructions to copy implementation code.

1. **Keep the platform/game boundary explicit.** Porpoise separates its launcher and host-specific services from the Dolphin core. Boonta should likewise keep platform-specific controller, video, audio and storage adapters behind the existing native game interfaces, without introducing an emulator layer.
2. **Treat controller mapping as a named, testable contract.** Document logical actions (steer, accelerate, brake, boost, pause) separately from physical buttons. Test mapping and edge cases on host, then verify actual response in visible Dolphin and on hardware when available. Do not copy DualSense or PS5 mapping.
3. **Make runtime state observable.** Per-game settings, logs and a reportable diagnostic bundle are useful patterns. For Boonta, expose a small deterministic debug snapshot for race state, lap/progress, vehicle speed/steering, boost/heat and AI state, while keeping normal HUD behavior unchanged.
4. **Protect user data during updates.** Porpoise documents hash/manifest verification and keeping saves/settings outside the application directory. This is a possible future lesson for Boonta save/update design, not a current gameplay milestone.
5. **Validate each platform claim at its own evidence level.** A host test, native build, emulator smoke, rendered frame, interactive controller session and physical-console run are different acceptance levels. Keep them separate in reports and CI.

## 4. Boonta reuse map (existing work first)

| Area | Existing Boonta foundation | Useful Porpoise lesson | Decision |
|---|---|---|---|
| Native GameCube rendering | `gamecube-demo/`, GX path and current build workflow | Separate host/application concerns from target rendering | Preserve the current GX path; no renderer rewrite. |
| Controls | Existing GameCube input abstraction and host tests | Logical action mapping and diagnostics | Audit existing mapping/tests first; add only missing regression coverage. |
| Race state and HUD | Existing race/lap/pause/reset code | Make runtime state easy to inspect | Consider a deterministic debug snapshot only if it directly helps the active race acceptance task. |
| Save/update infrastructure | Not part of the current playable slice | Keep persistent data separate and verify updates | Defer; not on the first playable-race critical path. |
| Wii support | Native target work and separate Wii controller research | Explicitly record experimental/unknown behavior | Do not infer Wii support from Porpoise; test Boonta's own backend. |

The existing Boonta operating rules and clean-room boundary take precedence. In particular, keep the active native work in issue #226 and reuse existing route/controller PRs rather than opening parallel implementation tracks.

## 5. Legal and clean-room decision

- No Porpoise or Dolphin source code, binary, artwork, sound, game image, firmware, keys, save, texture, model or other payload is copied into this repository by this audit.
- Public availability does not grant permission to copy all project content. Porpoise is GPL-3.0-or-later and Dolphin is GPL-2.0-or-later; a future code-reuse proposal would require exact file/revision review, license compatibility analysis, notices and compliance review before any import.
- Ideas and observed behavior may inform an independently written implementation, but do not copy expressive code or assets.
- The Porpoise release page says it contains no games or BIOS/firmware and expects users to supply their own lawful backups. Boonta must likewise keep commercial game content and user-owned reference files out of public GitHub and hosted AI tools.
- Budget impact: none. This audit uses public documentation only; no paid services or downloads are required.

## 6. Bounded next action

**Do not start a Porpoise integration.** The highest-value next step remains the current native playable-race work in issue #226.

For the next implementation-sized task, inspect the current GameCube input abstraction and the active route-runtime candidate, then select one missing end-to-end acceptance gap. Prefer a deterministic host test or a small native gameplay improvement that helps complete a three-lap race with a controllable pod, a circuit, at least one meaningful rival, finish and reset. Keep any Porpoise-inspired diagnostics strictly optional and only add them if they unblock that acceptance test.

### Acceptance for this audit

- [x] Public Porpoise README and release notes reviewed.
- [x] Platform architecture and documented limitations separated from Boonta target facts.
- [x] Existing Boonta controls/rendering/race foundations identified from repository documentation.
- [x] License/provenance boundary recorded.
- [ ] Exact full Porpoise source commit SHA and every subcomponent license independently audited.
- [ ] No Boonta code or runtime behavior changed by this research-only PR.
- [ ] No claim of GameCube/Wii compatibility or playable-game improvement is made from this audit.

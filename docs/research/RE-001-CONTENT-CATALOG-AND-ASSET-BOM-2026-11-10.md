# RE-001 — Full content catalogue and asset bill of materials

**Research date:** 2026-11-10  
**Repository baseline:** `main` at `730a49bd288db9bf749bbc7241d7a133cce891f9`  
**Target:** a clean-room racing game for native GameCube/Wii, inspired by *Star Wars: Episode I – Racer* (1999).  
**Purpose:** turn the existing system inventory into a concrete list of content the finished game needs: tracks, worlds, pilots, pods, upgrades, environments, UI, audio, effects and progression.  
**Status:** reference catalogue and production bill of materials. **This is not an asset import and not proof of GameCube/Wii content compatibility.**

---

## 1. Executive decision

The original game reference is much larger than the current Boonta prototype. Public reference material identifies **25 tracks across eight worlds** and **23 standard playable racers**; two additional character replacements are documented for an N64 cheat code. The exact roster, course order, menus and mechanics must still be checked against the precise reference version being studied. PC, N64 and Dreamcast evidence must not be silently promoted to GameCube/Wii facts. [Wookieepedia game overview](https://starwars.fandom.com/wiki/Star_Wars:_Episode_I_Racer) · [IGCD track catalogue](https://www.igcd.net/game.php?id=1000017265&type=circuits) · [IGCD vehicle catalogue](https://www.igcd.net/game.php?id=1000017265)

**The game needs four different kinds of content:**

1. **Reference metadata:** names, course ordering, roster, vehicle categories, parts, championship structure and rules. This can be recorded in Git as researched factual metadata with source/version labels.
2. **Reusable tools and formats:** parsers, exporters, texture converters, model importers, route editors, audio pipelines and test fixtures. Use only where the exact format is supported and the tool's license permits it.
3. **Actual visual/audio/gameplay assets:** track geometry, props, models, textures, animations, voices, music, engine sounds and effects. Put in the public repository only when original or explicitly licensed for redistribution.
4. **Runtime systems:** course loading, world streaming, pod handling, race progression, menus, AI, save data, effects and audio. Implement in Boonta as clean-room code, or reuse a compatible library after its code licence has been reviewed.

The shortcut is **not** to copy the commercial game. It is to recover privately what the owner is entitled to inspect, retain accurate metadata, use open tools to understand/convert proven formats, and fill missing public content with original or redistribution-cleared assets.

## 2. Reference course catalogue — 25 tracks / eight worlds

The following table merges the published tournament grouping with the published track-to-world catalogue. The world mapping is community-documented and should be treated as a **reference-version lead** until confirmed against a lawful local copy or primary documentation. [Track/world catalogue](https://www.igcd.net/game.php?id=1000017265&type=circuits) · [Tournament structure and course count](https://starwars.fandom.com/wiki/Star_Wars:_Episode_I_Racer) · [Course walkthrough](https://www.neoseeker.com/episode1racer/faqs/84525-racer-e.html)

| # | Championship | Track | World / environment family | Production note |
|---:|---|---|---|---|
| 1 | Amateur | Boonta Training Course | Tatooine | Tutorial/intro variant; not the same production package as the full Boonta Classic |
| 2 | Amateur | Mon Gazza Speedway | Mon Gazza | Industrial speedway / mining infrastructure |
| 3 | Amateur | Beedo's Wild Ride | Ando Prime | Mountain/canyon route variant |
| 4 | Amateur | Aquilaris Classic | Aquilaris | Coastal / underwater-city world family |
| 5 | Amateur | Malastare 100 | Malastare | Dense industrial / desert world variant |
| 6 | Amateur | Vengeance | Oovo IV | Harsh arena / hazardous route |
| 7 | Amateur | Spice Mine Run | Mon Gazza | Mine / industrial route; distinct geometry from Speedway |
| 8 | Semi-Pro | Sunken City | Aquilaris | Underwater-city architecture and water/coastal treatment |
| 9 | Semi-Pro | Howler Gorge | Ando Prime | Gorge / cliffs / long sightlines |
| 10 | Semi-Pro | Dug Derby | Malastare | Rough terrain / industrial race setting |
| 11 | Semi-Pro | Scrapper's Run | Ord Ibanna | Floating scrap / junkyard structures and large drops |
| 12 | Semi-Pro | Zugga Challenge | Mon Gazza | Industrial course variant |
| 13 | Semi-Pro | Baroo Coast | Baroonda | Coastal route / water and vegetation |
| 14 | Semi-Pro | Bumpy's Breakers | Aquilaris | Coastal / wave and water presentation |
| 15 | Galactic | Executioner | Oovo IV | High-risk arena environment |
| 16 | Galactic | Sebulba's Legacy | Malastare | Malastare variant; distinguish its layout and props from Malastare 100 |
| 17 | Galactic | Grabvine Gateway | Baroonda | Dense vegetation / grabvine obstacle identity |
| 18 | Galactic | Andobi Mountain Run | Ando Prime | Mountain climb / descent route |
| 19 | Galactic | Dethro's Revenge | Ord Ibanna | Floating-scrap / industrial structures |
| 20 | Galactic | Fire Mountain Rally | Baroonda | Volcanic / lava / fire-themed course |
| 21 | Galactic | The Boonta Classic | Tatooine | Signature desert arena / canyon finish |
| 22 | Invitational | Ando Prime Centrum | Ando Prime | Bonus championship course |
| 23 | Invitational | Abyss | Ord Ibanna | Deep-drop / floating-platform course |
| 24 | Invitational | The Gauntlet | Oovo IV | Bonus high-hazard arena course |
| 25 | Invitational | Inferno | Baroonda | Bonus volcanic / lava environment |

### The eight world environment kits Boonta must support

| World | Minimum unique visual language to reproduce independently |
|---|---|
| Tatooine | Dune/sand material set, rock mesas, canyon walls, desert haze, sparse settlement/arena dressing |
| Ando Prime | Mountain rock, high cliff silhouettes, industrial/settlement structures, snow/rock/vegetation variants where verified |
| Baroonda | Coastal water, tropical/alien vegetation, sand/rock, swamp/river/lava variants where a particular course requires them |
| Mon Gazza | Mine infrastructure, pipelines, industrial platforms, machinery, dust and dark interior/exterior transitions |
| Malastare | Desert/rock, rugged ground, industrial props, broad track-side formations |
| Oovo IV | Arena/fortress structures, exposed platforms, hazard dressing and strong industrial silhouettes |
| Ord Ibanna | Floating scrap platforms, suspended structures, junkyard props, large vertical drops |
| Aquilaris | Underwater-city/coastal architecture, water surface/fog, marine/rock formations, blue/teal lighting language |

This is a **world-level art direction checklist**, not a claim that every listed material occurs on every course. A course manifest must select the correct subset and its exact route-specific props, hazards, sky and lighting.

### What a course package must contain

Each of the 25 catalogue entries ultimately needs an independently authored or legally cleared package with:

- Stable course ID, display name, championship, world, reference version and unlock condition.
- One or more route graphs: start/finish, ordered edges, branch/split/rejoin decisions, alternate paths, checkpoint/progress events, lap direction and respawn-safe positions.
- Spline/control-point data, tangent/frame information, route width, surface type and elevation.
- Track mesh, road/rail/edge geometry, terrain, collision meshes and out-of-bounds recovery.
- Scene/object catalogue: static props, animated props, hazards, triggers, moving obstacles and visual effects.
- Start grid, player and rival spawn definitions, camera rails/look-ahead markers and marshal/checkpoint positions.
- Environment package: skybox or skydome, terrain materials, fog, lighting, water/lava/vegetation/particle variants and course-specific ambience.
- Minimap or track-map geometry and HUD route metadata.
- Thumbnail, course-selection preview, title/description and localisation keys.
- Memory budget, texture budget, draw-call/material estimate, LOD rules and a tested GameCube/Wii package size.

**Critical design decision:** do not build 25 unrelated maps by hand. Build a reusable route/course schema plus modular environment/prop kits; then author each track as its own route, surface/obstacle configuration and scene composition. Share only verified/common modules, not unsupported assumptions from a PC or N64 data layout.

## 3. Pilot roster — 23 standard racers

Public reference lists identify six starting racers and 17 unlockable racers. The following is a roster metadata baseline, not a licence to reproduce film likenesses, voice performances, portrait art or commercial pod models. [Roster overview](https://starwars.fandom.com/wiki/Star_Wars:_Episode_I_Racer)

### Starting racers

| Racer ID | Pilot | Initial availability |
|---|---|---|
| PILOT-ANAKIN | Anakin Skywalker | Starting roster |
| PILOT-DUD-BOLT | Dud Bolt | Starting roster |
| PILOT-EBE-ENDOCOTT | Ebe Endocott | Starting roster |
| PILOT-ELAN-MAK | Elan Mak | Starting roster |
| PILOT-GASGANO | Gasgano | Starting roster |
| PILOT-ODY-MANDRELL | Ody Mandrell | Starting roster |

### Unlockable racers

| Racer ID | Pilot | Initial availability |
|---|---|---|
| PILOT-ALDAR-BEEDO | Aldar Beedo | Unlockable |
| PILOT-ARK-ROOSE | Ark "Bumpy" Roose | Unlockable |
| PILOT-BEN-QUADINAROS | Ben Quadinaros | Unlockable |
| PILOT-BOLES-ROOR | Boles Roor | Unlockable |
| PILOT-BOZZIE-BARANTA | Bozzie Baranta | Unlockable |
| PILOT-BULLSEYE-NAVIOR | "Bullseye" Navior | Unlockable; see spelling note below |
| PILOT-CLEGG-HOLDFAST | Clegg Holdfast | Unlockable |
| PILOT-FUD-SANG | Fud Sang | Unlockable |
| PILOT-MARS-GUO | Mars Guo | Unlockable |
| PILOT-MAWHONIC | Mawhonic | Unlockable |
| PILOT-NEVA-KEE | Neva Kee | Unlockable |
| PILOT-RATTS-TYERELL | Ratts Tyerell | Unlockable |
| PILOT-SEBULBA | Sebulba | Unlockable |
| PILOT-SLIDE-PARAMITA | Slide Paramita | Unlockable |
| PILOT-TEEMTO-PAGALIES | Teemto Pagalies | Unlockable |
| PILOT-TOY-DAMPNER | Toy Dampner | Unlockable |
| PILOT-WAN-SANDAGE | Wan Sandage | Unlockable |

### N64 cheat replacements — do not count as standard roster

| Racer ID | Pilot | Version note |
|---|---|---|
| PILOT-CY-YUNGA | Cy Yunga | Documented as an N64 cheat-code character replacement; not part of the 23 standard roster |
| PILOT-JINN-REESO | Jinn Reeso | Documented as an N64 cheat-code character replacement; not part of the 23 standard roster |

The roster's standard count and the two N64 replacement entries must remain separate. The GameCube/Wii target's intended roster is not established by the existence of these N64 cheat variants.

### Pilot asset checklist

For every pilot identity, the eventual content system needs:

- Pilot ID, display name, unlock condition, statistics/configuration reference and vehicle ID.
- Original, rights-cleared portrait / selection-card artwork and UI crop.
- Original, rights-cleared model or cockpit/driver representation if the chosen camera exposes the pilot.
- Animation/state set: idle, selection, pre-race, victory/defeat and any pit/garage presentation that is included.
- Voice/audio event mapping only when original recordings or an expressly licensed replacement are available.
- Localisation strings, selection text, rivalry/biography fields if used.
- Version/platform tags and provenance for every non-original reference.

Do not copy actors' likenesses, film frames, official character art or dialogue recordings into the public project.

## 4. Pod / vehicle catalogue — 25 reference configurations

The following are public catalogue names pairing pilots with their commonly listed pod model labels. They are useful as a content-reference database and to keep names consistent across research. They are **not** a validated list of GameCube/Wii model files, and model names do not confer rights to the models or textures. The IGCD catalogue also spells the Bullseye pilot "Namor" in one entry, whereas the roster reference uses "Navior"; preserve that discrepancy until the exact version's UI/reference is checked. [IGCD vehicle catalogue](https://www.igcd.net/game.php?id=1000017265) · [Roster reference](https://starwars.fandom.com/wiki/Star_Wars:_Episode_I_Racer)

| Vehicle ID | Pilot / associated racer | Published pod model label | Notes |
|---|---|---|---|
| POD-ALDAR-BEEDO | Aldar Beedo | Mk IV Flat Twin Turbojet Podracer | Standard roster |
| POD-ANAKIN | Anakin Skywalker | Anakin Skywalker's Podracer | Standard roster |
| POD-ARK-ROOSE | Ark "Bumpy" Roose | Plug-8G 927 Cluster Array Podracer | Standard roster |
| POD-BEN-QUADINAROS | Ben Quadinaros | BT310 Quadra Podracer | Standard roster |
| POD-BOLES-ROOR | Boles Roor | Quadrijet 4-Barrel 904E Podracer | Standard roster |
| POD-BOZZIE-BARANTA | Bozzie Baranta | Shelba 730 Razor Podracer | Standard roster |
| POD-BULLSEYE-NAVIOR | "Bullseye" Navior | RQ 550C Dart Podracer | IGCD lists "Namor"; unresolved spelling |
| POD-CLEGG-HOLDFAST | Clegg Holdfast | 9T9-B Wasp Podracer | Standard roster |
| POD-CY-YUNGA | Cy Yunga | V-71 Ridge Piranha Podracer | N64 cheat replacement |
| POD-DUD-BOLT | Dud Bolt | Vulptereen 327 Podracer | Standard roster |
| POD-EBE-ENDOCOTT | Ebe Endocott | J930 Dash-8 Podracer | Standard roster |
| POD-ELAN-MAK | Elan Mak | KRT 410C Podracer | Standard roster |
| POD-FUD-SANG | Fud Sang | BRE Block6 Tri-Ram Podracer | Standard roster |
| POD-GASGANO | Gasgano | Ord Pedrovia Podracer | Standard roster |
| POD-JINN-REESO | Jinn Reeso | Jinn Reeso's Podracer | N64 cheat replacement |
| POD-MARS-GUO | Mars Guo | Plug-2 Behemoth Podracer | Standard roster |
| POD-MAWHONIC | Mawhonic | GPE-3130 Podracer | Standard roster |
| POD-NEVA-KEE | Neva Kee | FG 8T8-Twin Block2 Special Podracer | Standard roster |
| POD-ODY-MANDRELL | Ody Mandrell | XL 5115 Podracer | Standard roster |
| POD-RATTS-TYERELL | Ratts Tyerell | Scatalpen Podracer | Standard roster |
| POD-SEBULBA | Sebulba | Plug-F Mammoth Podracer | Standard roster |
| POD-SLIDE-PARAMITA | Slide Paramita | Stinger 627 S Podracer | Standard roster |
| POD-TEEMTO-PAGALIES | Teemto Pagalies | IPG-X1131 LongTail Podracer | Standard roster |
| POD-TOY-DAMPNER | Toy Dampner | 910 Special Podracer | Standard roster |
| POD-WAN-SANDAGE | Wan Sandage | TurboDyne 99-U Podracer | Standard roster |

### A full vehicle is more than a mesh

Each Pod content record needs independently authored or cleared assets/data for:

- Main hull/engine/nacelle meshes, engine cables/arms, cockpit and attachment points.
- Materials, texture sets, damage masks, emissive engine/fire maps and LODs.
- Rig/skeleton or rigid-part hierarchy, animation clips and effects sockets.
- Collision primitives/meshes, hit regions, repair/damage state and reset pose.
- Audio profile: idle, acceleration, load, boost, overheat, collision and damage, with original/licensed recordings.
- Physics profile: mass/inertia or arcade equivalents, thrust, acceleration, steering response, traction, air brake, cooling/heat, repair/damage susceptibility.
- Driver/pilot relationship, colourway, garage/selection thumbnail and unlock/economy metadata.
- GameCube/Wii budgets: vertex formats, GX texture formats, palette/LOD, memory/draw-call limits and measured performance.

The current source-authored twin-engine pod is a useful clean-room technical seed. It is **not** any of the original 25 commercial models. A future original Boonta fleet should have distinct silhouettes and tuned driving identities without directly tracing or copying protected pod designs.

## 5. Parts, upgrades, damage and pit crew

The reference game documents seven upgrade attributes:

1. Traction
2. Turning
3. Acceleration
4. Top speed
5. Air brake
6. Cooling
7. Repair rate

Its progression involves default/replacement parts, part condition/damage, pit droids, Watto's shop, a junkyard, race rewards and unlock tiers. A public community guide lists example high-level parts such as R-600 Repulsorgrip, Control Stabilizer, MAG-6 Injector, Block6 Thrust Coil, Quadrijet Air Brake, Turbo Coolant Pump and Cluster2 Power Plug. These names are **reference metadata only**; the complete six-part-per-category catalogue, values, prices and platform/version rules still need a separately checked data source. [Upgrade-system guide](https://www.speedrun.com/swe1r/guides/498gh) · [Best parts guide](https://www.speedrun.com/fr-FR/swe1r/guides/sdik9) · [Original-era FAQ](https://www.neoseeker.com/episode1racer/faqs/27446-racer-a.html)

### Boonta production requirements

- Seven stable stat definitions, units/scale, base values and upgrade multipliers.
- Part catalogue per stat: ID, name, tier, values, cost, condition, compatibility and unlock threshold.
- Damage/condition model, repair cost/time, part failure and replacement rules.
- Pit droid crew: count, cost, ownership, assignment and repair automation.
- Credits/Truguts accounting, race reward settings, shop prices, sell-back/devaluation rules and junkyard selection.
- Garage and vehicle-upgrade UI; compare before/after statistics and highlight trade-offs.
- Save/profile data for ownership, money, unlocks, selected vehicle, part inventory and records.
- Deterministic tests for purchases, insufficient funds, unlock gates, damage rolls, repair, reset and save/load.

The original part names and numbers should stay as research labels until the exact data source has been lawfully inspected. For a clean-room enhanced game, use new original part names and descriptions rather than presenting copied commercial naming as new original content.

## 6. Complete game content bill of materials

This is the production checklist to turn the catalogue into real game content. A row marked "missing" means the current public Boonta tree does not yet contain the listed content system at the level described.

| Content group | Required deliverables | Current Boonta baseline | Gap / disposition |
|---|---|---|---|
| Course catalogue | 25 course metadata records, four championship groups, unlock map and previews | One synthetic oval only | Missing: data catalogue and course packages |
| Route data | Spline/Bezier edges, branches, joins, checkpoints, lap/finish events, respawn and route maps | One synthetic closed oval, eight nodes/eight Bezier edges | Missing: course-specific graphs and branching runtime use |
| Track geometry | Road/rails, terrain mesh, trackside collision, surfaces, ramps and barriers | Procedural test road/canyon | Missing: authored course geometry |
| World kits | Eight world/environment kits, sky, terrain, water/lava, fog, vegetation/rock/industrial props | One procedural desert environment | Missing: seven world families and course variation |
| Static props | Buildings, signs, lamps, rocks, machinery, debris, vegetation, structures and set dressing | A few procedural canyon props | Missing: reusable prop library and course-specific placement |
| Moving hazards | Animated obstacles, moving props, triggers, hazard state and collision | Basic rival craft/collision prototype | Missing: course-specific hazards and event data |
| Pilot roster | 23 standard identities + platform-specific bonus roster records | No complete pilot database, portraits or models | Missing: metadata/selection and original/cleared representation |
| Pod fleet | 23 standard pod configurations + version-specific cheat variants where appropriate | One original test pod mesh | Missing: model fleet, rigs, texture/material sets and physics profiles |
| Pod physics | 7 vehicle stat families plus handling/damage tuning and surface response | Clean-room basic handling | Missing: per-pod tuning and advanced model |
| Rival AI | Racing line, pace, route choice, passing, defending, collision recovery, difficulty and ranking | Three simple procedural rivals | Missing: full driver roster behaviours, robust state-based AI |
| Parts/upgrades | Seven categories, part catalogue, shop, junkyard, condition, damage, repair and droids | Not implemented | Missing: full system |
| Progression | Tournament unlocks, race results, credits, career/profile and records | Not implemented as complete game flow | Missing: menus/state/save integration |
| Menus/UI | Boot/title, profile, mode, course/vehicle select, garage/shop, options, pause/results/credits | Basic in-race HUD only | Missing: front-end and menu flows |
| HUD/minimap | Speed, lap, position, heat/boost, damage, race clock, route map, messages and accessibility | Partial prototype HUD | Missing: production UI/data binding |
| Audio | Music, engine loops, acceleration/boost, impacts, menu, announcer, ambience and spatial mixing | No integrated game audio | Missing: original/licensed audio and sound engine |
| Animation/VFX | Pod engine/exhaust, pilot, track objects, particles, dust, smoke, sparks, water/lava and finish effects | Basic procedural exhaust/environment | Missing: library and event-driven effect system |
| Cameras | Chase, cockpit/alternate, intro, finish/results and replay if in scope | Prototype chase camera | Missing: camera profiles and authored rails |
| Multiplayer/modes | Versus, time trial, free play, tournament, options per actual target scope | Not implemented as complete modes | Verify per-platform scope before building |
| Packaging/localisation | Course thumbnails, metadata, font glyphs, languages, credits, save/version migration | Basic prototype data | Missing: production asset packaging and language data |

### Content scale / counts to budget around

- **25** named reference tracks across **8** worlds.
- **4** tournament groups: Amateur, Semi-Pro, Galactic and Invitational.
- **23** standard pilot/pod identities; **2** additional N64 cheat-code replacements should remain a platform-specific optional group.
- **7** upgrade-stat categories; public guides describe multiple part tiers per category, but the exact complete part inventory still needs local/versioned verification.
- At least one complete, unique track package per catalogue entry. Shared world kits can reduce duplication but cannot replace the unique route, geometry, obstacle set and race tuning for each track.

These are scope estimates from published reference metadata, not a claim that Boonta must copy every original level or exact asset. Product direction can select a faithful baseline and then add original bonus content.

## 7. Current Boonta asset inventory — what exists today

Checked on `main` at `730a49bd288db9bf749bbc7241d7a133cce891f9`:

### Present in the public tree

- `gamecube-demo/data/original-test-oval-route-graph.json`: one original synthetic closed route graph.
- `gamecube-demo/data/original-test-oval-surface-widths.json`: the synthetic test route's surface widths.
- `gamecube-demo/data/meshes/original_twin_engine_racer.json`: one source-authored test pod mesh.
- `gamecube-demo/data/meshes/original_synthetic_diamond.json` and `original_synthetic_triangle.json`: small synthetic geometry fixtures.
- `gamecube-demo/data/textures/original_twin_engine_panel.json`: one original source-authored texture source.
- Generated C headers for the mesh, texture, route graph and track.
- A native GX renderer, basic driving/boost/heat/lap/pause state, three simple procedural rivals, route sampling, host tests, native DOL/ELF build and bounded Dolphin diagnostics.

### Not present as full content

- No 25-track content database or 25 authored route/scene packages.
- No eight complete world kits or production course environments.
- No original commercial pilot/pod models, pilot portraits, or full 23-pod fleet.
- No 23 pod physics profiles or complete upgrade/parts/economy model.
- No title/front-end, course/vehicle selection, garage/shop, full tournament/progression/save flow.
- No original or cleared game music/voice/announcer set, or complete engine/collision/ambience audio.
- No runtime filesystem/content loader for a commercial game archive; no proven Racer-specific proprietary asset parser.
- No human-confirmed complete interactive race or physical GameCube/Wii hardware acceptance.

The README and source tree describe a clean-room prototype with procedural test content, not a hidden stock-game asset library. Do not infer that a missing content set is already present just because a reference project or a local archive exists outside Git.

## 8. Lawful sources and usable asset packs

### 8.1 Open assets safe to evaluate for the public repository

These sources are useful for **original placeholder assets, modular environment building and neutral UI/audio**, not for recreating recognisable Star Wars characters or proprietary pod designs.

| Source | Published licence / contents | Potential use | Gate before commit |
|---|---|---|---|
| [Kenney Racing Kit](https://kenney.nl/assets/racing-kit) | CC0; 110 files listed on the pack page | Generic track-side structures, race props and vehicle/road prototyping | Download only the needed files; record pack/date/hash; check polygon/material/texture budgets and visibly transform into original course art |
| [Kenney Space Kit](https://kenney.nl/assets/space-kit) | CC0; 150 files listed | Generic sci-fi structures, panels, hangar/garage and menu prototypes | Do not treat the pack as a ready-made podracer or copy another game's identity; create a source manifest |
| [Kenney Modular Space Kit](https://kenney.nl/assets/modular-space-kit) | CC0; 40 files listed | Modular industrial/spaceport set dressing | Select a small subset and test UV/material/vertex formats on GX |
| [Kenney Nature Kit](https://kenney.nl/assets/nature-kit) | CC0; 330 files listed | Rocks, foliage, trees and organic world dressing | Reduce meshes, create LODs, bake/convert materials and verify GameCube memory use |
| [Kenney City Kit — Roads](https://kenney.nl/assets/city-kit-roads) | CC0; 90 files listed | Generic roads, barriers, modular industrial/settlement pieces | Use as a prototyping kit; do not imply the models are original game assets |
| [Kenney UI Audio](https://kenney.nl/assets/ui-audio) | CC0; 50 files listed | Button focus, confirm/cancel and neutral menu feedback | Do not use it as race music, announcer or final engine sound |
| [Poly Haven](https://polyhaven.com/license) | Its asset library states CC0 for HDRIs, textures and 3D models | Surface materials, rock/metal/soil texture sources, sky/lighting reference | Download only selected assets; retain original source IDs/hashes; produce GX-appropriate derived maps and mip levels |

Kenney states its listed packs are public-domain CC0; Poly Haven likewise declares CC0 for its HDRIs, textures and 3D models. Preserve pack provenance anyway, and do not use either source's brand/logo as project branding. [Kenney asset pages](https://kenney.nl/assets) · [Poly Haven licence](https://polyhaven.com/license)

**Recommended first import:** one small neutral sample set only: a few rocks/terrain materials, a modular structure/roadside prop, and a handful of UI sounds. Build an automated source manifest and run the existing mesh/texture validators. Do not add hundreds of untouched files or commit a full downloaded pack simply because it is free.

### 8.2 Candidates that are not cleared for raw-file redistribution

- **Quaternius:** its newer Quaternius Asset License (QAL v1.0, updated 2026-08-28) allows game/product use subject to its conditions but restricts redistributing the assets themselves. Some older pack pages still advertise CC0; do not rely on that mismatch without verifying the exact downloaded pack/version and its included licence. For now, **do not commit Quaternius source pack files** into the public Boonta repository.
- **OpenGameArt engine-loop recordings:** a generic CC0 loop may be useful as a temporary audio-system placeholder, but it is not a faithful podracer sound design. Verify the exact audio file's licence/author before any inclusion; keep the final soundtrack and signature sound effects original or expressly licensed.
- **The Models Resource / model-rip mirrors:** useful only to identify what kinds of models exist or as private research references. A public download link does not grant redistribution rights; do not copy commercial model/texture/animation dumps.
- **SWE1R-Mods, Step 102 and extracted game folders:** may contain research leads and tool workflows, but mod files and the commercial game's extracted payload have separate rights. No wholesale import.

### 8.3 Tools help recover formats; they do not grant content rights

- `GCFT/gclib` (MIT) can inspect common GCM/DOL/REL/RARC/BTI/Yaz0/Yay0 and some J3D formats. No evidence yet that it reads Racer's proprietary course/model blocks.
- `decomp-toolkit`, Gekko-aware Ghidra tooling, `powerpc-rs` and `objdiff` are GameCube/Wii executable-analysis tools; they help understand our lawful local target and our own binary, not automatically recover all game assets.
- `swe1r-assets` and `swe1r-tools` document PC/N64-side formats; a matching extension or common block name does not establish target-console compatibility.
- `devkitPro/gamecube-tools/gxtexconv` is a GPL-2.0 TPL/GX texture converter reference; it is separate from the MIT project until a deliberate code-licence decision is made.

Keep commercial disc images, ROMs, DOL/REL files, extracted models, textures, voices and music local and out of GitHub, CI artifacts and hosted AI prompts. Use synthetic fixtures or CC0 sample inputs for public tests.

## 9. Provenance and versioning rules for every asset

Before a model, texture, audio clip, font, map, route or scene enters the public repository, record:

| Field | Required meaning |
|---|---|
| `asset_id` | Stable unique identifier used by the game |
| `category` | track, route, terrain, prop, pilot, pod, texture, material, animation, audio, UI, font, VFX, etc. |
| `source_url` | Exact source page or repository |
| `source_revision_or_download_date` | Commit/tag or download date/version |
| `author` | Original creator / credited author where known |
| `license_id` | Exact licence and included licence-file reference |
| `platform_scope` | PC, N64, GameCube, Wii, neutral CC0, or unknown |
| `source_format` | Original file format and relevant game/platform version |
| `source_sha256` | Hash of the exact lawful source file |
| `conversion_tool_revision` | Exact exporter/converter revision, if converted |
| `converted_sha256` | Hash of derived public output |
| `modifications` | Scale, topology, palette, texture, material and audio changes |
| `redistribution_rights` | Explicit public redistribution status, not just private-use rights |
| `status` | `CLEARED`, `LOCAL_ONLY`, `HOLD`, or `REJECTED` |
| `validation` | Parser/mesh/texture/audio test, native build and runtime result, as applicable |

Use `CLEARED` only when the exact asset file and all relevant dependencies have been reviewed. "Found online", "included in a ZIP", "used by another fan project", or "the tool is MIT" are not licence evidence for an original game's content.

## 10. Prioritised content acquisition and production plan

1. **Freeze this catalogue as the researched scope.** Convert names and groupings into small machine-readable content metadata only after the roster/course-source discrepancies and intended target version are labelled. This is factual metadata, not extracted asset data.
2. **Establish the exact permitted reference inputs privately.** The owner already has private PC/N64/game archives recorded in `docs/SOURCE_AND_ARTIFACT_REGISTER.md`; keep those local. Identify each executable/disc version and hash. Do not upload the archives or extracted payload to GitHub or hosted AI.
3. **Validate the local content extraction path.** For one locally owned sample only, identify the true container/format first. Test GCFT/gclib only if the file signature says it is a supported format. A PC or N64 parser success must not be reported as GameCube/Wii support.
4. **Start the public asset library with a tiny CC0 kit.** Pick a small subset from Kenney/Poly Haven, document file-level source and license, convert to our existing `boonta-mesh-v1` and GX texture pipeline, and add deterministic tests for mesh bounds, indices, UVs, palette/format and output hashes.
5. **Create the core art-production pipeline.** Define a route/course authoring format, mesh/material import pipeline, asset catalogue and deterministic exporters. Keep track geometry, surfaces, props, hazards, pilot/pod data and visual assets in separately testable groups.
6. **Build original course/world modules.** First prove one finished original course with terrain, props, collisions, triggers, audio and a minimap. Then reuse world kits to produce distinct route packages rather than cloning one oval 25 times.
7. **Build a pod roster system.** Use distinct clean-room pod designs and seven-stat physics profiles. Add pilots/portraits only where the distribution rights and character/IP boundaries permit; otherwise use original racer identities and silhouettes.
8. **Add the complete game loop.** Front-end, garage, part shop/junkyard, pit crew, credits, tournament unlocks, saves, results and selectable race modes all need deterministic data/state tests.
9. **Finish audio and presentation.** Engine/boost/heat/damage/impact/ambient/UI/announcer/music events; original or CC0 audio only. Keep memory and streaming constraints within GameCube/Wii budgets.
10. **Validate against the target separately.** Host parsers/tests, native DOL/ELF builds, Dolphin rendering/input, human-driven complete race and physical GameCube/Wii hardware are distinct evidence classes.

### Recommended production order

| Priority | Deliverable | Reason |
|---|---|---|
| P0 | Course/asset metadata schema + manifest + one validated CC0 import | Creates a lawful, repeatable content pipeline |
| P0 | One full original course package (route, scenery, surfaces, obstacles, start/finish, minimap) | Proves the actual content path end to end |
| P0 | Pod data schema + one high-quality original pod and distinct physics profile | Proves model, material, collision, audio and handling integration |
| P1 | Full racer/vehicle database and selection UI | Enables a scalable roster without duplicated code |
| P1 | Reusable eight-world environment kits and additional route packages | Scales course production to the 25-entry catalogue |
| P1 | Seven-stat parts, damage/repair, pit droids, shop and progression | Adds the key long-term vehicle loop |
| P1 | Race menus, championship/results/save state | Connects the content into a complete game |
| P2 | Audio/music/announcer, richer VFX, replay/multiplayer/options | Presentation and mode completion after core loop works |

## 11. Evidence limitations and explicit non-actions

- Course/world/racer/pod names are published reference metadata, primarily community-maintained. They are not proof of the exact content in an original GameCube/Wii build.
- The pod-model name list includes a "Bullseye Navior"/"Bullseye Namor" discrepancy. Do not normalise it without stronger evidence.
- No commercial ROM, disc image, binary, DOL/REL, model, texture, voice, music or extracted track data was copied into Boonta.
- No Step 102 file has been cleared by this document.
- No external asset pack was downloaded, imported, converted or measured in this pass.
- No claim is made that the original game's content is recoverable from a GameCube/Wii retail executable; no such retail Racer executable has been identified.
- No runtime, native build, Dolphin or physical hardware test was performed for this documentation-only update.

**Bottom line:** Boonta needs a real course/pod/world/audio/UI asset pipeline and a lawful content library, not another isolated procedural oval. This bill of materials makes the scope explicit while keeping the actual proprietary commercial assets outside the public repository.

## Machine-readable catalogue

The same reference names are available as a versioned, non-runtime JSON dataset at [`docs/research/data/SWE1R-CONTENT-REFERENCE-CATALOG-2026-11-10.json`](data/SWE1R-CONTENT-REFERENCE-CATALOG-2026-11-10.json). It contains 25 track records, eight world IDs, four championship records, 23 standard pilot identities, two N64 cheat replacements, 25 pilot/pod model-name references, seven upgrade categories, named high-tier part examples, provenance sources and an explicit current-Boonta content snapshot. It contains names and metadata only; no commercial game asset data.

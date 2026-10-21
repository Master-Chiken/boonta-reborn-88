# Source preservation ledger — Boonta Reborn 88

**Ledger date:** 2026-10-21  
**Purpose:** preserve every known GitHub research lead across sessions. This is an index, not a license clearance, code-import approval, or claim that a tool has been run against *Star Wars: Episode I – Racer*.

## Preservation rules

1. **Do not delete older sources because a newer or apparently better tool appears.** Add a new row and explain whether it supersedes, complements, or is unrelated to an older lead.
2. Pin exact commits for claims that depend on repository content. A repository's default branch is a moving target; when a commit is not recorded below, the current revision still needs to be captured before relying on it.
3. Label evidence by platform. PC findings do not establish N64, Dreamcast, GameCube or Wii behavior. Dreamcast method examples are not *Racer* evidence.
4. Keep commercial ROM/disc images, executables, extracted course records, proprietary assets and binaries local. This ledger stores public URLs and research decisions only.
5. Review repository and dependency licenses separately. A tool license does not license the original game or any extracted payload.
6. The locally maintained N64 note `RE-001_N64_STATE_AND_TRIGGER_TRACE_2026-10-21.md` is a research artifact in the owner’s ChatGPT Library; it is not a source repository and is not automatically present in GitHub. Its conclusions must remain N64-only.

## A. Research repositories and tools explicitly supplied or discussed by the project owner

| Source | Platform / role | Current use and limits | Pin / license status |
|---|---|---|---|
| [Dreamcast Disassembly, Debugging & Decompilation Diaries](https://github.com/AltoRetrato/Dreamcast-Disassembly-Debugging-and-Decompilation-Diaries) | Dreamcast reverse-engineering methodology; Ghidra, FID databases, Flycast GDB workflow and related tools | **Keep.** Methodology/tool discovery only; not a *Racer* decompilation. | The repository's current default branch is moving; record a commit SHA when using a specific instruction. No license determination recorded here. |
| [gditools3](https://github.com/AltoRetrato/gditools3) | Dreamcast GDI image listing/extraction and `IP.BIN` extraction | **Keep.** Possible local disc-inventory tool if a lawful GDI is available. README describes limited testing on Python 2.7, 3.4 and 3.7; verify compatibility before depending on it. | No pinned commit/license audit recorded here. Do not place extracted game files in this repository. |
| [tbg-decomp](https://github.com/lhsazevedo/tbg-decomp) | Dreamcast SH-4 decompilation, function-equivalence testing and SH-4 object simulation | **Keep.** Strong example of a functional-equivalence workflow for a Dreamcast game, but it targets *Tokyo Bus Guide*, not *Racer*. | No exact commit/license audit recorded here; pin before citing particular functions or adapting any code. |
| [recv-dc-decomp](https://github.com/fmil95/recv-dc-decomp) | Dreamcast SH-4 executable splitting/build setup; *Resident Evil Code: Veronica* | **Keep.** Secondary example for a Dreamcast `1ST_READ.BIN` workflow, not evidence about *Racer*. It relies on the proprietary Katana SDK/toolchain. | No exact commit/license audit recorded here. Do not copy game code or SDK files. |
| [Flycast](https://github.com/flyinghead/flycast) | Dreamcast emulator and potential runtime/debug validation | **Keep.** Potential runtime debugger/emulator for a legally obtained local build; not a source of *Racer* implementation semantics by itself. | Pin the tested release/commit and debugger configuration in any future test log. |
| [decomp.anything](https://github.com/giveen/decomp.anything) | Local reverse-engineering workbench for N64 MIPS and GameCube/Wii binaries | **Keep; already audited.** Candidate for inspecting the local N64 ROM's code/data and, separately, our own GameCube/Wii DOL. It is not a ready-made *Racer* spline decoder and its presence does not validate every loaded overlay. | Inspected at [`fd8c15ea975678ae32f70988440c1fdbeac1405c`](https://github.com/giveen/decomp.anything/tree/fd8c15ea975678ae32f70988440c1fdbeac1405c); repo declares MIT. Dependencies and toolchains retain separate licenses. |
| [sp00nznet/racer](https://github.com/sp00nznet/racer) | N64-targeted *Star Wars: Episode I – Racer* static-recompilation / analysis lead | **Keep; high relevance to N64 code research.** Use named functions/symbols as leads and cross-check addresses against the locally identified US ROM. A static-recompilation project is not automatically proof of retail runtime behavior. | Reviewed at [`11f6f70469f995304422f2209a47e9c2df5ff6d0`](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0). Reconfirm license and target ROM identity before reuse. |
| [sp00nznet/recompclass](https://github.com/sp00nznet/recompclass) | Educational N64 MIPS/static-recompilation material; route to the `unit-6-console-architectures/module-20-n64-mips/lecture.md` lesson | **Keep as a methodology/source-discovery lead.** Not a *Racer* implementation source. | Use the precise lesson URL and revision when citing; license not audited in this ledger. |
| [Wii64 / Cube64](https://github.com/emukidid/Wii64) | N64 emulator compatibility lead for Wii homebrew | **Keep, but separate from native GameCube development.** Running an N64 game under Wii64 is not a native port or HD enhancement. | Record emulator revision, settings and lawful user-supplied ROM identity if tested. |
| [SWE1R tools](https://github.com/OpenSWE1R/swe1r-tools) | PC-format extractors and research utilities; README explicitly labels the `decompress.c` model-block chunk decoder as N64-specific | **Keep.** Reuse-first reference for existing parsers, with each parser's supported format checked separately. Its N64 decompressor does not imply that PC spline parsers accept N64 records. | Historical audit records GPL-2.0-or-later; pin file/revision and recheck dependency terms before adapting code. |
| [SWE1R asset tools](https://github.com/akopetsch/swe1r-assets) | PC model/spline/sprite/texture block reader/writer | **Keep; high priority for PC format cross-checks.** Bit-identical no-op reserialization tests are useful methodology, not proof of console-format equivalence. | Reviewed at [`922ef535f6598a1330ff93d6b07258956f990b34`](https://github.com/akopetsch/swe1r-assets/tree/922ef535f6598a1330ff93d6b07258956f990b34); MIT code license recorded in the existing source register. |
| [swe1r-assets-unity](https://github.com/akopetsch/swe1r-assets-unity) | Sample Unity workflow on top of swe1r-assets | **Keep as a secondary experiment.** Work-in-progress importer/editor reference, not a required dependency for Boonta. | Check exact revision, dependencies and license before adapting. |
| [blender-swe1r — OpenSWE1R repository](https://github.com/OpenSWE1R/blender-swe1r) | Blender import/export of *Racer* models/splines | **Keep.** Useful for route topology and parser hypotheses. Treat exporter constraints as tool limitations unless independently proven to be game-engine limits. | Repository currently identifies GPL-3.0; pin the exact parser version used. |
| [blender-swe1r — historical pinned path](https://github.com/louriccia/blender-swe1r/blob/b0d4019addb97d51523019ca1233411fae0508d6/splineblock.py) | Historical Blender spline parser citation already referenced by the schema audit | **Keep this exact historical link as well as the current repository link.** Do not silently replace a historical source citation with a moving repository. | Pinned commit `b0d4019addb97d51523019ca1233411fae0508d6`; GPL-3.0 status is recorded in the existing schema notes. |
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Primary PC function/symbol/reverse-engineering research | **Keep; central PC behavioral reference.** It documents/reimplements selected functions, not a complete executable end-to-end reference; key route/progress functions are stubs in the revision studied. | Reviewed at [`a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab); AGPL-3.0 recorded. No code imported. |
| [swep1r_decomp](https://github.com/DeonPoncini/swep1r_decomp) | Frozen Steam-PC Ghidra decompilation; function bodies used to cross-check incomplete PC source reconstructions | **Keep read-only.** Independent PC evidence only; not proof of console parity. | Reviewed at [`d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef`](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef). No root license was found in the prior audit; do not copy/adapt code. |
| [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) | Historical open PC-port/emulation architecture | **Keep secondary.** Useful architectural study; still depends on original binary/assets in areas and is not a GameCube/Wii port. | Existing audit records GPL-2.0 and deprecated status; recheck the current README before making new status claims. |
| [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re) | Historical PC reverse-engineering notes | **Keep secondary for corroboration.** Ensure each claim names the PC build/version. | Pin source revision and executable identity for every result. |
| [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | Community modding, unpack/repack workflows and examples | **Keep as a discovery index only.** Extracted assets and third-party scripts require separate provenance review. | Repo-wide licensing/provenance not established in the prior audit; no assets/scripts imported. |
| [swe1r-patcher](https://github.com/JayFoxRox/swe1r-patcher) | Legacy PC patching and compatibility leads | **Keep for behavioral leads only.** Earlier register records no-commercial-use/no-redistribution restrictions. Do not reuse patcher code or output. | Review its exact license/version before citing or doing anything beyond read-only study. |
| [Star-Wars-Episode-I-Racer-PCVR](https://github.com/GameOrDie007/Star-Wars-Episode-I-Racer-PCVR) | PCVR/OpenXR fork | **Keep low priority.** Potential hook/renderer comparison, not core gameplay baseline. | Pin the fork revision; inspect upstream changes separately. |
| [PitDroidModManager](https://github.com/OpenSWE1R/PitDroidModManager) | PC mod-loader architecture | **Keep as architecture-only unless a concrete need appears.** A PC DLL loader likely does not transfer to native GameCube/Wii. | Existing register records Apache-2.0; recheck revision and dependencies before adapting. |
| [Sw_Racer](https://github.com/Olganix/Sw_Racer) | Older model-block conversion tooling | **Keep as secondary parser comparison.** | Existing register records GPL-2.0-or-later; use only after file and license review. |
| [ep1-racer-save-editor](https://github.com/jcfieldsdev/ep1-racer-save-editor) | PC save-data format research | **Keep as secondary evidence.** README reportedly credits swe1r-tools; do not treat it as independent confirmation of that same format claim. | Existing register records GPL-3.0; pin and recheck before reuse. |

## B. Other public references already in the project research

| Source | Why it is retained | Evidence boundary |
|---|---|---|
| [BizHawk issue #2603](https://github.com/TASEmulators/BizHawk/issues/2603) | N64 emulation/capture/synchronization behavior lead | Community/emulator report, not a course-format or GameCube finding. |
| [N64-Documentation — Expansion Pak games](https://github.com/supavgx/N64-Documentation/blob/main/WIP%20custom%20docs/ExpansionPakGames.md) | Secondary clue about N64 Racer's high-resolution/Expansion Pak mode | Needs independent version-specific validation; not an implementation spec. |
| [StarWars.com — Racer legacy overview](https://www.starwars.com/news/star-wars-episode-i-racer-legacy) | Official high-level feature context | Not internal technical behavior evidence. |
| [StarWars.com — producer interview](https://www.starwars.com/news/star-wars-episode-i-racer-interview) | Official retrospective context on N64 release/design | Does not prove that later PC or console versions share internals. |
| [Steam product page](https://store.steampowered.com/app/808910/STAR_WARS_Episode_I_Racer/) | PC rerelease/platform metadata | Product information only. |
| [PCGamingWiki — SWE1R](https://www.pcgamingwiki.com/wiki/SWE1R) | Compatibility/version behavior leads | Pin the claim and corroborate it against a named build. |
| [Racer Wiki](https://starwars-racer.fandom.com/wiki/Star_Wars_Episode_1:_Racer_Wiki) | Community terms, track names and player-facing behavior | Discovery only; independently confirm technical claims. |

## C. Supporting non-GitHub leads (kept so they do not disappear from the research trail)

- [Dreamcast technical documentation by Marcus Comstedt](https://mc.pp.se/dc/) — general Dreamcast hardware/programming reference, not a *Racer* implementation source.
- [REA](https://rea.tools/) — separately identified native-binary/runtime-analysis tool lead encountered during research. **It has not been established that this is related to `borer.lol`**; keep those names separate unless the owner supplies confirming evidence.
- `https://borer.lol` — owner-supplied lead; the site could not be reliably identified during the prior pass. Preserve the URL as unresolved rather than guessing what product it represents.

## D. Active work threads and canonical Boonta documents

- [Issue #226 — active research queue, RE-001 route/spline progression](https://github.com/Master-Chiken/boonta-reborn-88/issues/226)
- [PR #242 — research-first operating model; remains open/unmerged unless GitHub says otherwise](https://github.com/Master-Chiken/boonta-reborn-88/pull/242)
- [RE-001 PC route/spline dossier](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/research/RE-001-route-spline-progress.md)
- [RE-001 schema compatibility matrix](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/research/RE-001-schema-compatibility-matrix.md)
- [Cross-platform reference matrix](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/CROSS_PLATFORM_REFERENCE_MATRIX.md)
- [Source and artifact register](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/SOURCE_AND_ARTIFACT_REGISTER.md)
- [Step 102 source/provenance audit](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/STEP102_SOURCE_PROVENANCE.md)
- [Wii64 reference tools](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/WII64_REFERENCE_TOOLS.md)
- [Dreamcast build status](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/DREAMCAST_BUILD_STATUS.md)

## E. Current next research action

Continue the N64-only trace from the local reference note. The best established chain currently links a cursor/geometry-derived scalar from `0x80080BEC` into participant field `+0x74`, followed by ranking updates to `+0x5C`. It **does not yet establish** physical distance units, lap wrap, or the HUD lap-counter writer. Next inspect the indexed accumulation around `+0x78`, the manager bound at `+0x1C8` set from a `Begn` message, and downstream finish/state handlers. Keep ROM-derived binary bytes, extracted route data and asset payloads local; publish only evidence notes and public source links.

**Ledger policy:** when another URL appears in the conversation, append it here with a short description and a platform/license caveat. Do not rely on chat memory alone as the permanent source list.


## F. New cross-check lead — N64 lap RAM cheat codes (2026-10-21)

- [TheForce.Net — Episode I Racer N64 codes](https://www.theforce.net/videogames/codes/n64/racer.asp): the page lists “Start on Lap” and “Always on Lap” code addresses at `0x8011900A` for Player 1 and `0x80119092` for Player 2, a difference of `0x88`.
- **Disposition:** retain as an old community RAM-code lead, not as verified disassembly or a confirmed mapping to `Jdge +0x78` or `+0x1C8`. It provides an external target for a later lawful memory-watch/cross-reference test. Check version/region assumptions and do not name the field or infer whether it is zero-based until a runtime or code path confirms it.
- Private local follow-up note: `RE-001_N64_HUD_LAP_FIELD_CROSSCHECK_2026-10-21.md` (kept in the owner's ChatGPT Library; not committed with ROM-derived data).
- The main remaining gap is the HUD writer for `LAP` / `FINAL LAP` and its current/configured value pair. Keep the source string data and ROM-derived output local.



## G. Official agent-workflow documentation checked 2026-10-21

- [Jules documentation](https://jules.google/docs/) — current setup guide says Jules works in a cloud VM, produces a plan before changes, and automatically reads root AGENTS.md. Use this to ground task routing; Jules still cannot see files that exist only in the owner's ChatGPT Library/computer.
- [Jules changelog](https://jules.google/docs/changelog/) — current product changelog. Consult before relying on newer agent behavior such as GitHub integration or CI-failure handling.
- [GitHub Copilot cloud agent task guide](https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/kick-off-a-task) — states cloud agent access is available on paid Copilot plans. The project default stays €0 and therefore excludes it unless the owner already has access and explicitly elects to use it.
- [Boonta shared agent playbook](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/MULTI_AGENT_RESEARCH_PLAYBOOK.md) — repository-specific task routing, current roles, exact boundaries, and the three overlapping steering-deadzone PRs used as a concrete duplicate-work example.
- [Boonta AI workflow rules](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/AI_AGENT_WORKFLOW.md) and [root agent instructions](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/AGENTS.md) — authoritative local rules for Gemini CLI, data/privacy, write gates, and every contributor's handoff expectations.


## H. N64 CPU address-space reference verified during RE-001 (2026-10-21)

- [Nintendo 64 Introductory Manual — CPU address map](https://ultra64.ca/files/documentation/online-manuals/man/kantan/step1/1-4.html): source for the 32-bit KUSEG, KSEG0 (direct-mapped/cacheable), KSEG1 (direct-mapped/non-cacheable), KSSEG and KSEG3 ranges. Used to correct the shorthand in the Gemini audit: KSEG0 is the wider 0x80000000–0x9FFFFFFF segment, while 0x80000000–0x803FFFFF is only a narrow 4 MiB RAM-range assumption. Keep this technical clarification separate from lap-field semantics.
- [n64docs virtual memory map](https://n64.readthedocs.io/): accessible explanatory reference for the same address-space distinction.


## I. N64 lap-state cheat-code evidence added 2026-10-21

- [TheForce.Net — Episode I: Racer N64 codes](https://www.theforce.net/videogames/codes/n64/racer.asp): explicitly labels `8111900A 00??` as Player 1 “Start on Lap” / “Always on Lap” and `81119092 00??` as the corresponding Player 2 codes; values `00–04` are labelled laps 1–5. Treat this as public documentation of cheat-target semantics, not source-level disassembly.
- [GameRevolution — Star Wars: Episode I: Racer N64 cheats](https://www.gamerevolution.com/guides/28992-star-wars-episode-1-racer-cheats): independent corroboration of `8111900A0002` as Player 1 “Start On Lap 3.”
- [sp00nznet/racer pinned at `11f6f70469f995304422f2209a47e9c2df5ff6d0`](https://github.com/sp00nznet/racer/tree/11f6f70469f995304422f2209a47e9c2df5ff6d0): public N64 static recompilation reference. The checked-in [README](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/README.md) says no N64 decompilation exists; `symbols.toml` is not a source-level definition of lap state. The [IDA handoff](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/docs/IDA_ANALYSIS_HANDOFF.md) names a local Windows decompilation path that is not included in the public repository.
- **Interpretation:** high confidence that the cheat listings intend these two addresses to set/hold the corresponding player's lap value; the `0x88` address difference is consistent with corresponding player-state locations but is not proof of a shared struct layout. Exact retail revision, native writer/increment routine, finish crossing and HUD consumer remain unknown.
- Keep the source links and version caveats in future updates; do not upload a ROM, full memory dump, local disassembly or extracted game data.


## J. PC HUD analogue preserved as a non-parity reference

- tim-tim707/SW_RACER_RE, pinned at a9863edd4caaa573f89ff634fa7d1cd6d41738ab (https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab) — PC/Windows only.
- src/Swr/swrRace.c, function swrRace_InRaceTimer / PC address 0x00460950: source of the PC in-race HUD's lap fraction, lap-time popup, LAP TIME, FINAL LAP, LAP, POS and text resource identifiers.
- src/Swr/swrObj.c, function swrObjJdge_F2 / PC address 0x0045EA30: reference for how the PC implementation increments the lap counter after a route-progress crossing and handles the configured lap threshold.
- Use limit: these PC functions are comparison leads only. They do not prove N64 implementation, resource IDs, structure layouts, or control-flow parity. N64-specific claims must stay based on N64 local static/dynamic evidence and the independently labelled public GameShark documentation.

## K. N64 HUD display data flow cross-check

- Local-only static trace on the user's US N64 build now connects the HUD's current/configured lap fraction to the previously traced participant progression counter and manager threshold. Displayed current value is participant count + 1 clamped to the configured target; the target value comes from the same manager threshold.
- The second %d/%d template is position / total racer count and pairs with POS.
- The FINAL LAP text is directly referenced by the same HUD function. Its branch compares the next displayed lap with the configured target, requires the single-local-player HUD layout, and is fade-gated to the lap-completion popup.
- Keep raw instruction addresses, exact ROM string offsets, disassembly, and derived binary data in the owner's local notes. The public dossier contains only summary findings.
- Status: high confidence in N64 HUD lap-counter and FINAL LAP selection data flow based on local static code; runtime observation and physical finish-line timing remain unverified. Do not infer PC/DC/GameCube/Wii parity.
## L. Manager results-screen transition remains an open question

- Local-only static follow-up examined the manager phase dispatcher, timer/event branches and manager-side local-player threshold check. The threshold/HUD path is traced, but no conclusive caller-to-results-renderer or scene-load edge has been demonstrated.
- Generic `Fini` / `Abrt` lifecycle tags and phase-bit changes are not enough to identify the terminal race/results transition; keep them semantically unnamed until the destination path is proven.
- An ASCII search for plain uppercase results/finish terms found no obvious literals, but this is weak negative evidence only because text may be encoded/compressed/resource-based.
- The user environment currently has no N64 emulator/debugger or Dolphin CLI in PATH; no runtime test has been performed.
- Next: trace the all-local-participants-done condition into the lifecycle-phase writer and from there into a positively identified results UI resource/scene selection. No gameplay code/assets changed.
## M. Lifecycle-tag semantics do not prove the race-results destination

- A local static pass reviewed the phase-dispatch table and the generic tag consumer. `Fini` / `Abrt` route through general object lifecycle/state handling (object flags, timers and shared fade/control state); the consumer also handles `Load`, `RStr`, `Stop` and other tags, and is called beyond the targeted race-manager path.
- The current static evidence does not show a conclusive direct edge from the all-local-participants-done condition to a positively identified results renderer or scene-load handler. Do not infer results semantics from tag strings or phase names alone.
- Lap counter + `FINAL LAP` HUD selector are traced; manager/results-screen destination remains open. The next target is a call/data-flow chain from the all-done predicate through the manager phase writer to an actual results UI/resource selection.

## N. PC results-transition analogue — exact pinned source and limits (2026-10-21)

- `tim-tim707/SW_RACER_RE` pinned commit [`a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab), PC/Windows reference only.
- [src/Swr/swrObj.c lines 918–970](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c#L918-L970): `swrObjJdge_F2` provisionally sets state 2 (“all local racers finished”), then re-arms state 1 while eligible local racers remain in progress.
- [src/Swr/swrObj.c lines 800–875](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c#L800-L875): state 4 is the post-race camera sweep; a skip path sets `swrRace_resultsScreenActive` immediately, while normal sweep completion advances to state 5 and state 5 sets the flag on its own handler pass.
- [src/Swr/swrRace.c lines 320–340](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c#L320-L340): `swrRace_ResultsMenu` is described as the post-race results-screen routine, including score sorting, record/name-entry handling and tournament progression/save work.
- Interpretation boundary: this gives a useful PC comparison map but does not prove any N64 state number, flag, event, structure, or call path. The N64 results destination remains unproven by current local static evidence; no runtime test is claimed. Keep ROMs, extracted assets and raw disassembly local.

## O. Public N64 static-recompilation boundary check — 2026-10-21

- Pinned source: [sp00nznet/racer README](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/README.md#L22-L24), [function section table](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/src/section_table.cpp#L647-L653), and [symbol table](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/symbols.toml#L3229-L3232).
- Direct observation: the project README describes static recompilation and says there is no N64 decompilation. The public tables expose only the generic function boundary `func_80080BEC` (section offset `0x807EC`, size `0x5F0`, VRAM `0x80080BEC`), not its semantic body or a results-screen call/data-flow chain.
- Bounded searches for the function label/address and generic lifecycle tags did not locate a positive results-renderer edge in the reviewed public repository. This is a scoped negative result only; it does not prove no other public source exists.
- Decision: do not assign results semantics from a generic function name or transfer the pinned Windows-PC result-state model to N64. The PC source is a comparison checklist only.
- Next local check: follow the exact manager state/phase field write after the all-local-participants-done predicate; enumerate readers of that field; trace onward to a positively identified result UI/resource/scene selector. If no positive destination appears, keep the blocker explicit.
- No ROM, disc image, extracted asset, raw local disassembly, or private binary offset is included in this public ledger. No gameplay code was changed and no runtime test is claimed.

## P. Runtime-debugging method reference — methodology only (2026-10-21)

- [Finding Jingle Town: Debugging an N64 Game without Symbols](https://blog.chrislewis.au/finding-jingle-town-debugging-an-n64-game-without-symbols/) documents an Ares + GDB remote-debugging workflow that tests a hypothesis using breakpoints and observed state values.
- [Using Coding Agents to Decompile Nintendo 64 Games](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/) explains that matching a function's assembly is distinct from understanding its role; cross-references and call-site behavior are needed for semantic naming.
- Scope warning: both articles concern Snowboard Kids 2, not SWE1R. They are methodology references only, not evidence of any SWE1R function's semantics and not source code to import.
- Proposed test, if a suitable lawful local setup is available: break at the locally identified all-local-done branch, record the manager field write, inspect readers of that exact field, follow the first camera/input and UI/resource destination, and confirm the transition in a controlled runtime. Preserve exact ROM/build identity and repeatability in local notes; publish only a short supported summary.
- Status: not executed here. No local SWE1R ROM, emulator/debugger, or runtime evidence was accessed by this public-source check.

## Q. Public symbol-table coverage check — RE-001 (2026-10-21)

Audited `sp00nznet/racer` at [`11f6f70469f995304422f2209a47e9c2df5ff6d0`](https://github.com/sp00nznet/racer/commit/11f6f70469f995304422f2209a47e9c2df5ff6d0). Its README says this is a static recompilation and that no N64 decompilation exists for the game. Its public `symbols.toml` contains 880 function entries; most remain generic. `render_submit` is named at 0x800181BC, but there is no published proof that it renders the results screen. `func_80080BEC` remains generic at 0x80080BEC (size 0x5F0), mapped by `src/section_table.cpp` to offset 0x807EC and the same size.

Repository links: [README](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/README.md), [`symbols.toml` candidate](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/symbols.toml#L3229-L3232), [section table mapping](https://github.com/sp00nznet/racer/blob/11f6f70469f995304422f2209a47e9c2df5ff6d0/src/section_table.cpp#L647-L653). Public tree inspection found no tracked generated `RecompiledFuncs/` output or public semantic call graph linking the all-local-done branch to a results resource/scene selector. Search absence is bounded evidence only.

Decision: do not rename `render_submit` or `func_80080BEC`, do not infer a results transition from generic phases/tags, and do not change gameplay code. RE-001 remains blocked pending a permitted local runtime trace or a separately published semantic analysis. No ROM or assets were accessed/uploaded by this pass.

## R. Public N64 debug-menu references — test lead only (2026-10-21)

- [GameFAQs N64 cheats](https://gamefaqs.gamespot.com/n64/198780-star-wars-episode-i-racer/cheats), [N64 FAQ](https://gamefaqs.gamespot.com/n64/198780-star-wars-episode-i-racer/faqs/2522), and [Ethereal Games guide](https://etherealgames.com/n64/s/star-wars-episode-i-racer/cheats-secrets-tips-tricks/) describe an in-game `RRDEBUG`/debug-menu flow and controls including fast-forward/rewind.
- Evidence type: community gameplay documentation only. It is not source-level evidence and does not identify the race manager state field, its readers, or a results UI path.
- Potential use: could aid reproducible local testing if supported by the game revision; it cannot replace memory breakpoints/cross-reference tracing. Region/version compatibility is unverified.
- Status: lead recorded only. No runtime test, ROM access, asset extraction, or gameplay change.

## S. Platform boundary — older OpenSWE1R sources (2026-10-21)

- The [OpenSWE1R/swe1r-re repository page](https://github.com/OpenSWE1R/swe1r-re) states its function documentation is based on a Windows patch executable. Treat it as PC analysis, not N64 proof.
- The [OpenSWE1R/openswe1r README](https://github.com/OpenSWE1R/openswe1r) describes a Windows/x86-focused compatibility project and lists other platforms, including N64, as possible future support rather than the baseline. The user-owned [Master-Chiken/openswe1r fork](https://github.com/Master-Chiken/openswe1r) reflects the same project lineage.
- License caution: OpenSWE1R is GPL-2.0-or-later; no source was imported. Keep function names/behavior as PC-only cross-reference leads unless N64-specific evidence independently confirms them.
- No proprietary executable was downloaded or inspected, no runtime test was done, and no N64 semantic conclusion changed.


## T. N64 lap code addresses — public cheat-list evidence only (2026-10-21)

- Source: [TheForce.Net N64 Episode I Racer code list, lines 88–99](https://theforce.net/videogames/codes/n64/racer.asp). It labels GameShark writes to `0x8011900A` as “Start on Lap” / “Always on Lap” for Player 1 and `0x80119092` for Player 2, with `00`–`04` labelled Lap 1–5.
- Both target addresses differ by `0x88`. The same difference appears in the page's paired “Low Timer” locations (`0x80119004` / `0x8011908C`) and “Always Place First” locations (`0x80118FED` / `0x80119075`). This is moderate evidence for a repeated two-player address layout, not proof of a C struct or a global racer-record stride.
- **Supported:** these are documented lap-related cheat target addresses. **Not supported:** direct ownership by a participant struct, exact native type/offset, final-lap/finish semantics, reads by a race manager, or any connection to a results renderer/scene selector.
- Evidence is community cheat documentation, not disassembly or a controlled local memory trace. No runtime test was run. Keep as watchpoint candidates only.
- Minimal verification: in a lawful local debugger, observe the P1/P2 addresses across lap changes, identify the writers/readers, and separately trace the final-lap completion condition to the actual results UI/resource selector. If unavailable, preserve the blocker. No ROM/assets uploaded or committed.


## U. Ares/GDB runtime-trace preparation — tool feasibility, not game proof (2026-10-21)

- [Chris Lewis' debugger walkthrough](https://blog.chrislewis.au/finding-jingle-town-debugging-an-n64-game-without-symbols/) demonstrates Ares + `gdb-multiarch`, MIPS architecture selection, remote attachment, breakpoints, and raw memory inspection on Snowboard Kids 2. It is a workflow reference only; it is not SWE1R evidence.
- [Ares issue #1778](https://github.com/ares-emulator/ares/issues/1778) reported an N64 GDB attach/continue crash (v140–v141/bleeding edge) in January 2025. The issue timeline records the fix commits [`c8ddc5d`](https://github.com/ares-emulator/ares/commit/c8ddc5d) and [`dfcd7d4`](https://github.com/ares-emulator/ares/commit/dfcd7d4), and linked issue [#1793](https://github.com/ares-emulator/ares/issues/1793) marked the report completed on 2025-01-26.
- The latest non-prerelease upstream release returned in the 2026-10-21 release check is [Ares v148](https://github.com/ares-emulator/ares/releases/tag/v148), published 2026-05-30. Its tag is 812 commits ahead of and zero commits behind the merged fix commit, so the fix is included in its ancestry.
- Interpretation: the historical fixes alone do not prove current host/version compatibility. A separate source audit in section V below verifies that the reviewed Ares N64 implementation has memory-watchpoint hooks; end-to-end operation with SWE1R remains untested. Use the selected build's configured port; public examples mention different ports.
- Recommended gate before any game-specific trace: start with official stable [Ares v148](https://github.com/ares-emulator/ares/releases/tag/v148), record Ares/GDB versions, and attach to the small public homebrew test case linked from #1778. Verify the second `continue` after a breakpoint at `main`; if v148 fails, record that result before comparing it separately with a nightly build. Only then try the lawful local game and inspect lap-address candidates `0x8011900A` / `0x80119092` during lap changes. Follow actual writes/readers and the race-manager condition to a positively identified results UI/resource/scene. If the setup or semantic path fails, record the blocker and do not infer.
- Status: **not executed in this pass**. No ROM/game binary/assets were accessed or uploaded and no gameplay code changed.


## V. Ares N64 watchpoint implementation audit — source verified, test pending (2026-10-21)

Pinned Ares code revision: [`9408cb43d4948fc3ea6e152a307a34348df3fe04`](https://github.com/ares-emulator/ares/commit/9408cb43d4948fc3ea6e152a307a34348df3fe04).

- The [GDB server documentation](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/nall/nall/gdb/Readme.md) documents read/write/access watchpoints and the address-normalization hook.
- The N64 target sets `normalizeAddress` via `cpu.devirtualizeDebug` ([system.cpp lines 162–165](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/system/system.cpp#L162-L165)); its CPU read/write methods report memory events ([memory.cpp lines 166–193](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/cpu/memory.cpp#L166-L193)); and the recompiler includes active watchpoint state in its key ([recompiler.cpp lines 252–262](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/cpu/recompiler.cpp#L252-L262)).
- **Conclusion:** N64 memory-watchpoint support is present in the reviewed source; live behavior with a current Ares build and SWE1R is untested. This improves the runtime test plan but does not identify the lap writer/reader or close the results-screen transition.
- Next: smoke-test attach/breakpoint/continue on the open homebrew `ctest.z64` reproducer referenced by [Ares issue #1778](https://github.com/ares-emulator/ares/issues/1778); then test a watchpoint against a documented lap-address candidate in a lawful local game copy, using the actual configured port. Follow the observed field into the race manager and positively identified results UI/resource/scene selector. If this fails, record the precise failure and preserve the blocker.
- No emulator test was performed in this pass; no ROM or proprietary asset was accessed or committed. No gameplay source changed.



## W. Concrete GDB watchpoint procedure — prepared, not executed (2026-10-21)

A local-only test checklist was added to the RE-001 dossier. It uses the reviewed Ares default debug port `9123` as a starting value, but requires the operator to read the actual configured port. The Ares UI warns that **Use IPv4** binds to any device and may expose the debug server to the network; prefer its local-only mode unless the host setup specifically requires IPv4, and restrict access if used.

Use official stable [Ares v148](https://github.com/ares-emulator/ares/releases/tag/v148) as the first baseline; the fix for issue #1778 is present in its ancestry. Avoid a nightly build for the first attempt so the baseline is a published release. If it fails, capture that result before doing a separately reported nightly comparison.

First reproduce Ares issue [#1778](https://github.com/ares-emulator/ares/issues/1778) with its public [attached `ctest.zip`](https://github.com/user-attachments/files/18465249/ctest.zip) (built from [libdragon's ctest example](https://github.com/DragonMinded/libdragon/tree/trunk/examples/ctest)). Keep it out of the repo. In the extracted folder, run:

```sh
gdb-multiarch -ex "target extended-remote :9123" -ex "break main" -ex "continue" build/ctest.elf
```

Then quickly launch `./ares ctest.z64` from the directory holding that ROM. Use the actual configured port and record whether attach → breakpoint at `main` → second continue succeeds. This is a generic debugger smoke test only, not a SWE1R test. Only after that passes, a lawful local game copy may be tested with:

```text
gdb-multiarch
(gdb) set architecture mips:4000
(gdb) target extended-remote localhost:9123
(gdb) x/2hx 0x8011900a
(gdb) watch *(unsigned short *)0x8011900a
(gdb) info watchpoints
(gdb) continue
```

Capture PC/registers and the observed value around each stop, then follow the writer/reader chain. The 16-bit expression is a trial based on the public cheat-code encoding, not a verified native type. Official GDB documentation says `watch` fires when the expression value changes; absence of a stop alone cannot prove absence of writes. Ares source supports read/write/access watchpoint packets, but live attach, packet negotiation, stop timing and SWE1R behavior remain **untested**. See dossier section W for the full guardrails and exact file/line links. No game was run or binary/assets uploaded in this pass.


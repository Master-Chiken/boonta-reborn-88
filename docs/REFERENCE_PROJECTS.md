# Relationship to existing SW_RACER_RE research

## Reference repository

The public repository [tim-tim707/SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) is a related PC-game decompilation and modding research project. Its README says the goal is to document and re-implement some original game functions, not to produce a matching compilation or a complete decompilation. The README identifies `data_symbols.syms` and generated hook functions as important project sources of truth, and describes a separate PC `dinput_hook/` HD replacement renderer.

This makes it a useful **research reference** for understanding documented PC-side behavior, symbol names, function roles and existing modding work. It is not itself a ready-made GameCube/Wii port, and its PC renderer is a separate architecture.

- Project: https://github.com/tim-tim707/SW_RACER_RE
- README: https://github.com/tim-tim707/SW_RACER_RE/blob/master/README.md
- License file: https://github.com/tim-tim707/SW_RACER_RE/blob/master/LICENSE

## Licensing and content boundary

At the time of this review, the repository declares **AGPL-3.0**. That licence is a material difference from this repository's MIT license. Do not copy code across repositories without deciding how the resulting licensing should work and preserving the required notices. This documentation page contains no copied implementation code.

The reference repository also has substantial binary data under `assets/custom_tracks/` and other asset folders. The existence of the AGPL license file must not be treated as automatic proof that every game-derived model, texture, spline, dump or other asset can be redistributed. Do not bulk-copy those assets, extracted game data, binaries or ROM/disc content into Boonta Reborn 88.

The same provenance rule applies to the supplied Step102 ZIP: its README identifies mod-derived PC course centerlines, and the ZIP does not provide a license covering the source tree as a whole. Step102 was therefore brought into the draft branch only as a source-only subset, with those centerlines/assets excluded. **The Step102 source itself still needs an authorship/licensing review before PR #17 is merged.**

## Practical integration plan

1. Use SW_RACER_RE as a linkable reference for documented game behavior and for choosing questions to investigate; cite the relevant file/function when recording findings.
2. Translate useful findings into independent, platform-appropriate code and tests for the GameCube/Wii target. Do not import PC hook code and assume it will compile on libogc.
3. Keep a short mapping document for each behavior (PC reference, independent GC/Wii implementation, test proving the behavior). Start with controller mapping, race progression, physics/boost/heat, track traversal and save data.
4. Only revisit any code or asset transfer after the actual file's author, license and redistribution scope have been checked.

This is a technical and provenance workflow, not legal advice.

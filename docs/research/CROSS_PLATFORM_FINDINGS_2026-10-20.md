# Cross-platform findings — 2026-10-20

These are preliminary source-backed findings, not runtime-verified facts.

| Topic | Finding | Status |
|---|---|---|
| Core gameplay | Official retrospective identifies overheating, shortcuts, hazards and local split-screen among defining features. | DOCUMENTED; broad features only. |
| Cinematics | Secondary history reports PC/Mac cinematics absent on N64 due to cartridge constraints; a contemporary Dreamcast preview advertised prerendered cinematics. | DOCUMENTED; verify exact regional releases. |
| Audio | Reviews report a reduced N64 soundtrack compared with PC/Dreamcast. | DOCUMENTED by reviews; no track-by-track comparison yet. |
| Graphics | N64 Expansion Pak supports a high-resolution mode; Dreamcast was advertised as higher resolution. | DOCUMENTED; does not prove shared assets or renderer. |
| Dreamcast online time comparison | Mentioned in a contemporary preview; actual implementation/service status not verified. | ANNOUNCED, not runtime-confirmed. |
| Exact track/racer/mode parity | Not inventoried by identified build/region. | UNKNOWN. |
| N64-specific data | Pinned OpenSWE1R/swe1r-tools README says its Comp model-block decompressor applies only to N64. | STATIC-DOCUMENTED; evidence of at least one platform-specific data path. |

## Sources

- Official overview: https://www.starwars.com/news/star-wars-episode-i-racer-legacy
- Contemporary Dreamcast preview: https://www.gamespot.com/articles/star-wars-episode-i-racer-preview/1100-2540691/
- N64 review: https://www.nintendolife.com/reviews/n64/star_wars_episode_i_racer
- Dreamcast review: https://www.gamespot.com/reviews/star-wars-episode-i-racer-review/1900-2557867/
- Pinned tooling README: https://github.com/OpenSWE1R/swe1r-tools/blob/239911513834e19d1530fc908b6dc40eabea25fc/README.md

## Next checks

1. Inspect version-pinned PC source files for track/racer/race-mode tables and record executable assumptions.
2. Build a version-specific N64 inventory, distinguishing region/revision and Expansion Pak settings.
3. Investigate Dreamcast file-layout/tooling evidence before assuming it follows PC or N64.
4. Record exact counts only when a named version-specific source supports them.
5. Do not change gameplay code until the inventory identifies a concrete discrepancy against Boonta.


## Additional evidence: asset-library release matrix and checksums

Source: https://github.com/akopetsch/swe1r-assets/blob/main/src/SWE1R.Assets.Blocks.Original/Resources/checksums.sha1
Supporting source: https://github.com/akopetsch/swe1r-assets/blob/main/src/SWE1R.Assets.Blocks/Resources/Metadata/Release.csv

The public asset-tool repository has a version-labelled SHA-1 catalog for selected *extracted block files*. Its names include:
- `out_modelblock.bin/n64_us.bin` and `n64_eu-jp.bin`;
- `out_modelblock.bin/win-demo.bin` and `_default.bin`;
- `out_splineblock.bin/n64.bin` and `_default.bin`;
- `out_textureblock.bin/n64.bin` and `win-demo.bin`;
- sprite block variants labelled `n64_us`, `n64_jp`, `win-demo`, and `win_de__mac__dc`.

### What this establishes — and what it does not

- The community tooling tracks N64 and Windows-demo block data as distinct named variants; this is evidence that a single generic PC asset dump should not automatically be treated as the console's data.
- At least one sprite-block variant is grouped under a shared Windows / German / Macintosh / Dreamcast label in that repository. This is a tool author's grouping label, not proof that all Dreamcast assets match PC or that the entire formats are interchangeable.
- The listed checksum set does **not** show a separately named Dreamcast model-block or spline-block variant. That is a gap in this catalog, not proof that Dreamcast uses the same files or lacks such data.
- These are checksums of extracted asset files, not checksums of original executables or disc images. Do not use them to identify a complete retail release or region by themselves.
- The asset library advertises bit-perfect reserialization for supported block formats, making a no-change round-trip test a strong future validation candidate. It should be run only against a lawfully available local file; no copyrighted game assets need to be committed to Boonta.

## Updated next research question

**Can the format/asset evidence distinguish PC, N64, and Dreamcast without relying on visual guesses?**

1. Pin the exact commit of the asset library and record its release metadata plus the precise scope of each checksum.
2. Inspect the N64-specific model-block decompressor and compare its stated input assumptions with the generic block reader; document only the format boundary, not extracted game data.
3. Find a Dreamcast-specific primary source or reproducible tool/parser before claiming shared formats. Until then, Dreamcast model/spline format stays **unknown**.
4. Do not compare hash values across labels unless the source proves they were produced from equivalent extraction pipelines and matching release inputs.


## N64 compression: concrete format boundary from public tooling

Source: https://github.com/OpenSWE1R/swe1r-tools/blob/master/decompress.c

The tool's source documents a Comp chunk with:
- a four-byte Comp magic checked after byte-order conversion;
- an output-size field read from the header;
- a compressed stream beginning after a 12-byte header;
- a 0x1000-byte history window;
- LZ77-style literals and back-references, with a zero source offset terminating the stream;
- an assertion that the produced output size matches the header's declared output size.

The tool README explicitly scopes this decompressor to model-block chunks found only in the N64 version. This is meaningful platform-specific evidence for the model-block chunk path, but not a claim that every N64 asset is compressed or that the whole N64 file system differs. The implementation also has a notable input contract: it allocates a 0x1000-byte window before the input pointer, so a future independent parser must reproduce that memory model safely rather than copy the pointer arithmetic blindly.

The asset library's release-labelled checksum list includes separate N64 US and EU/JP model-block variants, while the model-block documentation describes an archive of 323 model entries for its documented sample. Those details should not be combined into a claim that every region has the same count or layout: the sample/release identity must be pinned first.

### Practical consequence

Boonta's asset pipeline should keep container format, compression wrapper, and model payload as three separate layers. A parser should identify the platform/build from grounded metadata, validate lengths and bounds before decompression, and round-trip only formats for which the tool's support is demonstrated. Do not assume a PC block reader can accept an N64 Comp chunk, and do not label Dreamcast support as present until there is a Dreamcast-specific sample or primary parser evidence.


## Release metadata audit: Dreamcast mapping evidence boundary

Pinned source snapshot: `akopetsch/swe1r-assets` commit `922ef535f6598a1330ff93d6b07258956f990b34`.

Sources:
- https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Release.csv
- https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Metadata/ReleaseMetadata.cs
- https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original/Resources/checksums.sha1

The schema defines four selectors: ModelBlockId, SplineBlockId, SpriteBlockId, and TextureBlockId. Release.csv maps Windows International, Mac, and Dreamcast to the same IDs (0,0,3,0); N64 USA to (2,1,2,1); N64 Europe to (1,1,0,1); N64 Japan to (1,1,1,1); and Windows Demo to (3,0,4,2).

Interpretation: the library's metadata explicitly routes Dreamcast through the same generic block selections as Windows International/Mac. This is more specific than inferring similarity from a filename, but it remains the tool author's mapping, not independent proof from a Dreamcast disc. The checksum catalogue names a combined win_de__mac__dc sprite variant but does not separately list Dreamcast model, spline, or texture hashes. Thus byte identity of all Dreamcast assets, identical loaders, and identical renderer/physics remain unproven. N64 region-specific selection is explicitly represented and must remain part of asset provenance.

Next question: find independent Dreamcast-specific evidence for model/spline/texture handling (a parser, version-pinned format note, or provenance-labelled inventory). Until then, mark Dreamcast model/spline/texture runtime behavior UNKNOWN and do not start a port based solely on matching metadata IDs.


## Dreamcast executable string evidence: four named asset files

GitHub code search found string-extraction reports for both USA and Europe Dreamcast builds in `lhsazevedo/dc-redump-extracted-data`, pinned at commit `832abe37573642c56298d3efd006f72416391755`:
- USA: https://github.com/lhsazevedo/dc-redump-extracted-data/blob/832abe37573642c56298d3efd006f72416391755/output/Star%20Wars%20-%20Episode%20I%20-%20Racer%20(USA)/bins/1ST_READ.BIN.strings.txt
- Europe: https://github.com/lhsazevedo/dc-redump-extracted-data/blob/832abe37573642c56298d3efd006f72416391755/output/Star%20Wars%20-%20Episode%20I%20-%20Racer%20(Europe)/bins/1ST_READ.BIN.strings.txt

Both string reports contain `OUT_SPRITEBLOCK.BIN`, `OUT_SPLINEBLOCK.BIN`, `OUT_TEXTUREBLOCK.BIN`, and `OUT_MODELBLOCK.BIN`, followed by an error string for a missing named file. This is independent Dreamcast-specific evidence that the executable expects the familiar four block filenames in those builds. It does **not** establish that their binary layouts, compression, byte order, item IDs, or contents match PC/Mac: filenames are not a format specification. Treat this as a useful loader-level clue, not a validated Dreamcast parser.

### Revised Dreamcast evidence ladder

1. **Observed:** USA and Europe executable string reports contain all four expected block filenames.
2. **Observed:** the asset library's release metadata assigns Dreamcast the same block IDs as Windows International/Mac.
3. **Still unknown:** whether that mapping is based on verified byte-identical Dreamcast blocks, shared logical formats with different payloads, or an assumption made for tool convenience.
4. **Next research action:** find source-level Dreamcast loading logic or a provenance-documented Dreamcast block inventory; compare metadata and format structure only after provenance is established. Do not infer file compatibility from names alone.

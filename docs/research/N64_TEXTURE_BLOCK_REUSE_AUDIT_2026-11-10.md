# N64 texture-block reuse audit — 2026-11-10

**Status:** DOCUMENTED reuse path; end-to-end extraction from a user-owned N64 ROM remains unverified.  
**Target:** N64 asset inspection as a local-only bridge for Boonta's clean-room GameCube/Wii renderer.  
**Scope:** pinned public source and metadata inspection only. No ROM, disc image, embedded game-data resource, model payload, texture payload, image, or extracted asset was downloaded, copied, committed, or uploaded.

## Result

Do **not** implement a new generic texture PNG decoder yet, and do not use emulator texture dumping as the primary path. The pinned MIT `swe1r-assets` project already contains:

1. N64 release metadata selecting a dedicated N64 texture block;
2. a typed texture-block item with pixel and palette parts;
3. a material-to-texture lookup using the model's `TextureIndex`;
4. a PNG exporter that decodes the supported pixel formats, palette indices, and doubled-width/height texture variants; and
5. a command-line exporter, `export-models-textures`, that accepts a model block plus a texture block and optional model indices.

This is the strongest currently identified reuse path for the Anakin candidate. It removes the need to write the PNG/palette conversion logic from scratch, but it does **not** yet prove that the complete N64 block files can be reconstructed directly from the locally held ROM or that the exporter accepts every N64 model variant without an adapter.

## Pinned evidence

All source references below are pinned to `akopetsch/swe1r-assets@922ef535f6598a1330ff93d6b07258956f990b34`.

### N64 release selects its own texture block

- `src/SWE1R.Assets.Blocks/Resources/Metadata/Release.csv` maps:
  - Nintendo 64 (USA): model block ID 2, spline block ID 1, sprite block ID 2, texture block ID 1;
  - Nintendo 64 (Europe): model block ID 1, spline block ID 1, sprite block ID 0, texture block ID 1;
  - Nintendo 64 (Japan): model block ID 1, spline block ID 1, sprite block ID 1, texture block ID 1.
- `src/SWE1R.Assets.Blocks/Resources/Metadata/Block.csv` records the N64 texture block (ID 1) as **BigEndian**, **1,648 items**, **2,741,112 bytes**. The N64 USA model block (ID 2) is recorded as **307 items**, **12,406,512 bytes**.

These are format-catalogue facts, not proof that a locally reconstructed block has been extracted correctly.

### Anakin model catalogue cross-check

The N64 USA model catalogue `src/SWE1R.Assets.Blocks.Original/Resources/out_modelblock.bin/n64_us.md` identifies model item **0087** as `Pupp_Racer_Anakin_Skywalker`. The corresponding `ModelBlockItem.csv` metadata row records **68,284 bytes** for that item.

The locally prepared candidate also has 68,284 decoded bytes and was successfully deserialized as a `PuppModel`. This is a strong catalogue-size and structural match for the Anakin candidate, but the local extraction's item-order-to-catalogue-index mapping has not yet been independently proven. Keep the identity confidence at **strong candidate**, not byte-identity confirmed.

### Existing texture decoding and PNG export code

Relevant MIT source files:

- `src/SWE1R.Assets.Blocks/TextureBlock/TextureBlockItem.cs`: exposes pixel and palette parts; `Load()` decodes its palette as RGBA5551.
- `src/SWE1R.Assets.Blocks/ModelBlock/ModelBlockItemDataPart.cs` and `src/SWE1R.Assets.Blocks/ModelBlock/Compression/Compressor.cs`: automatically recognize and decompress the N64 `CompWolf` model payload on part load; compression is not implemented.
- `src/SWE1R.Assets.Blocks/ModelBlock/Materials/Export/MaterialTextureExporter.cs`: resolves a model material's `TextureIndex` into the texture block, decodes the pixels and palette, then applies child-level double-width/double-height mirroring.
- `src/SWE1R.Assets.Blocks/Textures/Export/TextureExporter.cs`: implements PNG-ready RGBA output for indexed RGBA5551 I4/I8, four-bit grayscale/alpha, eight-bit grayscale, and RGBA32 material formats.
- `src/SWE1R.Assets.Blocks.CommandLine/Exporters/ModelTexturesBlockExporter.cs`: walks a model's mesh materials and writes effective images as PNG files.
- `src/SWE1R.Assets.Blocks.CommandLine/Options/ExportModelTexturesOptions.cs`: exposes the `export-models-textures` verb and requires `--texture-block`; the inherited options accept model indices.

The existing command-line exporter expects a **complete model block file** and a **complete texture block file**. The locally prepared 68,284-byte candidate is an individual decoded model payload, not by itself the complete model block expected by that command. The library's `Block<T>` reader expects a big-endian count, per-part offset table, total size, and item parts.

Importantly, the pinned source already handles the N64 model compression wrapper inside a model block: `ModelBlockItemDataPart` subscribes to its part-loaded event, recognizes the `CompWolf` signature, reads the big-endian decompressed size, and calls `Compressor.Decompress()`. The compressor source implements the read/decompression path, while its `Compress()` path still throws `NotImplementedException`. This means a complete local N64 model block can be loaded through the existing parser without writing another CompWolf decoder, assuming its outer block table and offsets have first been reconstructed correctly. It does **not** mean that the standalone local candidate or the full ROM-to-block extraction was tested through that path.

The original-resource test project contains N64-labelled model and texture block resources and an original material/texture catalog, and its catalog generator iterates release metadata to associate model materials with the selected texture-block metadata. The tests demonstrate the export path in the source tree; this audit does not claim that an N64-specific test suite was run against a locally reconstructed ROM block.

## Technical decision

**Reuse the pinned MIT parser/exporter as a read-only extraction dependency or reference; do not write a second texture conversion implementation.** A narrowly scoped local adapter may still be needed to supply a full N64 model block, the N64 texture block, or the model record in the form expected by the existing exporter.

Before integration, resolve these gates:

1. Locate and reconstruct the N64 texture block from the owner-controlled local ROM without publishing any game data.
2. Reconstruct or adapt the full N64 model block so its item index and `CompWolf` payload boundaries are preserved; do not infer index 87 solely from the sorted Pupp candidate list.
3. Run the existing exporter locally against only the user-owned files and report aggregate results (number of referenced textures decoded, unsupported formats, missing indices, and export success). Keep PNGs and model files local.
4. Audit exact package/dependency notices before shipping the parser or exporter in Boonta. The library's MIT source licence does not grant rights to redistribute embedded commercial game resources or extracted assets.
5. Treat exported PNGs as an intermediate format only. The native GameCube/Wii renderer still needs an independently validated GX texture upload/conversion path; N64 rendering and texture encodings are not automatically GameCube/Wii-compatible.

## Reuse and safety boundary

- No RMG/GLideN64 capture is needed for the next source-research step. Keep the already-installed emulator as an optional fallback only.
- Do not download or copy the upstream project's embedded N64 texture/model binaries into Boonta; the original-resource project bundles game-derived resources separately from the MIT source-code licence.
- Do not commit ROMs, model payloads, PNGs, material dumps, texture hashes, ROM offsets, or extracted proprietary data.
- Use only aggregate local test results in public reports.
- Do not copy GPL `swe1r-tools` or GPL-3 `blender-swe1r` implementation code into the MIT Boonta core.

## Primary pinned references

- [Release metadata](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Release.csv)
- [Block metadata](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Block.csv)
- [N64 USA model catalogue](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original/Resources/out_modelblock.bin/n64_us.md)
- [Model item metadata](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/ModelBlockItem.csv)
- [Texture block item](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/TextureBlock/TextureBlockItem.cs)
- [CompWolf model part reader](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/ModelBlock/ModelBlockItemDataPart.cs)
- [CompWolf decompressor](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/ModelBlock/Compression/Compressor.cs)
- [Material texture exporter](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/ModelBlock/Materials/Export/MaterialTextureExporter.cs)
- [Texture exporter](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Textures/Export/TextureExporter.cs)
- [Model texture block exporter](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.CommandLine/Exporters/ModelTexturesBlockExporter.cs)
- [Export command options](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.CommandLine/Options/ExportModelTexturesOptions.cs)
- [Original resource project file](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original/SWE1R.Assets.Blocks.Original.csproj)

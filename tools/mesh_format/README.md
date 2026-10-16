# Neutral mesh source format (v1)

This folder defines an original, engine-neutral source format for meshes authored from scratch. It is not a parser or converter for commercial game files, extracted models, ROMs, or third-party assets.

## Format

The format identifier is boonta-mesh-v1. Each vertex contains:
- position: exactly three finite numbers (X, Y, Z), bounded to +/- 1,000,000.
- color: exactly four integer RGBA8 channels (0..255).
- indices: a non-empty indexed triangle list. Its length must be a multiple of three and no greater than 4095; vertex count is limited to 4096.

The validator rejects missing/ill-typed fields, non-finite/out-of-range positions, invalid colors, invalid indices, and zero-area triangles before any header is written. The exporter uses only Python's standard library and creates deterministic C output.

## Commands

~~~sh
python3 tools/mesh_format/validate_mesh.py gamecube-demo/data/meshes/original_synthetic_triangle.json
python3 tools/mesh_format/export_mesh_header.py gamecube-demo/data/meshes/original_synthetic_triangle.json gamecube-demo/source/generated_mesh.h
python3 -m unittest discover -s gamecube-demo/tools -p 'test_mesh_format.py' -v
~~~

The checked-in C header is generated output; change the JSON source and re-export rather than editing generated arrays by hand. The GameCube build consumes generated static data at compile time, so no runtime file system dependency is added.

This first example is entirely synthetic. It proves a source-file-to-GX-data path, not compatibility with PC/N64/GameCube/Wii commercial asset formats. Their format versions, licenses, and provenance must be established separately before a parser is considered.

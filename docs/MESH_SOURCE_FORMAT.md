# `boonta-mesh-v1` source format

Status: **the only supported mesh source format for the current clean-room asset slice**. This is a small project-owned authoring format, not a claim of compatibility with any commercial GameCube/Wii asset format.

Implementation references:
- Validator: `tools/mesh_format/validate_mesh.py`
- Deterministic C-header exporter: `tools/mesh_format/export_mesh_header.py`
- Runtime contract: `gamecube-demo/source/mesh_data.h`
- Original fixture: `gamecube-demo/data/meshes/original_synthetic_triangle.json`

## Purpose and pipeline

The JSON file is the editable source of truth. The host-side Python exporter validates it and generates a C header at build time. The GameCube runtime consumes the generated, statically compiled arrays; it does **not** read JSON or load files from a runtime filesystem.

```text
authored JSON
    -> validate schema, numeric ranges, counts and topology
    -> deterministic generated C header
    -> BoontaMeshView
    -> runtime validation
    -> existing GX submission path
```

The validator and runtime validator are separate safety layers: successful export does not remove the requirement to validate the view before renderer submission.

## JSON schema

A document has exactly these required semantic fields:

| Field | Type | Contract |
|---|---|---|
| `format` | string | Must equal `boonta-mesh-v1`. |
| `name` | string | Non-empty after trimming; at most 80 characters. Used to derive stable C identifiers. |
| `vertices` | array | 3 to 4096 vertex objects. |
| `vertices[].position` | array of numbers | Exactly three finite coordinates `[x, y, z]`; each coordinate is in [-1,000,000, 1,000,000]. Booleans are not numbers for this contract. |
| `vertices[].color` | array of integers | Exactly four RGBA8 channels, each in [0, 255]. Booleans and fractional values are rejected. |
| `indices` | array of integers | 3 to 4095 entries; count must be divisible by three. Each index is zero-based and must refer to an existing vertex. Booleans and fractional values are rejected. |

Each consecutive group of three indices describes one triangle. Triangles with zero area are rejected by both the host validator and runtime contract. Unknown optional attributes such as normals, UVs, materials, textures, skeletons and collision metadata are **not part of v1**; do not silently imply that they are supported. Unknown keys at the top level or inside vertex objects are currently ignored by the validator rather than rejected; they are not supported v1 fields, and callers must not rely on them.

The top-level example below is a complete minimal document:

```json
{
  "format": "boonta-mesh-v1",
  "name": "original-synthetic-triangle",
  "vertices": [
    { "position": [-0.65, 0.0, 0.0], "color": [255, 70, 50, 255] },
    { "position": [0.65, 0.0, 0.0], "color": [50, 220, 255, 255] },
    { "position": [0.0, 1.10, 0.0], "color": [255, 240, 110, 255] }
  ],
  "indices": [0, 1, 2]
}
```

The checked-in fixture is the canonical runnable example. Keep all test meshes original and synthetic unless provenance and redistribution permission are independently established.

## Limits and safety

- Maximum vertices: 4096.
- Maximum indices: 4095 (the largest multiple of three not exceeding the renderer's 4096-vertex expansion cap).
- Positions must be finite and bounded; RGBA channels must fit in one unsigned byte.
- Index count must form complete triangles, all indices must be in range, and zero-area triangles are rejected.
- Invalid source must fail before a generated header is written. Do not weaken checks to accommodate a questionable input file.
- Runtime `BoontaMeshView` includes explicit backing-array byte lengths. In C, those declared lengths cannot prove the real allocation behind an arbitrary pointer; callers must ensure they describe the actual readable arrays.

## Generate and test

From the repository root, run the exporter against the checked-in original fixture, writing to a temporary path:

```sh
python3 tools/mesh_format/export_mesh_header.py \
  gamecube-demo/data/meshes/original_synthetic_triangle.json \
  /tmp/original_synthetic_triangle.generated.h
```

Run the existing mesh-format test entry point:

```sh
python3 gamecube-demo/tools/test_mesh_format.py
```

The test suite checks valid input, malformed/missing fields, numeric and count limits, invalid indices, degenerate triangles, malformed JSON, and deterministic generated-header parity. The normal GameCube workflow additionally exercises host regressions, native DOL/ELF build/artifact checks and Dolphin diagnostics; consult the exact workflow run rather than assuming local tests establish visual or hardware acceptance.

## Explicit non-goals

v1 does not provide runtime filesystem loading, commercial-asset import, proprietary format parsing, textures/UVs/normals/materials, animation/skeletons, collision data, or a general-purpose model pipeline. GameCube J3D BMD/BDL, Wii BRRES/MDL0, PC data blocks and N64 formats are distinct candidates and must not be treated as interchangeable without version-specific evidence and tests. Keep the Step 102 archive and all uncleared source/data on HOLD.

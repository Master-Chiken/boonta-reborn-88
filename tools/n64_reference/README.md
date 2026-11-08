# N64 reference function inspector

This is a small **read-only local analysis helper** adapted from
[sp00nznet/racer](https://github.com/sp00nznet/racer)'s
`tools/func_differ.py`, pinned at commit
[`694c5663b3a7c30e2862fc240344f34683f99a9c`](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c).
The upstream tool is MIT-licensed; see [LICENSE.sp00nznet](LICENSE.sp00nznet).

## Use

Provide your own legally held, local N64 ROM and a local `symbols.toml`
from an independently obtained symbol-analysis workspace:

```sh
python3 tools/n64_reference/mips_function_inspector.py func_80000470 \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml"
```

You can also query an exact start address:

```sh
python3 tools/n64_reference/mips_function_inspector.py 0x80000470 \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml"
```

The tool reads the ROM and TOML file, prints a bounded disassembly to stdout,
and writes no output files. It accepts canonical big-endian `.z64`,
byte-swapped `.v64`, and word-swapped `.n64` images. The section-relative
mapping comes from the supplied TOML `[[section]]` entries; no ROM offset is
hard-coded into the Boonta tool.

## Limits and provenance

- This is a **partial MIPS III decoder**, not a full disassembler or decompiler.
  Unsupported instructions are emitted as raw `.word` values.
- A symbol's name and address are search leads, not proof of its behaviour.
  Verify callers, callees, control flow and data references independently.
- This utility is **N64/MIPS only**. It says nothing about GameCube/Wii
  Gekko/Broadway behaviour or format compatibility.
- Do not commit ROMs, `symbols.toml`, disassembly output, generated code,
  extracted assets or game-derived files. Do not attach them to issues, PRs,
  hosted AI prompts, or CI artifacts.
- CI tests use only synthetic instruction words and tiny synthetic ROM headers.

The source map is derived from the MIT-licensed upstream disassembler. We keep
its attribution and license notice separate from Boonta's own project license.

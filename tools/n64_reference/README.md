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

## Create a provisional symbol map

When no local symbol map is available, the companion scanner can list common
`addiu $sp, $sp, -N` stack-allocation prologue candidates and write a TOML
file that the inspector accepts:

```sh
python3 tools/n64_reference/mips_symbol_scanner.py \
  --rom "$HOME/racer-work/racer_us.z64" \
  --rom-offset 0x1000 \
  --vram-base 0x80000400 \
  --code-size "$CODE_SIZE" \
  --output "$HOME/racer-work/symbols-candidates.toml"
```

Set `CODE_SIZE` to the verified size of the executable region for the exact
ROM/revision; the tool deliberately does not guess a code-end address. Its
output uses the next prologue as a **provisional** function-size boundary.
Prologue detection can miss leaf functions and mistake instruction/data bytes
for starts. Verify each candidate, boundary and caller/callee manually before
using it as evidence.

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

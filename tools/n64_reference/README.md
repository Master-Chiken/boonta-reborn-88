# Local N64 reverse-engineering helpers

These read-only tools adapt selected analysis ideas from
[sp00nznet/racer](https://github.com/sp00nznet/racer), pinned at
[694c5663b3a7c30e2862fc240344f34683f99a9c](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c).
The upstream project declares MIT for its own tools/runtime/build/documentation
and explicitly excludes the commercial game and code generated from a user's
ROM. See [LICENSE.sp00nznet](LICENSE.sp00nznet).

## Local setup

Every command below requires the operator's own legally held N64 ROM. Keep the
ROM, symbol maps, outputs and notes derived from it in a private local work
directory. The public repository and hosted CI contain synthetic fixtures only.

### 1. Inspect a function

~~~sh
python3 tools/n64_reference/mips_function_inspector.py 0x80000470 \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml"
~~~

This accepts canonical big-endian .z64, byte-swapped .v64 and word-swapped
.n64 images. It uses the section-relative ROM/VRAM mapping in the supplied
TOML and prints a bounded subset of MIPS III instructions. Unknown instructions
remain raw .word directives; this is not a full disassembler/decompiler.

### 2. Generate provisional function candidates

When a local symbol map is not available, scan an explicitly specified code
range:

~~~sh
python3 tools/n64_reference/mips_symbol_scanner.py \
  --rom "$HOME/racer-work/racer_us.z64" \
  --rom-offset 0x1000 \
  --vram-base 0x80000400 \
  --code-size "$CODE_SIZE" \
  --output "$HOME/racer-work/symbols-candidates.toml"
~~~

Set CODE_SIZE to the verified executable-region size for the exact ROM
revision. The scanner deliberately does not guess a code-end address. It only
finds common addiu $sp, $sp, -N stack-frame prologues; it can miss leaf
functions and mistake data/instructions for starts. The next candidate is only
a provisional end boundary. Manually verify every candidate and boundary.

### 3. Build a direct-call graph

~~~sh
python3 tools/n64_reference/mips_callgraph.py \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml" \
  --top 50

python3 tools/n64_reference/mips_callgraph.py \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml" \
  --function 0x80000470
~~~

The graph resolves direct JAL sites to exact symbol starts and lists
unresolved targets, ambiguous symbol addresses and indirect JALR sites.
Incoming counts are static call-site counts, not runtime call frequencies.
Indirect calls require separate data-flow or runtime investigation.

### 4. Find strings and likely resource names

~~~sh
python3 tools/n64_reference/mips_string_scanner.py \
  --rom "$HOME/racer-work/racer_us.z64" --category files

python3 tools/n64_reference/mips_string_scanner.py \
  --rom "$HOME/racer-work/racer_us.z64" --category game
~~~

The string scanner prints offsets and matching ASCII strings to stdout. Its
categories are keyword hints (debug, files, menu, dialogue, credits, game and
other), not semantic identification. Use it locally; do not paste extracted
text into public issues, PRs or hosted AI prompts.

### 5. Locate N64 OS, hardware and floating-point candidates

~~~sh
python3 tools/n64_reference/mips_os_candidates.py \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml"

python3 tools/n64_reference/mips_os_candidates.py \
  --rom "$HOME/racer-work/racer_us.z64" \
  --symbols "$HOME/racer-work/symbols.toml" \
  --function func_8008C100
~~~

This reports COP0 register transfers, common N64 MMIO high-half constants,
COP1 control transfers, floating-point loads/stores, stack-frame candidates and
jr ra sites. It deliberately does not rename a function to osPiStartDma,
osViManager or another API from partial evidence. Confirm the full body and
callers/callees before assigning a semantic name.

### 6. Prioritize the next functions to inspect

~~~sh
python3 tools/n64_reference/mips_symbol_progress.py \
  --symbols "$HOME/racer-work/symbols.toml" --top 20

python3 tools/n64_reference/mips_symbol_progress.py \
  --symbols "$HOME/racer-work/symbols.toml" --json
~~~

This reports how many functions have descriptive names versus common
auto-generated names, mapped byte coverage, size distribution and the largest
remaining auto-named candidates. It does not claim a named function is
understood, correctly identified or implemented; use it only as a triage aid.

## Research sequence

For a new question, use the tools in this order:

1. Build/verify the local symbol map for the exact ROM and region.
2. Search the local strings for menu, track, audio, vehicle or file-path clues.
3. Use the call graph to find likely callers, shared helpers and indirect-call gaps.
4. Use the OS-candidate report to separate likely libultra/hardware support from
   game-specific code.
5. Inspect only the most promising functions and record evidence, counter-
   evidence, callers/callees and confidence.
6. Treat N64/MIPS findings as N64-only leads. Confirm PC, Dreamcast or
   GameCube/Wii behaviour independently before transferring a design decision.

## Limits and provenance

- These tools are N64/MIPS only. They do not decode GameCube/Wii Gekko or
  Broadway instructions, GX display lists, PC x86 code or Dreamcast SH-4 code.
- A prologue, name, string or call edge is not proof of what a function does.
  Static calls do not reveal function pointers or execution frequency.
- No ROM, symbols.toml, decompiled code, section table, save, RSP output,
  extracted model/texture/audio, or other game-derived content belongs in this
  public repository, CI, PR attachments or hosted prompts.
- The tools are read-only with respect to the ROM. The symbol scanner writes
  only the explicitly requested TOML output path; direct analysis tools print
  metadata to stdout.
- CI tests use only generated instruction words, synthetic ROM headers and
  source-authored strings. They do not validate any commercial Racer ROM or
  establish compatibility with the retail game.
- The upstream symbol table and N64Recomp configuration are not copied here:
  they are revision-specific research metadata, not a portable GameCube/Wii
  code base.

# GitHub source status — 2026-10-20

## PC references

- [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE): primary current lead for PC functions, symbols, generated hooks and Ghidra scripts. Its README says function progress means analyzed, not necessarily implemented. Read-only first; license review required before reuse.
- [OpenSWE1R/openswe1r](https://github.com/OpenSWE1R/openswe1r): historical PC port attempt, marked deprecated by its organization. It combines Windows API emulation and x86 CPU emulation, and still depends on the original binary and assets. It is not a ready-made GameCube port.
- [OpenSWE1R/swe1r-re](https://github.com/OpenSWE1R/swe1r-re): historical reverse-engineering reference, also marked deprecated. Useful for corroboration, not as the only source of truth.
- [PCVR fork](https://github.com/GameOrDie007/Star-Wars-Episode-I-Racer-PCVR): downstream fork adding OpenXR features on top of SW_RACER_RE. Low priority for core gameplay, potentially useful for understanding renderer hooks.

## Data tools

- [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools): marked deprecated, but still useful as historical format documentation. Its README explicitly says its `decompress.c` model-block chunks are N64-only.
- [swe1r-assets](https://github.com/akopetsch/swe1r-assets): MIT reader/writer for PC asset blocks; strongest candidate for a no-op byte-identical round-trip test once a lawful local input is available.
- [ep1-racer-save-editor](https://github.com/jcfieldsdev/ep1-racer-save-editor): GPL-3.0 PC save editor whose README credits swe1r-tools for save-format knowledge; secondary corroboration only.

## Dreamcast gap

No full public Dreamcast decompilation or dedicated Dreamcast asset parser has been established in this pass. Treat Dreamcast behavior and file formats as UNKNOWN until evidence tied to an identified release is found. Do not infer PC/N64 equivalence from reviews.

## Next work order

1. Index SW_RACER_RE functions for handling, race progression, AI, collision, track loading and renderer interfaces, pinning exact commits.
2. Design a no-op PC asset-block round-trip test; do not run it without a lawful local block.
3. Inventory N64-specific format and behavior differences.
4. Keep a separate Dreamcast evidence ledger.
5. Change Boonta code only after a concrete gap is documented.

Maintain the 80/20 ratio: eight research/reverse-engineering blocks per two implementation, testing or integration blocks. Respect each repository's license and keep commercial game assets/binaries out of the public repo.

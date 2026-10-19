# Synthetic MDL0 v11 header probe

This is a small, independently tested **fixed-header bounds probe**, not a BRRES
or MDL0 importer, model decoder, renderer, or evidence that the game can load
any model. Every test constructs bytes in memory; no game assets or binary
fixtures are included.

## Run

    python3 -m unittest discover -s tools/brres_probe -p 'test_*.py' -v

## Checked prefix and assumptions

The fixed MDL0 v11 prefix is 0x4C bytes: magic MDL0, big-endian u32 subfile
length and version, a signed i32 back-reference to the outer BRRES, 14 signed
i32 section offsets, and a signed i32 name offset. All offsets are relative to
the beginning of the MDL0 header.

The signed outer-container back-reference is resolved against the supplied
synthetic buffer. Negative values are allowed when they point backward to the
expected container. Section offset zero is treated as an absent/optional
section; nonzero section targets must lie after the fixed header and before
the declared end of the MDL0 subfile. The name offset resolves into the
containing buffer because the name string belongs to the shared BRRES string
pool, and its target must be NUL-terminated within that buffer.

The range checks are intentionally conservative. This probe does not parse
BRRES root/index groups, validate the contents of section targets, decode
vertices or draw lists, or establish all legal string-pool layouts. It checks
only the fixed prefix, arithmetic/buffer bounds, and the stated synthetic
target relationships.

## Public format references

- https://mkwiiki.org/wiki/MDL0 — header field order, 14 sections for v11,
  signed relative offsets, and shared name pool.
- https://mkwiiki.org/wiki/BRRES_(File_Format)
- https://mkwiiki.org/wiki/BRRES_Subfiles_(File_Format)

The code is an independent implementation. No third-party parser code is
copied or imported. The public notes are community-maintained documentation;
format edge cases and licensing/provenance of real assets are outside this
probe's claims.

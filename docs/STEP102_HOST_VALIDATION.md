# Step 102 source-only bundle: host validation

Date: 2026-10-14

## Scope

Validation was run against the separately supplied `step102-source-only-import.b64.txt` bundle after decoding and extracting it into a temporary directory. The bundle contains 123 files. It is **not yet imported into this GitHub repository**, and these results are not GitHub Actions results.

The bundle's import README says it excludes PC-mod-derived centerline headers/data, generated mesh/boundary headers, audio, OBJ/MTL assets, ROM/disc images, and PC/N64 extraction/reverse-engineering helpers. Its Makefile defaults to `USE_IMPORTED_SPLINE=0`, which selects the procedural/demo route path.

## Results

| Check | Result |
|---|---:|
| Host shell regression scripts (`tests/*_host.sh`) | **32 passed, 0 failed** |
| Python source-bundle policy tests | **5 passed, 0 failed** |
| Total checks in these two groups | **37 passed, 0 failed** |
| Native GameCube cross-build | **Not run** |
| Dolphin / console runtime | **Not run** |

Commands used from the extracted bundle root:

```sh
for f in tests/*_host.sh; do bash "$f" || exit 1; done
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Environment limitation

This environment has no `DEVKITPPC` variable and no `powerpc-eabi-gcc` executable available on PATH. Therefore it cannot produce a valid native GameCube `.dol` here. The shell checks include host compilation and mock-libogc syntax checks; they do not substitute for devkitPPC/libogc.

## Next steps

1. Review file-by-file source provenance and redistribution rights before importing the bundle into the public repository.
2. Import the approved source-only subset on a dedicated branch, preserving the procedural default and excluding unclear-provenance assets/data.
3. Run the same host suite in GitHub Actions against the imported files.
4. Configure a real devkitPPC/libogc CI build, retain logs and the `.dol` artifact, and test it in Dolphin.
5. Record visible rendering, controls, frame pacing, and gameplay separately from compilation success.

These results establish that the supplied source-only bundle passes its available host checks in this environment. They do **not** establish that the full game builds natively or is playable.

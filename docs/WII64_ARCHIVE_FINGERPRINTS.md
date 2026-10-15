# Wii64 archive fingerprints

Date: 2026-10-15

This manifest records sizes and SHA-256 digests of the four `boot.dol` files in the supplied `wii64.zip`. It is intended to help identify which exact packaged variant is being tested on a Wii or Wii U Virtual Wii setup. It does not redistribute the executables.

## Package metadata

All four `meta.xml` files identify Wii64 version `1.5.0` and release string `202609231942`.

| Application directory | Metadata title | Target / plugin |
|---|---|---|
| `apps/wii64/` | `Wii64 | glN64 GFX` | Wii, glN64 |
| `apps/wii64 Rice/` | `Wii64 | Rice GFX` | Wii, Rice |
| `apps/wii64_wiivc/` | `Wii64 | glN64 GFX | WiiVC` | Wii U Virtual Wii/WiiVC, glN64 |
| `apps/wii64 Rice_wiivc/` | `Wii64 | Rice GFX | WiiVC` | Wii U Virtual Wii/WiiVC, Rice |

The metadata explicitly describes the WiiVC-labeled executables as intended for Wii VC mode on Wii U. Do not infer that they are needed for an ordinary Wii console.

## Executable fingerprints

| Archive path | Size (bytes) | SHA-256 |
|---|---:|---|
| `apps/wii64/boot.dol` | 1,955,872 | `1cc4a749a6019edd6fdd85c5f743fc275c539232845b55d2d56918c87a79fefb` |
| `apps/wii64 Rice/boot.dol` | 2,698,816 | `faddd5e59461bb2517571501b560aa0e201df28abc66bb70b9ebb8c77c2b5ced` |
| `apps/wii64_wiivc/boot.dol` | 1,961,408 | `cf80a1bfbbbd6e7f3f87ba8ec10e0f0dd8d4a38b2cd006a177ee7a19a4a5a37b` |
| `apps/wii64 Rice_wiivc/boot.dol` | 2,703,456 | `7c7aa017f348c8ae09becbb479abc5409638cb9f7da0dcd471e7977a1d1640ea` |

Archive SHA-256:

```text
cf935283854f69210b52ce668b6aa78551ab6c1086e6b25be2290b0c8077d154
```

## Reproducing the check locally

From a directory containing `wii64.zip`, run:

```python
import hashlib
import zipfile

archive = "wii64.zip"
paths = [
    "apps/wii64/boot.dol",
    "apps/wii64 Rice/boot.dol",
    "apps/wii64_wiivc/boot.dol",
    "apps/wii64 Rice_wiivc/boot.dol",
]

with zipfile.ZipFile(archive) as zf:
    for path in paths:
        data = zf.read(path)
        digest = hashlib.sha256(data).hexdigest()
        print(f"{len(data):>10}  {digest}  {path}")
```

To compare an installed copy, calculate SHA-256 on the extracted `boot.dol` and compare it with the corresponding row. Keep in mind that a changed digest establishes only that the bytes differ; it does not tell us whether the change is legitimate, safe, or functionally better.

## Use in the project

- Use the exact variant and digest in test logs so Rice/glN64 and Wii/WiiVC results are not accidentally mixed.
- Do not commit these binaries to Boonta Reborn 88; this manifest contains only metadata and hashes.
- A hash match does not verify that a binary works on a particular console.
- No `boot.dol` was executed during creation of this manifest.

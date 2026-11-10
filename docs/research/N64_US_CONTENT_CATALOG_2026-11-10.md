# N64 USA content catalogue inventory (metadata only)

**Snapshot:** 2026-11-10  
**Source:** [`akopetsch/swe1r-assets`](https://github.com/akopetsch/swe1r-assets/tree/922ef535f6598a1330ff93d6b07258956f990b34) at commit `922ef535f6598a1330ff93d6b07258956f990b34`.

This is a planning inventory, not an asset dump. It stores names and logical metadata IDs only. It contains no ROM bytes, model geometry, textures, asset hashes, payload offsets or extracted files. The parser source declares MIT, but that does not grant rights to commercial game assets.

## N64 USA release profile

The source metadata selects release ID **3 — Nintendo 64 (USA)**:

| Block | Block ID | Entries |
|---|---:|---:|
| Model | 2 | 307 |
| Spline | 1 | 91 |
| Sprite | 2 | 173 |
| Texture | 1 | 1648 |

The broader metadata catalogue contains 433 model-value rows across these prefixes: `MAlt` 29, `Trak` 34, `Podd` 29, `Part` 233, `Pupp` 51, `Modl` 15, `Scen` 28, `N64` 14. This is a combined metadata catalogue across versions, not the N64 USA model-block count.

The catalogue also contains 127 spline records (46 track-segment rows, 25 camera records and 56 other entries), 180 sprite metadata rows and 1675 texture metadata rows. The selected N64 USA block contains 173 sprites and 1648 textures.

## Physical block inventories

The machine-readable file now contains every mapped item entry from all four selected N64 USA blocks, using only physical index, metadata ValueId, descriptive name (when available) and a derived category.

### Model block — 307 entries

| Category | Entries |
|---|---:|
| part | 183 |
| racer-model | 38 |
| alternate-pod | 25 |
| pod | 25 |
| N64-alias | 14 |
| track | 11 |
| model | 9 |
| scene | 2 |

All 307 model entries have a metadata name; there are 306 unique names (one duplicate name).

### Spline block — 91 entries

| Category | Entries |
|---|---:|
| generic-spline | 36 |
| track | 28 |
| camera | 14 |
| part | 13 |

The 36 generic `__SPLINE__` records and 13 `Part_` entries are retained as-is rather than assigned a guessed circuit role.

### Sprite block — 173 entries

| Category | Entries |
|---|---:|
| sprite | 54 |
| gui | 26 |
| avatar | 23 |
| racerflag | 23 |
| system-ui | 12 |
| planet | 8 |
| light | 6 |
| banner | 5 |
| countdown | 3 |
| palette | 3 |
| winnerflag | 3 |
| background | 2 |
| lucasarts | 2 |
| tatooine | 1 |
| gradient | 1 |
| teamphoto | 1 |

There are 169 unique names; repeated names and generic `Sprite_` entries are preserved by physical index.

### Texture block — 1648 entries

The selected block maps 1648 physical indices, but the upstream `TextureBlockItem.csv` supplies **no descriptive names** for these rows. The JSON therefore records each `Index`/`ValueId` pair and leaves its name null. Materials and their texture references must provide the semantic association; no labels or image content are inferred.

## Content subsystem breakdown

The N64 USA model block contains named groups beyond the headline pilot and track models:

| Group | Count |
|---|---:|
| Racer LOD1 parts | 25 |
| Racer LOD2 parts | 23 |
| Track-ground auxiliary parts | 25 |
| Upgrade parts | 54 |
| Planet-selection parts | 13 |
| Hangar / pit-droid parts | 7 |
| HUD parts | 4 |
| Effects / shatter / energy-binder parts | 13 |
| Scene records | 2 |

### Upgrade subgroups

| Metadata name group | Entries |
|---|---:|
| Turning control | 5 |
| Air brake | 6 |
| Cooling | 6 |
| Top speed | 6 |
| Acceleration | 6 |
| Traction | 6 |
| Repair | 6 |
| Generic/unclassified upgrade names | 13 |

Several upgrade records have only generic labels such as `Part_Upgrade_55`; their function remains unknown until the model/material graph or a runtime observation establishes it.

### One auxiliary track-ground part per circuit

All **25/25** `Part_TrackGround_*` records name-match one row in the 25-track catalogue:

| N64 physical model index | Asset metadata name | Track ID | Track |
|---:|---|---:|---|
| 122 | Part_TrackGround_AndoPrime_AndoPrimeCentrum | 5 | Andobi Prime Centrum |
| 172 | Part_TrackGround_AndoPrime_BeedosWildRide | 2 | Beedo's Wild Ride |
| 173 | Part_TrackGround_AndoPrime_HowlerGorge | 3 | Howler Gorge |
| 174 | Part_TrackGround_AndoPrime_AndobiMountainRun | 4 | Andobi Mountain Run |
| 175 | Part_TrackGround_Aquilaris_AquilarisClassic | 6 | Aquilaris Classic |
| 176 | Part_TrackGround_Aquilaris_SunkenCity | 7 | Sunken City |
| 177 | Part_TrackGround_Malastare_Malastare100 | 22 | Malastare 100 |
| 178 | Part_TrackGround_Malastare_DugDerby | 23 | Dug Derby |
| 179 | Part_TrackGround_Malastare_SebulbasLegacy | 24 | Sebulba's Legacy |
| 180 | Part_TrackGround_Aquilaris_BumbysBreakers | 8 | Bumpy's Breakers |
| 181 | Part_TrackGround_OrdIbanna_ScrappersRun | 9 | Scrapper's Run |
| 182 | Part_TrackGround_OrdIbanna_DethrosRevenge | 10 | Dethro's Revenge |
| 183 | Part_TrackGround_OrdIbanna_Abyss | 11 | Abyss |
| 184 | Part_TrackGround_MonGazza_Speedway | 16 | Mon Gazza Speedway |
| 185 | Part_TrackGround_MonGazza_SpiceMineRun | 17 | Spice Mine Run |
| 186 | Part_TrackGround_Baroonda_Inferno | 15 | Inferno |
| 187 | Part_TrackGround_MonGazza_ZuggaChallenge | 18 | Zugga Challenge |
| 188 | Part_TrackGround_OovoIv_Vengeance | 19 | Vengeance |
| 189 | Part_TrackGround_OovoIv_Executioner | 20 | Executioner |
| 190 | Part_TrackGround_OovoIv_TheGauntlet | 21 | The Gauntlet |
| 231 | Part_TrackGround_Baroonda_BarooCoast | 12 | Baroo Coast |
| 244 | Part_TrackGround_Baroonda_GrabvineGateway | 13 | Grabvine Gateway |
| 245 | Part_TrackGround_Baroonda_FireMountainRally | 14 | Fire Mountain Rally |
| 274 | Part_TrackGround_Tatooine_Training | 0 | The Boonta Training Course |
| 275 | Part_TrackGround_Tatooine_Classic | 1 | The Boonta Classic |

These are named ground/support parts associated with the tracks. This does not establish that they contain the full road/terrain geometry or all environment objects for the corresponding track.

## Racer roster — 25 entries

Each model reference is stored as a logical catalogue ID and, when resolvable, its physical N64 USA block index. Joining by exact model name produced **123/123** unique matches across **123** distinct model indices. The last two roster entries have no LOD2 reference in this metadata snapshot.

| ID | Racer | Model references (logical catalogue ID → physical N64 block index) |
|---:|---|---|
| 1 | Anakin Skywalker | Podd: catalogue 2 → N64 index 2; MAlt: catalogue 0 → N64 index 0; Pupp: catalogue 87 → N64 index 87; Lod1: catalogue 256 → N64 index 251; Lod2: catalogue 208 → N64 index 203 |
| 2 | Teemto Pagalies | Podd: catalogue 4 → N64 index 4; MAlt: catalogue 3 → N64 index 3; Pupp: catalogue 86 → N64 index 86; Lod1: catalogue 257 → N64 index 252; Lod2: catalogue 227 → N64 index 222 |
| 3 | Sebulba | Podd: catalogue 6 → N64 index 6; MAlt: catalogue 5 → N64 index 5; Pupp: catalogue 91 → N64 index 91; Lod1: catalogue 255 → N64 index 250; Lod2: catalogue 225 → N64 index 220 |
| 4 | Ratts Tyerell | Podd: catalogue 8 → N64 index 8; MAlt: catalogue 7 → N64 index 7; Pupp: catalogue 93 → N64 index 93; Lod1: catalogue 258 → N64 index 253; Lod2: catalogue 220 → N64 index 215 |
| 5 | Aldar Beedo | Podd: catalogue 9 → N64 index 9; MAlt: catalogue 10 → N64 index 10; Pupp: catalogue 105 → N64 index 105; Lod1: catalogue 259 → N64 index 254; Lod2: catalogue 207 → N64 index 202 |
| 6 | Mawhonic | Podd: catalogue 12 → N64 index 12; MAlt: catalogue 11 → N64 index 11; Pupp: catalogue 89 → N64 index 89; Lod1: catalogue 260 → N64 index 255; Lod2: catalogue 222 → N64 index 217 |
| 7 | Ark Bumpy Roose | Podd: catalogue 14 → N64 index 14; MAlt: catalogue 13 → N64 index 13; Pupp: catalogue 96 → N64 index 96; Lod1: catalogue 261 → N64 index 256; Lod2: catalogue 213 → N64 index 208 |
| 8 | Mars Guo | Podd: catalogue 16 → N64 index 16; MAlt: catalogue 18 → N64 index 18; Pupp: catalogue 92 → N64 index 92; Lod1: catalogue 263 → N64 index 258; Lod2: catalogue 221 → N64 index 216 |
| 9 | Wan Sandage | Podd: catalogue 17 → N64 index 17; MAlt: catalogue 15 → N64 index 15; Pupp: catalogue 99 → N64 index 99; Lod1: catalogue 262 → N64 index 257; Lod2: catalogue 229 → N64 index 224 |
| 10 | Ebe E. Endocott | Podd: catalogue 20 → N64 index 20; MAlt: catalogue 19 → N64 index 19; Pupp: catalogue 95 → N64 index 95; Lod1: catalogue 264 → N64 index 259; Lod2: catalogue 216 → N64 index 211 |
| 11 | Dud Bolt | Podd: catalogue 22 → N64 index 22; MAlt: catalogue 21 → N64 index 21; Pupp: catalogue 98 → N64 index 98; Lod1: catalogue 265 → N64 index 260; Lod2: catalogue 215 → N64 index 210 |
| 12 | Gasgano | Podd: catalogue 24 → N64 index 24; MAlt: catalogue 23 → N64 index 23; Pupp: catalogue 88 → N64 index 88; Lod1: catalogue 266 → N64 index 261; Lod2: catalogue 219 → N64 index 214 |
| 13 | Clegg Holdfast | Podd: catalogue 26 → N64 index 26; MAlt: catalogue 25 → N64 index 25; Pupp: catalogue 97 → N64 index 97; Lod1: catalogue 267 → N64 index 262; Lod2: catalogue 214 → N64 index 209 |
| 14 | Elan Mak | Podd: catalogue 28 → N64 index 28; MAlt: catalogue 27 → N64 index 27; Pupp: catalogue 100 → N64 index 100; Lod1: catalogue 268 → N64 index 263; Lod2: catalogue 217 → N64 index 212 |
| 15 | Neva Kee | Podd: catalogue 30 → N64 index 30; MAlt: catalogue 29 → N64 index 29; Pupp: catalogue 103 → N64 index 103; Lod1: catalogue 269 → N64 index 264; Lod2: catalogue 223 → N64 index 218 |
| 16 | Bozziee Baranta | Podd: catalogue 32 → N64 index 32; MAlt: catalogue 31 → N64 index 31; Pupp: catalogue 106 → N64 index 106; Lod1: catalogue 270 → N64 index 265; Lod2: catalogue 211 → N64 index 206 |
| 17 | Boles Roor | Podd: catalogue 34 → N64 index 34; MAlt: catalogue 33 → N64 index 33; Pupp: catalogue 107 → N64 index 107; Lod1: catalogue 271 → N64 index 266; Lod2: catalogue 210 → N64 index 205 |
| 18 | Ody Mandrell | Podd: catalogue 36 → N64 index 36; MAlt: catalogue 35 → N64 index 35; Pupp: catalogue 90 → N64 index 90; Lod1: catalogue 272 → N64 index 267; Lod2: catalogue 224 → N64 index 219 |
| 19 | Fud Sang | Podd: catalogue 38 → N64 index 38; MAlt: catalogue 37 → N64 index 37; Pupp: catalogue 102 → N64 index 102; Lod1: catalogue 273 → N64 index 268; Lod2: catalogue 218 → N64 index 213 |
| 20 | Ben Quadinaros | Podd: catalogue 40 → N64 index 40; MAlt: catalogue 39 → N64 index 39; Pupp: catalogue 94 → N64 index 94; Lod1: catalogue 274 → N64 index 269; Lod2: catalogue 209 → N64 index 204 |
| 21 | Slide Paramita | Podd: catalogue 42 → N64 index 42; MAlt: catalogue 41 → N64 index 41; Pupp: catalogue 104 → N64 index 104; Lod1: catalogue 275 → N64 index 270; Lod2: catalogue 226 → N64 index 221 |
| 22 | Toy Dampner | Podd: catalogue 44 → N64 index 44; MAlt: catalogue 43 → N64 index 43; Pupp: catalogue 101 → N64 index 101; Lod1: catalogue 276 → N64 index 271; Lod2: catalogue 228 → N64 index 223 |
| 23 | Bullseye Navior | Podd: catalogue 46 → N64 index 46; MAlt: catalogue 45 → N64 index 45; Pupp: catalogue 108 → N64 index 108; Lod1: catalogue 277 → N64 index 272; Lod2: catalogue 212 → N64 index 207 |
| 24 | Jinn Reeso | Podd: catalogue 299 → N64 index 283; MAlt: catalogue 298 → N64 index 282; Pupp: catalogue 304 → N64 index 288; Lod1: catalogue 302 → N64 index 286; Lod2: — |
| 25 | Cy Yunga | Podd: catalogue 301 → N64 index 285; MAlt: catalogue 300 → N64 index 284; Pupp: catalogue 305 → N64 index 289; Lod1: catalogue 303 → N64 index 287; Lod2: — |

## Track catalogue — 25 entries

`Track.Model` is a logical model catalogue reference, not a physical block index. Exact-name matching resolved **11/25** track references. The remaining **14** have release-specific or placeholder aliases that this pass did not resolve. **Unresolved does not mean missing.** The physical N64 model inventory also contains 14 `N64__`-prefixed alias records; the equal counts are a lead for further mapping work, **not** proof of a one-to-one assignment to those 14 tracks.

| ID | Track | Planet | Model catalogue reference | N64 exact-name match |
|---:|---|---|---:|---|
| 0 | The Boonta Training Course | Tatooine | 115 | index 115 |
| 1 | The Boonta Classic | Tatooine | 1 | index 1 |
| 2 | Beedo's Wild Ride | Ando Prime | 130 | index 130 |
| 3 | Howler Gorge | Ando Prime | 131 | index 131 |
| 4 | Andobi Mountain Run | Ando Prime | 132 | alias unresolved |
| 5 | Andobi Prime Centrum | Ando Prime | 128 | index 128 |
| 6 | Aquilaris Classic | Aquilaris | 133 | alias unresolved |
| 7 | Sunken City | Aquilaris | 134 | alias unresolved |
| 8 | Bumpy's Breakers | Aquilaris | 135 | alias unresolved |
| 9 | Scrapper's Run | Ord Ibanna | 136 | alias unresolved |
| 10 | Dethro's Revenge | Ord Ibanna | 137 | alias unresolved |
| 11 | Abyss | Ord Ibanna | 138 | alias unresolved |
| 12 | Baroo Coast | Baroonda | 139 | alias unresolved |
| 13 | Grabvine Gateway | Baroonda | 140 | alias unresolved |
| 14 | Fire Mountain Rally | Baroonda | 141 | alias unresolved |
| 15 | Inferno | Baroonda | 129 | index 129 |
| 16 | Mon Gazza Speedway | Mon Gazza | 142 | index 142 |
| 17 | Spice Mine Run | Mon Gazza | 143 | index 143 |
| 18 | Zugga Challenge | Mon Gazza | 144 | index 144 |
| 19 | Vengeance | Oovo IV | 145 | alias unresolved |
| 20 | Executioner | Oovo IV | 148 | alias unresolved |
| 21 | The Gauntlet | Oovo IV | 231 | alias unresolved |
| 22 | Malastare 100 | Malastare | 232 | alias unresolved |
| 23 | Dug Derby | Malastare | 233 | index 228 |
| 24 | Sebulba's Legacy | Malastare | 315 | index 299 |

## Regional comparison — USA, Europe and Japan

A separate comparison of `Release.csv`, `Block.csv` and `BlockItem.csv` at the same pinned source revision found:

| Release | Model block | Model entries | Sprite block | Sprite entries |
|---|---|---:|---|---:|
| N64 USA | `n64_us` (ID 2) | 307 | `n64_us` (ID 2) | 173 |
| N64 Europe | `n64_eu-jp` (ID 1) | 307 | `_default` (ID 0) | 179 |
| N64 Japan | `n64_eu-jp` (ID 1) | 307 | `n64_jp` (ID 1) | 182 |

- **Models:** USA vs Europe and USA vs Japan each show zero physical-index name differences across all 307 entries. The same 123 racer model references also resolve by exact name in all three selected N64 model blocks. This supports one shared N64 model inventory across the three regional metadata variants; it is still metadata evidence, not a byte-for-byte runtime test.
- **Sprites:** USA vs Europe/default differ at 8 physical indices; USA vs Japan differ at 11. Do not share a single regional sprite index map blindly. The Europe release points to the shared `_default` block in `Release.csv`; it is not labeled as a dedicated N64 Europe sprite block.
- **Splines and textures:** all three N64 release rows select the same spline block ID 1 and texture block ID 1 in `Release.csv`.

These differences suggest a practical content-pipeline split: shared N64 model/spline/texture metadata, but separately resolved regional sprite catalogues. No sprite payload or image is included.

### Group-level candidates for the 14 unresolved tracks

The 14 unresolved `Track.Model` rows can be narrowed to six candidate groups by planet label in the N64 model block:

| Planet | Unresolved track IDs | Candidate physical indices | Confidence |
|---|---|---|---|
| Ando Prime | 4 | 132 | HYPOTHESIS |
| Aquilaris | 6, 7, 8 | 133, 134, 135 | HYPOTHESIS |
| Ord Ibanna | 9, 10, 11 | 136, 137, 138 | HYPOTHESIS |
| Baroonda | 12, 13, 14 | 139, 140, 141 | HYPOTHESIS |
| Oovo IV | 19, 20, 21 | 145, 148, 226 | HYPOTHESIS; all three aliases are marked UNITYNULLREF |
| Malastare | 22 | 227 | HYPOTHESIS |

The candidate counts and planet labels line up, but they do not establish individual track-to-index identity. In particular, do not map same-planet tracks by order alone. The full alias names and per-track group membership are included in the JSON as `trackAliasCandidateGroups`.

## Critical mapping rule

Three different identifiers occur in the source metadata:

- `ModelBlockItem.Id`: logical model-value catalogue ID;
- `BlockItem.ValueId`: logical value ID associated with one item in a selected block;
- `BlockItem.Index`: physical item index inside that block.

They are not interchangeable. Bonus-racer aliases demonstrate why ID-only joins are unsafe: some N64 physical entries use a different value ID from the canonical racer table while retaining the same exact model name.

The upstream [`TrakModelFormatTester.cs`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original.Tests/Format/Testers/ModelBlock/Models/TrakModelFormatTester.cs) explicitly marks its track lookup as a TODO because its `Track.Model` lookup fails for values such as 1001. Track alias resolution is therefore left open rather than guessed.

## Source files

- [`ModelBlockItem`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/ModelBlockItem.csv)
- [`Racer`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Racer.csv)
- [`Track`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Track.csv)
- [`BlockItem`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/BlockItem.csv)
- [`Block`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Block.csv)
- [`SplineBlockItem`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/SplineBlockItem.csv)
- [`SpriteBlockItem`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/SpriteBlockItem.csv)
- [`TextureBlockItem`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/TextureBlockItem.csv)
- [`Release`](https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks/Resources/Metadata/Release.csv)

## What this inventory does not prove

- It does not establish that every track entry is present or selectable in every region or revision.
- It does not reconstruct game assets or authorize their redistribution.
- It does not validate track geometry, spline continuity, textures, collisions or runtime loading.
- It does not establish N64-to-GameCube/Wii compatibility.
- It does not replace the local material/texture exporter validation tracked in PR #381.

Machine-readable version: [`n64-us-content-catalog.json`](data/n64-us-content-catalog.json).

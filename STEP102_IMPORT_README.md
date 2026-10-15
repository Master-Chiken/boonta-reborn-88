# Step 102 source-only import bundle

This is a selective import of the supplied Step 102 native GameCube/Wii prototype.

Included: C source and headers, procedural demo centerline inputs, selected host regression tests and mock-libogc declarations, and general build/test utilities.

Excluded: PC-mod-derived centerline data and manifests, imported centerline headers, generated mesh/boundary headers, all voice audio, OBJ/MTL model assets, ROM/disc images, extracted data, and PC/N64 asset extraction/reverse-engineering helpers.

The Makefile defaults to `USE_IMPORTED_SPLINE=0`, selecting the bundled demo/procedural centerline rather than any PC-mod-derived route. A successful build remains only compile proof; visible rendering, controller behavior and gameplay require a separate Dolphin/console check.

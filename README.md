# The Last Lighthouse

A tiny lighthouse on a split basalt spire sends its last signal across an immense eclipse. Curving magnetic filaments and solar arches frame the dark disc, while perspective waves break its gold reflection into a cold blue sea. The lantern room, weathered masonry, basalt facets, sea foam, horizon fog, seeded stars, and film grain are rendered from equations.

Run with Python 3.13 and its standard library.

```sh
MAKEFUN_OUTPUT_DIR=out python3.13 main.py
```

The renderer writes a deterministic 768 × 768 RGB PNG to `out/entry.png`. In Make.fun's sandbox it writes to `/output/entry.png` by default.

No packages, model calls, external assets, or network access are required. The PNG writer uses the Python standard library and includes checksums for every chunk. The artwork is distributed under the repository's MIT license.

The renderer packs one RGB row at a time, applies PNG Sub prediction, and feeds
one continuous zlib stream into IDAT chunks capped at 64 KiB. It does not retain
the full uncompressed frame or allocate byte strings for individual pixels.
Sub filtering was retained after a Sub/Up residual heuristic increased this
scene's compressed size. The scene and its reconstructed pixels are preserved.

Run `python3.13 -m unittest -v` for independent PNG CRC, zlib completion, filter
reconstruction, and encoder round-trip tests, including multi-chunk output and
mutable row iterators. The row encoder rejects invalid dimensions and row counts.

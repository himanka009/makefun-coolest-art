# The Last Lighthouse

A tiny lighthouse on a split basalt spire sends its last signal across an immense eclipse. Curving magnetic filaments and solar arches frame the dark disc, while perspective waves break its gold reflection into a cold blue sea. The lantern room, weathered masonry, basalt facets, sea foam, horizon fog, seeded stars, and film grain are rendered from equations.

Run with Python 3.13 and its standard library.

```sh
MAKEFUN_OUTPUT_DIR=out python3.13 main.py
```

The renderer writes a deterministic 768 × 768 RGB PNG to `out/entry.png`. In Make.fun's sandbox it writes to `/output/entry.png` by default.

No packages, model calls, external assets, or network access are required. The PNG writer uses the Python standard library and includes checksums for every chunk. The artwork is distributed under the repository's MIT license.

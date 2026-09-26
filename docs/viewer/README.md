# Nami 3D viewer

Static full-color GLB viewer, published at https://jemdiggity.github.io/nami/viewer/.
GitHub Pages serves the `docs/` directory on `main`.

Regenerate the model from the compact PCB with:

```sh
python3 hardware/tools/export_web_model.py
```

Requires KiCad 10; set `KICAD_CLI` if it is not on PATH or at the standard macOS location. Export preserves KiCad geometry, colors, pads, and silkscreen. The script adjusts material roughness/metallicity and makes soldermask/FR4 opaque for reliable browser rendering. No source PCB changes are made.

Preview locally from the repository root:

```sh
python3 -m http.server 8765 --directory docs
```

Open http://localhost:8765/viewer/. Model-viewer 4.1.0 is vendored from the official `@google/model-viewer` npm package; its Apache 2.0 license is included under `vendor/`. The page and model need no CDN at runtime. Geometry is illustrative and not a manufacturing acceptance model.

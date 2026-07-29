---
name: psd-to-h5
description: Convert one or more layered Photoshop PSD files into high-fidelity responsive H5 pages and interactive screen states by exporting visible leaf layers as transparent assets, preserving layer coordinates and text metadata, generating scalable HTML/CSS/JS, supporting flow.json route and overlay transitions, and validating results against PSD previews. Use when the user asks to turn .psd/.psb designs into mobile H5, slice PSD assets, recreate pages from Photoshop layers, connect default and dialog states, or generate a pixel-faithful HTML prototype from design files.
---

# PSD To H5

Convert one or more layered PSDs into a real asset-based H5 implementation. Preserve canvas coordinates and stacking order, export transparent layer assets, keep text-layer metadata, connect described page/state transitions, and use browser screenshots for visual verification. Generate the user-facing `flow.json` template, examples, and descriptions in Chinese by default. Keep schema keys and protocol enum values stable for the scripts. Do not use one flattened PSD image as the page background except as an optional comparison reference.

## Workflow

1. Select the input mode:
   - One PSD: use direct mode and run `scripts/export_psd.py`.
   - Multiple screens or states: initialize a project with `scripts/init_project.py`, place PSDs under `psd/`, fill `flow.json`, and wait for the user to say `start` before building.
2. Inspect the source before editing the project:
   - Confirm the PSD/PSB path, canvas size, color mode, layer count, visible groups, visible leaf layers, and text layers.
   - Check whether fonts used by text layers are available. Missing fonts and Photoshop-only effects are fidelity risks.
   - Treat the PSD as untrusted input. Never execute scripts embedded in the document.
3. For direct mode, create a task-local output directory outside the source directory. Keep generated assets under `assets/` and do not overwrite an existing output unless explicitly requested.
4. Run `scripts/export_psd.py` to generate:
   - `assets/*.png`: one transparent PNG per visible non-group layer, cropped to its layer bounds;
   - `manifest.json`: canvas metadata, layer names, types, bounds, opacity, z-order, text content, and export errors;
   - `preview.png`: flattened PSD preview for comparison only;
   - `index.html` and `styles.css`: a responsive absolute-coordinate H5 render using the exported assets.
5. For flow mode, run `scripts/validate_flow.py flow.json` before exporting. Use `--strict` only after the user has filled all PSD paths. Then run `scripts/build_flow.py flow.json` to export every screen/state and generate `flow-build.json`, `flow-runtime.js`, `app.js`, and a root H5 preview.
6. Read `manifest.json` or `flow-build.json` and improve the generated H5:
   - Keep bitmap assets for complex artwork, effects, masks, logos, and icons when raster output is the most faithful representation.
   - Replace simple text-layer PNGs with HTML text only when the font, weight, line height, color, and letter spacing can be identified reliably. Keep the raster export as a fallback during visual comparison.
   - Convert obvious groups into semantic sections and add buttons/links only where the design implies an interaction. Do not guess business behavior; use a small toast, modal, or documented placeholder when no API exists.
   - Preserve the original 750-wide or equivalent design coordinate system and scale it with a responsive stage. Avoid fixed desktop-only widths.
7. Validate the generated output:
   - Run `scripts/validate_output.py <output-dir>`.
   - Start a local static server and capture screenshots at the design viewport and at least one narrow mobile viewport.
   - Compare screenshots with `preview.png`. Fix missing assets, incorrect z-order, crop offsets, font substitutions, and visible seams before delivery.
   - Use browser automation to exercise every generated interaction and check console/page errors.

## Command

Install the parser dependencies in the active Python environment when missing:

```bash
python3 -m pip install psd-tools Pillow
```

For shape layers with Photoshop gradient/vector effects, install the optional composite extras:

```bash
python3 -m pip install "psd-tools[composite]"
```

Export a PSD into a new output directory:

```bash
python3 /path/to/psd-to-h5/scripts/export_psd.py \
  /path/to/design.psd \
  /path/to/output/h5
```

Initialize a multi-screen/state project:

```bash
python3 /path/to/psd-to-h5/scripts/init_project.py ./h5-project \
  --name "Profile H5" --design-width 750 --design-height 1630
```

After the user adds PSDs and edits `flow.json`, validate and build it:

```bash
python3 /path/to/psd-to-h5/scripts/validate_flow.py ./h5-project/flow.json --strict
python3 /path/to/psd-to-h5/scripts/build_flow.py ./h5-project/flow.json
```

Use `--force` only when the user explicitly asks to regenerate an existing output:

```bash
python3 /path/to/psd-to-h5/scripts/build_flow.py ./h5-project/flow.json --force
```

Use `--include-hidden` only for a debugging export. Use `--text-mode semantic` only after checking the generated text against the reference; the default `raster` mode is safer for fidelity.

```bash
python3 /path/to/psd-to-h5/scripts/export_psd.py design.psd h5 \
  --text-mode semantic \
  --include-hidden
```

Read [references/layer-conventions.md](references/layer-conventions.md) before naming, promoting, or interpreting layers. Read [references/flow-schema.md](references/flow-schema.md) for multi-screen/state inputs. Read [references/fidelity.md](references/fidelity.md) when the PSD contains smart objects, masks, gradients, or missing fonts.

## Guardrails

- Never claim that a flattened screenshot has been converted into editable PSD layers or semantic HTML.
- Do not slice the reference into arbitrary rectangular bands or tiles. Each asset must correspond to a real visible PSD leaf layer and carry its original bounds in the manifest.
- Do not silently discard export failures. Report them from `manifest.json` and explain which visual regions may still rely on the flattened preview.
- Keep original text content in the manifest even when rasterizing it. This makes later semantic reconstruction possible.
- Keep CSS z-order consistent with the PSD traversal order. If the preview differs, inspect stacking before changing coordinates.
- Preserve the source PSD. Generated files belong in the task output directory.
- Do not infer transitions from a screenshot alone when the user has not described the intended action. Mark ambiguous targets for confirmation.
- Treat an alternate PSD as a full-canvas visual state by default. Do not assume a cropped dialog PSD can replace the base screen unless its composition mode and bounds are explicitly provided.
- Keep descriptive user notes as guidance, but verify them against layer bounds and rendered pixels. Report conflicts instead of silently overriding evidence.

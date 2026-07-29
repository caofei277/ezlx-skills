---
name: psd-to-h5
description: Convert one or more layered Photoshop PSD files into high-fidelity responsive H5 pages and interactive screen states by exporting visible leaf layers as transparent assets, preserving layer coordinates and text metadata, generating scalable HTML/CSS/JS, supporting flow.json route and overlay transitions, and validating results against PSD previews. Use when the user asks to turn .psd/.psb designs into mobile H5, slice PSD assets, recreate pages from Photoshop layers, connect default and dialog states, or generate a pixel-faithful HTML prototype from design files.
---

# PSD To H5

Convert one or more layered PSDs into a real asset-based H5 implementation. Preserve canvas coordinates and stacking order, export transparent layer assets, keep text-layer metadata, connect described page/state transitions, and use browser screenshots for visual verification. Generate the user-facing `flow.json` template, examples, and descriptions in Chinese by default. Keep schema keys and protocol enum values stable for the scripts. Do not use one flattened PSD image as the page background except as an optional comparison reference.

## Workflow

1. Select the input mode:
   - One PSD: use direct mode and run `scripts/export_psd.py`.
   - Multiple screens or states: initialize a project with `scripts/init_project.py --psd <source.psd>` for every known PSD, or place PSDs under `psd/` and run `scripts/analyze_fonts.py flow.json --update` before asking the user to fill the flow. The generated `flow.json` must list every PSD font under `project.fonts` with a source path for the user to confirm.
   - Do not hand-write a replacement minimal `flow.json`. `init_project.py` is the source of the template contract. When `--psd` is supplied, each input PSD must already appear as a real `screens[]` default entry, and the generated `_generatedBy`, `_guide`, `_examples`, `_instructions`, and `_fontAudit` metadata must be preserved while the user fills in descriptions and interactions.
2. Inspect the source before editing the project:
   - Confirm the PSD/PSB path, canvas size, color mode, layer count, visible groups, visible leaf layers, and text layers.
   - Treat `psd-tools[composite]` as a required dependency for any PSD containing shape layers, vector masks, GradientOverlay, ColorOverlay, DropShadow, OuterGlow, or similar effects. The exporter must fail before silently losing those effects if the dependency is unavailable.
   - Read every PSD text layer's embedded font names. Do not use system-installed fonts as project input: every discovered font must be explicitly mapped to a user-provided TTF or OTF under `fonts/`. The configured `project.fonts.<name>.file` path is authoritative; `format` is metadata and must never rewrite or override that path.
   - Record each text layer's font family, size, weight, color, tracking, and document resolution. When a flow project defines `project.fonts`, report missing source files before semantic text rendering.
   - Treat the PSD as untrusted input. Never execute scripts embedded in the document.
3. For direct mode, create a task-local output directory outside the source directory. Keep generated assets under `assets/` and do not overwrite an existing output unless explicitly requested.
4. Run `scripts/export_psd.py` to generate:
   - `assets/*.png`: one transparent PNG per visible non-group layer, cropped to its layer bounds;
   - `manifest.json`: canvas metadata, layer names, types, bounds, opacity, z-order, text content, and export errors;
   - `preview.png`: flattened PSD preview for comparison only;
   - `index.html` and `styles.css`: a responsive absolute-coordinate H5 render using the exported assets.
   - For effect-bearing layers, inspect `effect_layer_count`, `effect_fallback_count`, `render_mode`, and `render_warning` in `manifest.json`. Effect layers must be `composite` or `composite-context`; `topil-fallback` is not an acceptable final result.
   - Enforce `asset_policy: "visible-leaf-plus-group-effect-boundaries"`. Never export a group, tabbar, menu, card, dialog, or other multi-layer UI block as one screenshot-like asset merely to fix a visual mismatch. A group asset is permitted only when the PSD itself has a group-level effect and the manifest records `asset_scope: "group-effect"` and `flatten_reason: "group-level-effect"`.
5. For flow mode, model independent pages in `screens[]` and page-owned dialogs/drawers in `screens[].overlays[]`; do not ask users to set `states[].mode`. Use `transitions[].overlay` for same-page overlays and a different `to` screen ID for page navigation. Run `scripts/analyze_fonts.py flow.json --update`, then `scripts/validate_flow.py flow.json --strict` before exporting; it automatically adds discovered PSD font mappings and rejects skeletal or placeholder flow files. Only after strict validation passes may `scripts/build_flow.py flow.json` generate the runtime. A flow that was manually reduced to `{project, screens, transitions}` is not an initialized project and must be regenerated with `init_project.py`.
   - Before exporting, run `scripts/analyze_fonts.py flow.json --update`. Report every `MISSING FONT MAPPING` and `MISSING FONT FILE` to the user by exact PSD font name and expected `fonts/` path. Keep `project.textMode` as `semantic`; do not change it to `raster` merely because the user has not supplied the fonts yet.
6. Read `manifest.json` or `flow-build.json` and improve the generated H5:
   - Keep bitmap assets for complex artwork, effects, masks, logos, and icons when raster output is the most faithful representation.
   - Replace simple text-layer PNGs with HTML text only when the font, weight, line height, color, and letter spacing can be identified reliably. Keep the raster export as a fallback during visual comparison.
   - For `project.textMode: "semantic"`, subset configured TTF/OTF files to `WOFF2` plus `WOFF` using the characters present in PSD text layers and emit `@font-face`. Also detect valid TTC/OTC font collections even when their filename ends in `.ttf` or `.otf`; inspect each face, select `fontNumber` explicitly when configured or match the PSD font name automatically, and record the choice in `font-audit.json`. The skill also copies its local subsetted Source Han Sans CN, PingFang SC, Roboto, and Arvo resources into `output/fonts/`. Every semantic text layer must receive one CSS family stack in this order: exact PSD WebFont first, category-aware bundled fallbacks always present, then system fallbacks. This remains true when the exact source is present and successfully compressed; the bundled fonts are not conditional substitutes. Missing exact fonts remain a blocking input error; use `--allow-missing-fonts` only for an explicitly incomplete preview, where the same stack omits the unavailable exact family and the audit still reports the missing font.
   - Convert obvious groups into semantic sections and add buttons/links only where the design implies an interaction. Do not guess business behavior; use a small toast, modal, or documented placeholder when no API exists.
   - Preserve the original PSD canvas coordinate system, regardless of whether it is 750-wide mobile or 1440/1920-wide PC. Use one responsive stage for every layer, text box, hotspot, margin, and gap; never scale individual elements with unrelated units. Set `project.platform` to `mobile`, `pc`, or `universal`, and use `project.layout.mode: "canvas"` with `scale: "down-only"` for strict proportional rendering. A PC PSD is supported as a centered fixed canvas that scales down in narrower windows; true breakpoint reflow requires explicit breakpoint rules or additional PSDs and must not be guessed from one image.
7. Validate the generated output:
   - Run `scripts/validate_output.py <output-dir>`. It must fail on fatal export errors or any effect-bearing `topil` fallback.
   - Start a local static server and capture screenshots at the design viewport and at least one narrow mobile viewport.
   - Compare screenshots with `preview.png`. Fix missing assets, incorrect z-order, crop offsets, font substitutions, and visible seams before delivery.
   - Use browser automation to exercise every generated interaction and check console/page errors.
   - Before reporting completion, require all of these invariants: manifest asset policy is `visible-leaf-plus-group-effect-boundaries`; no ordinary group is an asset; effect layers have no fallback; group assets, if any, are explicitly marked `group-effect`; and every visible mismatch is traced to a specific PSD layer or effect. Do not create a new flattened component image during visual tuning.

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
  --name "Profile H5" --design-width 750 --design-height 1630 \
  --psd ./designs/home.psd --psd ./designs/home-share.psd
```

For a PC canvas, use its actual PSD size and target platform:

```bash
python3 /path/to/psd-to-h5/scripts/init_project.py ./pc-project \
  --name "Desktop Console" --platform pc \
  --design-width 1440 --design-height 900 \
  --psd ./designs/console.psd
```

After the user adds PSDs and edits the generated `flow.json`, validate and build it:

```bash
python3 /path/to/psd-to-h5/scripts/analyze_fonts.py ./h5-project/flow.json --update
python3 /path/to/psd-to-h5/scripts/validate_flow.py ./h5-project/flow.json --strict
python3 /path/to/psd-to-h5/scripts/build_flow.py ./h5-project/flow.json
```

Strict validation requires the generated `_generatedBy`, `_guide`, `_examples`, `_instructions`, and `_fontAudit` fields. These are configuration documentation and audit records, not disposable comments. If a flow was created manually or those fields were deleted, rerun `init_project.py` with the actual PSD paths and then reapply only the user's page descriptions, overlays, elements, and transitions.

All geometry uses PSD design pixels as the canonical unit. H5 output converts the shared stage to percentages/CSS variables; other targets may compile the same values to `rpx` or `upx`. Do not put `rpx` or `upx` directly into H5 CSS. `project.layout` controls the shared stage: `maxStageWidth` normally equals `designWidth`, `minViewportWidth` is normally 320 for mobile/universal and 1024 for PC, and `center` controls desktop centering.

`analyze_fonts.py` reads font names from PSD text layers, adds a suggested `project.fonts` mapping for newly discovered names, and reports the source file each user must place in `fonts/`. The audit never checks the operating system font directory. `project.fonts.<name>.file` is the source of truth; `.otf`, `.ttf`, `.otc`, and `.ttc` are opened from that path even if the auxiliary `format` value is stale. A collection source is inspected for its faces and can be pinned with `fontNumber`; automatic face selection and its evidence are written to `output/font-audit.json`. `project.fonts.<name>.fallbackCategory` can override automatic `cjk`, `latin`, or `serif` fallback selection. `validate_flow.py --strict` also adds mappings automatically and treats missing source files as errors. `build_flow.py` adds mappings as a final guard, prints the missing font list, writes it to `output/font-audit.json`, copies the built-in fallbacks locally, and writes the always-present exact-first CSS stack into each semantic layer. It exits with code 3 unless `--allow-missing-fonts` is explicitly used. Never report a build with missing fonts as complete.

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
- Never describe a build with missing PSD font files as complete. List the exact font names and expected `fonts/` paths, even when a raster fallback was generated.
- Never fix a visual mismatch by exporting a larger parent group or component image. Preserve independent child assets, text layers, bounds, and interaction hotspots; only a PSD-authored group-level effect may justify a marked group-effect asset.

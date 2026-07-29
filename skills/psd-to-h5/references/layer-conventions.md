# Layer Conventions

Layer names are metadata, not a substitute for inspecting the layer type and rendered result. Prefer explicit names when the designer provides them:

| Suffix | Meaning | H5 treatment |
| --- | --- | --- |
| `|text` | Editable text candidate | Use HTML text after verifying font metrics; keep PNG fallback |
| `|img` | Bitmap or smart object | Use the exported transparent PNG |
| `|bg` | Background or gradient | Use a layer asset or CSS only when CSS matches the preview |
| `|button` | Interactive visual region | Wrap the visual layer in a semantic button and add a handler |
| `|link` | Navigation visual region | Wrap the visual layer in an anchor or router link |
| `|group` | Layout/container group | Recreate as a semantic section when it contains a meaningful workflow |

When no suffix exists, use PSD layer kind and visual inspection. `type` layers are text candidates, `smartobject` layers are bitmap candidates, `shape` layers can be CSS or PNG depending on effects, and `group` layers should not be exported as duplicate leaf images.

## Coordinate Rules

- Use the PSD canvas as the design coordinate system.
- Store bounds as `[left, top, right, bottom]` in source pixels.
- Render every target inside one stage whose width is `min(100vw, project.layout.maxStageWidth)` and whose aspect ratio matches the PSD. For PC, center the stage and set `project.layout.minViewportWidth` appropriately; do not infer a fluid column reflow from a single PSD.
- Keep PSD pixels as the canonical unit for positions, dimensions, margins, padding, and gaps. H5 converts them at the stage boundary; `rpx` and `upx` are target-platform output units, not units to mix into H5 CSS.
- Convert coordinates to percentages or CSS custom properties. Do not resize individual assets independently from their recorded bounds.
- Retain the source z-order. A background layer should be below its child artwork, and text should remain above the artwork it labels.

## Text Rules

The `manifest.json` text entry is authoritative for content, not necessarily for exact font rendering. Verify:

- family and fallback family;
- font size and weight;
- line height and letter spacing;
- anti-aliasing differences between Photoshop and browser;
- whether the layer uses warp, character styles, paragraph styles, or effects.

If any of these are uncertain, render the exported PNG and expose the text content in metadata or accessible attributes rather than forcing an inaccurate HTML text layer.

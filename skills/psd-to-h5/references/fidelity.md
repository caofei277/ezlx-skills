# Fidelity And Failure Modes

## Reliable Cases

Layered UI screens with a known mobile canvas, ordinary text layers, transparent icons, flat shapes, and simple groups usually convert well. Exporting each visible leaf layer retains the original pixels while keeping the HTML layout responsive.

## Risky Cases

- Smart objects may expose only a rendered thumbnail instead of their editable source.
- Photoshop-only blend modes, filters, layer effects, and adjustment layers may not render identically through `psd-tools`.
- Shape layers with gradients, vector masks, ColorOverlay, or other layer effects require `psd-tools[composite]`; the exporter now fails instead of silently using `topil()` for an effect-bearing layer.
- Missing fonts make semantic text differ even when the text content is correct.
- A `.ttf` or `.otf` filename may contain a TTC/OTC font collection. The builder must inspect the file signature and collection faces instead of assuming one face from the extension; otherwise a valid source can incorrectly fall back to raster text.
- The skill bundles subsetted Source Han Sans CN, PingFang SC, Roboto, and Arvo as local project fonts. They are always emitted and ordered by CJK, Latin, or serif category after the exact PSD font and before system fonts in every semantic layer's CSS `font-family`. They improve network/runtime resilience but cannot reproduce the metrics of a missing PSD font and never clear the missing-font audit.
- Clipping masks and inherited group visibility can produce blank or duplicated exports if the layer tree is flattened incorrectly.
- Groups are structural containers, not general export assets. A group is allowed as a raster boundary only when the PSD itself puts a layer effect on that group; flattening a tabbar, menu, card, or dialog group merely to match a screenshot destroys independent text and interaction boundaries.
- Hidden layers should be omitted from the page but preserved in the manifest only when `--include-hidden` is requested.

## Recovery

1. Use `manifest.json` to find the failing layer and its bounds.
2. Install `psd-tools[composite]` and rerun the export. `validate_output.py` treats effect-bearing `topil()` fallbacks as failures.
3. Inspect the individual layer with `layer.topil()` or open it in Photoshop/Photopea and export that layer as a transparent PNG.
4. Keep the recovered asset at the same bounds and z-index. Do not replace the whole page with a flattened screenshot.
5. Re-render the H5 and compare against `preview.png` at the PSD's native aspect ratio.

## Effect Bounds

Drop shadows and outer glows can extend outside a layer's Photoshop `bbox`. The exporter estimates the effect extent, caches one full-PSD composite per source, and uses the full composite only for the outside effect band while keeping the original layer's isolated pixels inside the original bounds. The manifest records `render_mode: "composite-context"` and the expanded bounds. This avoids cropping a tabbar shadow while limiting duplication of neighboring layers.

## Asset Boundary

The default export policy is `visible-leaf-plus-group-effect-boundaries`. Every ordinary asset must point to one visible PSD leaf layer and preserve its `path`, `bounds`, z-order, text metadata, and effects. A group asset is accepted only when its own PSD layer effects are recorded as `flatten_reason: "group-level-effect"`; this is different from manually exporting a whole tabbar or menu. The exporter and validator reject arbitrary group flattening.

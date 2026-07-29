# Fidelity And Failure Modes

## Reliable Cases

Layered UI screens with a known mobile canvas, ordinary text layers, transparent icons, flat shapes, and simple groups usually convert well. Exporting each visible leaf layer retains the original pixels while keeping the HTML layout responsive.

## Risky Cases

- Smart objects may expose only a rendered thumbnail instead of their editable source.
- Photoshop-only blend modes, filters, layer effects, and adjustment layers may not render identically through `psd-tools`.
- Shape layers with gradients or vector masks may require `psd-tools[composite]` or a Photoshop export fallback.
- Missing fonts make semantic text differ even when the text content is correct.
- Clipping masks and inherited group visibility can produce blank or duplicated exports if the layer tree is flattened incorrectly.
- Hidden layers should be omitted from the page but preserved in the manifest only when `--include-hidden` is requested.

## Recovery

1. Use `manifest.json` to find the failing layer and its bounds.
2. Retry with `psd-tools[composite]` installed.
3. Inspect the individual layer with `layer.topil()` or open it in Photoshop/Photopea and export that layer as a transparent PNG.
4. Keep the recovered asset at the same bounds and z-index. Do not replace the whole page with a flattened screenshot.
5. Re-render the H5 and compare against `preview.png` at the PSD's native aspect ratio.

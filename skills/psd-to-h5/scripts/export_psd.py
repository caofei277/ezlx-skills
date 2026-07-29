#!/usr/bin/env python3
"""Export visible PSD leaf layers and generate a responsive asset-based H5 render."""

from __future__ import annotations

import argparse
from html import escape
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


def fail(message: str) -> None:
    print(f"[psd-to-h5] error: {message}", file=sys.stderr)
    raise SystemExit(2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to a .psd or .psb file")
    parser.add_argument("output", type=Path, help="New output directory")
    parser.add_argument("--include-hidden", action="store_true", help="Export hidden leaf layers too")
    parser.add_argument("--text-mode", choices=("raster", "semantic"), default="raster")
    parser.add_argument("--force", action="store_true", help="Allow overwriting generated files in an existing output directory")
    return parser.parse_args()


def load_dependencies():
    try:
        from PIL import Image  # noqa: F401
        from psd_tools import PSDImage
    except ImportError as exc:
        fail("missing dependencies; run: python3 -m pip install psd-tools Pillow")
    return PSDImage


def safe_filename(name: str, index: int) -> str:
    ascii_name = name.encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name).strip("-.")[:48]
    return f"{index:04d}-{ascii_name or 'layer'}.png"


def as_bounds(value: Any) -> list[int] | None:
    if value is None:
        return None
    try:
        bounds = [int(round(float(item))) for item in value]
    except (TypeError, ValueError):
        return None
    return bounds if len(bounds) == 4 and bounds[2] > bounds[0] and bounds[3] > bounds[1] else None


def layer_text(layer: Any) -> str | None:
    if getattr(layer, "kind", None) != "type":
        return None
    value = getattr(layer, "text", None)
    return value if isinstance(value, str) else None


def text_styles(layer: Any) -> list[dict[str, Any]]:
    """Extract browser-relevant character styles from Photoshop EngineData."""
    if getattr(layer, "kind", None) != "type":
        return []
    try:
        engine = getattr(layer, "engine_dict", {}) or {}
        resources = getattr(layer, "resource_dict", {}) or {}
        font_set = resources.get("FontSet", []) or []
        runs = ((engine.get("StyleRun") or {}).get("RunArray") or [])
        styles: list[dict[str, Any]] = []
        for run in runs:
            data = ((run.get("StyleSheet") or {}).get("StyleSheetData") or {})
            raw_index = data.get("Font")
            index = int(raw_index) if raw_index is not None else -1
            font_name = ""
            if 0 <= index < len(font_set):
                font_name = str(font_set[index].get("Name", "")).strip().strip("'\"")
            raw_size = data.get("FontSize")
            font_size = float(raw_size) if raw_size is not None else None
            fill = data.get("FillColor") or {}
            values = fill.get("Values") or []
            color = None
            if len(values) >= 4:
                # Photoshop stores this color as alpha, red, green, blue.
                color = "#%02x%02x%02x" % tuple(max(0, min(255, round(float(value) * 255))) for value in values[1:4])
            styles.append({
                "font_family": font_name,
                "font_size": font_size,
                "font_weight": 700 if data.get("FauxBold") or "Bold" in font_name else 400,
                "font_style": "italic" if data.get("FauxItalic") else "normal",
                "letter_spacing": float(data.get("Tracking", 0) or 0) / 1000,
                "color": color,
            })
        return [style for style in styles if style.get("font_family") or style.get("font_size")]
    except Exception:
        return []


def has_effects(layer: Any) -> bool:
    try:
        return bool(list(getattr(layer, "effects", ()) or ()))
    except Exception:
        return False


def walk_layers(node: Any, parent_visible: bool = True, path: tuple[str, ...] = ()) -> Iterable[tuple[Any, bool, tuple[str, ...]]]:
    for child in node:
        current_path = path + (str(getattr(child, "name", "layer")),)
        visible = parent_visible and bool(getattr(child, "visible", True))
        yield child, visible, current_path
        # Render an effect-bearing group as one asset so inherited effects are
        # preserved instead of being lost or duplicated across its children.
        if getattr(child, "kind", None) == "group" and not has_effects(child):
            yield from walk_layers(child, visible, current_path)


def render_layer(layer: Any):
    composite_error = None
    try:
        image = layer.composite()
        if image is not None:
            return image.convert("RGBA"), "composite", composite_error
    except Exception as exc:
        composite_error = str(exc)
    image = layer.topil()
    if image is None:
        raise RuntimeError("layer renderer returned no image")
    return image.convert("RGBA"), "topil-fallback", composite_error


def write_h5(output: Path, width: int, height: int, layers: list[dict[str, Any]], text_mode: str) -> None:
    html_layers: list[str] = []
    for index, layer in enumerate(layers):
        left, top, right, bottom = layer["bounds"]
        text = layer.get("text")
        alt = escape(text or "", quote=True)
        common = (
            f'data-layer="{escape(layer["name"], quote=True)}" data-kind="{layer["kind"]}" '
            f'data-text="{alt}" style="--x:{left};--y:{top};--w:{right-left};--h:{bottom-top};'
            f'--z:{index};--opacity:{1 if layer.get("rendered_opacity") else layer["opacity"] / 255:.4f};'
        )
        if text_mode == "semantic" and text:
            font_size = max(8, int((bottom - top) * 0.78))
            html_layers.append(
                f'      <span class="psd-text" {common}--font-size:{font_size};">{escape(text)}</span>'
            )
        else:
            html_layers.append(
                f'      <img class="psd-layer" src="{layer["asset"]}" alt="{alt}" {common}" />'
            )

    semantic_note = "" if text_mode == "raster" else " Text layers remain rasterized until their browser font metrics are verified."
    html = f'''<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>PSD to H5 Preview</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <main class="preview" aria-label="PSD H5 preview">
      <div class="psd-stage" style="--design-width:{width};--design-height:{height};">
{chr(10).join(html_layers)}
      </div>
    </main>
    <!-- Generated from real visible PSD leaf layers.{semantic_note} -->
  </body>
</html>
'''
    css = f''':root {{ font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif; background: #f2f2f2; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; min-height: 100%; }}
body {{ min-width: 320px; background: #f2f2f2; }}
.preview {{ display: flex; justify-content: center; min-height: 100vh; }}
.psd-stage {{ position: relative; width: min(100vw, calc(var(--design-width) * 1px)); aspect-ratio: var(--design-width) / var(--design-height); overflow: hidden; background: #fff; isolation: isolate; }}
.psd-layer, .psd-text {{ position: absolute; display: block; left: calc(var(--x) * 100% / var(--design-width)); top: calc(var(--y) * 100% / var(--design-height)); width: calc(var(--w) * 100% / var(--design-width)); height: calc(var(--h) * 100% / var(--design-height)); z-index: var(--z); opacity: var(--opacity); user-select: none; -webkit-user-drag: none; }}
.psd-text {{ overflow: hidden; color: #3d3026; font-size: min(calc(var(--font-size) * 100vw / var(--design-width)), calc(var(--font-size) * 1px)); line-height: 1; white-space: nowrap; }}
@media (min-width: 520px) {{ .preview {{ padding: 28px 0; }} .psd-stage {{ border-radius: 12px; box-shadow: 0 12px 40px rgba(34,24,14,.16); }} }}
'''
    (output / "index.html").write_text(html, encoding="utf-8")
    (output / "styles.css").write_text(css, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        fail(f"source does not exist: {source}")
    if output.exists() and not args.force and any(output.iterdir()):
        fail(f"output is not empty: {output}; choose a new directory or pass --force")
    output.mkdir(parents=True, exist_ok=True)
    assets_dir = output / "assets"
    assets_dir.mkdir(exist_ok=True)

    PSDImage = load_dependencies()
    try:
        psd = PSDImage.open(source)
    except Exception as exc:
        fail(f"could not open PSD: {exc}")

    width, height = map(int, psd.size)
    layers: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    order = 0
    for layer, visible, path in walk_layers(psd):
        kind = str(getattr(layer, "kind", "unknown"))
        if (kind == "group" and not has_effects(layer)) or (not visible and not args.include_hidden):
            continue
        bounds = as_bounds(getattr(layer, "bbox", None))
        if bounds is None:
            errors.append({"name": getattr(layer, "name", "layer"), "reason": "invalid bounds"})
            continue
        name = str(getattr(layer, "name", "layer"))
        filename = safe_filename(name, order)
        asset_path = assets_dir / filename
        record: dict[str, Any] = {
            "index": order,
            "name": name,
            "path": list(path),
            "kind": kind,
            "visible": visible,
            "bounds": bounds,
            "opacity": int(getattr(layer, "opacity", 255) or 255),
            "rendered_opacity": True,
            "asset": f"assets/{filename}",
        }
        try:
            record["blend_mode"] = str(getattr(layer, "blend_mode", "normal"))
        except Exception:
            record["blend_mode"] = "normal"
        record["clipping"] = bool(getattr(layer, "clipping", False))
        record["has_mask"] = getattr(layer, "mask", None) is not None
        record["has_vector_mask"] = getattr(layer, "vector_mask", None) is not None
        try:
            record["effects"] = [type(effect).__name__ for effect in getattr(layer, "effects", ()) or ()]
        except Exception:
            record["effects"] = []
        text = layer_text(layer)
        if text is not None:
            record["text"] = text
            styles = text_styles(layer)
            if styles:
                record["text_styles"] = styles
                record["font_family"] = styles[0].get("font_family", "")
                record["font_size"] = styles[0].get("font_size")
                record["font_weight"] = styles[0].get("font_weight", 400)
                record["font_style"] = styles[0].get("font_style", "normal")
                record["letter_spacing"] = styles[0].get("letter_spacing", 0)
                record["text_color"] = styles[0].get("color")
        try:
            image, render_mode, render_warning = render_layer(layer)
            record["render_mode"] = render_mode
            record["rendered_opacity"] = render_mode == "composite"
            if render_warning:
                record["render_warning"] = render_warning
            image.save(asset_path, "PNG", optimize=True)
        except Exception as exc:
            record.pop("asset", None)
            errors.append({"name": name, "kind": kind, "bounds": bounds, "reason": str(exc)})
            continue
        layers.append(record)
        order += 1

    try:
        psd.composite().convert("RGBA").save(output / "preview.png", "PNG", optimize=True)
    except Exception as exc:
        errors.append({"name": "__composite__", "reason": str(exc)})

    manifest = {
        "source": str(source),
        "canvas": {"width": width, "height": height},
        "layer_count": len(layers),
        "text_layer_count": sum(1 for layer in layers if "text" in layer),
        "text_mode": args.text_mode,
        "layers": layers,
        "errors": errors,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_h5(output, width, height, layers, args.text_mode)
    print(json.dumps({"canvas": [width, height], "exported_layers": len(layers), "text_layers": manifest["text_layer_count"], "errors": len(errors), "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

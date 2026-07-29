#!/usr/bin/env python3
"""Export visible PSD leaf layers and generate a responsive asset-based H5 render."""

from __future__ import annotations

import argparse
from html import escape
import json
import math
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
    parser.add_argument("--allow-render-fallback", action="store_true", help="Allow effect-bearing layers to fall back to topil when composite rendering fails")
    parser.add_argument("--force", action="store_true", help="Allow overwriting generated files in an existing output directory")
    return parser.parse_args()


def load_dependencies(require_composite: bool = True):
    try:
        from PIL import Image  # noqa: F401
        from psd_tools import PSDImage
    except ImportError as exc:
        fail("missing dependencies; run: python3 -m pip install psd-tools Pillow")
    if require_composite:
        missing = []
        for name in ("scipy", "aggdraw", "skimage"):
            try:
                __import__(name)
            except ImportError:
                missing.append(name)
        if missing:
            fail(
                "missing PSD composite dependencies: "
                + ", ".join(missing)
                + "; install with: python3 -m pip install 'psd-tools[composite]'"
            )
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


def effect_padding(layer: Any) -> int:
    """Estimate the outward extent needed for effects that can exceed layer.bbox."""
    maximum = 0.0
    try:
        for effect in getattr(layer, "effects", ()) or ():
            name = type(effect).__name__
            size = float(getattr(effect, "size", 0) or 0)
            distance = float(getattr(effect, "distance", 0) or 0)
            angle = math.radians(float(getattr(effect, "angle", 90) or 90))
            if name in ("DropShadow", "OuterGlow", "Shadow"):
                spread = size * 0.5 + 2.0
                maximum = max(maximum, spread + max(abs(distance * math.cos(angle)), abs(distance * math.sin(angle))))
    except Exception:
        return 0
    return int(math.ceil(maximum))


def clamp_bounds(bounds: list[int], canvas_size: tuple[int, int]) -> list[int]:
    width, height = canvas_size
    return [
        max(0, bounds[0]),
        max(0, bounds[1]),
        min(width, bounds[2]),
        min(height, bounds[3]),
    ]


def effect_context_bounds(bounds: list[int], padding: int, canvas_size: tuple[int, int]) -> list[int]:
    return clamp_bounds(
        [bounds[0] - padding, bounds[1] - padding, bounds[2] + padding, bounds[3] + padding],
        canvas_size,
    )


def walk_layers(node: Any, parent_visible: bool = True, path: tuple[str, ...] = ()) -> Iterable[tuple[Any, bool, tuple[str, ...]]]:
    for child in node:
        current_path = path + (str(getattr(child, "name", "layer")),)
        visible = parent_visible and bool(getattr(child, "visible", True))
        yield child, visible, current_path
        # A group with its own Photoshop effect is an explicit raster boundary;
        # keep it as one effect asset. Ordinary groups remain structural.
        if getattr(child, "kind", None) == "group" and not has_effects(child):
            yield from walk_layers(child, visible, current_path)


def render_layer(
    layer: Any,
    psd: Any,
    canvas_size: tuple[int, int],
    context_image: Any = None,
    allow_render_fallback: bool = False,
):
    composite_error = None
    try:
        bounds = as_bounds(getattr(layer, "bbox", None))
        padding = effect_padding(layer)
        if padding and bounds and context_image is not None:
            context_bounds = effect_context_bounds(bounds, padding, canvas_size)
            original_bounds = clamp_bounds(bounds, canvas_size)
            image = context_image.crop(tuple(context_bounds)).convert("RGBA")
            isolated = layer.composite(viewport=tuple(original_bounds))
            if isolated is not None:
                isolated = isolated.convert("RGBA")
                offset = (original_bounds[0] - context_bounds[0], original_bounds[1] - context_bounds[1])
                image.paste(isolated, offset, isolated)
            return image, "composite-context", composite_error, context_bounds
        image = layer.composite()
        if image is not None:
            return image.convert("RGBA"), "composite", composite_error, bounds
    except Exception as exc:
        composite_error = str(exc)
        if has_effects(layer) and not allow_render_fallback:
            raise RuntimeError(f"effect layer composite rendering failed: {composite_error}") from exc
    image = layer.topil()
    if image is None:
        raise RuntimeError("layer renderer returned no image")
    return image.convert("RGBA"), "topil-fallback", composite_error, as_bounds(getattr(layer, "bbox", None))


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

    PSDImage = load_dependencies(require_composite=not args.allow_render_fallback)
    try:
        psd = PSDImage.open(source)
    except Exception as exc:
        fail(f"could not open PSD: {exc}")

    width, height = map(int, psd.size)
    context_image = None
    group_effects = [
        {"name": str(getattr(layer, "name", "layer")), "path": list(path), "effects": [type(effect).__name__ for effect in getattr(layer, "effects", ()) or ()]}
        for layer, visible, path in walk_layers(psd)
        if visible and getattr(layer, "kind", None) == "group" and has_effects(layer)
    ]
    errors: list[dict[str, Any]] = []
    if any(effect_padding(layer) > 0 for layer, visible, _ in walk_layers(psd) if visible and getattr(layer, "kind", None) != "group"):
        try:
            context_image = psd.composite().convert("RGBA")
        except Exception as exc:
            errors.append({"name": "__composite_context__", "reason": str(exc), "fatal": True})
    layers: list[dict[str, Any]] = []
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
            "asset_scope": "group-effect" if kind == "group" else "leaf",
        }
        if kind == "group":
            record["flatten_reason"] = "group-level-effect"
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
        record["effect_padding"] = effect_padding(layer)
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
            image, render_mode, render_warning, rendered_bounds = render_layer(
                layer,
                psd,
                (width, height),
                context_image=context_image,
                allow_render_fallback=args.allow_render_fallback,
            )
            if rendered_bounds:
                record["bounds"] = rendered_bounds
            record["render_mode"] = render_mode
            record["rendered_opacity"] = render_mode in ("composite", "composite-context")
            if render_warning:
                record["render_warning"] = render_warning
            if render_mode == "topil-fallback" and has_effects(layer):
                record["effect_fallback"] = True
            image.save(asset_path, "PNG", optimize=True)
        except Exception as exc:
            record.pop("asset", None)
            errors.append({"name": name, "kind": kind, "bounds": bounds, "reason": str(exc), "fatal": has_effects(layer) and not args.allow_render_fallback})
            continue
        layers.append(record)
        order += 1

    try:
        preview_image = context_image if context_image is not None else psd.composite().convert("RGBA")
        preview_image.save(output / "preview.png", "PNG", optimize=True)
    except Exception as exc:
        errors.append({"name": "__composite__", "reason": str(exc)})

    manifest = {
        "source": str(source),
        "canvas": {"width": width, "height": height},
        "layer_count": len(layers),
        "text_layer_count": sum(1 for layer in layers if "text" in layer),
        "text_mode": args.text_mode,
        "asset_policy": "visible-leaf-plus-group-effect-boundaries",
        "composite_dependencies": not args.allow_render_fallback,
        "effect_layer_count": sum(1 for layer in layers if layer.get("effects")),
        "effect_fallback_count": sum(1 for layer in layers if layer.get("effect_fallback")),
        "group_effect_count": len(group_effects),
        "group_effects": group_effects,
        "layers": layers,
        "errors": errors,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_h5(output, width, height, layers, args.text_mode)
    print(json.dumps({"canvas": [width, height], "exported_layers": len(layers), "text_layers": manifest["text_layer_count"], "errors": len(errors), "effect_fallbacks": manifest["effect_fallback_count"], "output": str(output)}, ensure_ascii=False))
    if any(error.get("fatal") for error in errors):
        raise SystemExit(3)


if __name__ == "__main__":
    main()

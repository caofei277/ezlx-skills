#!/usr/bin/env python3
"""Validate the asset and effect-rendering quality produced by export_psd.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_output.py OUTPUT_DIR", file=sys.stderr)
        return 2
    output = Path(sys.argv[1]).expanduser().resolve()
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        print(f"missing {manifest_path}", file=sys.stderr)
        return 1
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    if data.get("asset_policy") not in ("visible-leaf-only", "visible-leaf-plus-group-effect-boundaries"):
        failures.append("manifest asset_policy is missing or does not enforce PSD layer boundaries")
    canvas = data.get("canvas", {})
    if not canvas.get("width") or not canvas.get("height"):
        failures.append("manifest canvas is missing width/height")
    for layer in data.get("layers", []):
        asset = layer.get("asset")
        bounds = layer.get("bounds")
        if not asset or not (output / asset).is_file():
            failures.append(f"missing asset for layer {layer.get('name')!r}: {asset}")
        if not isinstance(bounds, list) or len(bounds) != 4:
            failures.append(f"invalid bounds for layer {layer.get('name')!r}")
    html_files = [path for path in output.glob("*.html") if path.is_file()]
    if not html_files:
        failures.append("missing generated HTML preview (expected a page-named .html file)")
    for filename in ("styles.css", "preview.png"):
        if not (output / filename).is_file():
            failures.append(f"missing generated file: {filename}")
    errors = data.get("errors", []) or []
    if errors:
        fatal_errors = [error for error in errors if error.get("fatal")]
        if fatal_errors:
            failures.append(f"{len(fatal_errors)} fatal layer/composite errors are recorded in manifest.json")
        else:
            print(f"warning: {len(errors)} non-fatal layer/composite errors are recorded in manifest.json")
    effect_fallbacks = int(data.get("effect_fallback_count", 0) or 0)
    if effect_fallbacks:
        failures.append(f"{effect_fallbacks} effect-bearing layers used topil fallback; install psd-tools[composite]")
    for layer in data.get("layers", []):
        if layer.get("kind") == "group":
            if not layer.get("effects") or layer.get("asset_scope") != "group-effect" or layer.get("flatten_reason") != "group-level-effect":
                failures.append(f"group layer {layer.get('name')!r} was flattened without an explicit group-level effect boundary")
        if layer.get("effects") and layer.get("render_mode") not in ("composite", "composite-context"):
            failures.append(f"effect layer {layer.get('name')!r} was not rendered with composite support")
    if data.get("group_effect_count"):
        print(f"warning: {data['group_effect_count']} explicit group-level effect boundary asset(s) are recorded")
    if failures:
        for failure in failures:
            print(f"error: {failure}", file=sys.stderr)
        return 1
    print(f"valid: {len(data.get('layers', []))} exported layers, canvas {canvas['width']}x{canvas['height']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

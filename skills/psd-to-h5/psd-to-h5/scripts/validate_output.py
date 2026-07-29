#!/usr/bin/env python3
"""Validate the asset and manifest output produced by export_psd.py."""

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
    for filename in ("index.html", "styles.css", "preview.png"):
        if not (output / filename).is_file():
            failures.append(f"missing generated file: {filename}")
    if data.get("errors"):
        print(f"warning: {len(data['errors'])} layer/composite errors are recorded in manifest.json")
    if failures:
        for failure in failures:
            print(f"error: {failure}", file=sys.stderr)
        return 1
    print(f"valid: {len(data.get('layers', []))} exported layers, canvas {canvas['width']}x{canvas['height']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

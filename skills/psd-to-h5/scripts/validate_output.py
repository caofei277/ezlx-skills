#!/usr/bin/env python3
"""Validate the asset and effect-rendering quality produced by export_psd.py.

Supports both single-PSD export (a root manifest.json) and flow builds (a
flow-build.json whose states each carry their own manifest.json under an
asset directory), so validate_output.py can verify every exported screen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def check_manifest(base_dir: Path, manifest: dict, tag: str) -> list[str]:
    failures: list[str] = []
    if manifest.get("asset_policy") not in ("visible-leaf-only", "visible-leaf-plus-group-effect-boundaries"):
        failures.append(f"[{tag}] manifest asset_policy is missing or does not enforce PSD layer boundaries")
    canvas = manifest.get("canvas", {})
    if not canvas.get("width") or not canvas.get("height"):
        failures.append(f"[{tag}] manifest canvas is missing width/height")
    for layer in manifest.get("layers", []):
        asset = layer.get("asset")
        bounds = layer.get("bounds")
        if not asset or not (base_dir / asset).is_file():
            failures.append(f"[{tag}] missing asset for layer {layer.get('name')!r}: {asset}")
        if not isinstance(bounds, list) or len(bounds) != 4:
            failures.append(f"[{tag}] invalid bounds for layer {layer.get('name')!r}")
    errors = manifest.get("errors", []) or []
    if errors:
        fatal_errors = [error for error in errors if error.get("fatal")]
        if fatal_errors:
            failures.append(f"[{tag}] {len(fatal_errors)} fatal layer/composite errors are recorded in manifest.json")
        else:
            print(f"warning: [{tag}] {len(errors)} non-fatal layer/composite errors are recorded in manifest.json")
    effect_fallbacks = int(manifest.get("effect_fallback_count", 0) or 0)
    if effect_fallbacks:
        failures.append(f"[{tag}] {effect_fallbacks} effect-bearing layers used topil fallback; install psd-tools[composite]")
    for layer in manifest.get("layers", []):
        if layer.get("kind") == "group":
            if not layer.get("effects") or layer.get("asset_scope") != "group-effect" or layer.get("flatten_reason") != "group-level-effect":
                failures.append(f"[{tag}] group layer {layer.get('name')!r} was flattened without an explicit group-level effect boundary")
        if layer.get("effects") and layer.get("render_mode") not in ("composite", "composite-context"):
            failures.append(f"[{tag}] effect layer {layer.get('name')!r} was not rendered with composite support")
    if manifest.get("group_effect_count"):
        print(f"warning: [{tag}] {manifest['group_effect_count']} explicit group-level effect boundary asset(s) are recorded")
    return failures


def safe_output_path(output: Path, relative: str, tag: str, failures: list[str]) -> Path | None:
    """Resolve a generated relative path without allowing output escape."""
    candidate = Path(relative)
    if candidate.is_absolute():
        failures.append(f"[{tag}] generated path must be relative: {relative}")
        return None
    resolved = (output / candidate).resolve()
    try:
        resolved.relative_to(output)
    except ValueError:
        failures.append(f"[{tag}] generated path escapes output directory: {relative}")
        return None
    return resolved


def check_flow_pages(output: Path, flow: dict, failures: list[str]) -> None:
    pages = flow.get("pages")
    if not isinstance(pages, dict) or not pages:
        failures.append("flow-build.json has no generated page records")
        return
    for screen_id, page in pages.items():
        tag = f"{screen_id}:page"
        if not isinstance(page, dict):
            failures.append(f"[{tag}] page record is not an object")
            continue
        html_name = page.get("html")
        asset_dir = page.get("asset_dir")
        if not isinstance(html_name, str) or not html_name:
            failures.append(f"[{tag}] page HTML path is missing")
        else:
            html_path = safe_output_path(output, html_name, tag, failures)
            if html_path and not html_path.is_file():
                failures.append(f"[{tag}] missing page HTML: {html_name}")
        if not isinstance(asset_dir, str) or not asset_dir:
            failures.append(f"[{tag}] page asset directory is missing")
            continue
        page_dir = safe_output_path(output, asset_dir, tag, failures)
        if not page_dir:
            continue
        for filename in ("styles.css", "app.js", "flow-runtime.js"):
            if not (page_dir / filename).is_file():
                failures.append(f"[{tag}] missing generated page file: {asset_dir}/{filename}")
    initial_html = flow.get("initial_html")
    if isinstance(initial_html, str):
        initial_path = safe_output_path(output, initial_html, "initial", failures)
        if initial_path and not initial_path.is_file():
            failures.append(f"[initial] missing initial HTML: {initial_html}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_output.py OUTPUT_DIR", file=sys.stderr)
        return 2
    output = Path(sys.argv[1]).expanduser().resolve()
    failures: list[str] = []
    checked = 0

    manifest_path = output / "manifest.json"
    if manifest_path.is_file():
        checked += 1
        failures.extend(check_manifest(output, json.loads(manifest_path.read_text(encoding="utf-8")), "root"))
        html_files = [path for path in output.glob("*.html") if path.is_file()]
        if not html_files:
            failures.append("missing generated HTML preview (expected a page-named .html file)")
        for filename in ("styles.css", "preview.png"):
            if not (output / filename).is_file():
                failures.append(f"missing generated file: {filename}")
    else:
        flow_path = output / "flow-build.json"
        if not flow_path.is_file():
            print(f"missing {manifest_path} or {flow_path}", file=sys.stderr)
            return 1
        flow = json.loads(flow_path.read_text(encoding="utf-8"))
        check_flow_pages(output, flow, failures)
        for state_key, state in flow.get("states", {}).items():
            for layer in state.get("layers", []):
                asset = layer.get("asset")
                asset_path = safe_output_path(output, asset, state_key, failures) if isinstance(asset, str) and asset else None
                if not asset_path or not asset_path.is_file():
                    failures.append(f"[{state_key}] missing asset for layer {layer.get('name')!r}: {asset}")
        seen = set()
        for state_key, state in flow.get("states", {}).items():
            manifest_relative = state.get("manifest")
            state_manifest = None
            if isinstance(manifest_relative, str) and manifest_relative:
                state_manifest = safe_output_path(output, manifest_relative, state_key, failures)
            else:
                # Compatibility with flow-build files created before explicit
                # manifest paths were recorded.
                layer = next((l for l in state.get("layers", []) if l.get("asset")), None)
                if layer:
                    asset_path = safe_output_path(output, layer["asset"], state_key, failures)
                    state_manifest = asset_path.parent.parent / "manifest.json" if asset_path else None
                else:
                    failures.append(f"[{state_key}] state manifest path is missing")
                    continue
            if not state_manifest:
                continue
            key = state_manifest.as_posix()
            if key in seen:
                continue
            seen.add(key)
            if not state_manifest.is_file():
                failures.append(f"[{state_key}] missing state manifest: {state_manifest}")
                continue
            checked += 1
            try:
                state_data = json.loads(state_manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"[{state_key}] cannot read state manifest {state_manifest}: {exc}")
                continue
            failures.extend(check_manifest(state_manifest.parent, state_data, state_key))
        if not checked:
            failures.append("flow-build.json has no state manifests to validate")

    if failures:
        for failure in failures:
            print(f"error: {failure}", file=sys.stderr)
        return 1
    print(f"valid: {checked} manifest(s), no fatal export or effect fallback errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read font requirements from PSD text layers without consulting system fonts."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable


def load_psd_image():
    try:
        from psd_tools import PSDImage
    except ImportError as exc:
        raise RuntimeError("missing dependencies; run: python3 -m pip install psd-tools Pillow") from exc
    return PSDImage


def walk_layers(node: Any) -> Iterable[Any]:
    for child in node:
        yield child
        if getattr(child, "kind", None) == "group":
            yield from walk_layers(child)


def layer_font_names(layer: Any) -> set[str]:
    if getattr(layer, "kind", None) != "type":
        return set()
    try:
        resources = getattr(layer, "resource_dict", {}) or {}
        font_set = resources.get("FontSet", []) or []
        engine = getattr(layer, "engine_dict", {}) or {}
        runs = ((engine.get("StyleRun") or {}).get("RunArray") or [])
        names: set[str] = set()
        for run in runs:
            data = ((run.get("StyleSheet") or {}).get("StyleSheetData") or {})
            raw_index = data.get("Font")
            index = int(raw_index) if raw_index is not None else -1
            if 0 <= index < len(font_set):
                name = str(font_set[index].get("Name", "")).strip().strip("'\"")
                if name:
                    names.add(name)
        return names
    except Exception:
        return set()


def _display_path(path: Path, base_dir: Path | None) -> str:
    if base_dir is not None:
        try:
            return path.relative_to(base_dir).as_posix()
        except ValueError:
            pass
    return str(path)


def scan_psd_paths(paths: Iterable[Path], base_dir: Path | None = None) -> dict[str, Any]:
    """Return exact font names and PSD sources, including hidden text layers."""
    required: dict[str, dict[str, Any]] = {}
    psds: list[str] = []
    errors: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    PSDImage = load_psd_image()
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        if path in seen_paths:
            continue
        seen_paths.add(path)
        display_path = _display_path(path, base_dir)
        psds.append(display_path)
        if not path.is_file():
            errors.append({"psd": display_path, "reason": "file does not exist"})
            continue
        try:
            psd = PSDImage.open(path)
            names: set[str] = set()
            for layer in walk_layers(psd):
                names.update(layer_font_names(layer))
            for name in sorted(names):
                entry = required.setdefault(name, {"name": name, "psds": []})
                if display_path not in entry["psds"]:
                    entry["psds"].append(display_path)
        except Exception as exc:
            errors.append({"psd": display_path, "reason": str(exc)})
    return {
        "psds": sorted(psds),
        "required": [required[name] for name in sorted(required)],
        "errors": errors,
    }


def flow_psd_paths(flow: dict[str, Any], base_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for screen in flow.get("screens", []):
        if not isinstance(screen, dict):
            continue
        for key in ("default",):
            value = screen.get(key)
            if isinstance(value, str):
                paths.append(base_dir / value)
        for entry_name in ("overlays", "states"):
            for entry in screen.get(entry_name, []) or []:
                if isinstance(entry, dict) and isinstance(entry.get("psd"), str):
                    paths.append(base_dir / entry["psd"])
    return paths


def suggested_mapping(name: str) -> dict[str, str]:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.") or "font"
    return {
        "file": f"fonts/{safe_name}.ttf",
        "format": "ttf",
        "family": name,
    }


def audit_project_fonts(required: list[dict[str, Any]], project: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    configured = project.get("fonts", {}) if isinstance(project, dict) else {}
    configured = configured if isinstance(configured, dict) else {}
    missing_mapping: list[dict[str, Any]] = []
    missing_source: list[dict[str, Any]] = []
    for item in required:
        name = item["name"]
        mapping = configured.get(name)
        if not isinstance(mapping, dict):
            missing_mapping.append({**item, "suggested": suggested_mapping(name)})
            continue
        source_value = mapping.get("file")
        source = (base_dir / source_value).resolve() if isinstance(source_value, str) else None
        if source is None or not source.is_file():
            missing_source.append({
                **item,
                "file": source_value,
                "suggested": suggested_mapping(name),
            })
    return {
        "required": required,
        "missing_mapping": missing_mapping,
        "missing_source": missing_source,
        "ready": not missing_mapping and not missing_source,
    }

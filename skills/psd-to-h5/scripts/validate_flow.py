#!/usr/bin/env python3
"""Validate a PSD-to-H5 flow.json and populate required PSD font mappings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from font_audit import audit_project_fonts, flow_psd_paths, scan_psd_paths, suggested_mapping


def issue(message: str, errors: list[str], warnings: list[str], strict: bool = False) -> None:
    (errors if strict else warnings).append(message)


def state_key(screen_id: str, state_id: str) -> str:
    return f"{screen_id}:{state_id}"


def normalize_target(value: str) -> str:
    if ":" in value:
        return value
    if "#" in value:
        screen_id, state_id = value.split("#", 1)
        return state_key(screen_id, state_id)
    return state_key(value, "default")


def transition_target(transition: dict[str, Any], key: str) -> str | None:
    target = transition.get(key)
    if not isinstance(target, str):
        return None
    overlay = transition.get("overlay") if key == "to" else None
    return state_key(target, overlay) if isinstance(overlay, str) and overlay else normalize_target(target)


def validate_visual_entries(
    screen_id: str,
    entries: Any,
    entry_name: str,
    base_dir: Path,
    known_states: set[str],
    seen_states: set[str],
    errors: list[str],
    warnings: list[str],
    strict: bool,
    allow_mode: bool = False,
) -> None:
    if not isinstance(entries, list):
        errors.append(f"{screen_id}.{entry_name} must be an array")
        return
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(f"{screen_id}.{entry_name} entries must be objects")
            continue
        entry_id = entry.get("id")
        psd_path = entry.get("psd")
        if not isinstance(entry_id, str) or not entry_id:
            errors.append(f"{screen_id} {entry_name[:-1]} needs a non-empty id")
            continue
        if entry_id in seen_states:
            errors.append(f"duplicate state id: {screen_id}:{entry_id}")
        seen_states.add(entry_id)
        known_states.add(state_key(screen_id, entry_id))
        if allow_mode and entry.get("mode", "overlay") not in ("overlay", "route", "page"):
            errors.append(f"invalid mode for {screen_id}:{entry_id}")
        if not isinstance(psd_path, str):
            errors.append(f"{screen_id}:{entry_id}.psd must be a PSD path")
        elif not (base_dir / psd_path).resolve().is_file():
            issue(f"missing PSD: {psd_path}", errors, warnings, strict)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flow", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat missing PSD files as errors")
    parser.add_argument("--no-update-fonts", action="store_true", help="Do not add newly discovered PSD font mappings to flow.json")
    args = parser.parse_args()
    flow_path = args.flow.expanduser().resolve()
    try:
        data: dict[str, Any] = json.loads(flow_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"error: cannot read JSON: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    if data.get("version") != 1:
        errors.append("version must be 1")
    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
        project = {}
    for key in ("designWidth", "designHeight"):
        if not isinstance(project.get(key), int) or project[key] <= 0:
            errors.append(f"project.{key} must be a positive integer")

    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        errors.append("screens must be a non-empty array")
        screens = []
    known_states: set[str] = set()
    seen_screens: set[str] = set()
    base_dir = flow_path.parent

    for screen in screens:
        if not isinstance(screen, dict):
            errors.append("each screen must be an object")
            continue
        screen_id = screen.get("id")
        if not isinstance(screen_id, str) or not screen_id:
            errors.append("each screen needs a non-empty id")
            continue
        if screen_id in seen_screens:
            errors.append(f"duplicate screen id: {screen_id}")
        seen_screens.add(screen_id)
        default_psd = screen.get("default")
        if not isinstance(default_psd, str):
            errors.append(f"{screen_id}.default must be a PSD path")
        else:
            path = (base_dir / default_psd).resolve()
            if not path.is_file():
                issue(f"missing PSD: {default_psd}", errors, warnings, args.strict)
        known_states.add(state_key(screen_id, "default"))
        seen_states: set[str] = {"default"}
        validate_visual_entries(screen_id, screen.get("overlays", []), "overlays", base_dir, known_states, seen_states, errors, warnings, args.strict)
        if "states" in screen:
            warnings.append(f"{screen_id}.states is deprecated; use overlays without a mode field")
            validate_visual_entries(screen_id, screen.get("states"), "states", base_dir, known_states, seen_states, errors, warnings, args.strict, allow_mode=True)
        elements = screen.get("elements", [])
        if not isinstance(elements, list):
            errors.append(f"{screen_id}.elements must be an array")
        else:
            element_ids: set[str] = set()
            for element in elements:
                if not isinstance(element, dict) or not isinstance(element.get("id"), str):
                    errors.append(f"{screen_id} elements need string ids")
                elif element["id"] in element_ids:
                    errors.append(f"duplicate element id: {screen_id}:{element['id']}")
                else:
                    element_ids.add(element["id"])

    transitions = data.get("transitions", [])
    if not isinstance(transitions, list):
        errors.append("transitions must be an array")
        transitions = []
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            errors.append(f"transition {index} must be an object")
            continue
        for key in ("from", "trigger", "to"):
            if not isinstance(transition.get(key), str) or not transition[key]:
                errors.append(f"transition {index} needs {key}")
        overlay = transition.get("overlay")
        if overlay is not None and (not isinstance(overlay, str) or not overlay):
            errors.append(f"transition {index}.overlay must be a non-empty string")
        for key in ("from", "to"):
            normalized = transition_target(transition, key)
            target = transition.get(key)
            if normalized and normalized not in known_states:
                errors.append(f"transition {index} references unknown state: {target}")

    # PSD text layers define required project inputs. System-installed fonts do
    # not count; every discovered family needs an explicit fonts/ mapping.
    psd_paths = flow_psd_paths(data, base_dir)
    existing_psd_paths = [path for path in psd_paths if path.is_file()]
    if existing_psd_paths:
        try:
            font_scan = scan_psd_paths(existing_psd_paths, base_dir)
            configured = project.setdefault("fonts", {})
            added_fonts: list[str] = []
            if isinstance(configured, dict) and not args.no_update_fonts:
                for item in font_scan["required"]:
                    name = item["name"]
                    if name not in configured:
                        configured[name] = suggested_mapping(name)
                        added_fonts.append(name)
                if added_fonts:
                    data["_fontAudit"] = {
                        "说明": "由 validate_flow.py 根据 PSD 文本图层自动补齐；用户必须把对应 TTF/OTF 放入 fonts/ 并确认 project.fonts 路径。",
                        "required": font_scan["required"],
                        "missingMapping": [],
                        "missingSource": [],
                        "scanErrors": font_scan["errors"],
                    }
                    flow_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    print(f"font mappings added to flow.json: {', '.join(added_fonts)}")
            font_audit = audit_project_fonts(font_scan["required"], project, base_dir)
            for item in font_scan["errors"]:
                issue(f"font scan failed for {item['psd']}: {item['reason']}", errors, warnings, args.strict)
            for item in font_audit["missing_mapping"]:
                issue(
                    f"missing font mapping: {item['name']} (add project.fonts.{item['name']})",
                    errors,
                    warnings,
                    args.strict,
                )
            for item in font_audit["missing_source"]:
                issue(
                    f"missing font source: {item['name']} -> {item.get('file') or '(not configured)'}",
                    errors,
                    warnings,
                    args.strict,
                )
        except RuntimeError as exc:
            issue(f"font audit unavailable: {exc}", errors, warnings, args.strict)

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"valid: {len(seen_screens)} screen(s), {len(known_states)} state(s), {len(transitions)} transition(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

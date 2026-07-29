#!/usr/bin/env python3
"""List PSD font requirements and optionally add missing mappings to flow.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from font_audit import audit_project_fonts, flow_psd_paths, scan_psd_paths, suggested_mapping


def load_flow(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"cannot read flow.json: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("flow.json must contain an object")
    return value


def print_report(flow_path: Path, scan: dict[str, Any], audit: dict[str, Any]) -> None:
    print(f"font audit: {flow_path}")
    if scan["psds"]:
        print("PSD sources:")
        for path in scan["psds"]:
            print(f"  - {path}")
    if not scan["required"]:
        print("required fonts: none found")
    else:
        print("required fonts:")
        for item in scan["required"]:
            print(f"  - {item['name']} (from: {', '.join(item['psds'])})")
    for item in audit["missing_mapping"]:
        suggested = item["suggested"]
        print(f"MISSING FONT MAPPING: {item['name']}")
        print(f"  add project.fonts.{item['name']}: {json.dumps(suggested, ensure_ascii=False)}")
    for item in audit["missing_source"]:
        print(f"MISSING FONT FILE: {item['name']} -> {item.get('file') or '(file path not configured)'}")
        print(f"  put the TTF/OTF in fonts/ and set project.fonts.{item['name']}.file")
        print(f"  suggested path: {item['suggested']['file']}")
    for item in scan["errors"]:
        print(f"PSD FONT SCAN ERROR: {item['psd']} -> {item['reason']}", file=sys.stderr)
    if audit["ready"] and scan["required"]:
        print("font inputs: ready; every PSD font has a configured source file")
    elif scan["required"]:
        print("font inputs: incomplete; provide every listed source file before semantic text rendering")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flow", type=Path)
    parser.add_argument("--update", action="store_true", help="Add a suggested project.fonts mapping for each newly discovered font")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any font mapping or source file is missing")
    args = parser.parse_args()
    flow_path = args.flow.expanduser().resolve()
    try:
        data = load_flow(flow_path)
        base_dir = flow_path.parent
        scan = scan_psd_paths(flow_psd_paths(data, base_dir), base_dir)
        project = data.setdefault("project", {})
        if not isinstance(project, dict):
            raise RuntimeError("project must be an object")
        configured = project.setdefault("fonts", {})
        if not isinstance(configured, dict):
            raise RuntimeError("project.fonts must be an object")
        if args.update:
            for item in scan["required"]:
                configured.setdefault(item["name"], suggested_mapping(item["name"]))
            audit = audit_project_fonts(scan["required"], project, base_dir)
            data["_fontAudit"] = {
                "说明": "由 analyze_fonts.py 根据 PSD 文本图层生成；字体文件补齐后重新运行构建审计。",
                "required": scan["required"],
                "missingMapping": audit["missing_mapping"],
                "missingSource": audit["missing_source"],
            }
            flow_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        audit = audit_project_fonts(scan["required"], project, base_dir)
        print_report(flow_path, scan, audit)
        return 1 if args.strict and (scan["errors"] or not audit["ready"]) else 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

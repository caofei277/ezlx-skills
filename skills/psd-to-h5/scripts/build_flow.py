#!/usr/bin/env python3
"""Build all PSD screens/states in a flow.json and generate a small H5 runtime."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from font_audit import audit_project_fonts, flow_psd_paths, scan_psd_paths


def fail(message: str) -> None:
    print(f"[psd-to-h5] error: {message}", file=sys.stderr)
    raise SystemExit(2)


def normalize_key(value: str) -> str:
    if ":" in value:
        return value
    if "#" in value:
        screen_id, state_id = value.split("#", 1)
        return f"{screen_id}:{state_id}"
    return f"{value}:default"


def transition_target(transition: dict[str, Any], key: str) -> str:
    target = transition[key]
    if key == "to" and transition.get("overlay"):
        return f"{target}:{transition['overlay']}"
    return target


def layer_matches_exclusion(layer: dict[str, Any], exclusions: list[Any]) -> bool:
    """Match explicit layer names or PSD paths used to remove duplicate overlay bases."""
    path = layer.get("path", [])
    name = layer.get("name")
    for exclusion in exclusions:
        if isinstance(exclusion, str) and (name == exclusion or "/".join(path) == exclusion):
            return True
        if isinstance(exclusion, list) and path[: len(exclusion)] == exclusion:
            return True
    return False


def css_family_name(font_name: str) -> str:
    return "PSD_" + re.sub(r"[^A-Za-z0-9_-]+", "_", font_name).strip("_")


def collect_font_text(states: dict[str, Any]) -> tuple[set[str], str]:
    required: set[str] = set()
    text_parts: list[str] = []
    for state in states.values():
        for layer in state.get("layers", []):
            font_name = layer.get("font_family")
            if layer.get("text"):
                text_parts.append(str(layer["text"]))
            if font_name:
                required.add(str(font_name))
    return required, "".join(text_parts)


def subset_font(source: Path, destination: Path, text: str, flavor: str) -> None:
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError("missing font tools; install with: python3 -m pip install fonttools brotli") from exc
    options = subset.Options()
    options.flavor = flavor
    options.layout_features = ["*"]
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 16, 17]
    font = TTFont(str(source))
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(destination))


def build_fonts(flow_path: Path, output: Path, project: dict[str, Any], states: dict[str, Any]) -> dict[str, Any]:
    configured = project.get("fonts", {}) or {}
    required, text = collect_font_text(states)
    audit: dict[str, Any] = {
        "required": sorted(required),
        "missing": [],
        "unconfigured": [],
        "compression_errors": [],
        "generated": [],
    }
    fonts: dict[str, Any] = {}
    output_fonts = output / "fonts"
    output_fonts.mkdir(parents=True, exist_ok=True)
    for name in sorted(required):
        mapping = configured.get(name)
        if not isinstance(mapping, dict):
            audit["unconfigured"].append(name)
            continue
        source_value = mapping.get("file")
        source = (flow_path.parent / source_value).resolve() if isinstance(source_value, str) else None
        if source is None or not source.is_file():
            audit["missing"].append({"name": name, "file": source_value})
            continue
        css_family = str(mapping.get("cssFamily") or css_family_name(name))
        stem = css_family_name(name)
        woff2 = output_fonts / f"{stem}.woff2"
        woff = output_fonts / f"{stem}.woff"
        try:
            subset_font(source, woff2, text, "woff2")
            subset_font(source, woff, text, "woff")
        except Exception as exc:
            audit["compression_errors"].append({"name": name, "file": str(source), "reason": str(exc)})
            continue
        font_record = {
            "source_name": name,
            "family": css_family,
            "display_family": mapping.get("family", name),
            "weight": int(mapping.get("weight", 500 if "Medium" in name else 700 if "Bold" in name else 400)),
            "style": mapping.get("style", "italic" if "Italic" in name else "normal"),
            "woff2": (woff2.relative_to(output)).as_posix(),
            "woff": (woff.relative_to(output)).as_posix(),
        }
        fonts[name] = font_record
        audit["generated"].append(font_record)
    return {"fonts": fonts, "audit": audit, "text": text}


def load_flow(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot read flow.json: {exc}")
    if not isinstance(data, dict) or data.get("version") != 1:
        fail("flow.json must be an object with version=1")
    return data


def write_runtime(output: Path, runtime: dict[str, Any]) -> None:
    runtime_json = json.dumps(runtime, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (output / "flow-runtime.js").write_text(f"window.PSD_H5_FLOW = {runtime_json};\n", encoding="utf-8")
    (output / "app.js").write_text(
        """(() => {
  const runtime = window.PSD_H5_FLOW;
  const stage = document.querySelector('.flow-stage');
  const title = document.querySelector('[data-flow-title]');
  let current = runtime.initial;

  function cssPosition(bounds) {
    const [left, top, right, bottom] = bounds;
    return `--x:${left};--y:${top};--w:${right - left};--h:${bottom - top};`;
  }

  function render(stateKey) {
    const state = runtime.states[stateKey];
    if (!state) return;
    current = stateKey;
    stage.replaceChildren();
    stage.dataset.state = stateKey;
    const base = state.mode === 'overlay' ? runtime.states[state.base] : null;
    const layers = base ? [...base.layers, ...state.layers] : state.layers;
    layers.forEach((layer, index) => {
      const useText = runtime.textMode === 'semantic' && layer.text && layer.font_css_family;
      const node = document.createElement(useText ? 'span' : 'img');
      node.className = useText ? 'flow-text' : 'flow-layer';
      node.alt = layer.text || '';
      node.dataset.layer = layer.name;
      node.style.cssText = cssPosition(layer.bounds) + '--z:' + index + ';--opacity:' + (layer.rendered_opacity ? 1 : layer.opacity / 255) + ';';
      if (useText) {
        node.textContent = String(layer.text).replace(/\\r/g, '\\n');
        node.style.fontFamily = layer.font_css_family;
        node.style.fontSize = 'min(calc(' + (layer.font_size || 16) + ' * 100vw / ' + runtime.canvas.width + '), calc(' + (layer.font_size || 16) + 'px))';
        node.style.fontWeight = String(layer.font_weight || 400);
        node.style.fontStyle = layer.font_style || 'normal';
        node.style.letterSpacing = (layer.letter_spacing || 0) + 'em';
        node.style.color = layer.text_color || '#3d3026';
      } else {
        node.src = layer.asset;
      }
      stage.append(node);
    });
    for (const element of state.elements) {
      const button = document.createElement('button');
      button.className = 'flow-hotspot';
      button.type = 'button';
      button.ariaLabel = element.description || element.id;
      button.dataset.trigger = element.id;
      button.style.cssText = cssPosition(element.bounds);
      button.addEventListener('click', () => transition(element.id));
      stage.append(button);
    }
    title.textContent = state.title || stateKey;
  }

  function transition(trigger) {
    const match = runtime.transitions.find(item => item.from === current && item.trigger === trigger);
    if (match) {
      history.pushState({}, '', `#${encodeURIComponent(match.to)}`);
      render(match.to);
    }
  }

  const initial = location.hash ? decodeURIComponent(location.hash.slice(1)) : runtime.initial;
  render(runtime.states[initial] ? initial : runtime.initial);
  window.addEventListener('popstate', () => {
    const next = location.hash ? decodeURIComponent(location.hash.slice(1)) : runtime.initial;
    render(runtime.states[next] ? next : runtime.initial);
  });
})();
""",
        encoding="utf-8",
    )
    width = runtime["canvas"]["width"]
    height = runtime["canvas"]["height"]
    font_faces = []
    for font in runtime.get("fonts", {}).values():
        font_faces.append(
            "@font-face { "
            f'font-family: "{font["family"]}"; '
            f'src: url("./{font["woff2"]}") format("woff2"), url("./{font["woff"]}") format("woff"); '
            f'font-weight: {font["weight"]}; font-style: {font["style"]}; font-display: swap; '
            "}"
        )
    font_face_css = "\n".join(font_faces)
    (output / "styles.css").write_text(
        f"""{font_face_css}
:root {{ font-family: -apple-system, BlinkMacSystemFont, \"Helvetica Neue\", \"PingFang SC\", sans-serif; background:#f2f2f2; }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; min-height:100%; }}
body {{ min-width:320px; background:#f2f2f2; }}
.flow-preview {{ display:flex; justify-content:center; min-height:100vh; }}
.flow-stage {{ position:relative; width:min(100vw, {width}px); aspect-ratio:{width}/{height}; overflow:hidden; background:#fff; isolation:isolate; }}
.flow-layer {{ position:absolute; display:block; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:var(--z); opacity:var(--opacity); user-select:none; -webkit-user-drag:none; }}
.flow-text {{ position:absolute; display:block; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:var(--z); opacity:var(--opacity); overflow:hidden; line-height:1; white-space:pre-wrap; user-select:none; }}
.flow-hotspot {{ position:absolute; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:10000; border:0; background:transparent; cursor:pointer; }}
.flow-hotspot:focus-visible {{ outline:2px solid #c88735; outline-offset:-2px; border-radius:8px; }}
.sr-only {{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }}
@media (min-width:520px) {{ .flow-preview {{ padding:28px 0; }} .flow-stage {{ border-radius:12px; box-shadow:0 12px 40px rgba(34,24,14,.16); }} }}
""",
        encoding="utf-8",
    )
    (output / "index.html").write_text(
        """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>PSD to H5 Flow</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <main class="flow-preview" aria-label="PSD H5 flow preview">
      <span class="sr-only" data-flow-title aria-live="polite"></span>
      <div class="flow-stage"></div>
    </main>
    <script src="./flow-runtime.js"></script>
    <script src="./app.js"></script>
  </body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flow", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    flow_path = args.flow.expanduser().resolve()
    data = load_flow(flow_path)
    project = data.get("project", {})
    output = (flow_path.parent / project.get("outputDir", "output")).resolve()
    if output.exists() and any(output.iterdir()) and not args.force:
        fail(f"output is not empty: {output}; pass --force to regenerate")
    output.mkdir(parents=True, exist_ok=True)

    exporter = Path(__file__).with_name("export_psd.py")
    runtime: dict[str, Any] = {
        "canvas": {"width": int(project.get("designWidth", 750)), "height": int(project.get("designHeight", 1630))},
        "initial": "",
        "states": {},
        "transitions": [],
        "text_mode": "raster",
        "fonts": {},
        "font_audit": {},
    }
    state_specs: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for screen in data.get("screens", []):
        screen_id = screen["id"]
        state_specs.append((screen_id, "default", screen["default"], "page", screen))
        for overlay in screen.get("overlays", []):
            state_specs.append((screen_id, overlay["id"], overlay["psd"], "overlay", {"screen": screen, **overlay}))
        for state in screen.get("states", []):
            state_specs.append((screen_id, state["id"], state["psd"], state.get("mode", "overlay"), {"screen": screen, **state}))
    if not state_specs:
        fail("flow.json must contain at least one screen")
    runtime["initial"] = f"{state_specs[0][0]}:default"

    for screen_id, state_id, psd_rel, mode, spec in state_specs:
        source = (flow_path.parent / psd_rel).resolve()
        if not source.is_file():
            fail(f"missing PSD: {psd_rel}")
        state_dir = output / screen_id / state_id
        command = [sys.executable, str(exporter), str(source), str(state_dir)]
        if args.force:
            command.append("--force")
        subprocess.run(command, check=True)
        manifest = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))
        layer_by_name = {layer["name"]: layer for layer in manifest.get("layers", [])}
        elements: list[dict[str, Any]] = []
        for element in spec.get("elements", []):
            if not isinstance(element, dict) or not element.get("id"):
                continue
            bounds = element.get("bounds")
            if not bounds and element.get("layer") in layer_by_name:
                bounds = layer_by_name[element["layer"]].get("bounds")
            if not isinstance(bounds, list) or len(bounds) != 4:
                continue
            elements.append({"id": element["id"], "description": element.get("description", element["id"]), "bounds": bounds})
        key = f"{screen_id}:{state_id}"
        layers = []
        for layer in manifest.get("layers", []):
            if mode == "overlay" and layer_matches_exclusion(layer, spec.get("excludeLayers", [])):
                continue
            asset = layer.get("asset")
            if not asset:
                continue
            layers.append({**layer, "asset": (state_dir / asset).relative_to(output).as_posix()})
        state_record = {"title": spec.get("description", key), "mode": mode, "layers": layers, "elements": elements}
        if mode == "overlay":
            state_record["base"] = normalize_key(spec.get("base", screen_id))
        runtime["states"][key] = state_record

    font_result = build_fonts(flow_path, output, project, runtime["states"])
    runtime["fonts"] = font_result["fonts"]
    runtime["font_audit"] = font_result["audit"]
    try:
        all_psd_paths = [path for path in flow_psd_paths(data, flow_path.parent) if path.is_file()]
        font_scan = scan_psd_paths(all_psd_paths, flow_path.parent)
        source_audit = audit_project_fonts(font_scan["required"], project, flow_path.parent)
        runtime["font_audit"]["psd_required"] = font_scan["required"]
        runtime["font_audit"]["missing_mapping"] = source_audit["missing_mapping"]
        runtime["font_audit"]["missing_source"] = source_audit["missing_source"]
        runtime["font_audit"]["scan_errors"] = font_scan["errors"]
        runtime["font_audit"]["unconfigured"] = [item["name"] for item in source_audit["missing_mapping"]]
        runtime["font_audit"]["missing"] = source_audit["missing_source"]
    except RuntimeError as exc:
        runtime["font_audit"]["scan_errors"] = [{"reason": str(exc)}]
    requested_text_mode = project.get("textMode", "raster")
    can_use_semantic = requested_text_mode == "semantic" and not (
        font_result["audit"]["missing"]
        or font_result["audit"]["unconfigured"]
        or font_result["audit"]["compression_errors"]
    )
    runtime["text_mode"] = "semantic" if can_use_semantic else "raster"
    for state in runtime["states"].values():
        for layer in state["layers"]:
            font = runtime["fonts"].get(layer.get("font_family"))
            if font:
                layer["font_css_family"] = font["family"]

    for transition in data.get("transitions", []):
        if not all(isinstance(transition.get(key), str) for key in ("from", "trigger", "to")):
            continue
        runtime["transitions"].append({
            "from": normalize_key(transition["from"]),
            "trigger": transition["trigger"],
            "to": normalize_key(transition_target(transition, "to")),
        })

    (output / "font-audit.json").write_text(json.dumps(runtime["font_audit"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "flow-build.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_runtime(output, runtime)
    font_gaps = [item["name"] for item in runtime["font_audit"].get("missing_mapping", [])]
    font_gaps += [item["name"] for item in runtime["font_audit"].get("missing_source", [])]
    if font_gaps:
        print("[psd-to-h5] FONT INPUT REQUIRED: provide these PSD fonts in project.fonts and fonts/:", file=sys.stderr)
        for name in sorted(set(font_gaps)):
            print(f"  - {name}", file=sys.stderr)
    print(json.dumps({
        "output": str(output),
        "states": len(runtime["states"]),
        "transitions": len(runtime["transitions"]),
        "text_mode": runtime["text_mode"],
        "missing_fonts": sorted(set(font_gaps)),
        "missing_font_mappings": runtime["font_audit"].get("unconfigured", []),
        "font_compression_errors": runtime["font_audit"].get("compression_errors", []),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

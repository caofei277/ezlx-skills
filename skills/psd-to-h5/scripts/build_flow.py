#!/usr/bin/env python3
"""Build all PSD screens/states in a flow.json and generate a small H5 runtime."""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    print(f"[psd-to-h5] error: {message}", file=sys.stderr)
    raise SystemExit(2)


def normalize_key(value: str) -> str:
    return value if ":" in value else f"{value}:default"


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
    for (const layer of state.layers) {
      const image = document.createElement('img');
      image.className = 'flow-layer';
      image.src = layer.asset;
      image.alt = layer.text || '';
      image.dataset.layer = layer.name;
      image.style.cssText = `${cssPosition(layer.bounds)}--z:${layer.index};--opacity:${layer.opacity / 255};`;
      stage.append(image);
    }
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
    if (match) render(match.to);
  }

  render(current);
  window.addEventListener('popstate', () => render(location.hash.slice(1) || runtime.initial));
})();
""",
        encoding="utf-8",
    )
    width = runtime["canvas"]["width"]
    height = runtime["canvas"]["height"]
    (output / "styles.css").write_text(
        f""":root {{ font-family: -apple-system, BlinkMacSystemFont, \"Helvetica Neue\", \"PingFang SC\", sans-serif; background:#f2f2f2; }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; min-height:100%; }}
body {{ min-width:320px; background:#f2f2f2; }}
.flow-preview {{ display:flex; justify-content:center; min-height:100vh; }}
.flow-stage {{ position:relative; width:min(100vw, {width}px); aspect-ratio:{width}/{height}; overflow:hidden; background:#fff; isolation:isolate; }}
.flow-layer {{ position:absolute; display:block; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:var(--z); opacity:var(--opacity); user-select:none; -webkit-user-drag:none; }}
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
    }
    state_specs: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for screen in data.get("screens", []):
        screen_id = screen["id"]
        state_specs.append((screen_id, "default", screen["default"], "page", screen))
        for state in screen.get("states", []):
            state_specs.append((screen_id, state["id"], state["psd"], state.get("mode", "overlay"), {**screen, **state}))
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
            asset = layer.get("asset")
            if not asset:
                continue
            layers.append({**layer, "asset": (state_dir / asset).relative_to(output).as_posix()})
        runtime["states"][key] = {"title": spec.get("description", key), "mode": mode, "layers": layers, "elements": elements}

    for transition in data.get("transitions", []):
        if not all(isinstance(transition.get(key), str) for key in ("from", "trigger", "to")):
            continue
        runtime["transitions"].append({"from": normalize_key(transition["from"]), "trigger": transition["trigger"], "to": normalize_key(transition["to"])})

    (output / "flow-build.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_runtime(output, runtime)
    print(json.dumps({"output": str(output), "states": len(runtime["states"]), "transitions": len(runtime["transitions"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

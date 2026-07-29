#!/usr/bin/env python3
"""Build all PSD screens/states in a flow.json and generate a small H5 runtime."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from font_audit import audit_project_fonts, flow_psd_paths, scan_psd_paths, suggested_mapping
from validate_flow import validate_generated_contract


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


def page_file_stem(title: Any, used: set[str]) -> str:
    """Create a readable, deterministic HTML stem from a screen title."""
    raw = str(title or "页面").strip()
    stem = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", "-", raw)
    stem = re.sub(r"\s+", "-", stem)
    stem = re.sub(r"-{2,}", "-", stem).strip(" .-_") or "页面"
    if stem.lower() in {".", "..", "index"}:
        stem = f"{stem}-page"
    candidate = stem
    suffix = 2
    while candidate in used:
        candidate = f"{stem}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def page_file_map(screens: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Map screen IDs to isolated HTML and asset locations."""
    used: set[str] = {"fonts", "flow-build", "font-audit", "review"}
    result: dict[str, dict[str, str]] = {}
    for screen in screens:
        screen_id = screen["id"]
        title = screen.get("title") or screen_id
        stem = page_file_stem(title, used)
        result[screen_id] = {
            "title": str(title),
            "stem": stem,
            "html": f"{stem}.html",
            "asset_dir": f"{stem}.assets",
        }
    return result


def transition_target(transition: dict[str, Any], key: str) -> str:
    target = transition[key]
    if key == "to" and transition.get("overlay"):
        return f"{target}:{transition['overlay']}"
    return target


def transition_trigger_index(transitions: Any) -> dict[str, set[str]]:
    """Index declared triggers by normalized source state for element inference."""
    result: dict[str, set[str]] = {}
    if not isinstance(transitions, list):
        return result
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        source = transition.get("from")
        trigger = transition.get("trigger")
        if not isinstance(source, str) or not isinstance(trigger, str) or not source or not trigger:
            continue
        result.setdefault(normalize_key(source), set()).add(trigger)
    return result


def state_element_specs(
    screen: dict[str, Any],
    spec: dict[str, Any],
    mode: str,
    state_key: str,
    trigger_index: dict[str, set[str]],
) -> tuple[list[Any], str]:
    """Resolve state-owned elements without requiring users to duplicate page elements."""
    screen_elements = screen.get("elements", [])
    if not isinstance(screen_elements, list):
        screen_elements = []
    explicit = spec.get("elements")
    if mode != "overlay":
        return screen_elements, "screen"
    if isinstance(explicit, list) and explicit:
        return explicit, "overlay"
    triggers = trigger_index.get(state_key, set())
    inherited = [
        element for element in screen_elements
        if isinstance(element, dict) and element.get("id") in triggers
    ]
    return inherited, "screen-transition-inferred"


def layer_map(layers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {layer["name"]: layer for layer in layers if isinstance(layer, dict) and layer.get("name")}


def resolve_layout(project: dict[str, Any], width: int) -> dict[str, Any]:
    """Resolve one canvas scaling contract for mobile, universal, and PC targets."""
    platform = project.get("platform", "universal")
    if platform not in ("universal", "mobile", "pc"):
        fail("project.platform must be universal, mobile, or pc")
    raw = project.get("layout", {})
    if not isinstance(raw, dict):
        fail("project.layout must be an object")
    mode = raw.get("mode", "canvas")
    scale = raw.get("scale", "down-only")
    if mode != "canvas":
        fail("project.layout.mode currently supports only canvas")
    if scale != "down-only":
        fail("project.layout.scale currently supports only down-only")
    try:
        max_stage_width = int(raw.get("maxStageWidth", width))
        min_viewport_width = int(raw.get("minViewportWidth", 1024 if platform == "pc" else 320))
    except (TypeError, ValueError) as exc:
        fail("project.layout maxStageWidth and minViewportWidth must be integers")
        raise exc
    if max_stage_width <= 0 or min_viewport_width <= 0:
        fail("project.layout maxStageWidth and minViewportWidth must be positive")
    return {
        "platform": platform,
        "mode": mode,
        "scale": scale,
        "maxStageWidth": max_stage_width,
        "minViewportWidth": min_viewport_width,
        "center": bool(raw.get("center", True)),
    }


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


FALLBACK_CATEGORY_ORDER = {
    "cjk": ("cjk", "latin"),
    "latin": ("latin", "cjk"),
    "serif": ("serif", "cjk", "latin"),
}

SYSTEM_FALLBACKS = {
    "cjk": ('"PingFang SC"', '"Microsoft YaHei"', '"Noto Sans CJK SC"', "sans-serif"),
    "latin": ('"Arial"', '"Helvetica Neue"', "sans-serif"),
    "serif": ('"Georgia"', '"Times New Roman"', "serif"),
}


def bundled_fallback_root() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "fonts"


def load_bundled_fallbacks(output: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Copy the skill's local fallback fonts and return browser-ready records."""
    root = bundled_fallback_root()
    manifest_path = root / "fallback-fonts.json"
    audit: dict[str, Any] = {"manifest": str(manifest_path), "fonts": [], "errors": []}
    if not manifest_path.is_file():
        audit["errors"].append({"reason": "bundled fallback manifest is missing", "path": str(manifest_path)})
        return {}, audit
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        audit["errors"].append({"reason": f"cannot read bundled fallback manifest: {exc}"})
        return {}, audit
    records: dict[str, dict[str, Any]] = {}
    output_fonts = output / "fonts"
    output_fonts.mkdir(parents=True, exist_ok=True)
    for item in manifest.get("fonts", []):
        if not isinstance(item, dict) or not item.get("id") or not item.get("family"):
            audit["errors"].append({"reason": "invalid bundled fallback entry", "entry": item})
            continue
        files: list[dict[str, str]] = []
        for key, flavor in (("woff2", "woff2"), ("woff", "woff"), ("source", "truetype")):
            raw_name = item.get(key)
            if not isinstance(raw_name, str):
                continue
            source = (root / raw_name).resolve()
            try:
                source.relative_to(root.resolve())
            except ValueError:
                audit["errors"].append({"id": item["id"], "reason": "fallback path escapes assets/fonts", "path": raw_name})
                continue
            if not source.is_file():
                audit["errors"].append({"id": item["id"], "reason": "fallback font file is missing", "path": str(source)})
                continue
            destination = output_fonts / source.name
            shutil.copy2(source, destination)
            files.append({"path": destination.relative_to(output).as_posix(), "format": flavor})
        if not files:
            continue
        record = {
            "id": item["id"],
            "family": item["family"],
            "category": item.get("category", "latin"),
            "weight": int(item.get("weight", 400)),
            "style": item.get("style", "normal"),
            "files": files,
        }
        records[item["id"]] = record
        audit["fonts"].append(record)
    return records, audit


def infer_font_category(font_name: Any, text: Any = "", override: Any = None) -> str:
    """Choose a conservative fallback family group from PSD metadata and text."""
    if override in FALLBACK_CATEGORY_ORDER:
        return str(override)
    token = normalize_font_token(font_name)
    if any(value in token for value in ("serif", "arvo", "song", "ming")):
        return "serif"
    if re.search(r"[\u2e80-\u9fff\u3400-\u4dbf\uf900-\ufaff]", str(text or "")):
        return "cjk"
    if any(value in token for value in ("han", "cjk", "pingfang", "yahei", "heiti", "noto")):
        return "cjk"
    return "latin"


def fallback_stack(bundled: dict[str, dict[str, Any]], category: str) -> str:
    """Return a CSS family stack with category-ordered bundled and system fonts."""
    ordered_categories = FALLBACK_CATEGORY_ORDER.get(category, FALLBACK_CATEGORY_ORDER["latin"])
    families: list[str] = []
    for wanted_category in ordered_categories:
        for record in bundled.values():
            if record["category"] == wanted_category:
                family = f'"{record["family"]}"'
                if family not in families:
                    families.append(family)
    for family in SYSTEM_FALLBACKS.get(category, SYSTEM_FALLBACKS["latin"]):
        if family not in families:
            families.append(family)
    return ", ".join(families)


def normalize_font_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def font_face_names(font: Any) -> list[str]:
    names: list[str] = []
    if "name" not in font:
        return names
    table = font["name"]
    for record in table.names:
        if record.nameID not in (1, 2, 4, 6, 16, 17):
            continue
        try:
            value = record.toUnicode().strip()
        except Exception:
            continue
        if value and value not in names:
            names.append(value)
    return names


def select_font_face(source: Path, source_name: str, mapping: dict[str, Any]) -> dict[str, Any]:
    """Inspect TTF/OTF/TTC/OTC and choose a deterministic font face."""
    try:
        from fontTools.ttLib import TTCollection
    except ImportError as exc:
        raise RuntimeError("missing font tools; install with: python3 -m pip install fonttools brotli") from exc

    signature = source.read_bytes()[:4]
    if signature not in (b"ttcf",):
        return {"container": "single", "font_number": None, "faces": [], "selection": "single-font"}

    collection = TTCollection(str(source))
    faces: list[dict[str, Any]] = []
    for index, font in enumerate(collection.fonts):
        faces.append({"font_number": index, "names": font_face_names(font)})

    explicit = mapping.get("fontNumber")
    if explicit is not None:
        try:
            selected = int(explicit)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"fontNumber must be an integer for {source_name}") from exc
        if selected < 0 or selected >= len(faces):
            raise RuntimeError(f"fontNumber {selected} is outside the available range 0-{len(faces) - 1}")
        return {"container": "collection", "font_number": selected, "faces": faces, "selection": "explicit-fontNumber"}

    targets = [source_name, mapping.get("family"), mapping.get("postScriptName"), mapping.get("fullName")]
    target_tokens = [normalize_font_token(value) for value in targets if normalize_font_token(value)]
    scored: list[tuple[int, int]] = []
    for face in faces:
        score = 0
        for raw_name in face["names"]:
            face_token = normalize_font_token(raw_name)
            for target in target_tokens:
                if face_token == target:
                    score = max(score, 100)
                elif target and target in face_token:
                    score = max(score, 80)
                elif face_token and face_token in target:
                    score = max(score, 70)
                if "ui" in face_token and "ui" not in target:
                    score -= 5
        scored.append((score, face["font_number"]))
    best_score = max((item[0] for item in scored), default=0)
    selected = min(index for score, index in scored if score == best_score) if scored else 0
    selection = "name-match" if best_score > 0 else "default-first-face"
    return {
        "container": "collection",
        "font_number": selected,
        "faces": faces,
        "selection": selection,
        "match_score": best_score,
    }


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


def subset_font(source: Path, destination: Path, text: str, flavor: str, font_number: int | None = None) -> None:
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError as exc:
        raise RuntimeError("missing font tools; install with: python3 -m pip install fonttools brotli") from exc
    options = subset.Options()
    options.flavor = flavor
    options.layout_features = ["*"]
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 16, 17]
    font = TTFont(str(source), fontNumber=font_number) if font_number is not None else TTFont(str(source))
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(destination))


def build_fonts(flow_path: Path, output: Path, project: dict[str, Any], states: dict[str, Any]) -> dict[str, Any]:
    configured = project.get("fonts", {}) or {}
    required, text = collect_font_text(states)
    bundled, bundled_audit = load_bundled_fallbacks(output)
    audit: dict[str, Any] = {
        "required": sorted(required),
        "missing": [],
        "unconfigured": [],
        "compression_errors": [],
        "source_analysis": [],
        "generated": [],
        "bundled_fallbacks": bundled_audit,
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
        category = infer_font_category(name, text, mapping.get("fallbackCategory"))
        stem = css_family_name(name)
        woff2 = output_fonts / f"{stem}.woff2"
        woff = output_fonts / f"{stem}.woff"
        try:
            selection = select_font_face(source, name, mapping)
            audit["source_analysis"].append({"name": name, "file": str(source), **selection})
            font_number = selection["font_number"]
            subset_font(source, woff2, text, "woff2", font_number)
            subset_font(source, woff, text, "woff", font_number)
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
            "fallback_category": category,
            "fallback_css_family": fallback_stack(bundled, category),
        }
        font_record["css_stack"] = f'"{css_family}", {font_record["fallback_css_family"]}'
        if selection["container"] == "collection":
            font_record["source_container"] = "ttc/otc"
            font_record["source_font_number"] = selection["font_number"]
            font_record["source_face_selection"] = selection["selection"]
        fonts[name] = font_record
        audit["generated"].append(font_record)
    return {"fonts": fonts, "audit": audit, "text": text, "bundled": bundled}


def load_flow(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot read flow.json: {exc}")
    if not isinstance(data, dict) or data.get("version") != 1:
        fail("flow.json must be an object with version=1")
    contract_errors: list[str] = []
    contract_warnings: list[str] = []
    validate_generated_contract(data, contract_errors, contract_warnings, True)
    if contract_errors:
        fail("invalid flow.json initialization contract: " + "; ".join(contract_errors))
    return data


def prepare_font_config(flow_path: Path, data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Discover PSD fonts and persist suggested mappings before any build work."""
    project = data.setdefault("project", {})
    if not isinstance(project, dict):
        fail("project must be an object")
    configured = project.setdefault("fonts", {})
    if not isinstance(configured, dict):
        fail("project.fonts must be an object")
    psd_paths = [path for path in flow_psd_paths(data, flow_path.parent) if path.is_file()]
    try:
        scan = scan_psd_paths(psd_paths, flow_path.parent)
    except RuntimeError as exc:
        fail(str(exc))
    added: list[str] = []
    for item in scan["required"]:
        name = item["name"]
        if name not in configured:
            configured[name] = suggested_mapping(name)
            added.append(name)
    audit = audit_project_fonts(scan["required"], project, flow_path.parent)
    if added:
        data["_fontAudit"] = {
            "说明": "由 build_flow.py 根据 PSD 文本图层自动补齐；用户必须把对应 TTF/OTF 放入 fonts/ 并确认 project.fonts 路径。",
            "required": scan["required"],
            "missingMapping": audit["missing_mapping"],
            "missingSource": audit["missing_source"],
            "scanErrors": scan["errors"],
        }
        flow_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return scan, audit, added


def write_runtime(page_dir: Path, runtime: dict[str, Any], html_path: Path, output_root: Path) -> None:
    """Write one isolated document runtime for one root screen."""
    runtime_json = json.dumps(runtime, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (page_dir / "flow-runtime.js").write_text(f"window.PSD_H5_FLOW = {runtime_json};\n", encoding="utf-8")
    (page_dir / "app.js").write_text(
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
      const useText = (runtime.textMode || runtime.text_mode) === 'semantic' && layer.text && layer.font_css_family;
      const node = document.createElement(useText ? 'span' : 'img');
      node.className = useText ? 'flow-text' : 'flow-layer';
      node.alt = layer.text || '';
      node.dataset.layer = layer.name;
      node.style.cssText = cssPosition(layer.bounds) + '--z:' + index + ';--opacity:' + (layer.rendered_opacity ? 1 : layer.opacity / 255) + ';';
      if (useText) {
        const textContent = String(layer.text).replace(/\\r/g, '\\n');
        node.textContent = textContent;
        node.style.fontFamily = layer.font_css_family;
        node.style.fontSize = 'min(calc(' + (layer.font_size || 16) + ' * 100vw / ' + runtime.canvas.width + '), calc(' + (layer.font_size || 16) + 'px))';
        node.style.fontWeight = String(layer.font_weight || 400);
        node.style.fontStyle = layer.font_style || 'normal';
        node.style.letterSpacing = (layer.letter_spacing || 0) + 'em';
        node.style.color = layer.text_color || '#3d3026';
        node.style.whiteSpace = textContent.includes('\\n') ? 'pre' : 'nowrap';
        node.style.overflow = 'visible';
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
    title.textContent = state.title || runtime.page.title || stateKey;
  }

  function transition(trigger) {
    const match = runtime.transitions.find(item => item.from === current && item.trigger === trigger);
    if (!match) return;
    if (match.navigation === 'cross-page') {
      const targetState = match.target_state && match.target_state !== 'default'
        ? '#' + encodeURIComponent(match.target_state)
        : '';
      window.location.assign(match.href + targetState);
      return;
    }
    history.pushState({}, '', `#${encodeURIComponent(match.to)}`);
    render(match.to);
  }

  function renderFromHash() {
    const requested = location.hash ? decodeURIComponent(location.hash.slice(1)) : runtime.initial;
    render(runtime.states[requested] ? requested : runtime.initial);
  }

  renderFromHash();
  window.addEventListener('popstate', renderFromHash);
  window.addEventListener('hashchange', renderFromHash);
})();
""",
        encoding="utf-8",
    )
    width = runtime["canvas"]["width"]
    height = runtime["canvas"]["height"]
    layout = runtime["layout"]
    justify_content = "center" if layout["center"] else "flex-start"
    font_faces = []

    def css_font_url(path: str) -> str:
        return Path(os.path.relpath(output_root / path, page_dir)).as_posix()

    for font in runtime.get("fonts", {}).values():
        font_faces.append(
            "@font-face { "
            f'font-family: "{font["family"]}"; '
            f'src: url("{css_font_url(font["woff2"])}") format("woff2"), url("{css_font_url(font["woff"])}") format("woff"); '
            f'font-weight: {font["weight"]}; font-style: {font["style"]}; font-display: swap; '
            "}"
        )
    for font in runtime.get("fallback_fonts", {}).values():
        sources = ", ".join(
            f'url("{css_font_url(item["path"])}") format("{item["format"]}")' for item in font.get("files", [])
        )
        if sources:
            font_faces.append(
                "@font-face { "
                f'font-family: "{font["family"]}"; '
                f"src: {sources}; "
                f'font-weight: {font["weight"]}; font-style: {font["style"]}; font-display: swap; '
                "}"
            )
    font_face_css = "\n".join(font_faces)
    (page_dir / "styles.css").write_text(
        f"""{font_face_css}
:root {{ font-family: \"PSD_Fallback_SourceHanSansCN\", \"PSD_Fallback_Roboto\", -apple-system, BlinkMacSystemFont, \"Helvetica Neue\", \"PingFang SC\", sans-serif; background:#f2f2f2; }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; min-height:100%; }}
body {{ min-width:{layout["minViewportWidth"]}px; background:#f2f2f2; }}
.flow-preview {{ display:flex; justify-content:{justify_content}; min-height:100vh; }}
.flow-stage {{ position:relative; width:min(100vw, {layout["maxStageWidth"]}px); aspect-ratio:{width}/{height}; overflow:hidden; background:#fff; isolation:isolate; }}
.flow-layer {{ position:absolute; display:block; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:var(--z); opacity:var(--opacity); user-select:none; -webkit-user-drag:none; }}
.flow-text {{ position:absolute; display:block; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:var(--z); opacity:var(--opacity); overflow:visible; line-height:1; white-space:nowrap; user-select:none; }}
.flow-hotspot {{ position:absolute; left:calc(var(--x) * 100% / {width}); top:calc(var(--y) * 100% / {height}); width:calc(var(--w) * 100% / {width}); height:calc(var(--h) * 100% / {height}); z-index:10000; border:0; background:transparent; cursor:pointer; }}
.flow-hotspot:focus-visible {{ outline:2px solid #c88735; outline-offset:-2px; border-radius:8px; }}
.sr-only {{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }}
@media (min-width:520px) {{ .flow-preview {{ padding:28px 0; }} .flow-stage {{ border-radius:12px; box-shadow:0 12px 40px rgba(34,24,14,.16); }} }}
""",
        encoding="utf-8",
    )
    page_title = html.escape(str(runtime.get("page", {}).get("title") or "PSD H5 Page"), quote=True)
    html_path.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>{page_title}</title>
    <link rel="stylesheet" href="./{page_dir.name}/styles.css" />
  </head>
  <body>
    <main class="flow-preview" aria-label="PSD H5 page preview">
      <span class="sr-only" data-flow-title aria-live="polite"></span>
      <div class="flow-stage"></div>
    </main>
    <script src="./{page_dir.name}/flow-runtime.js"></script>
    <script src="./{page_dir.name}/app.js"></script>
  </body>
</html>
""",
        encoding="utf-8",
    )


def page_runtime(
    runtime: dict[str, Any],
    screen_id: str,
    page_info: dict[str, str],
    screens: dict[str, dict[str, str]],
    transitions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Project the global build records into one screen-local runtime."""
    prefix = f"{screen_id}:"
    states: dict[str, Any] = {}
    for key, state in runtime["states"].items():
        if not key.startswith(prefix):
            continue
        state_id = key[len(prefix):]
        record = json.loads(json.dumps(state, ensure_ascii=False))
        if record.get("mode") == "overlay":
            base = str(record.get("base", ""))
            record["base"] = base[len(prefix):] if base.startswith(prefix) else "default"
        states[state_id] = record

    local_transitions: list[dict[str, Any]] = []
    for transition in transitions:
        source = normalize_key(transition["from"])
        source_screen, source_state = source.split(":", 1)
        if source_screen != screen_id:
            continue
        target_screen = transition["to"]
        target_state = transition.get("overlay") or "default"
        if target_screen == screen_id:
            local_transitions.append({
                "from": source_state,
                "trigger": transition["trigger"],
                "to": target_state,
                "navigation": "same-page",
            })
            continue
        target = screens.get(target_screen)
        if not target:
            continue
        local_transitions.append({
            "from": source_state,
            "trigger": transition["trigger"],
            "navigation": "cross-page",
            "target_screen": target_screen,
            "target_state": target_state,
            "href": target["html"],
        })

    return {
        "canvas": runtime["canvas"],
        "layout": runtime["layout"],
        "initial": "default",
        "states": states,
        "transitions": local_transitions,
        "text_mode": runtime.get("text_mode", "raster"),
        "fonts": runtime.get("fonts", {}),
        "fallback_fonts": runtime.get("fallback_fonts", {}),
        "font_stack_policy": runtime.get("font_stack_policy"),
        "font_audit": runtime.get("font_audit", {}),
        "page": page_info,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flow", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-missing-fonts", action="store_true", help="Allow an incomplete preview to use the bundled CSS font fallback stack; still report missing PSD fonts")
    args = parser.parse_args()
    flow_path = args.flow.expanduser().resolve()
    data = load_flow(flow_path)
    font_scan, source_audit, added_fonts = prepare_font_config(flow_path, data)
    if added_fonts:
        print("[psd-to-h5] flow.json updated with required PSD font mappings:", file=sys.stderr)
        for name in added_fonts:
            print(f"  - {name}: {data['project']['fonts'][name]['file']}", file=sys.stderr)
    project = data.get("project", {})
    output = (flow_path.parent / project.get("outputDir", "output")).resolve()
    if output.exists() and any(output.iterdir()) and not args.force:
        fail(f"output is not empty: {output}; pass --force to regenerate")
    output.mkdir(parents=True, exist_ok=True)

    exporter = Path(__file__).with_name("export_psd.py")
    screens = data.get("screens", [])
    screen_files = page_file_map(screens)
    runtime: dict[str, Any] = {
        "canvas": {"width": int(project.get("designWidth", 750)), "height": int(project.get("designHeight", 1630))},
        "initial": "",
        "states": {},
        "pages": screen_files,
        "transitions": [],
        "text_mode": "raster",
        "fonts": {},
        "font_audit": {},
    }
    runtime["layout"] = resolve_layout(project, runtime["canvas"]["width"])
    trigger_index = transition_trigger_index(data.get("transitions", []))
    interaction_gaps: list[dict[str, str]] = []
    state_specs: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for screen in screens:
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
        page_dir = output / screen_files[screen_id]["asset_dir"]
        state_dir = page_dir / state_id
        command = [sys.executable, str(exporter), str(source), str(state_dir)]
        if args.force:
            command.append("--force")
        subprocess.run(command, check=True)
        manifest = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))
        layer_by_name = layer_map(manifest.get("layers", []))
        base_key = normalize_key(spec.get("base", screen_id)) if mode == "overlay" else ""
        base_layer_by_name = layer_map(runtime["states"].get(base_key, {}).get("layers", []))
        elements: list[dict[str, Any]] = []
        element_specs, element_source = state_element_specs(
            spec.get("screen", spec) if isinstance(spec.get("screen", spec), dict) else {},
            spec,
            mode,
            f"{screen_id}:{state_id}",
            trigger_index,
        )
        for element in element_specs:
            if not isinstance(element, dict) or not element.get("id"):
                continue
            bounds = element.get("bounds")
            if not bounds and element.get("layer") in layer_by_name:
                bounds = layer_by_name[element["layer"]].get("bounds")
            if not bounds and element.get("layer") in base_layer_by_name:
                bounds = base_layer_by_name[element["layer"]].get("bounds")
            if not isinstance(bounds, list) or len(bounds) != 4:
                continue
            elements.append({
                "id": element["id"],
                "description": element.get("description", element["id"]),
                "bounds": bounds,
                "source": element_source,
            })
        element_ids = {element["id"] for element in elements}
        for trigger in sorted(trigger_index.get(f"{screen_id}:{state_id}", set())):
            if trigger not in element_ids:
                interaction_gaps.append({
                    "state": f"{screen_id}:{state_id}",
                    "trigger": trigger,
                    "reason": "transition has no element with resolvable bounds",
                })
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
    runtime["fallback_fonts"] = font_result["bundled"]
    runtime["font_stack_policy"] = "exact-first-with-bundled-fallback-always"
    runtime["font_audit"] = font_result["audit"]
    try:
        runtime["font_audit"]["psd_required"] = font_scan["required"]
        runtime["font_audit"]["missing_mapping"] = source_audit["missing_mapping"]
        runtime["font_audit"]["missing_source"] = source_audit["missing_source"]
        runtime["font_audit"]["format_mismatches"] = source_audit.get("format_mismatches", [])
        runtime["font_audit"]["scan_errors"] = font_scan["errors"]
        runtime["font_audit"]["unconfigured"] = [item["name"] for item in source_audit["missing_mapping"]]
        runtime["font_audit"]["missing"] = source_audit["missing_source"]
    except RuntimeError as exc:
        runtime["font_audit"]["scan_errors"] = [{"reason": str(exc)}]
    requested_text_mode = project.get("textMode", "raster")
    font_blockers = bool(
        font_result["audit"]["missing"]
        or font_result["audit"]["unconfigured"]
        or font_result["audit"]["compression_errors"]
    )
    can_use_semantic = requested_text_mode == "semantic" and (not font_blockers or args.allow_missing_fonts)
    runtime["text_mode"] = "semantic" if can_use_semantic else "raster"
    runtime["semantic_font_fallback"] = bool(font_blockers and args.allow_missing_fonts and can_use_semantic)
    for state in runtime["states"].values():
        for layer in state["layers"]:
            font = runtime["fonts"].get(layer.get("font_family"))
            if font:
                layer["font_css_family"] = font["css_stack"]
                layer["font_fallback_category"] = font["fallback_category"]
                layer["font_fallback_available"] = True
                layer["font_fallback_used"] = False
                layer["font_stack_policy"] = "exact-first-with-bundled-fallback-always"
            elif layer.get("text"):
                mapping = project.get("fonts", {}).get(layer.get("font_family"), {})
                category = infer_font_category(
                    layer.get("font_family"),
                    layer.get("text"),
                    mapping.get("fallbackCategory") if isinstance(mapping, dict) else None,
                )
                layer["font_css_family"] = fallback_stack(font_result["bundled"], category)
                layer["font_fallback_category"] = category
                layer["font_fallback_available"] = bool(font_result["bundled"])
                layer["font_fallback_used"] = True
                layer["font_fallback_reason"] = "PSD 原字体未成功生成，使用内置兜底字体"
                layer["font_stack_policy"] = "bundled-fallback-with-system-fallback"

    for transition in data.get("transitions", []):
        if not all(isinstance(transition.get(key), str) for key in ("from", "trigger", "to")):
            continue
        runtime["transitions"].append({
            "from": normalize_key(transition["from"]),
            "trigger": transition["trigger"],
            "to": normalize_key(transition_target(transition, "to")),
            "overlay": transition.get("overlay"),
        })

    (output / "font-audit.json").write_text(json.dumps(runtime["font_audit"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runtime["interaction_gaps"] = interaction_gaps
    runtime["initial_html"] = screen_files[screens[0]["id"]]["html"]
    (output / "flow-build.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for screen in screens:
        screen_id = screen["id"]
        page_info = screen_files[screen_id]
        page_dir = output / page_info["asset_dir"]
        page_dir.mkdir(parents=True, exist_ok=True)
        local_runtime = page_runtime(runtime, screen_id, page_info, screen_files, data.get("transitions", []))
        local_runtime["interaction_gaps"] = [
            gap for gap in interaction_gaps if gap.get("state", "").startswith(f"{screen_id}:")
        ]
        write_runtime(page_dir, local_runtime, output / page_info["html"], output)
    font_gaps = [item["name"] for item in runtime["font_audit"].get("missing_mapping", [])]
    font_gaps += [item["name"] for item in runtime["font_audit"].get("missing_source", [])]
    font_build_errors = [item["name"] for item in runtime["font_audit"].get("compression_errors", []) if item.get("name")]
    font_failures = sorted(set(font_gaps + font_build_errors))
    if font_failures:
        print("[psd-to-h5] FONT INPUT REQUIRED: provide these PSD fonts in project.fonts and fonts/:", file=sys.stderr)
        for name in font_failures:
            print(f"  - {name}", file=sys.stderr)
    if interaction_gaps:
        print("[psd-to-h5] INTERACTION INPUT REQUIRED: these transitions have no clickable element:", file=sys.stderr)
        for gap in interaction_gaps:
            print(f"  - {gap['state']} -> {gap['trigger']}: {gap['reason']}", file=sys.stderr)
    print(json.dumps({
        "output": str(output),
        "initial_html": runtime["initial_html"],
        "pages": {screen_id: info["html"] for screen_id, info in screen_files.items()},
        "states": len(runtime["states"]),
        "transitions": len(runtime["transitions"]),
        "text_mode": runtime["text_mode"],
        "missing_fonts": font_failures,
        "missing_font_mappings": runtime["font_audit"].get("unconfigured", []),
        "font_compression_errors": runtime["font_audit"].get("compression_errors", []),
        "interaction_gaps": interaction_gaps,
    }, ensure_ascii=False))
    if interaction_gaps:
        print("[psd-to-h5] build stopped: add overlay elements or resolvable screen elements for every transition trigger.", file=sys.stderr)
        raise SystemExit(4)
    if font_failures and not args.allow_missing_fonts:
        print("[psd-to-h5] build stopped: provide the listed font files, then run build_flow.py again.", file=sys.stderr)
        raise SystemExit(3)


if __name__ == "__main__":
    main()

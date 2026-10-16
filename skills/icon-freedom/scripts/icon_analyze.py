#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
icon_analyze.py — SVG 图标五维风格分析（icon-freedom skill）

用法:
  python3 icon_analyze.py <spec.json> <icon.svg> [icon2.svg ...]

输出: 每个图标一个 JSON 对象的数组（stdout）。
判定: PASS / FIXABLE / REJECT
  REJECT  = 硬淘汰线，不可自动修正（彩色/渐变、线性↔面性与规格不符、线性+面性混合、空图形）
  FIXABLE = 可由 icon_normalize.py 修回规格（笔画粗细、圆角、栅格尺寸）
  PASS    = 直接入库

五维: ①线性/面性 ②笔画粗细比 ③圆角 ④栅格与留白 ⑤墨水密度(可选, 需 cairosvg, 仅报告不判罚)
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

SHAPES = {"path", "line", "circle", "ellipse", "rect", "polygon", "polyline"}
GROUPS = {"g", "svg", "symbol", "defs", "a"}
NON_PAINT = {"none", "transparent", "inherit", "auto", ""}  # currentcolor 由 paint_class 显式归类
URL_RE = re.compile(r"^url\s*\(", re.I)


def strip_ns(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def to_num(v, default=None):
    if v is None:
        return default
    m = re.match(r"^\s*([-+0-9.eE]+)", str(v))
    return float(m.group(1)) if m else default


def viewbox(root):
    vb = root.get("viewBox") or root.get("viewbox")
    if vb:
        parts = [to_num(p, 0.0) for p in re.split(r"[ ,]+", vb.strip()) if p]
        if len(parts) == 4 and parts[2] and parts[3]:
            return tuple(parts)
    w, h = to_num(root.get("width")), to_num(root.get("height"))
    if w and h:
        return (0.0, 0.0, w, h)
    return (0.0, 0.0, 24.0, 24.0)


def effective_props(root):
    """递归收集可见图形元素及其继承属性。返回 [(tag, props, element)]"""
    out = []

    def walk(el, inh):
        t = strip_ns(el.tag)
        props = dict(inh)
        for k in ("stroke", "fill", "stroke-width", "stroke-linecap", "stroke-linejoin"):
            if el.get(k) is not None:
                props[k] = el.get(k)
        if t in SHAPES:
            out.append((t, dict(props), el))
        elif t in GROUPS:
            for child in list(el):
                walk(child, props)

    walk(root, {})
    return out


def paint_class(v):
    """颜色归类: None(无) / 'url'(渐变引用) / 'currentColor'(单色画笔) / 'concrete'(具体色)"""
    if v is None:
        return None
    v = str(v).strip()
    lv = v.lower()
    if lv in NON_PAINT:
        return None
    if URL_RE.match(v):
        return "url"
    if lv == "currentcolor":
        return "currentColor"
    return "concrete"


def norm_color(v):
    """颜色归一化比较: #abc → #aabbcc，统一小写"""
    v = str(v).strip().lower()
    m = re.match(r"^#([0-9a-f]{3})$", v)
    if m:
        return "#" + "".join(c * 2 for c in m.group(1))
    return v


def ink_density(path_svg, size=64):
    """可选: 墨水密度 = 非透明像素占比。缺 cairosvg 时返回 None。"""
    try:
        import cairosvg  # noqa
    except ImportError:
        return None
    try:
        import io
        png = cairosvg.svg2png(url=path_svg, output_width=size, output_height=size)
        try:
            from PIL import Image
        except ImportError:
            return None
        img = Image.open(io.BytesIO(png)).convert("RGBA")
        px = img.getdata()
        ink = sum(1 for r, g, b, a in px if a > 8)
        return round(ink / float(size * size), 4)
    except Exception:
        return None


def analyze(path_svg, spec):
    issues, fixable = [], []
    try:
        root = ET.parse(path_svg).getroot()
    except Exception as e:
        return {"file": path_svg, "verdict": "REJECT", "reasons": ["SVG 解析失败: %s" % e]}

    vx, vy, vw, vh = viewbox(root)
    grid_max = max(vw, vh)
    elems = effective_props(root)

    stroked, filled = [], []
    paints = set()
    has_url = False
    widths, caps, joins = [], [], []

    for t, props, el in elems:
        st, fi = props.get("stroke"), props.get("fill")
        st_c, fi_c = paint_class(st), paint_class(fi)
        if st_c == "url" or fi_c == "url":
            has_url = True
            continue
        if st_c:
            if st_c == "concrete":
                paints.add(norm_color(st))
            stroked.append(props)
            sw = to_num(props.get("stroke-width"), 1.0)
            widths.append(sw)
            caps.append((props.get("stroke-linecap") or "butt").lower())
            joins.append((props.get("stroke-linejoin") or "miter").lower())
        if fi_c:
            if fi_c == "concrete":
                paints.add(norm_color(fi))
            filled.append(props)

    if not stroked and not filled:
        return {"file": path_svg, "verdict": "REJECT", "reasons": ["未检测到可见描边/填充图形"]}

    style = "linear" if stroked and not filled else ("fill" if filled and not stroked else "mixed")

    if has_url:
        issues.append("REJECT: 引用 url() 渐变/图案填充，字体管线不支持")
    if len(paints) > 1:
        issues.append("REJECT: 彩色图标(%d 种颜色)，字体管线只收单色" % len(paints))
    if style == "mixed":
        issues.append("REJECT: 线性+面性混合，与单一风格规格不符")
    if "<style" in (ET.tostring(root, encoding="unicode")):
        fixable.append("内嵌 <style> CSS，属性解析可能不全，须人工复核")

    spec_style = spec.get("style", "linear")
    grid = float(spec.get("grid", 24))
    stroke_px = float(spec.get("stroke_px", 2))
    spec_ratio = stroke_px / grid
    spec_cap = spec.get("caps", {}).get("linecap", "round")
    spec_join = spec.get("caps", {}).get("linejoin", "round")

    notes = []
    if style != "mixed" and style != spec_style:
        # fill 技术但视觉线性（带孔洞轮廓形, 如 Remix line 系）不算风格冲突
        visual_ok = False
        if style == "fill" and spec_style == "linear":
            from visualstyle import classify_fill
            visual_ok = classify_fill(path_svg) == "linear"
        if visual_ok:
            notes.append("fill 技术但视觉线性(带孔洞轮廓形), 风格判定放行")
        else:
            issues.append("REJECT: 风格=%s 与规格=%s 不符（线性↔面性不可自动转换）" % (style, spec_style))

    if widths:
        sw_med = sorted(widths)[len(widths) // 2]
        ratio = sw_med / grid_max
        dev = abs(ratio - spec_ratio) / spec_ratio
        if dev > 0.2:
            fixable.append("笔画粗细比 %.1f%% vs 规格 %.1f%%（偏差 %.0f%%，可规范化）"
                           % (ratio * 100, spec_ratio * 100, dev * 100))
        cap = max(set(caps), key=caps.count)
        join = max(set(joins), key=joins.count)
        if cap != spec_cap or join != spec_join:
            fixable.append("圆角 %s/%s vs 规格 %s/%s（可规范化）" % (cap, join, spec_cap, spec_join))

    if abs(grid_max - grid) > 0.01:
        fixable.append("栅格 %gx%g vs 规格 %gg（可规范化重缩放）" % (vw, vh, grid))

    verdict = "REJECT" if any(i.startswith("REJECT") for i in issues) else ("FIXABLE" if fixable else "PASS")
    reasons = issues if verdict == "REJECT" else []
    return {
        "file": path_svg,
        "verdict": verdict,
        "style": style,
        "viewbox": [vx, vy, vw, vh],
        "stroke_widths": sorted(set(widths)),
        "linecap": max(set(caps), key=caps.count) if caps else None,
        "distinct_colors": len(paints),
        "ink_density": ink_density(path_svg),
        "fixable": fixable,
        "notes": notes,
        "reasons": reasons,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)
    report = [analyze(p, spec) for p in sys.argv[2:]]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    rej = sum(1 for r in report if r["verdict"] == "REJECT")
    print("\n汇总: %d 个图标 — PASS %d / FIXABLE %d / REJECT %d"
          % (len(report), sum(1 for r in report if r["verdict"] == "PASS"),
             sum(1 for r in report if r["verdict"] == "FIXABLE"), rej),
          file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
icon_normalize.py — SVG 规范化落库（icon-freedom skill）

用法:
  python3 icon_normalize.py <spec.json> -o <out.svg> <in.svg>

做的事（全部可程序修正项，按 spec 修正）:
  1. 栅格重缩放: viewBox 归一到 spec.grid，内容等比缩放并居中
  2. 笔画粗细: stroke-width 按 spec.stroke_px/grid 比例改写（缩放不变性换算）
  3. 圆角: stroke-linecap/linejoin 统一为 spec.caps
  4. 去色: 所有具体颜色 → currentColor；fill="none" 保留
  5. 属性拍平: 描边元素的 stroke-width/linecap/linejoin 显式化，消除继承歧义

硬拒绝（exit 2）: 彩色/渐变、线性+面性混合 —— 与 analyzer 的 REJECT 口径一致。
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
SHAPES = {"path", "line", "circle", "ellipse", "rect", "polygon", "polyline"}
GROUPS = {"g", "svg", "symbol", "a"}
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
    v = str(v).strip().lower()
    m = re.match(r"^#([0-9a-f]{3})$", v)
    if m:
        return "#" + "".join(c * 2 for c in m.group(1))
    return v


def collect(elems_root, inh=None):
    """[(element, props)] 可见图形 + 继承属性（inh 为外部继承起点，如根元素呈现属性）"""
    out = []

    def walk(el, inherited):
        t = strip_ns(el.tag)
        props = dict(inherited)
        for k in ("stroke", "fill", "stroke-width", "stroke-linecap", "stroke-linejoin"):
            if el.get(k) is not None:
                props[k] = el.get(k)
        if t in SHAPES:
            out.append((el, dict(props)))
        elif t in GROUPS:
            for child in list(el):
                walk(child, props)

    walk(elems_root, dict(inh or {}))
    return out


def main():
    args = sys.argv[1:]
    spec_path, out_path, in_path = None, None, None
    i = 0
    while i < len(args):
        if args[i] == "-o":
            out_path = args[i + 1]
            i += 2
        elif spec_path is None:
            spec_path = args[i]
            i += 1
        else:
            in_path = args[i]
            i += 1
    if not (spec_path and out_path and in_path):
        print(__doc__)
        sys.exit(1)

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    grid = float(spec.get("grid", 24))
    stroke_px = float(spec.get("stroke_px", 2))
    spec_ratio = stroke_px / grid
    cap = spec.get("caps", {}).get("linecap", "round")
    join = spec.get("caps", {}).get("linejoin", "round")
    spec_style = spec.get("style", "linear")

    tree = ET.parse(in_path)
    root = tree.getroot()
    vx, vy, vw, vh = viewbox(root)
    grid_max = max(vw, vh)

    elems = collect(root)
    stroked = [p for _, p in elems if paint_class(p.get("stroke")) in ("currentColor", "concrete")]
    filled = [p for _, p in elems if paint_class(p.get("fill")) in ("currentColor", "concrete")]
    for _, p in elems:
        if paint_class(p.get("stroke")) == "url" or paint_class(p.get("fill")) == "url":
            print("REJECT: url() 渐变/图案填充，字体管线不支持", file=sys.stderr)
            sys.exit(2)
    paints = set()
    for p in stroked + filled:
        for k in ("stroke", "fill"):
            v = p.get(k)
            if paint_class(v) == "concrete":
                paints.add(norm_color(v))
    if len(paints) > 1:
        print("REJECT: 彩色图标(%d 种颜色)不收" % len(paints), file=sys.stderr)
        sys.exit(2)
    if stroked and filled:
        print("REJECT: 线性+面性混合，不自动转换", file=sys.stderr)
        sys.exit(2)
    if not stroked and not filled:
        print("REJECT: 空图形", file=sys.stderr)
        sys.exit(2)
    style = "linear" if stroked else "fill"
    if style != spec_style:
        # fill 技术但视觉线性（带孔洞轮廓形, 如 Remix line 系）不算"线性↔面性互转"，视觉判定放行
        if style == "fill" and spec_style == "linear":
            from visualstyle import classify_fill
            if classify_fill(in_path) == "linear":
                print("NOTE: fill 技术但视觉线性(带孔洞轮廓形), 放行", file=sys.stderr)
            else:
                print("REJECT: 风格=面性(实心剪影) 与规格=%s 不符（线性↔面性不可自动转换）" % spec_style, file=sys.stderr)
                sys.exit(2)
        else:
            print("REJECT: 风格=%s 与规格=%s 不符（线性↔面性不可自动转换）" % (style, spec_style), file=sys.stderr)
            sys.exit(2)

    # 笔画粗细换算系数: 目标比 / 原比（与缩放无关）
    widths = [to_num(p.get("stroke-width"), 1.0) for p in stroked]
    orig_ratio = (sorted(widths)[len(widths) // 2] if widths else 1.0) / grid_max
    factor = spec_ratio / orig_ratio if orig_ratio else 1.0

    changes = []

    # 重缩放 + 居中
    s = grid / grid_max
    tx = round((grid - vw * s) / 2 - vx * s, 4)
    ty = round((grid - vh * s) / 2 - vy * s, 4)

    # 新根: 去掉尺寸属性, 设 viewBox; 线性图标根 fill=none 防默认黑
    # 根元素呈现属性要接进继承链（重构后 wrapper 不再是根的子孙, 须显式带入）
    root_inherit = {k: root.get(k) for k in
                    ("stroke", "fill", "stroke-width", "stroke-linecap", "stroke-linejoin")
                    if root.get(k) is not None}
    for attr in ("viewBox", "viewbox", "width", "height"):
        if root.get(attr) is not None:
            del root.attrib[attr]
    root.set("viewBox", "0 0 %g %g" % (grid, grid))
    if style == "linear":
        root.set("fill", "none")

    wrapper = ET.Element("{%s}g" % SVG_NS)
    wrapper.set("transform", "translate(%g,%g) scale(%g)" % (tx, ty, s))
    wrapper.set("stroke-linecap", cap)
    wrapper.set("stroke-linejoin", join)
    children = list(root)
    for ch in children:
        root.remove(ch)
        wrapper.append(ch)
    root.append(wrapper)
    # 拍平后根上的描边呈现属性已冗余, 摘掉保持产物干净
    for k in ("stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"):
        if root.get(k) is not None:
            del root.attrib[k]

    # 描边元素: 拍平 stroke-width + 圆角 + 去色; 填充元素: 去色
    for el, props in collect(wrapper, root_inherit):
        st_c = paint_class(props.get("stroke"))
        fi_c = paint_class(props.get("fill"))
        if st_c in ("currentColor", "concrete"):
            sw = to_num(props.get("stroke-width"), 1.0) * factor
            el.set("stroke-width", "%.4g" % sw)
            el.set("stroke-linecap", cap)
            el.set("stroke-linejoin", join)
            if st_c == "concrete":
                changes.append("stroke→currentColor")
            el.set("stroke", "currentColor")
        elif strip_ns(el.tag) in SHAPES and props.get("stroke") is None:
            el.set("stroke", "none")
        if strip_ns(el.tag) in SHAPES:
            if fi_c in ("currentColor", "concrete"):
                if fi_c == "concrete":
                    changes.append("fill→currentColor")
                el.set("fill", "currentColor")
            elif fi_c is None and props.get("fill") is None:
                pass  # 未声明 fill: 线性图标根已有 fill=none 兜底
            elif fi_c is None and str(props.get("fill")).strip().lower() == "none":
                el.set("fill", "none")
        # 清理继承组上冗余的圆角/粗细, 避免拍平值被覆盖歧义
        if strip_ns(el.tag) == "g":
            for k in ("stroke-width", "stroke-linecap", "stroke-linejoin"):
                if el.get(k) is not None and el is not wrapper:
                    del el.attrib[k]

    if style == "linear" and abs(factor - 1.0) > 0.01:
        changes.append("笔画粗细 x%.3f → 比例 %.1f%%" % (factor, spec_ratio * 100))
    changes.append("栅格 %gx%g → %g" % (vw, vh, grid))

    ET.register_namespace("", SVG_NS)
    data = ET.tostring(root, encoding="unicode")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + data + "\n")

    print(json.dumps({"ok": True, "out": out_path, "style": style,
                      "stroke_factor": round(factor, 4), "changes": changes},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_sheet.py — 候选图标对比页（icon-freedom skill 第 2~3 步：agent 视觉复审 + 用户圈选）

用法:
  python3 render_sheet.py -o /tmp/sheet --refs 参照.svg ... --cands 候选1.svg 候选2.svg ...
      [--report 分析报告.json]

产出:
  <prefix>.html — 人看的圈选页：参照区 + 候选区同尺寸并排，点选后「复制选中 JSON」
  <prefix>.png  — agent 看的网格图（需 cairosvg+PIL，缺则跳过，agent 改用浏览器截图 html）

参照图放最上一排当风格标尺；agent 复审对照参照挑 3~5 个；用户圈选只点不吵。
"""
import argparse
import html
import json
import os
import re

TILE = 72  # 展示尺寸 px


def load_report(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {os.path.basename(r["file"]): r for r in rows}


def read_svg(path):
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r"<script[\s\S]*?</script>", "", s, flags=re.I)
    s = re.sub(r"\son\w+\s*=\s*\"[^\"]*\"", "", s)
    return s


def card(path, ref, meta):
    name = os.path.basename(path)
    badge = "ref" if ref else meta.get("verdict", "?").lower()
    info = []
    if meta:
        if meta.get("style"):
            info.append(str(meta["style"]))
        if meta.get("stroke_widths"):
            info.append("sw=%s" % ",".join(str(w) for w in meta["stroke_widths"]))
        if meta.get("viewbox"):
            vb = meta["viewbox"]
            info.append("vb=%gx%g" % (vb[2], vb[3]))
        if meta.get("ink_density") is not None:
            info.append("ink=%.0f%%" % (meta["ink_density"] * 100))
    why = ""
    if meta.get("reasons"):
        why = '<div class="why">%s</div>' % html.escape("；".join(meta["reasons"]))
    elif meta.get("fixable"):
        why = '<div class="fixable">%s</div>' % html.escape("；".join(meta["fixable"]))
    return (
        '<div class="card %s" data-name="%s">'
        '<div class="box">%s</div>'
        '<div class="name">%s</div>'
        '<div class="meta">%s</div>%s</div>'
        % (badge, html.escape(name), read_svg(path), html.escape(name),
           html.escape(" · ".join(info)), why)
    )


TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>icon-freedom 候选圈选</title><style>
body{font:14px/1.6 -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;margin:24px;color:#222}
h1{font-size:18px} h2{font-size:15px;margin:20px 0 8px;color:#666}
.grid{display:flex;flex-wrap:wrap;gap:12px}
.card{width:110px;border:2px solid #e5e5e5;border-radius:10px;padding:10px 8px;text-align:center;cursor:pointer;background:#fff}
.card:hover{border-color:#bbb}
.card.sel{border-color:#c8a253;background:#fdf9ef}
.card.ref{cursor:default;border-color:#c8a253}
.card.reject{opacity:.45}
.box{width:__TILE__px;height:__TILE__px;margin:0 auto;display:flex;align-items:center;justify-content:center}
.box svg{width:__TILE__px;height:__TILE__px}
.name{font-weight:600;margin-top:6px;word-break:break-all}
.meta{font-size:11px;color:#888}.why{font-size:11px;color:#c0392b;text-align:left;margin-top:4px}
.fixable{font-size:11px;color:#b8860b;text-align:left;margin-top:4px}
#bar{position:sticky;top:0;background:#fff;padding:10px 0;border-bottom:1px solid #eee;z-index:9}
button{padding:6px 18px;border-radius:6px;border:1px solid #c8a253;background:#c8a253;color:#fff;font-size:14px;cursor:pointer}
textarea{width:100%;height:60px;margin-top:8px;font-family:monospace}
</style></head><body>
<h1>icon-freedom 候选圈选页</h1>
<p>金色框 = 已入库参照（风格标尺）。点候选卡选中/取消，选好后点「复制选中 JSON」发给 agent。</p>
<div id="bar"><button onclick="copySel()">复制选中 JSON</button>
<textarea id="out" readonly></textarea></div>
__REFS__
__CANDS__
<script>
var sel={};
document.querySelectorAll('.card:not(.ref)').forEach(function(c){
  c.onclick=function(){var n=c.dataset.name;
    if(c.classList.toggle('sel'))sel[n]=1;else delete sel[n];
    document.getElementById('out').value=JSON.stringify({selected:Object.keys(sel)});};
});
function copySel(){var t=document.getElementById('out');t.select();
  try{navigator.clipboard.writeText(t.value)}catch(e){}
  if(document.execCommand)document.execCommand('copy');}
</script></body></html>"""


def section(title, paths, ref, report):
    cards = "".join(card(p, ref, report.get(os.path.basename(p), {})) for p in paths)
    return "<h2>%s</h2><div class='grid'>%s</div>" % (html.escape(title), cards)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", required=True, help="输出前缀, 如 /tmp/sheet")
    ap.add_argument("--refs", nargs="*", default=[], help="参照 SVG（已入库风格）")
    ap.add_argument("--cands", nargs="*", required=True, help="候选 SVG")
    ap.add_argument("--report", help="icon_analyze.py 的 JSON 报告")
    a = ap.parse_args()

    report = load_report(a.report)
    doc = (TEMPLATE
           .replace("__TILE__", str(TILE))
           .replace("__REFS__", section("参照（已入库风格标尺）", a.refs, True, report))
           .replace("__CANDS__", section("候选", a.cands, False, report)))
    out_html = a.out + ".html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(doc)

    out_png = None
    try:
        import io
        import cairosvg
        from PIL import Image, ImageDraw
        cell, pad, label_h, cols = 96, 10, 18, 4
        items = [("REF:" + os.path.basename(p), p) for p in a.refs] + \
                [(os.path.basename(p), p) for p in a.cands]
        rows = (len(items) + cols - 1) // cols
        W = cols * (cell + pad) + pad
        H = rows * (cell + label_h + pad) + pad
        img = Image.new("RGB", (W, H), "white")
        draw = ImageDraw.Draw(img)
        for i, (name, p) in enumerate(items):
            x = pad + (i % cols) * (cell + pad)
            y = pad + (i // cols) * (cell + label_h + pad)
            try:
                png = cairosvg.svg2png(url=p, output_width=cell, output_height=cell)
                icon = Image.open(io.BytesIO(png)).convert("RGBA")
                img.paste(icon, (x, y), icon)
            except Exception as e:
                draw.text((x, y + cell // 2), "ERR %s" % str(e)[:30], fill="red")
            draw.rectangle([x - 2, y - 2, x + cell + 2, y + cell + 2], outline="#cccccc")
            draw.text((x, y + cell + 2), name[:24], fill="black")
        out_png = a.out + ".png"
        img.save(out_png)
    except ImportError:
        pass

    print(json.dumps({"html": out_html, "png": out_png,
                      "refs": len(a.refs), "cands": len(a.cands)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

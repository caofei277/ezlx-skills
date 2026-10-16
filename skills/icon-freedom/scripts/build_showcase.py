#!/usr/bin/env python3
"""build_showcase.py — 项目图标 H5 展示页生成（icon-freedom skill）

用法（项目根目录执行）: python3 build_showcase.py .icons/spec.json

产出 <spec目录>/showcase.html：单文件自包含（woff2 base64 内嵌，file:// 双击即开，零外部请求）。
功能: 全量图标预览(40px+实际20px) / 关键字检索(名称·中文别名·码点) / 排序(加入时间 新→旧 默认 | 名称)
数据源: <codepoints 目录>/codepoints.json + <spec目录>/manifest.json（icon_add.py 自动维护）。
"""
import argparse, base64, datetime, json, os, re, sys

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · 图标库</title>
<style>
  :root { --ink:#56473b; --bg:#f5f5f5; --card:#fff; --line:#e8e5df; --muted:#8a8378; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; color:#333; }
  .wrap { max-width: 960px; margin: 0 auto; padding: 20px 16px 48px; }
  h1 { font-size: 18px; margin: 4px 0 2px; }
  .sub { color: var(--muted); font-size: 12px; margin-bottom: 14px; }
  .bar { display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:14px; position:sticky; top:0; background:var(--bg); padding:8px 0; z-index:2; }
  .bar input { flex:1; min-width:200px; padding:9px 12px; border:1px solid var(--line); border-radius:8px; font-size:14px; outline:none; background:var(--card); }
  .bar input:focus { border-color: var(--ink); }
  .bar select { padding:9px 8px; border:1px solid var(--line); border-radius:8px; font-size:13px; background:var(--card); }
  .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px,1fr)); gap:10px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 10px 10px; text-align:center; cursor:pointer; transition:border-color .15s; }
  .card:hover { border-color: var(--ink); }
  .big { font-size:40px; line-height:1; color:var(--ink); }
  .small { font-size:20px; line-height:1; color:var(--ink); margin-left:14px; opacity:.75; }
  .nm { margin-top:10px; font-size:12px; font-family:ui-monospace,Menlo,monospace; color:#444; word-break:break-all; }
  .meta { margin-top:3px; font-size:11px; color:var(--muted); }
  .meta b { color:#6b6357; font-weight:500; }
  .empty { text-align:center; color:var(--muted); padding:48px 0; font-size:14px; }
  #toast { position:fixed; left:50%; bottom:36px; transform:translateX(-50%); background:#3a332b; color:#fff; font-size:13px; padding:8px 16px; border-radius:8px; opacity:0; pointer-events:none; transition:opacity .2s; }
  #toast.on { opacity:1; }
</style>
</head>
<body>
<div class="wrap">
  <h1>__TITLE__ · 图标库</h1>
  <div class="sub">__SUB__</div>
  <div class="bar">
    <input id="q" type="search" placeholder="关键字：名称 / 中文 / 码点…" autofocus>
    <select id="sort">
      <option value="time">加入时间 新→旧</option>
      <option value="name">名称 A→Z</option>
    </select>
  </div>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" hidden>没有匹配的图标</div>
</div>
<div id="toast"></div>
<style>
@font-face { font-family:"ifd-showcase"; src:url(data:font/woff2;base64,__FONTB64__) format("woff2"); }
.ifd-showcase { font-family:"ifd-showcase"; font-style:normal; font-weight:normal; }
</style>
<script>
const DATA = __DATA__;
const FONT = 'ifd-showcase';
const grid = document.getElementById('grid'), q = document.getElementById('q'),
      sort = document.getElementById('sort'), empty = document.getElementById('empty'),
      toast = document.getElementById('toast');
let toastTimer;
function showToast(t){ toast.textContent = t; toast.classList.add('on');
  clearTimeout(toastTimer); toastTimer = setTimeout(()=>toast.classList.remove('on'), 1400); }
function glyph(cp){ return '&#x' + cp.replace(/^0x/i,'') + ';'; }
function render(){
  const kw = q.value.trim().toLowerCase();
  let list = DATA.filter(d => !kw ||
      d.name.toLowerCase().includes(kw) || d.alias.toLowerCase().includes(kw) || d.codepoint.toLowerCase().includes(kw));
  list.sort((a,b) => sort.value === 'name' ? a.name.localeCompare(b.name)
                                            : (a.added_at < b.added_at ? 1 : -1));
  grid.innerHTML = list.map(d =>
    `<div class="card" data-cp="${d.codepoint}" title="点击复制 ${d.cls}">
       <div><span class="ifd-showcase big">${glyph(d.codepoint)}</span><span class="ifd-showcase small">${glyph(d.codepoint)}</span></div>
       <div class="nm">${d.cls}</div>
       <div class="meta"><b>${esc(d.alias)}</b> · ${d.codepoint}<br>${esc(d.added_at.slice(0,10))}${d.source? ' · '+esc(d.source):''}</div>
     </div>`).join('');
  empty.hidden = list.length > 0;
}
function esc(s){ return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
grid.addEventListener('click', e => {
  const card = e.target.closest('.card'); if (!card) return;
  const cls = card.querySelector('.nm').textContent;
  const done = () => showToast('已复制 ' + cls);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(cls).then(done).catch(() => fallbackCopy(cls, done));
  } else fallbackCopy(cls, done);
});
function fallbackCopy(text, done){
  const ta = document.createElement('textarea');
  ta.value = text; ta.style.cssText = 'position:fixed;opacity:0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); done(); } catch(e){ showToast('复制失败，请手选: ' + text); }
  document.body.removeChild(ta);
}
q.addEventListener('input', render);
sort.addEventListener('change', render);
render();
</script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    b = spec['build']
    src_dir, out_dir = b['src_dir'], b['out_dir']
    font_name, prefix = b['font_name'], b['class_prefix'].rstrip('-')

    woff2 = os.path.join(out_dir, font_name + '.woff2')
    if not os.path.exists(woff2):
        sys.exit(f'✗ 字体不存在: {woff2}（先跑 icon_add.py / build_font.mjs）')
    b64 = base64.b64encode(open(woff2, 'rb').read()).decode()

    cp_file = os.path.join(src_dir, 'codepoints.json')
    cps = json.load(open(cp_file))
    spec_dir = os.path.dirname(os.path.abspath(a.spec))
    mf_path = os.path.join(spec_dir, 'manifest.json')
    mf = json.load(open(mf_path)) if os.path.exists(mf_path) else {}

    data = []
    for name, cp in cps.items():
        m = mf.get(name, {})
        data.append({
            'name': name,
            'cls': f'{prefix}-{name}',
            'alias': m.get('alias', name),
            'source': m.get('source', ''),
            'added_at': m.get('added_at', '1970-01-01T00:00:00+08:00'),
            'codepoint': m.get('codepoint') or hex(cp),
        })
    data.sort(key=lambda d: d['added_at'], reverse=True)

    html = (TEMPLATE
            .replace('__TITLE__', spec.get('project', '项目'))
            .replace('__SUB__', f'{len(data)} 个图标 · 码点 {min(cps.values()):#x}~{max(cps.values()):#x} · 字体 {font_name} · 生成于 {datetime.date.today()}')
            .replace('__FONTB64__', b64)
            .replace('__DATA__', json.dumps(data, ensure_ascii=False)))
    out = os.path.join(spec_dir, 'showcase.html')
    open(out, 'w').write(html)
    print(f'✓ showcase: {out}（{len(data)} 图标，file:// 双击即开）')


if __name__ == '__main__':
    main()

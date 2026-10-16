#!/usr/bin/env python3
"""fetch_icons.py — 主干库候选批量下载 + 跨库搜索（icon-freedom skill）

用法:
  python3 fetch_icons.py --lib remix --names "newspaper-line,article-line" -o /tmp/cands
  python3 fetch_icons.py --lib iconify --names "tabler:news,ph:newspaper,mdi:newspaper-variant-outline" -o /tmp/cands
  python3 fetch_icons.py --lib iconify --search "报 newspaper" --limit 12        # 跨 150+ 库关键字搜索
  python3 fetch_icons.py --lib iconify --sets                                    # 列出全部图标集

库路由（均为实测可用源，勿再试 unpkg / data API flat listing——均慢或挂）:
  remix    jsdelivr npm remixicon                     fill 技术轮廓形，免描摹直接入库（同风格首选）
  tabler   jsdelivr npm @tabler/icons outline         stroke 稿，入库须走描摹管线
  lucide   jsdelivr npm lucide-static                 stroke 稿，同上
  iconify  api.iconify.design  聚合 150+ 图标集/20 万+ 图标（tabler/ph/mdi/bootstrap/heroicons/…），
           名字带集合前缀 "集合:图标名"；stroke/fill 混杂，icon_add 自动路由。
           这是"大而全"通道：一个接口接全部库，且支持语义搜索。

扩展新库 = 在 ROUTES 加一条（URL 模板或 resolve 函数），十几行的事。
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cdn_cache')
LATEST = {
    'remix': 'https://data.jsdelivr.com/v1/packages/npm/remixicon/resolved',
    'tabler': 'https://data.jsdelivr.com/v1/packages/npm/@tabler/icons/resolved',
    'lucide': 'https://data.jsdelivr.com/v1/packages/npm/lucide-static/resolved',
}
CDN = 'https://cdn.jsdelivr.net/npm/{pkg}@{ver}/{path}'
ICONIFY = 'https://api.iconify.design'


UA = {'User-Agent': 'icon-freedom-fetch/1.0'}  # api.iconify.design 拦默认 python UA（403）


def http_json(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def latest_version(lib):
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, f'{lib}.ver')
    if os.path.exists(cf) and time.time() - os.path.getmtime(cf) < 86400:
        return open(cf).read().strip()
    d = http_json(LATEST[lib])
    ver = d.get('version') or d.get('tags', {}).get('latest')
    if not ver:
        sys.exit(f'[fetch] FAIL: 拿不到 {lib} 最新版本号')
    open(cf, 'w').write(ver)
    return ver


def remix_index(ver):
    """basename -> 完整路径（含 Category 目录）"""
    os.makedirs(CACHE, exist_ok=True)
    cf = os.path.join(CACHE, f'remixicon.{ver}.idx.json')
    if os.path.exists(cf) and time.time() - os.path.getmtime(cf) < 86400:
        return json.load(open(cf))
    d = http_json(f'https://data.jsdelivr.com/v1/packages/npm/remixicon@{ver}', timeout=30)
    idx = {}
    def walk(node, prefix=''):
        for f in node.get('files', []):
            p = prefix + '/' + f['name']
            if f['type'] == 'directory':
                walk(f, p)
            elif p.endswith('.svg'):
                idx[os.path.basename(p)] = p.lstrip('/')
    walk(d)
    json.dump(idx, open(cf, 'w'))
    return idx


def iconify_fetch(fullname, out_path):
    url = f'{ICONIFY}/{fullname}.svg?height=24'
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read()
    if b'<svg' not in data:
        raise ValueError('非 SVG 内容')
    open(out_path, 'wb').write(data)


def iconify_search(query, limit):
    # iconify 多词 AND 过严（"customer group" 常为 0）：整句先试，空则逐词检索合并去重
    words = query.split()
    icons = http_json(f'{ICONIFY}/search?query={urllib.parse.quote(query)}&limit={limit}', timeout=15).get('icons', [])
    if not icons and len(words) > 1:
        seen = set()
        for w in words:
            for i in http_json(f'{ICONIFY}/search?query={urllib.parse.quote(w)}&limit={limit}', timeout=15).get('icons', []):
                if i not in seen:
                    seen.add(i)
                    icons.append(i)
        icons = icons[:limit]
    if not icons:
        print(f'搜索 "{query}" 无结果（可换英文单词，或 --sets 看集合清单）')
        return
    print(f'搜索 "{query}" 命中 {len(icons)} → 用 --lib iconify --names "<名>" 取稿:')
    for i in icons:
        print(f'  {i}')


def iconify_sets():
    d = http_json(f'{ICONIFY}/collections', timeout=20)
    rows = sorted(d.items(), key=lambda kv: -kv[1].get('total', 0))
    print(f'共 {len(rows)} 个图标集（按数量排序，前 30）:')
    for sid, info in rows[:30]:
        print(f"  {sid:<22} {info.get('total', 0):>6} 个  {info.get('name', '')}")
    print('… 全集清单见 https://icon-sets.iconify.design')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', default='remix', choices=['remix', 'tabler', 'lucide', 'iconify'])
    ap.add_argument('--names', default='', help='逗号分隔；iconify 用 "集合:图标名"')
    ap.add_argument('--search', default='', help='iconify 专属：跨库语义搜索')
    ap.add_argument('--sets', action='store_true', help='iconify 专属：列出全部图标集')
    ap.add_argument('--limit', type=int, default=12)
    ap.add_argument('-o', '--out', default='/tmp/cands')
    a = ap.parse_args()

    if a.lib == 'iconify' and (a.search or a.sets):
        if a.sets:
            iconify_sets()
        else:
            iconify_search(a.search, a.limit)
        return

    if not a.names:
        sys.exit('[fetch] FAIL: --names 为空（iconify 搜索用 --search）')

    os.makedirs(a.out, exist_ok=True)
    ok, fail = [], []

    if a.lib == 'iconify':
        for name in [x.strip() for x in a.names.split(',') if x.strip()]:
            full = name if ':' in name else name
            fname = full.replace(':', '_') + '.svg'
            try:
                iconify_fetch(full, os.path.join(a.out, fname))
                ok.append((fname, full))
            except Exception as e:
                fail.append((name, str(e)[:80]))
    else:
        ver = latest_version(a.lib)
        pkg = {'remix': 'remixicon', 'tabler': '@tabler/icons', 'lucide': 'lucide-static'}[a.lib]
        idx = remix_index(ver) if a.lib == 'remix' else None
        for name in [x.strip() for x in a.names.split(',') if x.strip()]:
            fname = name if name.endswith('.svg') else name + '.svg'
            if a.lib == 'remix':
                path = idx.get(fname)
                if not path:
                    hits = [k for k in idx if name.lower() in k.lower()][:5]
                    fail.append((name, f'索引无此名，相近: {hits}'))
                    continue
            elif a.lib == 'tabler':
                path = f'icons/outline/{fname}'
            else:
                path = f'icons/{fname}'
            url = CDN.format(pkg=pkg, ver=ver, path=urllib.parse.quote(path))
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    data = r.read()
                if b'<svg' not in data:
                    raise ValueError('非 SVG 内容')
                open(os.path.join(a.out, fname), 'wb').write(data)
                ok.append((name, path))
            except Exception as e:
                fail.append((name, str(e)[:80]))

    for n, p in ok:
        print(f'OK   {n}  <- {p}')
    for n, why in fail:
        print(f'FAIL {n}  {why}')
    src = f'iconify(聚合源)' if a.lib == 'iconify' else f'{a.lib}@{latest_version(a.lib)}'
    print(f'--lib {a.lib} {src} | {len(ok)} OK / {len(fail)} FAIL | 输出: {os.path.abspath(a.out)}')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()

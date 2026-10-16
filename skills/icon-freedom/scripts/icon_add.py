#!/usr/bin/env python3
"""icon_add.py — 候选图标一条命令入库（icon-freedom skill）

在项目根目录执行（build.src_dir 等相对路径均以 CWD 解析）:
  python3 icon_add.py .icons/spec.json <name> <candidate.svg> [--alias 中文别名] [--source 出处] [--force]

自动路由:
  纯 fill 稿(如 Remix line)  -> icon_normalize.py 规范化直接落库
  含 stroke 稿(如 Tabler)    -> trace.mjs 高分辨率描摹 -> fixorient.py 绕向修正(取 A) -> 落库
随后固定执行: build_font 构建 -> fontTools 三件套验证(contours>0/绕向混合/码点入 cmap)
           -> manifest 更新(.icons/manifest.json) -> showcase.html 再生成
任一步失败即非 0 退出并给出排查指引；成功则打印类名与后续动作提示。
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
DRAW = '{http://www.w3.org/2000/svg}path', '{http://www.w3.org/2000/svg}line', \
       '{http://www.w3.org/2000/svg}circle', '{http://www.w3.org/2000/svg}rect', \
       '{http://www.w3.org/2000/svg}polygon', '{http://www.w3.org/2000/svg}polyline', \
       '{http://www.w3.org/2000/svg}ellipse'
OK, FAIL = '✓', '✗'


def sh(cmd, **kw):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)
    return r


def die(msg, hint=''):
    print(f'{FAIL} {msg}')
    if hint:
        print(f'  排查: {hint}')
    sys.exit(1)


def is_stroke_style(svg_path):
    root = ET.parse(svg_path).getroot()

    def walk(el, inherited):
        s = el.get('stroke')
        eff = s.strip().lower() if s else inherited
        if el.tag in DRAW and eff and eff != 'none':
            return True
        return any(walk(ch, eff) for ch in el)

    return walk(root, None)


def verify_font(font_path, want_name, want_cp):
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print(f'{FAIL} fontTools 未安装，跳过字体级验证——必须人工浏览器复核后再交付')
        return False
    f = TTFont(font_path)
    cmap = f.getBestCmap()
    glyph = cmap.get(want_cp)
    if not glyph:
        die(f'cmap 无码点 {hex(want_cp)}（{want_name}）', 'codepoints.json 与构建产物是否一致')
    g = f['glyf'][glyph]
    n = g.numberOfContours
    if n <= 0:
        die(f'字形 {glyph} 空（contours=0，实为空字形）', '源稿是否 stroke 未描摹 / 描摹是否失败')
    co, ends = g.coordinates, g.endPtsOfContours
    start, signs, boxes = 0, [], []
    for end in ends:
        pts = [(co[i][0], co[i][1]) for i in range(start, end + 1)]
        s = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        signs.append('+' if s > 0 else '-')
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        boxes.append((min(xs), min(ys), max(xs), max(ys), signs[-1]))
        start = end + 1
    # nonzero 语义：只有"嵌套且同向"才把孔洞填成实心；独立兄弟轮廓同向合法（如双箭头）
    def contains(a, b):
        return a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3] and a != b
    for a in boxes:
        for b in boxes:
            if a is not b and contains(a, b) and a[4] == b[4]:
                die(f'字形 {glyph} 存在嵌套且同绕向的轮廓（nonzero 下孔洞被填成实心块）',
                    '描摹稿须过 fixorient.py')
    print(f'{OK} 字体验证: {glyph} contours={n} 绕向={"".join(signs)}')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('name')
    ap.add_argument('candidate')
    ap.add_argument('--alias', default='', help='中文别名（showcase 检索用）')
    ap.add_argument('--source', default='', help='出处，如 remix/newspaper-line@4.9.1')
    ap.add_argument('--force', action='store_true', help='覆盖同名源稿（码点保持不变）')
    a = ap.parse_args()

    name = re.sub(r'[^a-z0-9-]+', '-', a.name.strip().lower()).strip('-')
    if not name:
        die('图标名需 kebab-case')
    if not os.path.exists(a.spec):
        die(f'spec 不存在: {a.spec}')
    if not os.path.exists(a.candidate):
        die(f'候选不存在: {a.candidate}')
    spec = json.load(open(a.spec))
    b = spec['build']
    src_dir, out_dir = b['src_dir'], b['out_dir']
    font_name, prefix = b['font_name'], b['class_prefix'].rstrip('-')
    dst = os.path.join(src_dir, name + '.svg')
    if os.path.exists(dst) and not a.force:
        die(f'{dst} 已存在（改用 --force 覆盖，或换语义名）')
    spec_dir = os.path.dirname(os.path.abspath(a.spec))

    # 1. 路由落库（先保证源目录存在：normalize 不建父目录）
    os.makedirs(src_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='icon_add_')
    if is_stroke_style(a.candidate):
        print(f'{OK} 检测: stroke 型 -> 描摹管线')
        traced = os.path.join(tmp, 'traced.svg')
        r = sh(['node', os.path.join(SCRIPTS, 'trace.mjs'), a.candidate, traced, '960'])
        if r.returncode != 0:
            die('描摹失败', f'node trace.mjs 输出: {r.stderr.strip()[:300]}')
        va, vb = os.path.join(tmp, 'A.svg'), os.path.join(tmp, 'B.svg')
        r = sh(['python3', os.path.join(SCRIPTS, 'fixorient.py'), traced, va, vb])
        if r.returncode != 0:
            die('绕向修正失败', f'fixorient.py 输出: {r.stderr.strip()[:300]}')
        shutil.copy(va, dst)
    else:
        print(f'{OK} 检测: fill 型 -> 规范化直接落库')
        r = sh(['python3', os.path.join(SCRIPTS, 'icon_normalize.py'), a.spec, '-o', dst, a.candidate])
        if r.returncode != 0:
            die('规范化被拒', f'icon_normalize.py 输出: {(r.stdout + r.stderr).strip()[:300]}')
    print(f'{OK} 落库: {dst}')

    # 2. 构建
    r = sh(['node', os.path.join(SCRIPTS, 'build_font.mjs'), '--spec', a.spec])
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        die('构建失败', out[-300:])
    print(f'{OK} 构建: {out_dir}/{font_name}.woff2 + .ttf + css')

    # 3. 验证
    cp_file = os.path.join(src_dir, 'codepoints.json')
    cps = json.load(open(cp_file))
    verify_font(os.path.join(out_dir, font_name + '.ttf'), name, cps[name])

    # 4. manifest
    mf_path = os.path.join(spec_dir, 'manifest.json')
    mf = json.load(open(mf_path)) if os.path.exists(mf_path) else {}
    mf[name] = {
        'alias': a.alias or name,
        'source': a.source or ('stroke->trace' if os.path.exists(dst) else 'fill'),
        'added_at': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        'codepoint': hex(cps[name]),
    }
    json.dump(mf, open(mf_path, 'w'), ensure_ascii=False, indent=2)
    print(f'{OK} manifest: {mf_path}（共 {len(mf)} 图标）')

    # 5. showcase
    r = sh(['python3', os.path.join(SCRIPTS, 'build_showcase.py'), a.spec])
    if r.returncode != 0:
        die('showcase 生成失败', (r.stdout + r.stderr).strip()[:300])

    print(f'\n完成: <{prefix}-{name}> 码点 {cps[name]:#x}  |  下一步: 替换页面引用 -> 项目构建/提交（showcase 已再生成: {os.path.join(spec_dir, "showcase.html")}）')


if __name__ == '__main__':
    main()

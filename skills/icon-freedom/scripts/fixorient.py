# 用法: python3 fixorient.py in.svg out_A.svg out_B.svg
# A: 外环 shoelace>0 / 孔洞 <0；B: 相反
import re, sys
from shapely.geometry import Polygon

def tokenize(d):
    # potrace 输出: 绝对 M/C/L/z
    out = []
    for m in re.finditer(r'([MLCZz])([^MLCZz]*)', d):
        op = m.group(1)
        nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', m.group(2))]
        out.append((op, nums))
    return out

def subpath_polys(tokens):
    subs, cur = [], None
    for op, nums in tokens:
        if op == 'M':
            if cur: subs.append(cur)
            cur = [(op, nums)]
        elif cur is not None:
            cur.append((op, nums))
    if cur: subs.append(cur)
    return subs

def all_points(sub):
    pts = [tuple(sub[0][1][:2])]
    for op, nums in sub[1:]:
        pts.append(tuple(nums[-2:]))
    return pts

def area(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i+1) % len(pts)]
        s += x1*y2 - x2*y1
    return s / 2.0

def depth_of(poly, polys):
    rp = poly.representative_point(); d = 0
    for q in polys:
        if q is not poly and q.area > poly.area and q.contains(rp):
            d += 1
    return d

def reverse_sub(sub):
    # sub: [(M,[x,y]), (C,[c1x,c1y,c2x,c2y,ex,ey]) | (L,[ex,ey]), ...]
    segs = []  # (op, start, ctl, end)
    start = tuple(sub[0][1])
    prev = start
    for op, nums in sub[1:]:
        if op == 'C':
            c1 = tuple(nums[0:2]); c2 = tuple(nums[2:4]); end = tuple(nums[4:6])
            segs.append(('C', prev, [c1, c2], end))
        elif op == 'L':
            end = tuple(nums[0:2])
            segs.append(('L', prev, [], end))
        prev = end
    out = 'M %.3f %.3f' % prev
    for op, s0, ctls, e0 in reversed(segs):
        if op == 'C':
            out += ' C %.3f %.3f %.3f %.3f %.3f %.3f' % (ctls[1][0], ctls[1][1], ctls[0][0], ctls[0][1], s0[0], s0[1])
        else:
            out += ' L %.3f %.3f' % s0
    return out + ' z'

def fix(d, outer_pos):
    tokens = tokenize(d)
    subs = subpath_polys(tokens)
    polys = [Polygon(all_points(s)).buffer(0) if Polygon(all_points(s)).is_valid else Polygon(all_points(s)).convex_hull for s in subs]
    parts = []
    for s, poly in zip(subs, polys):
        depth = depth_of(poly, polys)
        sign = area(all_points(s))
        want_pos = outer_pos if depth % 2 == 0 else not outer_pos
        if (sign > 0) == want_pos:
            # 保持原命令文本
            parts.append(' '.join(op + ' ' + ' '.join('%.3f' % v for v in nums) for op, nums in s).replace('Z', 'z'))
        else:
            parts.append(reverse_sub(s))
    return ' '.join(parts)

svg = open(sys.argv[1]).read()
d = re.search(r'd="([^"]+)"', svg).group(1)
for out, outer_pos in [(sys.argv[2], True), (sys.argv[3], False)]:
    nd = fix(d, outer_pos)
    open(out, 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 960" fill="currentColor"><path d="%s" fill-rule="nonzero"/></svg>' % nd)
    print('wrote', out)

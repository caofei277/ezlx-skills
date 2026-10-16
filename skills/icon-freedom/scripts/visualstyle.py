#!/usr/bin/env python3
"""visualstyle.py — 视觉风格判定（icon-freedom skill 共享件）

线性/面性属"视觉风格"，与涂料技术（stroke/fill）无关：Remix line 系 fill 技术的
轮廓形（带内孔），视觉是线性的，不应按涂料误判成面性拒收。

classify_fill(svg_path) -> 'linear' | 'fill' | None
  'linear'  渲染后存在内孔（轮廓形）→ 视觉线性
  'fill'    实心剪影 → 面性
  None      工具缺失/渲染失败，无法判定（调用方退回涂料判定）
依赖 rsvg-convert + PIL，缺则优雅降级。
"""
import io, subprocess, tempfile, os


def classify_fill(svg_path, px=192):
    """'linear' | 'fill' | None
    双判据：① 内孔（轮廓形强信号）② 墨水占比（细线字形如 ✕/箭头无内孔，
    但覆盖率 <25% 仍属视觉线性；实心剪影通常 >30%）。"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
            png_path = tf.name
        r = subprocess.run(['rsvg-convert', '-w', str(px), '-h', str(px), '-o', png_path, svg_path],
                           capture_output=True, timeout=10)
        if r.returncode != 0:
            return None
        from PIL import Image
        im = Image.open(png_path).convert('RGBA')
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return None
    finally:
        try:
            os.unlink(png_path)
        except OSError:
            pass

    w, h = im.size
    pix = im.load()
    EMPTY, FILLED, OUT = 0, 1, 2
    grid = [[FILLED if pix[x, y][3] > 64 else EMPTY for x in range(w)] for y in range(h)]
    ink = sum(row.count(FILLED) for row in grid) / float(w * h)

    from collections import deque
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if grid[y][x] == EMPTY:
                grid[y][x] = OUT
                dq.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if grid[y][x] == EMPTY:
                grid[y][x] = OUT
                dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == EMPTY:
                grid[ny][nx] = OUT
                dq.append((nx, ny))
    has_hole = any(grid[y][x] == EMPTY for y in range(h) for x in range(w))
    if has_hole:
        return 'linear'
    if ink < 0.25:
        return 'linear'
    return 'fill'

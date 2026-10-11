# -*- coding: utf-8 -*-
"""在用户的 0/30 整屏图和我的真实截图里，扫描定位券数数字（放宽范围+阈值）。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

CASES = [
    ("用户图 0/30 (2729x1536)", "shots/ticket_0of30_screen.png", 1.421),
    ("我的图 0/30 (1920x1080)", "shots/ticket_real_zero.png", 1.0),
]


def scan(path, scale):
    im = Image.open(path).convert("L")
    g = np.asarray(im, dtype=np.float32)
    H, W = g.shape
    # 归一化到 1920 基准后再扫描：x 1400~1920, y 0~120
    x1, x2 = int(1400 * scale), min(W, int(1920 * scale))
    y1, y2 = 0, min(H, int(120 * scale))
    sub = g[y1:y2, x1:x2]
    th = 170
    mask = sub > th
    cols = mask.sum(axis=0)
    segs, start = [], None
    for i, v in enumerate(cols):
        if v > 0 and start is None:
            start = i
        elif v == 0 and start is not None:
            segs.append((x1 + start, x1 + i - 1))
            start = None
    if start is not None:
        segs.append((x1 + start, x1 + len(cols) - 1))
    print(f"\n{path}  扫描 x{x1}~{x2} y{y1}~{y2} 阈值>{th}")
    for a1, a2 in segs:
        if a2 - a1 + 1 < 4:
            continue
        m = mask[:, a1 - x1:a2 - x1 + 1]
        rr = np.nonzero(m.sum(axis=1) > 0)[0]
        h = int(rr.max() - rr.min() + 1) if len(rr) else 0
        print(f"  x {a1:5d}~{a2:5d} 宽 {a2-a1+1:4d}(基准{(a2-a1+1)/scale:5.1f}) "
              f"高 {h:4d}(基准{h/scale:5.1f}) 亮 {int(m.sum()):6d}")


for label, path, scale in CASES:
    print("=" * 70)
    print(label)
    scan(path, scale)

# -*- coding: utf-8 -*-
"""找出 0/30 截图里数字的实际亮度，选合适阈值再量宽度。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/ticket_0of30_screen.png").convert("RGB")
W, H = im.size
sx, sy = W / 1920.0, H / 1080.0
g = np.asarray(im.convert("L"), dtype=np.float32)

x1, x2 = int(2200), int(2720)
y1, y2 = int(14), int(130)
sub = g[y1:y2, x1:x2]
print(f"券数区 x{x1}~{x2} y{y1}~{y2}: 均值 {sub.mean():.1f} 最大 {sub.max():.0f} "
      f"分位 90%={np.percentile(sub,90):.0f} 99%={np.percentile(sub,99):.0f}")

for th in (200, 180, 160):
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
    segs = [s for s in segs if s[1] - s[0] + 1 >= 3]
    print(f"\n阈值 {th}: 亮像素 {int(mask.sum())} 段数 {len(segs)}")
    for a1, a2 in segs:
        m = mask[:, a1 - x1:a2 - x1 + 1]
        rr = np.nonzero(m.sum(axis=1) > 0)[0]
        h = int(rr.max() - rr.min() + 1) if len(rr) else 0
        print(f"  x {a1}~{a2} 宽 {a2-a1+1:4d} 高 {h:4d} -> 1920基准 宽{(a2-a1+1)/sx:5.1f} 高{h/sy:5.1f}")

im.crop((x1, y1, x2, y2)).save("shots/ticket_0of30_zoom.png")
print("\n已保存 shots/ticket_0of30_zoom.png", (x2 - x1, y2 - y1))

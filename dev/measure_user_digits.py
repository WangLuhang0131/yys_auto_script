# -*- coding: utf-8 -*-
"""精确量「0/30」的数字：区域 x2260~2680, y25~110（用户整屏图坐标）。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/ticket_0of30_screen.png").convert("L")
g = np.asarray(im, dtype=np.float32)
X1, Y1, X2, Y2 = 2260, 25, 2680, 110
sub = g[Y1:Y2, X1:X2]
print(f"区域 {X1},{Y1}-{X2},{Y2}: 均值 {sub.mean():.1f} 最大 {sub.max():.0f} "
      f"p95={np.percentile(sub,95):.0f} p99={np.percentile(sub,99):.0f}")

for th in (130, 140, 150, 160):
    mask = sub > th
    cols = mask.sum(axis=0)
    segs, start = [], None
    for i, v in enumerate(cols):
        if v > 2 and start is None:
            start = i
        elif v <= 2 and start is not None:
            segs.append((X1 + start, X1 + i - 1))
            start = None
    if start is not None:
        segs.append((X1 + start, X1 + len(cols) - 1))
    segs = [s for s in segs if s[1] - s[0] + 1 >= 4]
    print(f"\n阈值 {th}: 段数 {len(segs)}")
    for a1, a2 in segs:
        m = mask[:, a1 - X1:a2 - X1 + 1]
        rr = np.nonzero(m.sum(axis=1) > 2)[0]
        h = int(rr.max() - rr.min() + 1) if len(rr) else 0
        print(f"  x {a1:5d}~{a2:5d} 宽 {a2-a1+1:4d} 高 {h:4d} 亮 {int(m.sum()):6d}")

im.crop((X1, Y1, X2, Y2)).resize(((X2 - X1) * 2, (Y2 - Y1) * 2), Image.NEAREST).save(
    "shots/user_digits_zoom.png")
print("\n已保存 shots/user_digits_zoom.png")

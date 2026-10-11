# -*- coding: utf-8 -*-
"""在 0/30 整屏图的右上角大范围扫描，定位计数数字并量宽度。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/ticket_0of30_screen.png").convert("RGB")
W, H = im.size
sx = W / 1920.0
g = np.asarray(im.convert("L"), dtype=np.float32)

# 右上角：从 x 1700 到右边、y 0~160
X1, Y1, X2, Y2 = 1700, 0, W, 160
sub = g[Y1:Y2, X1:X2]
print(f"扫描区 x{X1}~{X2} y{Y1}~{Y2} 均值 {sub.mean():.1f} 最大 {sub.max():.0f}")

th = max(120, float(np.percentile(sub, 99.5)))
print(f"取阈值 {th:.0f}")
mask = sub > th
cols = mask.sum(axis=0)
segs, start = [], None
for i, v in enumerate(cols):
    if v > 0 and start is None:
        start = i
    elif v == 0 and start is not None:
        segs.append((X1 + start, X1 + i - 1))
        start = None
if start is not None:
    segs.append((X1 + start, X1 + len(cols) - 1))

print(f"\n字形段（宽≥3）：")
for a1, a2 in segs:
    if a2 - a1 + 1 < 3:
        continue
    m = mask[:, a1 - X1:a2 - X1 + 1]
    rr = np.nonzero(m.sum(axis=1) > 0)[0]
    h = int(rr.max() - rr.min() + 1) if len(rr) else 0
    print(f"  x {a1}~{a2} 宽 {a2-a1+1:4d} 高 {h:4d} 亮 {int(m.sum()):5d}"
          f"  -> 1920基准 宽{(a2-a1+1)/sx:5.1f} 高{h/sx:5.1f}")

im.crop((X1, Y1, X2, Y2)).save("shots/ticket_0of30_zoom.png")
print("\n已保存 shots/ticket_0of30_zoom.png")

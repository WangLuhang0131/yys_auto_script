# -*- coding: utf-8 -*-
"""分析突破券计数「7/30」各位数字的精确位置与形状，设计稳定判据。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/ticket_now.png").convert("L")
a = np.asarray(im, dtype=np.float32)

# 数字区（实测）：x 1640~1805, y 20~80
sub = a[20:80, 1630:1810]
mask = sub > 150
cols = mask.sum(axis=0)
rows = mask.sum(axis=1)

# 找连续的字形段
segs = []
start = None
for i, v in enumerate(cols):
    if v > 0 and start is None:
        start = i
    elif v == 0 and start is not None:
        segs.append((1630 + start, 1630 + i - 1))
        start = None
if start is not None:
    segs.append((1630 + start, 1630 + len(cols) - 1))

print("字形段（x 范围，宽度）：")
for x1, x2 in segs:
    m = mask[:, x1 - 1630:x2 - 1630 + 1]
    rr = np.nonzero(m.sum(axis=1) > 0)[0]
    h = (rr.max() - rr.min() + 1) if len(rr) else 0
    print(f"  x {x1}~{x2}  宽 {x2-x1+1:3d}  高 {h:3d}  亮像素 {int(m.sum()):5d}  "
          f"填充率 {m.mean():.2f}")
print("  纵向范围: y", 20 + np.nonzero(rows > 0)[0].min(), "~", 20 + np.nonzero(rows > 0)[0].max())

# 保存数字区放大图
im.crop((1630, 20, 1810, 80)).resize((180 * 3, 60 * 3), Image.NEAREST).save("shots/ticket_digits_zoom.png")
print("\n已保存 shots/ticket_digits_zoom.png")

# -*- coding: utf-8 -*-
"""用两张状态图的差异，自动找出最有区分度的小区域，并给出干净判据。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

A = np.asarray(Image.open("shots/lockm_state1.png").convert("RGB"), dtype=np.float32)
B = np.asarray(Image.open("shots/lockm_state2.png").convert("RGB"), dtype=np.float32)
BOX = (1230, 845, 1330, 920)
x1, y1, x2, y2 = BOX
a = A[y1:y2, x1:x2]
b = B[y1:y2, x1:x2]
ga, gb = a.mean(axis=2), b.mean(axis=2)

# 逐像素差异
diff = gb - ga
print(f"区域尺寸 {a.shape[1]}x{a.shape[0]}")
print(f"状态1 平均亮度 {ga.mean():.1f} / 状态2 平均亮度 {gb.mean():.1f}")

# 找差异最大的 20x20 小块
best = None
h, w = ga.shape
for yy in range(0, h - 20, 5):
    for xx in range(0, w - 20, 5):
        d = abs(float((gb[yy:yy + 20, xx:xx + 20] - ga[yy:yy + 20, xx:xx + 20]).mean()))
        if best is None or d > best[0]:
            best = (d, xx, yy)
print(f"\n差异最大的 20x20 块：差异 {best[0]:.1f}，区域内偏移 ({best[1]},{best[2]}) "
      f"-> 全屏坐标 ({x1+best[1]},{y1+best[2]})-({x1+best[1]+20},{y1+best[2]+20})")

# 在这个块上量指标
d_, xx, yy = best
sub_a = a[yy:yy + 20, xx:xx + 20]
sub_b = b[yy:yy + 20, xx:xx + 20]
for name, sub in (("状态1", sub_a), ("状态2", sub_b)):
    g = sub.mean(axis=2)
    print(f"  {name}: 均值{g.mean():6.1f} 亮>120 {(g>120).mean():.3f} "
          f"暗<90 {(g<90).mean():.3f} 平均色 {tuple(round(float(v)) for v in sub.reshape(-1,3).mean(axis=0))}")

# 也在整块区域上给出「暗像素占比」两个值，看哪个更适合做判据
for name, g in (("状态1", ga), ("状态2", gb)):
    print(f"  整块 {name}: 暗<90 {(g<90).mean():.3f}  亮>160 {(g>160).mean():.3f}")

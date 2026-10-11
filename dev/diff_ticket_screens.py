# -*- coding: utf-8 -*-
"""整屏差异图：对比 0/30 与 7/30 两张真实截图，找出实际变化的位置。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

A = np.asarray(Image.open("shots/ticket_now.png").convert("L"), dtype=np.int16)
B = np.asarray(Image.open("shots/ticket_real_zero.png").convert("L"), dtype=np.int16)
d = np.abs(A - B)
print(f"整屏差异: 平均 {d.mean():.2f}  变化像素(>40) {int((d>40).sum())}")

# 找出变化最集中的区域（按 40x40 块统计）
h, w = d.shape
blocks = []
for y in range(0, h - 40, 40):
    for x in range(0, w - 40, 40):
        n = int((d[y:y + 40, x:x + 40] > 40).sum())
        if n > 50:
            blocks.append((n, x, y))
blocks.sort(reverse=True)
print("\n变化最多的块（前 15）:")
for n, x, y in blocks[:15]:
    print(f"  ({x:4d},{y:4d}) 变化像素 {n}")

# 特别看右上角区域
print("\n右上角 (x1500~1920, y0~120) 差异:", int((d[0:120, 1500:1920] > 40).sum()))

# -*- coding: utf-8 -*-
"""用「亮带」统计锁定三行的上下边界：面板底色比背景亮。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/state_now2.png").convert("L")
g = np.asarray(im, dtype=np.float32)

# 只看面板横向范围（避开左侧加成/皮肤），统计每行有多少像素是"面板浅色"
x1, x2 = 350, 1650
strip = g[:, x1:x2]
frac = (strip > 110).mean(axis=1)
print("y : 面板浅色像素占比（只打印 y 150~790，每 10 行）")
for y in range(150, 790, 10):
    bar = "#" * int(frac[y] * 50)
    print(f"{y:4d} {frac[y]:.2f} {bar}")

# 找出占比高的连续区间 = 行
runs = []
in_run = False
for y in range(120, 900):
    v = frac[y] > 0.55
    if v and not in_run:
        start, in_run = y, True
    elif not v and in_run:
        runs.append((start, y - 1)); in_run = False
if in_run:
    runs.append((start, 899))
print("\n亮带区间（占比>0.55）:")
for a, b in runs:
    if b - a > 30:
        print(f"  y {a}~{b}  高 {b-a+1}  中心 {(a+b)//2}")

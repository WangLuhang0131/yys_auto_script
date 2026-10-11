# -*- coding: utf-8 -*-
"""用红色像素自动定位探索页底栏的「结界突破」图标，避免目测坐标又裁偏。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")
S = im.size[0] / 1920.0
print("图", im.size, "缩放", round(S, 3))

# 底栏区域（基准 y 880~1010, x 150~900）找红色像素
X1, Y1, X2, Y2 = (int(150 * S), int(880 * S), int(900 * S), int(1010 * S))
a = np.asarray(im, dtype=np.float32)[Y1:Y2, X1:X2]
red = ((a[:, :, 0] > 140) & (a[:, :, 1] < 110) & (a[:, :, 2] < 110)
       & (a[:, :, 0] - a[:, :, 1] > 60))
n = int(red.sum())
print("红色像素数:", n)
if n:
    ys, xs = np.nonzero(red)
    # 按 x 聚类（相邻 60px 内算一簇）
    order = np.argsort(xs)
    xs_s, ys_s = xs[order], ys[order]
    clusters = []
    start = 0
    for i in range(1, len(xs_s)):
        if xs_s[i] - xs_s[i - 1] > 60:
            clusters.append((xs_s[start:i], ys_s[start:i]))
            start = i
    clusters.append((xs_s[start:], ys_s[start:]))
    print(f"红色簇数: {len(clusters)}")
    for cx, cy in clusters:
        bx1 = X1 + cx.min(); bx2 = X1 + cx.max()
        by1 = Y1 + cy.min(); by2 = Y1 + cy.max()
        print(f"  簇: 基准 x {bx1/S:.0f}~{bx2/S:.0f}  y {by1/S:.0f}~{by2/S:.0f}  "
              f"像素 {len(cx)}")

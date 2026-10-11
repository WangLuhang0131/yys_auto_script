# -*- coding: utf-8 -*-
"""在底栏更窄的范围内用亮红色精确定位「结界突破」图标。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")
S = im.size[0] / 1920.0

X1, Y1, X2, Y2 = (int(400 * S), int(900 * S), int(700 * S), int(1020 * S))
a = np.asarray(im, dtype=np.float32)[Y1:Y2, X1:X2]
red = ((a[:, :, 0] > 170) & (a[:, :, 1] < 95) & (a[:, :, 2] < 95))
print("亮红像素数:", int(red.sum()))
ys, xs = np.nonzero(red)
if len(xs):
    bx1, bx2 = X1 + xs.min(), X1 + xs.max()
    by1, by2 = Y1 + ys.min(), Y1 + ys.max()
    print("亮红范围(基准): x %.0f~%.0f  y %.0f~%.0f"
          % (bx1 / S, bx2 / S, by1 / S, by2 / S))
    # 按列看分布，找图标主体
    cols = red.sum(axis=0)
    idx = np.nonzero(cols > 2)[0]
    if len(idx):
        print("列分布(基准 x): %d~%d 宽 %d"
              % (X1 / S + idx.min() / S, X1 / S + idx.max() / S,
                 (idx.max() - idx.min()) / S))

# 直接裁一块大的看看到底在哪
box = tuple(int(v * S) for v in (400, 880, 720, 1030))
crop = im.crop(box)
crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save("shots/entry_region.png")
print("已存 shots/entry_region.png（基准 400~720, 880~1030）")

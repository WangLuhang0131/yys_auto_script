# -*- coding: utf-8 -*-
"""重新标定 9 宫格的行中心。

用「攻破记录」右侧进度条与格子边缘的亮度过渡找行边界，
再用「可打/已攻破」两种格子的亮度差验证。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/state_now2.png").convert("L")
g = np.asarray(im, dtype=np.float32)

# 沿 x 取几列（格子中部：列心 505/865/1225），看纵向亮度剖面找行
for cx in (505, 865, 1225):
    col = g[150:800, cx - 80:cx + 80].mean(axis=1)
    # 找亮/暗过渡（行的边界处会明显变化）
    d = np.abs(np.diff(col))
    edges = [150 + i for i in np.nonzero(d > 12)[0]]
    # 压缩相邻
    merged = []
    for e in edges:
        if not merged or e - merged[-1] > 8:
            merged.append(e)
    print(f"列 x={cx}: 纵向边界 {merged}")
    # 打印每 25 像素的均值，便于人眼看行区间
    print("   y:均值 " + " ".join(
        f"{150+i}:{col[i]:.0f}" for i in range(0, len(col), 25)))

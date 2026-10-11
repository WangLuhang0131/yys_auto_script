# -*- coding: utf-8 -*-
"""精确定位备战页「挑战次数」数字，并做「是否为 0」的判据。

实机画面：topbar 有两组「卷轴 + 数字」：
  第一组 = 剩余挑战次数（道具用尽时是 0）
  第二组 = 恢复道具（0）
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/prep_zero_live.png").convert("L")
g = np.asarray(im, dtype=np.float32)

# 在 y 20~90 找亮像素簇（白色数字）
band = g[20:90, 900:1920]
mask = band > 170
cols = mask.sum(axis=0)
segs, start = [], None
for i, v in enumerate(cols):
    if v > 0 and start is None:
        start = i
    elif v == 0 and start is not None:
        segs.append((900 + start, 900 + i - 1))
        start = None
if start is not None:
    segs.append((900 + start, 900 + len(cols) - 1))
print("亮像素段（x 范围, 宽, 高, 像素数）:")
for a1, a2 in segs:
    if a2 - a1 + 1 < 3:
        continue
    m = mask[:, a1 - 900:a2 - 900 + 1]
    rr = np.nonzero(m.sum(axis=1) > 0)[0]
    h = int(rr.max() - rr.min() + 1) if len(rr) else 0
    print(f"  x {a1}~{a2}  宽 {a2-a1+1:3d}  高 {h:3d}  亮 {int(m.sum()):5d}")

im.crop((1150, 10, 1400, 100)).resize((250 * 3, 90 * 3), Image.NEAREST).save(
    "shots/count_area_zoom.png")
print("\n已保存 shots/count_area_zoom.png")

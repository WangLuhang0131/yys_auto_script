# -*- coding: utf-8 -*-
"""用真实的「0/30」截图验证并校准突破券判据，同时给「结界挑战券不足」做模板。

用户给的 0/30 截图（整屏）是 jpeg，counter 是放大裁剪图。
整屏图里券数区域的像素坐标需要实测 —— 注意 0/30 比 7/30 窄，
数字整体会往中间靠，所以判据必须对这种方式鲁棒。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
from tasks.jiejie_tupo import attack as atk              # noqa: E402

FULL = "shots/ticket_0of30_screen.png"
im = Image.open(FULL).convert("RGB")
print("整屏尺寸:", im.size)

# 1) 先用当前判据跑一遍
info = atk.ticket_info(im)
print("\n当前判据结果:")
print("  字形段:", info["glyphs"])
print("  斜杠宽:", info["slash_w"], " 左数宽:", info["left_w"],
      " 左数位置:", info["left_x"], " 判定用完:", info["almost_out"])

# 2) 直接看券数区域（右上一片）的字形分布，确认位置是否和 7/30 一致
g = np.asarray(im.convert("L"), dtype=np.float32)
sub = g[20:80, 1600:1830]
mask = sub > 150
cols = mask.sum(axis=0)
segs, start = [], None
for i, v in enumerate(cols):
    if v > 0 and start is None:
        start = i
    elif v == 0 and start is not None:
        segs.append((1600 + start, 1600 + i - 1))
        start = None
if start is not None:
    segs.append((1600 + start, 1600 + len(cols) - 1))
print("\n券数区 (x1600~1830) 字形段:")
for x1, x2 in segs:
    m = mask[:, x1 - 1600:x2 - 1600 + 1]
    rr = np.nonzero(m.sum(axis=1) > 0)[0]
    h = int(rr.max() - rr.min() + 1) if len(rr) else 0
    print(f"  x {x1}~{x2} 宽 {x2-x1+1:3d} 高 {h:3d} 亮像素 {int(m.sum()):5d}")

im.crop((1600, 15, 1840, 85)).resize((240 * 3, 70 * 3), Image.NEAREST).save(
    "shots/ticket_0of30_zoom.png")
print("\n已保存 shots/ticket_0of30_zoom.png")

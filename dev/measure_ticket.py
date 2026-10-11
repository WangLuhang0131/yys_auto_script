# -*- coding: utf-8 -*-
"""量突破券计数区（右上 7/30），并制作「0/30」模板用于判断券是否用完。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from PIL import Image, ImageDraw                          # noqa: E402

a = Adb()
im = a.screenshot()
im.save("shots/ticket_now.png")
g = np.asarray(im.convert("L"), dtype=np.float32)

# 在右上角大范围里找「亮数字」的分布，定位数字簇
sub = g[20:80, 1400:1800]
cols = (sub > 150).sum(axis=0)
print("x=1400 起，各列亮像素数（>150）：")
runs = []
start = None
for i, v in enumerate(cols):
    if v > 0 and start is None:
        start = i
    elif v == 0 and start is not None:
        runs.append((1400 + start, 1400 + i - 1))
        start = None
if start is not None:
    runs.append((1400 + start, 1400 + len(cols) - 1))
print("  连续亮列区间:", runs)

rows = (sub > 150).sum(axis=1)
rr = np.nonzero(rows > 2)[0]
if len(rr):
    print(f"  数字纵向范围: y {20+rr.min()} ~ {20+rr.max()}")

# 生成一个「0/30」参考模板（把 7 换成 0，宽度略窄，只用它做粗略校验）
box = (1480, 25, 1640, 75)
crop = im.crop(box)
crop.resize((crop.width * 3, crop.height * 3)).save("shots/ticket_zoom.png")
print("\n计数区裁剪保存为 shots/ticket_zoom.png，尺寸", crop.size)

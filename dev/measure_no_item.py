# -*- coding: utf-8 -*-
"""抓取「道具用尽」时的备战页，量出可用判据。

现象：挑战次数 0、点挑战弹出「琥珀卷轴不足」，但挑战按钮看起来还是亮的
（所以我原来"按钮变灰"的判据失效）。
需要的新判据：中部提示（toast）的检测。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402

a = Adb()
im = a.screenshot()
im.save("shots/no_item_prep.png")
print("已保存 shots/no_item_prep.png", im.size)

g = np.asarray(im.convert("L"), dtype=np.float32)
# 中部提示带（用户截图里 toast 在 y≈320 附近）
band = g[300:360, 700:1250]
print(f"中部提示带 y300~360 x700~1250: 均值 {band.mean():.1f} 最大 {band.max():.0f}")

# 逐行看哪一行最亮（toast 文字是白色）
rows = (g[:, 700:1250] > 200).sum(axis=1)
top = np.argsort(rows)[::-1][:12]
print("亮像素最多的行（前12）:", sorted(int(y) for y in top))
for y in sorted(int(v) for v in top)[:6]:
    print(f"  y={y}: 亮像素 {rows[y]}")

# 挑最亮那一行，量它的横向范围
y = int(np.argmax(rows))
cols = np.nonzero(g[y - 25:y + 25, :] > 200)[1]
if len(cols):
    print(f"最亮行 y={y}，附近横向亮像素范围 x {cols.min()}~{cols.max()}")

# 顺便看右上角挑战次数区域
print("\n右上角次数区域（x 1450~1700, y 20~80）:")
sub = g[20:80, 1450:1700]
print(f"  均值 {sub.mean():.1f} 亮像素(>180) {int((sub>180).sum())}")
im.crop((1400, 10, 1760, 90)).resize((360 * 2, 80 * 2), Image.NEAREST).save(
    "shots/no_item_count_zoom.png")

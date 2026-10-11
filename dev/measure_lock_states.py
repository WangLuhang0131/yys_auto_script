# -*- coding: utf-8 -*-
"""量化「阵容」锁定图标的两种状态：未锁定(深色边框) / 已锁定(金色边框)。

用户说明：图1 深色边框 = 未锁定；图2 金色边框 = 已锁定。
用 adb 抓当前画面（游戏停在结界突破页，当前是已锁定状态），
先按「阵容」按钮位置裁一块看真实画面，再定判据。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from PIL import Image                                    # noqa: E402

a = Adb()
im = a.screenshot()
im.save("shots/lock_state_now.png")

# 「阵容」按钮整体（含左侧图标）：实测大致 x 1240~1400, y 850~915
BOX = (1230, 845, 1330, 920)
crop = im.crop(BOX)
crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST).save("shots/lock_icon_now.png")

arr = np.asarray(crop, dtype=np.float32)
g = arr.mean(axis=2)
print("当前（应为已锁定）图标区：")
print("  平均色:", tuple(round(v) for v in arr.reshape(-1, 3).mean(axis=0)))
print("  平均亮度: %.1f" % g.mean())
light = float((g > 120).mean())
gold = float(((arr[:, :, 0] > 140) & (arr[:, :, 1] > 110) & (arr[:, :, 2] < 150)
              & (arr[:, :, 0] - arr[:, :, 2] > 45)).mean())
print("  亮像素(>120)占比: %.3f" % light)
print("  金色像素占比: %.3f" % gold)
print("  已保存放大图 shots/lock_icon_now.png")

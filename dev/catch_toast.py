# -*- coding: utf-8 -*-
"""实机抓「琥珀卷轴不足」提示：在备战页点一次挑战，连拍找 toast。

备用方案：如果抓不到 toast，就用「挑战次数=0」这个更稳的判据
（次数显示在备战页右上，0 时只有一个瘦窄的数字）。
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from PIL import Image                                    # noqa: E402

a = Adb()
before = a.screenshot()
before.save("shots/prep_before_tap.png")
print("点挑战 (1727,857) ...")
a.shell("input tap 1727 857")

found = None
for i in range(1, 13):
    time.sleep(0.8)
    im = a.screenshot()
    g = np.asarray(im.convert("L"), dtype=np.float32)
    d = np.abs(g - np.asarray(before.convert("L"), dtype=np.float32))
    diff = int((d > 60).sum())
    # 中部提示带（toast 一般在 y 290~350）
    band = g[280:360, :]
    bright = int((band > 200).sum())
    print(f"  t={i*0.8:4.1f}s 变化像素={diff:6d} 中部亮像素={bright:5d}")
    if bright > 300 and found is None:
        found = i
        im.save("shots/toast_live.png")
        print("  <<< 中部出现亮字，已保存 shots/toast_live.png")

if found is None:
    print("没抓到中部亮字")

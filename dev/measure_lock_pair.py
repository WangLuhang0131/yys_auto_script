# -*- coding: utf-8 -*-
"""干净地量一对锁定状态：现在量一次 -> 点图标切换 -> 再量一次。
（每次都重新抓图，避免引用旧截图里不一致的数字）"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from tasks.jiejie_tupo import ui                         # noqa: E402

a = Adb()
BOX = ui.R_LINEUP_LOCK


def measure(tag):
    im = a.screenshot()
    im.save(f"shots/lockm_{tag}.png")
    arr = np.asarray(im.crop(BOX), dtype=np.float32)
    g = arr.mean(axis=2)
    gold1 = ((arr[:, :, 0] > 140) & (arr[:, :, 1] > 110) & (arr[:, :, 2] < 150)
             & (arr[:, :, 0] - arr[:, :, 2] > 45))
    gold2 = ((arr[:, :, 0] > 120) & (arr[:, :, 1] > 100) & (arr[:, :, 2] < 160)
             & (arr[:, :, 0] - arr[:, :, 2] > 30))
    dark = (g < 90)
    out = {
        "bright>120": round(float((g > 120).mean()), 3),
        "bright>160": round(float((g > 160).mean()), 3),
        "dark<90": round(float(dark.mean()), 3),
        "gold_a": round(float(gold1.mean()), 3),
        "gold_b": round(float(gold2.mean()), 3),
        "mean": round(float(g.mean()), 1),
    }
    print(f"  [{tag}] {out}")
    crop = im.crop(BOX)
    crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST).save(f"shots/lockm_{tag}_zoom.png")
    return out


from PIL import Image  # noqa: E402

print("第一次（点图标之前的状态）:")
m1 = measure("state1")

print(f"\n点图标 {ui.TAP_LOCK_ICON} 切换 ...")
a.shell(f"input tap {ui.TAP_LOCK_ICON[0]} {ui.TAP_LOCK_ICON[1]}")
time.sleep(3.0)

print("第二次（切换之后）:")
m2 = measure("state2")

print("\n两次对比：")
for k in m1:
    print(f"  {k:12s} {m1[k]:>8}  ->  {m2[k]:>8}")

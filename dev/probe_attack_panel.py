# -*- coding: utf-8 -*-
"""试试不同位置/等待时间，找出打开「进攻」面板的正确点法。"""
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adbkit import Adb  # noqa: E402

a = Adb()
# 页面基准图（判断弹窗是否出现：弹窗区域亮度会显著变化）
BASE = None

def shot():
    return a.grab_land(None, raw=False)

def panel_score(im):
    """弹窗区域（用户截图中弹窗在 x150~720, y370~800）的特征：
    弹窗是浅色米黄面板，该区域亮度会明显升高。"""
    g = np.asarray(im.convert("L"), dtype=np.float32)
    return g[380:790, 160:700].mean()

base = shot()
base.save(r"D:\Program Files\WKSPC\yys\shots\jj_base.png")
print(f"基准 弹窗区亮度 = {panel_score(base):.1f}")

for pt, wait in [((865, 285), 2.5), ((800, 250), 3.0), ((865, 250), 4.0),
                 ((1185, 300), 3.0), ((460, 460), 3.0)]:
    a.shell("input tap %d %d" % a.screen_xy(*pt))
    time.sleep(wait)
    im = shot()
    sc = panel_score(im)
    im.save(rf"D:\Program Files\WKSPC\yys\shots\jj_tap_{pt[0]}_{pt[1]}.png")
    print(f"点 {pt} 等 {wait}s -> 弹窗区亮度 {sc:.1f}  (基准 {panel_score(base):.1f})")

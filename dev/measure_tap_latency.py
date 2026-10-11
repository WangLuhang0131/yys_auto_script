# -*- coding: utf-8 -*-
"""量 adb 点击的响应延迟：点「刷新」，每秒抓一帧看确认弹窗何时出现。"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adbkit import Adb  # noqa: E402

a = Adb()
base = r"D:\Program Files\WKSPC\yys\shots"

# 弹窗出现判据：屏幕中央那块（弹窗区域）的平均亮度会明显变化
def center_lum(im):
    g = np.asarray(im.convert("L"), dtype=np.float32)
    return float(g[380:700, 600:1320].mean())

before = a.grab_land(None, raw=False)
l0 = center_lum(before)
print(f"点击前 中央亮度 = {l0:.1f}")

t0 = time.time()
a.shell("input tap 1540 855")          # 刷新
print("已发送点击，开始每秒采样...")
found_at = None
for i in range(16):
    time.sleep(1.0)
    im = a.grab_land(None, raw=False)
    l = center_lum(im)
    mark = ""
    if abs(l - l0) > 6 and found_at is None:
        found_at = time.time() - t0
        mark = "  <== 界面变化"
        im.save(os.path.join(base, "jj_refresh_dialog.png"))
    print(f"  t={time.time()-t0:5.1f}s 中央亮度={l:6.1f}{mark}")

print(f"\n界面变化出现在 t≈{found_at:.1f}s" if found_at else "\n16 秒内没检测到变化")

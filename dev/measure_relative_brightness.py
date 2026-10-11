# -*- coding: utf-8 -*-
"""在「横幅变暗」状态下量相对亮度判据（格子和锁区都按整屏均值归一化）。"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                    # noqa: E402
import vision                                             # noqa: E402
from tasks.jiejie_tupo import ui, attack as atk           # noqa: E402

a = Adb()
im = a.screenshot()
ok, s, bx, by = atk.find_attack_btn(im)
print(f"当前有进攻面板: {ok} (分 {s})")
if ok:
    print("点右上 X 关闭面板")
    a.shell("input tap 1785 190")
    time.sleep(2.5)

im = a.screenshot()
im.save("shots/jj_after_close.png")
g = np.asarray(im.convert("L"), dtype=np.float32)
page = float(g.mean())
print(f"\n整屏均值 = {page:.1f}")

print("\n各格亮度（绝对值 / 相对整屏比值）：")
for i, (cx, cy) in enumerate(ui.GRID_CENTERS, 1):
    lum = atk.cell_lum(im, cx, cy)
    print(f"  格{i}: {lum:6.1f}  比值 {lum/page:.3f}")

box = ui.R_LINEUP_LOCK
lock = np.asarray(im.crop(box).convert("L"), dtype=np.float32)
print(f"\n阵容锁图标区: 均值 {lock.mean():.1f}  比值 {lock.mean()/page:.3f}  "
      f"亮像素(>150)占比 {float((lock>150).mean()):.3f}")

# 顺带看格子相对比值在「正常亮度」图上是多少，用于对比
for f in ("shots/jj_after_battle.png", "shots/step2_jiejie.png", "shots/step1_explore.png"):
    i2 = Image.open(f).convert("L") if False else None
from PIL import Image  # noqa: E402
for f in ("shots/step2_jiejie.png", "shots/jj_after_battle.png", "shots/step1_explore.png"):
    i2 = Image.open(f).convert("L")
    gg = np.asarray(i2, dtype=np.float32)
    pg = float(gg.mean())
    vals = [atk.cell_lum(i2, cx, cy) / pg for cx, cy in ui.GRID_CENTERS]
    print(f"{os.path.basename(f):24s} 整屏{pg:6.1f} 格比值 " +
          " ".join(f"{v:.2f}" for v in vals))

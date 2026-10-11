# -*- coding: utf-8 -*-
"""先量出亮格子（可打），再点它，验证能否打开「进攻」面板。"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adbkit import Adb                                    # noqa: E402
from tasks.jiejie_tupo import ui                          # noqa: E402

a = Adb()
base = r"D:\Program Files\WKSPC\yys\shots"


def cell_lum(im, cx, cy):
    hw, hh = ui.CELL_HALF
    return float(np.asarray(im.crop((cx - hw, cy - hh, cx + hw, cy + hh)).convert("L"),
                            dtype=np.float32).mean())


def scan(tag):
    im = a.grab_land(None, raw=False)
    print(f"  [{tag}] 各格亮度：")
    rows = []
    for r, cy in enumerate(ui.GRID_Y):
        vals = [(c, cell_lum(im, cx, cy)) for c, cx in enumerate(ui.GRID_X)]
        rows.append(vals)
        print("     行%d: " % (r + 1) + "  ".join(
            f"({r+1},{c+1}){v:6.1f}{'亮' if v > ui.CELL_BRIGHT_TH else '灰'}" for c, v in vals))
    return im, rows


print("=== 当前格子状态 ===")
im, rows = scan("before")

# 找最亮的可打格子
best = None
for r, cy in enumerate(ui.GRID_Y):
    for c, cx in enumerate(ui.GRID_X):
        v = rows[r][c][1]
        if v > ui.CELL_BRIGHT_TH and (best is None or v > best[2]):
            best = (cx, cy, v, r + 1, c + 1)

if best is None:
    print("!! 没有可打的亮格子")
    sys.exit(0)

cx, cy, v, r, c = best
print(f"\n>>> 选中最亮格子 ({r},{c}) 中心=({cx},{cy}) 亮度={v:.1f}")

# 用户提示：点名字+进度圈那一片（头像右侧）
tap_x, tap_y = cx + 120, cy + 30
print(f">>> 点击其名字/进度圈区域 ({tap_x},{tap_y})")

a.shell(f"input tap {tap_x} {tap_y}")
for i in range(5):
    time.sleep(1.2)
    cur = a.grab_land(None, raw=False)
    d = np.abs(np.asarray(im.convert("L"), dtype=np.int16)
               - np.asarray(cur.convert("L"), dtype=np.int16))
    n = int((d > 40).sum())
    print(f"   {1.2*(i+1):4.1f}s 变化像素={n:6d}")
    if n > 20000:
        cur.save(os.path.join(base, "jj_panel_open.png"))
        print("   <<< 界面明显变化，已保存 shots/jj_panel_open.png")
        break
else:
    cur = a.grab_land(None, raw=False)
    cur.save(os.path.join(base, "jj_after_tap.png"))
    print("   没有明显变化，已保存 shots/jj_after_tap.png")

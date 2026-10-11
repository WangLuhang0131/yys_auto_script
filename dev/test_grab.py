# -*- coding: utf-8 -*-
"""验证 grab_land 的区域截图与整屏截图是否一致，并测量耗时。"""
import time
import numpy as np
from adbkit import Adb

a = Adb()

t = time.time(); full = a.screenshot(); t_full = time.time() - t
print(f"整屏截图 {t_full*1000:.0f} ms 尺寸 {full.size}")

for box in [(1640, 790, 1815, 920), (700, 960, 1230, 1080), (0, 0, 400, 200)]:
    t = time.time(); part = a.grab_land(box); dt = time.time() - t
    ref = full.crop(box)
    d = np.abs(np.asarray(part, dtype=np.int16) - np.asarray(ref, dtype=np.int16))
    print(f"区域 {box} 尺寸 {part.size} 耗时 {dt*1000:.0f} ms  "
          f"最大像素差={d.max()} 平均差={d.mean():.2f}")

# 连续 5 次区域截图耗时
ts = []
for _ in range(5):
    t = time.time(); a.grab_land((700, 960, 1230, 1080)); ts.append(time.time() - t)
print("底部区域连续截图耗时:", [f"{x*1000:.0f}ms" for x in ts])

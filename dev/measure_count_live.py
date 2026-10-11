# -*- coding: utf-8 -*-
"""到备战页实机量「挑战次数」区域：现在道具为 0，应该只有一个数字。

同时对照：用户给的 0 次截图（shots/no_item_user.png）。
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
# 从庭院 -> 活动 -> 前往活动 -> 古迹演武
print("导航到备战页...")
a.shell("input tap 1835 222"); time.sleep(4.0)     # 右侧活动
a.shell("input tap 1727 925"); time.sleep(4.0)     # 前往活动
a.shell("input tap 420 435"); time.sleep(4.5)      # 古迹演武
im = a.screenshot()
im.save("shots/prep_zero_live.png")

# 右上角整片（含次数与资源）
im.crop((900, 0, 1920, 110)).resize((1020, 220), Image.NEAREST).save(
    "shots/prep_topbar_zoom.png")
print("已保存 shots/prep_topbar_zoom.png")

g = np.asarray(im.convert("L"), dtype=np.float32)
for label, box in [("x1000~1200", (1000, 15, 1200, 90)),
                   ("x1040~1160", (1040, 20, 1160, 85)),
                   ("x1450~1620", (1450, 20, 1620, 85))]:
    sub = g[box[1]:box[3], box[0]:box[2]]
    print(f"  {label}: 亮像素(>170)={int((sub>170).sum()):5d} 均值={sub.mean():.1f}")

# 对照用户 0 次截图
u = Image.open("shots/no_item_user.png").convert("L")
s = u.size[0] / 1920.0
for label, box in [("x1000~1200", (1000, 15, 1200, 90)),
                   ("x1450~1620", (1450, 20, 1620, 85))]:
    b = tuple(int(v * s) for v in box)
    sub = np.asarray(u.crop(b), dtype=np.float32)
    print(f"  用户图 {label}: 亮像素(>170)={int((sub>170).sum()):5d}")

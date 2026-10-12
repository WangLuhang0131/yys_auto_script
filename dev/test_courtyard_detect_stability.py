# -*- coding: utf-8 -*-
"""连拍多帧，看庭院识别稳不稳（为什么回庭院要用 4 步）。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from adbkit import Adb                                    # noqa: E402
from human_click import Human                             # noqa: E402
from core.nav import Returner, warn_pixels                # noqa: E402
import vision                                             # noqa: E402

TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_courtyard_bar.png")
a = Adb()
h = Human(a, log=lambda m: None)
r = Returner(a, h, print)

print("当前页面:", r.detect(), flush=True)
print("\n=== 连续 10 帧：庭院栏模板分数 / 页面判定 / 中央暗像素 ===", flush=True)
for i in range(10):
    img = a.screenshot()
    s, _, _ = vision.match(img, TPL, region=(60, 830, 1880, 1070))
    print(f"  第{i+1:2d}帧: 庭院栏分={s:.3f}  页面={r.detect(img):10s} 暗像素={warn_pixels(img)}",
          flush=True)
    time.sleep(0.6)

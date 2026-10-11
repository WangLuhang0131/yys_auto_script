# -*- coding: utf-8 -*-
"""量备战页右上「挑战次数」区域的亮像素数，用来判断次数是否为 0。

· 次数 0  -> 只有一个数字，亮像素少
· 次数 >0 -> 三位数，亮像素多
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

# 次数数字区（1920 基准）：实测数字大致在 x 1400~1500, y 30~75
BOX = (1380, 20, 1560, 85)

cases = [
    ("shots/no_item_prep.png", "次数0（道具用尽）"),
    ("shots/prep_before_tap.png", "次数0？"),
    ("shots/ref_prep.png", "次数296"),
    ("shots/step2_jiejie.png", "结界突破页(对照)"),
    ("shots/courtyard_clean.png", "庭院(对照)"),
]
for f, label in cases:
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert("L")
    a = np.asarray(im.crop(BOX), dtype=np.float32)
    bright = int((a > 170).sum())
    print("%-24s 亮像素(>170)=%5d  均值=%.1f" % (label, bright, a.mean()))

# 顺便看看当前实机画面
from adbkit import Adb                                   # noqa: E402
adb = Adb()
im = adb.screenshot()
im.save("shots/current_count.png")
a = np.asarray(im.convert("L").crop(BOX), dtype=np.float32)
print("\n当前实机: 亮像素(>170)=%d" % int((a > 170).sum()))
im.crop((1300, 10, 1620, 95)).resize((320 * 2, 85 * 2), Image.NEAREST).save(
    "shots/current_count_zoom.png")

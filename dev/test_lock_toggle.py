# -*- coding: utf-8 -*-
"""决定性实验：点一下「阵容」左侧的金框图标，看锁定状态是否切换。

· 如果切换了 → 说明这个图标就是锁定开关，而且我拿到了两种状态的实机画面；
· 如果弹出了编队界面 → 说明它是别的入口（那就点返回，不再乱试）。
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
ICON = (1270, 880)          # 「阵容」按钮左侧的金框图标
BOX = (1230, 845, 1330, 920)


def metrics(tag):
    im = a.screenshot()
    im.save(f"shots/lock_{tag}.png")
    arr = np.asarray(im.crop(BOX), dtype=np.float32)
    g = arr.mean(axis=2)
    gold = ((arr[:, :, 0] > 140) & (arr[:, :, 1] > 110) & (arr[:, :, 2] < 150)
            & (arr[:, :, 0] - arr[:, :, 2] > 45))
    whole = float(np.asarray(im.convert("L"), dtype=np.float32).mean())
    print(f"  [{tag}] 均值{g.mean():6.1f} 亮>120占比{(g>120).mean():.3f} "
          f"亮>160占比{(g>160).mean():.3f} 金色占比{gold.mean():.3f} 整屏{whole:.1f}")
    crop = im.crop(BOX)
    crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST).save(f"shots/lock_{tag}_zoom.png")
    return im


print("切换前（应为已锁定）:")
metrics("before")

print(f"\n点一下图标 {ICON} ...")
a.shell(f"input tap {ICON[0]} {ICON[1]}")
time.sleep(3.0)

print("切换后:")
after = metrics("after")

# 判断界面是否被换掉（弹出编队页会让整屏均值大变）
before = Image.open("shots/lock_before.png").convert("L")
d = np.abs(np.asarray(before, dtype=np.int16) - np.asarray(after.convert("L"), dtype=np.int16))
print(f"\n点击前后画面变化像素 = {(d>40).sum()}")

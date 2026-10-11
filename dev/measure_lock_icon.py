# -*- coding: utf-8 -*-
"""标定「阵容」锁定图标的颜色/亮度判据。

对比两张手机截图（裁剪后）里锁图标的样子：
  · 已锁定：金色小锁（用户提供的锁定截图）
  · 未锁定：灰色小锁（打之前那张截图）
再用整屏截图核对位置。
"""
import os
import numpy as np
from PIL import Image

base = r"D:\Program Files\WKSPC\yys\shots"

for name in ("step2_jiejie.png", "jj_after_battle.png"):
    im = Image.open(os.path.join(base, name)).convert("RGB")
    a = np.asarray(im, dtype=np.float32)
    # 「阵容」按钮左侧图标大致在 x 1265~1320, y 830~890
    for box in [(1265, 828, 1322, 892), (1270, 835, 1315, 885)]:
        reg = a[box[1]:box[3], box[0]:box[2]]
        g = reg.mean(axis=2)
        gold = ((reg[:, :, 0] > 150) & (reg[:, :, 1] > 120) & (reg[:, :, 2] < 140)
                & (reg[:, :, 0] - reg[:, :, 2] > 40))
        print(f"{name:22s} 区{box} 平均亮度{g.mean():6.1f} "
              f"金色占比{gold.mean():.3f} 平均色{tuple(round(v) for v in reg.reshape(-1,3).mean(axis=0))}")

# 顺便看看 加成 按钮旁的小锁（结界突破页 x 60~100, y 25~75）
im = Image.open(os.path.join(base, "jj_after_battle.png")).convert("RGB")
a = np.asarray(im, dtype=np.float32)
box = (55, 20, 105, 78)
reg = a[box[1]:box[3], box[0]:box[2]]
g = reg.mean(axis=2)
gold = ((reg[:, :, 0] > 150) & (reg[:, :, 1] > 120) & (reg[:, :, 2] < 140)
        & (reg[:, :, 0] - reg[:, :, 2] > 40))
print(f"{'加成旁区域':22s} 区{box} 平均亮度{g.mean():6.1f} 金色占比{gold.mean():.3f}")

# -*- coding: utf-8 -*-
"""给「结界挑战券不足」红字警告做判据。

用户截图（2729x1536）里那句提示在画面中部；先定位、再量红色像素占比。
红色文字是游戏明确的「券不足」信号，比解析条带上的数字稳得多。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/ticket_0of30_screen.png").convert("RGB")
W, H = im.size
sx, sy = W / 1920.0, H / 1080.0
a = np.asarray(im, dtype=np.float32)

# 用户截图里提示带大致在画面中部偏上（按 1920 基准 y≈470 换算）
y1, y2 = int(400 * sy), int(540 * sy)
band = a[y1:y2, :]
r, g, b = band[:, :, 0], band[:, :, 1], band[:, :, 2]
red = (r > 150) & (g < 120) & (b < 120) & (r - g > 60)
print(f"中部带 y{y1}~{y2}: 红色像素 {int(red.sum())}  占比 {red.mean():.5f}")

# 找红色像素的横向范围
ys, xs = np.nonzero(red)
if len(xs):
    print(f"  红色像素范围: x {xs.min()}~{xs.max()}  y {y1+ys.min()}~{y1+ys.max()}")
    print(f"  换算到 1920 基准: x {xs.min()/sx:.0f}~{xs.max()/sx:.0f} "
          f"y {(y1+ys.min())/sy:.0f}~{(y1+ys.max())/sy:.0f}")
    # 平均颜色
    print("  平均色:", tuple(round(float(v)) for v in band[red].mean(axis=0)))

# 同时对照：券够的时候（我抓的图）同区域红色像素应该很少
for label, path in (("券空(0/30)", "shots/ticket_0of30_screen.png"),
                    ("券够(结界突破页)", "shots/ticket_now.png"),
                    ("券空(我抓的)", "shots/ticket_real_zero.png")):
    i2 = Image.open(path).convert("RGB")
    s2 = i2.size[0] / 1920.0
    aa = np.asarray(i2, dtype=np.float32)
    yy1, yy2 = int(400 * s2), int(540 * s2)
    bb = aa[yy1:yy2, :]
    rr, gg, bl = bb[:, :, 0], bb[:, :, 1], bb[:, :, 2]
    rd = (rr > 150) & (gg < 120) & (bl < 120) & (rr - gg > 60)
    print(f"{label:18s} 红色像素 {int(rd.sum()):6d} 占比 {rd.mean():.5f}")

# 保存提示带供查看
im.crop((0, y1, W, y2)).save("shots/warn_band_user.png")
print("\n已保存 shots/warn_band_user.png")

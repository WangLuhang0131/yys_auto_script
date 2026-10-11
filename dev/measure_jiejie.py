# -*- coding: utf-8 -*-
"""量 结界突破 页面的网格几何 + 可用/已攻破格子的颜色判据。"""
import numpy as np
from PIL import Image

im = Image.open(r"D:\Program Files\WKSPC\yys\shots\step2_jiejie.png").convert("RGB")
g = np.asarray(im.convert("L"), dtype=np.float32)
a = np.asarray(im, dtype=np.float32)

# 网格区域大致范围（从截图目测：x 205~1700, y 195~765）
X1, Y1, X2, Y2 = 205, 195, 1700, 765
band = g[Y1:Y2, X1:X2]
col = band.mean(axis=0)      # 沿垂直方向平均 -> 竖向分隔
row = band.mean(axis=1)      # 沿水平方向平均 -> 横向分隔

def edges(sig, th=8):
    d = np.abs(np.diff(sig))
    idx = np.nonzero(d > th)[0]
    out = []
    for i in idx:
        if not out or i - out[-1] > 12:
            out.append(i)
    return out

print("竖向边界(相对X1):", [int(i) for i in edges(col)][:14])
print("横向边界(相对Y1):", [int(i) for i in edges(row)][:14])

# 单元格亮度中心值 -> 判断哪些是「已攻破(灰)」
print("\n各格中心亮度与平均色（3x3）：")
cx = [505, 865, 1225]
cy = [285, 440, 595]
for r, y in enumerate(cy, 1):
    line = []
    for c, x in enumerate(cx, 1):
        patch = g[y-40:y+40, x-60:x+60]
        rgb = a[y-40:y+40, x-60:x+60].reshape(-1, 3).mean(axis=0)
        line.append(f"({r},{c}) 亮度{patch.mean():6.1f} 色{tuple(round(v) for v in rgb)}")
    print("   ".join(line))

# 攻破记录数字 "4" 的位置（红圈）
red = ((a[:, :, 0] > 150) & (a[:, :, 1] < 90) & (a[:, :, 2] < 90))
ys, xs = np.nonzero(red[760:830, 260:360])
if len(xs):
    print(f"\n攻破记录红色区域: x {260+xs.min()}~{260+xs.max()}  y {760+ys.min()}~{760+ys.max()}")
